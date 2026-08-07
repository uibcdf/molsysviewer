from ...exceptions import ArgumentError


def digest_faces_pickable(faces_pickable, caller=None):
    """Digest the optional ``faces_pickable`` flag.

    ``None`` leaves the decision to the shape's own default, so it is passed
    through untouched. Only real booleans are accepted: numbers or strings would
    silently read as truthy.
    """
    if faces_pickable is None:
        return None

    if isinstance(faces_pickable, bool):
        return faces_pickable

    raise ArgumentError("faces_pickable", value=faces_pickable, caller=caller, message=None)
