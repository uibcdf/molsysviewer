"""Public frame subscriptions follow the real player, without a browser clock."""

import molsysmt as msm
import pytest
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        result = msv.new_view(source.molsys, structure_indices=[8, 3, 11])
    with result:
        yield result


def _event(frame, is_playing=False):
    return {"event": "frame_changed", "frame": frame, "is_playing": is_playing}


@pytest.mark.parametrize(
    ("method", "args", "expected"),
    [
        ("go_to_structure", (2,), 2),
        ("go_to_first", (), 0),
        ("go_to_last", (), 2),
        ("step_forward", (), 2),
        ("step_backward", (), 0),
        ("step_forward", (2,), 0),
        ("step_backward", (2,), 2),
    ],
)
def test_public_navigation_notifies_once_after_state_acceptance(view, method, args, expected):
    view.player.go_to_structure(1)
    seen = []
    state_in_callback = []

    def callback(event):
        seen.append(event)
        state_in_callback.append(view.player.index)

    view.on_frame_change(callback)
    getattr(view.player, method)(*args)
    assert seen == [_event(expected)]
    assert state_in_callback == [expected]
    assert view.player.index == expected
    assert view._structure_index_mapper.original_structures == [8, 3, 11]
    view.off_frame_change(callback)
    view.player.step_forward()
    assert len(seen) == 1


def test_repeated_seek_and_frontend_echo_do_not_duplicate_notifications(view):
    seen = []
    view.on_frame_change(seen.append)
    view.player.go_to_structure(0)
    assert seen == []
    view.player.go_to_structure(1)
    view.player.go_to_structure(1)
    for _ in range(2):
        view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 1, "is_playing": False})
    assert seen == [_event(1)]
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2, "is_playing": True})
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2, "is_playing": True})
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2, "is_playing": False})
    assert seen == [_event(1), _event(2, True), _event(2)]


@pytest.mark.parametrize("skip", [False, True])
@pytest.mark.parametrize("index", [-1, 3, True])
def test_invalid_seek_does_not_change_state_or_notify(view, skip, index):
    seen = []
    view.on_frame_change(seen.append)
    with pytest.raises(ArgumentError):
        view.player.go_to_structure(index, skip_digestion=skip)
    assert view.player.index == 0
    assert seen == []


def test_native_query_failure_is_preserved_without_notification(view, monkeypatch):
    seen = []
    view.on_frame_change(seen.append)
    native_get = msm.get
    failure = RuntimeError("provider structure count unavailable")

    def fail_count(system, *args, **kwargs):
        if system is view.molsys and kwargs.get("n_structures"):
            raise failure
        return native_get(system, *args, **kwargs)

    monkeypatch.setattr(msm, "get", fail_count)
    with pytest.raises(RuntimeError) as error:
        view.player.go_to_structure(1)
    assert error.value is failure
    assert view.player.index == 0
    assert seen == []


def test_scene_send_failure_does_not_notify(view, monkeypatch):
    seen = []
    view.on_frame_change(seen.append)

    def fail_send(_message):
        raise RuntimeError("transport unavailable")

    monkeypatch.setattr(view, "_send", fail_send)
    with pytest.raises(RuntimeError, match="transport unavailable"):
        view.player.go_to_structure(1)
    assert view.player.index == 0
    assert seen == []


def test_canvas_navigation_uses_the_same_subscription_path(view):
    seen = []
    view.on_frame_change(seen.append)
    view._handle_frontend_event({"event": "interaction_context_action", "action": "set_trajectory_frame", "index": 1})
    assert seen == [_event(1)]
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 1})
    assert seen == [_event(1)]
    view._handle_frontend_event({"event": "interaction_context_action", "action": "step_trajectory", "by": -1})
    assert seen == [_event(1), _event(0)]


def test_python_navigation_while_playing_retains_playback_state(view):
    view.player.play()
    seen = []
    view.on_frame_change(seen.append)
    view.player.go_to_structure(2)
    assert seen == [_event(2, True)]
    assert view.player.is_playing


def test_python_play_and_pause_publish_state_before_identical_frontend_echo(view):
    seen = []
    view.on_frame_change(seen.append)
    view.player.play()
    view.player.play()
    assert seen == [_event(0, True)]
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 0, "is_playing": True})
    assert seen == [_event(0, True)]
    view.player.pause()
    view.player.pause()
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 0, "is_playing": False})
    assert seen == [_event(0, True), _event(0)]


@pytest.mark.parametrize("method", ["play", "pause"])
def test_failed_playback_command_does_not_publish_success(view, monkeypatch, method):
    view.player.play()
    seen = []
    view.on_frame_change(seen.append)

    def fail_send(_message):
        raise RuntimeError("playback transport unavailable")

    monkeypatch.setattr(view, "_send", fail_send)
    with pytest.raises(RuntimeError, match="playback transport unavailable"):
        getattr(view.player, method)()
    assert seen == []


def test_npt_box_is_refreshed_before_notification(view):
    from molsysviewer import pyunitwizard as puw

    msm.set(view.molsys, box=puw.quantity([[[2, 0, 0], [0, 2, 0], [0, 0, 2]]] * 3, "nm"))
    view.show_box()
    seen = []
    view.on_frame_change(lambda _event: seen.append(view._box_record["structure_indices"]))
    view.player.go_to_structure(1)
    assert seen == [1]


def test_removal_during_notification_applies_before_next_callback(view):
    seen = []
    callback = seen.append
    view.on_frame_change(lambda _event: view.off_frame_change(callback))
    view.on_frame_change(callback)
    view.player.go_to_structure(1)
    assert seen == []


def test_subscribers_are_independent_and_bad_callbacks_do_not_stop_delivery(view):
    other = msv.demo["dialanine"]
    other_seen = []
    seen = []

    def mutate(event):
        event["frame"] = 999
        raise RuntimeError("subscriber error")

    try:
        other.on_frame_change(other_seen.append)
        view.on_frame_change(mutate)
        view.on_frame_change(seen.append)
        view.on_frame_change(seen.append)
        view.player.go_to_structure(1)
        assert seen == [_event(1)]
        assert other_seen == []
        assert other.player.index == 0
    finally:
        other.close()


def test_reentrant_navigation_preserves_notification_order(view):
    seen = []

    def advance(event):
        if event["frame"] == 1:
            view.player.go_to_structure(2)

    view.on_frame_change(advance)
    view.on_frame_change(seen.append)
    view.player.go_to_structure(1)
    assert seen == [_event(1), _event(2)]
    assert view.player.index == 2


def test_close_during_dispatch_releases_and_stops_subscribers(view):
    seen = []
    view.on_frame_change(lambda _event: view.close())
    view.on_frame_change(seen.append)
    view.player.go_to_structure(1)
    assert view.closed
    assert seen == []
    assert view._frame_change_callbacks == []


def test_closed_view_rejects_navigation_and_late_frontend_events(view):
    seen = []
    callback = seen.append
    view.on_frame_change(callback)
    view.close()
    with pytest.raises(RuntimeError, match="closed"):
        view.player.go_to_structure(1)
    with pytest.raises(RuntimeError, match="closed"):
        view.on_frame_change(callback)
    view.off_frame_change(callback)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2})
    assert view.player.index == 0
    assert seen == []


def test_empty_view_cannot_publish_a_nonexistent_frame():
    with msv.MolSysView() as view:
        seen = []
        view.on_frame_change(seen.append)
        with pytest.raises(ArgumentError):
            view.player.go_to_structure(0)
        view.player.step_forward()
        view.player.step_backward()
        view.player.go_to_last()
        view.player.play()
        view.player.pause()
        assert seen == []


@pytest.mark.parametrize("method", ["play", "pause"])
def test_closed_view_rejects_playback_without_notification(view, method):
    seen = []
    view.on_frame_change(seen.append)
    view.close()
    with pytest.raises(RuntimeError, match="closed"):
        getattr(view.player, method)()
    assert seen == []
