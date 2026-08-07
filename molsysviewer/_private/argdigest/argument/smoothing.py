from ...exceptions import ArgumentError


def digest_smoothing(smoothing, caller=None):
    if smoothing is None:
        return None
    if isinstance(smoothing, (int, float)) and not isinstance(smoothing, bool):
        return float(smoothing)
    raise ArgumentError("smoothing", value=smoothing, caller=caller, message=None)
