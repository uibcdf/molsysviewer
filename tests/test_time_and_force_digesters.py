"""Time and force arguments answer with this package's error, not with pint's.

`digest_duration` used to pass an unparseable string straight through, so
`view.focus_region(region, duration="250 milisegundos")` failed a layer later as pint's
`UndefinedUnitError`, naming neither the argument nor the caller. A boolean escaped as
PyUnitWizard's `NotImplementedMethodError`, and `"250"` parsed as **250 radians** and died
on dimensionality. Twelve public callables take `duration` (uibcdf/molsysviewer#86).

The fix is not a patch on one digester: `digest_length_quantity` became the `[L]` case of
`digest_quantity`, and time and force are now the same instrument rather than a second and
third hand-rolled `is_quantity -> check -> standardize -> raise`.
"""

from __future__ import annotations

import pytest
from molsysviewer._private.argdigest._quantity import FORCE_DIMENSIONALITY, digest_quantity
from molsysviewer._private.argdigest.argument.duration import digest_duration
from molsysviewer._private.argdigest.argument.duration_ms import digest_duration_ms
from molsysviewer._private.argdigest.argument.force import digest_force
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw

#: A camera caller, i.e. not one of the movie timeline's plain-millisecond callers.
CAMERA = "molsysviewer.viewer.camera.focus_region"
MOVIE = "molsysviewer.viewer.movie.add_keyframe"

BOTH = (digest_duration, digest_duration_ms)


# --- the defect: a foreign exception reaching the caller -------------------

@pytest.mark.parametrize("digest", BOTH)
@pytest.mark.parametrize(
    "rejected",
    [
        "banana",          # UndefinedUnitError from pint
        "250 bananas",     # likewise, with a plausible shape
        True,              # NotImplementedMethodError from PyUnitWizard
        "250",             # parsed as 250 radians, then DimensionalityError
        "3.5 angstroms",   # a quantity, but not a time
        object(),
    ],
)
def test_a_duration_that_is_not_a_time_raises_this_packages_error(digest, rejected):
    """Exactly `ArgumentError`, never the exception of whatever library noticed.

    `pytest.raises(ArgumentError)` alone would not pin this: `ArgumentError` is a
    `ValueError`, and pint's `UndefinedUnitError` is one too, so a subclass check can pass
    while the caller still meets pint. The type is asserted exactly.
    """
    with pytest.raises(Exception) as raised:
        digest(rejected, caller=CAMERA)
    assert type(raised.value) is ArgumentError, (
        f"{type(raised.value).__name__} reached the caller instead of ArgumentError"
    )


@pytest.mark.parametrize("digest", BOTH)
def test_the_refusal_names_the_argument_and_the_caller(digest):
    with pytest.raises(ArgumentError) as raised:
        digest("banana", caller=CAMERA)
    message = str(raised.value)
    assert CAMERA in message, message
    assert "duration" in message, message


def test_the_original_exception_is_kept_as_the_cause():
    """Translated for the caller, not hidden from whoever debugs it."""
    with pytest.raises(ArgumentError) as raised:
        digest_duration("banana", caller=CAMERA)
    assert raised.value.__cause__ is not None
    assert type(raised.value.__cause__) is not ArgumentError


# --- what the two agree on -------------------------------------------------

@pytest.mark.parametrize("digest", BOTH)
@pytest.mark.parametrize("accepted", ["250 ms", "0.25 s", "250000 us"])
def test_a_time_with_its_units_is_standardized(digest, accepted):
    assert puw.get_unit(digest(accepted, caller=CAMERA)) == puw.unit("picosecond")


@pytest.mark.parametrize("digest", BOTH)
def test_none_stays_none(digest):
    assert digest(None, caller=CAMERA) is None


@pytest.mark.parametrize("spelling", ["250 ms", "0.25 s"])
def test_the_two_names_agree_wherever_they_overlap(spelling):
    """The point of the alias: same value, same answer, whichever name is used."""
    assert digest_duration(spelling, caller=CAMERA) == digest_duration_ms(spelling, caller=CAMERA)


# --- the one place they deliberately differ --------------------------------

@pytest.mark.parametrize("bare", [5, 0, 2.5])
def test_a_bare_number_is_milliseconds_only_where_the_name_says_so(bare):
    """`duration_ms=2` is two milliseconds because its name says so. `duration=2` is not
    anything: nothing in it distinguishes two seconds from two milliseconds, and guessing
    is the silent scale error the units policy exists to prevent."""
    assert puw.get_value(digest_duration_ms(bare, caller=CAMERA), to_unit="ms") == bare

    with pytest.raises(ArgumentError):
        digest_duration(bare, caller=CAMERA)


def test_the_refusal_of_a_bare_number_points_at_the_name_that_accepts_one():
    """A rule the caller cannot act on is a worse error than no rule."""
    with pytest.raises(ArgumentError) as raised:
        digest_duration(250, caller=CAMERA)
    message = str(raised.value)
    assert "duration_ms" in message, message
    assert "250 ms" in message, message


# --- the movie timeline's carve-out ----------------------------------------

def test_the_movie_timeline_still_gets_plain_milliseconds():
    """Keyframes are serialised to JSON by `to_dict`, where a quantity cannot travel."""
    value = digest_duration_ms(250, caller=MOVIE)
    assert value == 250.0 and isinstance(value, float)


@pytest.mark.parametrize("rejected", [0, -1, True, "250 ms"])
def test_the_movie_timeline_refuses_what_it_cannot_serialise(rejected):
    with pytest.raises(ArgumentError):
        digest_duration_ms(rejected, caller=MOVIE)


# --- force -----------------------------------------------------------------

@pytest.mark.parametrize("caller", ["molsysviewer.viewer.show", "molsysviewer.viewer.MolSysView.show"])
@pytest.mark.parametrize("flag", [True, False])
def test_force_is_a_boolean_where_show_asks_it(caller, flag):
    """Same name, unrelated question, decided by the caller."""
    assert digest_force(flag, caller=caller) is flag


def test_a_force_elsewhere_is_a_physical_magnitude():
    digested = digest_force("5 kilojoule/(mol*nanometer)", caller="molsysviewer.something")
    assert puw.get_value(digested, to_unit="kilojoule/(mol*nanometer)") == pytest.approx(5.0)


@pytest.mark.parametrize("rejected", [5, "banana", "3.5 angstroms", True])
def test_a_force_that_is_not_one_raises_this_packages_error(rejected):
    with pytest.raises(Exception) as raised:
        digest_force(rejected, caller="molsysviewer.something")
    assert type(raised.value) is ArgumentError, type(raised.value).__name__


# --- the shared boundary itself --------------------------------------------

@pytest.mark.parametrize(
    ("dimensionality", "accepted"),
    [
        ({"[L]": 1}, "3.5 angstroms"),
        ({"[T]": 1}, "250 ms"),
        (FORCE_DIMENSIONALITY, "5 kilojoule/(mol*nanometer)"),
    ],
)
def test_one_boundary_serves_every_magnitude(dimensionality, accepted):
    assert digest_quantity(accepted, "x", dimensionality, caller="test") is not None
    with pytest.raises(ArgumentError):
        digest_quantity("banana", "x", dimensionality, caller="test")
