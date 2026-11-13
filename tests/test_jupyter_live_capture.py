"""Explicit live-host receiving; an unselected profile is not passing evidence."""

import json
import os
import runpy
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

import pytest


def _moving_capture_contract_control():
    cases = []
    for scenario, owners in (
        ("default", (("notebook", ("Python",)),)),
        ("delayed", (("notebook", ("Python", "Studio")), ("popup", ("Studio",)))),
    ):
        for origin, methods in owners:
            for method in methods:
                for kind in ("state", "session"):
                    cases.append(
                        {
                            "scenario": scenario,
                            "origin": origin,
                            "method": method,
                            "kind": kind,
                            "request_id": f"{scenario}-{origin}-{method}-{kind}",
                            "uses_public_default": scenario == "default",
                            "requested_timeout_ms": 4999 if scenario == "default" else 9999,
                            "held_real_queries": 0 if scenario == "default" else 2,
                            "frame_changes_after_request": [] if scenario == "default" else [2, 1],
                            "independent_file_restore": True,
                            "source_identity_and_coordinates_unchanged": True,
                        }
                    )
    return {"moving_capture_cases": 8, "moving_cases": cases}


def test_moving_capture_contract_accepts_both_deadline_scopes():
    check = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))["_check_moving_capture_contract"]
    observed = _moving_capture_contract_control()
    original = deepcopy(observed)
    check(observed)
    assert observed == original


@pytest.mark.parametrize(
    "fault",
    [
        "default_scope",
        "delayed_scope",
        "default_deadline",
        "delayed_deadline",
        "frames",
        "restore",
        "source",
        "owner",
        "request",
    ],
)
def test_moving_capture_contract_rejects_missing_scope_or_deadline_drift(fault):
    check = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))["_check_moving_capture_contract"]
    report = _moving_capture_contract_control()
    default, delayed = report["moving_cases"][0], report["moving_cases"][2]
    if fault == "default_scope":
        default["scenario"] = "delayed"
    elif fault == "delayed_scope":
        delayed["scenario"] = "default"
    elif fault == "default_deadline":
        default["requested_timeout_ms"] = 6000
    elif fault == "delayed_deadline":
        delayed["requested_timeout_ms"] = 5000
    elif fault == "frames":
        delayed["frame_changes_after_request"] = [1, 1]
    elif fault == "restore":
        delayed["independent_file_restore"] = False
    elif fault == "source":
        delayed["source_identity_and_coordinates_unchanged"] = False
    elif fault == "owner":
        delayed["origin"] = "another-view"
    else:
        delayed["request_id"] = default["request_id"]
    with pytest.raises(AssertionError):
        check(report)


@pytest.mark.parametrize("kind", ["state", "session"])
def test_safe_browser_summary_names_default_moving_capture(tmp_path, kind):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    phase = f"Moving default Python notebook {kind}"
    report.write_text(json.dumps({"outcome": "failed", "stage": phase, "error_type": "Error"}))
    assert owner["_safe_browser_summary"](report)["phase"] == phase


def test_safe_browser_summary_retains_phase_and_counts_without_raw_diagnostics(tmp_path):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    private = "private-sentinel-do-not-publish"
    report.write_text(
        json.dumps(
            {
                "outcome": "failed",
                "stage": "Studio popup session",
                "error_type": "TimeoutError",
                "capture_restore_cases": 4,
                "strong_restore_cases": 3,
                "studio_cases": 2,
                "error": f"http://127.0.0.1/lab?token={private}",
                "stack": private,
                "records": [{"private": private}],
                "page_errors": [private],
            }
        )
    )
    original = report.read_bytes()
    summary = owner["_safe_browser_summary"](report)
    assert summary == {
        "status": "available",
        "outcome": "failed",
        "phase": "Studio popup session",
        "error_type": "TimeoutError",
        "capture_restore_cases": 4,
        "strong_restore_cases": 3,
        "studio_cases": 2,
    }
    assert private not in json.dumps(summary)
    assert report.read_bytes() == original


@pytest.mark.parametrize("untrusted", ["private-sentinel-do-not-publish", [], {}, None])
def test_safe_browser_summary_rejects_untrusted_names_and_noninteger_counts(tmp_path, untrusted):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    private = "private-sentinel-do-not-publish"
    report.write_text(
        json.dumps(
            {
                "outcome": "failed",
                "stage": untrusted,
                "error_type": untrusted,
                "capture_restore_cases": True,
                "strong_restore_cases": -1,
                "studio_cases": 1_000_000,
            }
        )
    )
    summary = owner["_safe_browser_summary"](report)
    assert summary == {
        "status": "available",
        "outcome": "failed",
        "phase": "unclassified",
        "error_type": "unclassified",
    }
    assert private not in json.dumps(summary)


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b'{"outcome":"in_progress"}',
        b"\xff",
        b'{"outcome":"failed","nested":' + b"[" * 2000 + b"0}",
    ],
    ids=["malformed", "non-object", "nonterminal", "invalid-utf8", "deep-malformed"],
)
def test_safe_browser_summary_reports_invalid_evidence_without_echoing_it(tmp_path, raw):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    report.write_bytes(raw)
    assert owner["_safe_browser_summary"](report) == {"status": "unavailable", "reason": "invalid"}


def test_safe_browser_summary_bounds_input_and_distinguishes_missing_evidence(tmp_path):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    assert owner["_safe_browser_summary"](report) == {"status": "unavailable", "reason": "missing"}
    report.write_bytes(b'{"outcome":"passed"}' + b" " * (1024 * 1024))
    assert owner["_safe_browser_summary"](report) == {"status": "unavailable", "reason": "oversized"}


def test_safe_browser_summary_accepts_completed_receiving_without_a_failure_phase(tmp_path):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    report.write_text(json.dumps({"outcome": "passed", "capture_restore_cases": 4, "studio_cases": 3}))
    assert owner["_safe_browser_summary"](report) == {
        "status": "available",
        "outcome": "passed",
        "capture_restore_cases": 4,
        "studio_cases": 3,
    }


def test_safe_movie_summary_retains_closed_counts_without_kernel_origins(tmp_path):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    report.write_text(
        json.dumps(
            {
                "outcome": "failed",
                "stage": "Movie popup camera",
                "error_type": "AssertionError",
                "movie_authoring_cases": 3,
                "kernel_origin": {"private": "private-sentinel"},
            }
        )
    )
    assert owner["_safe_browser_summary"](report) == {
        "status": "available",
        "outcome": "failed",
        "phase": "Movie popup camera",
        "error_type": "AssertionError",
        "movie_authoring_cases": 3,
    }


def test_safe_browser_summary_retains_moving_scope_without_raw_transport(tmp_path):
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    report = tmp_path / "observations.json"
    private = "private-moving-transport-sentinel"
    report.write_text(
        json.dumps(
            {
                "outcome": "failed",
                "stage": "Moving Studio popup session",
                "error_type": "AssertionError",
                "moving_capture_cases": 5,
                "moving_transport": {"private": private},
                "error": private,
            }
        )
    )
    summary = owner["_safe_browser_summary"](report)
    assert summary == {
        "status": "available",
        "outcome": "failed",
        "phase": "Moving Studio popup session",
        "error_type": "AssertionError",
        "moving_capture_cases": 5,
    }
    assert private not in json.dumps(summary)


def test_moving_kernel_helper_collects_without_optional_runtime_dependencies():
    child = Path(__file__).with_name("_jupyter_moving_capture.py")
    received = subprocess.run(
        [sys.executable, "-I", "-S", "-c", "import runpy,sys;runpy.run_path(sys.argv[1])", str(child)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert received.returncode == 0, received.stderr


def test_guard_process_cleanup_retains_reparented_children_and_preserves_unrelated_process(tmp_path):
    """Real child processes only; no Jupyter server or browser is launched."""
    psutil = pytest.importorskip("psutil")
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    child_pid_path = tmp_path / "child-pid.txt"
    script = (
        "import subprocess,sys,time\n"
        "from pathlib import Path\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
        "Path(sys.argv[1]).write_text(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    parent = subprocess.Popen([sys.executable, "-c", script, str(child_pid_path)])
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    process = psutil.Process(parent.pid)
    owned = {(process.pid, process.create_time()): process}
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            assert owner["_track_owned_processes"](owned) == []
            if child_pid_path.exists():
                child_pid = int(child_pid_path.read_text())
                if any(pid == child_pid for pid, _created in owned):
                    break
            time.sleep(0.01)
        else:
            raise AssertionError("The owned child did not become observable.")
        parent.terminate()
        parent.wait(timeout=2)
        # An ancestry query after this point cannot recover the child's former
        # parent; the retained Process identity still belongs to this operation.
        report = owner["_stop_owned_processes"](owned)
        assert report["survivors"] == [] and report["errors"] == []
        assert report["tracked"] >= 2
        assert unrelated.poll() is None
    finally:
        owner["_track_owned_processes"](owned)
        owner["_stop_owned_processes"](owned)
        parent.wait(timeout=2)
        unrelated.terminate()
        unrelated.wait(timeout=2)


@pytest.mark.jupyter_runtime
def test_live_background_jupyter_work_files(tmp_path):
    if os.environ.get("MOLSYSVIEWER_JUPYTER_TEST") != "1":
        pytest.skip("Select MOLSYSVIEWER_JUPYTER_TEST=1 with JupyterLab, ipykernel and native Chromium available.")
    script = Path(__file__).with_name("_jupyter_live_capture.py")
    output = tmp_path / "jupyter-background"
    exit_code = runpy.run_path(str(script))["run"](output, profile="background")
    receipt = json.loads((output / "command-result.json").read_text())
    assert exit_code == 0, f"Background receiving failed ({receipt}); private diagnostics: {output}"
    assert receipt["browser_summary"]["outcome"] == "passed"
    observed = json.loads((output / "observations.json").read_text())
    assert observed["outcome"] == "passed" and observed["capture_restore_cases"] == 2
    assert {(case["kind"], case["phase"]) for case in observed["cases"]} == {
        (kind, phase) for kind in ("state", "session") for phase in ("hidden", "visible retry")
    }
    for case in observed["cases"]:
        if case["phase"] == "hidden":
            assert case["hidden"]["hidden"] and case["after"]["hidden"]
            assert all(change["hidden"] for change in case["after"]["changes"][len(case["hidden"]["changes"]) :])
            result = case["result"]
            assert result["pending_requests"] == 0 and result["source_and_coordinates_preserved"]
            assert result["heartbeat_progress"] > 0
            if result["outcome"] == "refused":
                assert result["reason"] in {"request_timeout", "renderer_refused"}
                assert result["destination_preserved_on_refusal"]
            else:
                assert result["outcome"] == "saved" and case["after"]["draws"] > case["hidden"]["draws"]
        else:
            assert case["fresh_draw"] and case["independent_restore"] and case["pending_requests"] == 0
    assert not (output / "settings.json").exists()
    assert not (output / "config/jupyter_server_config.py").exists()


@pytest.mark.jupyter_runtime
def test_live_jupyter_controller_release(tmp_path):
    if os.environ.get("MOLSYSVIEWER_JUPYTER_TEST") != "1":
        pytest.skip("Select MOLSYSVIEWER_JUPYTER_TEST=1 with JupyterLab, ipykernel and native Chromium available.")
    output = tmp_path / "jupyter-lifecycle"
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    assert owner["run"](output, profile="lifecycle") == 0, f"Private lifecycle diagnostics: {output}"
    observed = json.loads((output / "lifecycle-observations.json").read_text())
    assert observed["outcome"] == "passed"
    assert observed["retired_callbacks"] == []
    assert all(observed["native_collected"][name] for name in ("structure", "model", "axis", "buffer"))
    assert observed["witness"] == observed["initial"]["witness"]
    assert not (output / "settings.json").exists()
    assert not (output / "config/jupyter_server_config.py").exists()


def test_live_jupyter_work_files(tmp_path):
    if os.environ.get("MOLSYSVIEWER_JUPYTER_TEST") != "1":
        pytest.skip("Select MOLSYSVIEWER_JUPYTER_TEST=1 with JupyterLab, ipykernel and Playwright available.")
    script = Path(__file__).with_name("_jupyter_live_capture.py")
    output = tmp_path / "jupyter-capture"
    # The receiving owner bounds startup/browser/cleanup separately. An outer
    # subprocess timeout could kill that owner before its finally releases the
    # kernel, Chromium descendants and ephemeral credentials.
    exit_code = runpy.run_path(str(script))["run"](output)
    receipt = json.loads((output / "command-result.json").read_text())
    assert exit_code == 0, f"Jupyter receiving failed ({receipt}); private diagnostics: {output}"
    assert receipt["browser_summary"]["status"] == "available"
    assert receipt["browser_summary"]["outcome"] == "passed"
    observed = json.loads((output / "observations.json").read_text())
    assert observed["outcome"] == "passed"
    assert observed["capture_restore_cases"] >= 4
    assert observed["studio_cases"] >= 3
    assert observed["strong_restore_cases"] == observed["capture_restore_cases"]
    assert observed["no_late_write_after_cancel"] is True
    assert observed["no_late_write_after_timeout"] is True
    assert len(observed["delayed_captures"]) == 2
    assert {case["kind"] for case in observed["delayed_captures"]} == {"cancel", "timeout"}
    assert all(
        case["ok"] and case["capture_version"] == 2 and case["fresh_native_draw"] and case["playing"] is False
        for case in observed["delayed_captures"]
    )
    runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))["_check_moving_capture_contract"](
        observed
    )
    assert not (output / "settings.json").exists()
    assert not (output / "config/jupyter_server_config.py").exists()
