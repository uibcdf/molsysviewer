"""Independent-system load intent, source correspondence and atomic preparation."""

import warnings
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture(scope="module")
def source_system():
    return msm.extract(
        msv.demo["pentalanine"].molsys,
        selection=list(range(10)),
        structure_indices=[0, 8, 3],
        to_form="molsysmt.MolSys",
    )


def _single(source_system):
    return msm.extract(source_system, structure_indices=[0], to_form="molsysmt.MolSys")


def _view():
    view = msv.MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None
    return view


def _values(view):
    return puw.get_value(view.get_coordinates(), to_unit="nm")


def _pairs(mapping):
    return [(source + i, current + i) for source, current, length in mapping["runs"] for i in range(length)]


def _unchanged(view, original, state, records, messages, undo):
    assert view.molsys is original
    assert view.export_state() == state
    assert view.load_blocks == records
    assert view._test_message_log == messages
    assert view.history._undo == undo


def test_batch_and_progressive_scientific_and_region_results_agree(source_system):
    source = _single(source_system)
    batch, progressive = _view(), _view()
    batch.load([source] * 4, multiple=True, labels=["A", "A", "C", None])
    for label in ["A", "A", "C", None]:
        progressive.load(source, label=label)
    np.testing.assert_array_equal(_values(batch), _values(progressive))
    assert batch.molsys.get_n_atoms() == 40
    assert len(batch.regions) == len(progressive.regions) == 4
    for left, right in zip(batch.load_blocks, progressive.load_blocks):
        assert left["label"] == right["label"]
        assert left["atom_map"] == right["atom_map"]
        assert batch.regions[left["region_tag"]].atom_indices == progressive.regions[right["region_tag"]].atom_indices
        assert batch.regions[left["region_tag"]].representation is None
    assert len({r["source_id"] for r in batch.load_blocks}) == 4
    payload = batch._materialize_molecular_projection(batch._current_molecular_projection)["payload"]
    assert len(set(payload["atoms"]["chain_index"])) == 4


def test_single_and_nested_complementary_forms_keep_one_system_intent(source_system, tmp_path):
    source = _single(source_system)
    complementary = [source.topology, source.structures]
    single = _view()
    single.load(complementary)
    assert len(single.load_blocks) == 1 and len(single.regions) == 0
    np.testing.assert_array_equal(_values(single), puw.get_value(source.structures.coordinates, to_unit="nm"))
    pdb = tmp_path / "source.pdb"
    msm.convert(source, to_form=str(pdb))
    mixed = _view()
    mixed.load([pdb, complementary], multiple=True, labels=["File", "Forms"])
    assert mixed.molsys.get_n_atoms() == 20
    assert mixed.load_blocks[0]["origin"]["reference"] == str(pdb)
    assert len(mixed.load_blocks[1]["origin"]["items"]) == 2


def test_source_atom_and_reordered_frame_maps_resolve_actual_coordinates(source_system):
    source = msm.copy(source_system)
    msm.set(source, time=None)
    view = _view()
    view.load(
        [source, source],
        multiple=True,
        selection=[[1, 3, 4], [0, 2]],
        structure_indices=[[0, 2], [2, 0]],
        structure_pairing="by_index",
        labels=[None, "second"],
    )
    records = view.load_blocks
    for record in records:
        atoms, frames = _pairs(record["atom_map"]), _pairs(record["structure_map"])
        for source_frame, current_frame in frames:
            for source_atom, current_atom in atoms:
                np.testing.assert_array_equal(
                    _values(view)[current_frame, current_atom],
                    puw.get_value(source.structures.coordinates, to_unit="nm")[source_frame, source_atom],
                )
    assert records[0]["atom_map"]["runs"] == [[1, 0, 1], [3, 1, 2]]
    assert view.molsys.structures.time is None
    records[0]["atom_map"]["runs"][0][0] = 999
    assert view.load_blocks[0]["atom_map"]["runs"][0][0] == 1


def test_common_flat_selectors_do_not_become_per_source_by_length(source_system):
    source = msm.copy(source_system)
    msm.set(source, time=None)
    view = _view()
    view.load([source, source], multiple=True, selection=[1, 2], structure_indices=[2, 0], structure_pairing="by_index")
    assert view.molsys.get_n_atoms() == 4
    assert view.molsys.structures.n_structures == 2
    for record in view.load_blocks:
        assert _pairs(record["structure_map"]) == [(2, 0), (0, 1)]


def test_source_identity_survives_region_rename_delete_and_later_add(source_system):
    source = _single(source_system)
    view = _view()
    view.load(source)
    assert len(view.regions) == 0
    identity = view.load_blocks[0]["source_id"]
    view.load(source)
    first = view.load_blocks[0]
    view.regions[first["region_tag"]].rename("renamed")
    assert view.load_blocks[0]["region_tag"] == "renamed"
    view.regions["renamed"].delete()
    assert view.load_blocks[0]["source_id"] == identity
    assert view.load_blocks[0]["region_tag"] is None
    view.load(source)
    assert len(view.regions) == 2
    assert view.load_blocks[0]["region_tag"] is None


@pytest.mark.parametrize("mode", ["add", "replace"])
def test_bad_later_source_preserves_system_scene_sources_and_history(source_system, tmp_path, mode):
    view = _view()
    source = _single(source_system)
    view.load(source)
    view.annotations.add("keep", atom_indices=[0], tag="note")
    original, state, records = view.molsys, view.export_state(), view.load_blocks
    messages, undo = deepcopy(view._test_message_log), list(view.history._undo)
    broken = tmp_path / "broken.h5msm"
    broken.write_bytes(b"not HDF5")
    with pytest.raises(OSError):
        view.load([source, broken], multiple=True, mode=mode, skip_digestion=True)
    _unchanged(view, original, state, records, messages, undo)


@pytest.mark.parametrize(
    "options",
    [
        {"labels": ["only one"]},
        {"labels": "AB"},
        {"labels": ["A", 1]},
        {"mode": "auto"},
        {"mode": "append_structures"},
        {"multiple": 1},
        {"structure_pairing": "automatic"},
        {"structure_indices": [[0]]},
        {"structure_indices": [True]},
        {"selection": [True]},
        {"selection": []},
        {"structure_indices": [99]},
        {"structure_indices": [-1]},
        {"selection": [True], "syntax": "MDTraj"},
        {"selection": [1.5], "syntax": "MDTraj"},
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_batch_arguments_fail_before_scene_mutation(source_system, options, skip):
    source = _single(source_system)
    view = _view()
    view.load(source)
    before = (
        view.molsys,
        view.export_state(),
        view.load_blocks,
        deepcopy(view._test_message_log),
        list(view.history._undo),
    )
    kwargs = {"multiple": True, **options}
    with pytest.raises(Exception):
        view.load([source, source], **kwargs, skip_digestion=skip)
    _unchanged(view, *before)


def test_trajectory_pairing_is_explicit_and_times_use_physical_units(source_system):
    left, right = msm.copy(source_system), msm.copy(source_system)
    msm.set(left, time=puw.quantity([0.0, 1.0, 2.0], "ns"))
    msm.set(right, time=puw.quantity([0.0, 1000.0, 2000.0], "ps"))
    view = _view()
    with pytest.raises(ValueError, match="structure_pairing"):
        view.load([left, right], multiple=True)
    assert view.molsys is None
    view.load([left, right], multiple=True, structure_pairing="by_index")
    np.testing.assert_allclose(
        puw.get_value(view.molsys.structures.time, to_unit="ps"), [0, 1000, 2000], rtol=1e-9, atol=1e-9
    )
    mismatched = msm.copy(right)
    msm.set(mismatched, time=puw.quantity([0.0, 1001.0, 2000.0], "ps"))
    before = (
        view.molsys,
        view.export_state(),
        view.load_blocks,
        deepcopy(view._test_message_log),
        list(view.history._undo),
    )
    with pytest.raises(ValueError, match="times"):
        view.load(mismatched, structure_pairing="by_index")
    _unchanged(view, *before)
    with pytest.raises(ValueError, match="same number"):
        view.load(_single(source_system), structure_pairing="by_index")
    _unchanged(view, *before)


def test_first_box_policy_including_absence_and_manual_removal(source_system):
    left, right = _single(source_system), _single(source_system)
    msm.set(left, box=None)
    msm.set(right, box=puw.quantity(np.eye(3) * 2, "nm"))
    view = _view()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=Warning)
        view.load([left, right], multiple=True)
        assert view.molsys.structures.box is None
        msm.set(view.molsys, box=puw.quantity(np.eye(3) * 5, "nm"))
        view.load(right)
        np.testing.assert_array_equal(puw.get_value(view.molsys.structures.box, to_unit="nm"), [np.eye(3) * 5])
        msm.set(view.molsys, box=None)
        view.load(right)
        assert view.molsys.structures.box is None


def _analysis(source):
    return msm.Interactions.from_records(
        [
            {
                "structure_index": 0,
                "interaction_type": "hbond",
                "participants": [
                    {"role": role, "atom_indices": [i]} for i, role in enumerate(("donor", "hydrogen", "acceptor"))
                ],
            }
        ],
        n_atoms=source.get_n_atoms(),
        n_structures=1,
        evaluated_structure_indices=[0],
        method="fixture",
    )


def test_named_incoming_analyses_reject_and_destination_analyses_survive(source_system):
    source = _single(source_system)
    with_analysis = msm.copy(source)
    with_analysis.interactions = {"contacts": _analysis(source)}
    view = _view()
    view.load(with_analysis)
    assert "contacts" in view.molsys.interactions
    original_result = view.molsys.interactions["contacts"]
    view.interactions.add("contacts", tag="hb")
    before = (
        view.molsys,
        view.export_state(),
        view.load_blocks,
        deepcopy(view._test_message_log),
        list(view.history._undo),
    )
    with pytest.raises(ValueError, match="analysis-merge"):
        view.load([source, with_analysis], multiple=True)
    _unchanged(view, *before)
    view.load(source)
    result = view.molsys.interactions["contacts"]
    assert result.n_atoms == 20
    assert result.evaluated_structure_indices.tolist() == []
    assert original_result.evaluated_structure_indices.tolist() == [0]
    assert view.interactions["hb"].broken is False


def test_batch_replace_resets_scene_after_success_and_skip_has_same_result(source_system):
    source = _single(source_system)
    view = _view()
    view.load(source)
    old_id = view.load_blocks[0]["source_id"]
    view.annotations.add("old", atom_indices=[0])
    view.load([source, source], multiple=True, labels=[None, "B"], mode="replace", skip_digestion=True)
    assert view.annotations.count() == 0
    assert view.molsys.get_n_atoms() == 20
    assert len(view.regions) == len(view.load_blocks) == 2
    assert old_id not in {r["source_id"] for r in view.load_blocks}
