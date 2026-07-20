from ...exceptions import ArgumentError


def digest_fade(fade, caller=None):
    """Digest the fade level applied to everything outside the focus.

    It is a transparency, so it must be a real number in ``[0, 1]``; ``0``
    clears the effect. Booleans are rejected because ``True``/``False`` are not
    meaningful transparencies.
    """
    if isinstance(fade, bool):
        raise ArgumentError("fade", value=fade, caller=caller, message=None)

    if isinstance(fade, (int, float)):
        value = float(fade)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "fade",
        value=fade,
        caller=caller,
        message=" Fade must be a number between 0 and 1.",
    )
