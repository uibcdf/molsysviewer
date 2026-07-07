"""Reference add-on templates for MolSysViewer extension authors."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from molsysviewer.addons import AddonSpec, GlobalAddonsRegistry
    from molsysviewer.viewer import MolSysView


REFERENCE_ADDON_MODULES: dict[str, str] = {
    "elasnetmt": "molsysviewer.addon_templates.minimal_elasnetmt",
    "minimal_elasnetmt": "molsysviewer.addon_templates.minimal_elasnetmt",
    "dummy": "molsysviewer.addon_templates.dummy_addon",
    "minimal_dummy": "molsysviewer.addon_templates.dummy_addon",
}


def list_reference_addons() -> list[str]:
    """Return the stable short names of bundled reference add-ons."""
    return sorted(name for name in REFERENCE_ADDON_MODULES if not name.startswith("minimal_"))


def resolve_reference_addon(name: str) -> str:
    """Resolve a short reference name or module-like key to its importable module."""
    from molsysviewer.addons import _ensure_non_empty_text

    normalized = _ensure_non_empty_text(name, "name")
    if normalized in REFERENCE_ADDON_MODULES:
        return REFERENCE_ADDON_MODULES[normalized]
    raise ValueError(
        f"Unknown bundled reference add-on {normalized!r}. "
        f"Available references: {', '.join(list_reference_addons())}."
    )


def register_reference_addon(
    name: str,
    *,
    registry: "GlobalAddonsRegistry | None" = None,
) -> "AddonSpec":
    """Register one bundled reference add-on into a registry."""
    from molsysviewer import addons as global_addons

    target = global_addons if registry is None else registry
    return target.register_module(resolve_reference_addon(name))


def register_all_reference_addons(
    *,
    registry: "GlobalAddonsRegistry | None" = None,
) -> list["AddonSpec"]:
    """Register all bundled reference add-ons into a registry."""
    target = registry
    seen: set[str] = set()
    registered: list["AddonSpec"] = []
    for name in list_reference_addons():
        module_name = resolve_reference_addon(name)
        if module_name in seen:
            continue
        seen.add(module_name)
        registered.append(register_reference_addon(name, registry=target))
    return registered


def import_reference_module(name: str):
    """Import the module behind a bundled reference add-on."""
    return import_module(resolve_reference_addon(name))


def register_dummy_addon(
    *,
    registry: "GlobalAddonsRegistry | None" = None,
) -> "AddonSpec":
    """Register the generic dummy/tester add-on into the registry."""
    return register_reference_addon("dummy", registry=registry)


def build_reference_demo_view(
    name: str,
    *,
    demo_key: str = "dialanine",
    registry: "GlobalAddonsRegistry | None" = None,
    expand_workbench: bool = True,
) -> "MolSysView":
    """Build a demo view with one bundled reference add-on already active.

    This is the shortest supported smoke path for downstream teams that want to
    inspect a credible add-on-shaped runtime without writing their own package
    first.
    """
    from molsysviewer import demo

    addon = register_reference_addon(name, registry=registry)
    view = demo[demo_key]
    if expand_workbench:
        view.set_panel_mode(panel="addons", expanded=True, skip_digestion=True)
        workspace = addon.workspaces[0] if len(addon.workspaces) > 0 else None
        if workspace is not None:
            view.set_workspace(workspace.id, skip_digestion=True)
            if isinstance(workspace.entry_panel, str) and workspace.entry_panel.strip() != "":
                view.set_workspace_panel(workspace.entry_panel, workspace=workspace.id, skip_digestion=True)
    return view


__all__ = [
    "REFERENCE_ADDON_MODULES",
    "list_reference_addons",
    "resolve_reference_addon",
    "register_reference_addon",
    "register_dummy_addon",
    "register_all_reference_addons",
    "import_reference_module",
    "build_reference_demo_view",
]
