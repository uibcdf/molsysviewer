from ...exceptions import ArgumentError


def digest_visible(visible, caller=None):
    if isinstance(visible, bool):
        return visible
    raise ArgumentError("visible", value=visible, caller=caller, message=None)
