from molsysviewer._private.exceptions import ArgumentError
import numpy as np

def digest_radii(radii, caller=None):
    if radii is None:
        return None
    if isinstance(radii, (int, float, np.number)):
        return float(radii)
    try:
        arr = np.asarray(radii, dtype=float)
        if arr.ndim == 1:
            return arr
    except Exception:
        pass
    raise ArgumentError('radii', value=radii, caller=caller)
