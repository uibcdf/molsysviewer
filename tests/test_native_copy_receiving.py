"""Receive protected native copying through real View/analysis owners.

The older public backend remains a separate compatibility lane. These tests
exercise the newer native copy/edit contract only when that public capability
exists; source receiving must execute them without skips.
"""

import inspect

import molsysmt as msm
import numpy as np
import pytest
from molsysmt.native import ChemicalStates, MolSys
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv

pytestmark = pytest.mark.skipif(
    "deep" not in inspect.signature(MolSys.copy).parameters or not hasattr(ChemicalStates, "remove_bonds"),
    reason="The public backend predates the protected native copy/edit contract (#259).",
)


@pytest.fixture
def source():
    with msv.demo["pentalanine"] as original:
        view = original.extract(structure_indices=[8, 3, 0])
    box = np.repeat(np.array([[[2, 0, 0], [0.5, 2, 0], [0, 0, 2]]]), 3, axis=0)
    msm.set(view.molsys, box=puw.quantity(box, "nm"))
    analysis = msm.Interactions.from_records(
        [
            {
                "structure_index": 0,
                "interaction_type": "pi_pi",
                "participants": [
                    {"role": "ring_a", "atom_indices": [0, 1, 2]},
                    {"role": "ring_b", "atom_indices": [3, 4, 5]},
                ],
                "images": [[0, 0, 0], [1, 0, 0]],
                "measurements": {"distance": distance},
            }
            for distance in (0.4, 0.41)
        ],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 1],
        method="synthetic_copy_receiving",
        parameters={"nested": {"values": [1]}},
        software={"fixture": "1"},
        measure_units={"distance": "nm"},
        atom_source_indices=np.arange(view.molsys.get_n_atoms()) + 100,
        source_n_atoms=view.molsys.get_n_atoms() + 100,
        structure_source_indices=[8, 3, 0],
        source_n_structures=9,
    )
    view.interactions.attach(analysis, name="contacts", assume_aligned=True)
    view.interactions.add("contacts", tag="rings")
    view.regions.add(atom_indices=[0, 1, 2], tag="part", representation="sticks")
    view.annotations.add("original", atom_indices=[0], tag="note")
    view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="sphere")
    try:
        yield view
    finally:
        view.close()


def _coverage(view):
    return view.interactions.get_analysis("contacts").evaluated_structure_indices.tolist()


@pytest.mark.parametrize("edit", ["coordinates", "box", "chemistry"])
def test_view_copy_isolates_controlled_edits_and_retains_old_analysis_handles(source, edit):
    with msv.tools.copy(source) as duplicate:
        original = source.interactions.get_analysis("contacts")
        old_result = duplicate.interactions.get_analysis("contacts")
        old_query = old_result.query(structure_indices=[1, 0])
        source_xyz = puw.get_value(msm.get(source.molsys, coordinates=True), to_unit="nm").copy()
        source_box = puw.get_value(msm.get(source.molsys, box=True), to_unit="nm").copy()
        bonds = source.molsys.chemical_states.get_bonds().copy(deep=True)
        assert original is not old_result
        old_result.parameters["nested"]["values"].append(2)
        assert original.parameters == {"nested": {"values": [1]}}
        if edit == "coordinates":
            msm.set(
                duplicate.molsys,
                selection=[0],
                structure_indices=[0],
                coordinates=puw.quantity([[[10, 20, 30]]], "angstrom"),
            )
            expected = [1]
            np.testing.assert_allclose(
                puw.get_value(
                    msm.get(duplicate.molsys, selection=[0], structure_indices=[0], coordinates=True), to_unit="nm"
                ),
                [[[1, 2, 3]]],
            )
        elif edit == "box":
            msm.set(duplicate.molsys, structure_indices=[1], box=puw.quantity([np.eye(3) * 30], "angstrom"))
            expected = [0]
        else:
            duplicate.molsys.chemical_states.remove_bonds([0], chemical_state="reference")
            assert len(duplicate.molsys.chemical_states.get_bonds()) == len(bonds) - 1
            expected = []
        assert _coverage(duplicate) == expected
        assert _coverage(source) == [0, 1]
        assert old_result.evaluated_structure_indices.tolist() == [0, 1]
        assert old_query.to_dict()["evaluated_structure_indices"].tolist() == [1, 0]
        np.testing.assert_array_equal(puw.get_value(msm.get(source.molsys, coordinates=True), to_unit="nm"), source_xyz)
        np.testing.assert_array_equal(puw.get_value(msm.get(source.molsys, box=True), to_unit="nm"), source_box)
        assert source.molsys.chemical_states.get_bonds().equals(bonds)
        # Edits in the opposite direction cannot modify the copied geometry or coverage.
        copied_xyz = puw.get_value(msm.get(duplicate.molsys, coordinates=True), to_unit="nm").copy()
        msm.set(source.molsys, selection=[1], structure_indices=[1], coordinates=puw.quantity([[[-1, -2, -3]]], "nm"))
        assert _coverage(source) == [0]
        assert _coverage(duplicate) == expected
        np.testing.assert_array_equal(
            puw.get_value(msm.get(duplicate.molsys, coordinates=True), to_unit="nm"), copied_xyz
        )


def test_failed_native_edit_and_visual_edits_do_not_change_the_other_view(source):
    with msv.tools.copy(source) as duplicate:
        before = puw.get_value(msm.get(duplicate.molsys, coordinates=True), to_unit="nm").copy()
        analysis = duplicate.interactions.get_analysis("contacts")
        with pytest.raises(msm.ArgumentError) as error:
            msm.set(duplicate.molsys, selection=[0], structure_indices=[0], coordinates=puw.quantity([[1, 2]], "nm"))
        assert "coordinates" in str(error.value).lower() or "shape" in str(error.value).lower()
        assert duplicate.interactions.get_analysis("contacts") is analysis
        assert _coverage(source) == _coverage(duplicate) == [0, 1]
        np.testing.assert_array_equal(puw.get_value(msm.get(duplicate.molsys, coordinates=True), to_unit="nm"), before)
        duplicate.regions["part"].hide()
        duplicate.annotations.set_text("note", "changed")
        duplicate.shapes["sphere"].hide()
        duplicate.interactions["rings"].hide()
        assert not source.regions["part"]._hidden
        assert source.annotations.info("note")["text"] == "original"
        assert not source.shapes["sphere"]._hidden
        assert not source.interactions["rings"]._hidden


def test_copied_analysis_survives_nonconsecutive_extraction_and_session(source, tmp_path):
    with msv.tools.copy(source) as duplicate:
        with duplicate.extract(selection=list(range(10)), structure_indices=[1, 0]) as subset:
            analysis = subset.interactions.get_analysis("contacts")
            page = analysis.to_page()
            assert page["structure_indices"].tolist() == [1, 1]
            assert page["evaluated_structure_indices"].tolist() == [0, 1]
            assert analysis.structure_source_indices.tolist() == [3, 8]
            assert analysis.atom_source_indices.tolist() == list(range(100, 110))
            assert page["participant_atoms"].tolist() == list(range(6))
            assert page["image_vectors"].tolist() == [[0, 0, 0], [1, 0, 0], [0, 0, 0], [1, 0, 0]]
            path = tmp_path / "copied.msv"
            subset.save_session(path)
            with msv.load_session(path) as restored:
                restored_page = restored.interactions.get_analysis("contacts").to_page()
                for key in ("occurrence_indices", "structure_indices", "participant_atoms", "image_vectors"):
                    np.testing.assert_array_equal(restored_page[key], page[key])
                assert restored_page["measure_units"] == {"distance": "nm"}
                assert restored.interactions.get_analysis("contacts").software == {"fixture": "1"}
                restored.interactions.delete("rings")
                assert subset.interactions.contains("rings")
        assert _coverage(source) == _coverage(duplicate) == [0, 1]
