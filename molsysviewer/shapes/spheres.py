# molsysviewer/shapes/spheres.py

from typing import Sequence


class SphereShapes:
    """Colección de utilidades para esferas en la escena."""

    def __init__(self, view) -> None:
        self._view = view

    def add_sphere(
        self,
        center=(0.0, 0.0, 0.0),
        radius: float = 10.0,
        color: int = 0x00FF00,
        alpha: float = 0.4,
        tag: str | None = None,
    ) -> None:
        """Añade una esfera (posiblemente transparente) a la escena."""
        self._view._send(
            {
                "op": "add_sphere",
                "options": {
                    "center": list(center),
                    "radius": float(radius),
                    "color": int(color),
                    "alpha": float(alpha),
                    "tag": tag,
                },
            }
        )

    def add_spheres(
        self,
        centers: Sequence[Sequence[float]],
        radii: float | Sequence[float] = 1.0,
        colors: int | Sequence[int] = 0x00FF00,
        alphas: float | Sequence[float] = 0.4,
        tags: str | Sequence[str] | None = None,
    ) -> None:
        """Añade muchas esferas a la escena.

        Parámetros
        ----------
        centers
            Secuencia de centros, cada uno (x, y, z).
        radii
            Radio (escalar para todas) o lista de radios (uno por esfera).
        colors
            Color en 0xRRGGBB (escalar o lista).
        alphas
            Transparencia (0.0-1.0), escalar o lista.
        tags
            Etiqueta opcional (escalar o lista, uno por esfera).
        """
        centers_list = [list(c) for c in centers]
        n = len(centers_list)

        if n == 0:
            return

        def _as_list(value, n, cast):
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if len(value) != n:
                    raise ValueError(
                        f"Esperaba {n} valores pero recibí {len(value)}."
                    )
                return [cast(v) for v in value]
            else:
                return [cast(value)] * n

        radii = _as_list(radii, n, float)
        colors = _as_list(colors, n, int)
        alphas = _as_list(alphas, n, float)
        tags = _as_list(tags, n, str) if tags is not None else [None] * n

        for c, r, col, a, t in zip(centers_list, radii, colors, alphas, tags):
            self.add_sphere(center=c, radius=r, color=col, alpha=a, tag=t)

    def add_set_alpha_spheres(
        self,
        *,
        centers: Sequence[Sequence[float]],
        radii: Sequence[float],
        atom_centers: Sequence[Sequence[float]] | None = None,
        atom_radius: float = 1.0,
        color_alpha_spheres: int = 0x00FF00,
        color_atoms: int = 0x0000FF,
        alpha_alpha_spheres: float = 0.3,
        alpha_atoms: float = 0.5,
        tag: str | None = None,
    ) -> None:
        """Representa un conjunto de alpha-spheres (y opcionalmente los átomos en contacto) en un solo envío.

        - `centers`, `radii`: posiciones y radios de las alpha-spheres.
        - `atom_centers`: centros de los átomos de contacto (si se aportan).
        - Colores y transparencias diferenciadas para alpha-spheres y átomos.
        - Usa un único mensaje para minimizar el overhead de creación individual.
        """
        centers_list = [list(c) for c in centers]
        radii_list = [float(r) for r in radii]

        if len(centers_list) != len(radii_list):
            raise ValueError("centers y radii deben tener la misma longitud")

        options: dict = {
            "alpha_spheres": {
                "centers": centers_list,
                "radii": radii_list,
                "color": int(color_alpha_spheres),
                "alpha": float(alpha_alpha_spheres),
            }
        }

        if atom_centers:
            options["atom_spheres"] = {
                "centers": [list(c) for c in atom_centers],
                "radius": float(atom_radius),
                "color": int(color_atoms),
                "alpha": float(alpha_atoms),
            }

        if tag is not None:
            options["tag"] = tag

        self._view._send({"op": "add_alpha_sphere_set", "options": options})
