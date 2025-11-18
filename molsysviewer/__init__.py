from ._version import __version__

def __print_version__():
    print("MolSysViewer version " + __version__)

from .viewer import MolSysView
from .molsysmt_integration import load

__all__ = [
    "MolSysView",
    "load",
]
