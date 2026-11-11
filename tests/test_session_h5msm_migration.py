"""Receive H5MSM schema migration through real public MolSysViewer sessions.

The molecular trajectory is real. The named observations deliberately use
synthetic geometry to make parallel records, maps and coverage unambiguous.
No detector accuracy or browser-rendering claim follows from this fixture.
"""

import zipfile
from copy import deepcopy

import h5py
import molsysmt as msm
import numpy as np
import pytest
from molsysmt._private.smonitor import ArgumentChoiceError
from molsysviewer._pyunitwizard import puw
from molsysviewer.interactions import _analysis_signature
from pandas.testing import assert_frame_equal

import molsysviewer as msv


def _schema(path):
    with h5py.File(path, "r") as file:
        return file.attrs["version"]


def _xyz(system):
    return puw.get_value(system.structures.coordinates, to_unit="nm")


def _analysis(n_atoms, *, empty=False):
    participants = [
        {"role": "donor", "atom_indices": [0]},
        {"role": "hydrogen", "atom_indices": [1]},
        {"role": "acceptor", "atom_indices": [2]},
    ]
    records = (
        []
        if empty
        else [
            {
                "structure_index": frame,
                "interaction_type": "hbond",
                "participants": participants,
                "measurements": {"distance": distance},
                "evidence": evidence,
                "images": images,
            }
            for frame, distance, evidence, images in [
                (0, 0.20, "synthetic-first", [[0, 0, 0]] * 3),
                (2, 0.23, "synthetic-middle", [[0, 0, 0]] * 3),
                (4, 0.21, "synthetic-periodic", [[0, 0, 0], [0, 0, 0], [1, 0, 0]]),
                (4, 0.22, "synthetic-parallel", [[0, 0, 0]] * 3),
            ]
        ]
    )
    if not empty:
        records.insert(
            1,
            {
                "structure_index": 0,
                "interaction_type": "pi_pi",
                "participants": [
                    {"role": "ring", "atom_indices": [3, 4, 5]},
                    {"role": "ring", "atom_indices": [6, 7, 8]},
                ],
                "measurements": {"distance": 0.36},
                "evidence": "synthetic-compound",
                "images": [[0, 0, 0], [0, 1, 0]],
            },
        )
    return msm.Interactions.from_records(
        records,
        n_atoms=n_atoms,
        n_structures=6,
        evaluated_structure_indices=[1, 5] if empty else [0, 1, 2, 4],
        method="molsysviewer_synthetic_migration_guard",
        parameters={"synthetic": True, "criterion": "persistence-only"},
        measure_units={"distance": "nm"},
        source_id="declared-correspondence-only",
        atom_source_indices=list(range(n_atoms + 6, 6, -1)),
        structure_source_indices=[4999, 0, 73, 12, 4, 1],
        source_n_atoms=n_atoms + 7,
        source_n_structures=5000,
    )


@pytest.fixture
def scientific_session(tmp_path):
    trajectory = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    with msv.new_view(trajectory, structure_indices=[4999, 0, 73, 12, 4, 1]) as view:
        n_atoms = _xyz(view.molsys).shape[1]
        for name, empty in [("parallel", False), ("empty-control", True)]:
            view.interactions.attach(_analysis(n_atoms, empty=empty), name=name, assume_aligned=True)
            view.interactions.add(name, tag=name)
        view.regions.add(selection=[0, 2, 4], tag="retained-atoms")
        view.annotations.add("Migration control", atom_indices=[0, 2], tag="note")
        view.shapes.add("sphere", center="[1, 2, 3] nm", radius="0.1 nm", tag="sphere")
        view.camera.set_snapshot({"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]})
        view.player.go_to_structure(4)
        path = tmp_path / "existing-05.msv"
        view.save_session(path)
        with zipfile.ZipFile(path) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        molecular = tmp_path / "original-05.h5msm"
        molecular.write_bytes(members["structure.h5msm"])
        assert _schema(molecular) == "0.5"
        yield view, path, molecular, members


def _migrated_session(tmp_path, original, version):
    _, source, molecular, members = original
    if version == "0.5":
        return source
    target = tmp_path / "migrated-10.h5msm"
    original_bytes = molecular.read_bytes()
    # Older supported MolSysMT releases do not implement explicit H5MSM 1.0.
    # Exercise the public capability and retain an explicit skip on that route.
    _write_layers(tmp_path / "capability.h5msm", "1.0", interactions={})
    msm.convert(molecular, to_form=target, format_version="1.0")
    assert molecular.read_bytes() == original_bytes
    assert _schema(target) == "1.0"
    path = tmp_path / "equivalent-10.msv"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, target.read_bytes() if name == "structure.h5msm" else data)
    with zipfile.ZipFile(path) as archive:
        for name, data in members.items():
            if name != "structure.h5msm":
                assert archive.read(name) == data
    return path


def _write_layers(path, version, **layers):
    try:
        msm.h5msm.write_layers(path, format_version=version, **layers)
    except ArgumentChoiceError as error:
        extra = getattr(error, "extra", {})
        if version == "1.0" and extra.get("argument") == "format_version" and "1.0" not in extra.get("choices", []):
            pytest.skip(f"Provider explicitly lacks H5MSM 1.0: {error}")
        raise
    except (ValueError, TypeError) as error:
        message = str(error)
        if (
            version == "1.0"
            and "format_version" in message
            and (
                "'0.5' or '0.6'" in message
                or "['0.5', '0.6']" in message
                or "unexpected keyword argument 'format_version'" in message
            )
        ):
            pytest.skip(f"Provider explicitly lacks H5MSM 1.0: {error}")
        raise


def _assert_system(expected, observed):
    np.testing.assert_array_equal(_xyz(observed), _xyz(expected))
    np.testing.assert_array_equal(
        puw.get_value(observed.structures.box, to_unit="nm"),
        puw.get_value(expected.structures.box, to_unit="nm"),
    )
    assert_frame_equal(
        expected.chemical_states.get_bonds(chemical_state="reference"),
        observed.chemical_states.get_bonds(chemical_state="reference"),
    )
    np.testing.assert_array_equal(
        msm.get(expected, element="atom", component_index=True),
        msm.get(observed, element="atom", component_index=True),
    )
    assert set(observed.interactions) == set(expected.interactions)
    for name, analysis in expected.interactions.items():
        restored = observed.interactions[name]
        assert _analysis_signature(restored) == _analysis_signature(analysis)
        np.testing.assert_array_equal(
            restored.to_dict()["occurrence_indices"], analysis.to_dict()["occurrence_indices"]
        )


def _assert_queries(view):
    analysis = view.interactions.get_analysis("parallel")
    selected = analysis.query(structure_indices=[4, 1, 0, 4, 3]).to_dict()
    np.testing.assert_array_equal(selected["structure_indices"], [4, 4, 0, 0])
    np.testing.assert_array_equal(selected["occurrence_indices"], [3, 4, 0, 1])
    np.testing.assert_array_equal(selected["evaluated_structure_indices"], [4, 1, 0])
    # Native construction canonically sorts parallel evidence; input record
    # order is not an identity promise. Check the actual declared identities.
    np.testing.assert_array_equal(selected["measurements"]["distance"], [0.22, 0.21, 0.20, 0.36])
    assert list(selected["evidence"][:2]) == ["synthetic-parallel", "synthetic-periodic"]
    np.testing.assert_array_equal(analysis.atom_source_indices, list(range(68, 6, -1)))
    np.testing.assert_array_equal(analysis.structure_source_indices, [4999, 0, 73, 12, 4, 1])
    assert analysis.query([0], [0], mode="involving_selection").n_interactions == 1
    assert analysis.query([0], [0, 1, 2], mode="within_selection").n_interactions == 1
    assert analysis.query([0], [0], mode="across_selection_boundary").n_interactions == 1
    assert analysis.between_selections([3, 4, 5], [6, 7, 8], exclusive=True).n_interactions == 1
    assert view.interactions.inspect("parallel", structure_index=1)["status"] == "evaluated"
    assert view.interactions.inspect("parallel", structure_index=3)["status"] == "unevaluated"
    for frame in [1, 3]:
        assert analysis.query([frame]).n_interactions == 0
    # The maps compose when the View itself is extracted in a different order.
    with view.extract(selection=[0, 1, 2], structure_indices=[4, 1, 0]) as subset:
        result = subset.interactions.get_analysis("parallel")
        np.testing.assert_array_equal(result.atom_source_indices, [68, 67, 66])
        np.testing.assert_array_equal(result.structure_source_indices, [4, 0, 4999])
        np.testing.assert_array_equal(result.evaluated_structure_indices, [0, 1, 2])
        assert result.n_interactions == 3


@pytest.mark.parametrize("version", ["0.5", "1.0"])
def test_session_schema_preserves_scene_science_and_queries(tmp_path, scientific_session, version):
    source = scientific_session[0]
    path = _migrated_session(tmp_path, scientific_session, version)
    with msv.load_session(path) as restored:
        _assert_system(source.molsys, restored.molsys)
        assert restored.export_state() == source.export_state()
        assert restored.camera.get_snapshot() == source.camera.get_snapshot()
        assert restored.player.index == 4
        _assert_queries(restored)
        # Persistence through the public writer still follows its default 0.5.
        output = tmp_path / "saved-again.msv"
        restored.save_session(output)
        with zipfile.ZipFile(output) as archive:
            embedded = tmp_path / "saved-again.h5msm"
            embedded.write_bytes(archive.read("structure.h5msm"))
        assert _schema(embedded) == "0.5"
        with msv.load_session(output) as again:
            _assert_system(restored.molsys, again.molsys)
            assert again.export_state() == restored.export_state()


@pytest.mark.parametrize("version", ["0.5", "1.0"])
@pytest.mark.parametrize("frames", [[4], [4, 0]])
def test_recovered_setter_invalidates_only_changed_frames(tmp_path, scientific_session, version, frames):
    source = scientific_session[0]
    path = _migrated_session(tmp_path, scientific_session, version)
    with msv.load_session(path) as restored:
        detached = restored.interactions.get_analysis("parallel")
        before = deepcopy(detached.to_dict())
        before_empty = _analysis_signature(restored.interactions.get_analysis("empty-control"))
        untouched = {f: deepcopy(restored.interactions.inspect("parallel", structure_index=f)) for f in [1, 2]}
        coordinates = _xyz(restored.molsys).copy()
        edited = coordinates[frames][:, [0]].copy() + [0.01, 0, 0]
        msm.set(restored.molsys, selection=[0], structure_indices=frames, coordinates=puw.quantity(edited, "nm"))
        expected = coordinates.copy()
        expected[np.ix_(frames, [0], [0, 1, 2])] = edited
        np.testing.assert_array_equal(_xyz(restored.molsys), expected)
        current = restored.interactions.get_analysis("parallel")
        assert current is not detached
        np.testing.assert_array_equal(current.evaluated_structure_indices, [f for f in [0, 1, 2, 4] if f not in frames])
        np.testing.assert_array_equal(detached.to_dict()["occurrence_indices"], before["occurrence_indices"])
        np.testing.assert_array_equal(detached.evaluated_structure_indices, [0, 1, 2, 4])
        assert _analysis_signature(restored.interactions.get_analysis("empty-control")) == before_empty
        for frame in frames:
            page = restored.interactions.inspect("parallel", structure_index=frame)
            assert page["status"] == "unevaluated"
            assert page["total"] == 0 and page["observations"] == []
        for frame in [1, 2]:
            page = restored.interactions.inspect("parallel", structure_index=frame)
            assert page["status"] == "evaluated"
            assert page["total"] == untouched[frame]["total"]
        # Original and persisted sessions remain independent of the edit.
        np.testing.assert_array_equal(_xyz(source.molsys), coordinates)
        with msv.load_session(path) as original:
            _assert_system(source.molsys, original.molsys)
        # Native edits invalidate the science. The explicit host operation
        # synchronizes molecular binding and projection before another save.
        # Preserve only the already selectively invalidated provider results.
        restored.apply_system_edit(restored.molsys, interactions_policy="preserve")
        output = tmp_path / "edited.msv"
        restored.save_session(output)
        with msv.load_session(output) as again:
            _assert_system(restored.molsys, again.molsys)
            for frame in frames:
                assert again.interactions.inspect("parallel", structure_index=frame)["status"] == "unevaluated"


@pytest.mark.parametrize("version", ["0.5", "1.0"])
def test_independent_interactions_attach_without_replacing_system(tmp_path, scientific_session, version):
    source = scientific_session[0]
    path = tmp_path / "interactions-only.h5msm"
    analyses = dict(source.molsys.interactions)
    _write_layers(path, version, interactions=analyses)
    assert _schema(path) == version
    with msv.new_view(source.molsys) as target:
        original_system = target.molsys
        original_coordinates = _xyz(target.molsys).copy()
        for name, result in analyses.items():
            imported = target.interactions.load(path, analysis_name=name, name=f"imported-{name}", assume_aligned=True)
            assert _analysis_signature(imported) == _analysis_signature(result)
        assert target.molsys is original_system
        np.testing.assert_array_equal(_xyz(target.molsys), original_coordinates)


def test_mechanics_10_session_reads_and_default_save_refuses_loss(tmp_path, scientific_session):
    source, _, _, members = scientific_session
    molecular = tmp_path / "mechanics-10.h5msm"
    mechanics = source.molsys.molecular_mechanics
    mechanics.forcefield = "synthetic-unresolved-persistence-request"
    mechanics.partial_charge = np.linspace(-0.25, 0.25, 62)
    mechanics.cutoff_distance = puw.quantity(12.0, "angstrom")
    _write_layers(tmp_path / "capability.h5msm", "1.0", interactions={})
    msm.h5msm.write(source.molsys, molecular, format_version="1.0")
    path = tmp_path / "mechanics-10.msv"
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, molecular.read_bytes() if name == "structure.h5msm" else data)
    with msv.load_session(path) as restored:
        _assert_system(source.molsys, restored.molsys)
        observed = restored.molsys.molecular_mechanics
        assert observed.forcefield == mechanics.forcefield
        np.testing.assert_array_equal(observed.partial_charge, mechanics.partial_charge)
        assert str(puw.get_unit(observed.cutoff_distance)) == "angstrom"
        assert puw.get_value(observed.cutoff_distance, to_unit="nm") == pytest.approx(1.2)
        output = tmp_path / "keep-existing.msv"
        sentinel = b"existing destination must survive unsupported default schema"
        output.write_bytes(sentinel)
        with pytest.raises(ValueError, match="molecular mechanics"):
            restored.save_session(output)
        assert output.read_bytes() == sentinel
