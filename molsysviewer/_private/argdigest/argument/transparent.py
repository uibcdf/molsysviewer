from ...exceptions import ArgumentError


def digest_transparent(transparent, caller=None):
    if isinstance(transparent, bool):
        return transparent
    raise ArgumentError("transparent", value=transparent, caller=caller, message=None)
