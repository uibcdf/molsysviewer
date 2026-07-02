import pytest

from molsysviewer import MolSysView


def _view_with_capture():
    view = MolSysView()
    sent: list = []
    view.widget.send = lambda msg, *a, **k: sent.append(msg)  # type: ignore[attr-defined]
    view._ready = True  # noqa: SLF001
    return view, sent


def test_show_sends_normalized_series_and_records_scene_look():
    view, sent = _view_with_capture()
    view.trajectory_plot.show({"rmsd": [0.1, 0.2, 0.3]}, y_label="RMSD (nm)", title="Run A")

    msg = sent[-1]
    assert msg["op"] == "set_trajectory_plot"
    opts = msg["options"]
    assert opts["visible"] is True
    assert opts["n_frames"] == 3
    assert opts["series"] == [{"label": "rmsd", "values": [0.1, 0.2, 0.3]}]
    assert opts["y_label"] == "RMSD (nm)"
    assert opts["title"] == "Run A"
    # Recorded as part of the reproducible scene look (survives rebuild/export).
    assert "trajectory_plot" in view._scene_look  # noqa: SLF001


def test_show_accepts_multiple_series_as_list():
    view, sent = _view_with_capture()
    view.trajectory_plot.show([[0, 1, 2], [3, 4, 5]])
    series = sent[-1]["options"]["series"]
    assert [s["label"] for s in series] == ["series 1", "series 2"]
    assert series[1]["values"] == [3.0, 4.0, 5.0]


def test_colors_by_cvd_safe_scheme_name():
    view, sent = _view_with_capture()
    view.trajectory_plot.show({"a": [1, 2], "b": [3, 4]}, colors="okabe_ito")
    series = sent[-1]["options"]["series"]
    assert series[0]["color"] == 0xE69F00  # Okabe-Ito first colour
    assert series[1]["color"] == 0x56B4E9


def test_events_are_normalized_and_range_checked():
    view, sent = _view_with_capture()
    view.trajectory_plot.show([0, 1, 2, 3], events=[{"frame": 2, "label": "bind", "color": "red"}])
    assert sent[-1]["options"]["events"] == [{"frame": 2, "label": "bind", "color": 0xFF0000}]

    with pytest.raises(ValueError):
        view.trajectory_plot.show([0, 1, 2, 3], events=[{"frame": 9}])


def test_series_length_mismatch_raises():
    view, _ = _view_with_capture()
    with pytest.raises(ValueError):
        view.trajectory_plot.show({"a": [0, 1, 2], "b": [0, 1]})


def test_clear_sends_hidden_state():
    view, sent = _view_with_capture()
    view.trajectory_plot.show([0, 1, 2])
    view.trajectory_plot.clear()
    assert sent[-1] == {"op": "set_trajectory_plot", "options": {"visible": False}}


def test_on_frame_change_callback_fires_and_unregisters():
    view = MolSysView()
    seen: list = []

    def cb(ev):
        seen.append(ev)

    view.on_frame_change(cb)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 5, "is_playing": True})  # noqa: SLF001
    assert seen == [{"event": "frame_changed", "frame": 5, "is_playing": True}]

    view.off_frame_change(cb)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 6, "is_playing": False})  # noqa: SLF001
    assert len(seen) == 1  # no further calls after unregister


def test_frame_change_callback_error_does_not_break_tracking():
    view = MolSysView()

    def boom(_ev):
        raise RuntimeError("bad callback")

    view.on_frame_change(boom)
    # Must not raise, and the frame index must still update.
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 4, "is_playing": False})  # noqa: SLF001
    assert view._current_structure_index == 4  # noqa: SLF001
