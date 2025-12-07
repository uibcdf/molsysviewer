from ._version import __version__
from .viewer import MolSysView
from .load import load
from . import demo


def __print_version__():
    print("MolSysViewer version " + __version__)


__all__ = [
    "MolSysView",
    "load",
    "demo",
]
