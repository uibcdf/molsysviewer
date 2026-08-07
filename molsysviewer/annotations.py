from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.argdigest import digest
from .layers import Annotation, Layer
from .scene_history import records_scene_history


class AnnotationsManager:
    """Annotation manager bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def __getitem__(self, tag: str) -> Layer:
        layer = self.get(tag, skip_digestion=True)
        if layer is None:
            raise KeyError(tag)
        return layer

    def _ensure_layer(self, tag: str, *, layer_tag: str | None = None) -> Layer:
        tag = self._view._tag_managers["annotation"].validate(tag)  # noqa: SLF001
        resolved_layer_tag = str(layer_tag).strip() if layer_tag is not None else tag
        self._view._ensure_layer_group(  # noqa: SLF001
            resolved_layer_tag,
            kind="annotation",
            provenance="user" if layer_tag is not None else "auto",
        )
        annotation = Annotation(self._view, tag, layer_tag=resolved_layer_tag, meta={})
        self._view._scene_objects[("annotation", tag)] = annotation  # noqa: SLF001
        return annotation

    def _annotation_layer(self, tag: str) -> Layer | None:
        layer = self._view._scene_objects.get(("annotation", tag))  # noqa: SLF001
        if layer is None or getattr(layer, "kind", None) != "annotation":
            return None
        return layer

    def _require_annotation_layer(self, tag: str) -> Layer:
        layer = self._annotation_layer(tag)
        if layer is None:
            raise ValueError(f"No annotation layer found for tag {tag!r}.")
        return layer

    def _resolve_anchor_atom_indices(
        self,
        selection: Any = None,
        *,
        atom_indices: Any = None,
        group_index: Any = None,
    ) -> list[int]:
        """Resolve the label anchor to a flat list of atom indices."""
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before adding labels.")

        if atom_indices is not None:
            resolved = [int(i) for i in atom_indices]
            if not resolved:
                raise ValueError("atom_indices is empty.")
            return resolved

        if selection is not None:
            resolved = [
                int(i)
                for i in msm.select(
                    self._view._molsys,  # noqa: SLF001
                    selection=selection,
                    syntax="MolSysMT",
                    skip_digestion=True,
                )
            ]
            if not resolved:
                raise ValueError(f"Selection {selection!r} did not resolve to any atoms.")
            return resolved

        if group_index is not None:
            import warnings
            warnings.warn(
                "The group_index parameter is deprecated. Use selection or atom_indices instead.",
                DeprecationWarning,
                stacklevel=3,
            )
            if not isinstance(group_index, list) or len(group_index) != 1:
                raise ValueError("group_index must be a single-element list.")
            group_idx = int(group_index[0])
            resolved = [
                int(i)
                for i in msm.select(
                    self._view._molsys,  # noqa: SLF001
                    selection=f"group_index=={group_idx}",
                    syntax="MolSysMT",
                    skip_digestion=True,
                )
            ]
            if not resolved:
                raise ValueError(f"Group index {group_idx} did not resolve to any atoms.")
            return resolved

        raise ValueError("Provide selection, atom_indices, or group_index.")

    def tags(self, skip_digestion: bool = False) -> list[str]:
        """Return the active annotation tags."""
        return [tag for kind, tag in self._view._scene_objects if kind == "annotation"]  # noqa: SLF001

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
            res = {
                "kind": "label" if record.get("op") == "add_label" else "annotation",
                "tag": record_tag,
                "owner": None if layer is None else layer.owner,
                "layer_tag": None if layer is None else getattr(layer, "layer_tag", record_tag),
                "text": options.get("text"),
                "style": dict(options.get("style") or {}),
                "n_atoms": len(atom_indices),
                "atom_indices": list(atom_indices),
                "visible": False if layer is None else not getattr(layer, "_hidden", False),
                "active": False if layer is None else bool(getattr(layer, "_active", False)),
                "broken": False if layer is None else bool(getattr(layer, "broken", False)),
                "broken_reason": None if layer is None else getattr(layer, "broken_reason", None),
            }
            if "position" in options:
                res["position"] = options["position"]
            if "offset_mode" in options:
                res["offset_mode"] = options["offset_mode"]
            if "offset" in options:
                if options.get("offset_mode") == "world":
                    from ._pyunitwizard import puw
                    offset_q = puw.quantity(options["offset"], "angstrom")
                    offset_std = puw.get_value(puw.standardize(offset_q))
                    res["offset"] = [float(x) for x in offset_std]
                else:
                    res["offset"] = options["offset"]
            if "leader_line" in options:
                res["leader_line"] = options["leader_line"]
            if "leader_line_style" in options:
                res["leader_line_style"] = options["leader_line_style"]
            return res

        records = self.records(skip_digestion=True)
        if tag is None:
            return [summarize(record) for record in records]

        for record in records:
            summary = summarize(record)
            if summary.get("tag") == tag:
                return summary

        raise ValueError(f"No annotation record found for tag {tag!r}.")

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def add_annotation(
        self,
        text: str,
        kind: str = "label",
        selection: Any = None,
        *,
        atom_indices: Any = None,
        position: tuple[float, float, float] | None = None,
        offset_mode: str = "camera",
        offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        leader_line: bool = False,
        leader_line_style: str = "dashed",
        tag: str | None = None,
        layer_tag: str | None = None,
        syntax: str = "MolSysMT",
        label_style: dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Add a persistent annotation anchored to a set of atoms or position.

        Parameters
        ----------
        text
            Annotation text to display.
        kind
            Annotation kind. Currently only ``"label"`` is supported.
        selection
            MolSysMT selection string or expression (e.g. ``'group_index==5'``).
        atom_indices
            Explicit list of atom indices. Takes priority over *selection*.
        position
            Explicit absolute coordinate tuple (x, y, z). Takes priority over selection/atom_indices.
        offset_mode
            Offset coordinate space: `"camera"` or `"world"`.
        offset
            Relative offset displacement vector.
        leader_line
            If True, draws a connection line from the anchor to the offset label.
        leader_line_style
            Style of the connection line: `"solid"`, `"dashed"`, or `"dotted"`.
        tag
            Unique identifier for this annotation object.
        layer_tag
            Layer group for this annotation.
        syntax
            Selection syntax (default ``"MolSysMT"``).
        label_style
            Optional visual style dict.
        """
        if position is not None:
            if not isinstance(position, (list, tuple)) or len(position) != 3:
                raise ValueError("position must be a 3-element tuple or list of floats.")
            from ._pyunitwizard import puw
            pos_q = position if puw.is_quantity(position) else puw.quantity(position, "nm")
            pos_ang = puw.get_value(pos_q, to_unit="angstrom")
            resolved_position = [float(x) for x in pos_ang]
            resolved_atom_indices = None
        else:
            resolved_position = None
            resolved_atom_indices = self._resolve_anchor_atom_indices(
                selection, atom_indices=atom_indices
            )

        object_tag = tag or self._view._next_annotation_tag()  # noqa: SLF001
        resolved_layer_tag = layer_tag if layer_tag is not None else object_tag
        layer = self._ensure_layer(object_tag, layer_tag=layer_tag)

        options: dict[str, Any] = {
            "text": text,
            "tag": object_tag,
            "layer_tag": resolved_layer_tag,
            "atom_indices": resolved_atom_indices,
        }
        if resolved_position is not None:
            options["position"] = resolved_position
        if offset_mode != "camera":
            options["offset_mode"] = offset_mode
        offset_list = list(offset) if isinstance(offset, (list, tuple)) else [0.0, 0.0, 0.0]
        if offset_list != [0.0, 0.0, 0.0]:
            if offset_mode == "world":
                from ._pyunitwizard import puw
                offset_q = offset_list if puw.is_quantity(offset_list) else puw.quantity(offset_list, "nm")
                offset_ang = puw.get_value(offset_q, to_unit="angstrom")
                options["offset"] = [float(x) for x in offset_ang]
            else:
                options["offset"] = offset_list
        if leader_line:
            options["leader_line"] = True
        if leader_line_style != "dashed":
            options["leader_line_style"] = leader_line_style
        if label_style:
            options["style"] = dict(label_style)

        self._view._send({"op": "add_label", "tag": object_tag, "options": options})  # noqa: SLF001
        return layer

    @records_scene_history
    def add(self, *args, **kwargs) -> Layer:
        """Create an annotation; canonical manager alias for :meth:`add_annotation`."""
        return self.add_annotation(*args, **kwargs)

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def add_label(
        self,
        text: str,
        selection: Any = None,
        *,
        atom_indices: Any = None,
        group_index: Any = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Deprecated: use ``add_annotation()`` instead."""
        import warnings
        warnings.warn(
            "annotations.add_label() is deprecated; use add_annotation() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Resolve group_index here so add_annotation() doesn't need it.
        resolved_atom_indices = atom_indices
        if group_index is not None and atom_indices is None and selection is None:
            resolved_atom_indices = self._resolve_anchor_atom_indices(
                selection=None, atom_indices=None, group_index=group_index
            )
        return self.add_annotation(
            text=text,
            kind="label",
            selection=selection,
            atom_indices=resolved_atom_indices,
            tag=tag,
            layer_tag=layer_tag,
            skip_digestion=True,
        )

    @records_scene_history
    @signal(tags=["annotation", "selection"])
    @digest()
    def add_label_from_active_selection(
        self,
        text: str,
        *,
        tag: str | None = None,
        layer_tag: str | None = None,
        label_style: dict | None = None,
        position: tuple[float, float, float] | None = None,
        offset_mode: str = "camera",
        offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        leader_line: bool = False,
        leader_line_style: str = "dashed",
        skip_digestion: bool = False,
    ) -> Layer:
        """Add a persistent label from the last active selection or coordinates."""
        if position is not None:
            return self.add_annotation(
                text=text,
                position=position,
                offset_mode=offset_mode,
                offset=offset,
                leader_line=leader_line,
                leader_line_style=leader_line_style,
                tag=tag,
                layer_tag=layer_tag,
                label_style=label_style,
                skip_digestion=True,
            )

        event = self._view.get_last_active_selection_event()
        if event is None:
            raise ValueError("No active selection stored. Select an element before adding a label.")

        atom_indices = event.get("atom_indices") or []
        if len(atom_indices) == 0:
            raise ValueError("Active selection is empty. Select at least one atom before adding a label.")

        return self.add_annotation(
            text=text,
            atom_indices=[int(i) for i in atom_indices],
            offset_mode=offset_mode,
            offset=offset,
            leader_line=leader_line,
            leader_line_style=leader_line_style,
            tag=tag,
            layer_tag=layer_tag,
            label_style=label_style,
            skip_digestion=True,
        )

    @records_scene_history
    @signal(tags=["annotation", "visibility"])
    @digest()
    def show(self, tag: str, skip_digestion: bool = False) -> Layer:
        """Show the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.show(skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["annotation", "visibility"])
    @digest()
    def hide(self, tag: str, skip_digestion: bool = False) -> Layer:
        """Hide the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.hide(skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["annotation", "visibility"])
    @digest()
    def show_all(self, skip_digestion: bool = False) -> None:
        """Show every annotation as one scene-history operation."""
        for tag in self.tags(skip_digestion=True):
            self._require_annotation_layer(tag).show(skip_digestion=True)

    @records_scene_history
    @signal(tags=["annotation", "visibility"])
    @digest()
    def hide_all(self, skip_digestion: bool = False) -> None:
        """Hide every annotation as one scene-history operation."""
        for tag in self.tags(skip_digestion=True):
            self._require_annotation_layer(tag).hide(skip_digestion=True)

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        """Delete the annotation layer for ``tag``."""
        layer = self._require_annotation_layer(tag)
        layer.delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> Layer:
        """Rename an annotation layer tag."""
        layer = self._require_annotation_layer(tag)
        layer.set_tag(new_tag, skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def set_layer_tag(self, tag: str, new_layer_tag: str, skip_digestion: bool = False) -> Layer:
        """Move an annotation to a different grouping layer."""
        layer = self._require_annotation_layer(tag)
        layer.set_layer_tag(new_layer_tag, skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        """Clear annotations globally or remove one annotation layer by tag."""
        if tag is None:
            self._view.clear_decorations(shapes=False, styles=False, labels=True, skip_digestion=True)  # noqa: SLF001
            return
        self.delete(tag, skip_digestion=True)

    @records_scene_history
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

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def set_style(self, tag: str, style: dict[str, Any], skip_digestion: bool = False) -> Layer:
        """Update an annotation's visual style without recreating its identity."""
        layer = self._require_annotation_layer(tag)
        if not isinstance(style, dict):
            raise TypeError("set_style() requires a style dictionary.")
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
                    "atom_indices": list(record.get("atom_indices") or []),
                    "layer_tag": layer.layer_tag,
                    "style": dict(style),
                },
            }
        )
        return layer

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def set_anchor(
        self,
        tag: str,
        selection: Any = None,
        *,
        atom_indices: Any = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Reanchor an existing label to a different set of atoms.

        Parameters
        ----------
        tag
            Tag of the annotation to reanchor.
        selection
            MolSysMT selection string (e.g. ``'group_index==3'``).
        atom_indices
            Explicit atom indices list.  Takes priority over *selection*.
        """
        layer = self._require_annotation_layer(tag)
        resolved_atom_indices = self._resolve_anchor_atom_indices(
            selection, atom_indices=atom_indices
        )
        record = self.info(tag, skip_digestion=True)
        if not isinstance(record, dict):
            raise ValueError(f"No annotation record found for tag {tag!r}.")
        self._view._send(  # noqa: SLF001
            {
                "op": "update_label",
                "tag": tag,
                "broken": False,
                "broken_reason": None,
                "options": {
                    "tag": tag,
                    "text": record.get("text"),
                    "atom_indices": list(resolved_atom_indices),
                    "layer_tag": layer.layer_tag,
                    "style": dict(record.get("style") or {}),
                },
            }
        )
        layer.broken = False
        layer.broken_reason = None
        self._view._sync_annotation_summaries_runtime()  # noqa: SLF001
        return layer

    @records_scene_history
    @signal(tags=["annotation"])
    @digest()
    def set_group_index(self, tag: str, group_index: Any, skip_digestion: bool = False) -> Layer:
        """Deprecated: use ``set_anchor(selection='group_index==N')`` instead."""
        import warnings
        warnings.warn(
            "annotations.set_group_index() is deprecated; use set_anchor(selection='group_index==N') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        gi = int(group_index) if not isinstance(group_index, list) else int(group_index[0])
        return self.set_anchor(tag, selection=f"group_index=={gi}", skip_digestion=True)


__all__ = ["AnnotationsManager"]
