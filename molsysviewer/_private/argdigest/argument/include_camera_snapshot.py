from ...exceptions import ArgumentError


def digest_include_camera_snapshot(include_camera_snapshot, caller=None):
    if isinstance(include_camera_snapshot, bool):
        return include_camera_snapshot
    raise ArgumentError("include_camera_snapshot", value=include_camera_snapshot, caller=caller)
