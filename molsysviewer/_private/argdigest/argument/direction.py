import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

# Playback entry points, where `direction` is a travel sense along the
# structures rather than a 3D vector. `MolSysView.play()` normalizes to
# `molsysviewer.viewer.play`, which the player-only prefix did not cover, so the
# public call fell through to the vector branch and was rejected.
_PLAYBACK_CALLERS = {
    "molsysviewer.viewer.play",
    "molsysviewer.viewer.MolSysView.play",
}


def digest_direction(direction, caller=None):

    caller = normalize_viewer_caller(caller)

    if caller is not None and (caller.startswith("molsysviewer.player.") or caller in _PLAYBACK_CALLERS):
        if direction is None:
            return None
        if isinstance(direction, str) and direction in ("forward", "backward"):
            return direction
        raise ArgumentError('direction', value=direction, caller=caller, message=None)

    if isinstance(caller, str) and caller.endswith('move_away'):
        if direction is None:
            return direction

    if isinstance(direction, (list, tuple)):
        direction = np.array(direction, dtype=np.float64)

    if isinstance(direction, np.ndarray):
        if (len(direction.shape)==1) and (direction.shape[0]==3):
            direction = np.array(direction).reshape(1, 3)
            direction = direction.astype(np.float64)
            direction[0] = direction[0]/np.linalg.norm(direction[0])
            return direction
        if (len(direction.shape)==2) and (direction.shape[1]==3): # structure_index, xyz
            direction = direction.astype(np.float64)
            for ii in range(len(direction.shape[0])):
                direction[ii] = direction[ii]/np.linalg.norm(direction[ii])
            return direction

    raise ArgumentError('direction', value=direction, caller=caller, message=None)

