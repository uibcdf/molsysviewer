"""Herramientas para representar vectores de desplazamiento."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


class VectorShapes:
    """Colección de utilidades para vectores (flechas) en la escena."""

    def __init__(self, view) -> None:
        self._view = view

    def add_displacement_vectors(
        self,
        origins: Sequence[Sequence[float]] | np.ndarray,
        displacements: Sequence[Sequence[float]] | np.ndarray,
        *,
        length_scale: float = 1.0,
        max_length: float | None = None,
        min_length: float = 0.0,
        color_mode: str = "norm",
        color_map: Iterable[float] | str | None = None,
        radius: float = 0.2,
        head_length_ratio: float = 0.25,
        head_radius_factor: float = 1.8,
        alpha: float = 1.0,
        tag: str | None = None,
        name: str | None = None,
    ) -> None:
        """Añade flechas de desplazamiento (cono + cilindro) a la escena.

        Parameters
        ----------
        origins, displacements
            Arrays (n, 3) con los puntos de origen y los vectores de desplazamiento.
        length_scale
            Escala multiplicativa aplicada a las longitudes de las flechas.
        max_length
            Si se indica, normaliza todas las flechas para que la longitud máxima
            coincida con este valor.
        min_length
            Descarta vectores con longitud (tras escalar) inferior a este umbral.
        color_mode
            "norm" para colorear por norma del vector, o "x"/"y"/"z" para usar
            la componente correspondiente.
        color_map
            Paleta de colores (lista de hexadecimales o nombre reconocible por Mol*).
        radius
            Radio del cilindro del cuerpo de la flecha.
        head_length_ratio
            Fracción de la longitud dedicada a la punta (cono).
        head_radius_factor
            Multiplicador del radio para la base del cono.
        alpha
            Factor de opacidad (0-1) aplicado a la representación.
        tag
            Etiqueta opcional para identificar el objeto en el árbol de estado.
        name
            Etiqueta legible en el árbol de estado.
        """

        origins_arr = np.asarray(origins, dtype=float)
        displacements_arr = np.asarray(displacements, dtype=float)

        if origins_arr.shape != displacements_arr.shape:
            raise ValueError("origins y displacements deben tener la misma forma")
        if origins_arr.ndim != 2 or origins_arr.shape[1] != 3:
            raise ValueError("origins y displacements deben tener forma (n, 3)")
        if origins_arr.shape[0] == 0:
            return

        options: dict[str, object] = {
            "origins": origins_arr.tolist(),
            "displacements": displacements_arr.tolist(),
            "length_scale": float(length_scale),
            "min_length": float(min_length),
            "radius": float(radius),
            "head_length_ratio": float(head_length_ratio),
            "head_radius_factor": float(head_radius_factor),
            "alpha": float(alpha),
        }

        if max_length is not None:
            options["max_length"] = float(max_length)
        if color_map is not None:
            options["color_map"] = (
                color_map if isinstance(color_map, str) else list(color_map)
            )

        options["color_mode"] = str(color_mode)
        if tag is not None:
            options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_displacement_vectors", "options": options})
