"""Native work-file receiving; explicit selection is separate from human acceptance."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests._jupyter_live_capture import _stop_owned_processes, _track_owned_processes


def test_qt_capture_child_collects_without_optional_dependencies():
    child = Path(__file__).with_name("_qt_live_capture.py")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            "import importlib.util,runpy,sys; "
            "assert importlib.util.find_spec('PySide6') is None; "
            "runpy.run_path(sys.argv[1],run_name='collection_guard')",
            str(child),
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.qt_runtime
def test_qt_live_capture_full_render_gpu(tmp_path):
    """Use the selected real host; never infer a human observation from this run."""
    if os.environ.get("MOLSYSVIEWER_QT_GPU_TEST") != "1":
        pytest.skip("Set MOLSYSVIEWER_QT_GPU_TEST=1 on the selected Qt/WebGL2 host.")
    try:
        import psutil
    except ImportError:
        pytest.fail("The selected Qt guard requires the test environment's psutil dependency.")

    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "native-capture"
    output.mkdir(mode=0o700)
    env = {**os.environ}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(root), env.get("PYTHONPATH")]))
    command = [sys.executable, str(Path(__file__).with_name("_qt_live_capture.py")), str(output)]
    owned, errors = {}, []
    child = None
    native_exit = None
    timed_out = False
    started = time.monotonic()
    try:
        with (output / "stdout.log").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
            child = subprocess.Popen(command, env=env, cwd=root, stdout=stdout, stderr=stderr)
            process = psutil.Process(child.pid)
            owned[(process.pid, process.create_time())] = process
            deadline = time.monotonic() + 210
            while child.poll() is None:
                tracking = _track_owned_processes(owned)
                errors.extend(tracking)
                if tracking:
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                time.sleep(0.05)
            native_exit = child.poll()
    finally:
        errors.extend(_track_owned_processes(owned))
        cleanup = _stop_owned_processes(owned)
        errors.extend(cleanup["errors"])
        if child is not None:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired as error:
                errors.append(f"reap:{child.pid}:{type(error).__name__}")
            native_exit = child.poll()
        stderr = (output / "stderr.log").read_text(errors="replace")
        receipt = {
            "command": command,
            "native_exit": native_exit,
            "outer_timeout": timed_out,
            "seconds": time.monotonic() - started,
            "process_cleanup": cleanup,
            "errors": errors,
            "stderr_observations": {
                "unsupported_none_get_form": stderr.count("Form '<class 'NoneType'>' is not supported"),
                "gbm_fallback": stderr.count("GBM is not supported"),
                "dbus_address": stderr.count("Failed to connect to the bus"),
                "deprecation": stderr.count("DeprecationWarning"),
                "scope": "Observed stderr patterns, not an exhaustive diagnostic classification or a globally error-free host claim.",
            },
            "scope": "Automated native Qt/WebEngine/Mol* capture; actual host in report.json; not human acceptance.",
        }
        (output / "command-result.json").write_text(json.dumps(receipt, indent=2) + "\n")

    # A failed child retains complete logs. There is no credential-bearing
    # server here: the fixture uses bundled demo data and local Qt transport.
    logs = (output / "stdout.log").read_text(errors="replace") + (output / "stderr.log").read_text(errors="replace")
    assert native_exit == 0 and not timed_out, f"{receipt}\n{logs}"
    assert not errors and not cleanup["survivors"], f"{receipt}\n{logs}"
    assert receipt["stderr_observations"]["unsupported_none_get_form"] == 0, f"{receipt}\n{logs}"
    observed = json.loads((output / "report.json").read_text())
    assert {(case["source"], case["kind"]) for case in observed["cases"]} == {
        (source, kind) for source in ("studio", "python-async") for kind in ("state", "session")
    }
    assert all(
        case["exact_correlated_camera"]
        and case["perturbed_camera"]
        and case["fresh_restored_draw"]
        and case["changed_frame"] != case["restored_frame"]
        and case["heartbeat_progress"] > 0
        for case in observed["cases"]
    )
    assert observed["cancel_before_draw"]["draws"] == 0
    assert observed["cancel_before_draw"]["no_file"] and observed["cancel_before_draw"]["exact_abort"]
    assert observed["cancel_before_draw"]["late_resume_no_revive"]
    assert not observed["failed_deliveries"] and not observed["frontend_diagnostics"]
    assert observed["heartbeat_count"] > 0 and observed["closed"]
    assert observed["rendering"]["webgl2"]
