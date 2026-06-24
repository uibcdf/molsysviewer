from ...exceptions import ArgumentError


def digest_surface_smoothing(surface_smoothing, caller=None):
    if surface_smoothing is None:
        return None
    if isinstance(surface_smoothing, (int, float)) and not isinstance(surface_smoothing, bool):
        value = float(surface_smoothing)
        if value > 0.0:
            return value
    raise ArgumentError('surface_smoothing', value=surface_smoothing, caller=caller, message=None)
