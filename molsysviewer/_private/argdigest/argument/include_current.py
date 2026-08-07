from ...exceptions import ArgumentError


def digest_include_current(include_current, caller=None):
    if isinstance(include_current, bool):
        return include_current
    raise ArgumentError("include_current", value=include_current, caller=caller, message=None)
