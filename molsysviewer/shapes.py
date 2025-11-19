from typing import Any, Sequence

class ShapesModule:

    def __init__(self, view):
        self._view = view

    def add_sphere(
        self,
        center=(0.0, 0.0, 0.0),
        radius: float = 10.0,
        color: int = 0x00FF00,
        alpha: float = 0.4,
        tag: str = None,
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
        color: int | Sequence[int] = 0x00FF00,
        alpha: float | Sequence[float] = 0.4,
        tag: str = None,
    ) -> None:
        """Añade muchas esferas a la escena.

        Parámetros
        ----------
        centers
            Secuencia de centros, cada uno (x, y, z).
        radius
            Radio (escalar para todas) o lista de radios (uno por esfera).
        color
            Color en 0xRRGGBB (escalar o lista).
        alpha
            Transparencia (0.0-1.0), escalar o lista.
        """
        # Normalizamos centers a lista de listas
        centers_list = [list(c) for c in centers]
        n = len(centers_list)

        if n == 0:
            return

        # Helpers para “broadcasting” simple de escalares a listas
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
        colors = _as_list(color, n, int)
        alphas = _as_list(alpha, n, float)

        for c, r, col, a in zip(centers_list, radii, colors, alphas):
            self.add_sphere(center=c, radius=r, color=col, alpha=a, tag=tag)
