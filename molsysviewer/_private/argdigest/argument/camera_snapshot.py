from ...exceptions import ArgumentError


def digest_camera_snapshot(camera_snapshot, caller=None):
    if camera_snapshot is None:
        return None
    if isinstance(camera_snapshot, dict):
        return dict(camera_snapshot)
    raise ArgumentError("camera_snapshot", value=camera_snapshot, caller=caller, message=None)
