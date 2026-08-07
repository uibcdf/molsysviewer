from ...exceptions import ArgumentError


def digest_surface_radius_scale(surface_radius_scale, caller=None):
    if surface_radius_scale is None:
        return None
    if isinstance(surface_radius_scale, (int, float)) and not isinstance(surface_radius_scale, bool):
        value = float(surface_radius_scale)
        if value > 0.0:
            return value
    raise ArgumentError('surface_radius_scale', value=surface_radius_scale, caller=caller, message=None)
