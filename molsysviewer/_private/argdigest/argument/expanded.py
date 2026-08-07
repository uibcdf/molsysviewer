from ...exceptions import ArgumentError


def digest_expanded(expanded, caller=None):
    if isinstance(expanded, bool):
        return expanded
    raise ArgumentError("expanded", value=expanded, caller=caller, message=None)

