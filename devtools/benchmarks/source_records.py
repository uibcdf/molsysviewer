"""Measure cold source binding and cached metadata on a real demo trajectory.

Run with the project's development interpreter; prints JSON. Allocation tracing
covers additional Python allocations after coordinates are already resident,
not total RSS or a supported-system ceiling.
"""
import json
import statistics
import time
import tracemalloc

import molsysviewer as msv


def main():
    source = msv.demo["pentalanine"].molsys
    with msv.new_view() as view:
        view.load([source, source], multiple=True, structure_pairing="by_index", labels=["A", "B"])
        view._source_binding_memo = None
        tracemalloc.start()
        started = time.perf_counter()
        metadata = view._export_source_state()
        cold = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memo = view._source_binding_memo
        timings = []
        for _ in range(20):
            started = time.perf_counter()
            current = view._export_source_state()
            timings.append(time.perf_counter() - started)
            assert view._source_binding_memo is memo and current == metadata
        print(json.dumps({
            "n_atoms": view.molsys.get_n_atoms(), "n_structures": view.molsys.structures.n_structures,
            "n_sources": len(view.load_blocks), "metadata_bytes": len(json.dumps(metadata).encode()),
            "cold_seconds_with_allocation_tracing": cold, "additional_python_peak_bytes": peak,
            "cached_median_seconds": statistics.median(timings), "cached_max_seconds": max(timings),
            "cached_samples": len(timings), "cache_reused": True,
            "boundary": "Resident demo coordinates; no RSS, hard ceiling, session-I/O or installed-provider claim.",
        }, indent=2))


if __name__ == "__main__":
    main()
