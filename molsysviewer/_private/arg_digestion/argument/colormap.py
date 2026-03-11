from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw
from matplotlib.pyplot import colormaps
from matplotlib.colors import LinearSegmentedColormap

def digest_colormap(colormap, caller=None):

    if colormap is None:
        return None

    if isinstance(colormap, str):
        if colormap in colormaps:
            return colormaps[colormap]

    if isinstance(colormap, LinearSegmentedColormap):
        return colormap

    raise ArgumentError('colormap', value=colormap, caller=caller, message=None)
