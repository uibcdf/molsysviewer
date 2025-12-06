from __future__ import annotations

from typing import Iterable, Sequence


class PocketBlobs:
    """API for volumetric blobs (Gaussian fields) built from alpha-spheres."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        normalized = []
        for idx, center in enumerate(centers):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] debe tener 3 coordenadas (x, y, z)")
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
            raise ValueError(f"Esperaba 1 o {n} valores, recibido {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * n
        return [cast(v) for v in seq]

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
        name: str | None = None,
    ):
        """Create a volumetric blob (iso-surface) from alpha-spheres."""

        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in radii]

        if len(centers_list) == 0:
            raise ValueError("centers no puede estar vacío")
        if len(centers_list) != len(radii_list):
            raise ValueError("centers y radii deben tener la misma longitud")

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
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_pocket_blob", "options": options})
        # Registrar layer para manejo de visibilidad
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
