from ...exceptions import ArgumentError


def digest_show_normals(show_normals, caller=None):
    """Digest the optional ``show_normals`` flag.

    ``None`` leaves the decision to the shape's own default, so it is passed
    through untouched. Only real booleans are accepted: numbers or strings would
    silently read as truthy.
    """
    if show_normals is None:
        return None

    if isinstance(show_normals, bool):
        return show_normals

    raise ArgumentError("show_normals", value=show_normals, caller=caller, message=None)
