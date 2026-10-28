"""Native prefix additions preserve scene identities and reject unknown series."""

import copy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.system_edits import SystemEditSyncError

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["dialanine"] as source:
        with msv.new_view(source.molsys) as result:
            yield result


def growth(view, axis, *, update=True, added=None):
    source = msm.copy(view.molsys)
    count = source.get_n_atoms() if axis == "atoms" else source.structures.n_structures
    native = msm.add if axis == "atoms" else msm.append_structures
    return view.addons.manager.system_edits.execute(
        lambda target: {
            "run": lambda: native(target, source),
            "changed": True,
            "added_count": count if added is None else added,
            "interactions_policy": "preserve",
        },
        name="receiving.prefix",
        axis_growth=axis,
        update_view=update,
    )


@pytest.mark.parametrize("update", [False, True])
@pytest.mark.parametrize("axis", ["atoms", "structures"])
def test_native_growth_preserves_target_handles_and_known_source_prefix(view, axis, update, tmp_path):
    manager = view.addons.manager.system_edits
    target = view.molsys
    n_atoms = target.get_n_atoms()
    source_id = view.load_blocks[0]["source_id"]
    region = view.regions.add(atom_indices=[0, 1], tag="retained")
    view.shapes.add_sphere(atom_indices=[0], radius="0.1 nm", tag="anchor")
    shape = view.shapes["anchor"]
    assert growth(view, axis, update=update) is None
    assert view.molsys is target
    assert target.get_n_atoms() == (2 * n_atoms if axis == "atoms" else n_atoms)
    assert target.structures.n_structures == (2 if axis == "structures" else 1)
    assert manager.get_status()["state"] == ("synchronized" if update else "pending")
    manager.synchronize()
    assert view.regions["retained"] is region and region.atom_indices == (0, 1)
    assert view.shapes["anchor"] is shape
    assert view.player.n_structures == (2 if axis == "structures" else 1)
    assert view.load_blocks[0]["source_id"] == source_id
    assert view.load_blocks[0]["structure_map"]["runs"] == [[0, 0, 1]]
    if axis == "atoms":
        assert len(view.load_blocks) == 2
        assert view.load_blocks[1]["origin"]["kind"] == "unmapped_edit"
    filename = tmp_path / "grown.msv"
    view.save_session(filename)
    with msv.load_session(filename) as restored:
        assert restored.export_state() == view.export_state()


@pytest.mark.parametrize("owner", ["shape", "plot"])
def test_new_structure_origins_reject_unknown_visual_series_before_science(view, owner):
    if owner == "shape":
        view.shapes.add_sphere(
            structure_centers=msm.pyunitwizard.quantity([[0, 0, 0]], "nm"), radius="0.1 nm", tag="per-structure"
        )
    else:
        view.trajectory_plot.show({"score": [1]}, tag="per-structure")
    before = copy.deepcopy(view.export_state())
    coordinates = view.molsys.structures.coordinates.copy()
    with pytest.raises(ValueError, match="Clear"):
        growth(view, "structures")
    assert view.molsys.structures.n_structures == 1
    np.testing.assert_array_equal(
        msm.pyunitwizard.get_value(view.molsys.structures.coordinates), msm.pyunitwizard.get_value(coordinates)
    )
    assert view.export_state() == before
    assert view.addons.manager.system_edits.get_status()["state"] == "synchronized"


def test_deferred_growth_composes_with_retained_structure_maps(view):
    manager = view.addons.manager.system_edits
    growth(view, "structures", update=False)
    growth(view, "structures", update=False)
    assert view.molsys.structures.n_structures == 4

    def remove_new_structure(target):
        edited = msm.extract(target, structure_indices=[0, 2, 3])
        # Public domain replacement also works at the MolSysMT 0.23.0 floor,
        # whose remove() does not yet implement in-place removal.
        target.structures = edited.structures
        target.interactions = edited.interactions

    manager.execute(
        lambda target: {
            "run": lambda: remove_new_structure(target),
            "changed": True,
            "structure_index_map": [0, 2, 3],
            "interactions_policy": "preserve",
        },
        name="receiving.remove-new",
        update_view=False,
    )
    # Three current structures now map to [old 0, new, new]. Repetition
    # remains available through the public adoption boundary after sync.
    manager.synchronize()
    assert view.player.n_structures == 3
    assert view.load_blocks[0]["structure_map"]["runs"] == [[0, 0, 1]]
    edited = msm.extract(view.molsys, structure_indices=[2, 0, 1, 0])
    view.apply_system_edit(edited, structure_index_map=[2, 0, 1, 0], interactions_policy="preserve")
    assert view.load_blocks[0]["structure_map"]["runs"] == [[0, 1, 1], [0, 3, 1]]


def test_incorrect_declared_growth_quarantines_completed_science(view):
    with pytest.raises(SystemEditSyncError):
        growth(view, "structures", added=2)
    assert view.molsys.structures.n_structures == 2
    assert view.addons.manager.system_edits.get_status()["state"] == "uncertain"
