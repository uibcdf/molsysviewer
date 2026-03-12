from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest
from .layers import Layer


class AnnotationsManager:
    """Annotation manager bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def _ensure_layer(self, tag: str) -> Layer:
        if tag not in self._view._layers:  # noqa: SLF001
            self._view._layers[tag] = Layer(self._view, tag, kind="annotation", meta={})  # noqa: SLF001
        else:
            self._view._layers[tag].kind = "annotation"  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001

    def _annotation_layer(self, tag: str) -> Layer | None:
        layer = self._view._layers.get(tag)  # noqa: SLF001
        if layer is None or getattr(layer, "kind", None) != "annotation":
            return None
        return layer

    def _require_annotation_layer(self, tag: str) -> Layer:
        layer = self._annotation_layer(tag)
        if layer is None:
            raise ValueError(f"No annotation layer found for tag {tag!r}.")
        return layer

    def _resolve_group_atom_indices(self, group_index: Any) -> list[int]:
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before adding labels.")

        if not isinstance(group_index, list) or len(group_index) != 1:
            raise ValueError("Annotation label operations currently require exactly one group_index.")

        group_idx = int(group_index[0])
        atom_indices = msm.select(
            self._view._molsys,  # noqa: SLF001
            selection=f"group_index=={group_idx}",
            syntax="MolSysMT",
            skip_digestion=True,
        )
        atom_indices = [int(ii) for ii in atom_indices]
        if len(atom_indices) == 0:
            raise ValueError(f"Group index {group_idx} did not resolve to any atoms.")
        return atom_indices

    @signal(tags=["annotation"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        """Return the active annotation tags."""
        return [tag for tag, layer in self._view._layers.items() if getattr(layer, "kind", None) == "annotation"]  # noqa: SLF001

    @signal(tags=["annotation"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        """Return whether an annotation layer exists for ``tag``."""
        return self._annotation_layer(tag) is not None

    @signal(tags=["annotation"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False) -> Layer | None:
        """Return the annotation layer for ``tag``, if present."""
        return self._annotation_layer(tag)

    @signal(tags=["annotation"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return a copy of the current replayable annotation records."""
        return [dict(item) for item in self._view._annotation_history]  # noqa: SLF001

    @signal(tags=["annotation"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        """Return the number of replayable annotation records."""
        return len(self._view._annotation_history)  # noqa: SLF001

    @signal(tags=["annotation", "query"])
    @digest()
    def info(self, tag: str | None = None, skip_digestion: bool = False) -> dict[str, Any] | list[dict[str, Any]]:
        """Return compact annotation metadata for one tag or all annotations."""

        def summarize(record: dict[str, Any]) -> dict[str, Any]:
            options = record.get("options")
            if not isinstance(options, dict):
                options = {}
            atom_indices = options.get("atom_indices")
            atom_indices = atom_indices if isinstance(atom_indices, list) else []
            record_tag = record.get("tag")
            if not isinstance(record_tag, str):
                record_tag = options.get("tag") if isinstance(options.get("tag"), str) else None
            layer = self._annotation_layer(record_tag) if record_tag is not None else None
            return {
                "kind": "label" if record.get("op") == "add_label" else "annotation",
                "tag": record_tag,
                "text": options.get("text"),
                "n_atoms": len(atom_indices),
                "atom_indices": list(atom_indices),
                "visible": False if layer is None else not getattr(layer, "_hidden", False),
                "active": False if layer is None else bool(getattr(layer, "_active", False)),
            }

        records = self.records(skip_digestion=True)
        if tag is None:
            return [summarize(record) for record in records]

        for record in records:
            summary = summarize(record)
            if summary.get("tag") == tag:
                return summary

        raise ValueError(f"No annotation record found for tag {tag!r}.")

    @signal(tags=["annotation"])
    @digest()
    def add_label(
        self,
        text: str,
        group_index: Any,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Add a persistent label anchored to a single group."""
        atom_indices = self._resolve_group_atom_indices(group_index)

        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        layer = self._ensure_layer(layer_tag)

        self._view._send(  # noqa: SLF001
            {
                "op": "add_label",
                "tag": layer_tag,
                "options": {
                    "text": text,
                    "tag": layer_tag,
                    "atom_indices": atom_indices,
                },
            }
        )
        return layer

    @signal(tags=["annotation", "selection"])
    @digest()
    def add_label_from_active_selection(
        self,
        text: str,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Add a persistent label from the last active selection.

        Current first slice:

        - requires a stored active selection event,
        - requires exactly one resolved group index,
        - delegates to :meth:`add_label`.
        """
        event = self._view.get_last_active_selection_event()
        if event is None:
            raise ValueError("No active selection stored. Select an element before adding a label.")

        group_indices = event.get("group_indices") or []
        if len(group_indices) != 1:
            raise ValueError(
                "add_label_from_active_selection() currently requires an active selection resolving to exactly one group."
            )

        return self.add_label(
            text=text,
            group_index=[int(group_indices[0])],
            tag=tag,
            skip_digestion=True,
        )

    @signal(tags=["annotation", "visibility"])
    @digest()
    def show(self, tag: str, skip_digestion: bool = False) -> Layer:
        """Show the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.show(skip_digestion=True)
        return layer

    @signal(tags=["annotation", "visibility"])
    @digest()
    def hide(self, tag: str, skip_digestion: bool = False) -> Layer:
        """Hide the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.hide(skip_digestion=True)
        return layer

    @signal(tags=["annotation"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        """Delete the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.delete(skip_digestion=True)

    @signal(tags=["annotation"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> Layer:
        """Rename an annotation layer tag."""
        layer = self._require_annotation_layer(tag)
        layer.set_tag(new_tag, skip_digestion=True)
        return layer

    @signal(tags=["annotation"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        """Clear annotations globally or remove one annotation layer by tag."""
        if tag is None:
            self._view.clear_decorations(shapes=False, styles=False, labels=True, skip_digestion=True)  # noqa: SLF001
            return
        self.delete(tag, skip_digestion=True)

    @signal(tags=["annotation"])
    @digest()
    def set_text(self, tag: str, text: str, skip_digestion: bool = False) -> Layer:
        """Update the text of an existing annotation label."""
        layer = self._require_annotation_layer(tag)
        if not isinstance(text, str) or text.strip() == "":
            raise ValueError("set_text() requires non-empty text.")

        record = self.info(tag, skip_digestion=True)
        atom_indices = record.get("atom_indices") if isinstance(record, dict) else None
        if not isinstance(atom_indices, list) or len(atom_indices) == 0:
            raise ValueError(f"Annotation tag {tag!r} does not have a valid atom-index anchor.")

        self._view._send(  # noqa: SLF001
            {
                "op": "update_label",
                "tag": tag,
                "options": {
                    "tag": tag,
                    "text": text.strip(),
                    "atom_indices": list(atom_indices),
                },
            }
        )
        return layer

    @signal(tags=["annotation"])
    @digest()
    def set_group_index(self, tag: str, group_index: Any, skip_digestion: bool = False) -> Layer:
        """Reanchor an existing label to a different single group."""
        layer = self._require_annotation_layer(tag)
        atom_indices = self._resolve_group_atom_indices(group_index)
        record = self.info(tag, skip_digestion=True)
        if not isinstance(record, dict):
            raise ValueError(f"No annotation record found for tag {tag!r}.")

        self._view._send(  # noqa: SLF001
            {
                "op": "update_label",
                "tag": tag,
                "options": {
                    "tag": tag,
                    "text": record.get("text"),
                    "atom_indices": list(atom_indices),
                },
            }
        )
        return layer


__all__ = ["AnnotationsManager"]
