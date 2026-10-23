"""Live adoption preserves all declared structure destinations and scene owners."""

from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with msv.new_view(source.molsys, structure_indices=[0, 8, 3], debug_js=True) as result:
            analysis = msm.Interactions.from_records(
                [
                    {
                        "structure_index": index,
                        "interaction_type": "hbond",
                        "participants": [
                            {"role": role, "atom_indices": [atom]}
                            for atom, role in enumerate(("donor", "hydrogen", "acceptor"))
                        ],
                    }
                    for index in range(3)
                ],
                n_atoms=result.molsys.get_n_atoms(),
                n_structures=3,
                evaluated_structure_indices=[0, 1, 2],
                method="structure_correspondence_fixture",
            )
            result.interactions.attach(analysis, name="contacts", assume_aligned=True)
            result.interactions.add("contacts", structure_indices=[2], tag="hb")
            result.shapes.add_sphere(radius="0.1 nm", structures_atom_indices=[[0], [1], [2]], tag="anchors")
            result.shapes.add_sphere(
                structure_centers=puw.quantity([[1, 0, 0], [2, 0, 0], [3, 0, 0]], "nm"),
                tag="points",
            )
            result.trajectory_plot.show(
                {"score": [10, 20, 30]},
                x=[1, 2, 3],
                events=[{"frame": 2, "label": "event"}],
                tag="data",
            )
            yield result


def _shape(view, tag):
    return next(record["options"] for record in view._shape_history if record["options"]["tag"] == tag)


def _pairs(record):
    return [
        (source + offset, current + offset)
        for source, current, count in record["structure_map"]["runs"]
        for offset in range(count)
    ]


@pytest.mark.parametrize("frames", [[2, 0, 2], [2, 0], [1]])
@pytest.mark.parametrize("current", [0, 2])
def test_live_adoption_remaps_shapes_filters_plots_player_and_source_maps(view, frames, current, tmp_path):
    view.player.go_to_structure(current)
    old = view.molsys
    source = view.load_blocks[0]
    original = puw.get_value(old.structures.coordinates, to_unit="nm")
    objects = (view.shapes["anchors"], view.interactions["hb"])
    edited = msm.extract(old, structure_indices=frames, to_form="molsysmt.MolSys")

    view.apply_system_edit(edited, structure_index_map=frames, interactions_policy="preserve")

    assert view.molsys is edited and view.molsys is not old
    np.testing.assert_array_equal(puw.get_value(edited.structures.coordinates, to_unit="nm"), original[frames])
    assert objects == (view.shapes["anchors"], view.interactions["hb"])
    assert view.player.index == next((new for new, old in enumerate(frames) if old == current), 0)
    assert _shape(view, "anchors")["structures_atom_indices"] == [[index] for index in frames]
    assert _shape(view, "points")["structures_coords"] == [[10 * (index + 1), 0, 0] for index in frames]
    assert view.interactions["hb"].filter["structure_indices"] == [new for new, old in enumerate(frames) if old == 2]
    np.testing.assert_array_equal(edited.interactions["contacts"].evaluated_structure_indices, range(len(frames)))
    card = view.trajectory_plot.records()[0]
    assert card["series"][0]["values"] == [10 * (index + 1) for index in frames]
    assert card["x"] == [index + 1 for index in frames]
    assert card["events"] == [{"frame": new, "label": "event"} for new, old in enumerate(frames) if old == 2]
    assert card["n_frames"] == len(frames)
    assert view.load_blocks[0]["source_id"] == source["source_id"]
    initial = dict((current, source) for source, current in _pairs(source))
    assert _pairs(view.load_blocks[0]) == [(initial[old], new) for new, old in enumerate(frames)]
    assert not view.history.can_undo()
    for index in range(len(frames)):
        payload = view.interactions._frame(view.interactions["hb"], index)
        assert payload["status"] == ("evaluated" if frames[index] == 2 else "excluded")

    path = tmp_path / "mapped.msv"
    view.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.export_state() == view.export_state()
        np.testing.assert_array_equal(
            puw.get_value(restored.molsys.structures.coordinates, to_unit="nm"), original[frames]
        )


@pytest.mark.parametrize("mapping", [[0, 1], [0, 1, 3], [True, 1, 2], [0.0, 1, 2], [[0], [1], [2]], "all"])
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_structure_correspondence_is_rejected_before_adoption(view, mapping, skip):
    original = view.molsys
    candidate = msm.copy(original)
    state = deepcopy(view.export_state())
    history = list(view.history._undo)
    analyses = dict(candidate.interactions)
    with pytest.raises(ValueError, match="structure_index_map"):
        view.apply_system_edit(candidate, structure_index_map=mapping, skip_digestion=skip)
    assert view.molsys is original
    assert view.export_state() == state
    assert view.history._undo == history
    assert all(candidate.interactions[name] is analysis for name, analysis in analyses.items())


def test_default_invalidation_and_unchanged_axis_compatibility(view):
    edited = msm.extract(view.molsys, structure_indices=[2, 0], to_form="molsysmt.MolSys")
    view.apply_system_edit(edited, structure_index_map=np.array([2, 0], dtype=np.int64))
    assert len(edited.interactions["contacts"].evaluated_structure_indices) == 0
    assert view.trajectory_plot.records()[0]["series"][0]["values"] == [30, 10]


def test_shared_extraction_policy_keeps_every_repeated_destination(view):
    view.player.go_to_structure(2)
    original_state = view.export_state()
    with view.extract(structure_indices=[2, 0, 2]) as result:
        assert result.player.index == 0
        assert result.interactions["hb"].filter["structure_indices"] == [0, 2]
        assert _shape(result, "anchors")["structures_atom_indices"] == [[2], [0], [2]]
        assert result.trajectory_plot.records()[0]["series"][0]["values"] == [30, 10, 30]
    assert view.export_state() == original_state


def test_same_object_structure_replacement_uses_the_previously_projected_axis(view):
    target = view.molsys
    source = view.load_blocks[0]
    original = puw.get_value(target.structures.coordinates, to_unit="nm").copy()
    view.player.go_to_structure(2)
    edited = msm.remove(target, structure_indices=[1], to_form="molsysmt.MolSys")
    # Announce a public domain replacement on the actual bound object, without
    # requiring newer provider in-place removal semantics at the backend floor.
    target.structures = edited.structures
    target.interactions = edited.interactions
    view.apply_system_edit(target, structure_index_map=[0, 2], interactions_policy="preserve")
    assert view.molsys is target and view.player.index == 1
    np.testing.assert_array_equal(puw.get_value(target.structures.coordinates, to_unit="nm"), original[[0, 2]])
    assert view.trajectory_plot.records()[0]["series"][0]["values"] == [10, 30]
    assert view.interactions["hb"].filter["structure_indices"] == [1]
    assert view.load_blocks[0]["source_id"] == source["source_id"]


def test_atom_and_structure_maps_remap_compound_scene_state_together(view):
    region = view.regions.add(atom_indices=[0, 1, 2], tag="fragment")
    frames = [2, 0]
    atoms = list(range(1, view.molsys.get_n_atoms()))
    edited = msm.extract(view.molsys, selection=atoms, structure_indices=frames, to_form="molsysmt.MolSys")
    view.apply_system_edit(
        edited,
        atom_index_map={old: new for new, old in enumerate(atoms)},
        structure_index_map=frames,
        interactions_policy="preserve",
    )
    assert view.regions["fragment"] is region and region.atom_indices == (0, 1)
    assert _shape(view, "anchors")["structures_atom_indices"] == [[1], None]
    assert view.interactions["hb"].filter["structure_indices"] == [0]
    assert view.trajectory_plot.records()[0]["series"][0]["values"] == [30, 10]
