from __future__ import annotations

import json
import time
from typing import Any
import numpy as np

from smonitor import get_manager
from molsysviewer.demo import demo

def benchmark_loading(iterations: int = 5) -> dict[str, dict[str, float]]:
    """Measure structure and topology loading speed from demo h5msm files."""
    results = {}
    keys = ["dialanine", "1TCD", "chicken_villin_HP35"]
    
    for key in keys:
        timings = []
        for _ in range(iterations):
            start = time.perf_counter()
            # demo access always returns a fresh view loaded from h5msm file
            view = demo[key]
            # Ensure it actually loaded
            assert view._molsys is not None
            timings.append((time.perf_counter() - start) * 1000.0)  # ms
        
        results[key] = {
            "min": float(np.min(timings)),
            "max": float(np.max(timings)),
            "mean": float(np.mean(timings)),
            "std": float(np.std(timings)),
        }
    return results

def benchmark_coordinates(iterations: int = 50) -> dict[str, dict[str, float]]:
    """Measure coordinate serialization (get) and deserialization/update (set) performance."""
    view_small = demo["dialanine"]
    view_large = demo["chicken_villin_HP35"]
    
    results = {}
    
    # Small system (dialanine)
    get_small_timings = []
    set_small_timings = []
    coords_small = view_small.get_coordinates(skip_digestion=True)
    
    for _ in range(iterations):
        start = time.perf_counter()
        _ = view_small.get_coordinates(skip_digestion=True)
        get_small_timings.append((time.perf_counter() - start) * 1000.0)
        
        start = time.perf_counter()
        view_small.set_coordinates(coords_small, skip_digestion=True)
        set_small_timings.append((time.perf_counter() - start) * 1000.0)
        
    results["dialanine_get"] = {
        "min": float(np.min(get_small_timings)),
        "max": float(np.max(get_small_timings)),
        "mean": float(np.mean(get_small_timings)),
        "std": float(np.std(get_small_timings)),
    }
    results["dialanine_set"] = {
        "min": float(np.min(set_small_timings)),
        "max": float(np.max(set_small_timings)),
        "mean": float(np.mean(set_small_timings)),
        "std": float(np.std(set_small_timings)),
    }
    
    # Large/trajectory system (chicken_villin_HP35)
    get_large_timings = []
    set_large_timings = []
    coords_large = view_large.get_coordinates(skip_digestion=True)
    
    for _ in range(iterations):
        start = time.perf_counter()
        _ = view_large.get_coordinates(skip_digestion=True)
        get_large_timings.append((time.perf_counter() - start) * 1000.0)
        
        start = time.perf_counter()
        view_large.set_coordinates(coords_large, skip_digestion=True)
        set_large_timings.append((time.perf_counter() - start) * 1000.0)
        
    results["villin_get"] = {
        "min": float(np.min(get_large_timings)),
        "max": float(np.max(get_large_timings)),
        "mean": float(np.mean(get_large_timings)),
        "std": float(np.std(get_large_timings)),
    }
    results["villin_set"] = {
        "min": float(np.min(set_large_timings)),
        "max": float(np.max(set_large_timings)),
        "mean": float(np.mean(set_large_timings)),
        "std": float(np.std(set_large_timings)),
    }
    
    return results

def benchmark_serialization(iterations: int = 100) -> dict[str, dict[str, float]]:
    """Measure JSON serialization latency for typical high-frequency payloads."""
    # Camera snapshot payload
    camera_payload = {
        "op": "set_camera_snapshot",
        "snapshot": {
            "target": [0.123, -4.56, 12.78],
            "position": [45.1, -12.3, 100.5],
            "up": [0.0, 1.0, 0.0],
            "radius": 24.5,
        },
        "duration_ms": 250,
    }
    
    # High-frequency coordinates payload (500 atoms)
    coords_list = [[1.234, -5.678, 12.345] for _ in range(500)]
    coords_payload = {
        "op": "partial_coordinates_update",
        "coordinates": coords_list,
        "atom_indices": list(range(500)),
        "transaction_id": "benchmark-serialization",
    }
    
    results = {}
    for name, payload in [("camera_snapshot", camera_payload), ("coordinates_500atoms", coords_payload)]:
        timings = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = json.dumps(payload)
            timings.append((time.perf_counter() - start) * 1000.0)  # ms
            
        results[name] = {
            "min": float(np.min(timings)),
            "max": float(np.max(timings)),
            "mean": float(np.mean(timings)),
            "std": float(np.std(timings)),
        }
    return results

def benchmark_telemetry_overhead(iterations: int = 50) -> dict[str, Any]:
    """Measure CPU overhead introduced by SMonitor tracking and ArgDigest validation."""
    view = demo["dialanine"]
    
    # Sequence of high-frequency operations
    def run_sequence(skip_digestion: bool) -> None:
        # 1. new_region
        reg = view.new_region(
            atom_indices=[0, 1, 2],
            tag="bench_reg",
            representation="sticks",
            skip_digestion=skip_digestion,
        )
        # 2. zoom
        view.zoom(selection="all", skip_digestion=skip_digestion)
        # 3. get_camera_snapshot
        snap = view.get_camera_snapshot(skip_digestion=skip_digestion)
        # 4. set_camera_snapshot
        if isinstance(snap, dict):
            view.set_camera_snapshot(snap, skip_digestion=skip_digestion)
        # 5. clean up
        reg.delete(skip_digestion=skip_digestion)
    
    manager = get_manager()
    original_smonitor_enabled = manager.config.enabled
    
    configs = [
        ("Baseline (None)", False, True),
        ("SMonitor-only", True, True),
        ("ArgDigest-only", False, False),
        ("Full Telemetry", True, False),
    ]
    
    runs = {}
    
    try:
        for name, sm_enabled, skip_dig in configs:
            manager.configure(enabled=sm_enabled)
            
            # Warm up
            for _ in range(3):
                run_sequence(skip_digestion=skip_dig)
                
            timings = []
            for _ in range(iterations):
                start = time.perf_counter()
                run_sequence(skip_digestion=skip_dig)
                timings.append((time.perf_counter() - start) * 1000.0)  # ms
                
            runs[name] = {
                "min": float(np.min(timings)),
                "max": float(np.max(timings)),
                "mean": float(np.mean(timings)),
                "std": float(np.std(timings)),
                "raw": timings,
            }
    finally:
        # Restore original state
        manager.configure(enabled=original_smonitor_enabled)
        
    # Calculate overheads relative to baseline
    baseline_mean = runs["Baseline (None)"]["mean"]
    
    for name in ["SMonitor-only", "ArgDigest-only", "Full Telemetry"]:
        mean = runs[name]["mean"]
        diff = mean - baseline_mean
        pct = (diff / baseline_mean) * 100.0 if baseline_mean > 0 else 0.0
        runs[name]["overhead_ms"] = float(diff)
        runs[name]["overhead_pct"] = float(pct)
        
    return runs

def run_benchmarks(iterations: int = 50, verbose: bool = True) -> str:
    """Execute the full molecular performance benchmark suite and return a Markdown report."""
    if verbose:
        print(f"Starting MolSysViewer Performance Benchmarks ({iterations} iterations)...")
        
    # 1. Loading speeds (we do a max of 5 loads per system to keep it reasonably fast)
    if verbose:
        print("  - Running Topology/Structure Loading benchmarks...")
    load_iters = min(iterations, 5)
    load_results = benchmark_loading(iterations=load_iters)
    
    # 2. Coordinates transfers
    if verbose:
        print("  - Running Coordinates Transfer benchmarks...")
    coords_results = benchmark_coordinates(iterations=iterations)
    
    # 3. Serialization latency
    if verbose:
        print("  - Running JSON Serialization benchmarks...")
    serial_results = benchmark_serialization(iterations=iterations)
    
    # 4. Telemetry overheads
    if verbose:
        print("  - Running Telemetry & Validation Overhead benchmarks...")
    telemetry_results = benchmark_telemetry_overhead(iterations=iterations)
    
    # Formulate markdown output
    lines = []
    lines.append("# MolSysViewer Performance Benchmark Report")
    lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Iterations: {iterations} (Loading: {load_iters})")
    lines.append("")
    
    # Table 1: Topology Loading
    lines.append("## 📦 1. Topology & Structure Loading Speed")
    lines.append("Measures fresh file loading duration (H5MSM structure files from demo package).")
    lines.append("")
    lines.append("| System | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for key, stats in load_results.items():
        lines.append(f"| `{key}` | {stats['min']:.2f} | {stats['max']:.2f} | {stats['mean']:.2f} | {stats['std']:.2f} |")
    lines.append("")
    
    # Table 2: Coordinates Transfer
    lines.append("## 🔄 2. Coordinate Transfer Performance")
    lines.append("Measures coordinate extraction (`get_coordinates`) and replacement/scene-rebuild (`set_coordinates`).")
    lines.append("")
    lines.append("| Operation | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for op, stats in coords_results.items():
        lines.append(f"| `{op}` | {stats['min']:.2f} | {stats['max']:.2f} | {stats['mean']:.2f} | {stats['std']:.2f} |")
    lines.append("")
    
    # Table 3: JSON Serialization
    lines.append("## ⚡ 3. JSON Serialization Latency")
    lines.append("Measures serialization cost (`json.dumps`) of representative outbound WebSocket payloads.")
    lines.append("")
    lines.append("| Payload Type | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for name, stats in serial_results.items():
        lines.append(f"| `{name}` | {stats['min']:.4f} | {stats['max']:.4f} | {stats['mean']:.4f} | {stats['std']:.4f} |")
    lines.append("")
    
    # Table 4: Telemetry Overhead
    lines.append("## 🚀 4. Telemetry & Validation Overhead")
    lines.append("Measures overhead on a sequence of API calls (`new_region`, `zoom`, `get_camera_snapshot`, `set_camera_snapshot`).")
    lines.append("")
    lines.append("| Telemetry Configuration | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) | Overhead (ms) | Slowdown (%) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    baseline = telemetry_results["Baseline (None)"]
    lines.append(f"| `Baseline (None)` | {baseline['min']:.2f} | {baseline['max']:.2f} | {baseline['mean']:.2f} | {baseline['std']:.2f} | — | — |")
    
    for name in ["SMonitor-only", "ArgDigest-only", "Full Telemetry"]:
        stats = telemetry_results[name]
        lines.append(
            f"| `{name}` | {stats['min']:.2f} | {stats['max']:.2f} | {stats['mean']:.2f} | {stats['std']:.2f} | "
            f"+{stats['overhead_ms']:.2f} | {stats['overhead_pct']:.1f}% |"
        )
    lines.append("")
    
    report = "\n".join(lines)
    if verbose:
        print("Benchmarks complete!")
    return report
