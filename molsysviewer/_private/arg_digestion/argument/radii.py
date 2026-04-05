from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_radii(radii, caller=None):
    if radii is None:
        return None
    if puw.is_quantity(radii):
        if puw.check(radii, dimensionality={'[L]': 1}):
            return puw.standardize(radii)
        raise ArgumentError('radii', value=radii, caller=caller)
    if isinstance(radii, (int, float, np.number)):
        return float(radii)
    try:
        arr = np.asarray(radii, dtype=float)
        if arr.ndim == 1:
            return arr
    except Exception:
        pass
    raise ArgumentError('radii', value=radii, caller=caller)
