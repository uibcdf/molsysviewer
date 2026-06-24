from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .._private.arg_digestion import digest
from ..colors import colors as global_colors
from ..colors import normalize_color
from ._registry import register_shape_layer
from ._units import to_wire_angstroms


class ChannelTubes:
    """API to build channel tubes along ordered centers/radii (e.g., TopoMT routes)."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        # Extract raw magnitudes in Angstroms (wire format for Mol*)
        centers_raw = to_wire_angstroms(centers)
        normalized: list[list[float]] = []
        for idx, center in enumerate(centers_raw):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] must have 3 coordinates (x, y, z)")
            normalized.append([float(center[0]), float(center[1]), float(center[2])])
        return normalized

    @staticmethod
    def _normalize_centers_raw(centers: Iterable) -> list[list[float]]:
        """Like _normalize_centers but skips puw conversion — for raw Angstrom data."""
        normalized: list[list[float]] = []
        for idx, center in enumerate(centers):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] must have 3 coordinates (x, y, z)")
            normalized.append([float(center[0]), float(center[1]), float(center[2])])
        return normalized

    @staticmethod
    def _normalize_sequence(values, n: int, cast):
        if values is None:
            return None
        if isinstance(values, (str, bytes)):
            return [cast(values)] * n
        try:
            seq = list(values)
        except TypeError:
            return [cast(values)] * n
        if len(seq) not in (1, n):
            raise ValueError(f"Expected 1 or {n} values, got {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * n
        return [cast(v) for v in seq]

    @signal(tags=["shape", "channel"])
    @digest()
    def add_channel_tube(
        self,
        *,
        centers: Iterable[Sequence[float]],
        radii: Iterable[float],
        structure_centers: Iterable | None = None,
        color_by: str | None = None,
        palette=None,
        color_mode: str | None = None,
        solvent_distances: Iterable[float] | None = None,
        colors: Sequence[int] | None = None,
        color_map: Sequence[int] | str | None = None,
        radial_segments: int | None = None,
        smoothing_subdivisions: int | None = None,
        tube_style: str | None = None,
        tube_aspect_ratio: float | None = None,
        surface_resolution: float | None = None,
        surface_smoothing: float | None = None,
        surface_iso_level: float | None = None,
        surface_radius_scale: float | None = None,
        alpha: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Generate a smoothed tube from ordered centers/radii (e.g., TopoMT routes)."""

        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in to_wire_angstroms(radii)]

        if len(centers_list) < 2:
            raise ValueError("You need at least two centers for a channel")
        if len(centers_list) != len(radii_list):
            raise ValueError("centers and radii must have the same length")

        distances_list = self._normalize_sequence(solvent_distances, len(centers_list), float)
        colors_list = self._normalize_sequence(colors, len(centers_list), normalize_color)
        color_registry = getattr(self._view, "colors", global_colors)
        resolved_color_by = color_by or color_mode
        resolved_palette = palette if palette is not None else color_map
        serialized_palette = None
        if resolved_palette is not None:
            serialized_palette = color_registry.resolve_palette(resolved_palette).colors

        options: dict = {
            "centers": centers_list,
            "radii": radii_list,
        }
        if resolved_color_by is not None:
            options["color_mode"] = resolved_color_by
            options["color_by"] = resolved_color_by
        if distances_list is not None:
            options["solvent_distances"] = distances_list
        if colors_list is not None:
            options["colors"] = colors_list
        if serialized_palette is not None:
            options["palette"] = serialized_palette
            options["color_map"] = serialized_palette
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        if smoothing_subdivisions is not None:
            options["smoothing_subdivisions"] = int(smoothing_subdivisions)
        if tube_style is not None:
            if tube_style not in {"smooth", "segments", "surface"}:
                raise ValueError("tube_style must be 'smooth', 'segments' or 'surface'")
            options["tube_style"] = tube_style
        if tube_aspect_ratio is not None:
            if tube_aspect_ratio <= 0:
                raise ValueError("tube_aspect_ratio must be positive")
            options["tube_aspect_ratio"] = float(tube_aspect_ratio)
        if surface_resolution is not None:
            options["surface_resolution"] = float(surface_resolution)
        if surface_smoothing is not None:
            options["surface_smoothing"] = float(surface_smoothing)
        if surface_iso_level is not None:
            options["surface_iso_level"] = float(surface_iso_level)
        if surface_radius_scale is not None:
            options["surface_radius_scale"] = float(surface_radius_scale)
        if alpha is not None:
            options["alpha"] = float(alpha)
        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag
        if name is not None:
            options["name"] = name
        if structure_centers is not None:
            options["structures_coords"] = [
                self._normalize_centers_raw(fc) if fc is not None else None
                for fc in structure_centers
            ]

        self._view._send({"op": "add_channel_tube", "options": options})
        return layer
