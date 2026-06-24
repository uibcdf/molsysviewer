from ...exceptions import ArgumentError


def digest_surface_iso_level(surface_iso_level, caller=None):
    if surface_iso_level is None:
        return None
    if isinstance(surface_iso_level, (int, float)) and not isinstance(surface_iso_level, bool):
        value = float(surface_iso_level)
        if value > 0.0:
            return value
    raise ArgumentError('surface_iso_level', value=surface_iso_level, caller=caller, message=None)
