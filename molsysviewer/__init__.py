from ._version import __version__
from ._pyunitwizard import puw as pyunitwizard
from .viewer import MolSysView
from .new_view import new_view
from .demo import demo


def __print_version__():
    print("MolSysViewer version " + __version__)


__all__ = [
    "MolSysView",
    "new_view",
    "demo",
]
