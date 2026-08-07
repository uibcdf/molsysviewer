from ...exceptions import ArgumentError


def digest_radial_segments(radial_segments, caller=None):
    if radial_segments is None:
        return None
    if isinstance(radial_segments, int) and radial_segments >= 3:
        return radial_segments
    raise ArgumentError("radial_segments", value=radial_segments, caller=caller, message=None)
