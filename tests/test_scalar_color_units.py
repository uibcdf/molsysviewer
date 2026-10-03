"""Physical scalar colors must survive unit changes, ranges and scene replay."""

import numpy as np
import pytest
import pyunitwizard as puw
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.colors import scalar_to_color_list
from molsysviewer.demo import demo

ANGSTROM_POLICY = ["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]
PALETTE = [0x000000, 0xFFFFFF]


@pytest.mark.parametrize("policy", [None, ANGSTROM_POLICY])
@pytest.mark.parametrize("range_form", ["array", "bounds", "string"])
def test_equivalent_physical_units_give_identical_colors(policy, range_form):
    with puw.context(standard_units=policy or ["nm", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        bounds = puw.quantity([0, 100], "angstrom**2")
        if range_form == "bounds":
            bounds = [puw.quantity(0, "nm**2"), puw.quantity(100, "angstrom**2")]
        elif range_form == "string":
            bounds = "[0,100] angstrom**2"
        expected = scalar_to_color_list([0, 0.5, 1], palette=PALETTE, value_range=[0, 1])
        assert scalar_to_color_list(puw.quantity([0, 0.5, 1], "nm**2"), palette=PALETTE, value_range=bounds) == expected
        assert (
            scalar_to_color_list(
                puw.quantity([0, 50, 100], "angstrom**2"),
                palette=PALETTE,
                value_range=puw.quantity([0, 1], "nm**2"),
            )
            == expected
        )


def test_inferred_physical_range_and_dimensionless_quantities_are_supported():
    expected = scalar_to_color_list([0, 0.5, 1], palette=PALETTE)
    assert scalar_to_color_list(puw.quantity([0, 50, 100], "angstrom**2"), palette=PALETTE) == expected
    assert scalar_to_color_list(puw.quantity([0, 50, 100], "percent"), palette=PALETTE, value_range=[0, 1]) == expected
    assert scalar_to_color_list([0, 0.5, 1], palette=PALETTE, value_range=puw.quantity([0, 100], "percent")) == expected


@pytest.mark.parametrize("case", ["bare_range", "wrong_dimension", "bare_values", "mixed_bounds", "nan", "reversed"])
def test_ambiguous_or_invalid_physical_ranges_are_rejected(case):
    values = puw.quantity([0, 0.5, 1], "nm**2")
    bounds = puw.quantity([0, 1], "nm**2")
    if case == "bare_range":
        bounds = [0, 1]
    elif case == "wrong_dimension":
        bounds = puw.quantity([0, 1], "ps")
    elif case == "bare_values":
        values = [0, 0.5, 1]
    elif case == "mixed_bounds":
        bounds = [0, puw.quantity(1, "nm**2")]
    elif case == "nan":
        bounds = puw.quantity([0, np.nan], "nm**2")
    else:
        bounds = [puw.quantity(1, "nm**2"), puw.quantity(0, "angstrom**2")]
    with pytest.raises(ArgumentError):
        scalar_to_color_list(values, palette=PALETTE, value_range=bounds)


@pytest.mark.parametrize("scope", ["whole", "region"])
@pytest.mark.parametrize("by_attribute", [False, True])
def test_real_demo_scalar_colors_preserve_units_and_survive_state_and_history(scope, by_attribute):
    view = demo["dialanine"]
    n_atoms = view.molsys.get_n_atoms()
    magnitudes = np.linspace(0, 1, n_atoms)
    view.molsys.structures.b_factor = puw.quantity(magnitudes[None, :], "nm**2")
    atom_indices = list(range(n_atoms)) if scope == "whole" else [0, 1, 2]
    target = view.whole if scope == "whole" else view.regions.add(atom_indices=atom_indices, tag="physical-colors")
    owner = "whole" if scope == "whole" else target.tag
    expected = scalar_to_color_list(magnitudes[atom_indices], palette=PALETTE, value_range=[0, 1])
    with puw.context(standard_units=ANGSTROM_POLICY):
        if by_attribute:
            target.set_color_by_attribute(
                "b_factor", palette=PALETTE, value_range=puw.quantity([0, 100], "angstrom**2")
            )
        else:
            target.set_color_by_values(
                puw.quantity(magnitudes[atom_indices], "nm**2"),
                palette=PALETTE,
                value_range=puw.quantity([0, 100], "angstrom**2"),
            )
    assert view._atom_color_layers[owner] == dict(zip(atom_indices, expected))
    state = view.export_state()
    view.history.undo()
    assert not view._atom_color_layers.get(owner)
    view.history.redo()
    assert view._atom_color_layers[owner] == dict(zip(atom_indices, expected))
    replacement = demo["dialanine"]
    replacement.import_state(state)
    assert replacement._atom_color_layers[owner] == dict(zip(atom_indices, expected))


@pytest.mark.parametrize("scope", ["whole", "region"])
def test_rejected_physical_range_does_not_change_scene_or_history(scope):
    view = demo["dialanine"]
    target = view.whole if scope == "whole" else view.regions.add(atom_indices=[0, 1], tag="reject-range")
    values = puw.quantity(np.zeros(view.molsys.get_n_atoms() if scope == "whole" else 2), "nm**2")
    before = view.export_state()
    before_undo = view.history.can_undo()
    with pytest.raises(ArgumentError, match="explicit compatible units"):
        target.set_color_by_values(values, value_range=[0, 1])
    assert view.export_state() == before
    assert view.history.can_undo() == before_undo


@pytest.mark.parametrize("scope", ["whole", "region"])
def test_canvas_attribute_actions_accept_physical_range_strings(scope):
    from molsysviewer.viewer.panel_actions.regions import color_region_by_attribute
    from molsysviewer.viewer.panel_actions.whole import color_whole_by_attribute

    view = demo["dialanine"]
    magnitudes = np.linspace(0, 1, view.molsys.get_n_atoms())
    view.molsys.structures.b_factor = puw.quantity(magnitudes[None, :], "nm**2")
    content = {"attribute": "b_factor", "palette": PALETTE, "value_range": "[0,100] angstrom**2"}
    atom_indices = list(range(view.molsys.get_n_atoms())) if scope == "whole" else [0, 1, 2]
    owner = "whole"
    if scope == "region":
        owner = view.regions.add(atom_indices=atom_indices, tag="canvas-physical").tag
        content["tag"] = owner
    with puw.context(standard_units=ANGSTROM_POLICY):
        (color_whole_by_attribute if scope == "whole" else color_region_by_attribute)(view, content)
    expected = scalar_to_color_list(magnitudes[atom_indices], palette=PALETTE, value_range=[0, 1])
    assert view._atom_color_layers[owner] == dict(zip(atom_indices, expected))
