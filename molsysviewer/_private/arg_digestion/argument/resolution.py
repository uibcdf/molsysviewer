from ...exceptions import ArgumentError


def digest_resolution(resolution, caller=None):
    if resolution is None:
        return None
    if isinstance(resolution, (int, float)) and not isinstance(resolution, bool):
        return float(resolution)
    raise ArgumentError("resolution", value=resolution, caller=caller, message=None)
