from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_values(values, caller=None):

    if values is None:
        return values

    if isinstance(values, (list, tuple, range, np.ndarray)):
        return values

    if puw.is_quantity(values):
        return puw.get_value(values)

    raise ArgumentError('values', value=values, caller=caller, message=None)

