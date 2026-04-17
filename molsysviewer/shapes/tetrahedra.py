from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.arg_digestion import digest
from ..colors import normalize_color
from ._registry import register_shape_layer


class Tetrahedra:
    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_vertices(tetra_coords: Iterable[Sequence[Sequence[float]]] | None) -> list[list[list[float]]]:
        if tetra_coords is None:
            return []

        # Extract raw magnitudes in Angstroms (wire format for Mol*)
        coords_raw = puw.get_value(tetra_coords, to_unit="angstroms")

        normalized: list[list[list[float]]] = []
        for idx, tetra in enumerate(coords_raw):
            coords = list(tetra)
            if len(coords) != 4:
                raise ValueError(f"tetra_coords[{idx}] must have 4 vertices")
            vertices: list[list[float]] = []
            for v in coords:
                if len(v) != 3:
                    raise ValueError(
                        f"Each vertex in tetra_coords[{idx}] must be [x, y, z]; got {v}"
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
                raise ValueError(f"atom_quads[{idx}] must have 4 indices")
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
            raise ValueError(f"Expected 1 or {n} values, got {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * n
        return [cast(v) for v in seq]

    @signal(tags=["shape", "tetrahedra"])
    @digest()
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
        draw_edges: bool | None = None,
        edge_radius: float | None = None,
        edge_color: int | None = None,
        show_normals: bool | None = None,
        normal_length: float | None = None,
        normal_color: int | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Add tetrahedra as a triangle mesh, using coordinates or atom indices.

        Optional flags:
        - draw_edges: draw edges as cylinders (`edge_radius`/`edge_color`).
        - show_normals: draw face normals as arrows (`normal_length`/`normal_color`).
        """

        coords_list = self._normalize_vertices(tetra_coords)
        atom_quads_list = self._normalize_quads(atom_quads)

        if not coords_list and not atom_quads_list:
            raise ValueError("You must provide tetra_coords or atom_quads")

        n = len(coords_list) if coords_list else len(atom_quads_list)

        colors_list = self._normalize_optional_list(colors, n, normalize_color)
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
        if draw_edges is not None:
            options["draw_edges"] = bool(draw_edges)
        if edge_radius is not None:
            options["edge_radius"] = float(puw.get_value(edge_radius, to_unit="angstroms"))
        if edge_color is not None:
            options["edge_color"] = int(edge_color)
        if show_normals is not None:
            options["show_normals"] = bool(show_normals)
        if normal_length is not None:
            options["normal_length"] = float(puw.get_value(normal_length, to_unit="angstroms"))
        if normal_color is not None:
            options["normal_color"] = int(normal_color)
        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag

        self._view._send({"op": "add_tetrahedra", "options": options})
        return layer
