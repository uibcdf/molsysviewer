"""`intensity` is the strength of the fog, in `[0, 1]`.

Booleans are rejected for the reason `ambient` rejects them: `True` and `False` are not
intensities, and Python would silently read them as 1 and 0 — full fog, or none.

`None` is valid and leaves the current value alone.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_intensity(intensity, caller=None):
    if intensity is None:
        return None
    if isinstance(intensity, bool) or not isinstance(intensity, (int, float)):
        raise ArgumentError("intensity", value=intensity, caller=caller, message=None)
    value = float(intensity)
    if 0.0 <= value <= 1.0:
        return value
    raise ArgumentError(
        "intensity",
        value=intensity,
        caller=caller,
        message="a fog intensity lies in [0, 1]",
    )
