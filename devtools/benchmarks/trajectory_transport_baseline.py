from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import molsysmt as msm

from molsysviewer.loaders.load_molsysmt import _serialize_molsys_payload
from molsysviewer.systems import systems


CASES = {
    "dialanine-1": ("dialanine", 1),
    "pentalanine-100": ("pentalanine", 100),
    "pentalanine-1000": ("pentalanine", 1000),
    "pentalanine-5000": ("pentalanine", 5000),
    "villin-1": ("chicken_villin_HP35", 1),
}


def _peak_rss_mb() -> float:
    """Process high-water mark. Monotonic: it never falls when memory is freed."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return float(rss) / (1024.0 if sys.platform != "darwin" else 1024.0 * 1024.0)


def _current_rss_mb() -> float:
    """Resident set size *right now*, which does fall when memory is released.

    The peak alone cannot separate transient transfer cost from what a viewer
    keeps resident, so D3 needs both numbers. Returns 0.0 where the platform
    exposes no cheap current-RSS source.
    """
    try:
        with open("/proc/self/statm", "r", encoding="utf-8") as handle:
            resident_pages = int(handle.read().split()[1])
        return resident_pages * os.sysconf("SC_PAGE_SIZE") / (1024.0 * 1024.0)
    except (OSError, IndexError, ValueError):
        return 0.0


def _rss_mb() -> float:  # backwards-compatible alias for the D0 baseline
    return _peak_rss_mb()


def _timed(call):
    started = time.perf_counter()
    value = call()
    return value, (time.perf_counter() - started) * 1000.0


def _safe_atom_attribute(molsys, **kwargs):
    try:
        return msm.get(molsys, element="atom", skip_digestion=True, **kwargs)
    except Exception:
        return None


def _case_payload(case_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    system_name, frame_count = CASES[case_name]
    source = getattr(systems, system_name).path
    structure_indices: str | list[int] = "all"
    if frame_count > 1:
        structure_indices = list(range(frame_count))

    gc.collect()
    rss_before_mb = _peak_rss_mb()
    current_rss_before_mb = _current_rss_mb()

    molsys, convert_ms = _timed(
        lambda: msm.convert(
            source,
            to_form="molsysmt.MolSys",
            structure_indices=structure_indices,
        )
    )
    viewer_json, viewer_json_ms = _timed(
        lambda: molsys.to_form("molsysmt.ViewerJSON")
    )

    def hierarchy_columns():
        return {
            "molecule_indices": _safe_atom_attribute(molsys, molecule_index=True),
            "component_indices": _safe_atom_attribute(molsys, component_index=True),
            "molecule_names": _safe_atom_attribute(molsys, molecule_name=True),
            "component_names": _safe_atom_attribute(molsys, component_name=True),
            "group_types": _safe_atom_attribute(molsys, group_type=True),
        }

    hierarchy, hierarchy_ms = _timed(hierarchy_columns)
    payload, normalize_ms = _timed(
        lambda: _serialize_molsys_payload(viewer_json, **hierarchy)
    )
    if payload is None:
        raise RuntimeError(f"{case_name}: MolSysViewer payload serialization failed")

    message = {
        "op": "load_molsys_payload",
        "payload": payload,
        "label": case_name,
        "multiple_structures": frame_count > 1,
    }
    payload_text, json_ms = _timed(
        lambda: json.dumps(message, separators=(",", ":"), allow_nan=False)
    )

    atom_count = len(payload["atoms"]["atom_id"])
    actual_frames = len(payload["structures"])
    if actual_frames != frame_count:
        raise AssertionError(
            f"{case_name}: expected {frame_count} frames, serialized {actual_frames}"
        )
    if any(len(frame["coordinates"]) != atom_count for frame in payload["structures"]):
        raise AssertionError(f"{case_name}: a frame does not match the topology")

    report = {
        "case": case_name,
        "source": str(source),
        "atoms": atom_count,
        "frames": actual_frames,
        "coordinate_values": atom_count * actual_frames * 3,
        "payload_bytes": len(payload_text.encode("utf-8")),
        "timings_ms": {
            "molsysmt_convert": convert_ms,
            "viewer_json_extract": viewer_json_ms,
            "hierarchy_extract": hierarchy_ms,
            "python_list_normalize": normalize_ms,
            "json_encode": json_ms,
        },
        "python_memory_mb": _memory_report(rss_before_mb, current_rss_before_mb),
    }
    return message, report


def _memory_report(peak_before_mb: float, current_before_mb: float) -> dict[str, float]:
    """Separate the transient transfer cost from what stays resident.

    `peak_rss_growth` is what the transfer *cost* at its worst; `retained_growth`
    is what is still resident once the work is done. D3 needs both: a transport
    can be judged good only if the peak is bounded *and* the retained footprint
    matches the science, not the wire format.
    """
    gc.collect()
    current_after_mb = _current_rss_mb()
    return {
        "peak_rss_before": peak_before_mb,
        "peak_rss": _peak_rss_mb(),
        "peak_rss_growth": max(0.0, _peak_rss_mb() - peak_before_mb),
        "current_rss_before": current_before_mb,
        "current_rss_after": current_after_mb,
        "retained_growth": max(0.0, current_after_mb - current_before_mb),
        # How much of the worst-case peak was transient rather than retained.
        "transient_growth": max(
            0.0, (_peak_rss_mb() - peak_before_mb) - max(0.0, current_after_mb - current_before_mb)
        ),
    }


def _worker(case_name: str, output: Path | None) -> None:
    message, report = _case_payload(case_name)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(message, separators=(",", ":"), allow_nan=False),
            encoding="utf-8",
        )
    print(json.dumps(report, sort_keys=True))


def _run_all() -> dict[str, Any]:
    case_reports = []
    script = Path(__file__).resolve()
    for case_name in CASES:
        completed = subprocess.run(
            [sys.executable, str(script), "_worker", "--case", case_name],
            check=True,
            capture_output=True,
            text=True,
        )
        output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not output_lines:
            raise RuntimeError(f"{case_name}: worker produced no report")
        case_reports.append(json.loads(output_lines[-1]))

    return {
        "schema_version": 1,
        "command": f"{sys.executable} {script} run",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor_count": os.cpu_count(),
            "molsysviewer": importlib.metadata.version("molsysviewer"),
            "molsysmt": importlib.metadata.version("molsysmt"),
            "numpy": importlib.metadata.version("numpy"),
        },
        "cases": case_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure the current JSON trajectory transport preparation path."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run")

    worker = subparsers.add_parser("_worker")
    worker.add_argument("--case", choices=CASES, required=True)
    worker.add_argument("--output", type=Path)

    emit = subparsers.add_parser("emit-payload")
    emit.add_argument("--case", choices=CASES, default="pentalanine-5000")
    emit.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "run":
        print(json.dumps(_run_all(), indent=2, sort_keys=True))
        return
    if args.command in {"_worker", "emit-payload"}:
        _worker(args.case, args.output)
        return
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    main()
