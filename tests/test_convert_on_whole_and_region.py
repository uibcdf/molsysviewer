"""`convert` on the two objects that have a subject, and the caller a user reads.

`view.convert` is going away with the rest of the MolSysMT-facing façade
(`uibcdf/molsysviewer#71`, executed in `uibcdf/molsysviewer#75`), and it was the one method
with nowhere to go: neither `Whole` nor `Region` had it. They do now, with the scoping
`get` already had — the whole answers for the whole system, a region for its own atoms.

The second thing pinned here is the error contract. Digestion is delegated to MolSysMT
because our copies accept exactly what theirs do, but a user who called
`whole.convert(...)` must not read a message blaming `molsysmt.basic.convert.convert` for
an argument they never handed to MolSysMT. Only the caller is replaced; the argument, the
value and the chained original all survive.
"""

from __future__ import annotations

import molsysmt as msm
import pytest

import molsysviewer as msv
from molsysviewer._private.exceptions import ArgumentError


@pytest.fixture(scope="module")
def view():
    v = msv.demo["1TCD"]
    v.make_regions_by("chain")
    return v


@pytest.fixture(scope="module")
def region(view):
    regions = view.regions
    return list(regions.values())[0] if hasattr(regions, "values") else regions[0]


def test_the_whole_converts_the_whole_system(view):
    converted = view.whole.convert(to_form="molsysmt.MolSys")
    assert msm.get(converted, n_atoms=True) == msm.get(view._molsys, n_atoms=True)  # noqa: SLF001


def test_a_region_converts_its_own_atoms_and_nothing_else(region):
    """The scoping that makes this worth having: a region is a selection, not the system."""
    converted = region.convert(to_form="molsysmt.MolSys")
    assert msm.get(converted, n_atoms=True) == len(region.atom_indices)


def test_a_region_converts_fewer_atoms_than_the_whole(view, region):
    """Guards the scoping itself: identical counts would pass the test above by accident."""
    assert len(region.atom_indices) < msm.get(view._molsys, n_atoms=True)  # noqa: SLF001


@pytest.mark.parametrize(
    ("owner", "caller"),
    [("whole", "molsysviewer.whole.convert"), ("region", "molsysviewer.regions.convert")],
)
def test_a_bad_argument_names_the_method_the_user_called(view, region, owner, caller):
    """Not `molsysmt.basic.convert.convert`, which the user never called."""
    target = view.whole if owner == "whole" else region

    with pytest.raises(ArgumentError) as raised:
        target.convert(to_form="no.such.form")

    message = str(raised.value)
    assert caller in message, message
    assert "molsysmt." not in message.split("Docs")[0], (
        f"the delegated library is named in the message a user reads: {message}"
    )
    assert "to_form" in message and "no.such.form" in message


@pytest.mark.parametrize("owner", ["whole", "region"])
def test_the_delegated_error_stays_chained(view, region, owner):
    """Replaced for the reader, kept for whoever is debugging."""
    target = view.whole if owner == "whole" else region
    with pytest.raises(ArgumentError) as raised:
        target.convert(to_form="no.such.form")
    assert raised.value.__cause__ is not None
    assert "molsysmt" in type(raised.value.__cause__).__module__
