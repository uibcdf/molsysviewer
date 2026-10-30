"""Private desktop affordances use real Qt widgets without a renderer substitute."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.qt_runtime
def test_native_status_details_and_normal_geometry(tmp_path):
    pytest.importorskip("PySide6.QtWidgets")
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH")]))
    receipt = tmp_path / "result.json"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("_qt_window_polish.py")), str(receipt)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(receipt.read_text())
    assert report == {"status": True, "details": True, "geometry": True, "platform": "offscreen"}
