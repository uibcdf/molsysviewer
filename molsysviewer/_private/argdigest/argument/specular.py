from ...exceptions import ArgumentError


def digest_specular(specular, caller=None):
    """Digest the specular light intensity.

    It is an intensity in ``[0, 1]``. Booleans are rejected: ``True``/``False`` are
    not meaningful intensities, and Python would otherwise accept them as 1 and 0.
    """
    if specular is None:
        return None

    if isinstance(specular, bool):
        raise ArgumentError("specular", value=specular, caller=caller, message=None)

    if isinstance(specular, (int, float)):
        value = float(specular)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "specular",
        value=specular,
        caller=caller,
        message=" The specular intensity must be a number between 0 and 1.",
    )
