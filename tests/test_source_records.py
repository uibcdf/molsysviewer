"""Scientific source correspondence survives scene and system transfers."""

import json
import zipfile
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture(scope="module")
def source():
    result = msm.extract(
        msv.demo["pentalanine"].molsys,
        selection=list(range(10)),
        structure_indices=[0, 8, 3],
        to_form="molsysmt.MolSys",
    )
    msm.set(result, time=None)
    return result


def _view(source):
    view = msv.MolSysView(debug_js=True)
    view.widget.send = lambda _message: None
    view.load(
        [source, source],
        multiple=True,
        labels=["A", "B"],
        selection=[[1, 3, 4], [0, 2]],
        structure_indices=[[0, 2, 1], [2, 0, 1]],
        structure_pairing="by_index",
    )
    return view


def _pairs(mapping):
    return [(source + i, current + i) for source, current, length in mapping["runs"] for i in range(length)]


def _assert_coordinates(view, source):
    actual = puw.get_value(view.molsys.structures.coordinates, to_unit="nm")
    original = puw.get_value(source.structures.coordinates, to_unit="nm")
    for record in view.load_blocks:
        for old_frame, frame in _pairs(record["structure_map"]):
            for old_atom, atom in _pairs(record["atom_map"]):
                np.testing.assert_array_equal(actual[frame, atom], original[old_frame, old_atom])


def test_state_copy_and_session_preserve_sources_and_deleted_region_links(source, tmp_path):
    view = _view(source)
    view.regions["A"].rename("renamed")
    view.regions["renamed"].show_only()
    view.regions["B"].delete()
    expected = view.load_blocks
    copied = msv.tools.basic.copy(view)
    assert copied.load_blocks == expected
    assert copied.export_state() == view.export_state()
    document = json.loads(json.dumps(view.export_state()))
    target = msv.new_view(msm.copy(view.molsys))
    target.import_state(document)
    assert target.load_blocks == expected
    path = tmp_path / "sources.msv"
    view.save_session(path)
    restored = msv.load_session(path)
    assert restored.load_blocks == expected
    assert restored.regions["renamed"]._show_only
    restored.load(source, selection=[0], structure_pairing="by_index")
    assert len(restored.regions) == 2
    assert restored.load_blocks[1]["region_tag"] is None


def test_extract_remaps_sparse_atoms_and_reordered_duplicate_frames(source):
    view = _view(source)
    extracted = view.extract(selection=[0, 2, 4], structure_indices=[2, 0, 2])
    assert [r["source_id"] for r in extracted.load_blocks] == [r["source_id"] for r in view.load_blocks]
    assert _pairs(extracted.load_blocks[0]["atom_map"]) == [(1, 0), (4, 1)]
    assert _pairs(extracted.load_blocks[1]["atom_map"]) == [(2, 2)]
    assert _pairs(extracted.load_blocks[0]["structure_map"]) == [(1, 0), (0, 1), (1, 2)]
    assert _pairs(extracted.load_blocks[1]["structure_map"]) == [(1, 0), (2, 1), (1, 2)]
    _assert_coordinates(extracted, source)
    only_b = view.extract(selection=[3, 4], structure_indices=[1, 0])
    assert len(only_b.load_blocks) == 1
    assert only_b.load_blocks[0]["source_id"] == view.load_blocks[1]["source_id"]
    assert only_b.load_blocks[0]["index"] == 0
    _assert_coordinates(only_b, source)


def test_history_restores_source_region_identity_without_recreating_deleted_sources(source):
    view = _view(source)
    ids = [r["source_id"] for r in view.load_blocks]
    view.history.clear()
    view.regions["A"].delete()
    assert view.load_blocks[0]["region_tag"] is None
    view.history.undo()
    assert view.load_blocks[0]["region_tag"] == "A"
    view.history.redo()
    assert view.load_blocks[0]["region_tag"] is None
    assert [r["source_id"] for r in view.load_blocks] == ids


def test_announced_removal_remaps_sources_and_unmapped_growth_has_explicit_origin(source):
    view = _view(source)
    ids = [r["source_id"] for r in view.load_blocks]
    kept = [0, 2, 4]
    edited = msm.extract(view.molsys, selection=kept, to_form="molsysmt.MolSys")
    view.apply_system_edit(edited, atom_index_map={old: new for new, old in enumerate(kept)})
    assert [r["source_id"] for r in view.load_blocks] == ids
    _assert_coordinates(view, source)
    grown = msm.copy(view.molsys)
    msm.add(grown, msm.extract(source, selection=[0], to_form="molsysmt.MolSys"), in_place=True)
    view.apply_system_edit(grown, atom_index_map={i: i for i in range(3)})
    assert [r["source_id"] for r in view.load_blocks[:2]] == ids
    assert view.load_blocks[-1]["origin"]["kind"] == "unmapped_edit"
    assert _pairs(view.load_blocks[-1]["atom_map"]) == [(3, 3)]
    assert view.export_state()["sources"]["binding"]["n_atoms"] == 4


def test_atom_domain_change_without_correspondence_collapses_to_current_whole(source):
    view = _view(source)
    ids = {r["source_id"] for r in view.load_blocks}
    edited = msm.extract(view.molsys, selection=[0, 2, 4], to_form="molsysmt.MolSys")
    view.apply_system_edit(edited)
    assert len(view.load_blocks) == 1 and view.load_blocks[0]["source_id"] not in ids
    assert _pairs(view.load_blocks[0]["atom_map"]) == [(0, 0), (1, 1), (2, 2)]


def test_frame_edit_invalidates_unknown_map_and_explicit_append_keeps_known_prefix(source):
    view = _view(source)
    edited = msm.extract(view.molsys, structure_indices=[2, 0], to_form="molsysmt.MolSys")
    view.apply_system_edit(edited)
    assert all(r["structure_map"] == {"encoding": "runs", "runs": [], "status": "unverified"} for r in view.load_blocks)
    view = _view(source)
    original = view.load_blocks
    view.load(msm.copy(view.molsys), mode="append_structures")
    assert view.molsys.structures.n_structures == 6
    assert view.load_blocks == original
    extracted = view.extract(structure_indices=[4, 0])
    assert _pairs(extracted.load_blocks[0]["structure_map"]) == [(0, 1)]


@pytest.mark.parametrize("mapping", [{0: 5}, {5: 0}, {0: 0, 1: 0}, {True: 0}, {0: 1.5}])
def test_invalid_announced_correspondence_preserves_system_scene_and_history(source, mapping):
    view = _view(source)
    system, state = view.molsys, view.export_state()
    messages, history = deepcopy(view._test_message_log), list(view.history._undo)
    with pytest.raises(ValueError):
        view.apply_system_edit(msm.copy(system), atom_index_map=mapping, skip_digestion=True)
    assert view.molsys is system and view.export_state() == state
    assert view._test_message_log == messages and view.history._undo == history


@pytest.mark.parametrize("damage", ["version", "id", "bool", "bounds", "overlap", "count"])
def test_invalid_source_state_is_refused_before_scene_mutation(source, damage):
    view = _view(source)
    view.annotations.add("keep", atom_indices=[0], tag="keep")
    state = view.export_state()
    document = deepcopy(state)
    records = document["sources"]["records"]
    if damage == "version":
        document["sources"]["version"] = 2
    elif damage == "id":
        records[1]["source_id"] = records[0]["source_id"]
    elif damage == "bool":
        records[0]["atom_map"]["runs"][0][0] = True
    elif damage == "bounds":
        records[0]["atom_map"]["runs"][0][1] = 99
    elif damage == "overlap":
        records[1]["atom_map"]["runs"][0][1] = 0
        records[1]["start"] = 0
        records[1]["stop"] = 2
    else:
        records[0]["n_atoms"] = 100
    handle = view.annotations["keep"]
    with pytest.raises(ValueError):
        view.import_state(document, skip_digestion=True)
    assert view.export_state() == state and view.annotations["keep"] is handle


def test_source_maps_do_not_replay_on_another_geometry_or_without_the_extension(source):
    view = _view(source)
    target = _view(source)
    target.partial_coordinates_update(puw.quantity([[9.0, 8.0, 7.0]], "nm"), selection=[0], structure_indices=[0])
    own_ids = [r["source_id"] for r in target.load_blocks]
    assert target.export_state()["structure"] == view.export_state()["structure"]
    target.import_state(view.export_state())
    assert [r["source_id"] for r in target.load_blocks] == own_ids
    legacy = deepcopy(view.export_state())
    legacy.pop("sources")
    target.import_state(legacy)
    assert [r["source_id"] for r in target.load_blocks] == own_ids


def test_overlay_import_keeps_the_destination_source_inventory(source):
    source_view, target = _view(source), _view(source)
    own_ids = [r["source_id"] for r in target.load_blocks]
    target.import_state(source_view.export_state(), clear_first=False, on_conflict="rename")
    assert [r["source_id"] for r in target.load_blocks] == own_ids


def test_merge_repeated_sources_keeps_lineage_and_remaps_region_links(source):
    view = _view(source)
    merged = msv.tools.basic.merge([view, msv.tools.basic.copy(view)])
    records = merged.load_blocks
    assert len(records) == 4 and len({r["source_id"] for r in records}) == 4
    assert [r["source_id"] for r in records[:2]] == [r["source_id"] for r in view.load_blocks]
    assert [r["parent_source_id"] for r in records[2:]] == [r["source_id"] for r in view.load_blocks]
    assert len(merged.regions) == 4
    for record in records:
        region = merged.regions[record["region_tag"]]
        assert region.uid == record["region_uid"]
        assert region.provenance["source_id"] == record["source_id"]
        assert list(region.atom_indices) == [current for _, current in _pairs(record["atom_map"])]
    _assert_coordinates(merged, source)


def test_binding_is_cached_metadata_is_compact_and_precision_survives_session(source, tmp_path):
    view = _view(source)
    before = view.export_state()
    cache = view._source_binding_memo
    assert view.export_state() == before and view._source_binding_memo is cache
    assert len(json.dumps(before["sources"])) < 4000
    coordinates = puw.get_value(view.get_coordinates(), to_unit="nm").copy()
    coordinates[0, 0, 0] += 0.12345678912345
    view.set_coordinates(puw.quantity(coordinates, "nm"))
    after = view.export_state()
    assert after["sources"]["binding"] != before["sources"]["binding"]
    assert after["sources"]["records"] == before["sources"]["records"]
    path = tmp_path / "precise.msv"
    view.save_session(path)
    restored = msv.load_session(path)
    assert restored.load_blocks == view.load_blocks
    np.testing.assert_array_equal(puw.get_value(restored.get_coordinates(), to_unit="nm"), coordinates)


def test_mismatched_session_binding_preserves_existing_destination(source, tmp_path):
    view, destination = _view(source), _view(source)
    path = tmp_path / "broken.msv"
    view.save_session(path)
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    state = json.loads(members["state.json"])
    state["sources"]["binding"]["fingerprint"] = "sha256:" + "0" * 64
    members["state.json"] = json.dumps(state).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    original, before = destination.molsys, destination.export_state()
    with pytest.raises(ValueError, match="source maps"):
        msv.load_session(path, view=destination)
    assert destination.molsys is original and destination.export_state() == before
