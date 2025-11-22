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
        origins: Sequence[Sequence[float]] | np.ndarray | None = None,
        displacements: Sequence[Sequence[float]] | np.ndarray,
        *,
        atom_indices: Sequence[int] | np.ndarray | None = None,
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
        origins
            Array (n, 3) con los puntos de origen. Opcional si se proporcionan
            `atom_indices`.
        displacements
            Array (n, 3) con los vectores de desplazamiento.
        atom_indices
            Índices de átomos de la estructura cargada desde los que se tomarán
            las coordenadas de origen. Si se indican, `origins` es opcional.
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

        displacements_arr = np.asarray(displacements, dtype=float)
        if displacements_arr.ndim != 2 or displacements_arr.shape[1] != 3:
            raise ValueError("displacements debe tener forma (n, 3)")
        if displacements_arr.shape[0] == 0:
            return

        origins_list: list[list[float]] | None = None
        if origins is not None:
            origins_arr = np.asarray(origins, dtype=float)
            if origins_arr.shape != displacements_arr.shape:
                raise ValueError("origins y displacements deben tener la misma forma")
            origins_list = origins_arr.tolist()
        elif atom_indices is None:
            raise ValueError("Debe indicarse origins o atom_indices para las flechas")
        else:
            atom_indices = np.asarray(atom_indices, dtype=int)
            if atom_indices.ndim != 1:
                raise ValueError("atom_indices debe ser un vector 1D")
            if atom_indices.size != displacements_arr.shape[0]:
                raise ValueError("atom_indices debe tener la misma longitud que displacements")
        options: dict[str, object] = {
            "displacements": displacements_arr.tolist(),
            "length_scale": float(length_scale),
            "min_length": float(min_length),
            "radius": float(radius),
            "head_length_ratio": float(head_length_ratio),
            "head_radius_factor": float(head_radius_factor),
            "alpha": float(alpha),
        }

        if origins_list is not None:
            options["origins"] = origins_list
        if atom_indices is not None:
            options["atom_indices"] = [int(v) for v in np.asarray(atom_indices).ravel()]

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
