"""Declared scientific overlay context and checked renderer layout metadata."""

import math
from copy import deepcopy
from numbers import Real


def overlay_requirements(view, scene):
    plots = [card for card in scene.get("trajectory_plots", []) if card.get("visible", True)]
    legend = view._scene_look.get("legend", {}).get("options", {})
    required = [{"kind": "trajectory_plot", "tag": str(card["tag"])} for card in plots]
    if legend.get("items"):
        required.append({"kind": "colour_legend", "tag": "colour-legend"})
    return required, deepcopy({"plots": plots, "legend": legend, "structure_indexing": "view-local zero-based"})


def overlay_revisions(view):
    # Public setters replace these detached messages; ordinary frame navigation
    # updates native playheads, not the stored scientific series. Retain the
    # messages themselves so a later allocation cannot reuse an old object's id.
    return tuple(view._scene_look.get(name) for name in ("trajectory_plot", "legend"))


def overlays_unchanged(view, revisions):
    return all(before is after for before, after in zip(revisions, overlay_revisions(view), strict=True))


def _record(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError("Invalid Movie composition record.")
    return value


def _number(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError("Movie composition requires finite numeric dimensions.")
    return value


def _rect(value, width, height):
    value = _record(value, ("x", "y", "width", "height"))
    for number in value.values():
        _number(number)
    if (
        value["width"] <= 0
        or value["height"] <= 0
        or value["x"] < -1
        or value["y"] < -1
        or value["x"] + value["width"] > width + 1
        or value["y"] + value["height"] > height + 1
    ):
        raise ValueError("Movie composition rectangle exceeds its viewport.")
    return value


def checked_composition(value, required, width, height):
    value = _record(value, ("schema", "viewport", "placement", "unit", "layers"))
    if (
        value["schema"] != "molsysviewer.movie_composition@1"
        or value["placement"] != "normalized-centres-uniform-scale@1"
        or value["unit"] != "px"
    ):
        raise ValueError("Unsupported Movie composition contract.")
    viewport = _record(value["viewport"], ("width", "height", "unit"))
    if viewport["unit"] != "css-px" or any(_number(viewport[key]) <= 0 for key in ("width", "height")):
        raise ValueError("Movie composition source viewport requires positive CSS-pixel dimensions.")
    if not isinstance(value["layers"], list) or len(value["layers"]) != len(required) or len(required) > 32:
        raise ValueError("Movie composition does not contain every declared overlay.")
    expected = {(row["kind"], row["tag"]) for row in required}
    seen = set()
    scale = min(width / viewport["width"], height / viewport["height"])
    for layer in value["layers"]:
        layer = _record(layer, ("kind", "tag", "bounds", "output", "rendering"))
        rendering = _record(layer["rendering"], ("opacity", "view_box"))
        if not 0 <= _number(rendering["opacity"]) <= 1:
            raise ValueError("Movie overlay opacity must be in [0, 1].")
        box = _record(rendering["view_box"], ("width", "height"))
        if any(_number(value) <= 0 for value in box.values()):
            raise ValueError("Movie overlay SVG view box must be positive.")
        if not isinstance(layer["kind"], str) or not isinstance(layer["tag"], str):
            raise ValueError("Invalid Movie overlay identity.")
        identity = layer["kind"], layer["tag"]
        if identity not in expected or identity in seen:
            raise ValueError("Unexpected or duplicate Movie overlay identity.")
        seen.add(identity)
        source = _rect(layer["bounds"], viewport["width"], viewport["height"])
        output = _rect(layer["output"], width, height)
        projected = {"width": source["width"] * scale, "height": source["height"] * scale}
        for axis, extent in (("x", "width"), ("y", "height")):
            limit = width if axis == "x" else height
            projected[axis] = (source[axis] + source[extent] / 2) / viewport[extent] * limit - projected[extent] / 2
        if any(not math.isclose(output[key], projected[key], rel_tol=1e-10, abs_tol=1e-7) for key in projected):
            raise ValueError("Movie overlay placement does not match its declared projection.")
    return deepcopy(value)
