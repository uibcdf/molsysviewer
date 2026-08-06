#!/usr/bin/env python

import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time
import traceback
import json
import hashlib
from typing import Any, Dict, Iterable, Set, Tuple

GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
RESET = "\033[0m"

# Log file in the same directory as this script, listing notebooks that failed.
ERROR_LOG_PATH = Path(__file__).resolve().with_name("notebook_errors.log")

KEEP_WIDGET_STATE_TAG = "keep-widget-state"
WIDGET_VIEW_MIME = "application/vnd.jupyter.widget-view+json"
WIDGET_STATE_MIME = "application/vnd.jupyter.widget-state+json"


def code_fingerprint(notebook_path: Path) -> str:
    """A hash of the notebook's **code**, and of nothing else.

    What the run mark has to answer is "is this the code that produced these
    outputs?". A clock cannot answer it: a fresh clone stamps every file with the
    checkout time, so every notebook looks newer than its mark and a whole corpus
    re-runs; and fixing a typo in a markdown cell moves the file's date without
    changing anything a run would produce.

    So fingerprint the code cells' source. Not the outputs, which the run itself
    rewrites, and not the prose, which cannot change a result. Measured at 0.5 ms
    per notebook, and this script already parses every notebook to strip widget
    state, so the read is paid for.
    """
    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    cells = notebook.get("cells", []) if isinstance(notebook, dict) else []
    source = "\n\x00".join(
        "".join(cell.get("source", []))
        for cell in cells
        if isinstance(cell, dict) and cell.get("cell_type") == "code"
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def write_run_mark(mark_path: Path, notebook_path: Path, quiet: bool = False) -> str:
    """Record what was executed. Written by the script, never by a person."""
    fingerprint = code_fingerprint(notebook_path)
    payload = {
        "code_sha256": fingerprint,
        # Decides nothing. It is here because "when did this last run?" is a fair
        # question to ask of a file you are looking at.
        "executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    mark_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    if not quiet:
        print(f"Run mark written to {mark_path}")
    return fingerprint


def read_run_mark(mark_path: Path) -> Dict[str, Any] | None:
    """The mark, or `None`. A bare number is the pre-2026-08-06 format."""
    try:
        text = mark_path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if not text:
        return None
    try:
        payload = json.loads(text)
        if isinstance(payload, dict) and "code_sha256" in payload:
            return payload
    except Exception:
        pass
    try:
        return {"legacy_timestamp": float(text)}
    except Exception:
        return None

def _walk_json(value: Any) -> Iterable[Any]:
    stack = [value]
    while stack:
        v = stack.pop()
        yield v
        if isinstance(v, dict):
            for vv in v.values():
                stack.append(vv)
        elif isinstance(v, list):
            for vv in v:
                stack.append(vv)

def _cell_tags(cell: Dict[str, Any]) -> Set[str]:
    tags = cell.get("metadata", {}).get("tags", [])
    if not isinstance(tags, list):
        return set()
    return {t for t in tags if isinstance(t, str)}

def _find_widget_model_ids_in_cell(cell: Dict[str, Any]) -> Set[str]:
    model_ids: Set[str] = set()
    for output in cell.get("outputs", []) or []:
        if not isinstance(output, dict):
            continue
        data = output.get("data")
        if not isinstance(data, dict):
            continue
        widget_view = data.get(WIDGET_VIEW_MIME)
        if isinstance(widget_view, dict):
            model_id = widget_view.get("model_id")
            if isinstance(model_id, str) and model_id:
                model_ids.add(model_id)
    return model_ids

def _remove_widget_view_outputs_in_cell(cell: Dict[str, Any]) -> bool:
    changed = False
    outputs = cell.get("outputs")
    if not isinstance(outputs, list):
        return False
    new_outputs = []
    for out in outputs:
        if not isinstance(out, dict):
            new_outputs.append(out)
            continue
        data = out.get("data")
        if not isinstance(data, dict) or WIDGET_VIEW_MIME not in data:
            new_outputs.append(out)
            continue
        data = dict(data)
        del data[WIDGET_VIEW_MIME]
        changed = True
        if len(data) == 0 and out.get("output_type") in ("display_data", "execute_result"):
            # Drop the output entirely if it only carried the widget view.
            continue
        out = dict(out)
        out["data"] = data
        new_outputs.append(out)
    if changed:
        cell["outputs"] = new_outputs
    return changed

def _get_widget_state_container(nb: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str | None]:
    meta = nb.get("metadata")
    if not isinstance(meta, dict):
        return None, None
    widgets = meta.get("widgets")
    if not isinstance(widgets, dict):
        return None, None
    if WIDGET_STATE_MIME in widgets and isinstance(widgets.get(WIDGET_STATE_MIME), dict):
        return widgets[WIDGET_STATE_MIME], WIDGET_STATE_MIME
    # Fallback for non-standard layouts.
    if "state" in widgets and isinstance(widgets.get("state"), dict):
        return widgets, None
    return None, None

def strip_widget_state(notebook_path: Path, keep_tag: str = KEEP_WIDGET_STATE_TAG) -> bool:
    """
    Remove ipywidgets/AnyWidget state that makes executed notebooks heavy.

    Default behavior:
    - Remove notebook-level widget state under `metadata.widgets`.
    - Remove cell outputs that display widget views.

    If a cell is tagged with `keep-widget-state`, keep only the widget models
    required to render those tagged cells, and strip widget-view outputs from
    other cells.
    """
    try:
        nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    if not isinstance(nb, dict):
        return False

    cells = nb.get("cells")
    if not isinstance(cells, list):
        return False

    keep_cells = [c for c in cells if isinstance(c, dict) and keep_tag in _cell_tags(c)]
    keep_model_ids: Set[str] = set()
    for cell in keep_cells:
        keep_model_ids |= _find_widget_model_ids_in_cell(cell)

    changed = False

    if not keep_model_ids:
        meta = nb.get("metadata")
        if isinstance(meta, dict) and "widgets" in meta:
            del meta["widgets"]
            changed = True
        for cell in cells:
            if isinstance(cell, dict):
                changed = _remove_widget_view_outputs_in_cell(cell) or changed
    else:
        # Keep only widgets needed for tagged cells; remove widget views elsewhere.
        for cell in cells:
            if isinstance(cell, dict) and keep_tag not in _cell_tags(cell):
                changed = _remove_widget_view_outputs_in_cell(cell) or changed

        container, container_key = _get_widget_state_container(nb)
        if container is None:
            # No state container; nothing else to do.
            pass
        else:
            models = container.get("state")
            if isinstance(models, dict):
                all_ids = {k for k in models.keys() if isinstance(k, str)}
                closure: Set[str] = set()
                frontier = [mid for mid in keep_model_ids if mid in all_ids]
                while frontier:
                    mid = frontier.pop()
                    if mid in closure:
                        continue
                    closure.add(mid)
                    model = models.get(mid)
                    if not isinstance(model, dict):
                        continue
                    model_state = model.get("state")
                    for v in _walk_json(model_state):
                        if isinstance(v, str) and v in all_ids and v not in closure:
                            frontier.append(v)
                        elif isinstance(v, dict):
                            maybe_id = v.get("model_id")
                            if isinstance(maybe_id, str) and maybe_id in all_ids and maybe_id not in closure:
                                frontier.append(maybe_id)
                if closure and closure != all_ids:
                    container["state"] = {k: models[k] for k in models.keys() if k in closure}
                    changed = True

            # If state is now empty, drop widgets metadata entirely.
            if isinstance(container.get("state"), dict) and len(container["state"]) == 0:
                meta = nb.get("metadata")
                if isinstance(meta, dict) and "widgets" in meta:
                    del meta["widgets"]
                    changed = True
            else:
                # Ensure the container remains under metadata.widgets if we found it.
                if container_key is not None:
                    meta = nb.get("metadata")
                    if isinstance(meta, dict):
                        widgets = meta.get("widgets")
                        if isinstance(widgets, dict):
                            widgets[container_key] = container

    if not changed:
        return False

    notebook_path.write_text(
        json.dumps(nb, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    return True

class ProgressTracker:
    """Milestone progress for a quiet run, so `-q` is quiet and not blind.

    Adopted from MolSysMT's `execute_notebooks.py`, which had it first and models
    it on `pytest-receptor`: a percentage line every so often on stderr rather
    than one line per notebook on stdout. A bulk run is minutes long; something
    has to say it is still moving.
    """

    def __init__(self, total: int, step_percent: int = 20):
        self.total = total
        self.step_percent = step_percent
        self.completed = 0
        self.executed = 0
        self.failed = 0
        self.start_time = time.monotonic()
        self.next_threshold = step_percent
        self.lock = threading.Lock()

    def update(self, executed: bool, failed: bool = False) -> None:
        with self.lock:
            self.completed += 1
            self.executed += int(executed)
            self.failed += int(failed)
            if self.total <= 0 or self.completed >= self.total:
                return
            percent = (self.completed * 100) // self.total
            if percent < self.next_threshold:
                return
            elapsed = time.monotonic() - self.start_time
            sys.stderr.write(
                f"execute_notebooks: {percent}% {self.completed}/{self.total} ({elapsed:.0f}s)\n"
            )
            sys.stderr.flush()
            self.next_threshold = (percent // self.step_percent + 1) * self.step_percent


def error_excerpt(output: str, max_lines: int = 40) -> str:
    """The part of nbconvert's output a person needs, without the log file.

    Writing documentation is a loop — edit a cell, run this, look at what
    happened — and until now a failure printed only the path of a log to go and
    open. The useful part is always the same block, so print that instead.
    """
    marker = "An error occurred while executing the following cell"
    lines = output.splitlines()
    start = next((i for i, line in enumerate(lines) if marker in line), None)
    excerpt = lines[start:] if start is not None else lines[-max_lines:]
    if len(excerpt) > max_lines:
        # Keep the head (the offending cell) and the tail (the exception).
        head, tail = excerpt[: max_lines // 2], excerpt[-max_lines // 2:]
        excerpt = head + [f"    … {len(excerpt) - max_lines} more lines …"] + tail
    return "\n".join(f"    {line}" for line in excerpt)


def execute_notebook(notebook_path: Path, force: bool = False, quiet: bool = False,
                     progress: "ProgressTracker | None" = None) -> bool:

    last_run_file = notebook_path.with_suffix('.nbconvert.last_run')
    log_file = notebook_path.with_suffix('.nbconvert.log')

    needs_execution = False

    mark = read_run_mark(last_run_file)
    if mark is None:
        needs_execution = True
    elif "code_sha256" in mark:
        needs_execution = mark["code_sha256"] != code_fingerprint(notebook_path)
    else:
        # Pre-2026-08-06 mark: a bare timestamp. Decide it the old way once, and
        # if the notebook is up to date, upgrade the mark *without executing* —
        # otherwise the change would cost every project a full re-run of its
        # corpus on the day it lands.
        needs_execution = notebook_path.stat().st_mtime > mark["legacy_timestamp"]
        if not needs_execution and not force:
            write_run_mark(last_run_file, notebook_path, quiet=True)

    if needs_execution or force:

        if not quiet:
            print(f"Executing notebook: {notebook_path}")
        env = os.environ.copy()
        env["MSM_VIEWS_FROM_HTML_FILES"] = "True"

        result = subprocess.run(
            ["jupyter", "nbconvert", "--execute", "--inplace", str(notebook_path)],
            capture_output=True,
            text=True,
            env=env
        )

        log_file.write_text(result.stdout + "\n" + result.stderr)

        if result.returncode != 0:
            print(f"{RED}✘{RESET} Error executing {notebook_path}")
            print(error_excerpt(result.stdout + "\n" + result.stderr))
            print(f"    (full output: {log_file})")
            if progress is not None:
                progress.update(executed=True, failed=True)
            if last_run_file.exists():
                last_run_file.unlink()
            # Log failing notebook immediately to the shared error log.
            try:
                with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
                    f.write(f"{notebook_path}\n")
            except Exception:
                pass
            return False
        else:
            if progress is not None:
                progress.update(executed=True)
            elif not quiet:
                print(f"{GREEN}✔{RESET} Notebook {notebook_path} executed successfully.")
            try:
                did_strip = strip_widget_state(notebook_path)
                if did_strip:
                    print(f"{GREEN}●{RESET} Stripped widget state from {notebook_path}")
            except Exception:
                # Never fail notebook execution because of a best-effort cleanup.
                pass
            write_run_mark(last_run_file, notebook_path, quiet=quiet or progress is not None)
            return True

    else:
        if progress is not None:
            progress.update(executed=False)
        elif not quiet:
            print(f"{BLUE}●{RESET} Notebook {notebook_path} is up to date. No execution needed.")
        return True


def main(force=False, notebook: Path = None, recursive: bool = False, n_workers: int = 1,
         quiet: bool = False) -> int:

    if notebook is not None:
        if not notebook.exists():
            print(f"{RED}✘{RESET} {notebook} does not exist.")
            return 1
        if notebook.is_file():
            nb_list = [notebook]
        elif notebook.is_dir():
            if recursive:
                nb_list = notebook.rglob("*.ipynb")
            else:
                nb_list = notebook.glob("*.ipynb")
    else:
        if recursive:
            nb_list = Path(".").rglob("*.ipynb")
        else:
            nb_list = Path(".").glob("*.ipynb")

    nb_list = [nb for nb in nb_list if ".ipynb_checkpoints" not in nb.parts]

    n_workers = max(1, int(n_workers) if n_workers is not None else 1)

    failed_notebooks = []
    progress = ProgressTracker(len(nb_list)) if quiet else None

    if n_workers == 1:
        for nb_path in nb_list:
            try:
                ok = execute_notebook(nb_path, force, quiet=quiet, progress=progress)
            except Exception:
                ok = False
                # Say what happened. This handler used to swallow the exception
                # whole, so a failure *outside* the notebook — a missing file, a
                # broken kernel spec, a bug in this script — was indistinguishable
                # from a notebook whose code raised, and left no trace anywhere.
                print(f"{RED}✘{RESET} {nb_path} could not be run at all:")
                traceback.print_exc()
                # Log unexpected failures (outside execute_notebook) immediately.
                try:
                    with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(f"{nb_path}\n")
                except Exception:
                    pass
            if not ok:
                failed_notebooks.append(nb_path)
    else:
        if not quiet:
            print(f"Executing {len(nb_list)} notebooks using {n_workers} workers.")
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            future_to_nb = {
                executor.submit(execute_notebook, nb_path, force, quiet, progress): nb_path
                for nb_path in nb_list
            }
            for future, nb_path in future_to_nb.items():
                try:
                    ok = future.result()
                except Exception:
                    ok = False
                    # Log unexpected failures (outside execute_notebook) immediately.
                    try:
                        with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
                            f.write(f"{nb_path}\n")
                    except Exception:
                        pass
                if not ok:
                    failed_notebooks.append(nb_path)

    if quiet and progress is not None:
        elapsed = time.monotonic() - progress.start_time
        print(f"execute_notebooks: {progress.completed} notebooks, "
              f"{progress.executed} executed, {progress.failed} failed ({elapsed:.0f}s)")

    if failed_notebooks:
        print(f"{RED}✘{RESET} {len(failed_notebooks)} notebook(s) failed. "
              f"See {ERROR_LOG_PATH}")
    else:
        print(f"{GREEN}✔{RESET} All notebooks executed successfully.")

    # The count is the exit status. Until 2026-08-06 this always ended in 0, so
    # anything automating it — a CI job above all — would report success while
    # documented examples were broken, which is the exact defect the gate exists
    # to catch, one level up.
    return len(failed_notebooks)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="""
    Execute Jupyter notebooks if they have been modified since their last successful execution.
    You can pass a single notebook path, a directory, or a wildcard pattern (e.g. '*.ipynb').
    
    Examples:
        python execute_notebooks.py                       # All notebooks in current directory
        python execute_notebooks.py -r                    # All notebooks recursively from current directory
        python execute_notebooks.py -n 4 -r               # Recursively using 4 workers in parallel
        python execute_notebooks.py -r docs/user_guide    # All notebooks in docs/user_guide recursively
        python execute_notebooks.py analysis.ipynb        # Only that notebook
        python execute_notebooks.py '/home/user/*.ipynb'  # Wildcard pattern (quoted)
        python execute_notebooks.py -f                    # Force re-execution of all
        python execute_notebooks.py -fr docs/user_guide   # Combine flags: force + recursive
    
    Each successful run updates a corresponding .nbconvert.log file with a timestamp.
    Notebooks are skipped if unchanged.
    """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("notebook", nargs="*", default=None,
                        help="Notebook(s) to execute. Supports wildcard patterns (e.g. *.ipynb).")
    parser.add_argument("-f", "--force", action="store_true",
                        help="Force execution of notebooks regardless of timestamps.")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Search for notebooks recursively in directories.")
    parser.add_argument(
        "-n", "--n-workers", type=int, default=1,
        help="Number of worker threads to use for notebook execution. "
             "Use 1 (default) to run serially without parallel workers."
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Milestone progress instead of one line per notebook. Failures are "
             "still printed in full: an error is not chatter.",
    )
    args = parser.parse_args()

    # Reset error log at the beginning of a CLI invocation.
    try:
        ERROR_LOG_PATH.write_text("", encoding="utf-8")
    except Exception:
        # If we cannot reset the log, continue execution; failures will still be reported on stdout.
        pass

    failures = 0
    if args.notebook:
        for nb in map(Path, args.notebook):
            if nb.is_file() or nb.is_dir():
                failures += main(force=args.force, notebook=nb, recursive=args.recursive,
                                 n_workers=args.n_workers, quiet=args.quiet)
            else:
                print(f"{RED}✘{RESET} File not found or not a notebook: {nb}")
                failures += 1
    else:
        failures = main(force=args.force, recursive=args.recursive, n_workers=args.n_workers,
                        quiet=args.quiet)

    raise SystemExit(1 if failures else 0)
