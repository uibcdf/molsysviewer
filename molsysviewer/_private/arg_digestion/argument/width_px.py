from ...exceptions import ArgumentError


def digest_width_px(width_px, caller=None):
    if width_px is None:
        return None
    if isinstance(width_px, bool):
        raise ArgumentError("width_px", value=width_px, caller=caller, message=None)
    if isinstance(width_px, int):
        return width_px
    raise ArgumentError("width_px", value=width_px, caller=caller, message=None)
