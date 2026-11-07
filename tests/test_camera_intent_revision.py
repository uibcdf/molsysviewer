"""Authority camera intent and bootstrap ownership; real renderer receiving is separate."""

from copy import deepcopy

import pytest
from molsysviewer.standalone_qt.utils import QtMessageBridge
from molsysviewer.standalone_qt.view_channel import QtViewChannel

import molsysviewer as msv

POSE = {"position": [10.0, 20.0, 30.0], "target": [1.0, 2.0, 3.0], "up": [0.0, 1.0, 0.0]}


def observe(view):
    messages = []
    original = view.widget.send

    def receive(message, buffers=None):
        messages.append(deepcopy(message))
        return original(message, buffers=buffers)

    view.widget.send = receive
    return messages


def poses(messages):
    return [message for message in messages if message.get("op") == "set_camera_snapshot"]


def seeds(messages):
    return [message for message in messages if message.get("op") == "set_camera_sync_revision"]


def test_explicit_intent_has_one_revision_across_all_endpoints_and_no_portable_metadata():
    with msv.demo["dialanine"] as view:
        view._ready = True
        view._endpoint_transfers.register("canvas-one", "canvas")
        view._endpoint_transfers.register("panel-one", "panel")
        messages = observe(view)
        original = deepcopy(POSE)
        view.camera.set_snapshot(original)
        first = poses(messages)
        assert len(first) == 3
        assert {message["camera_revision"] for message in first} == {1}
        assert {message["target_endpoint_id"] for message in first} == {
            f"widget-host:{view._binary_session_id}",
            "canvas-one",
            "panel-one",
        }
        assert all(message["snapshot"] == POSE for message in first)
        assert original == POSE
        assert "camera_revision" not in view.export_state()["view"]
        assert "camera_revision" not in view.export_state()["view"]["camera"]
        messages.clear()
        view.camera.set_snapshot({**POSE, "position": [20.0, 30.0, 40.0]})
        assert {message["camera_revision"] for message in poses(messages)} == {2}


def test_passive_telemetry_and_pure_bootstrap_cannot_advance_or_replay_authority_pose():
    with msv.demo["dialanine"] as view:
        view._ready = True
        messages = observe(view)
        view.camera.set_snapshot(deepcopy(POSE))
        passive = {**POSE, "position": [100.0, 200.0, 300.0]}
        view._handle_frontend_event({"event": "camera_snapshot", "snapshot": passive})
        messages.clear()
        for _ in range(3):
            popup = view.build_popup_scene_snapshot("canvas")
            assert seeds(popup) == [{"op": "set_camera_sync_revision", "camera_revision": 1}]
            assert poses(popup) == [], "a live popup obtains its actual pose from the live host"
        assert messages == [], "pure bootstrap cannot send an intent"
        view.camera.set_snapshot(deepcopy(POSE))
        assert poses(messages)[0]["camera_revision"] == 2


@pytest.mark.parametrize("transport", ["widget", "qt"])
def test_pre_ready_explicit_intent_is_detached_delivered_once_and_primary_only(transport):
    channel = None if transport == "widget" else QtViewChannel(QtMessageBridge(None, None))
    with msv.MolSysView(transport=channel) as view:
        messages = observe(view)
        first = deepcopy(POSE)
        view.camera.set_snapshot(first)
        latest = {**deepcopy(POSE), "position": [40.0, 50.0, 60.0]}
        view.camera.set_snapshot(latest)
        latest["position"][0] = -999.0
        assert poses(messages) == []
        view._handle_frontend_event({"event": "ready", "capabilities": {}})
        delivered = poses(messages)
        assert len(delivered) == 1
        assert delivered[0]["camera_revision"] == 2
        assert delivered[0]["snapshot"]["position"] == [40.0, 50.0, 60.0]
        target = delivered[0].get("target_endpoint_id")
        assert target == (f"widget-host:{view._binary_session_id}" if transport == "widget" else None)
        messages.clear()
        view._handle_frontend_event({"event": "ready", "capabilities": {}})
        assert poses(messages) == [], "ready/reconnect must not replay an already delivered pose"


def test_independent_static_export_starts_a_fresh_revision_domain_without_mutating_live_intent():
    with msv.demo["dialanine"] as view:
        view._ready = True
        messages = observe(view)
        view.camera.set_snapshot(deepcopy(POSE))
        exported = view._build_static_export_snapshot()
        assert seeds(exported) == [{"op": "set_camera_sync_revision", "camera_revision": 0}]
        assert poses(exported)[0]["camera_revision"] == 0
        assert poses(exported)[0]["snapshot"] == POSE
        messages.clear()
        view.camera.set_snapshot(deepcopy(POSE))
        assert poses(messages)[0]["camera_revision"] == 2


def test_cached_snapshot_is_detached_from_input_and_returned_nested_vectors():
    with msv.demo["dialanine"] as view:
        original = deepcopy(POSE)
        view.camera.set_snapshot(original)
        original["position"][0] = -999.0
        assert view.camera.get_snapshot() == POSE
        returned = view.camera.get_snapshot()
        returned["target"][0] = -999.0
        assert view.camera.get_snapshot() == POSE


@pytest.mark.parametrize(
    "navigation",
    [
        {"op": "reset_view", "options": {}},
        {"op": "reset_camera"},
        {"op": "zoom", "atom_indices": [0, 1], "options": {"duration_ms": 250, "extra_radius": 4.0}},
        {"op": "zoom_to_position", "center": [1.0, 2.0, 3.0], "radius": 5.0},
    ],
)
def test_later_navigation_replaces_camera_intent_once_before_endpoint_fanout(navigation):
    with msv.demo["dialanine"] as view:
        view._ready = True
        view._endpoint_transfers.register("canvas-one", "canvas")
        view._endpoint_transfers.register("panel-one", "panel")
        messages = observe(view)
        view.camera.set_snapshot(deepcopy(POSE))
        messages.clear()
        original = deepcopy(navigation)
        view._send(navigation)
        delivered = [message for message in messages if message.get("op") == navigation["op"]]
        assert len(delivered) == 3
        assert {message.get("camera_revision") for message in delivered} == {2}
        assert navigation == original
        for message in delivered:
            assert {key: message[key] for key in navigation} == original
        assert "camera_revision" not in view.export_state()["view"]


def test_pre_ready_reset_supersedes_a_pending_pose_without_replaying_that_pose():
    with msv.demo["dialanine"] as view:
        messages = observe(view)
        view.camera.set_snapshot(deepcopy(POSE))
        view.camera.reset()
        assert messages == []
        view._handle_frontend_event({"event": "ready", "capabilities": {}})
        navigation = [message for message in messages if message.get("op") in {"set_camera_snapshot", "reset_view"}]
        assert len(navigation) == 1
        assert navigation[0]["op"] == "reset_view"
        assert navigation[0]["camera_revision"] == 2
        assert navigation[0]["target_endpoint_id"] == f"widget-host:{view._binary_session_id}"
