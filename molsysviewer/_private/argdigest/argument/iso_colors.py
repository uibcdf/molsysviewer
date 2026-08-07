from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from typing import Sequence

def digest_iso_colors(iso_colors, syntax="MolSysMT", caller=None):
    """ Checks if iso_colors has the correct type (sequence of ints/hex). """

    if iso_colors is None:
        return None

    if isinstance(iso_colors, (Sequence, np.ndarray)) and not isinstance(iso_colors, (str, bytes)):
        try:
            return [int(v) for v in iso_colors]
        except (ValueError, TypeError):
            pass

    raise ArgumentError('iso_colors', value=iso_colors, caller=caller, message="Expected a sequence of integers (colors).")
