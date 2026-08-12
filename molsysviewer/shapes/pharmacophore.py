from __future__ import annotations

import warnings
from typing import Any, Iterable, Mapping, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from .._private.argdigest import digest
from ..scene_history import records_scene_history
from ..colors import colors as global_colors
from ._registry import register_shape_layer


INTERACTION_COLORS = {
    "donor": 0x3b82f6,        # blue
    "acceptor": 0xef4444,     # red
    "hydrophobe": 0xf59e0b,   # amber
    "aromatic": 0x8b5cf6,     # purple
    "positive": 0x2563eb,     # deep blue
    "negative": 0xf43f5e,     # pink/red
    "metal": 0x10b981,        # green
}
PHARM_COLORS = INTERACTION_COLORS


class PharmacophoreShapes:
    """API for pharmacophore glyphs (spheres/disks/arrows)."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _norm_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        # Extract raw magnitudes in Angstroms (wire format for Mol*)
        centers_raw = puw.get_value(centers, to_unit="angstroms")
        out: list[list[float]] = []
        for idx, c in enumerate(centers_raw):
            if len(c) != 3:
                raise ValueError(f"centers[{idx}] must have 3 coordinates")
            out.append([float(c[0]), float(c[1]), float(c[2])])
        return out

    @staticmethod
    def _norm_vectors(vectors: Iterable[Sequence[float]] | None) -> list[list[float]] | None:
        if vectors is None:
            return None
        import numpy as np
        arr = np.asarray(vectors, dtype=float)
        out: list[list[float]] = []
        for idx, v in enumerate(arr):
            if len(v) != 3:
                raise ValueError(f"directions[{idx}] must have 3 coordinates")
            out.append([float(v[0]), float(v[1]), float(v[2])])
        return out

    def _build_interaction_site_options(
        self,
        *,
        centers: Iterable[Sequence[float]],
        kinds: Sequence[str],
        radii: float | Sequence[float] | None = None,
        directions: Iterable[Sequence[float]] | None = None,
        alphas: float | Sequence[float] | None = None,
        colors: Sequence[int] | None = None,
        color_scheme: str | None = None,
        color_table: Mapping[str, Any] | None = None,
        tag: str | None = None,
        name: str | None = None,
    ) -> dict:
        centers_list = self._norm_centers(centers)
        kinds_list = list(kinds)

        if len(centers_list) != len(kinds_list):
            raise ValueError("centers and kinds must have the same length")

        def _as_list(val, cast, default):
            if val is None:
                return [default] * len(kinds_list)
            if isinstance(val, (str, bytes)) or not isinstance(val, Iterable):
                return [cast(val)] * len(kinds_list)
            seq = list(val)
            if len(seq) not in (1, len(kinds_list)):
                raise ValueError("Unexpected length for a repeatable parameter")
            if len(seq) == 1:
                return [cast(seq[0])] * len(kinds_list)
            return [cast(v) for v in seq]

        radii_raw = puw.get_value(radii, to_unit="angstroms") if radii is not None else None
        radii_list = _as_list(radii_raw, float, 0.6)
        alphas_list = _as_list(alphas, float, 0.6)
        color_registry = getattr(self._view, "colors", global_colors)
        normalized_color_table = None
        resolved_color_scheme = None
        if colors is None:
            if color_table is not None:
                resolved_color_scheme = color_scheme
                normalized_color_table = {
                    str(key).lower(): color_registry.normalize_color(value)
                    for key, value in color_table.items()
                }
            elif color_scheme is not None:
                resolved_scheme = color_registry.resolve_scheme(color_scheme)
                resolved_color_scheme = color_scheme
                normalized_color_table = {
                    str(key).lower(): value for key, value in resolved_scheme.mapping.items()
                }
        colors_list = colors if colors is not None else [
            (normalized_color_table or INTERACTION_COLORS).get(k.lower(), 0xcccccc) for k in kinds_list
        ]
        directions_list = self._norm_vectors(directions)

        options = {
            "centers": centers_list,
            "kinds": kinds_list,
            "radii": radii_list,
            "alphas": alphas_list,
            "colors": colors_list,
        }
        if directions_list is not None:
            options["directions"] = directions_list
        if resolved_color_scheme is not None:
            options["color_scheme"] = resolved_color_scheme
        if normalized_color_table is not None:
            options["color_table"] = dict(normalized_color_table)
        if tag is not None:
            options["tag"] = tag
        if name is not None:
            options["name"] = name
        return options

    @signal(tags=["shape", "pharmacophore"])
    @digest()
    @records_scene_history
    def add_interaction_sites(
        self,
        *,
        centers: Iterable[Sequence[float]],
        kinds: Sequence[str],
        radii: float | Sequence[float] | None = None,
        directions: Iterable[Sequence[float]] | None = None,
        alphas: float | Sequence[float] | None = None,
        colors: Sequence[int] | None = None,
        color_scheme: str | None = None,
        color_table: Mapping[str, Any] | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        name: str | None = None,
        skip_digestion: bool = False,
    ):
        """Render standard interaction-site glyphs (sphere/disk/arrow)."""
        shape_tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, shape_tag, layer_tag=layer_tag)
        options = self._build_interaction_site_options(
            centers=centers,
            kinds=kinds,
            radii=radii,
            directions=directions,
            alphas=alphas,
            colors=colors,
            color_scheme=color_scheme,
            color_table=color_table,
            tag=layer.tag,
            name=name,
        )
        options["layer_tag"] = layer.layer_tag
        self._view._send({"op": "add_pharmacophore_features", "options": options})
        return layer

    @signal(tags=["shape", "pharmacophore"])
    @records_scene_history
    def add_pharmacophore_features(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        """Deprecated alias for `add_interaction_sites(...)`."""
        warnings.warn(
            "add_pharmacophore_features(...) is deprecated; use add_interaction_sites(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.add_interaction_sites(*args, skip_digestion=True, **kwargs)
