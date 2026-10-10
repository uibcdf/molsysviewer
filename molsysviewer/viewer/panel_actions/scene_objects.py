from __future__ import annotations

from math import isfinite
from numbers import Integral, Real
from typing import Any, Mapping

import molsysmt as msm
import numpy as np

from ... import pyunitwizard as puw
from ...shapes import SHAPE_STYLE_CAPABILITIES


def _tag(content: Mapping[str, Any], action: str) -> str:
    tag = content.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"{action} requires non-empty tag.")
    return tag.strip()


def _requested_hidden(content: Mapping[str, Any], visible: bool) -> bool:
    """Explicit contextual Hide is idempotent; Studio retains its toggle."""
    hidden = content.get("hidden", visible)
    if not isinstance(hidden, bool):
        raise ValueError("hidden must be a boolean.")
    return hidden


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


def create_annotation(view: Any, content: Mapping[str, Any]) -> None:
    text = content.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("create_annotation requires non-empty text.")
    raw_style = content.get("label_style")
    position = content.get("position")
    if position is not None:
        if (
            not isinstance(position, (list, tuple))
            or len(position) != 3
            or any(isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) for value in position)
        ):
            raise ValueError("Annotation coordinates require three finite numbers in nm.")
    offset_mode = content.get("offset_mode", "camera")
    offset = content.get("offset", (0.0, 0.0, 0.0))
    leader_line = content.get("leader_line", False)
    leader_line_style = content.get("leader_line_style", "dashed")
    atom_indices = content.get("atom_indices")

    if atom_indices is not None or position is not None:
        view.annotations.add(
            text=text.strip(),
            atom_indices=atom_indices,
            position=position,
            offset_mode=offset_mode,
            offset=offset,
            leader_line=leader_line,
            leader_line_style=leader_line_style,
            label_style=dict(raw_style) if isinstance(raw_style, dict) else None,
            skip_digestion=True,
        )
    else:
        view.annotations.add_label_from_active_selection(
            text=text.strip(),
            label_style=dict(raw_style) if isinstance(raw_style, dict) else None,
            offset_mode=offset_mode,
            offset=offset,
            leader_line=leader_line,
            leader_line_style=leader_line_style,
            skip_digestion=True,
        )


def delete_annotation(view: Any, content: Mapping[str, Any]) -> None:
    view.annotations.delete(_tag(content, "delete_annotation"), skip_digestion=True)


def toggle_annotation_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_annotation_visibility")
    annotation = view.annotations.get(tag, skip_digestion=True)
    if annotation is None:
        raise ValueError(f"No annotation found with tag {tag!r}.")
    if _requested_hidden(content, view.annotations.info(tag, skip_digestion=True)["visible"]):
        annotation.hide(skip_digestion=True)
    else:
        annotation.show(skip_digestion=True)


def set_annotation_text(view: Any, content: Mapping[str, Any]) -> None:
    text = content.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("set_annotation_text requires non-empty text.")
    view.annotations.set_text(_tag(content, "set_annotation_text"), text.strip(), skip_digestion=True)


def rename_annotation(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_annotation requires non-empty new_tag.")
    view.annotations.set_tag(_tag(content, "rename_annotation"), new_tag.strip(), skip_digestion=True)


def set_annotation_layer(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "set_annotation_layer")
    layer = content.get("layer")
    view.annotations.set_layer_tag(
        tag,
        tag if layer is None or not str(layer).strip() else str(layer).strip(),
        skip_digestion=True,
    )


def reanchor_annotation(view: Any, content: Mapping[str, Any]) -> None:
    atom_indices = list(view.active_selection.atom_indices)
    if not atom_indices:
        raise ValueError("reanchor_annotation requires a non-empty active selection.")
    view.annotations.set_anchor(
        _tag(content, "reanchor_annotation"),
        atom_indices=atom_indices,
        skip_digestion=True,
    )


def set_annotation_style(view: Any, content: Mapping[str, Any]) -> None:
    style = content.get("style")
    if not isinstance(style, Mapping):
        raise ValueError("set_annotation_style requires a style mapping.")
    view.annotations.set_style(_tag(content, "set_annotation_style"), dict(style), skip_digestion=True)


def show_all_annotations(view: Any, _content: Mapping[str, Any]) -> None:
    view.annotations.show_all(skip_digestion=True)


def hide_all_annotations(view: Any, _content: Mapping[str, Any]) -> None:
    view.annotations.hide_all(skip_digestion=True)


def clear_annotations(view: Any, _content: Mapping[str, Any]) -> None:
    view.annotations.clear(skip_digestion=True)


def delete_shape(view: Any, content: Mapping[str, Any]) -> None:
    view.shapes.delete(_tag(content, "delete_shape"), skip_digestion=True)


def toggle_shape_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_shape_visibility")
    shape = view.shapes.get(tag, skip_digestion=True)
    if shape is None:
        raise ValueError(f"No shape found with tag {tag!r}.")
    if _requested_hidden(content, view.shapes.info(tag, skip_digestion=True)["visible"]):
        view.shapes.hide(tag, skip_digestion=True)
    else:
        view.shapes.show(tag, skip_digestion=True)


def _shape_and_op(view: Any, content: Mapping[str, Any], action: str):
    tag = _tag(content, action)
    shape = view.shapes.get(tag, skip_digestion=True)
    record = view.shapes.info(tag, skip_digestion=True)
    if shape is None:
        raise ValueError(f"No shape found with tag {tag!r}.")
    return shape, str(record.get("op"))


def _shape_for_capability(view: Any, content: Mapping[str, Any], action: str, capability: str):
    shape, op = _shape_and_op(view, content, action)
    supported = SHAPE_STYLE_CAPABILITIES.get(str(op))
    if supported is None or capability not in supported:
        raise ValueError(f"{action} is not supported for shape op {op!r}.")
    return shape


def rename_shape(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_shape requires non-empty new_tag.")
    view.shapes.set_tag(_tag(content, "rename_shape"), new_tag.strip(), skip_digestion=True)


def set_shape_layer(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "set_shape_layer")
    layer = content.get("layer")
    view.shapes.set_layer_tag(
        tag,
        tag if layer is None or not str(layer).strip() else str(layer).strip(),
        skip_digestion=True,
    )


def focus_shape(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "focus_shape")
    shape = view.shapes.get(tag, skip_digestion=True)
    if shape is None:
        raise ValueError(f"No shape found with tag {tag!r}.")
    shape.focus()


def set_shape_color(view: Any, content: Mapping[str, Any]) -> None:
    color = content.get("color")
    if not isinstance(color, str) or not color.strip():
        raise ValueError("set_shape_color requires a color string.")
    _, op = _shape_and_op(view, content, "set_shape_color")
    capability = "set_color" if op == "add_sphere" else "set_colors"
    shape = _shape_for_capability(view, content, "set_shape_color", capability)
    getattr(shape, capability)(color.strip(), skip_digestion=True)


def set_shape_alpha(view: Any, content: Mapping[str, Any]) -> None:
    alpha = content.get("alpha")
    if not isinstance(alpha, Real) or not isfinite(float(alpha)) or not 0.0 <= float(alpha) <= 1.0:
        raise ValueError("set_shape_alpha requires alpha between 0 and 1.")
    shape = _shape_for_capability(view, content, "set_shape_alpha", "set_alpha")
    shape.set_alpha(float(alpha), skip_digestion=True)


def _shape_length(content: Mapping[str, Any], action: str):
    value = content.get("radius")
    if not isinstance(value, Mapping):
        raise ValueError(f"{action} requires radius with magnitude and unit.")
    magnitude = value.get("magnitude")
    unit = value.get("unit")
    if not isinstance(magnitude, Real) or not isfinite(float(magnitude)) or float(magnitude) <= 0:
        raise ValueError(f"{action} requires a positive finite magnitude.")
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError(f"{action} requires an explicit unit.")
    return puw.quantity(float(magnitude), unit.strip())


def set_shape_radius(view: Any, content: Mapping[str, Any]) -> None:
    _, op = _shape_and_op(view, content, "set_shape_radius")
    capability = "set_radius" if op == "add_sphere" else "set_radii"
    shape = _shape_for_capability(view, content, "set_shape_radius", capability)
    getattr(shape, capability)(_shape_length(content, "set_shape_radius"), skip_digestion=True)


def set_shape_scale(view: Any, content: Mapping[str, Any]) -> None:
    kind = content.get("kind")
    capability = {
        "radius_scale": "set_radius_scale",
        "length_scale": "set_length_scale",
    }.get(kind)
    if capability is None:
        raise ValueError("set_shape_scale requires kind radius_scale or length_scale.")
    value = content.get("value")
    if not isinstance(value, Real) or not isfinite(float(value)) or float(value) <= 0:
        raise ValueError("set_shape_scale requires a positive finite value.")
    shape = _shape_for_capability(view, content, "set_shape_scale", capability)
    getattr(shape, capability)(float(value), skip_digestion=True)


def show_all_shapes(view: Any, _content: Mapping[str, Any]) -> None:
    view.shapes.show_all(skip_digestion=True)


def hide_all_shapes(view: Any, _content: Mapping[str, Any]) -> None:
    view.shapes.hide_all(skip_digestion=True)


def clear_shapes(view: Any, _content: Mapping[str, Any]) -> None:
    view.shapes.clear(skip_digestion=True)


def delete_measurement(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.delete(_tag(content, "delete_measurement"), skip_digestion=True)


def toggle_measurement_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "toggle_measurement_visibility")
    measurement = view.measurements.get(tag, skip_digestion=True)
    if measurement is None:
        raise ValueError(f"No measurement found with tag {tag!r}.")
    if view.measurements.info(tag)["visible"]:
        measurement.hide(skip_digestion=True)
    else:
        measurement.show(skip_digestion=True)


def hide_measurement(view: Any, content: Mapping[str, Any]) -> None:
    view.measurements.hide(_tag(content, "hide_measurement"), skip_digestion=True)


def focus_measurement(view: Any, content: Mapping[str, Any]) -> None:
    tag = _tag(content, "focus_measurement")
    measurement = view.measurements.get(tag, skip_digestion=True)
    if measurement is None:
        raise ValueError(f"No measurement found with tag {tag!r}.")
    measurement.focus()


def _active_measurement_picks(view: Any) -> list[list[int]]:
    if view.molsys is None:
        raise ValueError("A molecular system must be loaded before creating a measurement.")
    picks = [
        list(
            msm.select(
                view.molsys,
                selection=f"group_index=={group_index}",
                syntax="MolSysMT",
            )
        )
        for group_index in view.active_selection.group_indices
    ]
    return [pick for pick in picks if pick]


def create_measurement(view: Any, content: Mapping[str, Any]) -> None:
    kind = content.get("kind")
    required = {"distance": 2, "angle": 3, "dihedral": 4}
    if kind not in required:
        raise ValueError("create_measurement requires kind distance, angle, or dihedral.")
    picks = content.get("picks")
    if picks is None:
        picks = _active_measurement_picks(view)
    if len(picks) != required[kind]:
        raise ValueError(f"{kind} requires {required[kind]} selected endpoints; received {len(picks)}.")
    endpoint_policy = content.get("endpoint_policy")
    tag = content.get("tag")
    kwargs = {"skip_digestion": True}
    if endpoint_policy is not None:
        kwargs["endpoint_policy"] = endpoint_policy
    if tag is not None:
        kwargs["tag"] = tag
    getattr(view.measurements, f"add_{kind}")(*picks, **kwargs)


def rename_measurement(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_measurement requires non-empty new_tag.")
    view.measurements.set_tag(_tag(content, "rename_measurement"), new_tag.strip(), skip_digestion=True)


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
    view.measurements.set_endpoint_policy(str(content.get("policy") or ""), skip_digestion=True)


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


def _shape_point_nm(view: Any, atoms: Any, coordinates: Any) -> list[float]:
    """Resolve an explicit point or a geometric center in the visible structure."""
    if atoms is not None:
        if (
            not isinstance(atoms, (list, tuple))
            or not atoms
            or any(isinstance(index, bool) or not isinstance(index, Integral) for index in atoms)
        ):
            raise ValueError("Stage a nonempty atom selection for each anchor.")
        n_atoms = msm.get(view.molsys, element="system", n_atoms=True, skip_digestion=True)
        if any(index < 0 or index >= n_atoms for index in atoms):
            raise ValueError("An anchor refers to atoms outside the current system.")
        values = msm.get(
            view.molsys,
            element="atom",
            selection=list(dict.fromkeys(atoms)),
            coordinates=True,
            structure_indices=view.player.index,
            skip_digestion=True,
        )
        point = np.asarray(puw.get_value(values, to_unit="nm"), dtype=float).reshape(-1, 3).mean(axis=0)
    else:
        if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 3:
            raise ValueError("Stage each anchor or enter its three coordinates in nm.")
        if any(isinstance(value, bool) or not isinstance(value, Real) for value in coordinates):
            raise ValueError("Anchor coordinates must be finite numbers in nm.")
        point = np.asarray(coordinates, dtype=float)
    if not np.isfinite(point).all():
        raise ValueError("Anchor coordinates must be finite numbers in nm.")
    return point.tolist()


def create_shape(view: Any, content: Mapping[str, Any]) -> None:
    shape_type = str(content.get("shape_type", "add_sphere")).strip()
    raw_tag = content.get("tag")
    tag = str(raw_tag).strip() if isinstance(raw_tag, str) and raw_tag.strip() else None

    raw_color = content.get("color", "#3b82f6")
    color = str(raw_color).strip() if isinstance(raw_color, str) and raw_color.strip() else "#3b82f6"

    raw_alpha = content.get("alpha", 0.8)
    raw_radius = content.get("radius", 0.15)
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in (raw_alpha, raw_radius)):
        raise ValueError("Radius and opacity must be numerical scalars.")
    alpha, radius_val = float(raw_alpha), float(raw_radius)
    if not isfinite(radius_val) or radius_val <= 0 or not isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("Radius must be finite and positive; opacity must be between 0 and 1.")
    radius_q = puw.quantity(radius_val, "nm")

    atom_indices = content.get("atom_indices")
    atom_indices_2 = content.get("atom_indices_2")
    coordinates = content.get("coordinates")
    coordinates_2 = content.get("coordinates_2")

    if shape_type in ("add_sphere", "sphere"):
        point = _shape_point_nm(view, atom_indices, coordinates)
        if atom_indices is not None:
            view.shapes.add_sphere(
                atom_indices=atom_indices,
                radius=radius_q,
                color=color,
                alpha=alpha,
                tag=tag,
                skip_digestion=True,
            )
        else:
            center_q = puw.quantity(point, "nm")
            view.shapes.add_sphere(
                center=center_q,
                radius=radius_q,
                color=color,
                alpha=alpha,
                tag=tag,
                skip_digestion=True,
            )
    elif shape_type in ("add_links", "add_network_links", "link"):
        p1 = _shape_point_nm(view, atom_indices, coordinates)
        p2 = _shape_point_nm(view, atom_indices_2, coordinates_2)
        if p1 == p2:
            raise ValueError("A link needs two distinct anchor centers.")
        view.shapes.add_links(
            coordinate_pairs=puw.quantity([[p1, p2]], "nm"),
            radius=radius_q,
            color=color,
            alpha=alpha,
            tag=tag,
            skip_digestion=True,
        )
    elif shape_type in ("add_displacement_vectors", "displacement_vectors"):
        p1 = _shape_point_nm(view, atom_indices, coordinates)
        p2 = _shape_point_nm(view, atom_indices_2, coordinates_2)
        if p1 == p2:
            raise ValueError("A displacement arrow needs two distinct anchor centers.")
        view.shapes.add_displacement_vectors(
            origins=puw.quantity([p1], "nm"),
            vectors=puw.quantity([[b - a for a, b in zip(p1, p2)]], "nm"),
            radius_scale=radius_val,
            tag=tag,
            skip_digestion=True,
        )
    elif shape_type in ("add_pocket_surface", "pocket_surface"):
        if atom_indices is not None:
            _shape_point_nm(view, atom_indices, None)
            view.shapes.add_pocket_surface(
                atom_indices=atom_indices,
                alpha=alpha,
                tag=tag,
                skip_digestion=True,
            )
        else:
            raise ValueError("Stage the atoms defining the pocket surface.")
    elif shape_type in ("add_hbonds", "hbonds"):
        raise ValueError("Use Interactions to calculate hydrogen bonds and create a visual set.")
    elif shape_type in ("add_rings", "rings"):
        raise ValueError("Use the ring geometry guide to supply centers, normals and radii.")
    else:
        raise ValueError("This shape type is not available for Studio creation.")


HANDLERS = {
    "add_label_from_selection": add_label_from_selection,
    "create_annotation": create_annotation,
    "delete_annotation": delete_annotation,
    "toggle_annotation_visibility": toggle_annotation_visibility,
    "set_annotation_text": set_annotation_text,
    "rename_annotation": rename_annotation,
    "set_annotation_layer": set_annotation_layer,
    "reanchor_annotation": reanchor_annotation,
    "set_annotation_style": set_annotation_style,
    "show_all_annotations": show_all_annotations,
    "hide_all_annotations": hide_all_annotations,
    "clear_annotations": clear_annotations,
    "create_shape": create_shape,
    "delete_shape": delete_shape,
    "toggle_shape_visibility": toggle_shape_visibility,
    "rename_shape": rename_shape,
    "set_shape_layer": set_shape_layer,
    "focus_shape": focus_shape,
    "set_shape_color": set_shape_color,
    "set_shape_alpha": set_shape_alpha,
    "set_shape_radius": set_shape_radius,
    "set_shape_scale": set_shape_scale,
    "show_all_shapes": show_all_shapes,
    "hide_all_shapes": hide_all_shapes,
    "clear_shapes": clear_shapes,
    "delete_measurement": delete_measurement,
    "toggle_measurement_visibility": toggle_measurement_visibility,
    "hide_measurement": hide_measurement,
    "focus_measurement": focus_measurement,
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
