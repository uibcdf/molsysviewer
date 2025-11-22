"""Herramientas para visualizar vectores de desplazamiento."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


class DisplacementVectors:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _to_array(data: Iterable[Sequence[float]] | np.ndarray, name: str) -> np.ndarray:
        arr = np.asarray(data, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != 3:
            raise ValueError(f"{name} debe tener forma (n, 3), recibido {arr.shape}")
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
    ) -> None:
        """Añade flechas (cilindro + cono) para vectores de desplazamiento.

        Parameters
        ----------
        origins
            Coordenadas de origen (n, 3). Opcional si se usa ``atom_indices``.
        vectors
            Vectores de desplazamiento (n, 3).
        atom_indices
            Índices atómicos para tomar las coordenadas actuales como origen.
        length_scale
            Factor global de escala para la longitud de los vectores.
        min_length
            Umbral mínimo después de escalar; vectores más cortos se omiten.
        max_length
            Normaliza la longitud máxima resultante a este valor (si se define).
        color_mode
            "norm" o "component" para mapear colores por norma o por componente.
        color_component
            Componente usada al colorear por componente (0, 1 o 2).
        color_map
            Paleta opcional (lista de colores o nombre reconocido por Mol*).
        radius_scale
            Factor relativo de radio (respecto a la longitud final).
        radial_segments
            Segmentos radiales opcionales del cilindro/cono.
        tag
            Etiqueta opcional para el nodo de estado en Mol*.
        """

        vector_array = self._to_array(vectors, "vectors")
        origins_array = None if origins is None else self._to_array(origins, "origins")

        if origins_array is None and atom_indices is None:
            raise ValueError("Debes proporcionar origins o atom_indices")

        if origins_array is not None and origins_array.shape[0] != vector_array.shape[0]:
            raise ValueError("origins y vectors deben tener el mismo número de filas")

        options: dict = {
            "vectors": vector_array.tolist(),
            "length_scale": float(length_scale),
            "min_length": float(min_length),
            "color_mode": color_mode,
            "color_component": int(color_component),
            "radius_scale": float(radius_scale),
        }

        if origins_array is not None:
            options["origins"] = origins_array.tolist()
        if atom_indices is not None:
            options["atom_indices"] = [int(i) for i in atom_indices]
        if max_length is not None:
            options["max_length"] = float(max_length)
        if color_map is not None:
            options["color_map"] = self._to_list(color_map)
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        if tag is not None:
            options["tag"] = tag

        self._view._send({"op": "add_displacement_vectors", "options": options})
