"""Multiple plot cards survive canonical snapshots and molecular transfers."""

import pytest
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def view():
    return msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[8, 3, 0])


def populated(view):
    view.trajectory_plot.show([1, 2, 3], tag="a", x=[8, 3, 0], events=[{"frame": 0, "label": "first"}])
    view.trajectory_plot.show([4, 5, 6], tag="b")
    return view


def test_multiple_cards_hide_restore_clear_and_detached_records(view):
    populated(view)
    view.trajectory_plot.hide("a")
    records = view.trajectory_plot.records()
    assert [(card["tag"], card["visible"]) for card in records] == [("a", False), ("b", True)]
    records[0]["series"][0]["values"][0] = 999
    view.trajectory_plot.show(tag="a")
    assert view.trajectory_plot.records()[0]["series"][0]["values"] == [1, 2, 3]
    snapshot = view.build_popup_scene_snapshot("canvas")
    assert len(next(message for message in snapshot if message["op"] == "set_trajectory_plot")["options"]["cards"]) == 2
    view.trajectory_plot.clear("a")
    assert [card["tag"] for card in view.trajectory_plot.records()] == ["b"]
    view.trajectory_plot.clear()
    assert view.trajectory_plot.records() == []
    with pytest.raises(KeyError):
        view.trajectory_plot.show(tag="a")


def test_cards_survive_state_session_copy_and_nonconsecutive_extraction(view, tmp_path):
    populated(view)
    view.trajectory_plot.hide("a")
    original = view.trajectory_plot.records()
    state = view.export_state()
    target = msv.new_view(view.molsys)
    target.import_state(state)
    assert target.trajectory_plot.records() == original
    assert msv.tools.copy(view).trajectory_plot.records() == original
    view.save_session(tmp_path / "plots.msv")
    assert msv.load_session(tmp_path / "plots.msv").trajectory_plot.records() == original
    extracted = view.extract(structure_indices=[2, 0, 0])
    card = extracted.trajectory_plot.records()[0]
    assert card["series"][0]["values"] == [3, 1, 1]
    assert card["x"] == [0, 8, 8]
    assert [event["frame"] for event in card["events"]] == [1, 2]


def test_frame_and_import_validation_precede_mutation(view):
    populated(view)
    before = view.export_state()
    with pytest.raises(ArgumentError):
        view.trajectory_plot.show([1, 2], tag="bad")
    assert view.export_state() == before
    invalid = view.export_state()
    invalid["trajectory_plots"][0]["n_frames"] = 99
    with pytest.raises(ArgumentError):
        view.import_state(invalid)
    assert view.export_state() == before
    with pytest.raises(ValueError, match="already exists"):
        view.import_state(before, clear_first=False)
    assert view.export_state() == before
    view.import_state(before, clear_first=False, on_conflict="rename")
    assert [card["tag"] for card in view.trajectory_plot.records()] == ["a", "b", "a_2", "b_2"]


def test_card_close_event_retains_data_in_python(view):
    populated(view)
    view._handle_frontend_event({"event": "trajectory_plot_hidden", "tag": "b"})
    assert view.trajectory_plot.records()[1]["visible"] is False
    view.trajectory_plot.show(tag="b")
    assert view.trajectory_plot.records()[1]["visible"] is True


def test_structure_axis_changes_are_refused_before_mutation(view):
    populated(view)
    before = view.export_state()
    system = view.molsys
    with pytest.raises(ValueError, match="Clear trajectory plot"):
        view.load(msv.demo["pentalanine"].molsys, mode="append_structures", structure_indices=[0])
    assert view.molsys is system
    assert view.player.n_structures == 3
    assert view.export_state() == before
    edited = msv.new_view(system, structure_indices=[0, 1]).molsys
    with pytest.raises(ValueError, match="Clear trajectory plot"):
        view.apply_system_edit(edited)
    assert view.molsys is system
    assert view.export_state() == before
    view.trajectory_plot.clear()
    view.apply_system_edit(edited)
    assert view.player.n_structures == 2


def test_first_load_checks_prepared_plot_axis_before_mutation():
    view = msv.new_view()
    view.trajectory_plot.show([1, 2], tag="prepared")
    with pytest.raises(ValueError, match="Clear trajectory plot"):
        view.load(msv.demo["pentalanine"].molsys, structure_indices=[0, 1, 2])
    assert view.molsys is None
    assert view.molecular_system is None
    assert view.trajectory_plot.records()[0]["series"][0]["values"] == [1, 2]
    view.load(msv.demo["pentalanine"].molsys, structure_indices=[0, 1])
    assert view.player.n_structures == 2
