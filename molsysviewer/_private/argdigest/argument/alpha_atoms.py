from ...exceptions import ArgumentError


def digest_alpha_atoms(alpha_atoms, caller=None):
    """Digest the ``alpha_atoms`` opacity, a number in ``[0, 1]``.

    Booleans are rejected: ``True``/``False`` are ints in Python but not
    meaningful opacities.
    """
    if alpha_atoms is None:
        return None

    if not isinstance(alpha_atoms, bool) and isinstance(alpha_atoms, (int, float)):
        value = float(alpha_atoms)
        if 0.0 <= value <= 1.0:
            return value

    raise ArgumentError(
        "alpha_atoms",
        value=alpha_atoms,
        caller=caller,
        message=" Opacity must be a number between 0 and 1.",
    )
