"""Every MolSysMT attribute must answer through the viewer, whoever digests it.

This file used to ask a narrower question. The digesters here were copied from MolSysMT,
each one a whitelist of callers, and none of those whitelists knew MolSysViewer — so 58 of
81 query arguments were rejected for months under a green suite. The guard was: *does our
copy accept our caller?*

`uibcdf/molsysviewer#71` removed the copies. MolSysMT digests its own arguments now, and
its whitelist names its own function, so the failure mode that guard existed for cannot
recur in that form. What can still break is the thing a user cares about, and that is what
is asked here instead: **does the attribute answer?**

The question is asked of all three objects, because they used to differ. `region.get`
refused 77 of the 118 attributes `view.get` answered, for exactly the whitelist reason
above — its caller was in no list. Delegation made the three agree; this keeps them
agreeing.
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


def test_the_view_answers_most_of_the_attribute_surface(view):
    """A floor, not an exact count: MolSysMT refusing some of its own is theirs to decide."""
    assert len(_answered(view)) >= 100


def test_the_whole_answers_exactly_what_the_view_does(view):
    """The whole *is* the system, so a difference here is a bug on our side by definition."""
    assert _answered(view.whole) == _answered(view)


def test_a_region_answers_exactly_what_the_view_does(view, region):
    """The regression this file was rewritten for.

    Before delegation a region answered 41 of 118 where the view answered 105 — not
    because a region is different, but because our copies whitelisted
    `molsysviewer.viewer.get` and never `molsysviewer.regions.get`.
    """
    assert _answered(region) == _answered(view)


@pytest.mark.parametrize("owner", ["view", "whole", "region"])
def test_a_rejected_value_names_the_method_the_user_called(view, region, owner):
    """Delegated digestion must not delegate the message. See `_private/delegated_errors.py`."""
    from molsysviewer._private.exceptions import ArgumentError

    target = {"view": view, "whole": view.whole, "region": region}[owner]
    expected = {
        "view": "molsysviewer.viewer.get",
        "whole": "molsysviewer.whole.get",
        "region": "molsysviewer.regions.get",
    }[owner]

    with pytest.raises(ArgumentError) as raised:
        target.get(element="atom", atom_name=123)

    assert expected in str(raised.value)
