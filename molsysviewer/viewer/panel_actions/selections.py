from __future__ import annotations

from numbers import Integral
from typing import Any, Mapping

from ...active_selection import _combine


def _context_atoms(view: Any, content: Mapping[str, Any]) -> list[int]:
    """Resolve the declared target scope using the canonical molecular owner."""
    context = content.get("context")
    if not isinstance(context, Mapping):
        raise ValueError("A context target is required.")
    if context.get("kind") not in {"structure", "shape", "annotation", "measurement"}:
        raise ValueError("This target does not support molecular scope resolution.")
    if view._molsys is None:
        raise ValueError("No molecular system loaded.")
    frame = content.get("structure_index")
    if frame is not None and (
        isinstance(frame, bool) or not isinstance(frame, Integral) or frame != view.current_structure_index
    ):
        raise ValueError("The context frame has changed; open the menu again.")
    atoms = context.get("atom_indices")
    if not isinstance(atoms, (list, tuple)) or not atoms:
        raise ValueError("This context target has no atom anchors.")
    n_atoms = int(view._molsys.get_n_atoms())
    if any(isinstance(atom, bool) or not isinstance(atom, Integral) or not 0 <= atom < n_atoms for atom in atoms):
        raise ValueError("Context atom indices are invalid for the current system.")
    scope = content.get("scope", "target")
    if scope == "target":
        return sorted(set(int(atom) for atom in atoms))
    if context.get("kind") != "structure":
        raise ValueError("Only a molecular target supports atom/group/chain scopes.")
    if scope == "atom":
        atom = context.get("atom_index")
        if isinstance(atom, bool) or not isinstance(atom, Integral) or atom not in atoms:
            raise ValueError("There is no unambiguous pointed atom in this target.")
        return [int(atom)]
    if scope not in {"group", "chain"}:
        raise ValueError(f"Unsupported context scope: {scope!r}.")
    resolved = view._atoms_for_selection_level(list(atoms), scope)
    if not resolved:
        raise ValueError(f"This target has no declared {scope} membership; use target or atom scope.")
    return resolved


def select_context_target(view: Any, content: Mapping[str, Any]) -> None:
    operation = content.get("op", "replace")
    if operation not in {"replace", "add", "subtract"}:
        raise ValueError(f"Unsupported target selection operation: {operation!r}.")
    atoms = _context_atoms(view, content)
    view.active_selection.set(_combine(view.active_selection.atom_indices, atoms, operation), skip_digestion=True)


def create_region_from_target(view: Any, content: Mapping[str, Any]) -> None:
    from .regions import create_region_from_query

    atoms = _context_atoms(view, content)
    create_region_from_query(view, {**content, "expression": atoms, "syntax": "Indices"})


def create_annotation_from_target(view: Any, content: Mapping[str, Any]) -> None:
    from .scene_objects import create_annotation

    atoms = _context_atoms(view, content)
    create_annotation(view, {**content, "atom_indices": atoms})


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
    with view.history._atomic_operation(("studio", tag or "", "create_region")):
        if content.get("overwrite") is True and tag in view.regions:
            view.regions[tag].delete(skip_digestion=True)
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
    tag = _required_text(content, "tag", "save_selection")
    with view.history._atomic_operation(("studio", tag, "save_selection")):
        if content.get("overwrite") is True and tag in view.selections:
            view.selections.delete(tag, skip_digestion=True)
        view.active_selection.save(tag=tag, skip_digestion=True)


def delete_selection(view: Any, content: Mapping[str, Any]) -> None:
    view.selections.delete(_required_text(content, "tag", "delete_selection"), skip_digestion=True)


def rename_selection(view: Any, content: Mapping[str, Any]) -> None:
    tag = _required_text(content, "tag", "rename_selection")
    new_tag = _required_text(content, "new_tag", "rename_selection")
    with view.history._atomic_operation(("studio", tag, "rename_selection")):
        if content.get("overwrite") is True and new_tag != tag and new_tag in view.selections:
            view.selections.delete(new_tag, skip_digestion=True)
        view.selections.set_tag(tag, new_tag, skip_digestion=True)


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
    tag = raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None
    with view.history._atomic_operation(("studio", tag or "", "create_region")):
        if content.get("overwrite") is True and tag in view.regions:
            view.regions[tag].delete(skip_digestion=True)
        region = saved.new_region(tag=tag, representation=representation, skip_digestion=True)
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
    del view, content
    raise ValueError(
        "The former MolSysMT remove_selection addon action is no longer supported. "
        "Use clear_selection to clear the selection without editing the molecular system."
    )


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
    "select_context_target": select_context_target,
    "create_region_from_target": create_region_from_target,
    "create_annotation_from_target": create_annotation_from_target,
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
