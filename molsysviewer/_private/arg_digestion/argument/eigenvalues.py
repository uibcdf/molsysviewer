from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence, Iterable

def digest_eigenvalues(eigenvalues, syntax="MolSysMT", caller=None):
    """ Checks if eigenvalues has the correct type (sequence of (3,) float arrays). """

    if eigenvalues is None:
        return None

    try:
        if isinstance(eigenvalues, (Sequence, np.ndarray, Iterable)) and not isinstance(eigenvalues, (str, bytes)):
            array = np.asarray(eigenvalues, dtype=float)
            if array.ndim == 2 and array.shape[1] == 3:
                return array.tolist()
            if array.ndim == 1 and array.shape[0] == 3:
                # single set of eigenvalues, wrap it
                return [array.tolist()]
    except (ValueError, TypeError):
        pass

    raise ArgumentError('eigenvalues', value=eigenvalues, caller=caller, message="Expected a sequence of 3-component eigenvalues.")
