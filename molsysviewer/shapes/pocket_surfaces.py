from __future__ import annotations

from typing import Iterable, Sequence


def _normalize_mouths(mouth_atom_indices: Sequence[int] | Sequence[Sequence[int]]):
    if not isinstance(mouth_atom_indices, Sequence) or isinstance(
        mouth_atom_indices, (str, bytes)
    ):
        raise TypeError("mouth_atom_indices must be a sequence of indices or sequences")

    # Lista de listas (normalizada)
    if all(isinstance(x, Sequence) and not isinstance(x, (str, bytes)) for x in mouth_atom_indices):
        mouths = []
        for mouth in mouth_atom_indices:  # type: ignore[union-attr]
            mouths.append(_normalize_single_mouth(mouth))
        return mouths

    # Lista plana -> una sola boca
    return [_normalize_single_mouth(mouth_atom_indices)]


def _normalize_single_mouth(indices: Iterable[int]):
    values = [int(i) for i in indices]
    if not values:
        raise ValueError("mouth_atom_indices entries must not be empty")
    return values


class PocketSurfaces:
    """Utilidades para superficies de pocket/void basadas en átomos."""

    def __init__(self, view) -> None:
        self._view = view

    def add_pocket_surface(
        self,
        *,
        atom_indices: Sequence[int],
        scalars: Sequence[float] | None = None,
        grid: dict | None = None,
        alpha: float | None = None,
        color_map: str | Sequence[int] | None = None,
        mouth_atom_indices: Sequence[int] | Sequence[Sequence[int]] | None = None,
        clip_plane: dict | None = None,
    ) -> None:
        """Envía al frontend la petición de una superficie tipo pocket/void."""

        if not atom_indices:
            raise ValueError("atom_indices is required and cannot be empty")

        options: dict = {
            "atom_indices": [int(i) for i in atom_indices],
        }

        if scalars is not None:
            options["scalars"] = [float(s) for s in scalars]
        if grid is not None:
            options["grid"] = dict(grid)
        if alpha is not None:
            options["alpha"] = float(alpha)
        if color_map is not None:
            options["color_map"] = color_map

        if mouth_atom_indices is not None:
            options["mouth_atom_indices"] = _normalize_mouths(mouth_atom_indices)
        elif clip_plane is not None:
            options["clip_plane"] = dict(clip_plane)

        self._view._send(
            {
                "op": "add_pocket_surface",
                "options": options,
            }
        )
