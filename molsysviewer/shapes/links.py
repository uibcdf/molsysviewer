"""Helpers to render custom links/cylinders."""

from __future__ import annotations

from typing import Iterable, Sequence

from smonitor import signal

from .. import pyunitwizard as puw
from ._units import to_wire_angstroms
from .._private.arg_digestion import digest
from ..colors import colors as global_colors, normalize_color
from ._registry import register_shape_layer


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
                raise ValueError(f"Each pair must have length {expected_len}, got {len(pair)}")
            normalized.append([int(pair[0]), int(pair[1])])
        return normalized

    @staticmethod
    def _to_coord_pairs(coords: Iterable[Sequence[Sequence[float]]] | None) -> list[list[list[float]]]:
        if coords is None:
            return []

        # Internal length representation is nanometers; convert to the Mol*
        # angstrom wire format at this edge (bare values are treated as nm).
        coords_raw = to_wire_angstroms(coords)

        normalized: list[list[list[float]]] = []
        for pair in coords_raw:
            if len(pair) != 2:
                raise ValueError("Each entry in coordinate_pairs must have two points (start, end)")
            start, end = pair
            if len(start) != 3 or len(end) != 3:
                raise ValueError("Each point must have 3 coordinates (x, y, z)")
            normalized.append([[float(start[0]), float(start[1]), float(start[2])], [float(end[0]), float(end[1]), float(end[2])]])
        return normalized

    @staticmethod
    def _to_coord_pairs_raw(coords: Iterable | None) -> list[list[list[float]]]:
        """Like _to_coord_pairs but skips puw conversion — for raw Angstrom data."""
        if coords is None:
            return []
        normalized: list[list[list[float]]] = []
        for pair in coords:
            if len(pair) != 2:
                raise ValueError("Each entry must have two points (start, end)")
            start, end = pair
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
            raise ValueError(f"Expected 1 or {n} values, got {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * n
        return [cast(v) for v in seq]

    @signal(tags=["shape", "link"])
    @digest()
    def add_links(
        self,
        *,
        atom_pairs: Iterable[Sequence[int]] | None = None,
        coordinate_pairs: Iterable[Sequence[Sequence[float]]] | None = None,
        structure_coordinate_pairs: Iterable | None = None,
        radius="0.2 nm",
        color: int | Sequence[int] = 0x4499ff,
        radii=None,
        colors=None,
        pocket_ids: Sequence[int | str] | None = None,
        chain_ids: Sequence[str] | None = None,
        color_by: str | None = None,
        color_scheme: str | None = None,
        color_table: dict | None = None,
        color_mode: str = "link",
        alpha: float = 1.0,
        radial_segments: int | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Add cylinders/bars connecting pairs of points or atoms.

        Parameters
        ----------
        atom_pairs
            Pairs of atom indices (0-based) to connect. If provided, the current
            coordinates of the loaded structure are used.
        coordinate_pairs
            Lista de pares de coordenadas [[x1, y1, z1], [x2, y2, z2]].
        radii, colors
            Scalars or lists (one per link) for radius and color.
        pocket_ids, chain_ids
            Optional identifiers to color by pocket or chain.
        color_by
            Preferred categorical color driver for the new API surface.
            Currently `"link"`, `"pocket"`, or `"chain"`.
        color_scheme
            Optional categorical color scheme name resolved through the Python
            color registry.
        color_table
            Optional explicit mapping for categorical colors.
        color_mode
            Legacy alias for `color_by`.
        alpha
            Global alpha (0-1).
        radial_segments
            Cylinder radial segments (>=3). Default is 16.
        tag
            Optional tag for the Mol* state node.
        """

        import warnings
        if radii is not None:
            warnings.warn("'radii' is deprecated; use 'radius'.", DeprecationWarning, stacklevel=2)
            radius = radii
        if colors is not None:
            warnings.warn("'colors' is deprecated; use 'color'.", DeprecationWarning, stacklevel=2)
            color = colors

        coordinate_pairs_list = self._to_coord_pairs(coordinate_pairs)
        atom_pairs_list = self._to_pair_list(atom_pairs) if atom_pairs is not None else []

        structures_list: list | None = None
        if structure_coordinate_pairs is not None:
            structures_list = [
                self._to_coord_pairs_raw(fcp) if fcp is not None else None
                for fcp in structure_coordinate_pairs
            ]
            if not coordinate_pairs_list and structures_list and structures_list[0] is not None:
                coordinate_pairs_list = structures_list[0]

        if not coordinate_pairs_list and not atom_pairs_list:
            raise ValueError("You must provide coordinate_pairs or atom_pairs")

        n_links = len(coordinate_pairs_list) if coordinate_pairs_list else len(atom_pairs_list)

        # Extract raw magnitudes in Angstroms (wire format for Mol*)
        radii_raw = to_wire_angstroms(radius)
        radii_list = self._normalize_optional_list(radii_raw, n_links, float)
        colors_list = self._normalize_optional_list(color, n_links, normalize_color)
        pocket_ids_list = self._normalize_optional_list(pocket_ids, n_links, lambda v: v)
        chain_ids_list = self._normalize_optional_list(chain_ids, n_links, str)
        color_registry = getattr(self._view, "colors", global_colors)
        resolved_color_by = color_by or color_mode
        normalized_color_table = None
        dynamic_categories = None
        if resolved_color_by == "chain" and chain_ids_list is not None:
            dynamic_categories = [str(item) for item in chain_ids_list]
        elif resolved_color_by == "pocket" and pocket_ids_list is not None:
            dynamic_categories = [str(item) for item in pocket_ids_list]
        if color_table is not None:
            normalized_color_table = {
                str(key): color_registry.normalize_color(value) for key, value in color_table.items()
            }
        elif color_scheme is not None:
            resolved_scheme = color_registry.resolve_scheme(color_scheme, categories=dynamic_categories)
            normalized_color_table = dict(resolved_scheme.mapping)

        options: dict = {
            "mode": "atom-indices" if atom_pairs_list else "coordinates",
            "alpha": float(alpha),
            "color_mode": resolved_color_by,
            "color_by": resolved_color_by,
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
        if color_scheme is not None:
            options["color_scheme"] = color_scheme
        if normalized_color_table is not None:
            options["color_table"] = normalized_color_table
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)
        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(
            self._view,
            tag,
            layer_tag=layer_tag,
            meta={"shape_kind": "links", "shape_name": "Links"},
        )
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag
        if structures_list is not None:
            options["structures_coords"] = structures_list

        self._view._send({"op": "add_network_links", "options": options})
        return layer

    @signal(tags=["shape", "link"])
    @digest()
    def add_hbonds(
        self,
        *,
        structures,
        radius="0.1 nm",
        color: int = 0x4499ff,
        alpha: float = 0.8,
        radial_segments: int | None = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Add hydrogen-bond links that vary per structure.

        Parameters
        ----------
        structures
            List indexed by structure. Each entry is either ``None`` (no
            H-bonds visible on that structure) or a list of ``[donor, acceptor]``
            atom-index pairs (0-based).  Example::

                viewer.shapes.links.add_hbonds(structures=[
                    None,
                    [[3, 7], [8, 35]],
                    None,
                    [[1, 9], [24, 27]],
                ])

        radius
            Cylinder radius (puw quantity or plain value in nm).
        color
            Default link colour as ``0xRRGGBB``.
        alpha
            Global opacity 0–1.
        radial_segments
            Cylinder facet count (default 16).
        """
        structures_list = [
            [[int(d), int(a)] for d, a in entry] if entry is not None else None
            for entry in structures
        ]

        radius_ang = float(to_wire_angstroms(radius))

        options: dict = {
            "structures_atom_pairs": structures_list,
            "radii": [radius_ang],
            "colors": [normalize_color(color)],
            "alpha": float(alpha),
        }
        if radial_segments is not None:
            options["radial_segments"] = int(radial_segments)

        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(
            self._view,
            tag,
            layer_tag=layer_tag,
            meta={"shape_kind": "links", "shape_name": "H-bonds"},
        )
        options["tag"] = layer.tag
        options["layer_tag"] = layer.layer_tag

        self._view._send({"op": "add_hbonds", "options": options})
        return layer
