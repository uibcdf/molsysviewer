"""Real molecular authority receiving guards for portable popup state."""

from copy import deepcopy

import pytest

import molsysviewer as msv


@pytest.fixture
def view():
    result = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
    try:
        yield result
    finally:
        result.close()


def test_object_pick_projection_and_popup_snapshot_preserve_portable_identity(view):
    view.shapes.add_sphere(tag="pick", atom_indices=[0, 1])
    item = {
        "source_kind": "shape",
        "scene_kind": "shape",
        "shape_kind": "sphere",
        "tag": "pick",
        "shape_name": "pick",
        "atom_indices": [0, 1],
        "group_indices": [],
        "chain_indices": [],
        "entity_indices": [],
        "shape_groups": [{"ids": [0], "instance": 0}],
    }
    view._handle_frontend_event(
        {
            "event": "interaction_active_selection_changed",
            "source_kind": "shape",
            "items": [item],
            "atom_indices": [0, 1],
            "count_shapes": 1,
        }
    )
    for mode in ("canvas", "panel"):
        projection = next(msg for msg in view.build_popup_scene_snapshot(mode) if msg["op"] == "set_active_selection")
        assert projection["items"] == [item]
        assert projection["atom_indices"] == [0, 1]
        projection["items"][0]["shape_groups"][0]["ids"].append(10)
        assert view.active_selection.items[0]["shape_groups"][0]["ids"] == [0]

    # Choosing the same portable object after an edit must refresh local loci
    # in every endpoint without recording a second selection operation.
    before = len(view.history._undo)  # noqa: SLF001
    pushed = []
    view._send_runtime_only = lambda message: pushed.append(message)  # noqa: SLF001
    view._handle_frontend_event(deepcopy(view._last_active_selection_event))  # noqa: SLF001
    projection = next(message for message in pushed if message["op"] == "set_active_selection")
    assert projection["items"] == [item]
    assert len(view.history._undo) == before  # noqa: SLF001


def test_object_pick_identity_survives_state_and_history(view):
    view.shapes.add_sphere(tag="pick", atom_indices=[0, 1])
    item = {
        "source_kind": "shape",
        "scene_kind": "shape",
        "shape_kind": "sphere",
        "tag": "pick",
        "shape_name": "pick",
        "atom_indices": [0, 1],
        "group_indices": [],
        "chain_indices": [],
        "entity_indices": [],
        "shape_groups": [{"ids": [0], "instance": 0}],
    }
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "shape",
        "items": [item],
        "atom_indices": [0, 1],
        "count_shapes": 1,
    }
    view._handle_frontend_event(event)
    state = view.export_state()
    view.active_selection.set([4, 5])
    view.history.undo()
    assert view.active_selection.source_kind == "shape"
    assert view.active_selection.items == [item]
    view.import_state(deepcopy(state))
    assert view.active_selection.source_kind == "shape"
    assert view.active_selection.atom_indices == [0, 1]


def test_playback_stop_reprojects_final_authoritative_frame(view):
    before = len(view._test_message_log)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2, "is_playing": False})
    assert view.player.index == 2
    # Runtime projection must not become a replay command/history entry.
    assert len(view._test_message_log) == before
    assert (
        next(msg for msg in view.build_popup_scene_snapshot("canvas") if msg["op"] == "set_trajectory_frame")["index"]
        == 2
    )
