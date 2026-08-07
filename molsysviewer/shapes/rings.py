from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.argdigest import digest
from ..scene_history import records_scene_history
from ..colors import colors as global_colors, normalize_color
from ._registry import register_shape_layer


class Rings:
    """API to build flat rings (circles) perpendicular to a per-ring axis.

    Generic primitive — any consumer that needs orthogonal rings along an axis:
    HOLE-style pore clearance profiles, channel bottleneck rings, gate/mouth
    accents, etc. Each ring is a thin closed tube of ``thickness`` swept around a
    circle of the given ``radius`` centered at ``center`` in the plane normal to
    ``normal``. The render reuses the channel-tube geometry on the frontend.
    """

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_vectors(values: Iterable[Sequence[float]], name: str,
                           to_angstroms: bool) -> list[list[float]]:
        raw = puw.get_value(values, to_unit="angstroms") if to_angstroms else values
        out: list[list[float]] = []
        for idx, v in enumerate(raw):
            if len(v) != 3:
                raise ValueError(f"{name}[{idx}] must have 3 components (x, y, z)")
            out.append([float(v[0]), float(v[1]), float(v[2])])
        return out

    @staticmethod
    def _normalize_scalars(values, n: int, cast):
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

    @signal(tags=["shape", "rings"])
    @digest()
    @records_scene_history
    def add_rings(
        self,
        *,
        centers: Iterable[Sequence[float]],
        normals: Iterable[Sequence[float]],
        radii: Iterable[float],
        thickness=None,
        colors: Sequence[int] | None = None,
        color_by: str | None = None,
        color_mode: str | None = None,
        values: Iterable[float] | None = None,
        palette=None,
        color_map: Sequence[int] | str | None = None,
        segments: int | None = None,
        alpha: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Render one ring per (center, normal, radius).

        Parameters
        ----------
        centers, normals, radii
            Per-ring center (length, Å), axis (direction, unitless) and circle
            radius (length, Å). Must be the same length ``N``.
        thickness
            Tube thickness of the ring (Å), scalar or per-ring. Defaults to a thin
            ring relative to its radius.
        colors
            Per-ring color (or a single color for all).
        color_by / values / palette / color_map
            Scalar coloring: map ``values`` (e.g. clearance radius) through a
            palette. ``color_by`` selects the mode (e.g. ``'clearance'``).
        segments
            Circle resolution (number of straight chords per ring).
        """
        centers_list = self._normalize_vectors(centers, "centers", to_angstroms=True)
        normals_list = self._normalize_vectors(normals, "normals", to_angstroms=False)
        radii_list = [float(r) for r in puw.get_value(radii, to_unit="angstroms")]

        n = len(centers_list)
        if n == 0:
            raise ValueError("add_rings needs at least one ring")
        if not (len(normals_list) == n == len(radii_list)):
            raise ValueError("centers, normals and radii must have the same length")

        thickness_list = self._normalize_scalars(
            None if thickness is None else puw.get_value(thickness, to_unit="angstroms"),
            n,
            float,
        )
        colors_list = self._normalize_scalars(colors, n, normalize_color)
        values_list = self._normalize_scalars(values, n, float)

        color_registry = getattr(self._view, "colors", global_colors)
        resolved_color_by = color_by or color_mode
        resolved_palette = palette if palette is not None else color_map
        serialized_palette = None
        if resolved_palette is not None:
            serialized_palette = color_registry.resolve_palette(resolved_palette).colors

        options: dict = {
            "centers": centers_list,
            "normals": normals_list,
            "radii": radii_list,
        }
        if thickness_list is not None:
            options["thickness"] = thickness_list
        if colors_list is not None:
            options["colors"] = colors_list
        if values_list is not None:
            options["values"] = values_list
        if resolved_color_by is not None:
            options["color_by"] = resolved_color_by
            options["color_mode"] = resolved_color_by
        if serialized_palette is not None:
            options["palette"] = serialized_palette
            options["color_map"] = serialized_palette
        if segments is not None:
            options["segments"] = int(segments)
        if alpha is not None:
            options["alpha"] = float(alpha)

        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_rings", "options": options})
        return layer
