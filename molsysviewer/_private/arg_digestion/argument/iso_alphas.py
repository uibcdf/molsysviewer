from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence

def digest_iso_alphas(iso_alphas, syntax="MolSysMT", caller=None):
    """ Checks if iso_alphas has the correct type (sequence of floats 0.0-1.0). """

    if iso_alphas is None:
        return None

    if isinstance(iso_alphas, (Sequence, np.ndarray)) and not isinstance(iso_alphas, (str, bytes)):
        try:
            alphas = [float(v) for v in iso_alphas]
            if all(0.0 <= a <= 1.0 for a in alphas):
                return alphas
        except (ValueError, TypeError):
            pass

    raise ArgumentError('iso_alphas', value=iso_alphas, caller=caller, message="Expected a sequence of floats between 0.0 and 1.0.")
