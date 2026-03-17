from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence

def digest_iso_levels(iso_levels, syntax="MolSysMT", caller=None):
    """ Checks if iso_levels has the correct type (sequence of floats). """

    if iso_levels is None:
        return None

    if isinstance(iso_levels, (Sequence, np.ndarray)) and not isinstance(iso_levels, (str, bytes)):
        try:
            return [float(v) for v in iso_levels]
        except (ValueError, TypeError):
            pass

    raise ArgumentError('iso_levels', value=iso_levels, caller=caller, message="Expected a sequence of floats.")
