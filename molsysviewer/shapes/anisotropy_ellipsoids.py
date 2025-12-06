from __future__ import annotations

from typing import Iterable, Sequence


class AnisotropyEllipsoids:
    """Visualize oriented ellipsoids/disks from eigenvalues/eigenvectors or tensors."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _normalize_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        normalized: list[list[float]] = []
        for idx, center in enumerate(centers):
            if len(center) != 3:
                raise ValueError(f"centers[{idx}] debe tener 3 coordenadas (x, y, z)")
            normalized.append([float(center[0]), float(center[1]), float(center[2])])
        return normalized

    @staticmethod
    def _normalize_vectors(vectors: Iterable[Sequence[float]] | None) -> list[list[float]] | None:
        if vectors is None:
            return None
        normalized: list[list[float]] = []
        for idx, vec in enumerate(vectors):
            if len(vec) != 3:
                raise ValueError(f"vectors[{idx}] debe tener 3 componentes")
            normalized.append([float(vec[0]), float(vec[1]), float(vec[2])])
        return normalized

    @staticmethod
    def _normalize_matrices(mats: Iterable[Sequence[Sequence[float]]] | None) -> list[list[list[float]]] | None:
        if mats is None:
            return None
        normalized: list[list[list[float]]] = []
        for midx, mat in enumerate(mats):
            rows = list(mat)
            if len(rows) != 3 or any(len(r) != 3 for r in rows):
                raise ValueError(f"tensors[{midx}] debe ser 3x3")
            normalized.append([[float(x) for x in row] for row in rows])
        return normalized

    @staticmethod
    def _normalize_list(values, n: int, cast):
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
    ):
        """Send oriented ellipsoids or flat disks based on anisotropy inputs."""

        centers_list = self._normalize_centers(centers)
        if len(centers_list) == 0:
            raise ValueError("centers no puede estar vacío")

        eigenvalues_list = (
            [list(map(float, ev)) for ev in eigenvalues] if eigenvalues is not None else None
        )
        eigenvectors_list = (
            [self._normalize_vectors(vecs) for vecs in eigenvectors] if eigenvectors is not None else None
        )
        tensors_list = self._normalize_matrices(tensors)
        principal_dirs = self._normalize_vectors(principal_directions)

        if eigenvalues_list is not None and len(eigenvalues_list) != len(centers_list):
            raise ValueError("eigenvalues debe tener la misma longitud que centers")
        if eigenvectors_list is not None and len(eigenvectors_list) != len(centers_list):
            raise ValueError("eigenvectors debe tener la misma longitud que centers")
        if tensors_list is not None and len(tensors_list) != len(centers_list):
            raise ValueError("tensors debe tener la misma longitud que centers")
        if principal_dirs is not None and len(principal_dirs) != len(centers_list):
            raise ValueError("principal_directions debe tener la misma longitud que centers")

        colors_list = self._normalize_list(colors, len(centers_list), int)
        values_list = self._normalize_list(values, len(centers_list), float)

        options: dict = {
            "centers": centers_list,
        }
        if eigenvalues_list is not None:
            options["eigenvalues"] = eigenvalues_list
        if eigenvectors_list is not None:
            options["eigenvectors"] = eigenvectors_list
        if tensors_list is not None:
            options["tensors"] = tensors_list
        if principal_dirs is not None:
            options["principal_directions"] = principal_dirs
        if scale is not None:
            options["scale"] = float(scale)
        if max_eccentricity is not None:
            options["max_eccentricity"] = float(max_eccentricity)
        if color_mode is not None:
            options["color_mode"] = color_mode
        if colors_list is not None:
            options["colors"] = colors_list
        if color_map is not None:
            options["color_map"] = color_map
        if values_list is not None:
            options["values"] = values_list
        if alpha is not None:
            options["alpha"] = float(alpha)
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_anisotropy_ellipsoids", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
