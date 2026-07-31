"""D0 for the Qt standalone transport.

The AnyWidget connector was measured before it was optimized, and the planar
layout came out of looking at the numbers rather than at intuition. Qt is in
scope for 1.0 and has never been measured, so this is its baseline.

What Qt does today for a large structure: `_materialize_payload_ref` serializes
the molecular payload to JSON text, keeps those bytes in memory, and rewrites the
message to `load_molsys_payload_ref` pointing at a `molsysviewer-payload://`
URL. The page then fetches that URL and receives `application/json`.

The candidate is to serve the same generation as `application/octet-stream`
through the *same* scheme handler, which the transport diagnostic already proved
works with `fetch`. So the question this measures is not which mechanism to use
— the project already chose and validated it — but whether binary is worth it on
Qt at all.

Browser-side decode needs a real Qt window with WebGL and is deliberately out of
scope here; this measures the Python side, which is where the JSON path spends
its time and memory.

    python devtools/benchmarks/qt_transport_baseline.py
    python devtools/benchmarks/qt_transport_baseline.py --case pentalanine-5000
"""

import argparse
import gc
import json
import os
import resource
import sys
import time
from pathlib import Path

import molsysmt as msm

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer.loaders.array_native_molsys import (  # noqa: E402
    serialize_array_native_molsys,
)
from molsysviewer.loaders.load_molsysmt import _serialize_molsys_payload  # noqa: E402

CASES = {
    "pentalanine-1000": (("pentalanine", "traj_pentalanine.h5msm"), 1000),
    "pentalanine-5000": (("pentalanine", "traj_pentalanine.h5msm"), 5000),
}


def _current_rss_mb() -> float:
    try:
        with open("/proc/self/statm", "r", encoding="utf-8") as handle:
            pages = int(handle.read().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") / (1024.0 * 1024.0)
    except (OSError, IndexError, ValueError):
        return 0.0


def _peak_rss_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return float(rss) / (1024.0 if sys.platform != "darwin" else 1024.0 * 1024.0)


def _timed(call):
    started = time.perf_counter()
    value = call()
    return value, (time.perf_counter() - started) * 1000.0


def _atom_attribute(molsys, **kwargs):
    try:
        return msm.get(molsys, element="atom", skip_digestion=True, **kwargs)
    except Exception:
        return None


def measure(case_name: str) -> dict:
    (system_name, resource_name), frame_count = CASES[case_name]
    source = msm.systems[system_name][resource_name]
    structure_indices = list(range(frame_count)) if frame_count > 1 else "all"

    gc.collect()
    rss_before = _current_rss_mb()
    peak_before = _peak_rss_mb()

    molsys, convert_ms = _timed(
        lambda: msm.convert(
            source, to_form="molsysmt.MolSys", structure_indices=structure_indices
        )
    )

    # --- what Qt does today -------------------------------------------------
    viewer_json, viewer_json_ms = _timed(lambda: molsys.to_form("molsysmt.ViewerJSON"))
    payload, payload_ms = _timed(
        lambda: _serialize_molsys_payload(
            viewer_json,
            molecule_indices=_atom_attribute(molsys, molecule_index=True),
            component_indices=_atom_attribute(molsys, component_index=True),
            molecule_names=_atom_attribute(molsys, molecule_name=True),
            component_names=_atom_attribute(molsys, component_name=True),
            group_types=_atom_attribute(molsys, group_type=True),
        )
    )
    # `_materialize_payload_ref` serializes and keeps these bytes resident until
    # the page fetches the URL.
    payload_bytes, json_ms = _timed(
        lambda: json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    json_total_ms = viewer_json_ms + payload_ms + json_ms
    json_peak = _peak_rss_mb()

    # --- the candidate ------------------------------------------------------
    array_payload, array_ms = _timed(lambda: serialize_array_native_molsys(molsys))
    array_bytes = sum(array.nbytes for array in array_payload.arrays)
    metadata_bytes = len(
        json.dumps(
            {k: v for k, v in array_payload.metadata.items() if k != "structural_arrays"},
            separators=(",", ":"),
        ).encode("utf-8")
    )

    gc.collect()
    return {
        "case": case_name,
        "atoms": int(molsys.get_n_atoms()),
        "structures": int(molsys.structures.n_structures),
        "qt_json": {
            "wire_bytes": len(payload_bytes),
            "prepare_ms": round(json_total_ms, 1),
            "breakdown_ms": {
                "viewer_json": round(viewer_json_ms, 1),
                "payload_normalize": round(payload_ms, 1),
                "json_encode": round(json_ms, 1),
            },
        },
        "array_native": {
            "wire_bytes": array_bytes + metadata_bytes,
            "prepare_ms": round(array_ms, 1),
        },
        "ratios": {
            "bytes_json_over_binary": round(
                len(payload_bytes) / max(1, array_bytes + metadata_bytes), 1
            ),
            "prepare_json_over_binary": round(json_total_ms / max(0.001, array_ms), 1),
        },
        "python_memory_mb": {
            "convert_ms": round(convert_ms, 1),
            "rss_before": round(rss_before, 1),
            "peak_after_json": round(json_peak, 1),
            "peak_growth": round(max(0.0, json_peak - peak_before), 1),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    args = parser.parse_args()
    for case in args.case or ["pentalanine-1000", "pentalanine-5000"]:
        print(json.dumps(measure(case), sort_keys=True))


if __name__ == "__main__":
    main()
