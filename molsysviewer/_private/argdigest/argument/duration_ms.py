"""`duration_ms` is a duration whose name states its unit, so a bare number is allowed.

Two carve-outs, both semantic:

The movie timeline keeps **plain** milliseconds. Its keyframes are serialised to JSON by
`to_dict` and a quantity cannot travel there, so those callers get a float and the units
policy does not apply to them.

Everywhere else a bare number means milliseconds — that is what the argument's name says —
and anything else goes through the shared boundary, which raises `ArgumentError` rather
than letting pint's `UndefinedUnitError` out (uibcdf/molsysviewer#86).
"""

from molsysviewer._pyunitwizard import puw

from ...exceptions import ArgumentError
from .._quantity import digest_quantity

_PLAIN_MILLISECOND_CALLERS = frozenset({
    "molsysviewer.viewer.movie.add_keyframe",
    "molsysviewer.viewer.movie.add_camera_orbit",
    "molsysviewer.viewer.movie.add_structure_sweep",
    "molsysviewer.viewer.movie.export",
})

_MESSAGE = (" A duration in milliseconds: either a bare number (250) or a quantity with "
            "explicit units (\"250 ms\").")


def digest_duration_ms(duration_ms, caller=None):
    if duration_ms is None:
        return None

    if caller in _PLAIN_MILLISECOND_CALLERS:
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
            raise ArgumentError("duration_ms", value=duration_ms, caller=caller,
                                message="expected a duration in milliseconds")
        if duration_ms <= 0:
            raise ArgumentError("duration_ms", value=duration_ms, caller=caller,
                                message="must be positive: a segment of zero length holds no keyframes")
        return float(duration_ms)

    # `bool` before `int`, because `True` is an `int` and a boolean duration is a mistake,
    # not one millisecond.
    if not isinstance(duration_ms, bool) and isinstance(duration_ms, (int, float)):
        duration_ms = puw.quantity(float(duration_ms), "ms")

    return digest_quantity(duration_ms, "duration_ms", {"[T]": 1}, caller=caller,
                           message=_MESSAGE)
