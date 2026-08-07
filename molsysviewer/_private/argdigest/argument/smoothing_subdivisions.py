from ...exceptions import ArgumentError


def digest_smoothing_subdivisions(smoothing_subdivisions, caller=None):
    if smoothing_subdivisions is None:
        return None
    if isinstance(smoothing_subdivisions, int) and not isinstance(smoothing_subdivisions, bool):
        return smoothing_subdivisions
    raise ArgumentError("smoothing_subdivisions", value=smoothing_subdivisions, caller=caller, message=None)
