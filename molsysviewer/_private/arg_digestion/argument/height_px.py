from ...exceptions import ArgumentError


def digest_height_px(height_px, caller=None):
    if height_px is None:
        return None
    if isinstance(height_px, bool):
        raise ArgumentError("height_px", value=height_px, caller=caller, message=None)
    if isinstance(height_px, int):
        return height_px
    raise ArgumentError("height_px", value=height_px, caller=caller, message=None)
