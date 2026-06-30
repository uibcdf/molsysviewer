from __future__ import annotations

from importlib.resources import files
import warnings

import pytest

import molsysmt as msm  # noqa: F401
import molsysviewer as viewer
from molsysviewer import demo


def test_demo_region_hide():
    """Smoke-test: create a region and hide it without errors."""

    demo_system = files("molsysviewer.data.h5msm").joinpath("1TCD.h5msm")
    view = viewer.new_view(demo_system, debug_js=True)
    # Avoid real frontend traffic; we only need the calls to not fail.
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.show()
    region = view.new_region("chain_id == 'A'", representation="sticks")
    region.hide()

    assert region is not None
    assert region.tag in view.regions


def test_region_scoped_indices_bond():
    """Region._scoped_indices_for_element('bond') returns non-empty sorted int list."""
    view = demo["dialanine"]
    region = view.new_region(selection="group_index == 0", tag="bond-scope-test")

    bond_indices = region._scoped_indices_for_element("bond")

    assert isinstance(bond_indices, list)
    assert len(bond_indices) > 0
    assert all(isinstance(i, int) for i in bond_indices)
    assert bond_indices == sorted(set(bond_indices))


def test_region_scoped_indices_bond_subset():
    """Bond scoping on a single-atom region returns only the bonds of that atom."""
    view = demo["dialanine"]
    region = view.new_region(selection="atom_index == 1", tag="bond-scope-single")

    bond_indices = region._scoped_indices_for_element("bond")

    assert isinstance(bond_indices, list)
    assert len(bond_indices) > 0



def _empty_view():
    view = viewer.MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_region_boolean_composition_from_atom_indices():
    view = _empty_view()
    left = view.new_region(atom_indices=[0, 1, 2], tag="left", skip_digestion=True)
    right = view.new_region(atom_indices=[2, 3], tag="right", skip_digestion=True)

    difference = left.difference(right, tag="left-minus-right")
    intersection = left & right
    union = left.union(right, tag="left-or-right")

    assert difference.atom_indices == (0, 1)
    assert intersection.atom_indices == (2,)
    assert union.atom_indices == (0, 1, 2, 3)
    assert "left_and_right" in view.regions
    assert any(
        msg.get("op") == "create_region"
        and msg.get("tag") == "left-minus-right"
        and msg.get("atom_indices") == [0, 1]
        for msg in view._message_history  # noqa: SLF001
    )


def test_region_boolean_composition_rejects_empty_result():
    view = _empty_view()
    left = view.new_region(atom_indices=[0, 1], tag="left", skip_digestion=True)
    right = view.new_region(atom_indices=[2, 3], tag="right", skip_digestion=True)

    with pytest.raises(ValueError, match="empty region"):
        left.intersection(right)


def test_region_overlap_warning_when_visualizing_overlap():
    view = _empty_view()
    view.new_region(atom_indices=[0, 1, 2], tag="first", representation="line", skip_digestion=True)
    second = view.new_region(atom_indices=[2, 3], tag="second", skip_digestion=True)

    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        second.set_representation("ball-and-stick", skip_digestion=True)


def test_region_overlap_warning_when_creating_visual_overlap():
    view = _empty_view()
    view.new_region(atom_indices=[0, 1, 2], tag="first", representation="line", skip_digestion=True)

    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        view.new_region(atom_indices=[2, 3], tag="second", representation="ball-and-stick", skip_digestion=True)


def test_region_overlap_warning_ignores_logical_and_hidden_regions():
    view = _empty_view()
    view.new_region(atom_indices=[0, 1], tag="logical", skip_digestion=True)
    hidden = view.new_region(atom_indices=[1, 2], tag="hidden", representation="line", skip_digestion=True)
    hidden.hide(skip_digestion=True)

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        view.new_region(atom_indices=[1, 2, 3], tag="visible", representation="line", skip_digestion=True)

    assert record == []
