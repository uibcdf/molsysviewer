from __future__ import annotations

from typing import Iterable, Sequence


PHARM_COLORS = {
    "donor": 0x3b82f6,        # blue
    "acceptor": 0xef4444,     # red
    "hydrophobe": 0xf59e0b,   # amber
    "aromatic": 0x8b5cf6,     # purple
    "positive": 0x2563eb,     # deep blue
    "negative": 0xf43f5e,     # pink/red
    "metal": 0x10b981,        # green
}


class PharmacophoreShapes:
    """API for pharmacophore glyphs (spheres/disks/arrows)."""

    def __init__(self, view) -> None:
        self._view = view

    @staticmethod
    def _norm_centers(centers: Iterable[Sequence[float]]) -> list[list[float]]:
        out: list[list[float]] = []
        for idx, c in enumerate(centers):
            if len(c) != 3:
                raise ValueError(f"centers[{idx}] debe tener 3 coords")
            out.append([float(c[0]), float(c[1]), float(c[2])])
        return out

    @staticmethod
    def _norm_vectors(vectors: Iterable[Sequence[float]] | None) -> list[list[float]] | None:
        if vectors is None:
            return None
        out: list[list[float]] = []
        for idx, v in enumerate(vectors):
            if len(v) != 3:
                raise ValueError(f"directions[{idx}] debe tener 3 coords")
            out.append([float(v[0]), float(v[1]), float(v[2])])
        return out

    def add_pharmacophore_features(
        self,
        *,
        centers: Iterable[Sequence[float]],
        kinds: Sequence[str],
        radii: float | Sequence[float] | None = None,
        directions: Iterable[Sequence[float]] | None = None,
        alphas: float | Sequence[float] | None = None,
        colors: Sequence[int] | None = None,
        tag: str | None = None,
        name: str | None = None,
    ) -> None:
        """Render standard pharmacophore glyphs (sphere/disk/arrow)."""
        centers_list = self._norm_centers(centers)
        kinds_list = list(kinds)

        if len(centers_list) != len(kinds_list):
            raise ValueError("centers y kinds deben tener la misma longitud")

        def _as_list(val, cast, default):
            if val is None:
                return [default] * len(kinds_list)
            if isinstance(val, (str, bytes)) or not isinstance(val, Iterable):
                return [cast(val)] * len(kinds_list)
            seq = list(val)
            if len(seq) not in (1, len(kinds_list)):
                raise ValueError("Longitud inesperada en parámetro repetible")
            if len(seq) == 1:
                return [cast(seq[0])] * len(kinds_list)
            return [cast(v) for v in seq]

        radii_list = _as_list(radii, float, 0.6)
        alphas_list = _as_list(alphas, float, 0.6)
        colors_list = colors if colors is not None else [PHARM_COLORS.get(k.lower(), 0xcccccc) for k in kinds_list]
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
        if tag is not None:
            options["tag"] = tag
        if name is not None:
            options["name"] = name

        self._view._send({"op": "add_pharmacophore_features", "options": options})
