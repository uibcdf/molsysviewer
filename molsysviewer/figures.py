from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class FigureSpec:
    """Minimal reusable recipe for figure-oriented PNG export."""

    width_px: int | None = None
    height_px: int | None = None
    scale: float = 2.0
    background: str = "white"
    preset: str = "publication-light"
    camera_snapshot: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.width_px is not None and (not isinstance(self.width_px, int) or self.width_px <= 0):
            raise ValueError("FigureSpec.width_px must be a positive integer or None.")
        if self.height_px is not None and (not isinstance(self.height_px, int) or self.height_px <= 0):
            raise ValueError("FigureSpec.height_px must be a positive integer or None.")
        if not isinstance(self.scale, (int, float)) or float(self.scale) <= 0.0:
            raise ValueError("FigureSpec.scale must be a positive number.")
        if not isinstance(self.background, str) or not self.background.strip():
            raise ValueError("FigureSpec.background must be a non-empty string.")
        if not isinstance(self.preset, str) or not self.preset.strip():
            raise ValueError("FigureSpec.preset must be a non-empty string.")
        if self.camera_snapshot is not None and not isinstance(self.camera_snapshot, dict):
            raise ValueError("FigureSpec.camera_snapshot must be a dictionary or None.")

    def info(self) -> dict[str, Any]:
        """Return a JSON-friendly summary of the figure recipe."""
        return {
            "width_px": self.width_px,
            "height_px": self.height_px,
            "scale": float(self.scale),
            "background": self.background,
            "preset": self.preset,
            "camera_snapshot": dict(self.camera_snapshot) if self.camera_snapshot is not None else None,
        }

    @classmethod
    def from_view(
        cls,
        view: Any,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 2.0,
        background: str = "white",
        preset: str = "publication-light",
        include_camera: bool = True,
    ) -> "FigureSpec":
        """Build a figure recipe from the current state of a view.

        At this stage the reusable state captured from the view is intentionally
        narrow and limited to the current camera snapshot.
        """
        camera_snapshot = None
        if include_camera:
            getter = getattr(view, "get_camera_snapshot", None)
            if callable(getter):
                snapshot = getter(skip_digestion=True)
                if isinstance(snapshot, dict):
                    camera_snapshot = dict(snapshot)
        return cls(
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            background=background,
            preset=preset,
            camera_snapshot=camera_snapshot,
        )

    def with_overrides(
        self,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float | None = None,
        background: str | None = None,
        preset: str | None = None,
        camera_snapshot: dict[str, Any] | None = None,
        include_camera_snapshot: bool = True,
    ) -> "FigureSpec":
        """Return a new figure recipe with explicit overrides.

        ``camera_snapshot=None`` keeps the current snapshot unless
        ``include_camera_snapshot`` is set to ``False``.
        """
        updates: dict[str, Any] = {}
        if width_px is not None:
            updates["width_px"] = width_px
        if height_px is not None:
            updates["height_px"] = height_px
        if scale is not None:
            updates["scale"] = scale
        if background is not None:
            updates["background"] = background
        if preset is not None:
            updates["preset"] = preset
        if include_camera_snapshot:
            if camera_snapshot is not None:
                updates["camera_snapshot"] = dict(camera_snapshot)
        else:
            updates["camera_snapshot"] = None
        return replace(self, **updates)
