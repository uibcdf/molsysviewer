import numpy as np
from molsysmt import pyunitwizard as puw
from ...exceptions import ArgumentError

def digest_radius(radius, caller=None):

    if puw.is_quantity(radius):
        if puw.check(radius, dimensionality={'[L]':1}):
            return puw.standardize(radius)
    if caller is not None and caller.startswith("molsysviewer.") and isinstance(radius, (int, float)):
        return float(radius)

    raise ArgumentError('radius', value=radius, caller=caller, message=None)
