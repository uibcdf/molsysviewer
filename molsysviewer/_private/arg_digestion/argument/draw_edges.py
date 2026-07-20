from ...exceptions import ArgumentError


def digest_draw_edges(draw_edges, caller=None):
    """Digest the optional ``draw_edges`` flag.

    ``None`` leaves the decision to the shape's own default, so it is passed
    through untouched. Only real booleans are accepted: numbers or strings would
    silently read as truthy.
    """
    if draw_edges is None:
        return None

    if isinstance(draw_edges, bool):
        return draw_edges

    raise ArgumentError("draw_edges", value=draw_edges, caller=caller, message=None)
