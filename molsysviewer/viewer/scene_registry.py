from __future__ import annotations

from typing import Any
from smonitor import signal
from .._private.arg_digestion import digest
from ..layers import GroupLayer, Layer, SceneObject


class SceneRegistryMixin:
    def _unregister_layer(self, tag: str) -> None:
        self._layers.pop(tag, None)

    def _reregister_layer(self, old_tag: str, new_tag: str, layer: Layer) -> None:
        if old_tag in self._layers:
            self._layers.pop(old_tag, None)
        self._layers[new_tag] = layer

    def _unregister_scene_object(self, tag: str) -> None:
        status = getattr(self, "_shape_render_status", None)
        if isinstance(status, dict):
            status.pop(tag, None)
        obj = self._scene_objects.pop(tag, None)
        if obj is None:
            return
        layer_tag = getattr(obj, "layer_tag", None)
        if isinstance(layer_tag, str):
            layer = self._layers.get(layer_tag)
            if isinstance(layer, GroupLayer) and len(layer.members) == 0:
                self._layers.pop(layer_tag, None)

    def _reregister_scene_object(self, old_tag: str, new_tag: str, obj: SceneObject) -> None:
        if old_tag in self._scene_objects:
            self._scene_objects.pop(old_tag, None)
        self._scene_objects[new_tag] = obj

    def _sync_layer_group_hidden_state(self, layer_tag: str) -> None:
        layer = self._layers.get(layer_tag)
        if layer is None:
            return
        members = getattr(layer, "members", {})
        if len(members) == 0:
            layer._hidden = False  # noqa: SLF001
            return
        layer._hidden = all(getattr(item, "_hidden", False) for item in members.values())  # noqa: SLF001

    def _update_scene_object_history_layer_tag(self, tag: str, layer_tag: str) -> None:
        def rewrite(history: list[dict]) -> list[dict]:
            rewritten: list[dict] = []
            for item in history:
                if self._tag_from_message(item) != tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                else:
                    options = {}
                options["layer_tag"] = layer_tag
                updated["options"] = options
                rewritten.append(updated)
            return rewritten

        self._shape_history = rewrite(self._shape_history)
        self._annotation_history = rewrite(self._annotation_history)
        self._measurement_history = rewrite(self._measurement_history)

    def _set_scene_object_layer_tag(self, obj: SceneObject, new_layer_tag: str) -> None:
        text = str(new_layer_tag).strip()
        if text == "":
            raise ValueError("Layer tag must be a non-empty string.")
        old_layer_tag = getattr(obj, "layer_tag", None)
        if old_layer_tag == text:
            return
        self._ensure_layer_group(text, kind=getattr(obj, "kind", None))
        obj.layer_tag = text
        self._update_scene_object_history_layer_tag(obj.tag, text)
        if isinstance(old_layer_tag, str):
            old_layer = self._layers.get(old_layer_tag)
            if isinstance(old_layer, GroupLayer) and len(old_layer.members) == 0:
                self._layers.pop(old_layer_tag, None)
            else:
                self._sync_layer_group_hidden_state(old_layer_tag)
        self._sync_layer_group_hidden_state(text)

    def _cleanup_empty_layer_group(self, layer_tag: str) -> None:
        """Drop a grouping layer left empty (e.g. after a region moved out or
        was deleted), otherwise refresh its aggregate hidden state."""
        layer = self._layers.get(layer_tag)
        if isinstance(layer, GroupLayer) and len(layer.members) == 0:
            self._layers.pop(layer_tag, None)
        else:
            self._sync_layer_group_hidden_state(layer_tag)

    def _ensure_layer_group(self, layer_tag: str, *, kind: str | None = None) -> Layer:
        text = str(layer_tag).strip()
        if text == "":
            raise ValueError("Layer tag must be a non-empty string.")
        layer = self._layers.get(text)
        if layer is None:
            layer = GroupLayer(self, text, kind=kind or "layer", meta={})
            self._layers[text] = layer
        elif kind is not None:
            layer.kind = kind
        return layer

    def _move_or_rename_layer_group_for_object_tag_change(self, old_tag: str, new_tag: str, obj: SceneObject) -> None:
        old_layer = self._layers.get(old_tag)
        if isinstance(old_layer, GroupLayer) and len(old_layer.members) == 1 and obj.tag in old_layer.members:
            self._layers.pop(old_tag, None)
            old_layer.tag = new_tag
            self._layers[new_tag] = old_layer
            return
        self._ensure_layer_group(new_tag)

    def _assert_nonstructural_tag_available(self, tag: str, *, current_tag: str | None = None) -> str:
        text = str(tag).strip()
        if text == "":
            raise ValueError("Tag must be a non-empty string.")
        if current_tag is not None and text == current_tag:
            return text
        if text in self._layers:
            raise ValueError(f"Non-structural tag {text!r} already exists.")
        return text

    def _assert_scene_object_tag_available(self, tag: str, *, current_tag: str | None = None) -> str:
        text = str(tag).strip()
        if text == "":
            raise ValueError("Tag must be a non-empty string.")
        if current_tag is not None and text == current_tag:
            return text
        if text in self._scene_objects:
            raise ValueError(f"Scene-object tag {text!r} already exists.")
        return text

    @signal(tags=["layer"])
    @digest()
    def new_layer(
        self,
        *,
        tag: str | None = None,
        kind: str | None = None,
        skip_digestion: bool = False,
        **meta: Any,
    ) -> Layer:
        """Create a new layer (non-structural visual group)."""
        tag = tag or self._next_layer_tag()
        tag = self._assert_nonstructural_tag_available(tag)
        layer = Layer(self, tag, kind=kind, meta=meta)
        self._layers[tag] = layer
        layer._send_create()  # noqa: SLF001
        return layer


__all__ = ["SceneRegistryMixin"]
