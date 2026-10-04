"""Named-file and inspector actions on real molecular axes and sparse results."""

import json

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw
from molsysviewer.interactions import _to_plain
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv


@pytest.fixture
def view():
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[8, 3, 0])
    records = [
        {
            "structure_index": frame,
            "interaction_type": "pi_pi",
            "participants": [
                {"role": "ring_a", "atom_indices": [0, 1, 2]},
                {"role": "ring_b", "atom_indices": [3, 4, 5]},
            ],
            "measurements": {"distance": distance},
            "evidence": "synthetic",
        }
        for frame, distance in [(0, 0.4), (0, 0.41), (2, 0.42)]
    ]
    result = msm.Interactions.from_records(
        records,
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 1, 2],
        method="public_completion",
        measure_units={"distance": "nm"},
    )
    view.interactions.attach(result, name="rings", assume_aligned=True)
    view.interactions.attach(result, name="other", assume_aligned=True)
    view.interactions.add("rings", tag="rings")
    return view


def identity(view, offset=0):
    page = view.interactions.inspect("rings", offset=offset, limit=1)
    return dict(
        structure_index=page["frame"],
        analysis_revision=page["analysis_revision"],
        query_revision=page["query_revision"],
    )


def test_named_h5msm_save_reload_preserves_sparse_parallel_and_empty_frames(view, tmp_path):
    path = tmp_path / "analyses.h5msm"
    assert view.interactions.save(path, analysis_names="rings") == str(path)
    layers = msm.h5msm.read_layers(path, layers="interactions")
    assert list(layers["interactions"]) == ["rings"]
    restored = msv.new_view(view.molsys)
    restored.interactions.delete_analysis("rings")
    restored.interactions.load(path, analysis_name="rings", assume_aligned=True)
    original = view.interactions.get_analysis("rings")
    saved = restored.interactions.get_analysis("rings")
    assert json.dumps(_to_plain(saved.to_dict()), sort_keys=True) == json.dumps(
        _to_plain(original.to_dict()), sort_keys=True
    )
    assert saved.query(structure_indices=[1]).n_interactions == 0
    assert saved.evaluated_structure_indices.tolist() == [0, 1, 2]
    view.interactions.save(path, overwrite=True)
    assert set(msm.h5msm.read_layers(path, layers="interactions")["interactions"]) == {"rings", "other"}


def test_save_refusals_preserve_destination_and_analysis_collection(view, tmp_path):
    path = tmp_path / "existing.h5msm"
    path.write_bytes(b"original")
    before = view.interactions.analyses()
    with pytest.raises(FileExistsError):
        view.interactions.save(path)
    with pytest.raises(KeyError):
        view.interactions.save(path, analysis_names=["rings", "missing"], overwrite=True)
    for names in ([], ["rings", "rings"], [True]):
        with pytest.raises(ArgumentError):
            view.interactions.save(path, analysis_names=names, overwrite=True)
    assert path.read_bytes() == b"original" and view.interactions.analyses() == before
    directory = tmp_path / "directory.h5msm"
    directory.mkdir()
    with pytest.raises(OSError):
        view.interactions.save(directory, overwrite=True)
    assert directory.is_dir() and not list(tmp_path.glob(".*.h5msm"))


def test_select_and_focus_compound_parallel_observations(view):
    key = identity(view, offset=1)
    atoms = view.interactions.select_observation("rings", 1, **key)
    assert atoms == [0, 1, 2, 3, 4, 5] and view.active_selection.atom_indices == atoms
    view.interactions.focus_observation("rings", 1, **key)
    page = view.interactions.inspect("rings", offset=1, limit=1)
    assert page["observations"][0]["occurrence_index"] == 1
    event = dict(
        action="select_interaction_observation",
        tag="rings",
        occurrence_index=1,
        frame=key["structure_index"],
        analysis_revision=key["analysis_revision"],
        query_revision=key["query_revision"],
    )
    view.active_selection.clear()
    dispatch_panel_action(view, event)
    assert view.active_selection.atom_indices == atoms


@pytest.mark.parametrize("change", ["filter", "frame", "analysis", "missing"])
def test_stale_observations_cannot_change_selection(view, change):
    key = identity(view)
    if change == "filter":
        view.interactions["rings"].set_filter(selection=[10])
    elif change == "frame":
        view.player.go_to_structure(2)
    elif change == "analysis":
        key["analysis_revision"] = "sha256:" + "0" * 64
    view.active_selection.set([8])
    with pytest.raises(ArgumentError):
        view.interactions.select_observation("rings", 999 if change == "missing" else 0, **key)
    assert view.active_selection.atom_indices == [8]


def test_pages_and_actions_on_nonconsecutive_visible_structure(view):
    view.player.go_to_structure(2)
    page = view.interactions.inspect("rings")
    assert page["frame"] == 2 and page["total"] == 1
    index = page["observations"][0]["occurrence_index"]
    assert view.interactions.select_observation("rings", index, **identity(view)) == [0, 1, 2, 3, 4, 5]


def test_periodic_images_and_units_round_trip_through_native_save(view, tmp_path):
    box = np.array([[2, 0, 0], [0.5, 2, 0], [0, 0, 2]], dtype=float)
    msm.set(view.molsys, box=puw.quantity(np.repeat(box[None], 3, axis=0), "nm"))
    result = msm.Interactions.from_records(
        [
            {
                "structure_index": 0,
                "interaction_type": "hbond",
                "participants": [
                    {"role": role, "atom_indices": [index]}
                    for index, role in enumerate(("donor", "hydrogen", "acceptor"))
                ],
                "images": [[1, 0, 0], [1, 1, 0], [2, 1, 0]],
                "measurements": {"distance": 0.2},
            }
        ],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 2],
        method="periodic_round_trip",
        measure_units={"distance": "nm"},
    )
    view.interactions.attach(result, name="periodic", assume_aligned=True)
    path = tmp_path / "periodic.h5msm"
    view.interactions.save(path, analysis_names=["periodic"])
    saved = msm.h5msm.read_layers(path, layers="interactions")["interactions"]["periodic"]
    assert saved.to_page()["image_vectors"].tolist() == [[1, 0, 0], [1, 1, 0], [2, 1, 0]]
    assert saved.to_page()["measure_units"] == {"distance": "nm"}
    assert saved.evaluated_structure_indices.tolist() == [0, 2]


def test_mutating_inspection_reply_cannot_change_action_participants(view):
    page = view.interactions.inspect("rings", limit=1)
    page["observations"][0]["participants"][0]["atom_indices"][:] = [8]
    key = dict(
        structure_index=page["frame"],
        analysis_revision=page["analysis_revision"],
        query_revision=page["query_revision"],
    )
    assert view.interactions.select_observation("rings", 0, **key) == [0, 1, 2, 3, 4, 5]
