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
    ):
        """Generate a smoothed tube from ordered centers/radii (e.g., TopoMT routes)."""

        centers_list = self._normalize_centers(centers)
        radii_list = [float(r) for r in radii]

        if len(centers_list) < 2:
            raise ValueError("You need at least two centers for a channel")
        if len(centers_list) != len(radii_list):
            raise ValueError("centers and radii must have the same length")

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
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_channel_tube", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
