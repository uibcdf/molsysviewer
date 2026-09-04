"""Every MolSysMT attribute must answer through the viewer, whoever digests it.

This file used to ask a narrower question. The digesters here were copied from MolSysMT,
each one a whitelist of callers, and none of those whitelists knew MolSysViewer — so 58 of
81 query arguments were rejected for months under a green suite. The guard was: *does our
copy accept our caller?*

`uibcdf/molsysviewer#71` removed the copies. MolSysMT digests its own arguments now, and
its whitelist names its own function, so the failure mode that guard existed for cannot
recur in that form. What can still break is the thing a user cares about, and that is what
is asked here instead: **does the attribute answer?**

The question is asked of both objects that answer it, because they used to differ:
`region.get` refused 77 of the 118 attributes the view answered, for exactly the whitelist
reason above — its caller was in no list. Delegation made them agree; this keeps them
agreeing. The view itself no longer answers at all — `view.get` was removed in phase D of
`uibcdf/molsysviewer#75`, and the whole is where the system is asked.
"""

from __future__ import annotations

import pytest
from molsysmt.attribute import attributes

from molsysviewer import demo

#: MolSysMT's own attribute names, from their public data rather than a list of ours.
ATTRIBUTES = sorted(attributes.keys() if isinstance(attributes, dict) else attributes)


@pytest.fixture(scope="module")
def view():
    v = demo["1TCD"]
    v.make_regions_by("chain")
    return v


@pytest.fixture(scope="module")
def region(view):
    regions = view.regions
    return list(regions.values())[0] if hasattr(regions, "values") else regions[0]


def test_the_attribute_inventory_is_not_empty():
    """If this collapses, every sweep below passes by asking nothing."""
    assert len(ATTRIBUTES) > 100


def _answered(target) -> set[str]:
    answered = set()
    for name in ATTRIBUTES:
        try:
            target.get(element="atom", **{name: True})
        except Exception:
            continue
        answered.add(name)
    return answered


def test_the_whole_answers_most_of_the_attribute_surface(view):
    """A floor, not an exact count: MolSysMT refusing some of its own is theirs to decide."""
    assert len(_answered(view.whole)) >= 100


def test_a_region_answers_exactly_what_the_whole_does(view, region):
    """The regression this file was rewritten for.

    Before delegation a region answered 41 of 118 where the system answered 105 — not
    because a region is different, but because our copies whitelisted
    `molsysviewer.viewer.get` and never `molsysviewer.regions.get`. A region holds fewer
    atoms, not fewer *kinds of question*.
    """
    assert _answered(region) == _answered(view.whole)


def test_the_view_itself_no_longer_answers_about_the_system():
    """Phase D: the question has one place to be asked, and it is not the view."""
    import molsysviewer as msv

    assert not hasattr(msv.demo["1TCD"], "get")


@pytest.mark.parametrize("owner", ["whole", "region"])
def test_a_rejected_value_names_the_method_the_user_called(view, region, owner):
    """Delegated digestion must not delegate the message. See `_private/delegated_errors.py`."""
    from molsysviewer._private.exceptions import ArgumentError

    target = {"whole": view.whole, "region": region}[owner]
    expected = {
        "whole": "molsysviewer.whole.get",
        "region": "molsysviewer.regions.get",
    }[owner]

    with pytest.raises(ArgumentError) as raised:
        target.get(element="atom", atom_name=123)

    assert expected in str(raised.value)
