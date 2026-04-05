from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_centers(centers, caller=None):
    if centers is None:
        return None
    if puw.is_quantity(centers):
        if puw.check(centers, dimensionality={'[L]': 1}):
            return puw.standardize(centers)
        raise ArgumentError('centers', value=centers, caller=caller)
    try:
        arr = np.asarray(centers, dtype=float)
        if arr.ndim == 1 and arr.shape[0] == 3:
            return arr.reshape(1, 3)
        if arr.ndim == 2 and arr.shape[1] == 3:
            return arr
    except Exception:
        pass
    raise ArgumentError('centers', value=centers, caller=caller)
