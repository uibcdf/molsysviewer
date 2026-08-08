from ...exceptions import ArgumentError


def digest_diffuse(diffuse, caller=None):
    """Digest the diffuse light intensity.

    It is an intensity in ``[0, 1]``. Booleans are rejected: ``True``/``False`` are
    not meaningful intensities, and Python would otherwise accept them as 1 and 0.
    """
    if diffuse is None:
        return None

    if isinstance(diffuse, bool):
        raise ArgumentError("diffuse", value=diffuse, caller=caller, message=None)

    if isinstance(diffuse, (int, float)):
        value = float(diffuse)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "diffuse",
        value=diffuse,
        caller=caller,
        message=" The diffuse intensity must be a number between 0 and 1.",
    )
