from ...exceptions import ArgumentError


def digest_segments(segments, caller=None):
    """Digest the number of segments used to tessellate a ring.

    ``None`` keeps the shape's default. At least 3 segments are needed to form a
    closed ring, mirroring ``radial_segments``.
    """
    if segments is None:
        return None

    if isinstance(segments, bool):
        raise ArgumentError("segments", value=segments, caller=caller, message=None)

    if isinstance(segments, int) and segments >= 3:
        return segments

    raise ArgumentError("segments", value=segments, caller=caller, message=None)
