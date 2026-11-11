"""The curated renderer parameter catalogue is a real public API contract."""

import warnings
from copy import deepcopy

import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.viewer.representations import _CURATED_PARAMETER_VALUES

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["dialanine"] as view:
        yield view


@pytest.mark.parametrize("surface", ["whole", "region"])
def test_curated_size_factor_is_digested_without_missing_parameter_warning(view, surface):
    owner = view.whole if surface == "whole" else view.regions.add(atom_indices=[0, 1, 2], tag="fragment")
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        owner.set_representation("ball-and-stick", sizeFactor=0.7)
    assert not [row for row in records if type(row.message).__name__ == "DigestNotDigestedWarning"]
    params = owner.params if surface == "whole" else owner.repr_params
    assert params["sizeFactor"] == 0.7


_EXAMPLES = {
    "sizeFactor": ("sticks", 0.7, 0.7),
    "sizeAspectRatio": ("backbone", 1.5, 1.5),
    "terminalLinkSizeFactor": ("carbohydrate", 0.3, 0.3),
    "probeRadius": ("surface", "0.14 nm", 1.4),
    "resolution": ("gaussian-surface", "0.05 nm", 0.5),
    "tubularHelices": ("cartoon", False, False),
    "helixProfile": ("cartoon", " ROUNDED ", "rounded"),
    "nucleicProfile": ("cartoon", "elliptical", "elliptical"),
    "ignoreHydrogens": ("ball-and-stick", True, True),
    "ignoreHydrogensVariant": ("point", "non-polar", "non-polar"),
    "multipleBonds": ("line", "symmetric", "symmetric"),
    "quality": ("spacefill", " HIGH ", "high"),
}


@pytest.mark.parametrize("surface", ["whole", "region"])
@pytest.mark.parametrize("name", sorted(_EXAMPLES))
def test_every_curated_specific_field_and_quality_has_a_working_public_contract(view, surface, name):
    representation, value, expected = _EXAMPLES[name]
    owner = view.whole if surface == "whole" else view.regions.add(atom_indices=[0, 1, 2], tag="fragment")
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        owner.set_representation(representation, **{name: value})
    assert not [row for row in records if type(row.message).__name__ == "DigestNotDigestedWarning"]
    params = owner.params if surface == "whole" else owner.repr_params
    assert params[name] == pytest.approx(expected) if isinstance(expected, float) else params[name] == expected
    assert set(_EXAMPLES) == set(_CURATED_PARAMETER_VALUES)


@pytest.mark.parametrize("surface", ["whole", "region"])
@pytest.mark.parametrize(
    "name,value",
    [
        ("sizeFactor", -1),
        ("sizeFactor", True),
        ("sizeFactor", float("nan")),
        ("sizeFactor", float("inf")),
        ("sizeFactor", [0.7]),
        ("sizeFactor", "large"),
        ("sizeAspectRatio", 0),
        ("terminalLinkSizeFactor", -1),
        ("resolution", 0),
        ("resolution", -1),
        ("resolution", None),
        ("resolution", "1 ps"),
        ("resolution", "[1,2] nm"),
        ("probeRadius", "-1 angstrom"),
        ("probeRadius", "nan angstrom"),
        ("ignoreHydrogens", 1),
        ("ignoreHydrogens", "false"),
        ("tubularHelices", None),
        ("multipleBonds", "unknown"),
        ("helixProfile", "flat"),
        ("nucleicProfile", True),
        ("ignoreHydrogensVariant", "polar"),
        ("quality", "ultra"),
    ],
)
def test_invalid_curated_values_preserve_scene_history_and_molecular_data(view, surface, name, value):
    owner = view.whole if surface == "whole" else view.regions.add(atom_indices=[0, 1, 2], tag="fragment")
    owner.set_representation("ball-and-stick", sizeFactor=0.5)
    view.history.clear()
    before = view.export_state()
    coordinates = puw.get_value(view.molsys.structures.coordinates, to_unit="angstrom").copy()
    with pytest.raises(ValueError):
        owner.set_representation("ball-and-stick", **{name: value})
    assert view.export_state() == before
    assert not view.history.can_undo() and not view.history.can_redo()
    np.testing.assert_array_equal(puw.get_value(view.molsys.structures.coordinates, to_unit="angstrom"), coordinates)


@pytest.mark.parametrize("surface", ["whole", "region", "style"])
def test_normalized_values_and_core_checks_survive_delegation_and_skip_digest(view, surface):
    if surface == "whole":
        apply = view.whole.set_representation
    elif surface == "region":
        apply = view.regions.add(atom_indices=[0, 1, 2], tag="fragment").set_representation
    else:
        apply = view.styles.apply
    before = view.export_state()
    with pytest.raises(ValueError):
        apply(representation="ball-and-stick", sizeFactor=float("nan"), skip_digestion=True)
    assert view.export_state() == before
    apply(representation="ball-and-stick", sizeFactor=np.float32(0.5), ignoreHydrogens=np.bool_(True))
    params = view.regions["fragment"].repr_params if surface == "region" else view.whole.params
    assert params["sizeFactor"] == 0.5 and params["ignoreHydrogens"] is True


@pytest.mark.parametrize("policy", ["nm", "angstrom", "pm"])
@pytest.mark.parametrize("surface", ["whole", "region", "style"])
def test_renderer_lengths_convert_once_to_fixed_angstrom_coordinates(view, policy, surface):
    source = puw.quantity(0.14, "nm")
    with puw.context(standard_units=[policy, "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        if surface == "whole":
            view.whole.set_representation("surface", probeRadius=source, resolution="50 pm")
            params = view.whole.params
        elif surface == "region":
            region = view.regions.add(
                atom_indices=[0, 1, 2], tag="fragment", representation="surface", probeRadius=source, resolution="50 pm"
            )
            params = region.repr_params
        else:
            view.styles.apply(representation="surface", probeRadius=source, resolution="50 pm")
            params = view.whole.params
        assert params["probeRadius"] == pytest.approx(1.4)
        assert params["resolution"] == pytest.approx(0.5)
        assert puw.get_value(source, to_unit="nm") == 0.14
    schema = view.styles.representation_param_schema("surface")
    fields = {row["name"]: row for row in schema["specific_params"]}
    assert fields["probeRadius"]["unit"] == fields["resolution"]["unit"] == "angstrom"


def test_parameter_schema_nested_values_are_detached_from_validation(view):
    first = view.styles.representation_param_schema("sticks")
    second = deepcopy(first)
    for row in first["common_params"] + first["specific_params"]:
        if "values" in row:
            row["values"].append("invented")
    assert view.styles.representation_param_schema("sticks") == second
    with pytest.raises(ValueError):
        view.whole.set_representation("sticks", quality="invented")


def test_unknown_advanced_option_keeps_its_existing_warning_and_forwarding(view):
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        view.whole.set_representation("cartoon", radialSegments=20, sizeFactor=0.7)
    missing = [row for row in records if type(row.message).__name__ == "DigestNotDigestedWarning"]
    assert len(missing) == 1 and "radialSegments" in str(missing[0].message)
    assert view.whole.params["radialSegments"] == 20 and view.whole.params["sizeFactor"] == 0.7


def test_zero_scales_and_probe_radius_are_valid_but_not_a_zero_grid_step(view):
    view.whole.set_representation("cartoon", sizeFactor=0)
    assert view.whole.params["sizeFactor"] == 0
    view.whole.set_representation("surface", probeRadius=0, resolution=0.5)
    assert view.whole.params == {"probeRadius": 0, "resolution": 0.5}


def test_curated_values_survive_session_and_undo_redo(view, tmp_path):
    view.whole.set_representation("surface", probeRadius="0.14 nm", resolution="0.05 nm")
    region = view.regions.add(
        atom_indices=[0, 1, 2], tag="fragment", representation="sticks", sizeFactor=0.7, ignoreHydrogens=True
    )
    view.history.clear()
    region.set_representation("sticks", sizeFactor=0.9, ignoreHydrogens=False)
    assert view.history.undo() and view.regions["fragment"].repr_params["sizeFactor"] == 0.7
    assert view.history.redo() and view.regions["fragment"].repr_params["sizeFactor"] == 0.9
    view.save_session(tmp_path / "representation-parameters.msv")
    with msv.load_session(tmp_path / "representation-parameters.msv") as restored:
        assert restored.whole.params == view.whole.params
        assert restored.regions["fragment"].repr_params == view.regions["fragment"].repr_params


def test_unrelated_pocket_resolution_contract_remains_unchanged():
    from molsysviewer._private.argdigest.argument.resolution import digest_resolution

    assert digest_resolution(None, caller="molsysviewer.shapes.pocket_blobs.add_pocket_blob") is None
    assert digest_resolution(0.5, caller="molsysviewer.shapes.pocket_blobs.add_pocket_blob") == 0.5


@pytest.mark.parametrize("value", [[0.5], [0.5, 0.7], None])
@pytest.mark.parametrize("surface", ["whole", "region", "style"])
def test_molecular_opacity_is_scalar_even_on_delegated_paths(view, value, surface):
    if surface == "whole":
        apply = view.whole.set_representation
    elif surface == "region":
        apply = view.regions.add(atom_indices=[0, 1, 2], tag="fragment").set_representation
    else:
        apply = view.styles.apply
    before = view.export_state()
    with pytest.raises(ValueError, match="alpha"):
        apply(representation="sticks", alpha=value)
    assert view.export_state() == before


def test_shape_opacity_batches_still_use_their_original_contract(view):
    layers = view.shapes.add_sphere(
        center=puw.quantity([[0, 0, 0], [1, 0, 0]], "nm"),
        radius="0.1 nm",
        alpha=[0.5, 0.7],
        tag=["one", "two"],
    )
    assert len(layers) == 2
