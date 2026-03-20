from smonitor.integrations import ensure_configured as _ensure_smonitor_configured
from depdigest import check_dependency as _check_dependency

from ._private.smonitor import PACKAGE_ROOT as _SMONITOR_PACKAGE_ROOT

_ensure_smonitor_configured(_SMONITOR_PACKAGE_ROOT)
_check_dependency(__name__)

from ._pyunitwizard import puw as pyunitwizard
from ._version import __version__
from .demo import demo
from .new_view import new_view
from . import tools
from .addons import (
    addons,
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonStyleHelperSpec,
    AddonToolModeSpec,
    AddonWorkbenchSectionSpec,
)
from .styles import Style
from .viewer import MolSysView


def __print_version__():
    print("MolSysViewer version " + __version__)


__all__ = [
    "MolSysView",
    "new_view",
    "demo",
    "tools",
    "addons",
    "Style",
    "AddonSpec",
    "AddonPanelSpec",
    "AddonContextActionSpec",
    "AddonWorkbenchSectionSpec",
    "AddonShapeProviderSpec",
    "AddonStyleHelperSpec",
    "AddonExportHelperSpec",
    "AddonToolModeSpec",
]
