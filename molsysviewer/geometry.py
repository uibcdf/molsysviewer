"""Viewer-neutral geometry payloads for final MolSysViewer shape adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json

import numpy as np


MESH_LOCAL = "mesh_local"
MOLECULAR_SYSTEM = "molecular_system"
VIEWER_LOCAL = "viewer_local"


def _require_unit(unit: str, owner: str) -> str:
    text = str(unit).strip()
    if text == "":
        raise ValueError(f"{owner}.unit is required.")
    return text


def _points(values: Any, *, owner: str = "Geometry") -> tuple[tuple[float, float, float], ...]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return ()
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError(f"{owner} coordinates must have shape (n, 3).")
    return tuple(tuple(float(value) for value in point) for point in array)


def _indexed(values: Any, *, size: int, owner: str) -> tuple[tuple[int, ...], ...]:
    items = tuple(tuple(int(value) for value in item) for item in values)
    if any(len(item) != size for item in items):
        raise ValueError(f"{owner} indices must contain {size} entries each.")
    return items


def _jsonable_payload(value: Any, *, owner: str) -> dict[str, Any]:
    if isinstance(value, EntityRef):
        payload = value.to_payload()
    else:
        payload = dict(value)
    try:
        json.dumps(payload)
    except TypeError as exc:
        raise ValueError(f"{owner} entity references must be JSON-serializable.") from exc
    return payload


def entity_ref_payload(ref: "EntityRef | dict[str, Any]") -> dict[str, Any]:
    """Return a JSON-serializable entity-reference payload."""
    return _jsonable_payload(ref, owner="EntityRef")


@dataclass(frozen=True)
class EntityRef:
    """Structured identity carried separately from geometric coordinates."""

    kind: str
    entity_id: Any
    atom_indices: tuple[int, ...] = ()
    atom_index_space: str = MOLECULAR_SYSTEM
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if str(self.kind).strip() == "":
            raise ValueError("EntityRef.kind is required.")
        object.__setattr__(self, "atom_indices", tuple(int(index) for index in self.atom_indices))
        payload = self.to_payload()
        try:
            json.dumps(payload)
        except TypeError as exc:
            raise ValueError("EntityRef must be JSON-serializable.") from exc

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "entity_id": self.entity_id,
            "atom_indices": list(self.atom_indices),
            "atom_index_space": self.atom_index_space,
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class PointGeometry:
    """Point geometry with mandatory units and one reference per point."""

    coordinates: tuple[tuple[float, float, float], ...]
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        coordinates = _points(self.coordinates, owner="PointGeometry")
        refs = tuple(_jsonable_payload(ref, owner="PointGeometry") for ref in self.refs)
        if refs and len(coordinates) != len(refs):
            raise ValueError("PointGeometry requires one entity reference per point.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "PointGeometry"))
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True)
class SphereGeometry:
    """Sphere geometry with mandatory units and one radius per center."""

    centers: tuple[tuple[float, float, float], ...]
    radii: tuple[float, ...]
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        centers = _points(self.centers, owner="SphereGeometry")
        radii = tuple(float(radius) for radius in self.radii)
        refs = tuple(_jsonable_payload(ref, owner="SphereGeometry") for ref in self.refs)
        if len(centers) != len(radii):
            raise ValueError("SphereGeometry requires one radius per center.")
        if refs and len(centers) != len(refs):
            raise ValueError("SphereGeometry requires one entity reference per center when refs are provided.")
        if any(radius < 0.0 for radius in radii):
            raise ValueError("SphereGeometry radii must be non-negative.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "SphereGeometry"))
        object.__setattr__(self, "centers", centers)
        object.__setattr__(self, "radii", radii)
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True)
class SegmentGeometry:
    """Line-segment geometry with mandatory units."""

    starts: tuple[tuple[float, float, float], ...]
    ends: tuple[tuple[float, float, float], ...]
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        starts = _points(self.starts, owner="SegmentGeometry")
        ends = _points(self.ends, owner="SegmentGeometry")
        refs = tuple(_jsonable_payload(ref, owner="SegmentGeometry") for ref in self.refs)
        if len(starts) != len(ends):
            raise ValueError("SegmentGeometry requires one end point per start point.")
        if refs and len(starts) != len(refs):
            raise ValueError("SegmentGeometry requires one entity reference per segment when refs are provided.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "SegmentGeometry"))
        object.__setattr__(self, "starts", starts)
        object.__setattr__(self, "ends", ends)
        object.__setattr__(self, "refs", refs)

    @property
    def coordinate_pairs(self) -> tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]:
        return tuple(zip(self.starts, self.ends, strict=True))


@dataclass(frozen=True)
class TetrahedraGeometry:
    """Tetrahedra geometry with explicit atom-index-space metadata."""

    coordinates: tuple[tuple[tuple[float, float, float], ...], ...]
    atom_quads: tuple[tuple[int, int, int, int], ...]
    atom_index_space: str
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if str(self.atom_index_space).strip() == "":
            raise ValueError("TetrahedraGeometry.atom_index_space is required.")
        quads = _indexed(self.atom_quads, size=4, owner="TetrahedraGeometry")
        coordinates = tuple(_points(item, owner="TetrahedraGeometry") for item in self.coordinates)
        refs = tuple(_jsonable_payload(ref, owner="TetrahedraGeometry") for ref in self.refs)
        if coordinates and len(coordinates) != len(quads):
            raise ValueError("TetrahedraGeometry coordinates must match atom quads.")
        if refs and len(quads) != len(refs):
            raise ValueError("TetrahedraGeometry requires one entity reference per tetrahedron when refs are provided.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "TetrahedraGeometry"))
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "atom_quads", quads)
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True)
class IndexedTriangleGeometry:
    """Triangle geometry with explicit atom-index-space metadata."""

    coordinates: tuple[tuple[tuple[float, float, float], ...], ...]
    atom_triplets: tuple[tuple[int, int, int], ...]
    atom_index_space: str
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if str(self.atom_index_space).strip() == "":
            raise ValueError("IndexedTriangleGeometry.atom_index_space is required.")
        triplets = _indexed(self.atom_triplets, size=3, owner="IndexedTriangleGeometry")
        coordinates = tuple(_points(item, owner="IndexedTriangleGeometry") for item in self.coordinates)
        refs = tuple(_jsonable_payload(ref, owner="IndexedTriangleGeometry") for ref in self.refs)
        if coordinates and len(coordinates) != len(triplets):
            raise ValueError("IndexedTriangleGeometry coordinates must match atom triplets.")
        if refs and len(triplets) != len(refs):
            raise ValueError("IndexedTriangleGeometry requires one entity reference per triangle when refs are provided.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "IndexedTriangleGeometry"))
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "atom_triplets", triplets)
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True)
class IndexedEdgeGeometry:
    """Edge geometry with explicit atom-index-space metadata."""

    coordinates: tuple[tuple[tuple[float, float, float], ...], ...]
    atom_pairs: tuple[tuple[int, int], ...]
    atom_index_space: str
    unit: str
    refs: tuple[EntityRef | dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if str(self.atom_index_space).strip() == "":
            raise ValueError("IndexedEdgeGeometry.atom_index_space is required.")
        pairs = _indexed(self.atom_pairs, size=2, owner="IndexedEdgeGeometry")
        coordinates = tuple(_points(item, owner="IndexedEdgeGeometry") for item in self.coordinates)
        refs = tuple(_jsonable_payload(ref, owner="IndexedEdgeGeometry") for ref in self.refs)
        if coordinates and len(coordinates) != len(pairs):
            raise ValueError("IndexedEdgeGeometry coordinates must match atom pairs.")
        if refs and len(pairs) != len(refs):
            raise ValueError("IndexedEdgeGeometry requires one entity reference per edge when refs are provided.")
        object.__setattr__(self, "unit", _require_unit(self.unit, "IndexedEdgeGeometry"))
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "atom_pairs", pairs)
        object.__setattr__(self, "refs", refs)
