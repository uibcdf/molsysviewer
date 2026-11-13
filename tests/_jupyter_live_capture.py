"""Own an isolated real Jupyter/kernel/browser receiving process for #319."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def _documented_live_state(root: Path) -> str:
    """Receive the exact named live-cell example through the actual kernel."""
    page = root / "docs/content/user/export/state.md"
    matches = re.findall(
        r"^```\{code-block\} python\n:name: live-state-capture\n:caption: [^\n]+\n\n(.*?)^```",
        page.read_text(encoding="utf-8"),
        re.MULTILINE | re.DOTALL,
    )
    assert len(matches) == 1, "State documentation must declare one live-cell example."
    return matches[0]


def _safe_browser_summary(path: Path) -> dict:
    """Publish only closed diagnostic vocabulary and bounded integer counts."""
    limit = 1024 * 1024
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except FileNotFoundError:
        return {"status": "unavailable", "reason": "missing"}
    except OSError:
        return {"status": "unavailable", "reason": "io_error"}
    if len(raw) > limit:
        return {"status": "unavailable", "reason": "oversized"}
    try:
        report = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        return {"status": "unavailable", "reason": "invalid"}
    if not isinstance(report, dict) or report.get("outcome") not in ("passed", "failed"):
        return {"status": "unavailable", "reason": "invalid"}
    summary = {"status": "available", "outcome": report["outcome"]}
    if report["outcome"] == "failed":
        phases = (
            {
                "bootstrap",
                "plain-kernel baseline",
                "canvas popup",
                "cancel late reply",
                "autonomous capture deadline",
                "moving setup",
                "lifecycle open",
                "lifecycle close",
                "lifecycle collection",
                "moving popup",
                "background state",
                "background session",
                "visible retry state",
                "visible retry session",
                "Movie notebook authoring",
                "Movie Python edit",
                "Movie notebook seek",
                "Movie popup camera",
                "Movie detached preview",
                "Movie detached export",
                "Movie session recovery",
                "Movie close cancellation",
            }
            | {
                f"{api} {origin} {kind}"
                for api in ("Python", "Studio")
                for origin in ("notebook", "popup")
                for kind in ("state", "session")
            }
            | {
                f"Moving {api} {origin} {kind}"
                for api in ("Python", "Studio")
                for origin in ("notebook", "popup")
                for kind in ("state", "session")
            }
            | {f"Moving default Python notebook {kind}" for kind in ("state", "session")}
        )
        error_types = {
            "Error",
            "AssertionError",
            "TimeoutError",
            "TypeError",
            "RangeError",
            "ReferenceError",
            "SyntaxError",
        }
        for source, target, allowed in (("stage", "phase", phases), ("error_type", "error_type", error_types)):
            value = report.get(source)
            summary[target] = value if isinstance(value, str) and value in allowed else "unclassified"
    for key in (
        "capture_restore_cases",
        "strong_restore_cases",
        "studio_cases",
        "moving_capture_cases",
        "movie_authoring_cases",
    ):
        value = report.get(key)
        if type(value) is int and 0 <= value <= 100:
            summary[key] = value
    return summary


def _track_owned_processes(owned):
    """Retain descendants while their known parents still own them."""
    import psutil

    errors = []
    for parent in tuple(owned.values()):
        try:
            if not parent.is_running():
                continue
            for child in parent.children(recursive=True):
                owned[(child.pid, child.create_time())] = child
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
        except psutil.Error as error:
            errors.append(f"track:{parent.pid}:{type(error).__name__}")
    return errors


def _stop_owned_processes(owned):
    """Stop only recorded process identities, including reparented children."""
    import psutil

    errors = []

    def live(process):
        try:
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            return False
        except psutil.Error as error:
            errors.append(f"status:{process.pid}:{type(error).__name__}")
            return True

    pending = [process for process in reversed(tuple(owned.values())) if live(process)]
    for process in pending:
        try:
            process.terminate()
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
        except psutil.Error as error:
            errors.append(f"terminate:{process.pid}:{type(error).__name__}")
    try:
        _gone, pending = psutil.wait_procs(pending, timeout=3)
    except psutil.Error as error:
        errors.append(f"wait_terminate:{type(error).__name__}")
    pending = [process for process in pending if live(process)]
    for process in pending:
        if not live(process):
            continue
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
        except psutil.Error as error:
            errors.append(f"kill:{process.pid}:{type(error).__name__}")
    try:
        _gone, pending = psutil.wait_procs(pending, timeout=3)
    except psutil.Error as error:
        errors.append(f"wait_kill:{type(error).__name__}")
    return {"tracked": len(owned), "survivors": [process.pid for process in pending if live(process)], "errors": errors}


def _check_moving_capture_contract(observed: dict) -> None:
    """Require distinct healthy defaults and all delayed scientific controls."""
    cases = observed["moving_cases"]
    assert observed["moving_capture_cases"] == len(cases) == 8
    assert len({case["request_id"] for case in cases}) == 8

    def identity(case):
        return case["origin"], case["method"], case["kind"]

    default = [case for case in cases if case["scenario"] == "default"]
    delayed = [case for case in cases if case["scenario"] == "delayed"]
    assert len(default) == 2 and {identity(case) for case in default} == {
        ("notebook", "Python", kind) for kind in ("state", "session")
    }
    assert len(delayed) == 6 and {identity(case) for case in delayed} == {
        (origin, method, kind)
        for origin, methods in (("notebook", ("Python", "Studio")), ("popup", ("Studio",)))
        for method in methods
        for kind in ("state", "session")
    }
    for case in cases:
        assert case["independent_file_restore"] is True
        assert case["source_identity_and_coordinates_unchanged"] is True
        timeout = case["requested_timeout_ms"]
        assert type(timeout) in (int, float) and 0 < timeout <= 10_000
    for case in default:
        assert case["uses_public_default"] is True
        assert case["requested_timeout_ms"] <= 5_000
        assert case["held_real_queries"] == 0
    for case in delayed:
        assert case["uses_public_default"] is False
        assert case["requested_timeout_ms"] > 5_000
        assert case["held_real_queries"] > 0
        frames = case["frame_changes_after_request"]
        assert len(frames) == 2 and frames[0] != frames[1]


def run(output: Path, *, profile: str = "full") -> int:
    if profile not in {"full", "background", "lifecycle", "movie"}:
        raise ValueError("Select the full, background, lifecycle or movie receiving profile.")
    for name in ("jupyterlab", "ipykernel", "anywidget", "psutil"):
        if importlib.util.find_spec(name) is None:
            raise RuntimeError(f"The live Jupyter guard requires {name}.")
    import psutil

    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    directories = ("config", "runtime", "data/kernels/receiving", "notebooks", "workspaces", "settings", "ipython")
    for directory in directories:
        (output / directory).mkdir(parents=True, mode=0o700)
    root = Path(__file__).resolve().parents[1]
    module = importlib.util.find_spec("molsysviewer")
    if module is None:
        raise RuntimeError("MolSysViewer must be importable in the receiving interpreter.")
    node = Path(sys.executable).with_name("node.exe" if os.name == "nt" else "node")
    if not node.is_file():
        found = shutil.which("node")
        if found is None:
            raise RuntimeError("The live Jupyter guard requires Node and the repository's Playwright installation.")
        node = Path(found)

    # A previous actual Chrome launch exceeded the Unix-socket path limit
    # under the long pytest output path. Browser scratch has a short lifetime
    # and root; caller-owned logs and media stay in output.
    scratch = tempfile.TemporaryDirectory(prefix="msv-jup-", dir="/tmp" if os.name == "posix" else None)
    env = {
        **os.environ,
        "JUPYTER_CONFIG_DIR": str(output / "config"),
        "JUPYTER_RUNTIME_DIR": str(output / "runtime"),
        "JUPYTER_PATH": str(output / "data"),
        "JUPYTER_DATA_DIR": str(output / "data"),
        "JUPYTERLAB_WORKSPACES_DIR": str(output / "workspaces"),
        "JUPYTERLAB_SETTINGS_DIR": str(output / "settings"),
        "IPYTHONDIR": str(output / "ipython"),
        "MPLCONFIGDIR": str(output / "matplotlib"),
        "TMPDIR": scratch.name,
        "TMP": scratch.name,
        "TEMP": scratch.name,
    }
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    token = secrets.token_hex(32)
    settings = output / "settings.json"
    config = output / "config/jupyter_server_config.py"
    server = browser = None
    owned = {}
    interrupted = None
    started = time.monotonic()
    result = {
        "scope": f"Actual Jupyter/kernel/anywidget/Mol* {profile} receiving; no installed or visible Qt claim.",
        "profile": profile,
        "state": "starting",
        "output": str(output),
    }
    try:
        settings.write_text(
            json.dumps(
                {
                    "port": port,
                    "token": token,
                    "viewer_root": str(root),
                    "output": str(output),
                    "profile": profile,
                }
            )
        )
        settings.chmod(0o600)
        env["MOLSYSVIEWER_JUPYTER_CAPTURE_SETTINGS"] = str(settings)
        (output / "data/kernels/receiving/kernel.json").write_text(
            json.dumps(
                {
                    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "MolSysViewer capture receiving",
                    "language": "python",
                    "env": {key: env[key] for key in ("PYTHONPATH",) if key in env},
                }
            )
        )
        config.write_text(
            "c = get_config()\n"
            f"c.IdentityProvider.token = {token!r}\n"
            "c.ServerApp.ip = '127.0.0.1'\n"
            f"c.ServerApp.port = {port}\n"
            "c.ServerApp.port_retries = 0\nc.ServerApp.open_browser = False\n"
            f"c.ServerApp.root_dir = {str(output / 'notebooks')!r}\n"
            "c.LabApp.expose_app_in_browser = True\n"
        )
        config.chmod(0o600)
        cell = "\n".join(
            [
                "from pathlib import Path",
                "import ast, copy, json, time, zipfile, threading",
                "import numpy as np",
                "import molsysviewer as msv",
                "import molsysmt as msm",
                f"assert Path(msv.__file__).resolve() == Path({str(module.origin)!r}).resolve()",
                "with msv.demo['pentalanine'] as seed:",
                "    view = seed.extract(structure_indices=[0, 8, 3])",
                "view.player.go_to_structure(2)",
                "view.measurements.add_distance([0], [5], tag='capture-distance')",
                "view.annotations.add('Capture control', atom_indices=[0], tag='capture-label')",
                "_coordinates = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit='angstrom').copy()",
                f"_output = Path({str(output / 'notebooks')!r})",
                f"_documented_live_state = {_documented_live_state(root)!r}",
                "def inspect_file(name, kind):",
                "    path = _output / name",
                "    if kind == 'state':",
                "        state = json.loads(path.read_text())",
                "    else:",
                "        with zipfile.ZipFile(path) as archive:",
                "            state = json.loads(archive.read('state.json'))",
                "    np.testing.assert_array_equal(msv.pyunitwizard.get_value(view.get_coordinates(), to_unit='angstrom'), _coordinates)",
                "    return {'state': state, 'pending_saves': len(view._work_file_saves._pending), 'pending_captures': len(view._frontend_requests._pending)}",
                "async def save_live(name, kind):",
                "    path = _output / name",
                "    if kind == 'state':",
                "        code = compile(_documented_live_state, 'state.md#live-state-capture', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)",
                "        await eval(code, {'view': view, 'path': path})",
                "    else:",
                "        await view.save_session_async(path)",
                "    return inspect_file(name, kind)",
                "view",
            ]
        )
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "name": "receiving",
                    "display_name": "MolSysViewer capture receiving",
                    "language": "python",
                }
            },
            "cells": [
                {
                    "id": "capture-setup",
                    "cell_type": "code",
                    "metadata": {},
                    "source": cell.splitlines(True),
                    "execution_count": None,
                    "outputs": [],
                }
            ],
        }
        if profile == "lifecycle":
            import runpy

            notebook["cells"] = [
                {
                    "id": f"lifecycle-{index}",
                    "cell_type": "code",
                    "metadata": {},
                    "source": source.splitlines(True),
                    "execution_count": None,
                    "outputs": [],
                }
                for index, source in enumerate(
                    runpy.run_path(str(Path(__file__).with_name("_jupyter_widget_lifecycle.py")))["notebook_cells"]()
                )
            ]
        elif profile == "movie":
            import runpy

            expected = {
                name: importlib.util.find_spec(name).origin
                for name in ("molsysviewer", "molsysmt", "pyunitwizard", "molsysmt._rust")
            }
            cells = runpy.run_path(str(Path(__file__).with_name("_jupyter_movie.py")))["notebook_cells"](
                output, expected
            )
            notebook["cells"] = [
                {
                    "id": f"movie-{index}",
                    "cell_type": "code",
                    "metadata": {},
                    "source": source.splitlines(True),
                    "execution_count": None,
                    "outputs": [],
                }
                for index, source in enumerate(cells)
            ]
        (output / "notebooks/capture.ipynb").write_text(json.dumps(notebook))
        with (output / "server.log").open("w") as log:
            (output / "server.log").chmod(0o600)
            server = subprocess.Popen(
                [sys.executable, "-m", "jupyterlab", "--no-browser"],
                cwd=output / "notebooks",
                env=env,
                stdout=log,
                stderr=log,
            )
            process = psutil.Process(server.pid)
            owned[(process.pid, process.create_time())] = process
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if _track_owned_processes(owned):
                raise RuntimeError("Could not track the isolated Jupyter process tree.")
            if server.poll() is not None:
                raise RuntimeError("The isolated Jupyter server exited before readiness.")
            try:
                request = Request(f"http://127.0.0.1:{port}/api/status", headers={"Authorization": f"token {token}"})
                with urlopen(request, timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                time.sleep(0.2)
        else:
            raise TimeoutError("The isolated Jupyter server did not become ready.")
        with (output / "browser.log").open("w") as log:
            (output / "browser.log").chmod(0o600)
            entry = Path(__file__).with_name(
                {
                    "background": "_jupyter_background_capture.mjs",
                    "lifecycle": "_jupyter_widget_lifecycle.mjs",
                    "full": "_jupyter_live_capture.mjs",
                    "movie": "_jupyter_live_capture.mjs",
                }[profile]
            )
            browser = subprocess.Popen([str(node), str(entry)], env=env, stdout=log, stderr=log)
            process = psutil.Process(browser.pid)
            owned[(process.pid, process.create_time())] = process
            # Eight full-profile moving cases now take 232 seconds on the
            # qualified shared host. Bound the aggregate independently of
            # the unchanged five-second defaults and explicit delayed calls.
            result["browser_timeout_seconds"] = 300 if profile == "full" else 240
            deadline = time.monotonic() + result["browser_timeout_seconds"]
            while browser.poll() is None:
                if _track_owned_processes(owned):
                    raise RuntimeError("Could not track the isolated browser process tree.")
                if time.monotonic() >= deadline:
                    raise TimeoutError("The isolated Jupyter browser guard exceeded its deadline.")
                time.sleep(0.1)
        result["browser_exit_code"] = browser.returncode
        if profile == "full" and browser.returncode == 0:
            _check_moving_capture_contract(json.loads((output / "observations.json").read_text()))
        result.update(state="completed", exit_code=browser.returncode)
    except BaseException as error:
        result.update(state="failed", exit_code=1, error_type=type(error).__name__)
        if not isinstance(error, Exception):
            interrupted = error
        # Raw logs may contain the ephemeral server URL. Keep diagnostics in
        # this owner-only workspace, not a credential-bearing pytest traceback.
    finally:
        cleanup_errors = []
        try:
            cleanup_errors.extend(_track_owned_processes(owned))
        except Exception as error:
            cleanup_errors.append(f"track:{type(error).__name__}")
        if server is not None:
            try:
                request = Request(
                    f"http://127.0.0.1:{port}/api/shutdown", method="POST", headers={"Authorization": f"token {token}"}
                )
                with urlopen(request, timeout=3):
                    pass
                server.wait(timeout=5)
            except (URLError, TimeoutError, subprocess.TimeoutExpired, OSError):
                # The recorded tree below also owns server and kernel fallback
                # termination; a failed graceful shutdown is not a process leak.
                pass
            except Exception as error:
                cleanup_errors.append(f"shutdown:{type(error).__name__}")
        try:
            result["process_cleanup"] = _stop_owned_processes(owned)
            cleanup_errors.extend(result["process_cleanup"]["errors"])
            if result["process_cleanup"]["survivors"]:
                cleanup_errors.append("owned_processes_survived")
        except Exception as error:
            cleanup_errors.append(f"process_cleanup:{type(error).__name__}")
        for child in (browser, server):
            if child is not None:
                try:
                    child.wait(timeout=1)
                except (subprocess.TimeoutExpired, OSError) as error:
                    cleanup_errors.append(f"reap:{child.pid}:{type(error).__name__}")
        for path in (settings, config):
            try:
                path.unlink(missing_ok=True)
            except OSError as error:
                cleanup_errors.append(f"credential_cleanup:{type(error).__name__}")
        try:
            scratch.cleanup()
        except OSError as error:
            cleanup_errors.append(f"scratch_cleanup:{type(error).__name__}")
        if cleanup_errors:
            result.update(state="failed", exit_code=1, cleanup_errors=cleanup_errors)
        result["browser_summary"] = _safe_browser_summary(output / "observations.json")
        result["seconds"] = time.monotonic() - started
        (output / "command-result.json").write_text(json.dumps(result, indent=2) + "\n")
    if interrupted is not None:
        raise interrupted
    print(json.dumps(result))
    return result["exit_code"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile", choices=("full", "background", "lifecycle", "movie"), default="full")
    arguments = parser.parse_args()
    selected = arguments.output
    if selected is None:
        parent = Path(__file__).resolve().parents[1] / ".pytest_cache" / "live-jupyter"
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # run() creates this unique directory atomically with exist_ok=False.
        # Neither a previous receiving result nor caller output is reused.
        selected = parent / f"capture-{secrets.token_hex(12)}"
    raise SystemExit(run(selected.resolve(), profile=arguments.profile))
