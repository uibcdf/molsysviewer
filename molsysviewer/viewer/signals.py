from __future__ import annotations

from importlib import import_module
from typing import Any


def _signal_value(args: tuple[Any, ...], kwargs: dict[str, Any], index: int, name: str) -> Any:
    if name in kwargs:
        return kwargs[name]
    if len(args) > index:
        return args[index]
    return None


def load_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    molecular_system = _signal_value(args, kwargs, 1, "molecular_system")
    return {"molecular_system": type(molecular_system).__name__ if molecular_system is not None else None}


def zoom_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {"selection": _signal_value(args, kwargs, 1, "selection")}


def controls_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "visible": _signal_value(args, kwargs, 1, "visible"),
        "autohide": _signal_value(args, kwargs, 2, "autohide"),
    }


def camera_snapshot_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    snapshot = _signal_value(args, kwargs, 1, "snapshot")
    return {
        "duration_ms": _signal_value(args, kwargs, 2, "duration_ms"),
        "snapshot_keys": sorted(snapshot.keys()) if isinstance(snapshot, dict) else [],
    }


def write_html_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "output_filename": _signal_value(args, kwargs, 1, "output_filename"),
        "mode": _signal_value(args, kwargs, 5, "mode"),
        "include_popout": _signal_value(args, kwargs, 4, "include_popout"),
    }


def resolve_entry_callable(entry: str) -> Any | None:
    if not isinstance(entry, str) or entry.strip() == "" or "." not in entry:
        return None
    module_name, _, attr_name = entry.rpartition(".")
    if not module_name or not attr_name:
        return None
    try:
        module = import_module(module_name)
    except Exception:
        return None
    return getattr(module, attr_name, None)


def panel_mode_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel": _signal_value(args, kwargs, 1, "panel"),
        "expanded": _signal_value(args, kwargs, 2, "expanded")
        if _signal_value(args, kwargs, 2, "expanded") is not None
        else True,
    }


def workspace_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {"workspace": _signal_value(args, kwargs, 1, "workspace") or "core"}


def workspace_panel_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel": _signal_value(args, kwargs, 1, "panel"),
        "workspace": _signal_value(args, kwargs, 2, "workspace"),
    }


def workspace_panels_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {"workspace": _signal_value(args, kwargs, 1, "workspace") or "core"}


def workspace_sections_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {"workspace": _signal_value(args, kwargs, 1, "workspace") or "core"}


def workspace_catalog_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    view = args[0] if args else None
    state = getattr(view, "_last_panel_mode_state_event", None)
    current_workspace = "core"
    if isinstance(state, dict):
        workspace = state.get("workspace")
        if isinstance(workspace, str) and workspace.strip() != "":
            current_workspace = workspace

    workspace_count = 1
    if view is not None:
        try:
            workspace_specs = view.addons.workspace_specs(skip_digestion=True)
            panel_specs = view.addons.panel_specs(skip_digestion=True)
            workbench_specs = view.addons.addon_section_specs(skip_digestion=True)
            for workspace in workspace_specs:
                workspace_id = workspace.get("id")
                addon_name = workspace.get("addon")
                if not isinstance(workspace_id, str) or not isinstance(addon_name, str):
                    continue
                panel_count = sum(
                    1
                    for item in panel_specs
                    if item.get("addon") == addon_name and item.get("target", "panel_mode") == "panel_mode"
                )
                workbench_section_count = sum(
                    1
                    for item in workbench_specs
                    if item.get("addon") == addon_name and item.get("target_panel", "addons") == "addons"
                )
                if panel_count + workbench_section_count > 0:
                    workspace_count += 1
        except Exception:
            pass

    return {
        "current_workspace": current_workspace,
        "workspace_count": workspace_count,
    }


def workspace_runtime_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    view = args[0] if args else None
    state = getattr(view, "_last_panel_mode_state_event", None)
    current_workspace = "core"
    if isinstance(state, dict):
        workspace = state.get("workspace")
        if isinstance(workspace, str) and workspace.strip() != "":
            current_workspace = workspace

    panel_count = 2 if current_workspace == "core" else 0
    if view is not None and current_workspace != "core":
        try:
            workspace_specs = view.addons.workspace_specs(skip_digestion=True)
            panel_specs = view.addons.panel_specs(skip_digestion=True)
            addon_name = next(
                (
                    item.get("addon")
                    for item in workspace_specs
                    if item.get("id") == current_workspace and isinstance(item.get("addon"), str)
                ),
                None,
            )
            if isinstance(addon_name, str):
                panel_count = sum(
                    1
                    for item in panel_specs
                    if item.get("addon") == addon_name and item.get("target", "panel_mode") == "panel_mode"
                )
        except Exception:
            pass

    return {
        "current_workspace": current_workspace,
        "panel_count": panel_count,
        "pretty": _signal_value(args, kwargs, 1, "pretty")
        if _signal_value(args, kwargs, 1, "pretty") is not None
        else False,
    }


def panel_mode_state_query_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "pretty": _signal_value(args, kwargs, 1, "pretty")
        if _signal_value(args, kwargs, 1, "pretty") is not None
        else False,
    }


__all__ = [
    "camera_snapshot_extra",
    "controls_signal_extra",
    "load_signal_extra",
    "panel_mode_signal_extra",
    "panel_mode_state_query_extra",
    "resolve_entry_callable",
    "workspace_catalog_signal_extra",
    "workspace_panel_signal_extra",
    "workspace_panels_signal_extra",
    "workspace_runtime_signal_extra",
    "workspace_sections_signal_extra",
    "workspace_signal_extra",
    "write_html_signal_extra",
    "zoom_signal_extra",
]
