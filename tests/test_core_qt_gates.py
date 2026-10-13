"""Exercise actual pytest selection and fail-closed core qualification (#231)."""

import subprocess
import sys
from pathlib import Path

import yaml
from devtools import ci_backlog

ROOT = Path(__file__).resolve().parents[1]
QT_PROBES = {
    "test_qt_event_transport_smoke_real_qt",
    "test_qt_payload_refs_replace_across_two_real_generations",
    "test_qt_live_model_smoke_real_window",
    "test_qt_live_model_full_render_gpu",
}


def collect(expression):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_standalone.py",
            "tests/test_qt_probe_resources.py",
            "tests/test_headless_export_resources.py",
            "--collect-only",
            "--strict-markers",
            "-o",
            "addopts=--doctest-modules",
            "-q",
            "-m",
            expression,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {line for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line}


def test_actual_core_and_qt_collection_keep_contract_and_chromium_checks():
    core = collect("not qt_runtime")
    qt = collect("qt_runtime")
    assert len(qt) == 12
    assert not core & qt
    assert {node.split("::", 1)[1] for node in qt if "test_standalone.py::" in node} == QT_PROBES
    assert all("test_qt_probe_resources.py::" in node or "test_standalone.py::" in node for node in qt)
    assert any("test_qt_view_channel_close_only_detaches_its_own_event_sink" in node for node in core)
    assert any("test_qt_message_bridge_materializes_large_payload_refs" in node for node in core)
    assert any("test_real_png_export_from_read_only_package" in node for node in core)
    assert not any("test_qt_probe_resources.py::" in node for node in core)


def test_workflows_use_the_same_scope_and_keep_qt_failure_visible():
    workflow_root = ROOT / ".github/workflows"
    def load(name):
        return yaml.load((workflow_root / name).read_text(), Loader=yaml.BaseLoader)
    ci = load("CI.yaml")
    qt = load("CI_qt_experimental.yaml")
    pair = load("ci-python-314-source-pair.yaml")
    core_command = next(step["run"] for step in ci["jobs"]["test"]["steps"] if step.get("name") == "Run tests")
    assert '-m "not qt_runtime"' in core_command
    assert '-m "not qt_runtime"' in next(
        step["run"]
        for job in pair["jobs"].values()
        for step in job.get("steps", [])
        if step.get("name") == "Run MolSysViewer Python tests"
    )
    assert set(ci["jobs"]["pr-gate"]["needs"]) == {"test"}
    assert 'test "$TEST_RESULT" = success' in ci["jobs"]["pr-gate"]["steps"][0]["run"]
    for job in qt["jobs"].values():
        assert job.get("continue-on-error", "false") == "false"
    diagnostics = [step for step in qt["jobs"]["qt-pipeline"]["steps"] if "python -m pytest" in step.get("run", "")]
    assert len(diagnostics) == 3
    for step in diagnostics:
        assert "-m qt_runtime" in step["run"]
        assert "always()" in step["if"]
        assert step.get("continue-on-error", "false") == "false"
        assert "|| true" not in step["run"]


def test_unknown_failed_job_never_becomes_an_experimental_exemption(monkeypatch):
    jobs = []
    for os_name in ("ubuntu-latest", "macos-15"):
        for version in ci_backlog.PYTHON_VERSIONS:
            steps = [{"name": "Run tests", "conclusion": "success"}]
            if os_name == "ubuntu-latest" and version == "3.13":
                steps.append({"name": "JS unit tests (Node)", "conclusion": "success"})
            jobs.append({"name": f"Test on {os_name}, Python {version}", "conclusion": "success", "steps": steps})
    jobs.append({"name": "Qt pipeline completes (Xvfb, software WebGL)", "conclusion": "failure", "steps": []})
    monkeypatch.setattr(ci_backlog, "api_json", lambda *_: {"jobs": jobs})
    assert ci_backlog.lane_passed("repo", 1, "token", "ci")
    assert not ci_backlog.lane_passed("repo", 1, "token", "qt")
    jobs.append({"name": "Additional required core check", "conclusion": "failure", "steps": []})
    assert not ci_backlog.lane_passed("repo", 1, "token", "ci")
    jobs.pop()
    jobs[0]["steps"][0]["conclusion"] = "skipped"
    assert not ci_backlog.lane_passed("repo", 1, "token", "ci")
