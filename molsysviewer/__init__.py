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
from . import addon_templates
from .addons import (
    addons,
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonLifecycleSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonStyleHelperSpec,
    AddonToolModeSpec,
    AddonWorkbenchSectionSpec,
    AddonWorkspaceSpec,
)
from .styles import Style
from .figures import FigureSpec
from .viewer import MolSysView


def __print_version__():
    print("MolSysViewer version " + __version__)


def build_standalone0_html(*args, **kwargs):
    from .standalone import build_standalone0_html as _build_standalone0_html

    return _build_standalone0_html(*args, **kwargs)


def launch_standalone0(*args, **kwargs):
    from .standalone import launch_standalone0 as _launch_standalone0

    return _launch_standalone0(*args, **kwargs)


__all__ = [
    "MolSysView",
    "new_view",
    "demo",
    "tools",
    "addon_templates",
    "addons",
    "Style",
    "FigureSpec",
    "build_standalone0_html",
    "launch_standalone0",
    "AddonSpec",
    "AddonWorkspaceSpec",
    "AddonPanelSpec",
    "AddonContextActionSpec",
    "AddonWorkbenchSectionSpec",
    "AddonShapeProviderSpec",
    "AddonStyleHelperSpec",
    "AddonExportHelperSpec",
    "AddonToolModeSpec",
    "AddonLifecycleSpec",
]
