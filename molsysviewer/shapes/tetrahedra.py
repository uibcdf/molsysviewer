from __future__ import annotations

from typing import Iterable, Sequence


class Tetrahedra:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_vertices(tetra_coords: Iterable[Sequence[Sequence[float]]] | None) -> list[list[list[float]]]:
        if tetra_coords is None:
            return []

        normalized: list[list[list[float]]] = []
        for idx, tetra in enumerate(tetra_coords):
            coords = list(tetra)
            if len(coords) != 4:
                raise ValueError(f"tetra_coords[{idx}] debe tener 4 vértices")
            vertices: list[list[float]] = []
            for v in coords:
                if len(v) != 3:
                    raise ValueError(
                        f"Cada vértice en tetra_coords[{idx}] debe ser [x, y, z]; recibido {v}"
                    )
                vertices.append([float(v[0]), float(v[1]), float(v[2])])
            normalized.append(vertices)
        return normalized

    @staticmethod
    def _normalize_quads(atom_quads: Iterable[Sequence[int]] | None) -> list[list[int]]:
        if atom_quads is None:
            return []

        normalized: list[list[int]] = []
        for idx, quad in enumerate(atom_quads):
            if len(quad) != 4:
                raise ValueError(f"atom_quads[{idx}] debe tener 4 índices")
            normalized.append([int(quad[0]), int(quad[1]), int(quad[2]), int(quad[3])])
        return normalized

    @staticmethod
    def _normalize_optional_list(values, n: int, cast):
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

    def add_tetrahedra(
        self,
        *,
        tetra_coords: Iterable[Sequence[Sequence[float]]] | None = None,
        atom_quads: Iterable[Sequence[int]] | None = None,
        colors: int | Sequence[int] = 0xFF8800,
        alphas: float | Sequence[float] = 0.6,
        labels: Sequence[str] | str | None = None,
        exterior_only: bool = True,
        show_all_faces: bool | None = None,
        tag: str | None = None,
        name: str | None = None,
    ) -> None:
        """Añade tetraedros como malla triangular, usando coordenadas o índices atómicos."""

        coords_list = self._normalize_vertices(tetra_coords)
        atom_quads_list = self._normalize_quads(atom_quads)

        if not coords_list and not atom_quads_list:
            raise ValueError("Debes proporcionar tetra_coords o atom_quads")

        n = len(coords_list) if coords_list else len(atom_quads_list)

        colors_list = self._normalize_optional_list(colors, n, int)
        alphas_list = self._normalize_optional_list(alphas, n, float)
        labels_list = self._normalize_optional_list(labels, n, str)

        options: dict = {"exterior_only": bool(exterior_only)}

        if show_all_faces is not None:
            options["show_all_faces"] = bool(show_all_faces)
        if name is not None:
            options["name"] = name
        if coords_list:
            options["tetra_coords"] = coords_list
        if atom_quads_list:
            options["atom_quads"] = atom_quads_list
        if colors_list is not None:
            options["colors"] = colors_list
        if alphas_list is not None:
            options["alphas"] = alphas_list
        if labels_list is not None:
            options["labels"] = labels_list
        if tag is not None:
            options["tag"] = tag

        self._view._send({"op": "add_tetrahedra", "options": options})

