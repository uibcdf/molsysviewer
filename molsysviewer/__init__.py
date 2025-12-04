from ._version import __version__

def __print_version__():
    print("MolSysViewer version " + __version__)

from .regions import Region
from .layers import Layer
from .viewer import MolSysView
from .load import load
from .demo import demo

__all__ = [
    "MolSysView",
    "Region",
    "Layer",
    "load",
    "demo",
]
