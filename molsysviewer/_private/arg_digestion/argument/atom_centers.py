from ..exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_atom_centers(atom_centers, caller=None):
    if atom_centers is None:
        return None
    if puw.is_quantity(atom_centers):
        if puw.check(atom_centers, dimensionality={'[L]': 1}):
            return puw.standardize(atom_centers)
        raise ArgumentError('atom_centers', value=atom_centers, caller=caller)
    try:
        arr = np.asarray(atom_centers, dtype=float)
        if arr.ndim == 2 and arr.shape[1] == 3:
            return arr
    except Exception:
        pass
    raise ArgumentError('atom_centers', value=atom_centers, caller=caller)
