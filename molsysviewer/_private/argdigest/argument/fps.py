from molsysviewer._private.exceptions import ArgumentError


def digest_fps(fps, caller=None):
    if fps is None:
        return None
    try:
        v = int(fps)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    raise ArgumentError('fps', value=fps, caller=caller, message=None)
