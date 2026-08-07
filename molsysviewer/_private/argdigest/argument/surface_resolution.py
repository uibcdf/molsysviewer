from ...exceptions import ArgumentError


def digest_surface_resolution(surface_resolution, caller=None):
    if surface_resolution is None:
        return None
    if isinstance(surface_resolution, (int, float)) and not isinstance(surface_resolution, bool):
        value = float(surface_resolution)
        if value > 0.0:
            return value
    raise ArgumentError('surface_resolution', value=surface_resolution, caller=caller, message=None)
