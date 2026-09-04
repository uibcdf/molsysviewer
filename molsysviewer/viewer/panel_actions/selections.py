from __future__ import annotations

from typing import Any, Mapping

from ...active_selection import _combine


def _required_text(content: Mapping[str, Any], key: str, action: str) -> str:
    value = content.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{action} requires non-empty {key}.")
    return value.strip()


def create_region_from_selection(view: Any, content: Mapping[str, Any]) -> None:
    raw_tag = content.get("tag")
    tag = raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None
    representation = content.get("representation")
    if representation is None:
        representation = "inherit"
    region = view.new_region_from_active_selection(
        tag=tag,
        representation=representation,
        skip_digestion=True,
    )
    preset = content.get("preset")
    if isinstance(preset, str) and preset.strip():
        region.set_representation(preset=preset.strip(), skip_digestion=True)


def activate_selection(view: Any, content: Mapping[str, Any]) -> None:
    view.selections.activate(_required_text(content, "tag", "activate_selection"), skip_digestion=True)


def save_selection(view: Any, content: Mapping[str, Any]) -> None:
    view.active_selection.save(tag=_required_text(content, "tag", "save_selection"), skip_digestion=True)


def delete_selection(view: Any, content: Mapping[str, Any]) -> None:
    view.selections.delete(_required_text(content, "tag", "delete_selection"), skip_digestion=True)


def rename_selection(view: Any, content: Mapping[str, Any]) -> None:
    view.selections.set_tag(
        _required_text(content, "tag", "rename_selection"),
        _required_text(content, "new_tag", "rename_selection"),
        skip_digestion=True,
    )


def compose_saved_selection(view: Any, content: Mapping[str, Any]) -> None:
    tag = _required_text(content, "tag", "compose_saved_selection")
    op = content.get("op")
    if op not in {"add", "subtract", "intersect"}:
        raise ValueError(f"Unsupported compose operation: {op!r}.")
    saved = view.selections.get(tag)
    if saved is None:
        raise ValueError(f"No saved selection found with tag {tag!r}.")
    view.active_selection.set(
        _combine(view.active_selection.atom_indices, saved.atom_indices, op),
        skip_digestion=True,
    )


def create_region_from_saved_selection(view: Any, content: Mapping[str, Any]) -> None:
    selection_tag = _required_text(content, "selection_tag", "create_region_from_saved_selection")
    saved = view.selections.get(selection_tag)
    if saved is None:
        raise ValueError(f"No saved selection found with tag {selection_tag!r}.")
    raw_tag = content.get("tag")
    representation = content.get("representation")
    if representation is None:
        representation = "inherit"
    region = saved.new_region(
        tag=raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None,
        representation=representation,
        skip_digestion=True,
    )
    preset = content.get("preset")
    if isinstance(preset, str) and preset.strip():
        region.set_representation(preset=preset.strip(), skip_digestion=True)


def create_label_from_saved_selection(view: Any, content: Mapping[str, Any]) -> None:
    selection_tag = _required_text(content, "selection_tag", "create_label_from_saved_selection")
    text = _required_text(content, "text", "create_label_from_saved_selection")
    saved = view.selections.get(selection_tag)
    if saved is None:
        raise ValueError(f"No saved selection found with tag {selection_tag!r}.")
    raw_tag = content.get("tag")
    saved.add_label(
        text=text,
        tag=raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None,
        skip_digestion=True,
    )


def apply_selection_query(view: Any, content: Mapping[str, Any]) -> None:
    view._apply_selection_query_action(content)


def set_active_selection_operation(view: Any, content: Mapping[str, Any]) -> None:
    view._apply_active_selection_operation(str(content.get("operation") or ""))


def preview_selection_query(view: Any, content: Mapping[str, Any]) -> None:
    view._preview_selection_query_action(content)


def expand_selection(view: Any, content: Mapping[str, Any]) -> None:
    view._expand_selection_action(content)


def remove_selection(view: Any, content: Mapping[str, Any]) -> None:
    atom_indices = list(view.active_selection.atom_indices)
    if not atom_indices:
        raise ValueError("remove_selection requires a non-empty active selection.")
    view.addons.handle_context_action(
        "molsysmt",
        "remove-selected-atoms",
        {
            "event": "interaction_context_action",
            "action": "remove_selection",
            "addon": "molsysmt",
            "addon_action_id": "remove-selected-atoms",
            "atom_indices": atom_indices,
            "context": content.get("context", {}),
        },
        skip_digestion=True,
    )
    view.active_selection.clear(skip_digestion=True)


def focus_target(view: Any, content: Mapping[str, Any]) -> None:
    context = content.get("context")
    context = context if isinstance(context, Mapping) else {}
    atom_indices = context.get("atom_indices")
    if isinstance(atom_indices, (list, tuple)) and atom_indices:
        view.camera.zoom(selection=list(atom_indices), skip_digestion=True)
        return
    tag = context.get("tag")
    if isinstance(tag, str) and tag.strip():
        view.camera.focus_on_object(tag.strip(), skip_digestion=True)
        return
    raise ValueError("focus_target requires atom indices or a tagged scene object.")


def focus_selection(view: Any, content: Mapping[str, Any]) -> None:
    del content
    atom_indices = list(view.active_selection.atom_indices)
    if not atom_indices:
        raise ValueError("focus_selection requires a non-empty active selection.")
    view.camera.zoom(selection=atom_indices, skip_digestion=True)


def clear_selection(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.active_selection.clear(skip_digestion=True)


HANDLERS = {
    "create_region_from_selection": create_region_from_selection,
    "activate_selection": activate_selection,
    "save_selection": save_selection,
    "delete_selection": delete_selection,
    "rename_selection": rename_selection,
    "compose_saved_selection": compose_saved_selection,
    "create_region_from_saved_selection": create_region_from_saved_selection,
    "create_label_from_saved_selection": create_label_from_saved_selection,
    "apply_selection_query": apply_selection_query,
    "set_active_selection_operation": set_active_selection_operation,
    "preview_selection_query": preview_selection_query,
    "expand_selection": expand_selection,
    "remove_selection": remove_selection,
    "focus_target": focus_target,
    "focus_selection": focus_selection,
    "clear_selection": clear_selection,
}
