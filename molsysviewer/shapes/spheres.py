# molsysviewer/shapes/spheres.py

from typing import Sequence

from ..layers import Layer

class SphereShapes:
    """Sphere helpers for the scene."""

    def __init__(self, view) -> None:
        self._view = view

    def add_sphere(
        self,
        center=(0.0, 0.0, 0.0),
        radius: float = 10.0,
        color: int = 0x00FF00,
        alpha: float = 0.4,
        tag: str | None = None,
    ) -> Layer:
        """Add a (possibly transparent) sphere to the scene."""
        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
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
        # Ensure the layer is immediately available in the Python registry.
        if tag not in self._view._layers:  # noqa: SLF001
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001

    def add_spheres(
        self,
        centers: Sequence[Sequence[float]],
        radii: float | Sequence[float] = 1.0,
        colors: int | Sequence[int] = 0x00FF00,
        alphas: float | Sequence[float] = 0.4,
        tags: str | Sequence[str] | None = None,
    ):
        """Add multiple spheres to the scene.

        Parameters
        ----------
        centers
            Sequence of centers, each `(x, y, z)`.
        radii
            Radius (scalar for all) or a list of radii (one per sphere).
        colors
            Color in `0xRRGGBB` (scalar or list).
        alphas
            Alpha (0.0-1.0), scalar or list.
        tags
            Optional tag (scalar or list, one per sphere).
        """
        centers_list = [list(c) for c in centers]
        n = len(centers_list)

        if n == 0:
            return

        def _as_list(value, n, cast):
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if len(value) != n:
                    raise ValueError(
                        f"Expected {n} values but got {len(value)}."
                    )
                return [cast(v) for v in value]
            else:
                return [cast(value)] * n

        radii = _as_list(radii, n, float)
        colors = _as_list(colors, n, int)
        alphas = _as_list(alphas, n, float)
        tags = _as_list(tags, n, str) if tags is not None else [None] * n

        layers = []
        for c, r, col, a, t in zip(centers_list, radii, colors, alphas, tags):
            layers.append(self.add_sphere(center=c, radius=r, color=col, alpha=a, tag=t))
        return layers

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
    ) -> Layer:
        """Render a set of alpha-spheres (and optionally contact atoms) in a single message.

        - `centers`, `radii`: alpha-sphere positions and radii.
        - `atom_centers`: contact atom centers (optional).
        - Separate colors and alpha for alpha-spheres and atoms.
        - Uses a single message to minimize per-shape overhead.
        """
        centers_list = [list(c) for c in centers]
        radii_list = [float(r) for r in radii]

        if len(centers_list) != len(radii_list):
            raise ValueError("centers and radii must have the same length")

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

        tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        options["tag"] = tag

        self._view._send({"op": "add_alpha_sphere_set", "options": options})
        if tag not in self._view._layers:  # noqa: SLF001
            self._view._layers[tag] = Layer(self._view, tag, kind="shape", meta={})  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001

    def clear(self, tag: str | None = None):
        """Delete shapes in the frontend (all or by tag)."""
        self._view._send({"op": "clear_shapes_by_tag", "tag": tag})
