import importlib

import numpy as np
import pytest
from molsysviewer._private.argdigest import (
    digest_selection_and_syntax,
    digest_selection_inputs,
)


def test_digest_selection_and_syntax_normalizes_syntax():
    selection, syntax = digest_selection_and_syntax("all", syntax="mdtraj", caller="test")

    assert selection == "all"
    assert syntax == "MDTraj"


def test_digest_selection_inputs_handles_indices():
    selection, structure_indices, syntax = digest_selection_inputs(
        selection=[1, 2, 3],
        structure_indices=0,
        syntax="MolSysMT",
        caller="test",
    )

    assert selection == [1, 2, 3]
    assert isinstance(structure_indices, np.ndarray)
    assert structure_indices.tolist() == [0]
    assert syntax == "MolSysMT"


@pytest.mark.parametrize("name", ["distance", "length", "z0"])
def test_the_scalar_length_digesters_go_through_the_shared_boundary(name):
    """Three digesters were the same twelve lines, and none of them said what to do.

    Each hand-rolled `is_quantity -> check -> standardize -> raise` and raised with
    `message=None`, so a caller who passed `3.5` was told only that the argument was
    wrong. Consolidated on `digest_length_quantity` under uibcdf/molsysviewer#33.

    What this pins is the *message*, not the plumbing: the units policy exists because
    a bare number is a silent nm/angstrom scale error waiting to happen, and an error
    that does not name the unit to add leaves the caller to guess which one this API
    wanted.
    """
    from molsysviewer._pyunitwizard import puw

    digest = getattr(
        importlib.import_module(f"molsysviewer._private.argdigest.argument.{name}"),
        f"digest_{name}",
    )

    # A quantity is standardized to the project's canonical unit, not merely accepted.
    standardized = digest(puw.quantity(3.5, "angstroms"), caller="test")
    assert puw.get_unit(standardized) == puw.unit("nanometer")

    with pytest.raises(Exception) as raised:
        digest(3.5, caller="test")
    message = str(raised.value)
    assert "explicit units" in message, message
    assert "angstrom" in message.lower(), (
        "the error does not name a unit the caller could actually type"
    )
