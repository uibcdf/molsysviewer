from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from ..._pyunitwizard import puw
from ...figures import FigureSpec


def _section(view: Any, content: Mapping[str, Any], action: str):
    tag = content.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"{action} requires a non-empty section tag.")
    section = view._scene_objects.get(("section", tag.strip()))
    if section is None:
        raise ValueError(f"No section found with tag {tag!r}.")
    return section


def _vector(content: Mapping[str, Any], key: str) -> list[float]:
    raw = content.get(key)
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise ValueError(f"{key} must be a 3-element vector.")
    return [float(value) for value in raw]


def _point_quantity(content: Mapping[str, Any]):
    raw = content.get("point")
    if isinstance(raw, Mapping):
        magnitude = raw.get("magnitude")
        unit = raw.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("point.unit must be a non-empty unit string.")
        if not isinstance(magnitude, (list, tuple)) or len(magnitude) != 3:
            raise ValueError("point.magnitude must be a 3-element vector.")
        return puw.quantity([float(value) for value in magnitude], unit.strip())
    return puw.quantity(_vector(content, "point"), "nm")


def toggle_background(view: Any, content: Mapping[str, Any]) -> None:
    if "mode" not in content:
        view._send({"op": "toggle_background"})
        return
    view.scene.set_background(content["mode"])


def reset_view(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.camera.reset(skip_digestion=True)


def toggle_spin(view: Any, content: Mapping[str, Any]) -> None:
    if "enabled" not in content:
        view._send({"op": "toggle_spin"})
        return
    view.scene.spin(enabled=bool(content["enabled"]))


def toggle_swing(view: Any, content: Mapping[str, Any]) -> None:
    if "enabled" not in content:
        view._send({"op": "toggle_swing"})
        return
    view.scene.swing(enabled=bool(content["enabled"]))


def set_camera_mode(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.set_projection(str(content.get("mode") or "perspective"))


def set_fog(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.set_fog(
        enabled=bool(content.get("enable", True)),
        intensity=float(content.get("intensity", 0.15)),
    )


def create_section_from_selection(view: Any, content: Mapping[str, Any]) -> None:
    if view._molsys is None:
        raise ValueError("create_section_from_selection requires a loaded molecular system.")
    atom_indices = list(view.active_selection.atom_indices)
    if not atom_indices:
        raise ValueError("create_section_from_selection requires a non-empty active selection.")

    from molsysmt.structure import get_center

    center = get_center(
        view._molsys,
        selection=atom_indices,
        structure_indices=[view.current_structure_index],
        syntax="MolSysMT",
        skip_digestion=True,
    )
    center_nm = np.squeeze(np.asarray(puw.get_value(center, to_unit="nm"), dtype=float))
    if center_nm.ndim == 2:
        center_nm = center_nm.mean(axis=0)

    raw_forward = content.get("camera_forward")
    normal = (
        np.asarray(raw_forward, dtype=float)
        if isinstance(raw_forward, (list, tuple)) and len(raw_forward) == 3
        else np.asarray([0.0, 0.0, -1.0], dtype=float)
    )
    norm = float(np.linalg.norm(normal))
    if norm < 1e-10:
        raise ValueError("camera_forward must be a non-zero vector.")
    view.scene.add_section(
        point=puw.quantity(center_nm.tolist(), "nm"),
        normal=(normal / norm).tolist(),
    )


def set_section_visibility(view: Any, content: Mapping[str, Any]) -> None:
    section = _section(view, content, "set_section_visibility")
    visible = content.get("visible")
    hidden = content.get("hidden")
    if visible is not None:
        target_visible = bool(visible)
    elif hidden is not None:
        target_visible = not bool(hidden)
    else:
        target_visible = not section.visible
    (section.show if target_visible else section.hide)(skip_digestion=True)


def set_section_point(view: Any, content: Mapping[str, Any]) -> None:
    _section(view, content, "set_section_point").set_point(_point_quantity(content))


def set_section_normal(view: Any, content: Mapping[str, Any]) -> None:
    _section(view, content, "set_section_normal").set_normal(_vector(content, "normal"))


def set_section_invert(view: Any, content: Mapping[str, Any]) -> None:
    _section(view, content, "set_section_invert").set_invert(bool(content.get("invert", False)))


def remove_section(view: Any, content: Mapping[str, Any]) -> None:
    _section(view, content, "remove_section").delete(skip_digestion=True)


def set_figure_spec(view: Any, content: Mapping[str, Any]) -> None:
    preset = str(content.get("figure_preset") or "publication-light")
    background = "dark" if "dark" in preset else "white"
    view.set_figure_spec(
        FigureSpec(
            preset=preset,
            scale=float(content.get("figure_scale", 2.0)),
            background=background,
        ),
        skip_digestion=True,
    )


def export_html(view: Any, content: Mapping[str, Any]) -> None:
    del content
    if callable(getattr(view.widget, "publish_download", None)):
        view._request_remote_html_download()
    else:
        view.export.html("molsysviewer_export.html")


def download_image(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view._request_remote_image_download()


HANDLERS = {
    "reset_view": reset_view,
    "toggle_background": toggle_background,
    "toggle_spin": toggle_spin,
    "toggle_swing": toggle_swing,
    "set_camera_mode": set_camera_mode,
    "set_fog": set_fog,
    "create_section_from_selection": create_section_from_selection,
    "set_section_visibility": set_section_visibility,
    "set_section_point": set_section_point,
    "set_section_normal": set_section_normal,
    "set_section_invert": set_section_invert,
    "remove_section": remove_section,
    "set_figure_spec": set_figure_spec,
    "download_image": download_image,
    "export_html": export_html,
}
