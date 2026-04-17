from ...exceptions import ArgumentError


def digest_max_eccentricity(max_eccentricity, caller=None):
    if max_eccentricity is None:
        return None
    if isinstance(max_eccentricity, (int, float)) and not isinstance(max_eccentricity, bool):
        return float(max_eccentricity)
    raise ArgumentError("max_eccentricity", value=max_eccentricity, caller=caller, message=None)
