from __future__ import annotations

from dataclasses import dataclass
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
