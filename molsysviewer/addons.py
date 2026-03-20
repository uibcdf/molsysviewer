from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest


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


@dataclass(frozen=True)
class AddonSpec:
    name: str
    package: str | None = None
    version: str | None = None
    description: str | None = None
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
        object.__setattr__(self, "panels", tuple(self.panels))
        object.__setattr__(self, "context_actions", tuple(self.context_actions))
        object.__setattr__(self, "workbench_sections", tuple(self.workbench_sections))
        object.__setattr__(self, "shape_providers", tuple(self.shape_providers))
        object.__setattr__(self, "style_helpers", tuple(self.style_helpers))
        object.__setattr__(self, "export_helpers", tuple(self.export_helpers))
        object.__setattr__(self, "tool_modes", tuple(self.tool_modes))
        object.__setattr__(self, "meta", _normalize_meta(self.meta))
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

    def _iter_effective_addons(self) -> list[tuple[str, AddonSpec]]:
        return [(name, self._registry[name]) for name in self.enabled(skip_digestion=True)]

    @signal(tags=["addon"])
    def register(self, addon: AddonSpec) -> AddonSpec:
        if not isinstance(addon, AddonSpec):
            raise ValueError("addons.register(...) requires an AddonSpec instance.")
        self._registry[addon.name] = addon
        self._enabled.add(addon.name)
        return addon

    @signal(tags=["addon"])
    @digest()
    def unregister(self, name: str, skip_digestion: bool = False) -> None:
        self._registry.pop(name, None)
        self._enabled.discard(name)

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

    @signal(tags=["addon"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        enabled = set(self.enabled(skip_digestion=True))
        for name in self.names(skip_digestion=True):
            record = self._registry[name].info()
            record["enabled"] = name in enabled
            records.append(record)
        return records

    @signal(tags=["addon"])
    @digest()
    def available(self, skip_digestion: bool = False) -> list[str]:
        return self.names(skip_digestion=True)

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


class ViewAddonsManager(_AddonAggregationMixin):
    """View-local add-on projection derived from the host registry."""

    def __init__(self, view: Any, host_registry: GlobalAddonsRegistry) -> None:
        self._view = view
        self._host = host_registry
        self._enabled_overrides: set[str] = set()
        self._disabled_overrides: set[str] = set()

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

    @signal(tags=["addon"])
    @digest()
    def disable(self, name: str, skip_digestion: bool = False) -> None:
        if not self._host.contains(name, skip_digestion=True):
            raise ValueError(f"No add-on named {name!r} is registered in molsysviewer.addons.")
        self._enabled_overrides.discard(name)
        self._disabled_overrides.add(name)

    @signal(tags=["addon"])
    @digest()
    def reset(self, skip_digestion: bool = False) -> None:
        self._enabled_overrides.clear()
        self._disabled_overrides.clear()

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
            records.append(record)
        return records


addons = GlobalAddonsRegistry()
