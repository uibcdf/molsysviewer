from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence, Iterable

def digest_eigenvectors(eigenvectors, syntax="MolSysMT", caller=None):
    """ Checks if eigenvectors has the correct type (sequence of 3x3 float matrices). """

    if eigenvectors is None:
        return None

    try:
        if isinstance(eigenvectors, (Sequence, np.ndarray, Iterable)) and not isinstance(eigenvectors, (str, bytes)):
            array = np.asarray(eigenvectors, dtype=float)
            # Should be (N, 3, 3) where each 3x3 are the 3 eigenvectors
            if array.ndim == 3 and array.shape[1] == 3 and array.shape[2] == 3:
                return array.tolist()
            if array.ndim == 2 and array.shape == (3, 3):
                # single matrix, wrap it
                return [array.tolist()]
    except (ValueError, TypeError):
        pass

    raise ArgumentError('eigenvectors', value=eigenvectors, caller=caller, message="Expected a sequence of 3x3 eigenvector matrices.")
