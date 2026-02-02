from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysmt import pyunitwizard as puw

def digest_color(color, caller=None):

    if isinstance(color, str):
        if len(color)==7 and color.startswith('#'):
            return color

    if caller is not None and caller.startswith("molsysviewer.") and isinstance(color, int):
        return color

    if isinstance(color, (list, tuple, np.ndarray)):
        if len(color)==3:
            return color

    if isinstance(color, str):
        return color

    raise ArgumentError('color', value=color, caller=caller, message=None)
