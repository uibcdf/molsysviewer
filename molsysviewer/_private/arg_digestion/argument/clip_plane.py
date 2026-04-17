from ...exceptions import ArgumentError


def digest_clip_plane(clip_plane, caller=None):
    if clip_plane is None:
        return None
    if not isinstance(clip_plane, dict):
        raise ArgumentError("clip_plane", value=clip_plane, caller=caller, message=None)

    point = clip_plane.get("point")
    normal = clip_plane.get("normal")
    if not isinstance(point, (list, tuple)) or len(point) != 3:
        raise ArgumentError("clip_plane", value=clip_plane, caller=caller, message=None)
    if not isinstance(normal, (list, tuple)) or len(normal) != 3:
        raise ArgumentError("clip_plane", value=clip_plane, caller=caller, message=None)
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in point):
        raise ArgumentError("clip_plane", value=clip_plane, caller=caller, message=None)
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in normal):
        raise ArgumentError("clip_plane", value=clip_plane, caller=caller, message=None)

    return {
        "point": [float(item) for item in point],
        "normal": [float(item) for item in normal],
    }
