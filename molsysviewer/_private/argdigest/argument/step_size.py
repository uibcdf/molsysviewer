from molsysviewer._private.exceptions import ArgumentError


def digest_step_size(step_size, caller=None):
    if step_size is None:
        return None
    try:
        v = int(step_size)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    raise ArgumentError('step_size', value=step_size, caller=caller, message=None)
