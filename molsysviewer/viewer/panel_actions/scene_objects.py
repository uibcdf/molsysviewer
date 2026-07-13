from __future__ import annotations

from typing import Any, Mapping


def _tag(content: Mapping[str, Any], action: str) -> str:
    tag = content.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"{action} requires non-empty tag.")
    return tag.strip()


def add_label_from_selection(view: Any, content: Mapping[str, Any]) -> None:
    text = content.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("add_label_from_selection requires non-empty text.")
    raw_style = content.get("label_style")
    view.annotations.add_label_from_active_selection(
        text=text.strip(),
        label_style=dict(raw_style) if isinstance(raw_style, dict) else None,
        skip_digestion=True,
    )


def delete_annotation(view: Any, content: Mapping[str, Any]) -> None:
    view.annotations.delete(_tag(content, "delete_annotation"), skip_digestion=True)


def toggle_annotation_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_annotation_visibility")
    annotation = view.annotations.get(tag, skip_digestion=True)
    if annotation is None:
        raise ValueError(f"No annotation found with tag {tag!r}.")
    if view.annotations.info(tag, skip_digestion=True)["visible"]:
        annotation.hide(skip_digestion=True)
    else:
        annotation.show(skip_digestion=True)


def delete_shape(view: Any, content: Mapping[str, Any]) -> None:
    view.shapes.delete(_tag(content, "delete_shape"), skip_digestion=True)


def toggle_shape_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_shape_visibility")
    shape = view.shapes.get(tag, skip_digestion=True)
    if shape is None:
        raise ValueError(f"No shape found with tag {tag!r}.")
    if view.shapes.info(tag, skip_digestion=True)[0]["visible"]:
        shape.hide(skip_digestion=True)
    else:
        shape.show(skip_digestion=True)


def delete_measurement(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.delete(_tag(content, "delete_measurement"), skip_digestion=True)


def toggle_measurement_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_measurement_visibility")
    measurement = view.measurements.get(tag, skip_digestion=True)
    if measurement is None:
        raise ValueError(f"No measurement found with tag {tag!r}.")
    if view.measurements.info(tag)[0]["visible"]:
        measurement.hide(skip_digestion=True)
    else:
        measurement.show(skip_digestion=True)


def hide_measurement(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.hide(_tag(content, "hide_measurement"), skip_digestion=True)


HANDLERS = {
    "add_label_from_selection": add_label_from_selection,
    "delete_annotation": delete_annotation,
    "toggle_annotation_visibility": toggle_annotation_visibility,
    "delete_shape": delete_shape,
    "toggle_shape_visibility": toggle_shape_visibility,
    "delete_measurement": delete_measurement,
    "toggle_measurement_visibility": toggle_measurement_visibility,
    "hide_measurement": hide_measurement,
}
