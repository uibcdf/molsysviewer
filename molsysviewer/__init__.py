from ._version import __version__

def __print_version__():
    print("MolSysViewer version " + __version__)

from .viewer import MolSysView
from .load import load

__all__ = [
    "MolSysView",
    "load",
]
