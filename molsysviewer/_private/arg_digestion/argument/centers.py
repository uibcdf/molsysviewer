from molsysviewer._private.exceptions import ArgumentError
import numpy as np

def digest_centers(centers, caller=None):
    if centers is None:
        return None
    try:
        arr = np.asarray(centers, dtype=float)
        if arr.ndim == 1 and arr.shape[0] == 3:
            return arr.reshape(1, 3)
        if arr.ndim == 2 and arr.shape[1] == 3:
            return arr
    except Exception:
        pass
    raise ArgumentError('centers', value=centers, caller=caller)
