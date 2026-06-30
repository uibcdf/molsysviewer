"""Final-boundary adapters from generic geometry payloads to shape APIs."""

from __future__ import annotations

import numpy as np

from . import pyunitwizard as puw
from .geometry import (
    IndexedEdgeGeometry,
    IndexedTriangleGeometry,
    PointGeometry,
    SegmentGeometry,
    SphereGeometry,
    TetrahedraGeometry,
)


def _shape_method(view, manager_name: str, method_name: str):
    shapes = view.shapes
    manager = getattr(shapes, manager_name, None)
    if manager is not None and hasattr(manager, method_name):
        return getattr(manager, method_name)
    return getattr(shapes, method_name)


def _refs(geometry) -> list[dict] | None:
    refs = list(getattr(geometry, "refs", ()) or ())
    return refs or None


def add_point_spheres(view, geometry: PointGeometry, *, radius, **kwargs):
    """Render point geometry as one or more spheres."""
    kwargs.pop("skip_digestion", None)
    coordinates = np.asarray(geometry.coordinates, dtype=float)
    center = coordinates[0] if len(coordinates) == 1 else coordinates
    if len(coordinates) == 1 and isinstance(kwargs.get("color"), (list, tuple)) and len(kwargs["color"]) == 1:
        kwargs["color"] = kwargs["color"][0]
    return _shape_method(view, "spheres", "add_sphere")(
        center=puw.quantity(center, geometry.unit),
        radius=radius,
        skip_digestion=True,
        **kwargs,
    )


def add_uniform_spheres(view, geometry: SphereGeometry, **kwargs):
    """Render sphere geometry with one common radius through add_sphere."""
    kwargs.pop("skip_digestion", None)
    if not geometry.radii:
        return None
    first_radius = geometry.radii[0]
    if any(radius != first_radius for radius in geometry.radii[1:]):
        raise ValueError("add_uniform_spheres requires one common radius.")
    return _shape_method(view, "spheres", "add_sphere")(
        center=puw.quantity(np.asarray(geometry.centers, dtype=float), geometry.unit),
        radius=puw.quantity(first_radius, geometry.unit),
        skip_digestion=True,
        **kwargs,
    )


def add_sphere_set(view, geometry: SphereGeometry, **kwargs):
    """Render variable-radius sphere geometry through add_set_alpha_spheres."""
    kwargs.pop("skip_digestion", None)
    return _shape_method(view, "spheres", "add_set_alpha_spheres")(
        centers=puw.quantity(np.asarray(geometry.centers, dtype=float), geometry.unit),
        radii=puw.quantity(np.asarray(geometry.radii, dtype=float), geometry.unit),
        skip_digestion=True,
        **kwargs,
    )


def add_segments(view, geometry: SegmentGeometry, *, radius, **kwargs):
    """Render segment geometry as link cylinders."""
    kwargs.pop("skip_digestion", None)
    return _shape_method(view, "links", "add_links")(
        coordinate_pairs=puw.quantity(np.asarray(geometry.coordinate_pairs, dtype=float), geometry.unit),
        radius=radius,
        skip_digestion=True,
        **kwargs,
    )


def add_indexed_edges(view, geometry: IndexedEdgeGeometry, *, radius, **kwargs):
    """Render indexed edge geometry as link cylinders."""
    kwargs.pop("skip_digestion", None)
    payload: dict = {"atom_pairs": geometry.atom_pairs}
    if geometry.coordinates:
        payload["coordinate_pairs"] = puw.quantity(np.asarray(geometry.coordinates, dtype=float), geometry.unit)
    return _shape_method(view, "links", "add_links")(
        radius=radius,
        skip_digestion=True,
        **payload,
        **kwargs,
    )


def add_tetrahedra(view, geometry: TetrahedraGeometry, **kwargs):
    """Render tetrahedra while preserving coordinates, pick indices, and refs."""
    kwargs.pop("skip_digestion", None)
    payload: dict = {"atom_quads": geometry.atom_quads}
    if geometry.coordinates:
        payload["tetra_coords"] = puw.quantity(np.asarray(geometry.coordinates, dtype=float), geometry.unit)
    refs = _refs(geometry)
    if refs is not None:
        payload["entity_refs"] = refs
    return _shape_method(view, "tetrahedra", "add_tetrahedra")(
        skip_digestion=True,
        **payload,
        **kwargs,
    )


def add_indexed_triangles(view, geometry: IndexedTriangleGeometry, **kwargs):
    """Render indexed triangles while preserving coordinates, pick indices, and refs."""
    kwargs.pop("skip_digestion", None)
    payload: dict = {"atom_triplets": geometry.atom_triplets}
    if geometry.coordinates:
        payload["vertices"] = puw.quantity(np.asarray(geometry.coordinates, dtype=float), geometry.unit)
    refs = _refs(geometry)
    if refs is not None:
        payload["entity_refs"] = refs
    return _shape_method(view, "triangles", "add_triangle_faces")(
        skip_digestion=True,
        **payload,
        **kwargs,
    )


def add_channel_tube(view, geometry: SphereGeometry, **kwargs):
    """Render ordered sphere geometry as a channel tube."""
    kwargs.pop("skip_digestion", None)
    return _shape_method(view, "tubes", "add_channel_tube")(
        centers=puw.quantity(np.asarray(geometry.centers, dtype=float), geometry.unit),
        radii=puw.quantity(np.asarray(geometry.radii, dtype=float), geometry.unit),
        skip_digestion=True,
        **kwargs,
    )


def add_pocket_blob(view, geometry: SphereGeometry, **kwargs):
    """Render sphere geometry as a pocket blob."""
    kwargs.pop("skip_digestion", None)
    return _shape_method(view, "blobs", "add_pocket_blob")(
        centers=puw.quantity(np.asarray(geometry.centers, dtype=float), geometry.unit),
        radii=puw.quantity(np.asarray(geometry.radii, dtype=float), geometry.unit),
        skip_digestion=True,
        **kwargs,
    )


def add_scalar_isosurface(view, geometry: SphereGeometry, **kwargs):
    """Render sphere geometry as a scalar isosurface."""
    kwargs.pop("skip_digestion", None)
    return _shape_method(view, "blobs", "add_scalar_isosurface")(
        centers=puw.quantity(np.asarray(geometry.centers, dtype=float), geometry.unit),
        radii=puw.quantity(np.asarray(geometry.radii, dtype=float), geometry.unit),
        skip_digestion=True,
        **kwargs,
    )
