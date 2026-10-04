"""Whole-only visibility constraints survive the existing scene lifecycle."""

from __future__ import annotations

from molsysviewer.demo import demo

import molsysviewer as msv


def _view():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None
    return view


def _visibility_messages(view, tag):
    return [
        msg["op"]
        for msg in view._test_message_log
        if msg.get("tag") == tag and msg.get("op") in {"hide_region", "show_region"}
    ]


def test_base_visibility_is_independent_of_whole_and_other_regions():
    view = _view()
    base = view.regions.add(atom_indices=[0, 1], tag="base")
    other = view.regions.add(atom_indices=[1, 2], tag="other", representation="spacefill")
    view.whole.hide()
    base.hide()
    base.show()
    assert view.whole.visible is False
    assert other.visible is True
    assert base.representation is None
    assert _visibility_messages(view, "base") == ["hide_region", "show_region"]
    assert _visibility_messages(view, "other") == []


def test_hidden_base_round_trips_through_state_and_session(tmp_path):
    view = _view()
    view.regions.add(atom_indices=[0, 1], tag="base").hide()
    state = view.export_state()
    assert next(r for r in state["regions"] if r["tag"] == "base")["hidden"] is True
    restored = _view()
    restored.import_state(state)
    assert restored.regions["base"].visible is False
    assert restored.regions["base"].representation is None
    assert "hide_region" in _visibility_messages(restored, "base")

    path = tmp_path / "hidden-base.msv"
    view.save_session(path)
    session = msv.load_session(path)
    assert session.regions["base"].visible is False
    assert session.regions["base"].representation is None
    assert "hide_region" in _visibility_messages(session, "base")


def test_hide_and_style_transition_survive_undo_redo_and_rebuild():
    view = _view()
    view.regions.add(atom_indices=[0, 1], tag="base").hide()
    assert view.history.undo()
    assert view.regions["base"].visible is True
    assert view.history.redo()
    assert view.regions["base"].visible is False
    view.regions["base"].set_representation("inherit")
    assert view.regions["base"].visible is False
    view.regions["base"].reset_representation()
    assert view.regions["base"].visible is False
    view.apply_system_edit(view.molsys, atom_index_map={i: i for i in range(view.molsys.get_n_atoms())})
    assert view.regions["base"].representation is None
    assert view.regions["base"].visible is False
    assert _visibility_messages(view, "base")[-1] == "hide_region"


def test_layer_and_studio_toggle_delegate_to_base_region_visibility():
    view = _view()
    base = view.regions.add(atom_indices=[0, 1], tag="base")
    base.set_layer("source")
    view.layers["source"].hide()
    assert base.visible is False
    assert _visibility_messages(view, "base")[-1] == "hide_region"
    view.layers["source"].show()
    assert base.visible is True
    assert _visibility_messages(view, "base")[-1] == "show_region"
    view._handle_frontend_event(
        {"event": "interaction_context_action", "action": "toggle_region_visibility", "tag": "base"}
    )
    assert base.visible is False
    assert _visibility_messages(view, "base")[-1] == "hide_region"
