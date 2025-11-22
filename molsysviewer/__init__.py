from ._version import __version__

def __print_version__():
    print("MolSysViewer version " + __version__)

from .viewer import MolSysView
from .load import load
from .demo import demo

__all__ = [
    "MolSysView",
    "load",
    "demo",
]
