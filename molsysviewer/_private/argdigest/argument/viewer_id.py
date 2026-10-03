from ...exceptions import ArgumentError


def digest_viewer_id(viewer_id, caller=None):
    if isinstance(viewer_id, str) and viewer_id.strip():
        return viewer_id
    raise ArgumentError("viewer_id", value=viewer_id, caller=caller)
