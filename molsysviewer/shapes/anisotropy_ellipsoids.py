from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.arg_digestion import digest


class AnisotropyEllipsoids:
    """Visualize oriented ellipsoids/disks from eigenvalues/eigenvectors or tensors."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        # Extract raw magnitudes in nanometers
        centers_raw = puw.get_value(centers, to_unit="nm")
        normalized: list[list[float]] = []
        for idx, center in enumerate(centers_raw):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] must have 3 coordinates (x, y, z)")
            normalized.append([float(center[0]), float(center[1]), float(center[2])])
        return normalized

    @signal(tags=["shape", "ellipsoid"])
    @digest()
    def add_anisotropy_ellipsoids(
        self,
        *,
        centers: Iterable[Sequence[float]],
        eigenvalues: Iterable[Sequence[float]] | None = None,
        eigenvectors: Iterable[Sequence[Sequence[float]]] | None = None,
        tensors: Iterable[Sequence[Sequence[float]]] | None = None,
        principal_directions: Iterable[Sequence[float]] | None = None,
        scale: float | None = None,
        max_eccentricity: float | None = None,
        color_mode: str | None = None,
        colors: Sequence[int] | None = None,
        color_map: Sequence[int] | str | None = None,
        values: Sequence[float] | None = None,
        alpha: float | None = None,
        tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Send oriented ellipsoids or flat disks based on anisotropy inputs."""

        centers_list = self._normalize_centers(centers)

        options: dict = {
            "centers": centers_list,
        }
        if eigenvalues is not None:
            options["eigenvalues"] = eigenvalues
        if eigenvectors is not None:
            options["eigenvectors"] = eigenvectors
        if tensors is not None:
            options["tensors"] = tensors
        if principal_directions is not None:
            options["principal_directions"] = principal_directions
        if scale is not None:
            options["scale"] = scale
        if max_eccentricity is not None:
            options["max_eccentricity"] = max_eccentricity
        if color_mode is not None:
            options["color_mode"] = color_mode
        if colors is not None:
            options["colors"] = colors
        if color_map is not None:
            options["color_map"] = color_map
        if values is not None:
            options["values"] = values
        if alpha is not None:
            options["alpha"] = alpha
        
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_anisotropy_ellipsoids", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
