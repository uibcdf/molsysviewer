from ...exceptions import ArgumentError


def digest_include_camera(include_camera, caller=None):
    if isinstance(include_camera, bool):
        return include_camera
    raise ArgumentError("include_camera", value=include_camera, caller=caller)
