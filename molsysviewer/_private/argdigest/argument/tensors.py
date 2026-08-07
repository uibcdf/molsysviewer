from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence, Iterable

def digest_tensors(tensors, syntax="MolSysMT", caller=None):
    """ Checks if tensors has the correct type (sequence of 3x3 float matrices). """

    if tensors is None:
        return None

    try:
        if isinstance(tensors, (Sequence, np.ndarray, Iterable)) and not isinstance(tensors, (str, bytes)):
            array = np.asarray(tensors, dtype=float)
            if array.ndim == 3 and array.shape[1] == 3 and array.shape[2] == 3:
                return array.tolist()
            if array.ndim == 2 and array.shape == (3, 3):
                return [array.tolist()]
    except (ValueError, TypeError):
        pass

    raise ArgumentError('tensors', value=tensors, caller=caller, message="Expected a sequence of 3x3 tensors.")
