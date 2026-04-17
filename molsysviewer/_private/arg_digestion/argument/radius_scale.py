from ...exceptions import ArgumentError


def digest_radius_scale(radius_scale, caller=None):
    if radius_scale is None:
        return None
    if isinstance(radius_scale, (int, float)) and not isinstance(radius_scale, bool):
        return float(radius_scale)
    raise ArgumentError("radius_scale", value=radius_scale, caller=caller, message=None)
