from ...exceptions import ArgumentError


def digest_exterior_only(exterior_only, caller=None):
    """Digest whether only exterior faces are drawn. Booleans only."""
    if isinstance(exterior_only, bool):
        return exterior_only

    raise ArgumentError("exterior_only", value=exterior_only, caller=caller, message=None)
