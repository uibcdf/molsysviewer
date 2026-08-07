from ...exceptions import ArgumentError


def digest_color_by(color_by, caller=None):
    if color_by is None:
        return None
    if isinstance(color_by, str):
        return color_by
    raise ArgumentError("color_by", value=color_by, caller=caller, message=None)
