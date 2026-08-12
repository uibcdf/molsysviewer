from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


#: The movie timeline keeps plain milliseconds: its keyframes are serialised to JSON by
#: `to_dict`, and a quantity cannot travel there. Everywhere else a duration is a physical
#: magnitude and is standardised, per the units policy.
_PLAIN_MILLISECOND_CALLERS = frozenset({
    "molsysviewer.viewer.movie.add_keyframe",
    "molsysviewer.viewer.movie.add_camera_orbit",
    "molsysviewer.viewer.movie.add_structure_sweep",
    "molsysviewer.viewer.movie.export",
})


def digest_duration_ms(duration_ms, caller=None):
    if duration_ms is None:
        return duration_ms
    if caller in _PLAIN_MILLISECOND_CALLERS:
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
            raise ArgumentError("duration_ms", value=duration_ms, caller=caller,
                                message="expected a duration in milliseconds")
        if duration_ms <= 0:
            raise ArgumentError("duration_ms", value=duration_ms, caller=caller,
                                message="must be positive: a segment of zero length holds no keyframes")
        return float(duration_ms)
    if puw.is_quantity(duration_ms):
        return puw.standardize(duration_ms)
    if isinstance(duration_ms, (int, float)):
        return puw.quantity(duration_ms, "ms", standardized=True)
    if isinstance(duration_ms, str):
        try:
            value = float(duration_ms)
        except ValueError:
            return duration_ms
        return puw.quantity(value, "ms", standardized=True)
    raise ArgumentError("duration_ms", value=duration_ms, caller=caller, message=None)
