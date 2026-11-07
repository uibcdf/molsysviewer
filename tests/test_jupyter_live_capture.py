"""Explicit live-host receiving; an unselected profile is not passing evidence."""

import json
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

import pytest


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
    observed = json.loads((output / "observations.json").read_text())
    assert observed["outcome"] == "passed"
    assert observed["capture_restore_cases"] >= 4
    assert observed["studio_cases"] >= 3
    assert observed["strong_restore_cases"] == observed["capture_restore_cases"]
    assert observed["no_late_write_after_cancel"] is True
    assert observed["no_late_write_after_timeout"] is True
    assert not (output / "settings.json").exists()
    assert not (output / "config/jupyter_server_config.py").exists()
