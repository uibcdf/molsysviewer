from ...exceptions import ArgumentError


def digest_alpha_alpha_spheres(alpha_alpha_spheres, caller=None):
    """Digest the ``alpha_alpha_spheres`` opacity, a number in ``[0, 1]``.

    Booleans are rejected: ``True``/``False`` are ints in Python but not
    meaningful opacities.
    """
    if alpha_alpha_spheres is None:
        return None

    if not isinstance(alpha_alpha_spheres, bool) and isinstance(alpha_alpha_spheres, (int, float)):
        value = float(alpha_alpha_spheres)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "alpha_alpha_spheres",
        value=alpha_alpha_spheres,
        caller=caller,
        message=" Opacity must be a number between 0 and 1.",
    )
