"""Loading must preserve a usable scene when public atom identity is unavailable."""

from copy import deepcopy
from pathlib import Path

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.interactions import _analysis_signature

import molsysviewer as msv


@pytest.fixture(scope="module")
def source():
    with msv.demo["pentalanine"] as demo:
        return msm.extract(demo.molsys, structure_indices=[0], to_form="molsysmt.MolSys")


def _decorate(view):
    view.regions.add([0, 1], tag="keep_region")
    view.annotations.add("keep", atom_indices=[0], tag="keep_note")
    analysis = view.interactions.hbonds.get_buch_hbonds(name="keep", distance_threshold="4 angstroms")
    view.interactions.add("keep", tag="keep_interactions")
    view.annotations.set_text("keep_note", "redo_text")
    assert view.history.undo()
    assert view.history.can_redo()
    return analysis


def _snapshot(view):
    return {
        "system": view.molsys,
        "coordinates": puw.get_value(view.molsys.structures.coordinates, to_unit="nm").copy()
        if view.molsys is not None else None,
        "state": view.export_state(),
        "sources": view.load_blocks,
        "messages": deepcopy(view._test_message_log),
        "undo": list(view.history._undo),
        "redo": list(view.history._redo),
        "objects": dict(view._scene_objects),
        "analyses": {name: (analysis, _analysis_signature(analysis))
                     for name, analysis in view.molsys.interactions.items()} if view.molsys is not None else {},
    }


def _assert_preserved(view, before):
    assert view.molsys is before["system"]
    if view.molsys is not None:
        np.testing.assert_array_equal(puw.get_value(view.molsys.structures.coordinates, to_unit="nm"),
                                      before["coordinates"])
        assert set(view.molsys.interactions) == set(before["analyses"])
    assert view.export_state() == before["state"]
    assert view.load_blocks == before["sources"]
    assert view._test_message_log == before["messages"]
    assert view.history._undo == before["undo"]
    assert view.history._redo == before["redo"]
    assert view._scene_objects == before["objects"]
    for name, (analysis, signature) in before["analyses"].items():
        assert view.molsys.interactions[name] is analysis
        assert _analysis_signature(analysis) == signature


def _invalid_identity(source):
    broken = msm.copy(source)
    # Coordinates and conversion are valid; the topology points outside its groups.
    # This stays a malformed input after the provider fixes nullable memberships.
    broken.topology.atoms.loc[0, "group_index"] = broken.topology.n_groups
    return broken


def test_initial_load_refuses_unexportable_identity(source):
    with msv.MolSysView() as view:
        before = _snapshot(view)
        with pytest.raises(ValueError, match="atom identities") as failure:
            view.load(_invalid_identity(source))
        assert isinstance(failure.value.__cause__, IndexError)
        _assert_preserved(view, before)
        view.load(source)
        assert view.export_state()["structure"]["n_atoms"] == source.get_n_atoms()


@pytest.mark.parametrize("skip", [False, True])
def test_rejected_replacement_preserves_scene_history_and_analyses(source, tmp_path, skip):
    with msv.new_view(source) as view:
        analysis = _decorate(view)
        assert analysis.n_interactions > 0
        before = _snapshot(view)
        with pytest.raises(ValueError, match="atom identities") as failure:
            view.load(_invalid_identity(source), mode="replace", skip_digestion=skip)
        assert isinstance(failure.value.__cause__, IndexError)
        _assert_preserved(view, before)
        assert view.history.redo()
        assert view.annotations.info("keep_note")["text"] == "redo_text"
        assert view.history.undo()
        assert view.annotations.info("keep_note")["text"] == "keep"
        session = tmp_path / "preserved.msv"
        view.save_session(session)
        with msv.load_session(session) as restored:
            assert restored.load_blocks == view.load_blocks
            assert restored.annotations.info("keep_note")["text"] == "keep"
            assert _analysis_signature(restored.interactions.get_analysis("keep")) == _analysis_signature(analysis)


@pytest.mark.parametrize("batch", [False, True])
def test_real_protein_ligand_load_is_usable_or_refused_before_mutation(tmp_path, batch):
    data = Path(msm.__file__).resolve().parent / "data"
    ligand = msm.convert(str(data / "sdf/caffeine.sdf"), to_form="molsysmt.MolSys")
    with msv.new_view(str(data / "pdb/1vii.pdb"), structure_indices=[0]) as view:
        protein = msm.copy(view.molsys)
        _decorate(view)
        before = _snapshot(view)
        candidate = msm.copy(protein)
        msm.add(candidate, ligand, keep_ids=True, in_place=True)
        try:
            msm.get(candidate, element="atom", group_id=True, group_name=True)
        except IndexError:
            # Current provider (#313): reject safely, retaining its diagnosis.
            with pytest.raises(ValueError, match="atom identities") as failure:
                if batch:
                    view.load([protein, ligand], multiple=True, mode="replace")
                else:
                    view.load(ligand)
            assert isinstance(failure.value.__cause__, IndexError)
            _assert_preserved(view, before)
        else:
            # Once the public provider supports partial hierarchy, exercise the
            # workflow rather than silently skipping the scientific regression.
            if batch:
                view.load([protein, ligand], multiple=True, mode="replace")
            else:
                view.load(ligand)
            assert view.export_state()["structure"]["n_atoms"] == candidate.get_n_atoms()
            assert len(view.load_blocks) == 2
            np.testing.assert_array_equal(puw.get_value(view.molsys.structures.coordinates, to_unit="nm"),
                                          puw.get_value(candidate.structures.coordinates, to_unit="nm"))
            view.regions.add([0, candidate.get_n_atoms() - 1], tag="across_sources")
            assert view.history.undo()
            assert view.history.redo()
        session = tmp_path / "protein.msv"
        view.save_session(session)
        with msv.load_session(session) as restored:
            assert restored.export_state()["structure"] == view.export_state()["structure"]
            assert restored.load_blocks == view.load_blocks
