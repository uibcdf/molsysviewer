from __future__ import annotations

from typing import Any, Mapping

from ...figures import FigureSpec


def toggle_background(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.set_background(content.get("mode", "dark"))


def toggle_spin(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.spin(enabled=bool(content.get("enabled", True)))


def toggle_swing(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.swing(enabled=bool(content.get("enabled", True)))


def set_camera_mode(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.set_projection(str(content.get("mode") or "perspective"))


def set_fog(view: Any, content: Mapping[str, Any]) -> None:
    view.scene.set_fog(
        enabled=bool(content.get("enable", True)),
        intensity=float(content.get("intensity", 0.15)),
    )


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
    view.export.html("molsysviewer_export.html")


HANDLERS = {
    "toggle_background": toggle_background,
    "toggle_spin": toggle_spin,
    "toggle_swing": toggle_swing,
    "set_camera_mode": set_camera_mode,
    "set_fog": set_fog,
    "set_figure_spec": set_figure_spec,
    "export_html": export_html,
}
