from ...exceptions import ArgumentError


def digest_styles(styles, caller=None):
    if isinstance(styles, bool):
        return styles
    raise ArgumentError("styles", value=styles, caller=caller, message=None)
