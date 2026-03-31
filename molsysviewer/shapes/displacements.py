"""Helpers to render displacement vectors."""

from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.arg_digestion import digest

import numpy as np


class DisplacementVectors:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _to_array(data: Iterable[Sequence[float]] | np.ndarray, name: str) -> np.ndarray:
        # Extract raw magnitudes in nanometers
        data_raw = puw.get_value(data, to_unit="nm")
        arr = np.asarray(data_raw, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != 3:
            raise ValueError(f"{name} must have shape (n, 3), got {arr.shape}")
        return arr

    @staticmethod
    def _to_list(values):
        if values is None:
            return None
        if isinstance(values, (str, bytes)):
            return values
        try:
            seq = list(values)
        except TypeError:
            return values
        return seq

    @signal(tags=["shape", "vector"])
    @digest()
    def add_displacement_vectors(
        self,
        origins: Iterable[Sequence[float]] | np.ndarray | None,
        vectors: Iterable[Sequence[float]] | np.ndarray,
        *,
        atom_indices: Iterable[int] | None = None,
        length_scale: float = 1.0,
        min_length: float = 0.0,
        max_length: float | None = None,
        color_mode: str = "norm",
        color_component: int = 2,
        color_map: Sequence[int] | str | None = None,
        radius_scale: float = 0.05,
        radial_segments: int | None = None,
        tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Add arrows (cylinder + cone) for displacement vectors.

        Parameters
        ----------
        origins
            Origin coordinates `(n, 3)`. Optional if you use ``atom_indices``.
        vectors
            Displacement vectors `(n, 3)`.
        atom_indices
            Atom indices to use the current structure coordinates as origins.
        length_scale
            Global scale factor for vector lengths.
        min_length
            Minimum length after scaling; shorter vectors are skipped.
        max_length
            Normalize the resulting maximum length to this value (if set).
        color_mode
            "norm" or "component" to map colors by norm or by component.
        color_component
            Component used for "component" coloring (0, 1, or 2).
        color_map
            Optional palette (color list or a Mol*-recognized name).
        radius_scale
            Relative radius factor (relative to final length).
        radial_segments
            Optional radial segments for cylinder/cone.
        tag
            Optional tag for the Mol* state node.
        """

        vector_array = self._to_array(vectors, "vectors")
        origins_array = None if origins is None else self._to_array(origins, "origins")

        if origins_array is None and atom_indices is None:
            raise ValueError("You must provide origins or atom_indices")

        if origins_array is not None and origins_array.shape[0] != vector_array.shape[0]:
            raise ValueError("origins and vectors must have the same number of rows")

        options: dict = {
            "vectors": vector_array.tolist(),
            "length_scale": float(puw.get_value(length_scale)),
            "min_length": float(puw.get_value(min_length, to_unit="nm")),
            "color_mode": color_mode,
            "color_component": int(color_component),
            "radius_scale": float(puw.get_value(radius_scale)),
        }

        if origins_array is not None:
            options["origins"] = origins_array.tolist()
        if atom_indices is not None:
            options["atom_indices"] = [int(i) for i in atom_indices]
        if max_length is not None:
            options["max_length"] = float(puw.get_value(max_length, to_unit="nm"))
        if color_map is not None:
            options["color_map"] = self._to_list(color_map)
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag

        self._view._send({"op": "add_displacement_vectors", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
