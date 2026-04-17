import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

def digest_width(width, caller=None):

    if isinstance(width, bool):
        raise ArgumentError('width', value=width, caller=caller, message=None)
    if isinstance(width, (int, float)):
        return float(width)
    if puw.is_quantity(width):
        if puw.check(width, dimensionality={'[L]':1}):
            return puw.standardize(width)

    raise ArgumentError('width', value=width, caller=caller, message=None)

