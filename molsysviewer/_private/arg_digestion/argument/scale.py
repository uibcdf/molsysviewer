from molsysviewer._private.exceptions import ArgumentError


def digest_scale(scale, caller=None):
    if scale is None:
        return None
    if isinstance(scale, bool):
        raise ArgumentError("scale", value=scale, caller=caller, message=None)
    if isinstance(scale, (int, float)):
        value = float(scale)
        if value > 0:
            return value
    raise ArgumentError("scale", value=scale, caller=caller, message=None)
