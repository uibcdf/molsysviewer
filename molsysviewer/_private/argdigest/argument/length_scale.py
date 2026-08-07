import math

from ...exceptions import ArgumentError


def digest_length_scale(length_scale, caller=None):
    """Digest the global scale factor applied to vector lengths.

    Must be a finite, strictly positive number: zero or negative would collapse
    or invert every vector.
    """
    if isinstance(length_scale, bool):
        raise ArgumentError("length_scale", value=length_scale, caller=caller, message=None)

    if isinstance(length_scale, (int, float)):
        value = float(length_scale)
        if math.isfinite(value) and value > 0.0:
            return value

    raise ArgumentError(
        "length_scale",
        value=length_scale,
        caller=caller,
        message=" The scale factor must be a positive number.",
    )
