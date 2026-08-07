from ...exceptions import ArgumentError


def digest_include_controls(include_controls, caller=None):
    if isinstance(include_controls, bool):
        return include_controls
    raise ArgumentError("include_controls", value=include_controls, caller=caller, message=None)
