# molsysviewer/shapes/__init__.py

import warnings
from copy import deepcopy
from typing import Any

from smonitor import signal

from .._private.argdigest import digest
from ..scene_history import records_scene_history
from .anisotropy_ellipsoids import AnisotropyEllipsoids
from .channel_tubes import ChannelTubes
from .displacements import DisplacementVectors
from .links import LinkShapes
from .pharmacophore import PharmacophoreShapes
from .pocket_blobs import PocketBlobs
from .pocket_surfaces import PocketSurfaces
from .rings import Rings
from .spheres import SphereShapes
from .tetrahedra import Tetrahedra
from .triangle_faces import TriangleFaces

SHAPE_STYLE_CAPABILITIES: dict[str, frozenset[str]] = {
    "add_sphere": frozenset({"set_color", "set_alpha", "set_radius"}),
    "add_network_links": frozenset({"set_colors", "set_alpha", "set_radii"}),
    "add_channel_tube": frozenset({"set_colors", "set_alpha", "set_radii"}),
    "add_tetrahedra": frozenset({"set_colors", "set_alpha"}),
    "add_triangle_faces": frozenset({"set_colors", "set_alpha"}),
    "add_anisotropy_ellipsoids": frozenset({"set_colors", "set_alpha"}),
    "add_pharmacophore_features": frozenset({"set_colors", "set_alpha", "set_radii"}),
    "add_displacement_vectors": frozenset({"set_radius_scale", "set_length_scale"}),
    "add_pocket_blob": frozenset({"set_alpha", "set_radii", "set_radius_scale"}),
    "add_pocket_surface": frozenset({"set_alpha"}),
    "add_alpha_sphere_set": frozenset(),
    "add_hbonds": frozenset(),
    "add_rings": frozenset(),
    "add_scalar_isosurface": frozenset(),
}


class ShapesManager:
    """Shape manager bound to a MolSysView.

    Provides high-level shortcuts (`add_sphere`, `add_pocket_surface`, etc.)
    and exposes specialized submodules (spheres, pockets, tubes, ellipsoids,
    pharmacophore, etc.).
    """

    def __init__(self, view) -> None:
        self._view = view

        # Specialized submodules
        self.spheres = SphereShapes(view)
        self.pockets = PocketSurfaces(view)
        self.links = LinkShapes(view)
        self.vectors = DisplacementVectors(view)
        self.triangles = TriangleFaces(view)
        self.tetrahedra = Tetrahedra(view)
        self.blobs = PocketBlobs(view)
        self.tubes = ChannelTubes(view)
        self.rings = Rings(view)
        self.ellipsoids = AnisotropyEllipsoids(view)
        self.interaction_sites = PharmacophoreShapes(view)

    def __getitem__(self, tag: str):
        layer = self.get(tag, skip_digestion=True)
        if layer is None:
            raise KeyError(tag)
        return layer

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add(self, kind: str, *, skip_digestion: bool = False, **kwargs):
        """Create a shape of explicit *kind* through its public constructor."""
        methods = {
            "sphere": self.add_sphere,
            "pocket_surface": self.add_pocket_surface,
            "alpha_spheres": self.add_set_alpha_spheres,
            "links": self.add_links,
            "displacement_vectors": self.add_displacement_vectors,
            "triangle_faces": self.add_triangle_faces,
            "tetrahedra": self.add_tetrahedra,
            "pocket_blob": self.add_pocket_blob,
            "scalar_isosurface": self.add_scalar_isosurface,
            "channel_tube": self.add_channel_tube,
            "rings": self.add_rings,
            "anisotropy_ellipsoids": self.add_anisotropy_ellipsoids,
            "interaction_sites": self.add_interaction_sites,
            "pharmacophore_features": self.add_pharmacophore_features,
        }
        normalized = str(kind).strip().lower().replace("-", "_")
        try:
            method = methods[normalized]
        except KeyError as exc:
            raise ValueError(f"Unsupported shape kind {kind!r}; choose from {sorted(methods)}.") from exc
        return method(skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        return [tag for kind, tag in getattr(self._view, "_scene_objects", {}) if kind == "shape"]  # noqa: SLF001

    @signal(tags=["shape"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        layer = getattr(self._view, "_scene_objects", {}).get(("shape", tag))  # noqa: SLF001
        return layer is not None and getattr(layer, "kind", None) == "shape"

    @signal(tags=["shape"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False):
        layer = getattr(self._view, "_scene_objects", {}).get(("shape", tag))  # noqa: SLF001
        if layer is None or getattr(layer, "kind", None) != "shape":
            return None
        return layer

    @signal(tags=["shape"])
    @digest()
    def keys(self, skip_digestion: bool = False) -> list[str]:
        """Return all shape tags."""
        return self.tags(skip_digestion=True)

    @signal(tags=["shape"])
    @digest()
    def values(self, skip_digestion: bool = False) -> list:
        """Return all Shape objects."""
        return [self.get(tag, skip_digestion=True) for tag in self.tags(skip_digestion=True)]

    @signal(tags=["shape"])
    @digest()
    def items(self, skip_digestion: bool = False) -> list[tuple]:
        """Return (tag, Shape) pairs for all shapes."""
        return [(tag, self.get(tag, skip_digestion=True)) for tag in self.tags(skip_digestion=True)]

    @signal(tags=["shape", "query"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        return len(self.tags(skip_digestion=True))

    @signal(tags=["shape", "query"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict]:
        return deepcopy(self._view._shape_history)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        shape = self.get(tag, skip_digestion=True)
        if shape is None:
            raise KeyError(tag)
        shape.delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False):
        shape = self.get(tag, skip_digestion=True)
        if shape is None:
            raise KeyError(tag)
        shape.set_tag(new_tag, skip_digestion=True)
        return shape

    @records_scene_history
    @signal(tags=["shape", "visibility"])
    @digest()
    def show(self, tag: str, skip_digestion: bool = False):
        shape = self.get(tag, skip_digestion=True)
        if shape is None:
            raise KeyError(tag)
        shape.show(skip_digestion=True)
        return shape

    @records_scene_history
    @signal(tags=["shape", "visibility"])
    @digest()
    def hide(self, tag: str, skip_digestion: bool = False):
        shape = self.get(tag, skip_digestion=True)
        if shape is None:
            raise KeyError(tag)
        shape.hide(skip_digestion=True)
        return shape

    @records_scene_history
    @signal(tags=["shape", "visibility"])
    @digest()
    def show_all(self, skip_digestion: bool = False) -> None:
        for tag in self.tags(skip_digestion=True):
            self.show(tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape", "visibility"])
    @digest()
    def hide_all(self, skip_digestion: bool = False) -> None:
        for tag in self.tags(skip_digestion=True):
            self.hide(tag, skip_digestion=True)

    @signal(tags=["shape", "query"])
    @digest()
    def render_status(self, tag: str | None = None, skip_digestion: bool = False):
        """Return runtime render diagnostics for dynamic shapes.

        These diagnostics are reported by the frontend while trajectory-bound
        shapes are resolved. They are runtime-only and are not part of the
        reproducible scene history used for rebuilds or exports.
        """
        statuses = getattr(self._view, "_shape_render_status", {})
        if tag is not None:
            status = statuses.get(tag)
            return None if status is None else dict(status)
        return {key: dict(value) for key, value in statuses.items()}

    @signal(tags=["shape", "query"])
    @digest()
    def info(
        self,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Return a summary of all shapes (or a single shape by tag).

        Each entry contains the wire ``op``, identity, editable style values,
        geometry-derived focus indices and visibility. Lengths remain proper
        PyUnitWizard quantities; wire-format conversion belongs to the viewer
        summary projection.
        """

        def _hex(v: int | None) -> str | None:
            if v is None:
                return None
            try:
                return f"#{int(v):06x}"
            except (TypeError, ValueError):
                return str(v)

        results = []

        def _first(value):
            if isinstance(value, (list, tuple)):
                return value[0] if value else None
            return value

        def _atom_indices(options: dict) -> list[int]:
            indices: set[int] = set()
            for key in ("atom_indices", "atom_pairs", "atom_triplets", "atom_quads"):
                stack = [options.get(key)]
                while stack:
                    value = stack.pop()
                    if isinstance(value, int):
                        indices.add(value)
                    elif isinstance(value, (list, tuple)):
                        stack.extend(value)
            return sorted(indices)

        for msg in getattr(self._view, "_shape_history", []):
            op = msg.get("op", "")
            options = msg.get("options") or {}
            msg_tag = options.get("tag") or msg.get("tag")
            if msg_tag is None:
                continue
            if tag is not None and msg_tag != tag:
                continue

            layer = getattr(self._view, "_scene_objects", {}).get(("shape", msg_tag))
            shape_kind = {
                "add_sphere": "sphere",
                "add_network_links": "link",
                "add_alpha_sphere_set": "alpha-sphere-set",
                "add_hbonds": "hbonds",
                "add_rings": "rings",
                "add_pocket_surface": "pocket-surface",
                "add_pocket_blob": "pocket-blob",
                "add_scalar_isosurface": "scalar-isosurface",
                "add_channel_tube": "channel-tube",
                "add_tetrahedra": "tetrahedra",
                "add_triangle_faces": "triangle-faces",
                "add_anisotropy_ellipsoids": "anisotropy-ellipsoids",
                "add_displacement_vectors": "displacement-vectors",
                "add_pharmacophore_features": "pharmacophore",
                "add_interaction_sites": "interaction-sites",
            }.get(op, op)

            entry: dict = {
                "op": op,
                "kind": shape_kind,
                "tag": msg_tag,
                "owner": None if layer is None else layer.owner,
                "layer_tag": options.get("layer_tag"),
                "color": _hex(options.get("color", _first(options.get("colors")))),
                "n_colors": len(options["colors"]) if isinstance(options.get("colors"), list) else None,
                "n_radii": len(options["radii"]) if isinstance(options.get("radii"), list) else None,
                "alpha": _first(options.get("alpha", options.get("alphas"))),
                "radius_scale": options.get("radius_scale"),
                "length_scale": options.get("length_scale"),
                "visible": False if layer is None else not getattr(layer, "_hidden", False),
                "atom_indices": _atom_indices(options),
                "broken": False if layer is None else bool(getattr(layer, "broken", False)),
                "broken_reason": None if layer is None else getattr(layer, "broken_reason", None),
            }

            from .. import pyunitwizard as puw

            def _to_standard_unit(val, unit="angstrom"):
                if val is None:
                    return None
                return puw.standardize(puw.quantity(val, unit))

            radius = options.get("radius", _first(options.get("radii")))
            if radius is not None:
                entry["radius"] = _to_standard_unit(radius)
            if "center" in options:
                entry["center"] = _to_standard_unit(options["center"])
            if "centers" in options:
                entry["centers"] = _to_standard_unit(options["centers"])
            if "radii" in options:
                entry["radii"] = _to_standard_unit(options["radii"])
            if "vertices" in options:
                entry["vertices"] = _to_standard_unit(options["vertices"])
            if "origins" in options:
                entry["origins"] = _to_standard_unit(options["origins"])
            if "vectors" in options:
                entry["vectors"] = _to_standard_unit(options["vectors"])

            if op == "add_network_links":
                radii = options.get("radii")
                val = radii[0] if isinstance(radii, list) and radii else options.get("radius")
                entry["width"] = _to_standard_unit(val)

            results.append(entry)

        if tag is None:
            return results
        if results:
            return results[0]
        raise ValueError(f"No shape record found for tag {tag!r}.")

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def set_layer_tag(self, tag: str, new_layer_tag: str, skip_digestion: bool = False):
        layer = self.get(tag, skip_digestion=True)
        if layer is None:
            raise ValueError(f"No shape found for tag {tag!r}.")
        layer.set_layer_tag(new_layer_tag, skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_sphere(
        self,
        center="[0.0, 0.0, 0.0] nm",
        radius="1.0 nm",
        color: int = 0x00FF00,
        alpha: float = 0.4,
        tag=None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
        **kwargs,
    ):
        """Add one or more spheres.

        Pass a single ``[x, y, z]`` point for a single sphere (returns a Shape),
        or a list of points for a batch (returns a list of Shapes sharing one
        ``layer_tag``).
        """
        return self.spheres.add_sphere(
            center,
            radius,
            color,
            alpha,
            tag=tag,
            layer_tag=layer_tag,
            skip_digestion=True,
            **kwargs,
        )

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_pocket_surface(self, *, atom_indices, scalars=None, grid=None, alpha=None, iso_levels=None, iso_colors=None, iso_alphas=None, color_map=None, mouth_atom_indices=None, clip_plane=None, tag=None, layer_tag=None, skip_digestion=False):
        return self.pockets.add_pocket_surface(atom_indices=atom_indices, scalars=scalars, grid=grid, alpha=alpha, iso_levels=iso_levels, iso_colors=iso_colors, iso_alphas=iso_alphas, color_map=color_map, mouth_atom_indices=mouth_atom_indices, clip_plane=clip_plane, tag=tag, layer_tag=layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_set_alpha_spheres(self, *, centers, radii, atom_centers=None, atom_radius='1.0 nm', color_alpha_spheres=65280, color_atoms=255, alpha_alpha_spheres=0.3, alpha_atoms=0.5, tag=None, layer_tag=None, skip_digestion=False):
        return self.spheres.add_set_alpha_spheres(centers=centers, radii=radii, atom_centers=atom_centers, atom_radius=atom_radius, color_alpha_spheres=color_alpha_spheres, color_atoms=color_atoms, alpha_alpha_spheres=alpha_alpha_spheres, alpha_atoms=alpha_atoms, tag=tag, layer_tag=layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_links(self, *, atom_pairs=None, coordinate_pairs=None, structure_coordinate_pairs=None, radius='0.2 nm', color=4495871, radii=None, colors=None, pocket_ids=None, chain_ids=None, color_by=None, color_scheme=None, color_table=None, color_mode='link', alpha=1.0, radial_segments=None, tag=None, layer_tag=None, skip_digestion=False):
        return self.links.add_links(atom_pairs=atom_pairs, coordinate_pairs=coordinate_pairs, structure_coordinate_pairs=structure_coordinate_pairs, radius=radius, color=color, radii=radii, colors=colors, pocket_ids=pocket_ids, chain_ids=chain_ids, color_by=color_by, color_scheme=color_scheme, color_table=color_table, color_mode=color_mode, alpha=alpha, radial_segments=radial_segments, tag=tag, layer_tag=layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_displacement_vectors(self, origins, vectors, *, atom_indices=None, length_scale=1.0, min_length='0.0 nm', max_length=None, color_by=None, palette=None, color_mode='norm', color_component=2, color_map=None, radius_scale=0.05, radial_segments=None, tag=None, layer_tag=None, skip_digestion=False):
        return self.vectors.add_displacement_vectors(origins=origins, vectors=vectors, atom_indices=atom_indices, length_scale=length_scale, min_length=min_length, max_length=max_length, color_by=color_by, palette=palette, color_mode=color_mode, color_component=color_component, color_map=color_map, radius_scale=radius_scale, radial_segments=radial_segments, tag=tag, layer_tag=layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_triangle_faces(self, *, vertices=None, structure_vertices=None, atom_triplets=None, colors=13421772, alpha=1.0, alphas=None, labels=None, entity_refs=None, draw_edges=None, edge_radius=None, edge_color=None, show_normals=None, normal_length=None, normal_color=None, tag=None, layer_tag=None, skip_digestion=False):
        return self.triangles.add_triangle_faces(vertices=vertices, structure_vertices=structure_vertices, atom_triplets=atom_triplets, colors=colors, alpha=alpha, alphas=alphas, labels=labels, entity_refs=entity_refs, draw_edges=draw_edges, edge_radius=edge_radius, edge_color=edge_color, show_normals=show_normals, normal_length=normal_length, normal_color=normal_color, tag=tag, layer_tag=layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_tetrahedra(self, *, tetra_coords=None, atom_quads=None, colors=16746496, alphas=0.6, labels=None, entity_refs=None, exterior_only=True, draw_faces=None, faces_pickable=None, face_meta=None, edge_meta=None, draw_edges=None, edge_radius=None, edge_color=None, show_normals=None, normal_length=None, normal_color=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.tetrahedra.add_tetrahedra(tetra_coords=tetra_coords, atom_quads=atom_quads, colors=colors, alphas=alphas, labels=labels, entity_refs=entity_refs, exterior_only=exterior_only, draw_faces=draw_faces, faces_pickable=faces_pickable, face_meta=face_meta, edge_meta=edge_meta, draw_edges=draw_edges, edge_radius=edge_radius, edge_color=edge_color, show_normals=show_normals, normal_length=normal_length, normal_color=normal_color, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_pocket_blob(self, *, centers, radii, radius_scale=None, resolution=None, iso_level=None, iso_levels=None, iso_colors=None, iso_alphas=None, smoothing=None, values=None, color_map=None, alpha=None, wireframe=False, wireframe_size=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.blobs.add_pocket_blob(centers=centers, radii=radii, radius_scale=radius_scale, resolution=resolution, iso_level=iso_level, iso_levels=iso_levels, iso_colors=iso_colors, iso_alphas=iso_alphas, smoothing=smoothing, values=values, color_map=color_map, alpha=alpha, wireframe=wireframe, wireframe_size=wireframe_size, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_scalar_isosurface(self, *, centers, radii, radius_scale=None, resolution=None, iso_level=None, iso_levels=None, iso_colors=None, iso_alphas=None, smoothing=None, values=None, color_map=None, alpha=None, wireframe=False, wireframe_size=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.blobs.add_scalar_isosurface(centers=centers, radii=radii, radius_scale=radius_scale, resolution=resolution, iso_level=iso_level, iso_levels=iso_levels, iso_colors=iso_colors, iso_alphas=iso_alphas, smoothing=smoothing, values=values, color_map=color_map, alpha=alpha, wireframe=wireframe, wireframe_size=wireframe_size, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_channel_tube(self, *, centers, radii, structure_centers=None, color_by=None, palette=None, color_mode=None, solvent_distances=None, colors=None, color_map=None, radial_segments=None, smoothing_subdivisions=None, tube_style=None, tube_aspect_ratio=None, surface_resolution=None, surface_smoothing=None, surface_iso_level=None, surface_radius_scale=None, alpha=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.tubes.add_channel_tube(centers=centers, radii=radii, structure_centers=structure_centers, color_by=color_by, palette=palette, color_mode=color_mode, solvent_distances=solvent_distances, colors=colors, color_map=color_map, radial_segments=radial_segments, smoothing_subdivisions=smoothing_subdivisions, tube_style=tube_style, tube_aspect_ratio=tube_aspect_ratio, surface_resolution=surface_resolution, surface_smoothing=surface_smoothing, surface_iso_level=surface_iso_level, surface_radius_scale=surface_radius_scale, alpha=alpha, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_rings(self, *, centers, normals, radii, thickness=None, colors=None, color_by=None, color_mode=None, values=None, palette=None, color_map=None, segments=None, alpha=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.rings.add_rings(centers=centers, normals=normals, radii=radii, thickness=thickness, colors=colors, color_by=color_by, color_mode=color_mode, values=values, palette=palette, color_map=color_map, segments=segments, alpha=alpha, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_anisotropy_ellipsoids(self, *, centers, eigenvalues=None, eigenvectors=None, tensors=None, principal_directions=None, scale=None, max_eccentricity=None, color_by=None, palette=None, color_mode=None, colors=None, color_map=None, values=None, alpha=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.ellipsoids.add_anisotropy_ellipsoids(centers=centers, eigenvalues=eigenvalues, eigenvectors=eigenvectors, tensors=tensors, principal_directions=principal_directions, scale=scale, max_eccentricity=max_eccentricity, color_by=color_by, palette=palette, color_mode=color_mode, colors=colors, color_map=color_map, values=values, alpha=alpha, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_interaction_sites(self, *, centers, kinds, radii=None, directions=None, alphas=None, colors=None, color_scheme=None, color_table=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        return self.interaction_sites.add_interaction_sites(centers=centers, kinds=kinds, radii=radii, directions=directions, alphas=alphas, colors=colors, color_scheme=color_scheme, color_table=color_table, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def add_pharmacophore_features(self, *, centers, kinds, radii=None, directions=None, alphas=None, colors=None, color_scheme=None, color_table=None, tag=None, layer_tag=None, name=None, skip_digestion=False):
        warnings.warn(
            "shapes.add_pharmacophore_features(...) is deprecated; use shapes.add_interaction_sites(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.interaction_sites.add_interaction_sites(centers=centers, kinds=kinds, radii=radii, directions=directions, alphas=alphas, colors=colors, color_scheme=color_scheme, color_table=color_table, tag=tag, layer_tag=layer_tag, name=name, skip_digestion=True)

    @records_scene_history
    @signal(tags=["shape"])
    @signal(tags=["shape", "topomt"])
    @digest()
    def add_topomt_feature(
        self,
        feature: "Any",
        tag: str | None = None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
        **kwargs,
    ):
        """Add a TopoMT feature (Pocket, Void, Mouth, Channel, BranchedChannel) to the viewer.

        This automatically handles feature dispatching, PyUnitWizard conversions,
        and layer registration.
        """
        # 1. Identify the feature type.
        f_type = getattr(feature, "feature_type", None)
        if f_type is None:
            raise ValueError("The provided object is not a valid TopoMT feature (missing 'feature_type').")

        f_type = str(f_type).lower().strip()

        # 2. Dispatch accordingly.
        if f_type in ("pocket", "void"):
            atom_indices = getattr(feature, "atom_indices", None)
            if atom_indices is None:
                raise ValueError(f"TopoMT feature {feature} has no atom_indices.")

            # Fetch mouth_atom_indices from connected boundaries if available
            mouth_atom_indices = []
            boundaries = getattr(feature, "boundaries", None)
            topography = getattr(feature, "_topography", None)
            if boundaries and topography is not None and getattr(topography, "features", None) is not None:
                for b_id in boundaries:
                    b_feat = topography.features.get(b_id)
                    if b_feat is not None:
                        b_atoms = getattr(b_feat, "atom_indices", None)
                        if b_atoms:
                            mouth_atom_indices.append(list(b_atoms))

            kwargs_passed = dict(kwargs)
            if mouth_atom_indices:
                kwargs_passed["mouth_atom_indices"] = mouth_atom_indices

            return self.add_pocket_surface(
                atom_indices=list(atom_indices), tag=tag, layer_tag=layer_tag, skip_digestion=True, **kwargs_passed
            )

        elif f_type in ("channel", "branched_channel"):
            from .. import pyunitwizard as puw

            # Extract centers and radii
            centers = getattr(feature, "centers", None)
            if centers is None:
                centers = getattr(feature, "coordinates", None)
            if centers is None and getattr(feature, "points", None) is not None:
                pts = feature.points
                if isinstance(pts, (list, tuple, set)):
                    try:
                        centers = [getattr(p, "coordinates", getattr(p, "center", p)) for p in pts]
                    except Exception:
                        pass

            if centers is None:
                raise ValueError(f"TopoMT feature {feature} of type {f_type} has no coordinates or centers.")

            if not puw.is_quantity(centers):
                centers = puw.quantity(centers, "nm")

            radii = getattr(feature, "radii", None)
            if radii is None:
                radii = getattr(feature, "radius", None)
            if radii is None and getattr(feature, "points", None) is not None:
                pts = feature.points
                if isinstance(pts, (list, tuple, set)):
                    try:
                        radii = [getattr(p, "radius", getattr(p, "radii", 1.0)) for p in pts]
                    except Exception:
                        pass

            if radii is None:
                radii = [1.0] * len(centers)

            if not puw.is_quantity(radii):
                radii = puw.quantity(radii, "nm")

            return self.add_channel_tube(
                centers=centers, radii=radii, tag=tag, layer_tag=layer_tag, skip_digestion=True, **kwargs
            )

        elif f_type in ("mouth", "boundary"):
            from .. import pyunitwizard as puw

            atom_indices = getattr(feature, "atom_indices", None)
            if atom_indices is not None and len(atom_indices) > 0:
                centers = getattr(feature, "centers", None)
                if centers is None:
                    centers = getattr(feature, "coordinates", None)
                if centers is not None:
                    if not puw.is_quantity(centers):
                        centers = puw.quantity(centers, "nm")
                    radii = getattr(feature, "radii", getattr(feature, "radius", [1.0] * len(centers)))
                    if not puw.is_quantity(radii):
                        radii = puw.quantity(radii, "nm")
                    return self.add_channel_tube(
                        centers=centers, radii=radii, tag=tag, layer_tag=layer_tag, skip_digestion=True, **kwargs
                    )
                else:
                    return self.add_pocket_surface(
                        atom_indices=list(atom_indices), tag=tag, layer_tag=layer_tag, skip_digestion=True, **kwargs
                    )
            raise ValueError(
                f"TopoMT feature {feature} of type {f_type} has no atom_indices or coordinate points to render."
            )

        else:
            raise NotImplementedError(f"Rendering for TopoMT feature type '{f_type}' is not implemented.")

    @records_scene_history
    @signal(tags=["shape"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False):
        """Delete shapes (all if tag is None, or by tag)."""
        self._view._send({"op": "clear_shapes_by_tag", "tag": tag})
        if hasattr(self._view, "_unregister_scene_object"):
            if tag is None:
                shape_tags = [
                    t for (kind, t), obj in getattr(self._view, "_scene_objects", {}).items() if kind == "shape"
                ]
                for t in shape_tags:
                    self._view._unregister_scene_object("shape", t)
            else:
                self._view._unregister_scene_object("shape", tag)
        else:
            scene_objects = getattr(self._view, "_scene_objects", None)
            if isinstance(scene_objects, dict):
                if tag is None:
                    shape_tags = [t for (kind, t), obj in scene_objects.items() if kind == "shape"]
                    for t in shape_tags:
                        scene_objects.pop(("shape", t), None)
                else:
                    scene_objects.pop(("shape", tag), None)


__all__ = [
    "SHAPE_STYLE_CAPABILITIES",
    "ShapesManager",
    "SphereShapes",
    "PocketSurfaces",
    "LinkShapes",
    "DisplacementVectors",
    "TriangleFaces",
    "Tetrahedra",
    "PocketBlobs",
    "ChannelTubes",
    "Rings",
    "AnisotropyEllipsoids",
    "PharmacophoreShapes",
]
