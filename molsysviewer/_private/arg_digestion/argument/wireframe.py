from ...exceptions import ArgumentError


def digest_wireframe(wireframe, caller=None):
    if isinstance(wireframe, bool):
        return wireframe
    raise ArgumentError("wireframe", value=wireframe, caller=caller, message=None)
