"""The local Qt shell is a live Python workbench, not a static HTML export."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from molsysviewer.standalone_qt import QtMessageBridge, QtViewChannel
from traitlets import TraitError

import molsysviewer as msv


def test_ui_preferences_use_the_same_validators_and_reject_partial_updates():
    bridge = QtMessageBridge(None, None)
    channel = QtViewChannel(bridge)
    with msv.MolSysView(transport=channel) as view:
        view.widget.viewer_mode = "cinema"
        state = bridge.queue[-1]["message"]
        assert state["op"] == "set_host_ui"
        assert state["values"]["viewer_mode"] == "cinema"
        assert any(row[0] == "Ctrl+Shift+D" for row in state["values"]["host_shortcuts"])
        assert "host_shortcuts" not in channel.get_state()
        assert all(message.get("op") != "set_host_ui" for message in view._build_export_messages())
        count = len(bridge.queue)
        channel._dispatch_event({"event": "qt_ui_state", "values": {"viewer_mode": "standard"}})
        assert view.widget.viewer_mode == "standard"
        assert len(bridge.queue) == count  # No preference echo loop.
        with pytest.raises(TraitError):
            channel._dispatch_event(
                {"event": "qt_ui_state", "values": {"viewer_mode": "cinema", "autohide_scope": "other"}}
            )
        assert view.widget.viewer_mode == "standard"
        with pytest.raises(ValueError, match="supported"):
            channel._dispatch_event({"event": "qt_ui_state", "values": {"runtime_session_id": "other"}})


@pytest.mark.qt_runtime
def test_qt_live_workbench_full_render_gpu(tmp_path):
    """Run actual UI actions and ten replacements in an isolated native window."""
    if not os.environ.get("MOLSYSVIEWER_QT_GPU_TEST"):
        pytest.skip("Set MOLSYSVIEWER_QT_GPU_TEST=1 on a WebGL-capable Qt host.")
    pytest.importorskip("PySide6.QtWebEngineWidgets")
    script = Path(__file__).with_name("_qt_live_workbench.py")
    env = os.environ.copy()
    env["MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH")]))
    try:
        result = subprocess.run(
            [sys.executable, str(script), str(tmp_path)], env=env, text=True, capture_output=True, timeout=180
        )
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or b"") + (error.stderr or b"")
        pytest.fail("Qt workbench timed out. Child phases and traceback:\n" + output.decode(errors="replace")[-12000:])
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["authority"] is True
    assert report["initial_binary_projection"] is True
    assert report["binary_replacements"] == 10
    assert report["all_mode_and_structure_indices"] is True
    assert report["modern_window_chrome"] is True
    assert report["host_shortcut_help"] is True
    assert report["fullscreen_status_details"] is True
    assert report["shared_studio_loading"] is True
    assert report["native_shortcuts"] is True
    if env.get("QT_QPA_PLATFORM") == "xcb":
        assert report["qt_platform"] == "xcb"
    assert report["region_atoms"] == [0, 1]
    assert report["camera_received"] is True
    assert report["image_received"] is True
    assert report["native_download_and_cancel"] is True
    assert report["fullscreen_roundtrip"] is True
    assert report["movie_frames"] == 3
    assert report["independent_host_and_cleanup"] is True
    assert report["timeout_without_reply"] is True
    assert report["python_mode"] == "cinema"
    assert report["browser_mode"] == "standard"
    assert report["loads"] == [22, 62] * 5
    assert report["failed_deliveries"] == []
