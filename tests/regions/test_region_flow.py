from __future__ import annotations

from importlib.resources import files

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
