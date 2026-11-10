"""Qualify result window ownership independently of visible Qt/GPU receiving."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.qt_runtime
def test_native_independent_result_window_ownership(tmp_path):
    pytest.importorskip("PySide6.QtWebEngineWidgets")
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "QTWEBENGINE_CHROMIUM_FLAGS": "--no-sandbox --disable-gpu"}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("_qt_presentations.py")), str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads((tmp_path / "result.json").read_text())
    assert receipt["same_application"]
    assert receipt["independent_qt_transport"]
    assert receipt["source_close_preserves_result"]
    assert receipt["native_close_releases_result"]
    assert receipt["temporary_shells_released"]


@pytest.mark.qt_runtime
def test_rendered_independent_result_window_disposal(tmp_path):
    """Receive actual page/profile/window retirement, including native process exit."""
    if os.environ.get("MOLSYSVIEWER_QT_GPU_TEST") != "1":
        pytest.skip("Select the native display guard with MOLSYSVIEWER_QT_GPU_TEST=1.")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("_qt_presentations_rendered.py")), str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Failed to restore OpenGL context" not in result.stderr
    assert "OpenGL resources will not be destroyed" not in result.stderr
    receipt = json.loads((tmp_path / "result.json").read_text())
    assert len(receipt["checks"]) == 4
    assert receipt["native_owners_retired"] == 6
    assert receipt["result_windows_destroyed"] == 5
    assert receipt["platform"] not in {"offscreen", "minimal"}
