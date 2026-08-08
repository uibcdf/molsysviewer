from ...exceptions import ArgumentError


def digest_ambient(ambient, caller=None):
    """Digest the ambient light intensity.

    It is an intensity in ``[0, 1]``. Booleans are rejected: ``True``/``False`` are
    not meaningful intensities, and Python would otherwise accept them as 1 and 0.
    """
    if ambient is None:
        return None

    if isinstance(ambient, bool):
        raise ArgumentError("ambient", value=ambient, caller=caller, message=None)

    if isinstance(ambient, (int, float)):
        value = float(ambient)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "ambient",
        value=ambient,
        caller=caller,
        message=" The ambient intensity must be a number between 0 and 1.",
    )
