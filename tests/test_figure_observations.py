"""Historical figure context survives actual scene ownership boundaries."""

from copy import deepcopy

import numpy as np
import pytest
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.figure_observation import MAX_OBSERVATION_BYTES

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source, source.extract(structure_indices=[8, 3, 0]) as view:
        yield view


def observation():
    return {
        "schema": "example.figure_observation@7",
        "method": "independent producer control",
        "source": {"structure_indices": [8, 3, 0], "atom_indices": [5, 1, 5]},
        "reference": {"kind": "independent", "input": "preserved-reference.h5msm", "atom_indices": [2, 0, 2]},
        "weights": {"encoding": "binary64_hex", "unit": "dalton", "values": [float(x).hex() for x in [12, 1, 12]]},
        "units": {"native": "nm", "displayed": "angstrom"},
        "literal": "<b data-observation-marker>literal</b>",
    }


def test_observation_is_detached_per_series_and_replacement_is_explicit(view):
    context = observation()
    expected = deepcopy(context)
    view.trajectory_plot.show({"A": [1, 2, 3], "B": [4, 5, 6]}, observations=[context, None])
    context["source"]["atom_indices"].clear()
    series = view.trajectory_plot.records()[0]["series"]
    assert series[0]["observation"] == expected
    assert series[0]["observation_rows"] == [0, 1, 2]
    assert "observation" not in series[1]
    series[0]["observation"]["source"].clear()
    assert view.trajectory_plot.records()[0]["series"][0]["observation"] == expected
    view.trajectory_plot.hide()
    view.trajectory_plot.show()
    assert view.trajectory_plot.records()[0]["series"][0]["observation"] == expected
    view.trajectory_plot.update([9, 8, 7])
    assert "observation" not in view.trajectory_plot.records()[0]["series"][0]


def test_context_persists_in_state_session_history_popups_and_repeated_extraction(view, tmp_path):
    view.trajectory_plot.show([1, 2, 3], observations=[observation()], tag="historical")
    expected = view.trajectory_plot.records()
    # Plot operations have no existing Undo promise. Receive their retained
    # context through real scene checkpoints taken by an undoable shape edit.
    view.shapes.add_sphere(
        center=msv.pyunitwizard.quantity([0, 0, 0], "angstrom"), radius="1 angstrom", tag="history-probe"
    )
    assert view.history.undo()
    assert view.trajectory_plot.records() == expected
    assert view.history.redo()
    assert view.trajectory_plot.records() == expected
    snapshot = view.build_popup_scene_snapshot("canvas")
    assert (
        next(message for message in snapshot if message["op"] == "set_trajectory_plot")["options"]["cards"] == expected
    )
    # Detached Studio is a control surface; the figures remain in its canvas.
    assert not any(message["op"] == "set_trajectory_plot" for message in view.build_popup_scene_snapshot("panel"))
    assert view.trajectory_plot.records() == expected
    with view.extract(structure_indices=[2, 0, 0]) as extracted:
        series = extracted.trajectory_plot.records()[0]["series"][0]
        assert series["values"] == [3, 1, 1]
        assert series["observation"] == observation()
        assert series["observation_rows"] == [2, 0, 0]
        assert series["observation_count"] == 3
        with extracted.extract(structure_indices=[2, 1]) as second:
            assert second.trajectory_plot.records()[0]["series"][0]["observation_rows"] == [0, 0]
    view.save_session(tmp_path / "context.msv")
    with msv.load_session(tmp_path / "context.msv") as restored:
        assert restored.trajectory_plot.records() == expected
    with msv.new_view(view.molsys) as restored:
        restored.import_state(view.export_state())
        assert restored.trajectory_plot.records() == expected


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        {},
        {"schema": ""},
        {"schema": "x", "value": float("nan")},
        {"schema": "x", "value": float("inf")},
        {"schema": "x", "value": 2**53},
        {"schema": "x", "value": object()},
        {"schema": "x", 1: "bad key"},
        {"schema": "x", "value": "x" * (MAX_OBSERVATION_BYTES + 1)},
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_malformed_or_oversized_context_is_rejected_without_scene_changes(view, invalid, skip):
    view.trajectory_plot.show([1, 2, 3], observations=[observation()])
    before = view.export_state()
    payload = invalid if invalid is not None else {"schema": "x"}
    if invalid is None:
        payload["cycle"] = payload
    with pytest.raises((ValueError, ArgumentError)):
        view.trajectory_plot.show([4, 5, 6], observations=[payload], skip_digestion=skip)
    assert view.export_state() == before


def test_invalid_import_rows_or_context_preserve_existing_scene(view):
    view.trajectory_plot.show([1, 2, 3], observations=[observation()])
    before = view.export_state()
    for key, value in [("observation_rows", [0, 1, 3]), ("observation_count", True), ("observation", {"schema": ""})]:
        state = deepcopy(before)
        state["trajectory_plots"][0]["series"][0][key] = value
        with pytest.raises(ValueError):
            view.import_state(state)
        assert view.export_state() == before


def test_native_independent_reference_inputs_and_nondefault_units_can_be_reproduced(view, tmp_path):
    import molsysmt as msm

    puw = msm.pyunitwizard
    atoms = [5, 1, 5]
    coordinates = puw.get_value(view.molsys.structures.coordinates, to_unit="nm").copy()
    reference = msm.extract(view.molsys, structure_indices=[1])
    reference_coordinates = puw.get_value(reference.structures.coordinates, to_unit="nm") + [0.1, 0, 0]
    msm.set(reference, coordinates=puw.quantity(reference_coordinates, "nm"))
    reference_path = tmp_path / "independent-reference.h5msm"
    msm.convert(reference, to_form=str(reference_path))
    with puw.context(standard_units=["pm", "ps", "dalton", "radians"]):
        native = msm.structure.get_rmsd(
            view.molsys,
            selection=atoms,
            structure_indices=[0, 1, 2],
            reference_molecular_system=reference,
            reference_selection=atoms,
            reference_structure_index=0,
            engine="MolSysMT",
            use_gpu=False,
        )
        displayed = puw.get_value(native, to_unit="angstrom")
        expected = (
            np.sqrt(np.mean(np.sum((coordinates[:, atoms] - reference_coordinates[:, atoms]) ** 2, axis=2), axis=1))
            * 10
        )
        np.testing.assert_allclose(displayed, expected, rtol=2e-12, atol=1e-12)
        context = {
            "schema": "example.native_rmsd@1",
            "method": "molsysmt.structure.get_rmsd",
            "software": {"molsysmt": msm.__version__},
            "selection": atoms,
            "structure_indices": [0, 1, 2],
            "reference": {
                "kind": "independent",
                "artifact": reference_path.name,
                "selection": atoms,
                "structure_index": 0,
            },
            "units": {"native": str(puw.get_unit(native)), "displayed": "angstrom"},
        }
        view.trajectory_plot.show(displayed, observations=[context], y_label="RMSD without superposition (Å)")
    view.save_session(tmp_path / "rmsd.msv")
    with msv.load_session(tmp_path / "rmsd.msv") as restored:
        retained = restored.trajectory_plot.records()[0]["series"][0]
        assert retained["observation"] == context
        preserved_reference = msm.convert(str(reference_path), to_form="molsysmt.MolSys")
        reproduced = msm.structure.get_rmsd(
            restored.molsys,
            selection=atoms,
            structure_indices=[0, 1, 2],
            reference_molecular_system=preserved_reference,
            reference_selection=atoms,
            reference_structure_index=0,
            engine="MolSysMT",
            use_gpu=False,
        )
        np.testing.assert_allclose(
            puw.get_value(reproduced, to_unit="angstrom"), retained["values"], rtol=2e-12, atol=1e-12
        )
