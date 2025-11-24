from __future__ import annotations

from typing import Iterable, Sequence


class ChannelTubes:
    """API to build channel tubes along ordered centers/radii (e.g., TopoMT routes)."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        normalized: list[list[float]] = []
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

    def add_channel_tube(
        self,
        *,
        centers: Iterable[Sequence[float]],
        radii: Iterable[float],
        color_mode: str | None = None,
        solvent_distances: Iterable[float] | None = None,
        colors: Sequence[int] | None = None,
        color_map: Sequence[int] | str | None = None,
        radial_segments: int | None = None,
        smoothing_subdivisions: int | None = None,
        alpha: float | None = None,
        tag: str | None = None,
        name: str | None = None,
    ) -> None:
        """Generate a smoothed tube from ordered centers/radii (e.g., TopoMT routes)."""

        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in radii]

        if len(centers_list) < 2:
            raise ValueError("Se necesitan al menos dos centros para un canal")
        if len(centers_list) != len(radii_list):
            raise ValueError("centers y radii deben tener la misma longitud")

        distances_list = self._normalize_sequence(solvent_distances, len(centers_list), float)
        colors_list = self._normalize_sequence(colors, len(centers_list), int)

        options: dict = {
            "centers": centers_list,
            "radii": radii_list,
        }
        if color_mode is not None:
            options["color_mode"] = color_mode
        if distances_list is not None:
            options["solvent_distances"] = distances_list
        if colors_list is not None:
            options["colors"] = colors_list
        if color_map is not None:
            options["color_map"] = color_map
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        if smoothing_subdivisions is not None:
            options["smoothing_subdivisions"] = int(smoothing_subdivisions)
        if alpha is not None:
            options["alpha"] = float(alpha)
        if tag is not None:
            options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_channel_tube", "options": options})
