from ...exceptions import ArgumentError


def digest_color_scheme(color_scheme, caller=None):
    if color_scheme is None:
        return None
    if isinstance(color_scheme, str):
        return color_scheme
    raise ArgumentError("color_scheme", value=color_scheme, caller=caller, message=None)
