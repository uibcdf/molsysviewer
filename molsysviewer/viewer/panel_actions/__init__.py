from __future__ import annotations

from collections.abc import Callable, Mapping
from concurrent.futures import Future
from typing import Any

from ..work_file_saves import WorkFileSaveCancelled
from ._file_selection import HANDLERS as FILE_SELECTION_HANDLERS
from .addons import HANDLERS as ADDON_HANDLERS
from .batch import batch_scene_objects
from .interactions import HANDLERS as INTERACTION_HANDLERS
from .loading import load_systems
from .persistence import HANDLERS as PERSISTENCE_HANDLERS
from .regions import HANDLERS as REGION_HANDLERS
from .scene_objects import HANDLERS as SCENE_OBJECT_HANDLERS
from .selections import HANDLERS as SELECTION_HANDLERS
from .trajectory import HANDLERS as TRAJECTORY_HANDLERS
from .viewport import HANDLERS as VIEWPORT_HANDLERS
from .whole import HANDLERS as WHOLE_HANDLERS

PanelActionHandler = Callable[[Any, Mapping[str, Any]], Any]


def _sync_system_edits(view, content):
    view.addons.manager.system_edits.synchronize()


STUDIO_RESULT_DOMAINS = {
    "save_work_file": "export",
    "cancel_work_file": "export",
    "restore_work_file": "export",
    "create_region_from_selection": "regions",
    "create_region_from_saved_selection": "regions",
    "save_selection": "selections",
    "rename_selection": "selections",
    "create_label_from_saved_selection": "annotations",
    "addon_register_module": "addons",
    "create_shape": "shapes",
    "create_measurement": "measurements",
    "create_annotation": "annotations",
    "create_layer": "layers",
    "delete_interaction_analysis": "interactions",
}


def _build_handlers() -> dict[str, PanelActionHandler]:
    handlers: dict[str, PanelActionHandler] = {}
    for domain in (
        FILE_SELECTION_HANDLERS,
        ADDON_HANDLERS,
        INTERACTION_HANDLERS,
        {
            "load_systems": load_systems,
            "batch_scene_objects": batch_scene_objects,
            "sync_system_edits": _sync_system_edits,
        },
        SELECTION_HANDLERS,
        REGION_HANDLERS,
        SCENE_OBJECT_HANDLERS,
        WHOLE_HANDLERS,
        VIEWPORT_HANDLERS,
        TRAJECTORY_HANDLERS,
        PERSISTENCE_HANDLERS,
    ):
        duplicates = handlers.keys() & domain.keys()
        if duplicates:
            raise RuntimeError(f"Duplicate panel action handlers: {sorted(duplicates)!r}.")
        handlers.update(domain)
    return handlers


HANDLERS = _build_handlers()

# These names belong to the closed TypeScript PanelAction vocabulary but are
# intentionally consumed by the browser before the Python dispatch seam.
FRONTEND_LOCAL_PANEL_ACTIONS = frozenset(
    {
        "undo_active_selection",
        "redo_active_selection",
        "begin_scene_history_coalescing",
        "end_scene_history_coalescing",
        "selection_query_preview_request",
    }
)

# These enter through interaction_context_action from context menus or addon
# infrastructure, but are not emitted by a Studio subpanel.
CONTEXT_ONLY_ACTIONS = frozenset(
    {
        "addon_context_action",
        "addon_disable",
        "addon_enable",
        "addon_rescan",
        "hide_measurement",
        "focus_target",
        "focus_selection",
        "clear_selection",
        "select_context_target",
        "create_region_from_target",
        "create_annotation_from_target",
        "select_picked_interaction",
        "focus_picked_interaction",
        "preview_selection_query",
        "remove_selection",
        "set_trajectory_frame",
        "set_trajectory_playback",
        "step_trajectory",
    }
)


def _studio_result(view, content, domain, error=None):
    message = {
        "op": "studio_action_result",
        "action": content["action"],
        "request_id": content["request_id"],
        "ok": error is None,
        "domain": domain,
    }
    if error is not None:
        message["error_message"] = str(error)
        if isinstance(error, WorkFileSaveCancelled):
            message["cancelled"] = True
    owner = content.get("_studio_owner_endpoint_id", content.get("_work_file_owner_endpoint_id"))
    if isinstance(owner, str) and owner:
        message["target_endpoint_id"] = f"widget-host:{view._binary_session_id}" if owner == "primary" else owner
    # A verdict releases requester controls; it must not wait for an unrelated
    # structure stream (or for the stream whose failure caused this verdict).
    if view._ready:
        view._transmit_widget_message(message)


def dispatch_panel_action(view: Any, content: Mapping[str, Any]):
    action = content.get("action")
    if not isinstance(action, str) or not action:
        raise ValueError("Panel action requires a non-empty action name.")
    handler = HANDLERS.get(action)
    if handler is None:
        raise ValueError(f"Unsupported panel action: {action!r}.")
    if (action in STUDIO_RESULT_DOMAINS or action == "batch_scene_objects") and isinstance(
        content.get("request_id"), str
    ):
        domain = STUDIO_RESULT_DOMAINS.get(action, content.get("domain"))
        try:
            pending = handler(view, content)
        except Exception as exc:
            _studio_result(view, content, domain, exc)
            raise
        else:
            if isinstance(pending, Future):
                intent = dict(content)

                def completed(future):
                    try:
                        future.result()
                    except BaseException as error:
                        _studio_result(view, intent, domain, error)
                        if (
                            isinstance(error, Exception)
                            and action != "cancel_work_file"
                            and not isinstance(error, WorkFileSaveCancelled)
                        ):
                            view._send_backend_error_ack(intent, error)
                    else:
                        _studio_result(view, intent, domain)

                pending.add_done_callback(completed)
                return pending
            _studio_result(view, content, domain)
    else:
        handler(view, content)


__all__ = [
    "CONTEXT_ONLY_ACTIONS",
    "FRONTEND_LOCAL_PANEL_ACTIONS",
    "HANDLERS",
    "dispatch_panel_action",
]
