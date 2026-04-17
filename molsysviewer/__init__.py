from smonitor.integrations import ensure_configured as _ensure_smonitor_configured
from depdigest import check_dependency as _check_dependency

from ._private.smonitor import PACKAGE_ROOT as _SMONITOR_PACKAGE_ROOT

_ensure_smonitor_configured(_SMONITOR_PACKAGE_ROOT)
_check_dependency(__name__)

from ._pyunitwizard import puw as pyunitwizard
from ._version import __version__
from .demo import demo
from .systems import systems
from .new_view import new_view
from . import tools
from . import addon_templates
from .addons import (
    addons,
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonLifecycleSpec,
    AddonPanelSpec,
    AddonPanelWidget,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonStyleHelperSpec,
    AddonToolModeSpec,
    AddonWorkbenchSectionSpec,
    AddonWorkspaceSpec,
)
from .styles import Style
from .figures import FigureSpec
from .viewer import MolSysView, ViewerInfo
from .colors import (
    ColorRegistry,
    ContinuousPalette,
    CategoricalColorScheme,
    colors,
    normalize_color,
    normalize_colors,
    scalar_to_color_list,
    expand_values_to_atoms,
)


def __print_version__():
    print("MolSysViewer version " + __version__)


def build_standalone0_html(*args, **kwargs):
    from .standalone import build_standalone0_html as _build_standalone0_html

    return _build_standalone0_html(*args, **kwargs)


def launch_standalone0(*args, **kwargs):
    from .standalone import launch_standalone0 as _launch_standalone0

    return _launch_standalone0(*args, **kwargs)


def create_standalone_qt0_window(*args, **kwargs):
    from .standalone_qt import create_standalone_qt0_window as _create_standalone_qt0_window

    return _create_standalone_qt0_window(*args, **kwargs)


def launch_standalone_qt0(*args, **kwargs):
    from .standalone_qt import launch_standalone_qt0 as _launch_standalone_qt0

    return _launch_standalone_qt0(*args, **kwargs)


addons.discover()

__all__ = [
    "MolSysView",
    "ViewerInfo",
    "new_view",
    "demo",
    "systems",
    "tools",
    "addon_templates",
    "addons",
    "Style",
    "FigureSpec",
    "colors",
    "normalize_color",
    "normalize_colors",
    "scalar_to_color_list",
    "expand_values_to_atoms",
    "ColorRegistry",
    "ContinuousPalette",
    "CategoricalColorScheme",
    "build_standalone0_html",
    "launch_standalone0",
    "create_standalone_qt0_window",
    "launch_standalone_qt0",
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
    "AddonPanelWidget",
]
