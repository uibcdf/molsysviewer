from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from types import ModuleType
from collections.abc import Callable
from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest
from .config.project_config import load_project_config


def _ensure_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _normalize_tuple(values: tuple[str, ...] | list[str] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (tuple, list)):
        raise ValueError(f"{field_name} must be a tuple/list of strings.")
    normalized: list[str] = []
    for value in values:
        normalized.append(_ensure_non_empty_text(value, field_name))
    return tuple(normalized)


def _normalize_meta(meta: dict[str, Any] | None, field_name: str = "meta") -> dict[str, Any]:
    if meta is None:
        return {}
    if not isinstance(meta, dict):
        raise ValueError(f"{field_name} must be a dictionary.")
    return dict(meta)


def _coerce_callback(candidate: Any, field_name: str) -> Callable[[Any], None] | None:
    if candidate is None:
        return None
    if not callable(candidate):
        raise ValueError(f"{field_name} must be callable when provided.")
    return candidate


@dataclass(frozen=True)
class AddonWorkspaceSpec:
    id: str
    title: str
    entry_panel: str | None = None
    description: str | None = None
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonWorkspaceSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonWorkspaceSpec.title"))
        if self.entry_panel is not None:
            object.__setattr__(self, "entry_panel", _ensure_non_empty_text(self.entry_panel, "AddonWorkspaceSpec.entry_panel"))
        if self.description is not None:
            object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry_panel": self.entry_panel,
            "description": self.description,
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonPanelSpec:
    id: str
    title: str
    entry: str | None = None
    description: str | None = None
    order: int = 0
    target: str = "panel_mode"
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonPanelSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonPanelSpec.title"))
        if self.entry is not None:
            object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonPanelSpec.entry"))
        if self.description is not None:
            object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "target", _ensure_non_empty_text(self.target, "AddonPanelSpec.target"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "description": self.description,
            "order": self.order,
            "target": self.target,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonContextActionSpec:
    id: str
    title: str
    entry: str
    target_kinds: tuple[str, ...] = field(default_factory=tuple)
    group: str | None = None
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonContextActionSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonContextActionSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonContextActionSpec.entry"))
        if self.group is not None:
            object.__setattr__(self, "group", self.group.strip())
        object.__setattr__(self, "target_kinds", _normalize_tuple(self.target_kinds, "AddonContextActionSpec.target_kinds"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "target_kinds": list(self.target_kinds),
            "group": self.group,
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonWorkbenchSectionSpec:
    id: str
    title: str
    entry: str
    target_panel: str = "workbench"
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonWorkbenchSectionSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonWorkbenchSectionSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonWorkbenchSectionSpec.entry"))
        object.__setattr__(self, "target_panel", _ensure_non_empty_text(self.target_panel, "AddonWorkbenchSectionSpec.target_panel"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "target_panel": self.target_panel,
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonShapeProviderSpec:
    id: str
    title: str
    entry: str
    kinds: tuple[str, ...] = field(default_factory=tuple)
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonShapeProviderSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonShapeProviderSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonShapeProviderSpec.entry"))
        object.__setattr__(self, "kinds", _normalize_tuple(self.kinds, "AddonShapeProviderSpec.kinds"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "kinds": list(self.kinds),
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonStyleHelperSpec:
    id: str
    title: str
    entry: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonStyleHelperSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonStyleHelperSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonStyleHelperSpec.entry"))
        object.__setattr__(self, "tags", _normalize_tuple(self.tags, "AddonStyleHelperSpec.tags"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "tags": list(self.tags),
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonExportHelperSpec:
    id: str
    title: str
    entry: str
    formats: tuple[str, ...] = field(default_factory=tuple)
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonExportHelperSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonExportHelperSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonExportHelperSpec.entry"))
        object.__setattr__(self, "formats", _normalize_tuple(self.formats, "AddonExportHelperSpec.formats"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "formats": list(self.formats),
            "order": self.order,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class AddonToolModeSpec:
    id: str
    title: str
    entry: str
    order: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _ensure_non_empty_text(self.id, "AddonToolModeSpec.id"))
        object.__setattr__(self, "title", _ensure_non_empty_text(self.title, "AddonToolModeSpec.title"))
        object.__setattr__(self, "entry", _ensure_non_empty_text(self.entry, "AddonToolModeSpec.entry"))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))

    def info(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry": self.entry,
            "order": self.order,
            "meta": dict(self.meta),
        }


def _validate_unique_ids(items: tuple[Any, ...], label: str) -> None:
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} must not contain duplicate contribution ids.")


KNOWN_ADDON_MODULES: tuple[str, ...] = (
    "molsysviewer_topomt",
    "molsysviewer_pharmacophoremt",
    "molsysviewer_elasnetmt",
)


@dataclass(frozen=True)
class AddonLifecycleSpec:
    on_enable: Callable[[Any], None] | None = None
    on_disable: Callable[[Any], None] | None = None
    on_context_action: Callable[[Any, str, dict[str, Any]], None] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "on_enable", _coerce_callback(self.on_enable, "AddonLifecycleSpec.on_enable"))
        object.__setattr__(self, "on_disable", _coerce_callback(self.on_disable, "AddonLifecycleSpec.on_disable"))
        object.__setattr__(
            self,
            "on_context_action",
            _coerce_callback(self.on_context_action, "AddonLifecycleSpec.on_context_action"),
        )

    def info(self) -> dict[str, bool]:
        return {
            "has_on_enable": self.on_enable is not None,
            "has_on_disable": self.on_disable is not None,
            "has_on_context_action": self.on_context_action is not None,
        }


def _coerce_addon_spec(candidate: Any, source_name: str) -> AddonSpec:
    if isinstance(candidate, AddonSpec):
        return candidate
    if callable(candidate):
        produced = candidate()
        if isinstance(produced, AddonSpec):
            return produced
    raise ValueError(
        f"{source_name} did not expose a valid add-on contract. "
        "Expected `addon`, `ADDON`, or `get_addon()` producing an AddonSpec."
    )


def _load_addon_spec_from_module(module: ModuleType) -> AddonSpec:
    module_name = getattr(module, "__name__", "<unknown module>")
    if hasattr(module, "addon"):
        return _coerce_addon_spec(getattr(module, "addon"), f"{module_name}.addon")
    if hasattr(module, "ADDON"):
        return _coerce_addon_spec(getattr(module, "ADDON"), f"{module_name}.ADDON")
    if hasattr(module, "get_addon"):
        return _coerce_addon_spec(getattr(module, "get_addon"), f"{module_name}.get_addon")
    raise ValueError(
        f"{module_name} does not expose a valid add-on contract. "
        "Expected `addon`, `ADDON`, or `get_addon()`."
    )


def _load_addon_lifecycle_from_module(module: ModuleType) -> AddonLifecycleSpec | None:
    lifecycle = None
    if hasattr(module, "lifecycle"):
        lifecycle = getattr(module, "lifecycle")
    elif hasattr(module, "LIFECYCLE"):
        lifecycle = getattr(module, "LIFECYCLE")

    if isinstance(lifecycle, AddonLifecycleSpec):
        return lifecycle

    on_enable = getattr(module, "on_enable", None)
    on_disable = getattr(module, "on_disable", None)
    on_context_action = getattr(module, "on_context_action", None)
    if lifecycle is None and on_enable is None and on_disable is None and on_context_action is None:
        return None

    if lifecycle is not None and not isinstance(lifecycle, AddonLifecycleSpec):
        raise ValueError(
            f"{getattr(module, '__name__', '<unknown module>')} lifecycle must be an AddonLifecycleSpec."
        )

    if lifecycle is not None:
        return lifecycle
    return AddonLifecycleSpec(
        on_enable=on_enable,
        on_disable=on_disable,
        on_context_action=on_context_action,
    )


@dataclass(frozen=True)
class AddonSpec:
    name: str
    package: str | None = None
    version: str | None = None
    description: str | None = None
    workspaces: tuple[AddonWorkspaceSpec, ...] = field(default_factory=tuple)
    panels: tuple[AddonPanelSpec, ...] = field(default_factory=tuple)
    context_actions: tuple[AddonContextActionSpec, ...] = field(default_factory=tuple)
    workbench_sections: tuple[AddonWorkbenchSectionSpec, ...] = field(default_factory=tuple)
    shape_providers: tuple[AddonShapeProviderSpec, ...] = field(default_factory=tuple)
    style_helpers: tuple[AddonStyleHelperSpec, ...] = field(default_factory=tuple)
    export_helpers: tuple[AddonExportHelperSpec, ...] = field(default_factory=tuple)
    tool_modes: tuple[AddonToolModeSpec, ...] = field(default_factory=tuple)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _ensure_non_empty_text(self.name, "AddonSpec.name"))
        if self.package is not None:
            object.__setattr__(self, "package", _ensure_non_empty_text(self.package, "AddonSpec.package"))
        if self.version is not None:
            object.__setattr__(self, "version", _ensure_non_empty_text(self.version, "AddonSpec.version"))
        if self.description is not None:
            object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "workspaces", tuple(self.workspaces))
        object.__setattr__(self, "panels", tuple(self.panels))
        object.__setattr__(self, "context_actions", tuple(self.context_actions))
        object.__setattr__(self, "workbench_sections", tuple(self.workbench_sections))
        object.__setattr__(self, "shape_providers", tuple(self.shape_providers))
        object.__setattr__(self, "style_helpers", tuple(self.style_helpers))
        object.__setattr__(self, "export_helpers", tuple(self.export_helpers))
        object.__setattr__(self, "tool_modes", tuple(self.tool_modes))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))
        _validate_unique_ids(self.workspaces, "AddonSpec.workspaces")
        _validate_unique_ids(self.panels, "AddonSpec.panels")
        _validate_unique_ids(self.context_actions, "AddonSpec.context_actions")
        _validate_unique_ids(self.workbench_sections, "AddonSpec.workbench_sections")
        _validate_unique_ids(self.shape_providers, "AddonSpec.shape_providers")
        _validate_unique_ids(self.style_helpers, "AddonSpec.style_helpers")
        _validate_unique_ids(self.export_helpers, "AddonSpec.export_helpers")
        _validate_unique_ids(self.tool_modes, "AddonSpec.tool_modes")

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "package": self.package,
            "version": self.version,
            "description": self.description,
            "workspaces": [item.info() for item in self.workspaces],
            "panels": [item.info() for item in self.panels],
            "context_actions": [item.info() for item in self.context_actions],
            "workbench_sections": [item.info() for item in self.workbench_sections],
            "shape_providers": [item.info() for item in self.shape_providers],
            "style_helpers": [item.info() for item in self.style_helpers],
            "export_helpers": [item.info() for item in self.export_helpers],
            "tool_modes": [item.info() for item in self.tool_modes],
            "meta": dict(self.meta),
        }


class _AddonAggregationMixin:
    def _iter_effective_addons(self) -> list[tuple[str, AddonSpec]]:
        raise NotImplementedError

    def _aggregate(self, attr: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for addon_name, addon in self._iter_effective_addons():
            for item in getattr(addon, attr):
                record = item.info()
                record["addon"] = addon_name
                records.append(record)
        records.sort(key=lambda item: (int(item.get("order", 0)), str(item.get("addon", "")), str(item.get("id", ""))))
        return records

    @signal(tags=["addon", "panel"])
    @digest()
    def workspace_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("workspaces")

    @signal(tags=["addon", "panel"])
    @digest()
    def panel_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("panels")

    @signal(tags=["addon", "context"])
    @digest()
    def context_action_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("context_actions")

    @signal(tags=["addon", "workbench"])
    @digest()
    def workbench_section_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("workbench_sections")

    @signal(tags=["addon", "shape"])
    @digest()
    def shape_provider_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("shape_providers")

    @signal(tags=["addon", "style"])
    @digest()
    def style_helper_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("style_helpers")

    @signal(tags=["addon", "export"])
    @digest()
    def export_helper_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("export_helpers")

    @signal(tags=["addon", "tool"])
    @digest()
    def tool_mode_specs(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        return self._aggregate("tool_modes")


class GlobalAddonsRegistry(_AddonAggregationMixin):
    """Host-level add-on registry shared by all MolSysViewer views."""

    def __init__(self) -> None:
        self._registry: dict[str, AddonSpec] = {}
        self._enabled: set[str] = set()
        self._module_sources: dict[str, str] = {}
        self._lifecycles: dict[str, AddonLifecycleSpec] = {}
        self._project_enabled_defaults: set[str] = set()
        self._project_disabled_defaults: set[str] = set()

    def _iter_effective_addons(self) -> list[tuple[str, AddonSpec]]:
        return [(name, self._registry[name]) for name in self.enabled(skip_digestion=True)]

    @signal(tags=["addon"])
    def register(
        self,
        addon: AddonSpec,
        *,
        lifecycle: AddonLifecycleSpec | None = None,
    ) -> AddonSpec:
        if not isinstance(addon, AddonSpec):
            raise ValueError("addons.register(...) requires an AddonSpec instance.")
        self._registry[addon.name] = addon
        if addon.name in self._project_disabled_defaults:
            self._enabled.discard(addon.name)
        else:
            self._enabled.add(addon.name)
        if addon.name in self._project_enabled_defaults:
            self._enabled.add(addon.name)
        if lifecycle is not None:
            if not isinstance(lifecycle, AddonLifecycleSpec):
                raise ValueError("addons.register(..., lifecycle=...) requires an AddonLifecycleSpec instance.")
            self._lifecycles[addon.name] = lifecycle
        else:
            self._lifecycles.pop(addon.name, None)
        return addon

    @signal(tags=["addon"])
    def register_module(self, module: str | ModuleType) -> AddonSpec:
        imported = import_module(module) if isinstance(module, str) else module
        addon = self.register(
            _load_addon_spec_from_module(imported),
            lifecycle=_load_addon_lifecycle_from_module(imported),
        )
        self._module_sources[addon.name] = getattr(imported, "__name__", addon.name)
        return addon

    @signal(tags=["addon"])
    def discover(self, modules: tuple[str, ...] | list[str] | None = None) -> list[AddonSpec]:
        discovered: list[AddonSpec] = []
        module_names = KNOWN_ADDON_MODULES if modules is None else tuple(modules)
        for module_name in module_names:
            try:
                addon = self.register_module(module_name)
            except ModuleNotFoundError:
                continue
            discovered.append(addon)
        return discovered

    @signal(tags=["addon"])
    @digest()
    def unregister(self, name: str, skip_digestion: bool = False) -> None:
        self._registry.pop(name, None)
        self._enabled.discard(name)
        self._module_sources.pop(name, None)
        self._lifecycles.pop(name, None)

    @signal(tags=["addon"])
    @digest()
    def contains(self, name: str, skip_digestion: bool = False) -> bool:
        return name in self._registry

    @signal(tags=["addon"])
    @digest()
    def get(self, name: str, skip_digestion: bool = False) -> AddonSpec | None:
        return self._registry.get(name)

    @signal(tags=["addon"])
    @digest()
    def names(self, skip_digestion: bool = False) -> list[str]:
        return sorted(self._registry.keys())

    @signal(tags=["addon"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        return len(self._registry)

    @signal(tags=["addon"])
    @digest()
    def clear(self, skip_digestion: bool = False) -> None:
        self._registry.clear()
        self._enabled.clear()
        self._module_sources.clear()
        self._lifecycles.clear()
        self._project_enabled_defaults.clear()
        self._project_disabled_defaults.clear()

    @signal(tags=["addon"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        enabled = set(self.enabled(skip_digestion=True))
        for name in self.names(skip_digestion=True):
            record = self._registry[name].info()
            record["enabled"] = name in enabled
            record["project_default_enabled"] = name in self._project_enabled_defaults
            record["project_default_disabled"] = name in self._project_disabled_defaults
            record["module"] = self._module_sources.get(name)
            lifecycle = self._lifecycles.get(name)
            record["lifecycle"] = lifecycle.info() if lifecycle is not None else {
                "has_on_enable": False,
                "has_on_disable": False,
                "has_on_context_action": False,
            }
            records.append(record)
        return records

    @signal(tags=["addon"])
    @digest()
    def available(self, skip_digestion: bool = False) -> list[str]:
        return self.names(skip_digestion=True)

    @signal(tags=["addon"])
    @digest()
    def known_modules(self, skip_digestion: bool = False) -> list[str]:
        return list(KNOWN_ADDON_MODULES)

    @signal(tags=["addon"])
    @digest()
    def module_for(self, name: str, skip_digestion: bool = False) -> str | None:
        return self._module_sources.get(name)

    @signal(tags=["addon"])
    @digest()
    def lifecycle_for(self, name: str, skip_digestion: bool = False) -> AddonLifecycleSpec | None:
        return self._lifecycles.get(name)

    @signal(tags=["addon", "config"])
    @digest()
    def project_enabled_defaults(self, skip_digestion: bool = False) -> list[str]:
        return sorted(self._project_enabled_defaults)

    @signal(tags=["addon", "config"])
    @digest()
    def project_disabled_defaults(self, skip_digestion: bool = False) -> list[str]:
        return sorted(self._project_disabled_defaults)

    @signal(tags=["addon"])
    @digest()
    def enabled(self, skip_digestion: bool = False) -> list[str]:
        return sorted(name for name in self._enabled if name in self._registry)

    @signal(tags=["addon"])
    @digest()
    def disabled(self, skip_digestion: bool = False) -> list[str]:
        enabled = set(self.enabled(skip_digestion=True))
        return [name for name in self.names(skip_digestion=True) if name not in enabled]

    @signal(tags=["addon"])
    @digest()
    def is_enabled(self, name: str, skip_digestion: bool = False) -> bool:
        return name in self._enabled and name in self._registry

    @signal(tags=["addon"])
    @digest()
    def enable(self, name: str, skip_digestion: bool = False) -> None:
        if name not in self._registry:
            raise ValueError(f"No add-on named {name!r} is registered.")
        self._enabled.add(name)

    @signal(tags=["addon"])
    @digest()
    def disable(self, name: str, skip_digestion: bool = False) -> None:
        if name not in self._registry:
            raise ValueError(f"No add-on named {name!r} is registered.")
        self._enabled.discard(name)

    @signal(tags=["addon", "config"])
    @digest()
    def load_project_config(self, path: str, skip_digestion: bool = False) -> dict[str, Any]:
        config = load_project_config(path, skip_digestion=True)
        enabled_defaults = set(config.get("addons_enabled") or [])
        disabled_defaults = set(config.get("addons_disabled") or [])
        overlap = enabled_defaults.intersection(disabled_defaults)
        if overlap:
            raise ValueError(
                "Project add-on defaults must not overlap: " + ", ".join(sorted(overlap))
            )
        self._project_enabled_defaults = enabled_defaults
        self._project_disabled_defaults = disabled_defaults
        for name in list(self._registry.keys()):
            if name in self._project_disabled_defaults:
                self._enabled.discard(name)
            else:
                self._enabled.add(name)
            if name in self._project_enabled_defaults:
                self._enabled.add(name)
        return {
            "path": config.get("path"),
            "addons_enabled": sorted(enabled_defaults),
            "addons_disabled": sorted(disabled_defaults),
        }


class ViewAddonsManager(_AddonAggregationMixin):
    """View-local add-on projection derived from the host registry."""

    def __init__(self, view: Any, host_registry: GlobalAddonsRegistry) -> None:
        self._view = view
        self._host = host_registry
        self._enabled_overrides: set[str] = set()
        self._disabled_overrides: set[str] = set()
        self._active_runtime: set[str] = set()
        self._notify_view_runtime = False
        self._sync_runtime()

    def bind_runtime(self) -> None:
        self._notify_view_runtime = True
        self._notify_runtime_summary()

    def _effective_enabled(self) -> list[str]:
        names = []
        for name in self._host.available(skip_digestion=True):
            if name in self._disabled_overrides:
                continue
            if name in self._enabled_overrides or self._host.is_enabled(name, skip_digestion=True):
                names.append(name)
        return sorted(names)

    def _iter_effective_addons(self) -> list[tuple[str, AddonSpec]]:
        return [
            (name, addon)
            for name in self._effective_enabled()
            if (addon := self._host.get(name, skip_digestion=True)) is not None
        ]

    def _activate_addon(self, name: str) -> None:
        if name in self._active_runtime:
            return
        lifecycle = self._host.lifecycle_for(name, skip_digestion=True)
        if lifecycle is not None and lifecycle.on_enable is not None:
            lifecycle.on_enable(self._view)
        self._active_runtime.add(name)

    def _deactivate_addon(self, name: str) -> None:
        if name not in self._active_runtime:
            return
        lifecycle = self._host.lifecycle_for(name, skip_digestion=True)
        if lifecycle is not None and lifecycle.on_disable is not None:
            lifecycle.on_disable(self._view)
        self._active_runtime.discard(name)

    def _sync_runtime(self) -> None:
        desired = set(self._effective_enabled())
        active = set(self._active_runtime)
        for name in sorted(active - desired):
            self._deactivate_addon(name)
        for name in sorted(desired - active):
            self._activate_addon(name)
        self._notify_runtime_summary()

    def _notify_runtime_summary(self) -> None:
        if not self._notify_view_runtime:
            return
        sync = getattr(self._view, "_sync_addons_runtime", None)
        if callable(sync):
            sync()

    @signal(tags=["addon"])
    @digest()
    def available(self, skip_digestion: bool = False) -> list[str]:
        return self._host.available(skip_digestion=True)

    @signal(tags=["addon"])
    @digest()
    def enabled(self, skip_digestion: bool = False) -> list[str]:
        return self._effective_enabled()

    @signal(tags=["addon"])
    @digest()
    def disabled(self, skip_digestion: bool = False) -> list[str]:
        enabled = set(self.enabled(skip_digestion=True))
        return [name for name in self.available(skip_digestion=True) if name not in enabled]

    @signal(tags=["addon"])
    @digest()
    def is_enabled(self, name: str, skip_digestion: bool = False) -> bool:
        return name in set(self.enabled(skip_digestion=True))

    @signal(tags=["addon"])
    @digest()
    def enable(self, name: str, skip_digestion: bool = False) -> None:
        if not self._host.contains(name, skip_digestion=True):
            raise ValueError(f"No add-on named {name!r} is registered in molsysviewer.addons.")
        self._disabled_overrides.discard(name)
        self._enabled_overrides.add(name)
        self._sync_runtime()

    @signal(tags=["addon"])
    @digest()
    def disable(self, name: str, skip_digestion: bool = False) -> None:
        if not self._host.contains(name, skip_digestion=True):
            raise ValueError(f"No add-on named {name!r} is registered in molsysviewer.addons.")
        self._enabled_overrides.discard(name)
        self._disabled_overrides.add(name)
        self._sync_runtime()

    @signal(tags=["addon"])
    @digest()
    def reset(self, skip_digestion: bool = False) -> None:
        self._enabled_overrides.clear()
        self._disabled_overrides.clear()
        self._sync_runtime()

    @signal(tags=["addon"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        enabled = set(self.enabled(skip_digestion=True))
        records: list[dict[str, Any]] = []
        for name in self.available(skip_digestion=True):
            addon = self._host.get(name, skip_digestion=True)
            if addon is None:
                continue
            record = addon.info()
            record["enabled"] = name in enabled
            record["module"] = self._host.module_for(name, skip_digestion=True)
            lifecycle = self._host.lifecycle_for(name, skip_digestion=True)
            record["lifecycle"] = lifecycle.info() if lifecycle is not None else {
                "has_on_enable": False,
                "has_on_disable": False,
                "has_on_context_action": False,
            }
            records.append(record)
        return records

    @signal(tags=["addon", "context"])
    @digest()
    def handle_context_action(
        self,
        addon: str,
        action_id: str,
        payload: dict[str, Any],
        skip_digestion: bool = False,
    ) -> bool:
        if addon not in self._effective_enabled():
            return False
        lifecycle = self._host.lifecycle_for(addon, skip_digestion=True)
        handler = lifecycle.on_context_action if lifecycle is not None else None
        if handler is None:
            return False
        handler(self._view, action_id, dict(payload))
        return True


addons = GlobalAddonsRegistry()
