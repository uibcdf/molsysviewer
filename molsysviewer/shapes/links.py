"""Herramientas para representar enlaces/cilindros personalizados."""

from __future__ import annotations

from typing import Iterable, Sequence


class LinkShapes:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _to_pair_list(pairs: Iterable[Sequence[int]] | None, expected_len: int = 2) -> list[list[int]]:
        if pairs is None:
            return []
        normalized: list[list[int]] = []
        for pair in pairs:
            if len(pair) != expected_len:
                raise ValueError(f"Cada par debe tener longitud {expected_len}, recibido {len(pair)}")
            normalized.append([int(pair[0]), int(pair[1])])
        return normalized

    @staticmethod
    def _to_coord_pairs(coords: Iterable[Sequence[Sequence[float]]] | None) -> list[list[list[float]]]:
        if coords is None:
            return []
        normalized: list[list[list[float]]] = []
        for pair in coords:
            if len(pair) != 2:
                raise ValueError("Cada entrada de coordinate_pairs debe tener dos puntos (start, end)")
            start, end = pair
            if len(start) != 3 or len(end) != 3:
                raise ValueError("Cada punto debe tener 3 coordenadas (x, y, z)")
            normalized.append([[float(start[0]), float(start[1]), float(start[2])], [float(end[0]), float(end[1]), float(end[2])]])
        return normalized

    @staticmethod
    def _normalize_optional_list(values, n, cast):
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

    def add_links(
        self,
        *,
        atom_pairs: Iterable[Sequence[int]] | None = None,
        coordinate_pairs: Iterable[Sequence[Sequence[float]]] | None = None,
        radii: float | Sequence[float] = 0.2,
        colors: int | Sequence[int] = 0x4499ff,
        pocket_ids: Sequence[int | str] | None = None,
        chain_ids: Sequence[str] | None = None,
        color_mode: str = "link",
        alpha: float = 1.0,
        radial_segments: int | None = None,
        tag: str | None = None,
    ) -> None:
        """Añade cilindros/barras conectando pares de puntos o de átomos.

        Parameters
        ----------
        atom_pairs
            Pares de índices atómicos (0-based) a conectar. Si se proporciona,
            se usan las coordenadas actuales de la estructura cargada.
        coordinate_pairs
            Lista de pares de coordenadas [[x1, y1, z1], [x2, y2, z2]].
        radii, colors
            Escalares o listas (uno por enlace) para radio y color.
        pocket_ids, chain_ids
            Identificadores opcionales para colorear por pocket o cadena.
        color_mode
            "link" | "pocket" | "chain".
        alpha
            Transparencia global (0-1).
        radial_segments
            Segmentos radiales del cilindro (>=3). Por defecto 16.
        tag
            Etiqueta opcional para el nodo de estado en Mol*.
        """

        coordinate_pairs_list = self._to_coord_pairs(coordinate_pairs)
        atom_pairs_list = self._to_pair_list(atom_pairs) if atom_pairs is not None else []

        if not coordinate_pairs_list and not atom_pairs_list:
            raise ValueError("Debes aportar coordinate_pairs o atom_pairs")

        n_links = len(coordinate_pairs_list) if coordinate_pairs_list else len(atom_pairs_list)

        radii_list = self._normalize_optional_list(radii, n_links, float)
        colors_list = self._normalize_optional_list(colors, n_links, int)
        pocket_ids_list = self._normalize_optional_list(pocket_ids, n_links, lambda v: v)
        chain_ids_list = self._normalize_optional_list(chain_ids, n_links, str)

        options: dict = {
            "mode": "atom-indices" if atom_pairs_list else "coordinates",
            "alpha": float(alpha),
            "color_mode": color_mode,
        }

        if atom_pairs_list:
            options["atom_pairs"] = atom_pairs_list
        if coordinate_pairs_list:
            options["coordinate_pairs"] = coordinate_pairs_list
        if radii_list is not None:
            options["radii"] = radii_list
        if colors_list is not None:
            options["colors"] = colors_list
        if pocket_ids_list is not None:
            options["pocket_ids"] = pocket_ids_list
        if chain_ids_list is not None:
            options["chain_ids"] = chain_ids_list
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        if tag is not None:
            options["tag"] = tag

        self._view._send({"op": "add_network_links", "options": options})
