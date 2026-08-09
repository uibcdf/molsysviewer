"""Item 8 of the transport audit: copies and peak memory in the Qt binary scheme.

`qt_transport_baseline.py` established that binary is worth it on Qt at all — it
measured wire bytes and preparation time. It did not measure what the audit
asked about: Qt's bridge assembles the structural buffers into **one Python
`bytes` object** before Chromium consumes it,

    blob = b"".join(bytes(buffer) for buffer in payload.buffers)

and a full transient copy of a large system is the kind of cost that never shows
up in a timing. AnyWidget hands the same buffers to its connector without
joining, so the two connectors differ here by construction.

**Measured with `tracemalloc`, not RSS.** RSS answers a different question: the
allocator keeps freed arenas, so a released copy leaves no trace — the first
draft of this benchmark reported the same "retained" figure before and after
`del blob`, which is a property of the allocator and not of the code under test.
`tracemalloc` tracks Python allocations, so a transient copy is visible as a peak
above the final size, which is exactly the claim being tested. RSS is still
reported alongside, labelled for what it is worth.

Cases are real systems for grounding and synthetic buffers for scale. The
synthetic ones exercise the join itself at sizes the shipped demo systems do not
reach, which is legitimate because the join knows nothing about molecules.

    python devtools/benchmarks/qt_payload_copies.py
    python devtools/benchmarks/qt_payload_copies.py --case 4v4z --case synthetic-200mb
"""

import argparse
import gc
import json
import resource
import sys
import tracemalloc
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_PAGE_SIZE = 4096


def _current_rss_mb() -> float:
    with open("/proc/self/statm", "r", encoding="utf-8") as handle:
        return int(handle.read().split()[1]) * _PAGE_SIZE / (1024.0 * 1024.0)


def _peak_rss_mb() -> float:
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def _preallocated_metrics(buffers) -> dict:
    """The candidate: copy each buffer into one preallocated `bytearray`.

    Measured rather than assumed, because the audit's rule is to change this path
    only if a lower-copy alternative exists *and* the peak is release-relevant.
    """
    total = sum(len(memoryview(b).cast("B")) for b in buffers)
    gc.collect()
    tracemalloc.start()

    out = bytearray(total)
    offset = 0
    for buffer in buffers:
        view = memoryview(buffer).cast("B")
        out[offset:offset + len(view)] = view
        offset += len(view)

    _, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    size = len(out)
    del out
    gc.collect()
    mb = 1024.0 * 1024.0
    return {
        "prealloc_peak_mb": round(traced_peak / mb, 2),
        "prealloc_overhead_mb": round(max(0.0, traced_peak - size) / mb, 2),
    }


def _join_metrics(buffers, label: str, extra: dict) -> dict:
    """Run the bridge's join under measurement and report what it cost."""
    total_bytes = sum(len(memoryview(b).cast("B")) for b in buffers)

    gc.collect()
    rss_before = _current_rss_mb()
    peak_rss_before = _peak_rss_mb()
    tracemalloc.start()

    # Exactly what `QtMessageBridge._materialize_payload_ref` does.
    blob = b"".join(bytes(buffer) for buffer in buffers)

    traced_current, traced_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_rss_after = _peak_rss_mb()
    blob_bytes = len(blob)
    del blob
    gc.collect()

    mb = 1024.0 * 1024.0
    return {
        "case": label,
        **extra,
        "buffers": len(buffers),
        "arrays_mb": round(total_bytes / mb, 2),
        "blob_mb": round(blob_bytes / mb, 2),
        # One `bytes(buffer)` per buffer, plus the join's own output.
        "copies": len(buffers) + 1,
        "traced_peak_mb": round(traced_peak / mb, 2),
        "traced_after_mb": round(traced_current / mb, 2),
        # How much more than the blob itself was alive at the worst moment.
        "transient_overhead_mb": round(max(0.0, traced_peak - blob_bytes) / mb, 2),
        "rss_before_mb": round(rss_before, 1),
        "peak_rss_growth_mb": round(max(0.0, peak_rss_after - peak_rss_before), 2),
        **_preallocated_metrics(buffers),
    }


def _real_case(label: str, system_name: str, resource_name: str, n_structures) -> dict:
    import molsysmt as msm

    from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys

    source = msm.systems[system_name][resource_name]
    structure_indices = (
        "all" if n_structures == "all" else list(range(int(n_structures)))
    )
    molsys = msm.convert(
        source, to_form="molsysmt.MolSys", structure_indices=structure_indices
    )
    payload = serialize_array_native_molsys(molsys)
    return _join_metrics(
        payload.buffers,
        label,
        {
            "n_atoms": int(payload.metadata["n_atoms"]),
            "n_structures": int(payload.metadata["n_structures"]),
            "synthetic": False,
        },
    )


def _representative_case(label: str, scale_case: str, n_structures: int) -> dict:
    from devtools.benchmarks.representative_scale_gate import build_representative_molsys
    from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys

    molsys = build_representative_molsys(scale_case, n_structures)
    payload = serialize_array_native_molsys(molsys)
    return _join_metrics(
        payload.buffers,
        label,
        {
            "n_atoms": int(payload.metadata["n_atoms"]),
            "n_structures": int(payload.metadata["n_structures"]),
            "synthetic": False,
        },
    )


def _synthetic_case(label: str, megabytes: int, buffers: int = 3) -> dict:
    per_buffer = int(megabytes * 1024 * 1024 / buffers / 4)
    arrays = [np.zeros(per_buffer, dtype=np.float32) for _ in range(buffers)]
    return _join_metrics(
        [memoryview(array).cast("B") for array in arrays],
        label,
        {"n_atoms": None, "n_structures": None, "synthetic": True},
    )


CASES: dict[str, callable] = {
    "pentalanine-5000": lambda: _real_case(
        "pentalanine-5000", "pentalanine", "traj_pentalanine.h5msm", "all"
    ),
    "4v4z": lambda: _real_case("4v4z", "4V4Z", "4v4z.bcif.gz", "all"),
    "representative-large-100": lambda: _representative_case(
        "representative-large-100", "large", 100
    ),
    "representative-xlarge-10": lambda: _representative_case(
        "representative-xlarge-10", "xlarge", 10
    ),
    "synthetic-50mb": lambda: _synthetic_case("synthetic-50mb", 50),
    "synthetic-200mb": lambda: _synthetic_case("synthetic-200mb", 200),
    "synthetic-800mb": lambda: _synthetic_case("synthetic-800mb", 800),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    args = parser.parse_args()
    for case in args.case or ["pentalanine-5000", "4v4z", "synthetic-50mb", "synthetic-200mb"]:
        print(json.dumps(CASES[case](), sort_keys=True))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
