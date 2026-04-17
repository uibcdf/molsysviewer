from __future__ import annotations

from ..layers import GroupLayer, Shape


def normalize_new_shape_tag(view, tag: str) -> str:
    text = str(tag).strip()
    checker = getattr(view, "_assert_scene_object_tag_available", None)
    if callable(checker):
        return checker(text)
    if text == "":
        raise ValueError("Shape tag must be a non-empty string.")
    objects = getattr(view, "_scene_objects", {})
    if text in objects:
        raise ValueError(f"Shape tag {text!r} already exists.")
    return text


def register_shape_layer(view, tag: str, layer_tag: str | None = None, meta: dict | None = None) -> Shape:
    normalized_tag = normalize_new_shape_tag(view, tag)
    normalized_layer_tag = str(layer_tag).strip() if layer_tag is not None else normalized_tag
    if hasattr(view, "_ensure_layer_group"):
        view._ensure_layer_group(normalized_layer_tag, kind="shape")  # noqa: SLF001
    else:
        layers = getattr(view, "_layers", None)
        if layers is not None and normalized_layer_tag not in layers:
            layers[normalized_layer_tag] = GroupLayer(view, normalized_layer_tag, kind="shape", meta={})
    objects = getattr(view, "_scene_objects", None)
    if objects is None:
        objects = {}
        setattr(view, "_scene_objects", objects)
    shape = Shape(view, normalized_tag, layer_tag=normalized_layer_tag, meta=dict(meta or {}))
    objects[normalized_tag] = shape
    return shape
