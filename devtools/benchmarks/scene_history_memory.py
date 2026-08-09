"""Measure the retained cost of the 25-entry scene history.

The ordinary case uses the small representative molecular fixture. The literal
overlay case uses the 100k-atom solvated fixture and installs one explicit base
colour per atom before recording selection changes. The colour map is assigned
directly because this benchmark measures snapshot retention, not palette
generation; every checkpoint still passes through the production
``export_state()`` path.

Each case runs in a fresh worker so allocator history from one case cannot be
reported as retained memory in the other.

Examples
--------
python devtools/benchmarks/scene_history_memory.py
python devtools/benchmarks/scene_history_memory.py --case literal-overlay
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from devtools.benchmarks.representative_scale_gate import build_representative_molsys
from molsysviewer import MolSysView


MIB = 1024 * 1024
HISTORY_LIMIT = 25


def _current_rss_bytes() -> int:
    resident_pages = int(Path("/proc/self/statm").read_text().split()[1])
    return resident_pages * os.sysconf("SC_PAGE_SIZE")


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def run_worker(case: str) -> dict:
    scale_case = "small" if case == "ordinary" else "large"
    molsys = build_representative_molsys(scale_case, 1)
    view = MolSysView()
    view.widget.send = lambda *args, **kwargs: None
    view.load(molsys, skip_digestion=True)

    if case == "literal-overlay":
        # Model an already-created literal layer. History cost is paid when the
        # following public mutations snapshot it through export_state().
        atom_count = int(molsys.get_n_atoms())
        view._atom_color_layers["whole"] = {  # noqa: SLF001
            index: (index * 2654435761) & 0xFFFFFF
            for index in range(atom_count)
        }

    view.history.clear()
    gc.collect()
    rss_before = _current_rss_bytes()
    started = time.perf_counter()
    for index in range(HISTORY_LIMIT):
        view.active_selection.set(
            [index % int(molsys.get_n_atoms())],
            syntax="Indices",
            skip_digestion=True,
        )
    checkpoint_ms = (time.perf_counter() - started) * 1000
    gc.collect()
    rss_with_history = _current_rss_bytes()
    serialized_bytes = sum(
        len(snapshot) for snapshot in view.history._undo  # noqa: SLF001
    )
    history_depth = len(view.history._undo)  # noqa: SLF001

    view.history.clear()
    gc.collect()
    rss_after_clear = _current_rss_bytes()
    depth_after_clear = len(view.history._undo)  # noqa: SLF001
    view.close()

    return {
        "schema_version": 1,
        "case": case,
        "atoms": int(molsys.get_n_atoms()),
        "snapshots": HISTORY_LIMIT,
        "history_depth": history_depth,
        "history_depth_after_clear": depth_after_clear,
        "timings_ms": {"record_25": checkpoint_ms},
        "snapshot_bytes": serialized_bytes,
        "rss_mib": {
            "before": rss_before / MIB,
            "with_history": rss_with_history / MIB,
            "peak": max(_peak_rss_bytes(), rss_with_history) / MIB,
            "retained_growth": (rss_with_history - rss_before) / MIB,
            "after_clear": rss_after_clear / MIB,
            "released_after_clear": (rss_with_history - rss_after_clear) / MIB,
        },
    }


def _summary(samples: list[dict]) -> dict:
    def summarize(path: tuple[str, ...]) -> dict:
        values = []
        for sample in samples:
            value = sample
            for key in path:
                value = value[key]
            values.append(float(value))
        median = statistics.median(values)
        return {
            "median": median,
            "mad": statistics.median(abs(value - median) for value in values),
            "min": min(values),
            "max": max(values),
        }

    return {
        "schema_version": 1,
        "case": samples[0]["case"],
        "atoms": samples[0]["atoms"],
        "snapshots": HISTORY_LIMIT,
        "repeats": len(samples),
        "snapshot_bytes": samples[0]["snapshot_bytes"],
        "timings_ms": {"record_25": summarize(("timings_ms", "record_25"))},
        "rss_mib": {
            key: summarize(("rss_mib", key))
            for key in samples[0]["rss_mib"]
        },
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("ordinary", "literal-overlay"), action="append")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    cases = args.case or ["ordinary", "literal-overlay"]
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    if args.worker:
        if len(cases) != 1:
            parser.error("a worker requires exactly one --case")
        print(json.dumps(run_worker(cases[0]), sort_keys=True))
        return 0

    for case in cases:
        samples = []
        for _ in range(args.repeats):
            completed = subprocess.run(
                [sys.executable, __file__, "--case", case, "--worker"],
                check=True,
                capture_output=True,
                text=True,
            )
            samples.append(json.loads(completed.stdout.splitlines()[-1]))
        print(json.dumps(_summary(samples), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
