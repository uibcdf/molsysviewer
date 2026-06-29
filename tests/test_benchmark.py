import pytest
import molsysviewer as msv
from molsysviewer.tools import benchmark as benchmark_module

def test_benchmark_smoke():
    """Verify that the benchmarking suite executes successfully with a few iterations."""
    # Run the benchmark suite with 2 iterations to keep it fast
    report = msv.tools.run_benchmarks(iterations=2, verbose=True)
    
    assert isinstance(report, str)
    assert "# MolSysViewer Performance Benchmark Report" in report
    assert "1. Topology & Structure Loading Speed" in report
    assert "2. Coordinate Transfer Performance" in report
    assert "3. JSON Serialization Latency" in report
    assert "4. Telemetry & Validation Overhead" in report
    assert "dialanine" in report
    assert "chicken_villin_HP35" in report
    assert "Baseline (None)" in report
    assert "SMonitor-only" in report
    assert "ArgDigest-only" in report
    assert "Full Telemetry" in report

def test_benchmark_serialization_uses_live_coordinate_update_contract(monkeypatch):
    payloads = []

    def fake_dumps(payload):
        payloads.append(payload)
        return "{}"

    monkeypatch.setattr(benchmark_module.json, "dumps", fake_dumps)

    result = benchmark_module.benchmark_serialization(iterations=1)

    assert "coordinates_500atoms" in result
    coordinate_payload = next(payload for payload in payloads if payload.get("op") == "partial_coordinates_update")
    assert coordinate_payload["coordinates"]
    assert coordinate_payload["atom_indices"] == list(range(500))
    assert coordinate_payload["transaction_id"] == "benchmark-serialization"
    assert all(payload.get("op") != "update_coordinates" for payload in payloads)
