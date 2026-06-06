# molsysviewer/shapes/__init__.py

import warnings

from .spheres import SphereShapes
from .pocket_surfaces import PocketSurfaces
from .links import LinkShapes
from .displacements import DisplacementVectors
from .triangle_faces import TriangleFaces
from .tetrahedra import Tetrahedra
from .pocket_blobs import PocketBlobs
from .channel_tubes import ChannelTubes
from .rings import Rings
from .anisotropy_ellipsoids import AnisotropyEllipsoids
from .pharmacophore import PharmacophoreShapes
from smonitor import signal
from .._private.arg_digestion import digest


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

    @signal(tags=["shape"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        return [tag for tag, layer in getattr(self._view, "_scene_objects", {}).items() if getattr(layer, "kind", None) == "shape"]  # noqa: SLF001

    @signal(tags=["shape"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        layer = getattr(self._view, "_scene_objects", {}).get(tag)  # noqa: SLF001
        return layer is not None and getattr(layer, "kind", None) == "shape"

    @signal(tags=["shape"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False):
        layer = getattr(self._view, "_scene_objects", {}).get(tag)  # noqa: SLF001
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
    def info(self, tag: str | None = None, skip_digestion: bool = False) -> list[dict]:
        """Return a summary of all shapes (or a single shape by tag).

        Each entry contains: ``kind``, ``tag``, ``layer_tag``, ``color``,
        ``radius`` / ``width`` (when applicable), and ``visible``.
        """
        from ..colors import normalize_color as _nc

        def _hex(v: int | None) -> str | None:
            if v is None:
                return None
            try:
                return f"#{int(v):06X}"
            except (TypeError, ValueError):
                return str(v)

        results = []
        for msg in getattr(self._view, "_shape_history", []):
            op = msg.get("op", "")
            options = msg.get("options") or {}
            msg_tag = options.get("tag") or msg.get("tag")
            if msg_tag is None:
                continue
            if tag is not None and msg_tag != tag:
                continue

            layer = getattr(self._view, "_scene_objects", {}).get(msg_tag)
            shape_kind = {
                "add_sphere": "sphere",
                "add_network_links": "link",
                "add_alpha_sphere_set": "alpha-sphere-set",
                "add_pocket_surface": "pocket-surface",
                "add_pocket_blob": "pocket-blob",
                "add_channel_tube": "channel-tube",
                "add_tetrahedra": "tetrahedra",
                "add_triangle_faces": "triangle-faces",
                "add_anisotropy_ellipsoids": "anisotropy-ellipsoids",
                "add_displacement_vectors": "displacement-vectors",
                "add_pharmacophore_features": "pharmacophore",
                "add_interaction_sites": "interaction-sites",
            }.get(op, op)

            entry: dict = {
                "kind": shape_kind,
                "tag": msg_tag,
                "layer_tag": options.get("layer_tag"),
                "color": _hex(options.get("color")),
                "visible": False if layer is None else not getattr(layer, "_hidden", False),
            }

            from .. import pyunitwizard as puw
            def _to_standard_unit(val, unit="angstrom"):
                if val is None:
                    return None
                return puw.standardize(puw.quantity(val, unit))

            if "radius" in options:
                entry["radius"] = _to_standard_unit(options["radius"])
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

        return results

    @signal(tags=["shape"])
    @digest()
    def set_layer_tag(self, tag: str, new_layer_tag: str, skip_digestion: bool = False):
        layer = self.get(tag, skip_digestion=True)
        if layer is None:
            raise ValueError(f"No shape found for tag {tag!r}.")
        layer.set_layer_tag(new_layer_tag, skip_digestion=True)
        return layer

    @signal(tags=["shape"])
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
            center, radius, color, alpha,
            tag=tag, layer_tag=layer_tag, skip_digestion=True, **kwargs,
        )


    @signal(tags=["shape"])
    def add_pocket_surface(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.pockets.add_pocket_surface(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_set_alpha_spheres(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.spheres.add_set_alpha_spheres(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_links(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.links.add_links(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_displacement_vectors(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.vectors.add_displacement_vectors(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_triangle_faces(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.triangles.add_triangle_faces(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_tetrahedra(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.tetrahedra.add_tetrahedra(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_pocket_blob(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.blobs.add_pocket_blob(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_channel_tube(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.tubes.add_channel_tube(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_rings(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.rings.add_rings(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_anisotropy_ellipsoids(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.ellipsoids.add_anisotropy_ellipsoids(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_interaction_sites(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.interaction_sites.add_interaction_sites(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_pharmacophore_features(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        warnings.warn(
            "shapes.add_pharmacophore_features(...) is deprecated; use shapes.add_interaction_sites(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.interaction_sites.add_interaction_sites(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
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
                atom_indices=list(atom_indices),
                tag=tag,
                layer_tag=layer_tag,
                skip_digestion=True,
                **kwargs_passed
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
                centers=centers,
                radii=radii,
                tag=tag,
                layer_tag=layer_tag,
                skip_digestion=True,
                **kwargs
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
                        centers=centers,
                        radii=radii,
                        tag=tag,
                        layer_tag=layer_tag,
                        skip_digestion=True,
                        **kwargs
                    )
                else:
                    return self.add_pocket_surface(
                        atom_indices=list(atom_indices),
                        tag=tag,
                        layer_tag=layer_tag,
                        skip_digestion=True,
                        **kwargs
                    )
            raise ValueError(f"TopoMT feature {feature} of type {f_type} has no atom_indices or coordinate points to render.")

        else:
            raise NotImplementedError(f"Rendering for TopoMT feature type '{f_type}' is not implemented.")

    @signal(tags=["shape"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False):
        """Delete shapes (all if tag is None, or by tag)."""
        self._view._send({"op": "clear_shapes_by_tag", "tag": tag})
        if hasattr(self._view, "_unregister_scene_object"):
            if tag is None:
                shape_tags = [t for t, obj in getattr(self._view, "_scene_objects", {}).items() if getattr(obj, "kind", None) == "shape"]
                for t in shape_tags:
                    self._view._unregister_scene_object(t)
            else:
                self._view._unregister_scene_object(tag)
        else:
            scene_objects = getattr(self._view, "_scene_objects", None)
            if isinstance(scene_objects, dict):
                if tag is None:
                    shape_tags = [t for t, obj in scene_objects.items() if getattr(obj, "kind", None) == "shape"]
                    for t in shape_tags:
                        scene_objects.pop(t, None)
                else:
                    scene_objects.pop(tag, None)



__all__ = [
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
