"""Reference add-on templates for MolSysViewer extension authors."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from molsysviewer.addons import AddonSpec, GlobalAddonsRegistry


REFERENCE_ADDON_MODULES: dict[str, str] = {
    "topomt": "molsysviewer.addon_templates.minimal_topomt",
    "minimal_topomt": "molsysviewer.addon_templates.minimal_topomt",
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


__all__ = [
    "REFERENCE_ADDON_MODULES",
    "list_reference_addons",
    "resolve_reference_addon",
    "register_reference_addon",
    "register_all_reference_addons",
    "import_reference_module",
]
