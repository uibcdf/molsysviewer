from __future__ import annotations

from typing import Iterable, Sequence


class TriangleFaces:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_vertices(vertices: Iterable[Sequence[float]] | None) -> list[list[list[float]]]:
        if vertices is None:
            return []

        normalized: list[list[list[float]]] = []
        for tri in vertices:
            tri_list = list(tri)
            if len(tri_list) == 3 and all(isinstance(v, Sequence) and len(v) == 3 for v in tri_list):
                normalized.append(
                    [
                        [float(tri_list[0][0]), float(tri_list[0][1]), float(tri_list[0][2])],
                        [float(tri_list[1][0]), float(tri_list[1][1]), float(tri_list[1][2])],
                        [float(tri_list[2][0]), float(tri_list[2][1]), float(tri_list[2][2])],
                    ]
                )
            elif len(tri_list) == 9:
                normalized.append(
                    [
                        [float(tri_list[0]), float(tri_list[1]), float(tri_list[2])],
                        [float(tri_list[3]), float(tri_list[4]), float(tri_list[5])],
                        [float(tri_list[6]), float(tri_list[7]), float(tri_list[8])],
                    ]
                )
            else:
                raise ValueError(
                    "Cada triángulo debe ser [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]] o una lista de 9 números"
                )
        return normalized

    @staticmethod
    def _normalize_triplets(atom_triplets: Iterable[Sequence[int]] | None) -> list[list[int]]:
        if atom_triplets is None:
            return []

        normalized: list[list[int]] = []
        for tri in atom_triplets:
            if len(tri) != 3:
                raise ValueError("Cada entrada de atom_triplets debe tener 3 índices")
            normalized.append([int(tri[0]), int(tri[1]), int(tri[2])])
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

    def add_triangle_faces(
        self,
        *,
        vertices: Iterable[Sequence[float]] | None = None,
        atom_triplets: Iterable[Sequence[int]] | None = None,
        colors: int | Sequence[int] = 0xCCCCCC,
        alpha: float = 1.0,
        labels: Sequence[str] | str | None = None,
        tag: str | None = None,
    ) -> None:
        """Añade caras triangulares personalizadas usando coordenadas o índices atómicos."""

        vertices_list = self._normalize_vertices(vertices)
        atom_triplets_list = self._normalize_triplets(atom_triplets)

        if not vertices_list and not atom_triplets_list:
            raise ValueError("Debes proporcionar vertices o atom_triplets")

        n = len(vertices_list) if vertices_list else len(atom_triplets_list)

        colors_list = self._normalize_optional_list(colors, n, int)
        labels_list = self._normalize_optional_list(labels, n, str)

        options: dict = {"alpha": float(alpha)}

        if vertices_list:
            options["vertices"] = vertices_list
        if atom_triplets_list:
            options["atom_triplets"] = atom_triplets_list
        if colors_list is not None:
            options["colors"] = colors_list
        if labels_list is not None:
            options["labels"] = labels_list
        if tag is not None:
            options["tag"] = tag

        self._view._send({"op": "add_triangle_faces", "options": options})
