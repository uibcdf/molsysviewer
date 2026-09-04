from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .addons import HANDLERS as ADDON_HANDLERS
from .regions import HANDLERS as REGION_HANDLERS
from .scene_objects import HANDLERS as SCENE_OBJECT_HANDLERS
from .selections import HANDLERS as SELECTION_HANDLERS
from .trajectory import HANDLERS as TRAJECTORY_HANDLERS
from .viewport import HANDLERS as VIEWPORT_HANDLERS
from .whole import HANDLERS as WHOLE_HANDLERS

PanelActionHandler = Callable[[Any, Mapping[str, Any]], None]


def _build_handlers() -> dict[str, PanelActionHandler]:
    handlers: dict[str, PanelActionHandler] = {}
    for domain in (
        ADDON_HANDLERS,
        SELECTION_HANDLERS,
        REGION_HANDLERS,
        SCENE_OBJECT_HANDLERS,
        WHOLE_HANDLERS,
        VIEWPORT_HANDLERS,
        TRAJECTORY_HANDLERS,
    ):
        duplicates = handlers.keys() & domain.keys()
        if duplicates:
            raise RuntimeError(f"Duplicate panel action handlers: {sorted(duplicates)!r}.")
        handlers.update(domain)
    return handlers


HANDLERS = _build_handlers()

# These names belong to the closed TypeScript PanelAction vocabulary but are
# intentionally consumed by the browser before the Python dispatch seam.
FRONTEND_LOCAL_PANEL_ACTIONS = frozenset({
    "undo_active_selection",
    "redo_active_selection",
    "begin_scene_history_coalescing",
    "end_scene_history_coalescing",
    "selection_query_preview_request",
})

# These enter through interaction_context_action from context menus or addon
# infrastructure, but are not emitted by a Studio subpanel.
CONTEXT_ONLY_ACTIONS = frozenset({
    "addon_context_action",
    "addon_disable",
    "addon_enable",
    "addon_register_module",
    "addon_rescan",
    "hide_measurement",
    "preview_selection_query",
    "remove_selection",
    "set_trajectory_frame",
    "set_trajectory_playback",
    "step_trajectory",
})


def dispatch_panel_action(view: Any, content: Mapping[str, Any]) -> None:
    action = content.get("action")
    if not isinstance(action, str) or not action:
        raise ValueError("Panel action requires a non-empty action name.")
    handler = HANDLERS.get(action)
    if handler is None:
        raise ValueError(f"Unsupported panel action: {action!r}.")
    handler(view, content)


__all__ = [
    "CONTEXT_ONLY_ACTIONS",
    "FRONTEND_LOCAL_PANEL_ACTIONS",
    "HANDLERS",
    "dispatch_panel_action",
]
