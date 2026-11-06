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
