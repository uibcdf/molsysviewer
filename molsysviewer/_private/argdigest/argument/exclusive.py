from ...exceptions import ArgumentError


def digest_exclusive(exclusive, caller=None):
    if isinstance(exclusive, bool):
        return exclusive
    raise ArgumentError("exclusive", value=exclusive, caller=caller)
