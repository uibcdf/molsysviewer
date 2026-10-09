"""Region isolation is a durable scene operation, including base regions."""

from copy import deepcopy

import pytest
from molsysviewer.demo import demo

import molsysviewer as msv


def _view():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None
    return view


def _isolated(view):
    return [r["tag"] for r in view.export_state()["regions"] if r.get("show_only")]


def _scene():
    view = _view()
    view.regions.add(atom_indices=[0, 1], tag="base")
    view.regions.add(atom_indices=[1, 2], tag="overlap")
    view.regions.add(atom_indices=[2, 3], tag="own", representation="spacefill")
    return view


def test_base_isolation_shows_whole_and_hides_other_regions_only():
    view = _scene()
    overlay = view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="s")
    view.whole.hide()
    view.regions["base"].show_only()
    assert view.whole.visible is True
    assert view.regions["base"].representation is None
    assert _isolated(view) == ["base"]
    assert view.regions["overlap"].visible is False
    assert view.regions["own"].visible is False
    assert overlay._hidden is False


def test_isolation_round_trips_without_hiding_later_visible_regions(tmp_path):
    view = _scene()
    view.regions["base"].show_only()
    view.regions.add(atom_indices=[3, 4], tag="later", representation="line")
    view.whole.hide()  # User changed whole visibility after isolation.
    path = tmp_path / "isolation.msv"
    view.save_session(path)
    restored = msv.load_session(path)
    assert _isolated(restored) == ["base"]
    assert restored.whole.visible is False
    assert restored.regions["later"].visible is True
    for messages in (restored.build_popup_scene_snapshot("canvas"), restored._build_export_messages()):
        assert {"op": "show_only_region", "tag": "base", "restore_only": True} in messages


def test_isolation_survives_rename_copy_extract_and_rebuild():
    view = _scene()
    view.regions["base"].show_only()
    view.regions["base"].rename("source")
    assert _isolated(view) == ["source"]
    assert _isolated(msv.tools.basic.copy(view)) == ["source"]
    extracted = view.extract(selection=[1, 3, 4])
    assert _isolated(extracted) == ["source"]
    assert extracted.regions["source"].atom_indices == (0,)
    assert _isolated(view.extract(selection=[3, 4])) == []
    view.apply_system_edit(view.molsys, atom_index_map={i: i for i in range(view.molsys.get_n_atoms())})
    assert _isolated(view) == ["source"]
    assert {"op": "show_only_region", "tag": "source", "restore_only": True} in view._test_message_log


@pytest.mark.parametrize(
    "action", ["show_target", "hide_target", "show_other", "delete_target", "show_all", "hide_all"]
)
def test_visibility_operations_release_isolation(action):
    view = _scene()
    view.regions["base"].show_only()
    if action == "show_target":
        view.regions["base"].show()
    elif action == "hide_target":
        view.regions["base"].hide()
    elif action == "show_other":
        view.regions["own"].show()
    elif action == "delete_target":
        view.regions["base"].delete()
    elif action == "show_all":
        view.regions.show_all()
    else:
        view.regions.hide_all()
    assert _isolated(view) == []


def test_isolation_is_one_undo_step_and_survives_representation_changes():
    view = _scene()
    view.whole.hide()
    view.regions["base"].show_only()
    assert view.history.undo()
    assert view.whole.visible is False
    assert _isolated(view) == []
    assert view.history.redo()
    assert view.whole.visible is True
    assert _isolated(view) == ["base"]
    view.regions["base"].set_representation("inherit")
    assert _isolated(view) == ["base"]
    view.regions["base"].reset_representation()
    assert _isolated(view) == ["base"]


@pytest.mark.parametrize("invalid", ["multiple", "hidden", "non_boolean"])
def test_invalid_isolation_state_is_rejected_before_scene_mutation(invalid):
    view = _scene()
    before = view.export_state()
    state = deepcopy(before)
    state["regions"][0]["show_only"] = True
    if invalid == "multiple":
        state["regions"][1]["show_only"] = True
    elif invalid == "hidden":
        state["regions"][0]["hidden"] = True
    else:
        state["regions"][0]["show_only"] = "yes"
    with pytest.raises(ValueError, match="show_only"):
        view.import_state(state)
    assert view.export_state() == before


def test_isolated_member_of_hidden_layer_remains_visible_on_restore():
    view = _scene()
    view.regions["base"].set_layer("source")
    view.layers["source"].hide()
    view.regions["base"].show_only()
    state = view.export_state()
    restored = _view()
    restored.import_state(state)
    assert restored.regions["base"].visible is True
    assert _isolated(restored) == ["base"]


def test_empty_dynamic_isolation_survives_restore_and_rebuild_then_reappears(tmp_path):
    view = _view()
    original = view.get_coordinates(selection=[1], structure_indices=[0])
    region = view.regions.add(
        selection="atom_index==1 within 1 nm without pbc of atom_index==0",
        tag="near",
    )
    region.mode = "dynamic"
    region.show_only()
    view.partial_coordinates_update(
        msv.pyunitwizard.quantity([[[100.0, 100.0, 100.0]]], "nm"),
        selection=[1],
        structure_indices=[0],
    )
    assert region.atom_indices == ()
    state = view.export_state()
    view.import_state(state)
    assert "near" in view.regions, f"Empty dynamic region was lost; exported regions: {state['regions']!r}"
    assert view.regions["near"].atom_indices == ()
    assert _isolated(view) == ["near"]
    assert _isolated(msv.tools.basic.copy(view)) == ["near"]
    path = tmp_path / "empty-isolation.msv"
    view.save_session(path)
    restored = msv.load_session(path)
    assert restored.regions["near"].atom_indices == ()
    assert _isolated(restored) == ["near"]
    view.apply_system_edit(view.molsys)
    assert view.regions["near"].atom_indices == ()
    assert _isolated(view) == ["near"]
    view.partial_coordinates_update(original, selection=[1], structure_indices=[0])
    assert view.regions["near"].atom_indices == (1,)
    assert _isolated(view) == ["near"]
