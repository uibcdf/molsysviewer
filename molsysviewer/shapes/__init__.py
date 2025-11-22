# molsysviewer/shapes/__init__.py

from .spheres import SphereShapes
from .pocket_surfaces import PocketSurfaces
from .links import LinkShapes
from .displacements import DisplacementVectors
from .triangle_faces import TriangleFaces
from .tetrahedra import Tetrahedra


class ShapesManager:
    """Gestor de formas (shapes) asociadas a un MolSysView.

    Expone atajos de alto nivel (add_sphere, add_spheres) y agrupa
    submódulos específicos (por ahora sólo `spheres`).
    """

    def __init__(self, view) -> None:
        self._view = view

        # Submódulos especializados
        self.spheres = SphereShapes(view)
        self.pockets = PocketSurfaces(view)
        self.links = LinkShapes(view)
        self.vectors = DisplacementVectors(view)
        self.triangles = TriangleFaces(view)
        self.tetrahedra = Tetrahedra(view)

    def add_sphere(
        self,
        *args,
        **kwargs,
    ):
        return self.spheres.add_sphere(*args, **kwargs)

    def add_spheres(
        self,
        *args,
        **kwargs,
    ):
        return self.spheres.add_spheres(*args, **kwargs)

    def add_pocket_surface(
        self,
        *args,
        **kwargs,
    ):
        return self.pockets.add_pocket_surface(*args, **kwargs)

    def add_set_alpha_spheres(
        self,
        *args,
        **kwargs,
    ):
        return self.spheres.add_set_alpha_spheres(*args, **kwargs)

    def add_links(
        self,
        *args,
        **kwargs,
    ):
        return self.links.add_links(*args, **kwargs)

    def add_displacement_vectors(
        self,
        *args,
        **kwargs,
    ):
        return self.vectors.add_displacement_vectors(*args, **kwargs)

    def add_triangle_faces(
        self,
        *args,
        **kwargs,
    ):
        return self.triangles.add_triangle_faces(*args, **kwargs)

    def add_tetrahedra(
        self,
        *args,
        **kwargs,
    ):
        return self.tetrahedra.add_tetrahedra(*args, **kwargs)


__all__ = [
    "ShapesManager",
    "SphereShapes",
    "PocketSurfaces",
    "LinkShapes",
    "DisplacementVectors",
    "TriangleFaces",
    "Tetrahedra",
]
