from ...exceptions import ArgumentError


def digest_color_mode(color_mode, caller=None):
    if color_mode is None:
        return None
    if isinstance(color_mode, str):
        return color_mode
    raise ArgumentError("color_mode", value=color_mode, caller=caller, message=None)
