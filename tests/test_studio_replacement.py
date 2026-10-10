"""Studio replacements preserve the complete old scene on failure and Undo."""

import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv


@pytest.fixture
def view():
    value = msv.demo["pentalanine"]
    try:
        yield value
    finally:
        value.close()


def scene(view):
    return {
        key: value
        for key, value in view.export_state().items()
        if key not in {"order_high_water_mark", "uid_high_water_mark", "tag_high_water_marks"}
    }


@pytest.mark.parametrize("source", ["active", "saved"])
def test_region_replacement_restores_complete_scene_in_one_undo(view, source):
    view.regions.add(atom_indices=[0], tag="target", representation="ball-and-stick")
    view.active_selection.set([1, 2])
    view.active_selection.save("source")
    view.history.clear()
    before = scene(view)
    action = {
        "action": "create_region_from_selection" if source == "active" else "create_region_from_saved_selection",
        "tag": "target",
        "overwrite": True,
        "selection_tag": "source",
    }
    dispatch_panel_action(view, action)
    assert list(view.regions["target"].atom_indices) == [1, 2]
    after = scene(view)
    assert view.history.undo() and scene(view) == before
    assert not view.history.can_undo()
    assert view.history.redo() and scene(view) == after


def test_failed_region_replacement_preserves_previous_object_and_redo(view):
    view.regions.add(atom_indices=[0], tag="target")
    view.active_selection.set([])
    view.shapes.add_sphere(atom_indices=[0], tag="undo-me")
    view.history.undo()
    before = scene(view)
    with pytest.raises(ValueError, match="active selection"):
        dispatch_panel_action(view, {"action": "create_region_from_selection", "tag": "target", "overwrite": True})
    assert scene(view) == before and view.history.can_redo()


def test_selection_replacement_and_rename_have_one_undo(view):
    view.selections.add("target", atom_indices=[0])
    view.active_selection.set([1, 2])
    view.history.clear()
    before = scene(view)
    dispatch_panel_action(view, {"action": "save_selection", "tag": "target", "overwrite": True})
    after = scene(view)
    assert view.selections["target"].atom_indices == [1, 2]
    assert view.history.undo() and scene(view) == before and not view.history.can_undo()
    assert view.history.redo() and scene(view) == after
    view.selections.add("source", atom_indices=[3])
    view.history.clear()
    before = scene(view)
    dispatch_panel_action(view, {"action": "rename_selection", "tag": "source", "new_tag": "target", "overwrite": True})
    assert view.selections["target"].atom_indices == [3] and "source" not in view.selections
    assert view.history.undo() and scene(view) == before and not view.history.can_undo()


def test_failed_selection_replacement_preserves_previous_object(view):
    view.selections.add("target", atom_indices=[0])
    view.active_selection.set([])
    before = scene(view)
    with pytest.raises(ValueError):
        dispatch_panel_action(view, {"action": "save_selection", "tag": "target", "overwrite": True})
    assert scene(view) == before


def test_public_selection_mutations_own_history(view):
    view.active_selection.set([0])
    view.history.clear()
    view.active_selection.save("saved")
    assert view.history.undo() and "saved" not in view.selections
    assert view.history.redo() and "saved" in view.selections
    view.selections.delete("saved")
    assert view.history.undo() and "saved" in view.selections


def test_addon_rejection_returns_correlated_failure(view):
    messages = []
    view.widget.send = lambda message: messages.append(message)
    view._ready = True
    with pytest.raises(ValueError, match="retired"):
        dispatch_panel_action(
            view, {"action": "addon_register_module", "name": "molsysviewer_molsysmt", "request_id": "registration"}
        )
    assert messages[-1]["op"] == "studio_action_result"
    assert messages[-1]["request_id"] == "registration" and messages[-1]["domain"] == "addons"
    assert not messages[-1]["ok"]


def test_panel_snapshot_preserves_live_scene_settings(view):
    view.active_selection.set([0, 1])
    snapshot = {message["op"]: message for message in view.build_popup_scene_snapshot("panel")}
    for op in ["set_annotation_summaries", "set_measurement_summaries", "set_section_summaries"]:
        assert snapshot[op]["system_loaded"] is True
        assert snapshot[op]["active_selection_count"] > 0
    assert (
        snapshot["set_measurement_summaries"]["endpoint_policy_default"]
        == view.measurements.settings()["endpoint_policy_default"]
    )
