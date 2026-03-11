# molsysviewer/shapes/__init__.py

from .spheres import SphereShapes
from .pocket_surfaces import PocketSurfaces
from .links import LinkShapes
from .displacements import DisplacementVectors
from .triangle_faces import TriangleFaces
from .tetrahedra import Tetrahedra
from .pocket_blobs import PocketBlobs
from .channel_tubes import ChannelTubes
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
        self.ellipsoids = AnisotropyEllipsoids(view)
        self.ph4 = PharmacophoreShapes(view)

    @signal(tags=["shape"])
    def add_sphere(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.spheres.add_sphere(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_spheres(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.spheres.add_spheres(*args, skip_digestion=True, **kwargs)

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
    def add_anisotropy_ellipsoids(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.ellipsoids.add_anisotropy_ellipsoids(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    def add_pharmacophore_features(
        self,
        *args,
        skip_digestion: bool = False,
        **kwargs,
    ):
        return self.ph4.add_pharmacophore_features(*args, skip_digestion=True, **kwargs)

    @signal(tags=["shape"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False):
        """Delete shapes (all if tag is None, or by tag)."""
        self._view._send({"op": "clear_shapes_by_tag", "tag": tag})


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
    "AnisotropyEllipsoids",
    "PharmacophoreShapes",
]
