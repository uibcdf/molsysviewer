from molsysviewer._private.exceptions import ArgumentError
import numpy as np

def digest_step(step, caller=None):

    # Optional wherever it defaults to None (playback step size, for instance);
    # the callee applies its own default.
    if step is None:
        return None

    if isinstance(step, bool):
        raise ArgumentError('step', value=step, caller=caller, message=None)

    if isinstance(step, int):
        return step

    raise ArgumentError('step', value=step, caller=caller, message=None)

