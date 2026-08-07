from ...exceptions import ArgumentError


def digest_draw_faces(draw_faces, caller=None):
    """Digest the optional ``draw_faces`` flag.

    ``None`` leaves the decision to the shape's own default, so it is passed
    through untouched. Only real booleans are accepted: numbers or strings would
    silently read as truthy.
    """
    if draw_faces is None:
        return None

    if isinstance(draw_faces, bool):
        return draw_faces

    raise ArgumentError("draw_faces", value=draw_faces, caller=caller, message=None)
