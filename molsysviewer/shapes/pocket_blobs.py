from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .._private.arg_digestion import digest
from ..scene_history import records_scene_history
from ._registry import register_shape_layer
from .. import pyunitwizard as puw


class PocketBlobs:
    """API for volumetric blobs (Gaussian fields) built from alpha-spheres."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        # Extract raw magnitude in Angstroms (wire format for Mol*) in a single batch call
        val = puw.get_value(centers, to_unit="angstroms")
        return val.tolist()

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

    def _add_gaussian_isosurface(
        self,
        *,
        op: str,
        centers: Iterable[Sequence[float]],
        radii: Iterable[float],
        radius_scale: float | None = None,
        resolution: float | None = None,
        iso_level: float | None = None,
        smoothing: float | None = None,
        values: Iterable[float] | None = None,
        color_map: Sequence[int] | str | None = None,
        alpha: float | None = None,
        wireframe: bool = False,
        wireframe_size: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
    ):
        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in puw.get_value(radii, to_unit="angstroms")]

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
        if wireframe:
            options["wireframe"] = True
        if wireframe_size is not None:
            options["wireframe_size"] = float(wireframe_size)
        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": op, "options": options})
        return layer

    @signal(tags=["shape", "isosurface"])
    @digest()
    @records_scene_history
    def add_scalar_isosurface(
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
        wireframe: bool = False,
        wireframe_size: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Create a generic scalar/gaussian isosurface from centers and radii."""
        return self._add_gaussian_isosurface(
            op="add_scalar_isosurface",
            centers=centers,
            radii=radii,
            radius_scale=radius_scale,
            resolution=resolution,
            iso_level=iso_level,
            smoothing=smoothing,
            values=values,
            color_map=color_map,
            alpha=alpha,
            wireframe=wireframe,
            wireframe_size=wireframe_size,
            tag=tag,
            layer_tag=layer_tag,
            name=name,
        )

    @signal(tags=["shape", "pocket"])
    @digest()
    @records_scene_history
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
        wireframe: bool = False,
        wireframe_size: float | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Create a volumetric blob (iso-surface) from alpha-spheres."""

        return self._add_gaussian_isosurface(
            op="add_pocket_blob",
            centers=centers,
            radii=radii,
            radius_scale=radius_scale,
            resolution=resolution,
            iso_level=iso_level,
            smoothing=smoothing,
            values=values,
            color_map=color_map,
            alpha=alpha,
            wireframe=wireframe,
            wireframe_size=wireframe_size,
            tag=tag,
            layer_tag=layer_tag,
            name=name,
        )
