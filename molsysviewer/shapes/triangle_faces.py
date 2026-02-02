from __future__ import annotations

from typing import Iterable, Sequence

from .._private.digestion import digest


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
                    "Each triangle must be [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]] or a list of 9 numbers"
                )
        return normalized

    @staticmethod
    def _normalize_triplets(atom_triplets: Iterable[Sequence[int]] | None) -> list[list[int]]:
        if atom_triplets is None:
            return []

        normalized: list[list[int]] = []
        for tri in atom_triplets:
            if len(tri) != 3:
                raise ValueError("Each entry in atom_triplets must have 3 indices")
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
            raise ValueError(f"Expected 1 or {n} values, got {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * n
        return [cast(v) for v in seq]

    @digest()
    def add_triangle_faces(
        self,
        *,
        vertices: Iterable[Sequence[float]] | None = None,
        atom_triplets: Iterable[Sequence[int]] | None = None,
        colors: int | Sequence[int] = 0xCCCCCC,
        alpha: float = 1.0,
        labels: Sequence[str] | str | None = None,
        draw_edges: bool | None = None,
        edge_radius: float | None = None,
        edge_color: int | None = None,
        show_normals: bool | None = None,
        normal_length: float | None = None,
        normal_color: int | None = None,
        tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Add custom triangle faces using coordinates or atom indices.

        Extra parameters:
        - draw_edges: draw edges as thin cylinders (`edge_radius`/`edge_color`).
        - show_normals: draw normals as arrows (`normal_length`/`normal_color`).
        """

        vertices_list = self._normalize_vertices(vertices)
        atom_triplets_list = self._normalize_triplets(atom_triplets)

        if not vertices_list and not atom_triplets_list:
            raise ValueError("You must provide vertices or atom_triplets")

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
        if draw_edges is not None:
            options["draw_edges"] = bool(draw_edges)
        if edge_radius is not None:
            options["edge_radius"] = float(edge_radius)
        if edge_color is not None:
            options["edge_color"] = int(edge_color)
        if show_normals is not None:
            options["show_normals"] = bool(show_normals)
        if normal_length is not None:
            options["normal_length"] = float(normal_length)
        if normal_color is not None:
            options["normal_color"] = int(normal_color)
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag

        self._view._send({"op": "add_triangle_faces", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
