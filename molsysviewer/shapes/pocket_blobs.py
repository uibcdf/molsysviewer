from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.arg_digestion import digest
from ._registry import register_shape_layer


class PocketBlobs:
    """API for volumetric blobs (Gaussian fields) built from alpha-spheres."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        normalized = []
        for idx, center in enumerate(centers):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] must have 3 coordinates (x, y, z)")
            # Extract raw magnitude in nanometers to avoid DimensionalityError
            val = puw.get_value(center, to_unit="nm")
            normalized.append([float(val[0]), float(val[1]), float(val[2])])
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

    @signal(tags=["shape", "pocket"])
    @digest()
    def add_pocket_blob(
        self,
        *,
        centers: Iterable[Sequence[float]],
        radii: Iterable[float],
        radius_scale: float | None = None,
        resolution: float | None = None,
        iso_level: float | None = None,
        smoothing: float | None = None,
        values: Iterable[float] | None = None,
        color_map: Sequence[int] | str | None = None,
        alpha: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Create a volumetric blob (iso-surface) from alpha-spheres."""

        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in puw.get_value(radii, to_unit="nm")]

        if len(centers_list) == 0:
            raise ValueError("centers must not be empty")
        if len(centers_list) != len(radii_list):
            raise ValueError("centers and radii must have the same length")

        values_list = self._normalize_sequence(values, len(centers_list), float)

        options: dict = {
            "centers": centers_list,
            "radii": radii_list,
        }

        if resolution is not None:
            options["resolution"] = float(resolution)
        if iso_level is not None:
            options["iso_level"] = float(iso_level)
        if smoothing is not None:
            options["smoothing"] = float(smoothing)
        if radius_scale is not None:
            options["radius_scale"] = float(radius_scale)
        if values_list is not None:
            options["values"] = values_list
        if color_map is not None:
            options["color_map"] = color_map
        if alpha is not None:
            options["alpha"] = float(alpha)
        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_pocket_blob", "options": options})
        return layer
