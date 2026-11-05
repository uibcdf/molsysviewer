"""Numeric region selectors retain source provenance across changed atom axes."""

from copy import deepcopy

import numpy as np
import pytest
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def source():
    with msv.demo["dialanine"] as demo:
        with msv.new_view(demo.molsys, structure_indices=[0, 0, 0]) as view:
            yield view


def selector(kind, n_atoms):
    if kind == "list":
        return [2, 4]
    if kind == "tuple":
        return (2, 4)
    if kind == "array":
        return np.array([2, 4], dtype=np.int64)
    if kind == "mask":
        return np.isin(np.arange(n_atoms), [2, 4])
    return 2


@pytest.mark.parametrize("kind", ["list", "tuple", "array", "scalar"])
@pytest.mark.parametrize("mode", ["static", "dynamic"])
def test_numeric_query_is_transferred_without_replaying_source_indices(source, kind, mode):
    region = source.regions.add(selection=selector(kind, source.molsys.get_n_atoms()), tag="chosen")
    region.set_mode(mode)
    region.set_color(0x112233)
    original = deepcopy(dict(region.provenance))
    source_state = deepcopy(source.export_state())
    expected = (1,) if kind == "scalar" else (1, 2)
    with source.extract(selection=[1, 2, 4], structure_indices=[2, 0]) as result:
        transferred = result.regions["chosen"]
        assert transferred.atom_indices == expected
        assert transferred.mode == "static"
        assert transferred.provenance["kind"] == "transferred"
        assert transferred.provenance["broken"] is True
        assert transferred.provenance["frame_dependent"] is False
        np.testing.assert_equal(transferred.provenance["source_recipe"], original)
        assert result.molsys.structures.n_structures == 2
        colors = result.export_state()["regions"][0]["color_layer"]
        assert colors == {str(i): 0x112233 for i in expected}
    np.testing.assert_equal(source.export_state(), source_state)
    np.testing.assert_equal(dict(region.provenance), original)


@pytest.mark.parametrize("kind", ["list", "tuple", "array", "scalar"])
def test_identity_atom_extraction_preserves_numeric_recipe(source, kind):
    region = source.regions.add(selection=selector(kind, source.molsys.get_n_atoms()), tag="chosen")
    with source.extract(selection="all", structure_indices=[2, 0]) as result:
        assert result.regions["chosen"].atom_indices == region.atom_indices
        np.testing.assert_equal(dict(result.regions["chosen"].provenance), dict(region.provenance))


def test_numeric_transferred_recipe_survives_reconstruction_and_session(source, tmp_path):
    source.regions.add(selection=[2, 4], tag="chosen")
    with source.extract(selection=[1, 2, 4]) as result:
        state = result.export_state()
        with msv.new_view(result.molsys) as restored:
            restored.import_state(state)
            assert restored.regions["chosen"].atom_indices == (1, 2)
            assert restored.regions["chosen"].provenance == result.regions["chosen"].provenance
        path = tmp_path / "numeric-region.msv"
        result.save_session(path)
        with msv.load_session(path) as restored:
            assert restored.regions["chosen"].atom_indices == (1, 2)
            assert restored.regions["chosen"].provenance == result.regions["chosen"].provenance


def test_textual_index_recipe_keeps_existing_transfer_behavior(source):
    region = source.regions.add(selection="atom_index in [2, 4]", tag="chosen")
    with source.extract(selection=[1, 2, 4]) as result:
        assert result.regions["chosen"].atom_indices == (1, 2)
        assert result.regions["chosen"].provenance["source_recipe"] == region.provenance


def test_unadmitted_boolean_mask_is_still_rejected_before_region_creation(source):
    before = deepcopy(source.export_state())
    with pytest.raises(ArgumentError):
        source.regions.add(selection=selector("mask", source.molsys.get_n_atoms()), tag="chosen")
    np.testing.assert_equal(source.export_state(), before)
