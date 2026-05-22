import pytest
import molsysviewer as msv

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
