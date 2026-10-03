"""Public geometry edits reconcile real trajectories and scientific coverage."""

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3], debug_js=True)
    result = msm.Interactions.from_records(
        [{"structure_index": frame, "interaction_type": "hbond", "participants": [
            {"role": role, "atom_indices": [index]}
            for index, role in enumerate(("donor", "hydrogen", "acceptor"))
        ]} for frame in range(3)],
        n_atoms=view.molsys.get_n_atoms(), n_structures=3,
        evaluated_structure_indices=[0, 1, 2], method="coordinate_edit_fixture",
    )
    view.interactions.attach(result, name="contacts", assume_aligned=True)
    view.interactions.add("contacts", tag="hb")
    return view


@pytest.mark.parametrize("method", ["set_coordinates", "partial_coordinates_update"])
def test_coordinate_edits_invalidate_only_edited_structures_and_refresh_projection(view, method):
    before = puw.get_value(view.get_coordinates(), to_unit="nm")
    projected = view.interactions._frame(view.interactions["hb"], 0)
    assert projected["links"]
    revision = view.interactions._system_revision
    values = before[[2, 0], 2:3, :] + np.array([[[1.0, 0.0, 0.0]], [[2.0, 0.0, 0.0]]])
    getattr(view, method)(puw.quantity(values, "nm"), selection=[2], structure_indices=[2, 0])
    after = puw.get_value(view.get_coordinates(), to_unit="nm")
    np.testing.assert_allclose(after[[2, 0], 2:3, :], values)
    np.testing.assert_array_equal(after[1], before[1])
    np.testing.assert_array_equal(after[:, :2], before[:, :2])
    np.testing.assert_array_equal(view.interactions.get_analysis("contacts").evaluated_structure_indices, [1])
    assert view.interactions._system_revision > revision
    assert view.interactions._frame(view.interactions["hb"], 0)["status"] == "unevaluated"
    assert view.interactions._frame(view.interactions["hb"], 0)["links"] == []
    assert not view.history.can_undo()
    projection = view._materialize_molecular_projection(view._current_molecular_projection)
    np.testing.assert_allclose(projection["payload"]["structures"][0]["coordinates"][2], after[0, 2] * 10)
    if method == "partial_coordinates_update":
        message = next(item for item in reversed(view._test_message_log) if item.get("op") == method)
        assert message["structure_indices"] == [2, 0]
        assert message["coordinate_unit"] == "angstrom"
        np.testing.assert_allclose(message["coordinates"], values * 10)


@pytest.mark.parametrize("structures, values", [
    ([3], np.zeros((1, 1, 3))),
    ([True], np.zeros((1, 1, 3))),
    ([0.5], np.zeros((1, 1, 3))),
    ([0, 0], np.zeros((2, 1, 3))),
    ([0], np.zeros((1, 2, 3))),
    ([0], np.full((1, 1, 3), np.nan)),
])
def test_rejected_coordinate_edits_preserve_system_analysis_and_history(view, structures, values):
    before = puw.get_value(view.get_coordinates(), to_unit="nm")
    analysis = view.interactions.get_analysis("contacts")
    state = view.export_state()
    undo = list(view.history._undo)
    with pytest.raises(Exception):
        view.partial_coordinates_update(puw.quantity(values, "nm"), selection=[2], structure_indices=structures)
    np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="nm"), before)
    assert view.interactions.get_analysis("contacts") is analysis
    assert view.export_state() == state
    assert view.history._undo == undo


def test_edit_supersedes_pending_native_buffers_before_lazy_fallback(view):
    sent = []
    view.widget.send = lambda message, buffers=None: sent.append(dict(message))
    view._handle_frontend_event({"event": "ready", "capabilities": {
        "binary_structure_data": [1], "max_buffer_bytes": 16 * 1024 * 1024}})
    manager = view._structure_transfer_manager(None)
    old = manager.active
    assert old is not None
    values = puw.get_value(view.get_coordinates(selection=[2], structure_indices=[0]), to_unit="nm") + 1
    view.partial_coordinates_update(puw.quantity(values, "nm"), selection=[2], structure_indices=[0])
    assert manager.active is not old
    assert any(m.get("op") == "structure_data_cancel" for m in sent)
    projection = view._materialize_molecular_projection(view._current_molecular_projection)
    np.testing.assert_allclose(projection["payload"]["structures"][0]["coordinates"][2], values[0, 0] * 10)
