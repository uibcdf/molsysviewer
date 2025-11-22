# molsysviewer/shapes/__init__.py

from .spheres import SphereShapes
from .pocket_surfaces import PocketSurfaces


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

    # Atajos de conveniencia para mantener la API actual:
    #
    # v.shapes.add_sphere(...)
    # v.shapes.add_spheres(...)
    # v.shapes.add_pocket_surface(...)
    #
    # pero internamente delegamos en `self.spheres`.

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


__all__ = ["ShapesManager", "SphereShapes", "PocketSurfaces"]
