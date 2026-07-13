from __future__ import annotations

from typing import Any, Mapping

import molsysmt as msm


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


def _active_measurement_picks(view: Any) -> list[list[int]]:
    if view.molsys is None:
        raise ValueError("A molecular system must be loaded before creating a measurement.")
    picks = [
        list(msm.select(
            view.molsys,
            selection=f"group_index=={group_index}",
            syntax="MolSysMT",
        ))
        for group_index in view.active_selection.group_indices
    ]
    return [pick for pick in picks if pick]


def create_measurement(view: Any, content: Mapping[str, Any]) -> None:
    kind = content.get("kind")
    required = {"distance": 2, "angle": 3, "dihedral": 4}
    if kind not in required:
        raise ValueError("create_measurement requires kind distance, angle, or dihedral.")
    picks = _active_measurement_picks(view)
    if len(picks) != required[kind]:
        raise ValueError(
            f"{kind} requires {required[kind]} selected endpoints; received {len(picks)}."
        )
    getattr(view.measurements, f"add_{kind}")(*picks, skip_digestion=True)


def rename_measurement(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_measurement requires non-empty new_tag.")
    view.measurements.set_tag(
        _tag(content, "rename_measurement"), new_tag.strip(), skip_digestion=True
    )


def set_measurement_layer(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "set_measurement_layer")
    layer = content.get("layer")
    view.measurements.set_layer_tag(
        tag,
        tag if layer is None or str(layer).strip() == "" else str(layer).strip(),
        skip_digestion=True,
    )


def _set_all_measurements_visibility(view: Any, visible: bool) -> None:
    for tag in view.measurements.tags(skip_digestion=True):
        method = view.measurements.show if visible else view.measurements.hide
        method(tag, skip_digestion=True)


def show_all_measurements(view: Any, _content: Mapping[str, Any]) -> None:
    _set_all_measurements_visibility(view, True)


def hide_all_measurements(view: Any, _content: Mapping[str, Any]) -> None:
    _set_all_measurements_visibility(view, False)


def clear_measurements(view: Any, _content: Mapping[str, Any]) -> None:
    view.measurements.clear(skip_digestion=True)


def set_measurement_endpoint_policy(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.set_endpoint_policy(
        str(content.get("policy") or ""), skip_digestion=True
    )


def set_measurement_representative_atom(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.set_representative_atom(
        str(content.get("target") or ""),
        str(content.get("atom_name") or ""),
        skip_digestion=True,
    )


def request_measurement_series(view: Any, content: Mapping[str, Any]) -> None:
    request_id = content.get("request_id")
    view._send_runtime_only(  # noqa: SLF001
        view._measurement_series_payload(  # noqa: SLF001
            _tag(content, "request_measurement_series"),
            int(request_id) if request_id is not None else None,
        )
    )


HANDLERS = {
    "add_label_from_selection": add_label_from_selection,
    "delete_annotation": delete_annotation,
    "toggle_annotation_visibility": toggle_annotation_visibility,
    "delete_shape": delete_shape,
    "toggle_shape_visibility": toggle_shape_visibility,
    "delete_measurement": delete_measurement,
    "toggle_measurement_visibility": toggle_measurement_visibility,
    "hide_measurement": hide_measurement,
    "create_measurement": create_measurement,
    "rename_measurement": rename_measurement,
    "set_measurement_layer": set_measurement_layer,
    "show_all_measurements": show_all_measurements,
    "hide_all_measurements": hide_all_measurements,
    "clear_measurements": clear_measurements,
    "set_measurement_endpoint_policy": set_measurement_endpoint_policy,
    "set_measurement_representative_atom": set_measurement_representative_atom,
    "request_measurement_series": request_measurement_series,
}
