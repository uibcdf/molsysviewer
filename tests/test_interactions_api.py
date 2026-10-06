"""Scientific interaction workflows on real demo systems, without an addon.

Small synthetic observations attached to real MolSys axes exercise sparse
query/import semantics; separate calculations exercise the real detectors.
"""

import json
import warnings
import zipfile
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from argdigest import UnknownArgumentError
from molsysviewer._private.exceptions.interaction_analysis_error import InteractionAnalysisError
from molsysviewer.demo import demo
from molsysviewer.interactions import _analysis_signature
from molsysviewer.session import SessionFormatError

import molsysviewer as msv


@pytest.fixture
def view():
    return msv.new_view(demo["pentalanine"].molsys, structure_indices=[0, 8, 3])


def _observations(view):
    participants = [
        {"role": role, "atom_indices": [index]} for index, role in enumerate(("donor", "hydrogen", "acceptor"))
    ]
    records = [
        {
            "structure_index": 0,
            "interaction_type": "hbond",
            "participants": participants,
            "measurements": {"distance": distance},
            "images": [[0, 0, 0], [1, 0, 0], [1, 0, 0]],
        }
        for distance in (0.2, 0.21)
    ]
    records.append(
        {
            "structure_index": 0,
            "interaction_type": "pi_stacking",
            "participants": [{"role": "ring", "atom_indices": [3, 4]}, {"role": "ring", "atom_indices": [5, 6]}],
            "measurements": {"distance": 0.4},
            "images": [[0, 0, 0], [0, 1, 0]],
        }
    )
    return msm.Interactions.from_records(
        records,
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 1],
        method="synthetic_query_fixture",
        measure_units={"distance": "nm"},
        parameters={"threshold_nm": 0.5},
        source_id="declared-demo-axis",
        software={"fixture": "1"},
        atom_source_indices=np.arange(view.molsys.get_n_atoms()) + 100,
        source_n_atoms=view.molsys.get_n_atoms() + 100,
        structure_source_indices=[8, 20, 3],
        source_n_structures=21,
    )


def _attach(view, name="contacts"):
    result = _observations(view)
    view.interactions.attach(result, name=name, assume_aligned=True)
    return result


def test_attachment_declares_alignment_and_does_not_overwrite(view):
    result = _observations(view)
    with pytest.raises(InteractionAnalysisError, match="assume_aligned=True"):
        view.interactions.attach(result, name="contacts")
    assert view.interactions.analyses() == []
    attached = view.interactions.attach(result, name="contacts", assume_aligned=True)
    assert attached is view.molsys.interactions["contacts"] is result
    with pytest.raises(InteractionAnalysisError, match="already exists"):
        view.interactions.attach(result.remap(), name="contacts", assume_aligned=True)
    assert view.interactions.get_analysis("contacts") is result


def test_attachment_rejects_query_views_and_wrong_axes_atomically(view):
    original = _attach(view)
    with pytest.raises(ValueError, match="full Interactions"):
        view.interactions.attach(original.query(structure_indices=[0]), name="filtered", assume_aligned=True)
    wrong = original.remap(atom_indices=[0, 1, 2])
    with pytest.raises(ValueError, match="domains"):
        view.interactions.attach(wrong, name="wrong", assume_aligned=True)
    assert dict(view.molsys.interactions) == {"contacts": original}


def test_metadata_is_compact_and_detached_from_scientific_parameters(view):
    result = _attach(view)
    records = view.interactions.analyses()
    assert records[0]["n_occurrences"] == 3
    assert records[0]["n_evaluated_structures"] == 2
    assert records[0]["software"] == {"fixture": "1"}
    assert "participant_atoms" not in records[0]
    assert "evaluated_structure_indices" not in records[0]
    records[0]["parameters"]["threshold_nm"] = 99
    assert result.parameters["threshold_nm"] == 0.5
    assert result.numeric_nbytes < result.n_atoms**2 * result.n_structures * 8
    with pytest.raises(KeyError):
        view.interactions.get_analysis("absent")


def test_discovered_existing_analysis_names_are_looked_up_exactly(view):
    result = _observations(view)
    view.molsys.interactions = {" stored name ": result}
    name = view.interactions.analyses()[0]["name"]
    assert name == " stored name "
    assert view.interactions.get_analysis(name) is result
    assert view.interactions.query(name).n_interactions == 3


def test_nonconsecutive_frames_preserve_parallel_identity_and_empty_coverage(view):
    result = _attach(view)
    query = view.interactions.query("contacts", structure_indices=[1, 2, 0, 1], interaction_types="hbond")
    data = query.to_dict()
    np.testing.assert_array_equal(data["evaluated_structure_indices"], [1, 0])
    np.testing.assert_array_equal(data["structure_indices"], [0, 0])
    np.testing.assert_array_equal(data["occurrence_indices"], [0, 1])
    assert query.participant_atoms is result.participant_atoms
    np.testing.assert_array_equal(
        view.interactions.query("contacts", structure_indices=1).to_dict()["evaluated_structure_indices"], [1]
    )
    assert view.interactions.query("contacts", structure_indices=1).n_interactions == 0
    assert view.interactions.query("contacts", structure_indices=2).to_dict()["evaluated_structure_indices"].size == 0


def test_atom_queries_include_hydrogen_and_all_group_members(view):
    _attach(view)
    assert view.interactions.query("contacts", selection=1).n_interactions == 2
    assert view.interactions.query("contacts", selection=[0, 2], mode="within_selection").n_interactions == 0
    assert view.interactions.query("contacts", selection=[0, 1, 2], mode="within_selection").n_interactions == 2
    assert view.interactions.query("contacts", selection=[0, 2], mode="across_selection_boundary").n_interactions == 2
    assert view.interactions.query("contacts", selection=[3], interaction_types="pi_stacking").n_interactions == 1
    assert view.interactions.query("contacts", selection=[3, 5], mode="within_selection").n_interactions == 0
    assert view.interactions.query("contacts", selection=[3, 4, 5, 6], mode="within_selection").n_interactions == 1
    assert view.interactions.query("contacts", selection="atom_index == 1").n_interactions == 2


def test_between_queries_delegate_disjoint_and_exclusive_semantics(view):
    _attach(view)
    assert (
        view.interactions.query("contacts", mode="between_selections", selection=[0], selection_2=[2]).n_interactions
        == 2
    )
    assert (
        view.interactions.query(
            "contacts", mode="between_selections", selection=[0], selection_2=[2], exclusive=True
        ).n_interactions
        == 0
    )
    assert (
        view.interactions.query(
            "contacts", mode="between_selections", selection=[0, 1], selection_2=[2], exclusive=True
        ).n_interactions
        == 2
    )
    with pytest.raises(ValueError, match="disjoint"):
        view.interactions.query("contacts", mode="between_selections", selection=[0], selection_2=[0])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "between_selections"},
        {"selection_2": [2]},
        {"exclusive": True},
        {"structure_indices": [-1]},
        {"structure_indices": [3]},
        {"structure_indices": [True]},
        {"structure_indices": [[0]]},
        {"selection": [True]},
        {"selection": [0.9]},
        {"selection": [-1]},
    ],
)
def test_bad_queries_fail_without_mutating_scientific_data(view, kwargs):
    result = _attach(view)
    with pytest.raises(ValueError):
        view.interactions.query("contacts", **kwargs)
    assert view.molsys.interactions["contacts"] is result


def test_calculation_defaults_to_current_frame_and_retains_provenance(view):
    view.player.go_to_structure(2)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        result = view.interactions.hbonds.get_buch_hbonds(name="buch", distance_threshold="4 angstroms")
    assert not [warning for warning in emitted if "has no digester" in str(warning.message)]
    assert isinstance(result, msm.Interactions)
    np.testing.assert_array_equal(result.evaluated_structure_indices, [2])
    assert result.n_structures == 3
    assert result.n_interactions > 0
    assert result.parameters["distance_definition"] == "hydrogen_acceptor"
    assert result.parameters["distance_threshold_nm"] == pytest.approx(0.4)
    assert result.parameters["pbc"] is False
    assert result.software == {"molsysmt": msm.__version__}
    assert result.measure_units["distance"] == "nm"
    assert [part["role"] for part in result.relation(0)["participants"]] == ["donor", "hydrogen", "acceptor"]
    assert view.interactions.get_analysis("buch") is result
    view.player.go_to_structure(1)
    assert result.query(structure_indices=[1]).to_dict()["evaluated_structure_indices"].size == 0


def test_calculation_selected_axes_and_failures_preserve_existing_data(view):
    result = view.interactions.hbonds.get_buch_hbonds(name="buch", structure_indices=[2, 0, 2])
    np.testing.assert_array_equal(result.evaluated_structure_indices, [2, 0])
    expected = msm.interactions.hbonds.get_buch_hbonds(
        view.molsys, structure_indices=[2, 0], pbc=False, output_type="molsysmt.Interactions"
    )
    assert _analysis_signature(result) == _analysis_signature(expected)
    for kwargs in (
        {"name": "buch"},
        {"name": "bad", "pbc": "yes"},
        {"name": "bad", "distance_threshold": "not a length"},
    ):
        with pytest.raises(ValueError):
            view.interactions.hbonds.get_buch_hbonds(**kwargs)
    # A named scientific criterion cannot be overridden through a hidden option.
    with pytest.raises(UnknownArgumentError, match="method"):
        view.interactions.hbonds.get_buch_hbonds(name="bad", method="unknown")
    assert dict(view.molsys.interactions) == {"buch": result}


def test_disulfide_candidates_keep_empty_evaluated_frames_and_do_not_edit_topology(view):
    before = int(msm.get(view.molsys, n_bonds=True))
    result = view.interactions.disulfides.get_disulfide_candidates(name="candidates", structure_indices="all")
    assert result.n_interactions == 0  # the real pentalanine demo has no cysteine
    np.testing.assert_array_equal(result.evaluated_structure_indices, [0, 1, 2])
    assert result.method.endswith("get_disulfide_candidates")
    assert result.parameters["max_bond_length_nm"] == pytest.approx(0.205)
    assert int(msm.get(view.molsys, n_bonds=True)) == before


def test_periodic_calculation_requires_boxes_and_retains_observed_images(view):
    view.molsys.structures.box = None
    with pytest.raises(InteractionAnalysisError, match="boxes"):
        view.interactions.hbonds.get_buch_hbonds(name="periodic", pbc=True)
    assert view.interactions.analyses() == []
    view.molsys.structures.box = msm.pyunitwizard.quantity(np.zeros((3, 3, 3)), "nm")
    with pytest.raises(InteractionAnalysisError, match="boxes"):
        view.interactions.hbonds.get_buch_hbonds(name="singular", pbc=True)
    view.molsys.structures.box = msm.pyunitwizard.quantity(np.repeat((np.eye(3) * 2)[None], 3, axis=0), "nm")
    result = view.interactions.hbonds.get_buch_hbonds(
        name="periodic", pbc=True, distance_threshold="4 angstroms", structure_indices=[2, 0]
    )
    assert result.n_interactions > 0
    assert result.parameters["pbc"] is True
    assert result.to_dict()["image_vectors"] is not None


@pytest.mark.parametrize("complete_system", [False, True])
def test_loading_h5msm_requires_declaration_and_keeps_view_coordinates(view, tmp_path, complete_system):
    result = _observations(view)
    source = view.molsys.copy()
    source.interactions = {"stored": result}
    filename = tmp_path / "contacts.h5msm"
    if complete_system:
        msm.h5msm.write(source, str(filename))
    else:
        msm.h5msm.write_layers(str(filename), interactions={"stored": result})
    original_system = view.molsys
    before = msm.get(original_system, coordinates=True)
    with pytest.raises(InteractionAnalysisError, match="assume_aligned"):
        view.interactions.load(filename, analysis_name="stored")
    loaded = view.interactions.load(filename, analysis_name="stored", name="imported", assume_aligned=True)
    assert _analysis_signature(loaded) == _analysis_signature(result)
    assert view.molsys is original_system
    np.testing.assert_array_equal(
        msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True)), msm.pyunitwizard.get_value(before)
    )
    with pytest.raises(KeyError):
        view.interactions.load(filename, analysis_name="absent", assume_aligned=True)
    assert set(view.molsys.interactions) == {"imported"}


def test_import_remaps_source_axes_including_repeated_structures(view, tmp_path):
    result = _observations(view)
    filename = tmp_path / "contacts.h5msm"
    msm.h5msm.write_layers(str(filename), interactions={"stored": result})
    target = msv.new_view(view.molsys, selection=[2, 1, 0], structure_indices=[0, 0, 1])
    loaded = target.interactions.load(
        filename, analysis_name="stored", assume_aligned=True, atom_indices=[2, 1, 0], structure_indices=[0, 0, 1]
    )
    assert loaded.n_atoms == 3 and loaded.n_structures == 3
    np.testing.assert_array_equal(loaded.atom_source_indices, [102, 101, 100])
    np.testing.assert_array_equal(loaded.structure_source_indices, [8, 8, 20])
    assert loaded.query(structure_indices=[0, 1]).n_interactions == 4
    assert loaded.query(structure_indices=[2]).n_interactions == 0


def test_molecular_edits_invalidate_by_default_and_allow_declared_preservation(view):
    _attach(view)
    edited = view.molsys.copy()
    view.apply_system_edit(edited)
    assert view.interactions.get_analysis("contacts").n_interactions == 0
    assert view.interactions.get_analysis("contacts").evaluated_structure_indices.size == 0
    original = _observations(view)
    preserved = view.molsys.copy()
    preserved.interactions = {"contacts": original}
    view.apply_system_edit(preserved, interactions_policy="preserve")
    assert view.interactions.get_analysis("contacts") is original


def test_same_object_edit_revision_rejects_a_stale_publication(view):
    result = _observations(view)
    original_system = view.molsys
    revision = view.interactions._system_revision
    view.apply_system_edit(original_system)
    with pytest.raises(InteractionAnalysisError, match="changed"):
        view.interactions._publish(result, "stale", original_system, revision)
    assert view.interactions.analyses() == []


def test_explicit_data_deletion_clears_undo_and_does_not_remove_other_analyses(view):
    _attach(view)
    view.interactions.disulfides.get_disulfide_candidates(name="other")
    view.regions.add(atom_indices=[0, 1], tag="region")
    assert view.history.can_undo()
    view.interactions.delete_analysis("contacts")
    assert not view.history.can_undo()
    assert set(view.molsys.interactions) == {"other"}
    assert view.regions.contains("region")


@pytest.mark.parametrize("reuse", [False, True])
def test_session_preserves_two_scientific_analyses_and_overlay_state(view, tmp_path, reuse):
    result = _attach(view)
    view.interactions.disulfides.get_disulfide_candidates(name="empty", structure_indices=[2, 0])
    view.regions.add(atom_indices=[0, 1], tag="region")
    path = tmp_path / "interactions.msv"
    view.save_session(path)
    destination = demo["dialanine"] if reuse else None
    restored = msv.load_session(path, view=destination)
    if reuse:
        assert restored is destination
    assert restored.molsys.get_n_atoms() == view.molsys.get_n_atoms()
    assert restored.molsys.structures.n_structures == 3
    assert set(restored.molsys.interactions) == {"contacts", "empty"}
    assert _analysis_signature(restored.interactions.get_analysis("contacts")) == _analysis_signature(result)
    np.testing.assert_array_equal(restored.interactions.get_analysis("empty").evaluated_structure_indices, [2, 0])
    assert restored.regions["region"].atom_indices == view.regions["region"].atom_indices
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(manifest["interaction_analyses"]["signatures"]) == {"contacts", "empty"}
        # Scientific arrays live in H5MSM, never duplicated into JSON scene undo.
        assert "occurrence_structures" not in archive.read("state.json").decode()


@pytest.mark.parametrize("damage", ["signature", "missing_name", "version"])
def test_session_rejects_changed_scientific_manifest_before_touching_destination(view, tmp_path, damage):
    _attach(view)
    path = tmp_path / "interactions.msv"
    view.save_session(path)
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members["manifest.json"])
    if damage == "signature":
        manifest["interaction_analyses"]["signatures"]["contacts"] = "sha256:changed"
    elif damage == "missing_name":
        manifest["interaction_analyses"]["signatures"].clear()
    else:
        manifest["interaction_analyses"]["version"] = 99
    members["manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in members.items():
            archive.writestr(name, value)
    destination = demo["dialanine"]
    before_system = destination.molsys
    before_state = deepcopy(destination.export_state())
    error_type = SessionFormatError if damage == "version" else InteractionAnalysisError
    expected_message = "Unsupported interaction-analysis" if damage == "version" else "differs"
    with pytest.raises(error_type, match=expected_message):
        msv.load_session(path, view=destination)
    assert destination.molsys is before_system
    assert destination.export_state() == before_state


def test_catalog_exception_is_reconstructible_and_keeps_structured_reason():
    error = InteractionAnalysisError(reason="name_conflict", extra={"name": "buch"})
    assert error.code == "MOLSYSVIEWER-INTERACTION-NAME-CONFLICT"
    assert error.extra["name"] == "buch"
    assert type(error)(*error.args).args == error.args


def test_no_system_calculation_fails_explicitly_and_discovery_is_empty():
    view = msv.MolSysView()
    assert view.interactions.analyses() == []
    with pytest.raises(InteractionAnalysisError, match="Load a molecular system"):
        view.interactions.hbonds.get_buch_hbonds(name="buch")


@pytest.mark.parametrize("mode", ["incident", "internal", "cross", "between"])
@pytest.mark.parametrize("skip_digestion", [False, True])
def test_legacy_query_names_are_rejected_on_all_public_routes(view, mode, skip_digestion):
    _attach(view)
    obj = view.interactions.add("contacts", tag="keep")
    before = view.export_state()
    for operation in (
        lambda: view.interactions.query("contacts", mode=mode, skip_digestion=skip_digestion),
        lambda: view.interactions.add("contacts", mode=mode, skip_digestion=skip_digestion),
        lambda: obj.set_filter(mode=mode, skip_digestion=skip_digestion),
    ):
        with pytest.raises(ValueError) as error:
            operation()
        if skip_digestion:
            assert "involving_selection" in str(error.value)
            assert "within_selection" in str(error.value)
            assert "across_selection_boundary" in str(error.value)
            assert "between_selections" in str(error.value)
        assert view.export_state() == before
