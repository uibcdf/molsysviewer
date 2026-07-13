from __future__ import annotations

from typing import Any, Mapping


def addon_context_action(view: Any, content: Mapping[str, Any]) -> None:
    addon = content.get("addon")
    action_id = content.get("addon_action_id")
    if not isinstance(addon, str) or not addon.strip():
        raise ValueError("addon_context_action requires non-empty addon.")
    if not isinstance(action_id, str) or not action_id.strip():
        raise ValueError("addon_context_action requires non-empty addon_action_id.")
    view.addons.handle_context_action(addon.strip(), action_id.strip(), dict(content), skip_digestion=True)
    view._sync_addons_runtime()


def addon_enable(view: Any, content: Mapping[str, Any]) -> None:
    name = content.get("name")
    if not isinstance(name, str) or not name.strip():
        return
    view.addons.enable(name.strip())
    view._sync_addons_runtime()


def addon_disable(view: Any, content: Mapping[str, Any]) -> None:
    name = content.get("name")
    if not isinstance(name, str) or not name.strip():
        return
    view.addons.disable(name.strip())
    view._sync_addons_runtime()


def addon_rescan(view: Any, content: Mapping[str, Any]) -> None:
    del content
    try:
        view.addons._host.discover(include_known_modules=True)
    except Exception:
        pass
    view._sync_addons_runtime()


def addon_register_module(view: Any, content: Mapping[str, Any]) -> None:
    name = content.get("name")
    if not isinstance(name, str) or not name.strip():
        return
    normalized = name.strip()
    try:
        addon = view.addons._host.register_module(normalized)
        view.addons.enable(addon.name)
    except Exception as exc:
        view.addons._host._record_discovery_failure(normalized, exc)
    view._sync_addons_runtime()


HANDLERS = {
    "addon_context_action": addon_context_action,
    "addon_enable": addon_enable,
    "addon_disable": addon_disable,
    "addon_rescan": addon_rescan,
    "addon_register_module": addon_register_module,
}
