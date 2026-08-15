from __future__ import annotations

import importlib
import sys
from types import ModuleType

from depdigest import check_dependency as _check_dependency
from smonitor.integrations import ensure_configured as _ensure_smonitor_configured

from ._private.smonitor import PACKAGE_ROOT as _SMONITOR_PACKAGE_ROOT
from ._version import __version__


_ensure_smonitor_configured(_SMONITOR_PACKAGE_ROOT)
if not getattr(sys.modules.get(__name__), "_checked_dep", False):
    _check_dependency(__name__)
    try:
        sys.modules[__name__]._checked_dep = True
    except AttributeError:
        pass


_LAZY_ATTRIBUTES = {
    "pyunitwizard": ("._pyunitwizard", "puw"),
    "config": ".config",
    "demo": (".demo", "demo"),
    "systems": (".systems", "systems"),
    "new_view": (".new_view", "new_view"),
    "tools": ".tools",
    "addon_templates": ".addon_templates",
    "shape_adapters": ".shape_adapters",
    "Style": (".styles", "Style"),
    "FigureSpec": (".figures", "FigureSpec"),
    "MolSysView": (".viewer", "MolSysView"),
    "ViewerInfo": (".viewer", "ViewerInfo"),
}

for _name in (
    "addons",
    "AddonContextActionSpec",
    "AddonExportHelperSpec",
    "AddonLifecycleSpec",
    "AddonPanelSpec",
    "AddonPanelWidget",
    "AddonShapeProviderSpec",
    "AddonSpec",
    "AddonStyleHelperSpec",
    "AddonToolModeSpec",
    "AddonSectionSpec",
    "AddonWorkspaceSpec",
    "AddonWorkbenchSectionSpec",
):
    _LAZY_ATTRIBUTES[_name] = (".addons", _name)

for _name in (
    "MESH_LOCAL",
    "MOLECULAR_SYSTEM",
    "VIEWER_LOCAL",
    "EntityRef",
    "PointGeometry",
    "SphereGeometry",
    "SegmentGeometry",
    "TetrahedraGeometry",
    "IndexedTriangleGeometry",
    "IndexedEdgeGeometry",
    "entity_ref_payload",
):
    _LAZY_ATTRIBUTES[_name] = (".geometry", _name)

for _name in (
    "ColorRegistry",
    "ContinuousPalette",
    "CategoricalColorScheme",
    "colors",
    "normalize_color",
    "normalize_colors",
    "scalar_to_color_list",
    "expand_values_to_atoms",
):
    _LAZY_ATTRIBUTES[_name] = (".colors", _name)


def _materialize(name: str):
    target = _LAZY_ATTRIBUTES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if isinstance(target, str):
        value = importlib.import_module(target, __name__)
    else:
        module_name, attribute_name = target
        module = importlib.import_module(module_name, __name__)
        if module_name == ".addons":
            module.addons.discover(include_known_modules=True)
            for public_name, public_target in _LAZY_ATTRIBUTES.items():
                if isinstance(public_target, tuple) and public_target[0] == ".addons":
                    globals()[public_name] = getattr(module, public_target[1])
        value = getattr(module, attribute_name)
    if name in {"MolSysView", "demo", "new_view"}:
        addons_module = importlib.import_module(".addons", __name__)
        addons_module.addons.discover(include_known_modules=True)
        globals()["addons"] = addons_module.addons
    globals()[name] = value
    return value


def __getattr__(name: str):
    return _materialize(name)


class _LazyPackageModule(ModuleType):
    def __getattribute__(self, name: str):
        lazy = ModuleType.__getattribute__(self, "__dict__").get("_LAZY_ATTRIBUTES", {})
        target = lazy.get(name)
        current = ModuleType.__getattribute__(self, "__dict__").get(name)
        if isinstance(current, ModuleType) and isinstance(target, tuple):
            return _materialize(name)
        return ModuleType.__getattribute__(self, name)


def __dir__():
    return sorted(set(globals()) | set(_LAZY_ATTRIBUTES))


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
    "entity_ref_payload",
    "IndexedEdgeGeometry",
    "IndexedTriangleGeometry",
    "TetrahedraGeometry",
    "SegmentGeometry",
    "SphereGeometry",
    "PointGeometry",
    "EntityRef",
    "VIEWER_LOCAL",
    "MOLECULAR_SYSTEM",
    "MESH_LOCAL",
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
    "AddonSectionSpec",
    "AddonShapeProviderSpec",
    "AddonStyleHelperSpec",
    "AddonExportHelperSpec",
    "AddonToolModeSpec",
    "AddonLifecycleSpec",
    "AddonPanelWidget",
    "config",
    "AddonWorkbenchSectionSpec",
]


sys.modules[__name__].__class__ = _LazyPackageModule


# The unit policy is declared when this package is imported, not on first use.
# Reaching it lazily meant `puw.configure.report()` described an empty session
# until something happened to touch it, and a user calling PyUnitWizard
# directly after importing this package got NoStandardsError. The cost is paid
# once per process -- a second suite library costs about 2 ms -- and it is a
# cost the session pays anyway at its first unit operation.
from . import _pyunitwizard  # noqa: E402,F401
