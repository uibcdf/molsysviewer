from __future__ import annotations

from typing import Iterable, Sequence

from .._private.arg_digestion import digest


def _normalize_mouths(mouth_atom_indices: Sequence[int] | Sequence[Sequence[int]]):
    if not isinstance(mouth_atom_indices, Sequence) or isinstance(
        mouth_atom_indices, (str, bytes)
    ):
        raise TypeError("mouth_atom_indices must be a sequence of indices or sequences")

    # List of lists (normalized)
    if all(isinstance(x, Sequence) and not isinstance(x, (str, bytes)) for x in mouth_atom_indices):
        mouths = []
        for mouth in mouth_atom_indices:  # type: ignore[union-attr]
            mouths.append(_normalize_single_mouth(mouth))
        return mouths

    # Flat list -> a single mouth
    return [_normalize_single_mouth(mouth_atom_indices)]


def _normalize_single_mouth(indices: Iterable[int]):
    values = [int(i) for i in indices]
    if not values:
        raise ValueError("mouth_atom_indices entries must not be empty")
    return values


class PocketSurfaces:
    """Helpers for pocket/void surfaces based on selected atoms."""

    def __init__(self, view) -> None:
        self._view = view

    @digest()
    def add_pocket_surface(
        self,
        *,
        atom_indices: Sequence[int],
        scalars: Sequence[float] | None = None,
        grid: dict | None = None,
        alpha: float | None = None,
        iso_levels: Sequence[float] | None = None,
        iso_colors: Sequence[int] | None = None,
        iso_alphas: Sequence[float] | None = None,
        color_map: str | Sequence[int] | None = None,
        mouth_atom_indices: Sequence[int] | Sequence[Sequence[int]] | None = None,
        clip_plane: dict | None = None,
        tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Send a pocket/void surface request to the frontend."""

        if atom_indices is None or len(atom_indices) == 0:
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
        if iso_levels is not None:
            options["iso_levels"] = [float(v) for v in iso_levels]
        if iso_colors is not None:
            options["iso_colors"] = [int(c) for c in iso_colors]
        if iso_alphas is not None:
            options["iso_alphas"] = [float(a) for a in iso_alphas]
        if color_map is not None:
            options["color_map"] = color_map

        if mouth_atom_indices is not None:
            options["mouth_atom_indices"] = _normalize_mouths(mouth_atom_indices)
        elif clip_plane is not None:
            options["clip_plane"] = dict(clip_plane)

        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag

        self._view._send(
            {
                "op": "add_pocket_surface",
                "options": options,
            }
        )
        if tag not in self._view._layers:  # noqa: SLF001
            from ..layers import Layer
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001
