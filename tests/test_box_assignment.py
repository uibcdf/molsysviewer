"""Whole-system cell edits preserve indices and invalidate scientific evidence."""
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    system = msm.extract(msv.demo["pentalanine"].molsys, selection=list(range(10)),
                         structure_indices=[0, 8, 3], to_form="molsysmt.MolSys")
    msm.set(system, box=None, time=None)
    view = msv.new_view(system, debug_js=True)
    result = msm.Interactions.from_records([
        {"structure_index": frame, "interaction_type": "hbond", "participants": [
            {"role": role, "atom_indices": [atom]}
            for atom, role in enumerate(("donor", "hydrogen", "acceptor"))
        ]} for frame in range(3)
    ], n_atoms=10, n_structures=3, evaluated_structure_indices=[0, 1, 2], method="box_edit_fixture")
    view.interactions.attach(result, name="contacts", assume_aligned=True)
    view.interactions.add("contacts", tag="hb")
    return view


def _cell(length=2):
    return puw.quantity(np.diag([length, length + 1, length + 2]), "nm")


def _box(view):
    quantity = view.molsys.structures.box
    return None if quantity is None else puw.get_value(quantity, to_unit="nm")


def test_provider_box_initialization_is_verified():
    """A real old provider must fail clearly; a capable provider must store the cell."""
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0], debug_js=True)
    try:
        view.set_box(None)
        assert view.molsys.structures.box is None
        reference = msm.copy(view.molsys)
        requested = _cell(5)
        msm.set(reference, box=requested)
        supported = msm.get(reference, box=True) is not None
        system, state, sources = view.molsys, view.export_state(), view.load_blocks
        messages = deepcopy(view._test_message_log)
        if supported:
            view.set_box(requested)
            np.testing.assert_array_equal(_box(view), [puw.get_value(requested, to_unit="nm")])
        else:
            with pytest.raises(ValueError, match="MolSysMT did not apply the requested box"):
                view.set_box(requested)
            assert view.molsys is system and view.molsys.structures.box is None
            assert view.export_state() == state and view.load_blocks == sources
            assert view._test_message_log == messages
    finally:
        view.close()


def test_assignment_and_removal_preserve_coordinates_sources_and_regions(view):
    incoming = msm.copy(view.molsys)
    incoming.interactions = {}
    view.load(incoming, structure_pairing="by_index")
    before = puw.get_value(view.get_coordinates(), to_unit="nm").copy()
    sources = view.load_blocks
    regions = list(view.regions.values())
    view.set_box(_cell())
    np.testing.assert_array_equal(_box(view), np.broadcast_to(puw.get_value(_cell(), to_unit="nm"), (3, 3, 3)))
    np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="nm"), before)
    assert view.load_blocks == sources
    assert list(view.regions.values()) == regions
    assert view.interactions.get_analysis("contacts").evaluated_structure_indices.size == 0
    assert not view.history.can_undo()
    projection = view._materialize_molecular_projection(view._current_molecular_projection)
    np.testing.assert_allclose(projection["payload"]["structures"][2]["box"], _box(view)[2] * 10)
    view.set_box(None)
    assert _box(view) is None and view.load_blocks == sources
    view.load(msm.extract(msv.demo["pentalanine"].molsys, selection=[0, 1], structure_indices=[0, 8, 3],
                          to_form="molsysmt.MolSys"), structure_pairing="by_index")
    assert _box(view) is None  # Later sources do not introduce a cell.


def test_subset_invalidates_only_edited_frames_and_refreshes_visible_edges(view):
    # Initialize through the scientific provider before attaching a fresh analysis.
    view.molsys.structures.set_box(value=puw.quantity(np.broadcast_to(np.eye(3), (3, 3, 3)).copy(), "nm"))
    view._source_binding_memo = None
    view.show_box(color="red", width=0.2, alpha=0.7)
    binding = view._source_state_binding()
    original = view.interactions.get_analysis("contacts")
    view.set_box(puw.quantity(np.array([np.diag([5, 6, 7]), np.diag([2, 3, 4])]), "nm"),
                 structure_indices=[2, 0])
    np.testing.assert_array_equal(_box(view)[1], np.eye(3))
    np.testing.assert_array_equal(original.evaluated_structure_indices, [0, 1, 2])
    np.testing.assert_array_equal(view.interactions.get_analysis("contacts").evaluated_structure_indices, [1])
    assert view.interactions._frame(view.interactions["hb"], 0)["status"] == "unevaluated"
    assert view._source_state_binding() != binding
    records = [m for m in view._shape_history if view._tag_from_message(m) == view._BOX_TAG]
    assert len(records) == 1
    assert records[0]["options"]["coordinate_pairs"][0] == [[0, 0, 0], [20, 0, 0]]
    assert view._box_record["color"] == 0xFF0000 and view._box_record["alpha"] == 0.7
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2})
    records = [m for m in view._shape_history if view._tag_from_message(m) == view._BOX_TAG]
    assert records[0]["options"]["coordinate_pairs"][0] == [[0, 0, 0], [50, 0, 0]]
    view.set_box(None)
    assert not view._box_visible and view._box_record is None
    assert not any(view._tag_from_message(m) == view._BOX_TAG for m in view._shape_history)


def test_box_from_independent_source_form_and_h5msm_preserves_axis(view, tmp_path):
    cells = np.array([np.diag([i + 2, i + 3, i + 4]) for i in range(3)])
    source = msm.copy(view.molsys)
    msm.set(source, box=puw.quantity(cells, "nm"))
    path = tmp_path / "cells.h5msm"
    msm.h5msm.write(source, str(path))
    view.set_box(molecular_system=path, source_structure_indices=[2, 0, 1], structure_indices=[1, 2, 0],
                 structure_pairing="by_index")
    np.testing.assert_array_equal(_box(view), cells[[1, 2, 0]])
    # A topology-free Structures form is a declared cell source as well.
    view.set_box(molecular_system=source.structures, source_structure_indices=[2], structure_indices=[0])
    np.testing.assert_array_equal(_box(view)[0], cells[2])
    assert len(view.load_blocks) == 1


def test_box_source_selected_times_use_explicit_units(view):
    source = msm.copy(view.molsys)
    msm.set(source, box=puw.quantity(np.broadcast_to(np.eye(3), (3, 3, 3)).copy(), "nm"),
            time=puw.quantity([0, 1000, 2000], "fs"))
    msm.set(view.molsys, time=puw.quantity([0, 1, 2], "ps"))
    view.set_box(molecular_system=source, structure_pairing="by_index")
    before = deepcopy(view.export_state())
    msm.set(source, time=puw.quantity([0, 2, 4], "ps"))
    with pytest.raises(ValueError, match="times"):
        view.set_box(molecular_system=source, structure_pairing="by_index")
    assert view.export_state() == before


@pytest.mark.parametrize("skip", [False, True])
@pytest.mark.parametrize("kwargs", [
    {"box": np.eye(3)},
    {"box": puw.quantity(np.eye(3), "ps")},
    {"box": puw.quantity(np.zeros((3, 3)), "nm")},
    {"box": puw.quantity(np.diag([-1, 1, 1]), "nm")},
    {"box": puw.quantity(np.ones((3, 3)), "nm")},
    {"box": puw.quantity(np.full((3, 3), np.nan), "nm")},
    {"box": puw.quantity(np.zeros((2, 3)), "nm")},
    {"box": _cell(), "structure_indices": [True]},
    {"box": _cell(), "structure_indices": [0.5]},
    {"box": _cell(), "structure_indices": [3]},
    {"box": _cell(), "structure_indices": [0, 0]},
    {"box": _cell(), "structure_indices": []},
    {"box": _cell(), "structure_indices": [1]},
    {"box": puw.quantity(np.broadcast_to(np.eye(3), (2, 3, 3)).copy(), "nm")},
    {"box": _cell(), "source_structure_indices": [0]},
    {"box": _cell(), "structure_pairing": "by_index"},
])
def test_rejected_input_keeps_science_scene_sources_and_history(view, kwargs, skip):
    state = deepcopy(view.export_state())
    messages, undo = list(view._test_message_log), list(view.history._undo)
    analysis = view.interactions.get_analysis("contacts")
    with pytest.raises(Exception):
        view.set_box(**kwargs, skip_digestion=skip)
    assert view.export_state() == state
    assert view._test_message_log == messages and view.history._undo == undo
    assert view.interactions.get_analysis("contacts") is analysis


@pytest.mark.parametrize("case", ["missing", "counts", "pairing", "both", "partial_remove"])
def test_rejected_source_or_partial_removal_preserves_system(view, case):
    source = msm.copy(view.molsys)
    if case != "missing":
        msm.set(source, box=puw.quantity(np.broadcast_to(np.eye(3), (3, 3, 3)).copy(), "nm"))
    kwargs = {"molecular_system": source, "structure_pairing": "by_index"}
    if case == "counts":
        kwargs["source_structure_indices"] = [0]
    elif case == "pairing":
        kwargs.pop("structure_pairing")
    elif case == "both":
        kwargs["box"] = _cell()
    elif case == "partial_remove":
        kwargs = {"box": None, "structure_indices": [0]}
    before = deepcopy(view.export_state())
    with pytest.raises(Exception):
        view.set_box(**kwargs)
    assert view.export_state() == before


def test_current_box_survives_addition_copy_extraction_and_session(view, tmp_path):
    view.set_box(puw.quantity(np.array([np.diag([2 + i, 3 + i, 4 + i]) for i in range(3)]), "nm"))
    cells = _box(view).copy()
    source = msm.extract(msv.demo["pentalanine"].molsys, selection=[0, 1], structure_indices=[0, 8, 3],
                         to_form="molsysmt.MolSys")
    msm.set(source, time=None)
    view.load(source, structure_pairing="by_index")
    np.testing.assert_array_equal(_box(view), cells)
    copied = msv.tools.copy(view)
    extracted = msv.tools.extract(view, selection=[0, 2], structure_indices=[2, 0])
    np.testing.assert_array_equal(_box(copied), cells)
    np.testing.assert_array_equal(_box(extracted), cells[[2, 0]])
    path = tmp_path / "session.msvz"
    view.save_session(path)
    restored = msv.load_session(path)
    np.testing.assert_array_equal(_box(restored), cells)
    assert restored.load_blocks == view.load_blocks


def test_assignment_requires_a_loaded_system():
    with pytest.raises(ValueError, match="No molecular system"):
        msv.MolSysView().set_box(_cell())
