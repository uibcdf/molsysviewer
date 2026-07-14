from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .colors import normalize_color
from .scene_history import records_scene_history

if TYPE_CHECKING:
    from .layers import Section


class SceneManager:
    """Programmatic control over viewer scene settings.

    Accessible via ``view.scene``.

    Examples
    --------
    >>> view.scene.set_background("dark")
    >>> view.scene.set_background("#1a1a2e")
    >>> view.scene.spin(enabled=True, speed=0.15)
    >>> view.scene.set_fog(enabled=True, intensity=0.6)
    >>> view.scene.set_lighting(ambient=0.4, diffuse=0.8)
    >>> view.scene.set_projection("orthographic")
    """

    def __init__(self, view: Any) -> None:
        self._view = view

    # ── Background ────────────────────────────────────────────────────────

    def set_background(self, color: Any = "dark") -> None:
        """Set the canvas background.

        Parameters
        ----------
        color
            Background color. Accepts:

            - ``"light"`` or ``"dark"`` — toggle between the built-in presets.
            - A hex string: ``"#f0f0f0"`` or ``"#fff"``.
            - An integer (0xRRGGBB): ``0x1a1a2e``.
            - A named CSS/Mol* color: ``"skyblue"``, ``"white"``, etc.
        """
        if isinstance(color, str) and color.strip().lower() in ("light", "dark"):
            self._view._send({"op": "toggle_background", "mode": color.strip().lower()})  # noqa: SLF001
            return
        color_int = normalize_color(color)
        self._view._send({"op": "set_background_color", "color": color_int})  # noqa: SLF001

    def spin(self, enabled: bool = True, speed: float | None = None) -> None:
        """Enable or disable continuous rotation around the vertical axis.

        Parameters
        ----------
        enabled
            ``True`` to start spinning, ``False`` to stop.
        speed
            Rotation speed (Mol* units; default ~0.1). Ignored when *enabled* is ``False``.
        """
        msg: dict = {"op": "toggle_spin", "enable": bool(enabled)}
        if speed is not None:
            msg["speed"] = float(speed)
        self._view._send(msg)  # noqa: SLF001

    def swing(self, enabled: bool = True, speed: float | None = None) -> None:
        """Enable or disable oscillating rock motion.

        Parameters
        ----------
        enabled
            ``True`` to start swinging, ``False`` to stop.
        speed
            Oscillation speed (Mol* units; default ~0.25). Ignored when *enabled* is ``False``.
        """
        msg: dict = {"op": "toggle_swing", "enable": bool(enabled)}
        if speed is not None:
            msg["speed"] = float(speed)
        self._view._send(msg)  # noqa: SLF001

    def set_fog(self, enabled: bool = True, intensity: float = 0.15) -> None:
        """Enable or disable depth fog.

        Parameters
        ----------
        enabled
            ``True`` to enable fog, ``False`` to disable.
        intensity
            Fog intensity between 0.0 and 1.0 (default 0.15, matching Mol*'s
            built-in default of 15/100). Ignored when *enabled* is ``False``.
        """
        self._view._send({"op": "set_fog", "enable": bool(enabled), "intensity": float(intensity)})  # noqa: SLF001

    # ── Lighting ──────────────────────────────────────────────────────────

    def set_lighting(
        self,
        ambient: float | None = None,
        diffuse: float | None = None,
        specular: float | None = None,
    ) -> None:
        """Adjust scene lighting components.

        Parameters
        ----------
        ambient
            Ambient (fill) light intensity, 0.0–1.0.
        diffuse
            Diffuse (directional) light intensity, 0.0–1.0.
        specular
            Specular highlight intensity, 0.0–1.0.  Not directly exposed by
            Mol* as a separate channel; mapped to ``lightIntensity`` alongside
            *diffuse* if both are provided.

        At least one parameter must be given.
        """
        if ambient is None and diffuse is None and specular is None:
            raise ValueError("At least one of ambient, diffuse, or specular must be provided.")
        msg: dict = {"op": "set_lighting"}
        if ambient is not None:
            msg["ambient"] = float(ambient)
        if diffuse is not None:
            msg["diffuse"] = float(diffuse)
        if specular is not None:
            msg["specular"] = float(specular)
        self._view._send(msg)  # noqa: SLF001

    # ── Projection ────────────────────────────────────────────────────────

    def set_projection(self, mode: str) -> None:
        """Switch between perspective and orthographic projection.

        Parameters
        ----------
        mode
            ``"perspective"`` or ``"orthographic"``.

        This delegates to ``view.camera.set_mode()``.
        """
        self._view.camera.set_mode(mode, skip_digestion=True)  # noqa: SLF001

    # ── Clipping ──────────────────────────────────────────────────────────

    def set_clip_planes(
        self,
        near: float | None = None,
        far: float | None = None,
        min_near: float | None = None,
        thickness: float | None = None,
    ) -> None:
        """Adjust camera Z-clipping planes.

        Parameters
        ----------
        near
            Near-clip radius as a percentage (0–99) of the scene radius.
            0 means no near clipping; larger values clip more of the front.
        far
            Far-clip depth as a percentage (0–100) of the scene radius from
            the back. 0 disables far clipping; any positive value enables it.
        min_near
            Minimum near-plane distance in scene units to prevent Z-fighting.
        thickness
            Convenience parameter: if given together with ``near``, ``far`` is
            automatically set to ``min(100, near + thickness)`` (enabling far
            clipping to isolate a depth slice).

        At least one of ``near``, ``far``, ``min_near``, or ``thickness``
        must be provided.
        """
        if near is None and far is None and min_near is None and thickness is None:
            raise ValueError("At least one of near, far, min_near, or thickness must be provided.")
        if thickness is not None:
            if near is None:
                raise ValueError("thickness requires near to be specified.")
            if far is None:
                far = min(100.0, float(near) + float(thickness))
        msg: dict = {"op": "set_clip_planes"}
        if near is not None:
            msg["near"] = float(near)
        if far is not None:
            msg["far"] = float(far)
        if min_near is not None:
            msg["min_near"] = float(min_near)
        self._view._send(msg)  # noqa: SLF001

    # ── Legend ────────────────────────────────────────────────────────────

    def set_legend(self, items: Any = None, *, position: str = "top-right") -> None:
        """Show a colour legend overlay (a generic key for any colour scheme).

        Parameters
        ----------
        items
            Iterable of legend entries, each a ``{"label": str, "color": int}``
            mapping or a ``(label, color)`` pair. ``None`` or ``[]`` hides the
            legend.
        position
            Corner of the viewport: ``"top-right"`` (default), ``"top-left"``,
            ``"bottom-right"`` or ``"bottom-left"``.
        """
        entries: list[dict] = []
        for item in (items or []):
            if isinstance(item, dict):
                label, color = item.get("label"), item.get("color")
            else:
                label, color = item[0], item[1]
            entries.append({"label": str(label), "color": int(color)})
        self._view._send(  # noqa: SLF001
            {"op": "set_legend", "options": {"items": entries, "position": str(position)}}
        )


    # ── Sectioning ────────────────────────────────────────────────────────

    @records_scene_history
    def add_section(
        self,
        point: Any,
        normal: Any,
        *,
        invert: bool = False,
        tag: str | None = None,
    ) -> "Section":
        """Add a world-space clipping plane to all structural representations.

        The plane passes through *point* with its normal along *normal*.
        Everything on the normal side is discarded when ``invert=False``
        (and everything on the anti-normal side when ``invert=True``).

        Parameters
        ----------
        point
            A point on the cutting plane.  Accepts:

            * A puw quantity or a plain ``[x, y, z]`` list in nm.
            * ``"centroid:<tag>"`` — centroid of the scene object with that tag
              (region, shape, annotation, measurement, …).
        normal
            Normal vector of the cutting plane.  Accepts:

            * A plain list/array; any non-zero vector (will be normalised).
            * ``"toward:<tag>"`` — unit vector from *point* toward the centroid
              of the scene object with that tag.
            * ``"mouth:<tag>"`` — alias for ``"toward:<tag>"`` (full TopoMT
              integration pending).
        invert
            Flip which side of the plane is clipped.
        tag
            Optional unique tag.  Auto-generated (``"section1"``, …) if omitted.

        Returns
        -------
        Section
            A handle that exposes :meth:`~layers.Section.get_point`,
            :meth:`~layers.Section.get_normal`,
            :meth:`~layers.Section.set_point`,
            :meth:`~layers.Section.set_normal`,
            :meth:`~layers.Section.set_invert`,
            :meth:`~layers.Section.enable_drag`,
            :meth:`~layers.Section.disable_drag`, and
            :meth:`~layers.Section.delete`.

            Two interactive handles appear in the canvas automatically (see
            :class:`~layers.Section` for details on the gizmo UX).
        """
        from .layers import Section as _Section  # noqa: PLC0415
        from . import pyunitwizard as puw  # noqa: PLC0415

        # ── Resolve point ──────────────────────────────────────────────────
        if isinstance(point, str):
            point_nm = self._resolve_point_string(point)
        elif puw.is_quantity(point):
            point_nm = puw.get_value(point, to_unit="nm").tolist()
        elif hasattr(point, "__iter__"):
            point_nm = list(np.asarray(point, dtype=float))
        else:
            raise TypeError("point must be a 3-element vector, puw quantity, or string.")
        if len(point_nm) != 3:
            raise ValueError("point must be a 3-element [x, y, z] vector.")

        # ── Resolve normal ─────────────────────────────────────────────────
        if isinstance(normal, str):
            normal_unit = self._resolve_normal_string(normal, point_nm)
        else:
            n = np.asarray(normal, dtype=float)
            norm = float(np.linalg.norm(n))
            if norm < 1e-10:
                raise ValueError("normal must be a non-zero vector.")
            normal_unit = (n / norm).tolist()

        # ── Assign tag and register ────────────────────────────────────────
        view = self._view
        if tag is None:
            tag = view._tag_managers["section"].allocate()  # noqa: SLF001
        else:
            tag = view._tag_managers["section"].validate(tag)  # noqa: SLF001

        record = {"tag": tag, "point": point_nm, "normal": normal_unit, "invert": bool(invert)}
        view._section_history.append(record)  # noqa: SLF001

        section = _Section(view, tag)
        view._scene_objects[("section", tag)] = section  # noqa: SLF001

        view._send({"op": "set_sections", "sections": list(view._section_history)})  # noqa: SLF001
        return section

    def sections(self) -> list["Section"]:
        """Return active clipping planes as live handles in creation order."""
        view = self._view
        result = []
        for record in view._section_history:  # noqa: SLF001
            tag = record.get("tag")
            section = view._scene_objects.get(("section", tag))  # noqa: SLF001
            if section is not None:
                result.append(section)
        return result

    # ── String resolution helpers ──────────────────────────────────────────

    def _get_object_centroid_nm(self, tag: str) -> list:
        """Return the centroid ``[x, y, z]`` in nm for the scene object *tag*."""
        from . import pyunitwizard as puw  # noqa: PLC0415

        view = self._view
        matches = [obj for (_kind, object_tag), obj in view._scene_objects.items() if object_tag == tag]  # noqa: SLF001
        obj = matches[0] if len(matches) == 1 else None
        if obj is None:
            raise ValueError(f"No scene object found with tag {tag!r}.")
        if not hasattr(obj, "get_coordinates"):
            raise TypeError(
                f"Scene object {tag!r} (type {type(obj).__name__}) does not support "
                "get_coordinates()."
            )
        coords = obj.get_coordinates()
        arr = (
            puw.get_value(coords, to_unit="nm")
            if puw.is_quantity(coords)
            else np.asarray(coords, dtype=float)
        )
        if arr.ndim == 1:
            return arr.tolist()
        if arr.ndim == 2:
            return arr.mean(axis=0).tolist()
        raise ValueError(
            f"Unexpected coordinate shape {arr.shape!r} from object {tag!r}."
        )

    def _resolve_point_string(self, s: str) -> list:
        if s.startswith("centroid:"):
            target_tag = s[len("centroid:"):]
            return self._get_object_centroid_nm(target_tag)
        raise ValueError(
            f"Unrecognised point string {s!r}. "
            "Supported forms: \"centroid:<tag>\"."
        )

    def _resolve_normal_string(self, s: str, point_nm: list) -> list:
        if s.startswith("toward:") or s.startswith("mouth:"):
            prefix = "toward:" if s.startswith("toward:") else "mouth:"
            target_tag = s[len(prefix):]
            target_centroid = self._get_object_centroid_nm(target_tag)
            n = np.array(target_centroid) - np.array(point_nm)
            norm = float(np.linalg.norm(n))
            if norm < 1e-10:
                raise ValueError(
                    f"Cannot compute normal: point centroid and target {target_tag!r} "
                    "centroid are coincident."
                )
            return (n / norm).tolist()
        raise ValueError(
            f"Unrecognised normal string {s!r}. "
            "Supported forms: \"toward:<tag>\", \"mouth:<tag>\"."
        )

    @records_scene_history
    def remove_section(self, tag: str) -> None:
        """Remove a clipping plane by tag.

        Parameters
        ----------
        tag
            Tag of the section to remove.
        """
        view = self._view
        new_history = [r for r in view._section_history if r.get("tag") != tag]  # noqa: SLF001
        if len(new_history) == len(view._section_history):  # noqa: SLF001
            raise KeyError(f"No section found with tag {tag!r}.")
        view._section_history = new_history  # noqa: SLF001
        view._scene_objects.pop(("section", tag), None)  # noqa: SLF001
        view._send({"op": "set_sections", "sections": new_history})  # noqa: SLF001

    @records_scene_history
    def clear_sections(self) -> None:
        """Remove all active clipping planes."""
        view = self._view
        section_tags = [
            tag for (kind, tag), _obj in view._scene_objects.items()  # noqa: SLF001
            if kind == "section"
        ]
        for tag in section_tags:
            view._scene_objects.pop(("section", tag), None)  # noqa: SLF001
        view._section_history.clear()  # noqa: SLF001
        view._send({"op": "set_sections", "sections": []})  # noqa: SLF001


__all__ = ["SceneManager"]
