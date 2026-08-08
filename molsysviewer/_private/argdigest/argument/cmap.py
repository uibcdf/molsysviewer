from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_cmap(cmap, caller=None):

    # Imported here, not at module level: ArgDigest loads every digester in this
    # package when it initializes, so a top-level import made any digested call pay
    # for a heavy library that most calls never need.
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.pyplot import colormaps

    if cmap is None:
        return None

    if isinstance(cmap, str):
        if cmap in colormaps:
            return colormaps[cmap]

    if isinstance(cmap, LinearSegmentedColormap):
        return cmap

    raise ArgumentError('cmap', value=cmap, caller=caller, message=None)
