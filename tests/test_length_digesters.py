"""The `[L]` digesters consolidated under `uibcdf/molsysviewer#33`, and what they promise.

Three promises, each of which was broken by at least one of these before this file existed:

**A length needs explicit units.** The normative policy refuses a bare number so a
nanometre can never be read as an angstrom. A string carrying units is accepted, because
`puw` parses it.

**A bad argument raises this package's own `ArgumentError`.** Never pint's
`UndefinedUnitError`, never `AttributeError`. Measured: syncing `threshold` with MolSysMT's
version let `UndefinedUnitError` escape for `"hola"`, and the branched copies of
`switch_distance` and `cutoff_distance` raised `AttributeError` for *every* value when no
caller was given, because they reached `caller.startswith` before testing it.

**`None` means what each argument means by it.** `switch_distance` and `max_bond_length`
take it as "unset" from anybody; `cutoff_distance` only from the form converters, which is
the narrower rule its branched version had. Widening it was measured to turn five
caller/None pairs from a refusal into a silent `None`, so it was not widened.
"""

from __future__ import annotations

import pytest

from molsysviewer._pyunitwizard import puw
from molsysviewer._private.argdigest.argument.cutoff_distance import digest_cutoff_distance
from molsysviewer._private.argdigest.argument.distance_threshold import digest_distance_threshold
from molsysviewer._private.argdigest.argument.extra_radius import digest_extra_radius
from molsysviewer._private.argdigest.argument.max_bond_length import digest_max_bond_length
from molsysviewer._private.argdigest.argument.min_radius import digest_min_radius
from molsysviewer._private.argdigest.argument.switch_distance import digest_switch_distance
from molsysviewer._private.argdigest.argument.threshold import digest_threshold
from molsysviewer._private.exceptions import ArgumentError

#: Every digester here, with a caller each one accepts values for.
DIGESTERS = [
    (digest_switch_distance, "molsysviewer.viewer.get"),
    (digest_cutoff_distance, "molsysviewer.viewer.get"),
    (digest_max_bond_length, "molsysviewer.viewer.get"),
    (digest_extra_radius, "molsysviewer.viewer.zoom"),
    (digest_min_radius, "molsysviewer.viewer.zoom"),
    (digest_threshold, "molsysmt.structure.get_contacts.get_contacts"),
    (digest_distance_threshold, "molsysmt.hbonds.get_buch_hbonds.get_buch_hbonds"),
]
IDS = [fn.__name__ for fn, _ in DIGESTERS]

#: The two whose branched versions crashed instead of refusing.
CRASHED_WITHOUT_A_CALLER = [digest_switch_distance, digest_cutoff_distance]


@pytest.mark.parametrize(("digest", "caller"), DIGESTERS, ids=IDS)
def test_a_length_in_units_is_standardized(digest, caller):
    assert digest("3.5 angstroms", caller=caller) == puw.quantity(0.35, "nanometer")
    assert digest(puw.quantity(3.5, "angstroms"), caller=caller) == puw.quantity(0.35, "nanometer")


@pytest.mark.parametrize(("digest", "caller"), DIGESTERS, ids=IDS)
@pytest.mark.parametrize("bare", [3.5, 1, True], ids=["float", "int", "bool"])
def test_a_bare_number_is_refused(digest, caller, bare):
    """The whole point of the policy: 3.5 nanometres and 3.5 angstroms differ by ten."""
    with pytest.raises(ArgumentError):
        digest(bare, caller=caller)


@pytest.mark.parametrize(("digest", "caller"), DIGESTERS, ids=IDS)
def test_an_unparseable_string_raises_this_packages_error(digest, caller):
    """Not pint's `UndefinedUnitError`, which MolSysMT's own version lets escape."""
    with pytest.raises(ArgumentError):
        digest("hola", caller=caller)


@pytest.mark.parametrize("digest", CRASHED_WITHOUT_A_CALLER, ids=lambda f: f.__name__)
@pytest.mark.parametrize(
    "value", ["3.5 angstroms", 3.5, None, "hola"], ids=["quantity", "bare", "none", "junk"]
)
def test_no_caller_is_answered_rather_than_crashed(digest, value):
    """The regression. `caller.startswith(...)` on `None` raised AttributeError for every value.

    What it answers matters less than that it answers: a digester reached without a caller
    must refuse, accept or pass through, never raise the error of a missing attribute.
    """
    try:
        digest(value, caller=None)
    except ArgumentError:
        pass
    except AttributeError as exc:  # pragma: no cover - the regression itself
        pytest.fail(f"{digest.__name__} crashed instead of answering: {exc}")


@pytest.mark.parametrize(
    ("digest", "caller", "accepted"),
    [
        (digest_switch_distance, "molsysviewer.viewer.get", True),
        (digest_max_bond_length, "molsysviewer.viewer.get", True),
        (digest_cutoff_distance, "molsysviewer.viewer.get", False),
        # The form branch is `.startswith("molsysmt.form.")` **and** two `.to_` segments;
        # one segment is not enough, which is why both of these appear here.
        (digest_cutoff_distance, "molsysmt.form.molsysmt_MolSys.to_molsysmt_Structures", False),
        (digest_cutoff_distance, "molsysmt.form.file_pdb.to_molsysmt_MolSys.to_molsysmt_MolSys", True),
    ],
    ids=["switch_distance", "max_bond_length", "cutoff_distance/viewer",
         "cutoff_distance/one-to", "cutoff_distance/two-to"],
)
def test_none_is_accepted_exactly_where_it_was_before(digest, caller, accepted):
    if accepted:
        assert digest(None, caller=caller) is None
    else:
        with pytest.raises(ArgumentError):
            digest(None, caller=caller)
