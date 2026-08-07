from ...exceptions import ArgumentError


def digest_replace(replace, caller=None):
    """Digest the color-layer replacement flag.

    Accepts only ``bool`` and returns it unchanged. Integers and strings are not
    coerced, because ``replace`` controls whether the existing color layer is
    discarded or incrementally updated.
    """
    if isinstance(replace, bool):
        return replace

    raise ArgumentError("replace", value=replace, caller=caller, message=None)
