from ...exceptions import ArgumentError


def digest_wireframe_size(wireframe_size, caller=None):
    if wireframe_size is None:
        return None
    if isinstance(wireframe_size, (int, float)) and not isinstance(wireframe_size, bool) and wireframe_size > 0.0:
        return float(wireframe_size)
    raise ArgumentError("wireframe_size", value=wireframe_size, caller=caller, message=None)
