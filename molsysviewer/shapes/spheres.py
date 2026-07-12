# molsysviewer/shapes/spheres.py

from typing import Sequence
import numpy as np
import molsysmt as msm
from smonitor import signal

from .. import pyunitwizard as puw
from ..layers import Layer, Shape
from .._private.arg_digestion import digest
from ..colors import normalize_color
from ._registry import register_shape_layer, normalize_new_shape_tag


def _resolve_batch_tags(view, n: int, tag) -> list[str]:
    """Return a list of *n* unique shape tags for a batch call.

    Rules
    -----
    - ``tag`` is a list  → use as-is (must have length *n*).
    - ``tag`` is a str   → generate ``tag1``, ``tag2``, … ``tagN``.
    - ``tag`` is None    → use the view's auto-counter (``shape1``, ``shape2``, …).
    """
    if tag is None:
        return [view._next_shape_tag() for _ in range(n)]  # noqa: SLF001
    if isinstance(tag, str):
        prefix = tag.strip()
        return [f"{prefix}{i + 1}" for i in range(n)]
    tags = list(tag)
    if len(tags) != n:
        raise ValueError(f"Expected {n} tags but got {len(tags)}.")
    return [str(t) for t in tags]


class SphereShapes:
    """Sphere helpers for the scene."""

    def __init__(self, view) -> None:
        self._view = view

    @signal(tags=["shape", "sphere"])
    @digest()
    def add_sphere(
        self,
        center="[0.0, 0.0, 0.0] nm",
        radius="1.0 nm",
        color: int = 0x00FF00,
        alpha: float = 0.4,
        tag: str | list | None = None,
        layer_tag: str | None = None,
        structure_centers=None,
        selection: str | None = None,
        atom_indices: Sequence[int] | None = None,
        structures_atom_indices: Sequence[Sequence[int]] | None = None,
        skip_digestion: bool = False,
        **kwargs,
    ):
        """Add one or more spheres to the scene.

        When *center* is a single 3-D point the call returns a single
        :class:`~molsysviewer.layers.Shape`.

        When *center* is a sequence of points a batch is created: all spheres
        share one ``layer_tag`` so they can be shown/hidden/deleted as a group,
        while each sphere keeps its own unique ``tag``.  The return value is a
        list of :class:`~molsysviewer.layers.Shape` objects.

        Parameters
        ----------
        center
            Single ``[x, y, z]`` point (with puw units) **or** a list/array of
            such points for a batch call.
        radius
            Radius scalar **or** a list of radii (one per sphere in a batch).
        color
            Color as ``0xRRGGBB`` integer (scalar or list).
        alpha
            Opacity 0–1 (scalar or list).
        tag
            Single tag (single sphere), list of tags (batch 1:1 mapping), or
            prefix string (batch generates ``prefix1``, ``prefix2``, …).
            Defaults to auto-generated ``shapeN`` names.
        layer_tag
            Shared layer tag for the batch.  Defaults to the single sphere's
            own tag (single) or a new auto-generated ``layerN`` (batch).
        """
        import warnings
        if "centers" in kwargs:
            warnings.warn("'centers' is deprecated; use 'center'.", DeprecationWarning, stacklevel=2)
            center = kwargs.pop("centers")
        if "radii" in kwargs:
            warnings.warn("'radii' is deprecated; use 'radius'.", DeprecationWarning, stacklevel=2)
            radius = kwargs.pop("radii")
        if "colors" in kwargs:
            warnings.warn("'colors' is deprecated; use 'color'.", DeprecationWarning, stacklevel=2)
            color = kwargs.pop("colors")
        if "alphas" in kwargs:
            warnings.warn("'alphas' is deprecated; use 'alpha'.", DeprecationWarning, stacklevel=2)
            alpha = kwargs.pop("alphas")

        # Resolve selection using MolSysMT if provided
        if selection is not None:
            n_structures = msm.get(self._view._molsys, element="system", n_structures=True)
            if n_structures > 1:
                indices_per_frame = []
                for frame in range(n_structures):
                    indices = msm.select(self._view._molsys, selection=selection, structure_indices=frame)
                    indices_per_frame.append([int(idx) for idx in indices])
                # Check if they are all identical
                first = indices_per_frame[0]
                if all(indices == first for indices in indices_per_frame):
                    atom_indices = first
                else:
                    structures_atom_indices = indices_per_frame
            else:
                indices = msm.select(self._view._molsys, selection=selection)
                atom_indices = [int(idx) for idx in indices]

        # Detect batch vs single by inspecting the resolved numpy array.
        # `center`/`radius` arrive as digested length quantities; Mol* wants
        # angstroms, so convert explicitly at this boundary.
        try:
            arr = np.asarray(puw.get_value(center, to_unit="angstroms"), dtype=float)
        except Exception:
            arr = None

        is_batch = arr is not None and arr.ndim == 2

        if is_batch:
            return self._add_sphere_batch(arr, radius, color, alpha, tag=tag, layer_tag=layer_tag)

        # ── Single sphere ──────────────────────────────────────────────────────
        resolved_tag = (tag if isinstance(tag, str) else None) or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(
            self._view,
            resolved_tag,
            layer_tag=layer_tag,
            meta={"shape_kind": "sphere", "shape_name": "Sphere"},
        )
        center_val = arr.tolist() if arr is not None else [float(v) for v in puw.get_value(center, to_unit="angstroms")]
        options: dict = {
            "center": center_val,
            "radius": float(puw.get_value(radius, to_unit="angstroms")),
            "color": normalize_color(color),
            "alpha": float(alpha),
            "tag": layer.tag,
            "layer_tag": layer.layer_tag,
        }
        if atom_indices is not None:
            options["atom_indices"] = [int(i) for i in atom_indices]
        if structures_atom_indices is not None:
            options["structures_atom_indices"] = [
                None if f is None else [int(i) for i in f]
                for f in structures_atom_indices
            ]

        if structure_centers is not None:
            fc_arr = np.asarray(puw.get_value(structure_centers, to_unit="angstroms"), dtype=float)
            options["structures_coords"] = [
                fc_arr[i].tolist() if fc_arr[i] is not None else None
                for i in range(len(fc_arr))
            ]
        self._view._send({"op": "add_sphere", "options": options})  # noqa: SLF001
        return layer

    def _add_sphere_batch(
        self,
        centers_arr: np.ndarray,
        radii,
        colors,
        alphas,
        *,
        tag,
        layer_tag: str | None,
    ) -> list:
        """Internal batch path — all spheres share one ``layer_tag``."""
        n = len(centers_arr)
        if n == 0:
            return []

        # Shared layer tag
        shared_layer_tag = str(layer_tag).strip() if layer_tag is not None else self._view._next_layer_tag()  # noqa: SLF001
        if hasattr(self._view, "_ensure_layer_group"):
            self._view._ensure_layer_group(shared_layer_tag, kind="shape")  # noqa: SLF001

        resolved_tags = _resolve_batch_tags(self._view, n, tag)

        def _as_list(value, cast):
            if isinstance(value, (list, tuple, np.ndarray)) and not isinstance(value, (str, bytes)):
                seq = list(value)
                if len(seq) == 1:
                    return [cast(seq[0])] * n
                if len(seq) != n:
                    raise ValueError(f"Expected 1 or {n} values but got {len(seq)}.")
                return [cast(v) for v in seq]
            return [cast(value)] * n

        radii_list = _as_list(puw.get_value(radii, to_unit="angstroms"), float)
        colors_list = _as_list(colors, normalize_color)
        alphas_list = _as_list(alphas, float)

        layers = []
        objects = getattr(self._view, "_scene_objects", {})
        for i, (c, r, col, a, t) in enumerate(
            zip(centers_arr.tolist(), radii_list, colors_list, alphas_list, resolved_tags)
        ):
            normalized_tag = normalize_new_shape_tag(self._view, t)
            shape = Shape(
                self._view,
                normalized_tag,
                layer_tag=shared_layer_tag,
                meta={"shape_kind": "sphere", "shape_name": "Sphere"},
            )
            objects[("shape", normalized_tag)] = shape
            self._view._send(  # noqa: SLF001
                {
                    "op": "add_sphere",
                    "options": {
                        "center": c,
                        "radius": r,
                        "color": col,
                        "alpha": a,
                        "tag": normalized_tag,
                        "layer_tag": shared_layer_tag,
                    },
                }
            )
            layers.append(shape)
        return layers


    @signal(tags=["shape", "sphere"])
    @digest()
    def add_set_alpha_spheres(
        self,
        *,
        centers: Sequence[Sequence[float]],
        radii: Sequence[float],
        atom_centers: Sequence[Sequence[float]] | None = None,
        atom_radius="1.0 nm",
        color_alpha_spheres: int = 0x00FF00,
        color_atoms: int = 0x0000FF,
        alpha_alpha_spheres: float = 0.3,
        alpha_atoms: float = 0.5,
        tag: str | None = None,
        layer_tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Render a set of alpha-spheres (and optionally contact atoms) in a single message.

        - `centers`, `radii`: alpha-sphere positions and radii.
        - `atom_centers`: contact atom centers (optional).
        - Separate colors and alpha for alpha-spheres and atoms.
        - Uses a single message to minimize per-shape overhead.
        """
        centers_raw = puw.get_value(centers, to_unit="angstroms")
        centers_list = [list(c) for c in centers_raw]
        radii_raw = puw.get_value(radii, to_unit="angstroms")
        radii_list = [float(r) for r in radii_raw]

        if len(centers_list) != len(radii_list):
            raise ValueError("centers and radii must have the same length")

        options: dict = {
            "alpha_spheres": {
                "centers": centers_list,
                "radii": radii_list,
                "color": normalize_color(color_alpha_spheres),
                "alpha": float(alpha_alpha_spheres),
            }
        }

        if atom_centers is not None:
            atom_centers_raw = puw.get_value(atom_centers, to_unit="angstroms")
            options["atom_spheres"] = {
                "centers": [list(c) for c in atom_centers_raw],
                "radius": float(puw.get_value(atom_radius, to_unit="angstroms")),
                "color": normalize_color(color_atoms),
                "alpha": float(alpha_atoms),
            }

        tag = tag or self._view._next_shape_tag()  # noqa: SLF001
        layer = register_shape_layer(self._view, tag, layer_tag=layer_tag)
        options["tag"] = layer.tag

        self._view._send({"op": "add_alpha_sphere_set", "options": options})
        return layer

    @signal(tags=["shape", "sphere"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False):
        """Delete shapes in the frontend (all or by tag)."""
        self._view._send({"op": "clear_shapes_by_tag", "tag": tag})
        if hasattr(self._view, "_unregister_scene_object"):
            if tag is None:
                shape_tags = [t for (kind, t), obj in getattr(self._view, "_scene_objects", {}).items() if kind == "shape"]
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
