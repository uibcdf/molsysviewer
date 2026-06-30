from __future__ import annotations

import pytest

from molsysviewer import (
    EntityRef,
    IndexedTriangleGeometry,
    MESH_LOCAL,
    MOLECULAR_SYSTEM,
    MolSysView,
    PointGeometry,
    SegmentGeometry,
    SphereGeometry,
    TetrahedraGeometry,
    entity_ref_payload,
)
from molsysviewer import shape_adapters


def test_geometry_payloads_validate_units_and_aligned_refs():
    ref = EntityRef("demo.point", "p1", atom_indices=(1, 2), atom_index_space=MOLECULAR_SYSTEM)
    geom = PointGeometry(((1.0, 2.0, 3.0),), unit="nm", refs=(ref,))

    assert geom.coordinates == ((1.0, 2.0, 3.0),)
    assert geom.refs == (entity_ref_payload(ref),)

    with pytest.raises(ValueError, match="unit is required"):
        PointGeometry(((1.0, 2.0, 3.0),), unit="", refs=(ref,))

    with pytest.raises(ValueError, match="one entity reference per point"):
        PointGeometry(((1.0, 2.0, 3.0),), unit="nm", refs=(ref, ref))

    with pytest.raises(ValueError, match="non-negative"):
        SphereGeometry(((0.0, 0.0, 0.0),), (-1.0,), unit="nm")


def test_indexed_geometry_requires_explicit_index_space_and_arity():
    ref = EntityRef("demo.face", "f1")

    with pytest.raises(ValueError, match="atom_index_space is required"):
        IndexedTriangleGeometry(
            coordinates=(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),),
            atom_triplets=((0, 1, 2),),
            atom_index_space="",
            unit="nm",
            refs=(ref,),
        )

    with pytest.raises(ValueError, match="3 entries"):
        IndexedTriangleGeometry(
            coordinates=(),
            atom_triplets=((0, 1),),
            atom_index_space=MESH_LOCAL,
            unit="nm",
            refs=(ref,),
        )


def test_triangle_adapter_preserves_refs_and_converts_units_at_boundary():
    view = MolSysView()
    ref = EntityRef("demo.face", "f1", atom_indices=(0, 1, 2), atom_index_space=MESH_LOCAL)
    geometry = IndexedTriangleGeometry(
        coordinates=(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),),
        atom_triplets=((0, 1, 2),),
        atom_index_space=MESH_LOCAL,
        unit="nm",
        refs=(ref,),
    )

    layer = shape_adapters.add_indexed_triangles(view, geometry, tag="tri", skip_digestion=False)

    options = view._shape_history[-1]["options"]  # noqa: SLF001
    assert layer.tag == "tri"
    assert options["vertices"] == [[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 10.0, 0.0]]]
    assert options["atom_triplets"] == [[0, 1, 2]]
    assert options["entity_refs"] == [entity_ref_payload(ref)]


def test_tetrahedra_adapter_preserves_coordinates_indices_and_refs():
    view = MolSysView()
    ref = EntityRef("demo.tetra", "t1")
    geometry = TetrahedraGeometry(
        coordinates=(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),),
        atom_quads=((0, 1, 2, 3),),
        atom_index_space=MESH_LOCAL,
        unit="nm",
        refs=(ref,),
    )

    shape_adapters.add_tetrahedra(view, geometry, tag="tetra")

    options = view._shape_history[-1]["options"]  # noqa: SLF001
    assert options["tetra_coords"] == [[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]]]
    assert options["atom_quads"] == [[0, 1, 2, 3]]
    assert options["entity_refs"] == [entity_ref_payload(ref)]


def test_sphere_and_segment_adapters_use_explicit_collection_semantics():
    view = MolSysView()
    spheres = SphereGeometry(
        centers=((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
        radii=(0.2, 0.2),
        unit="nm",
    )
    shape_adapters.add_uniform_spheres(view, spheres, tag="s")
    sphere_options = [msg["options"] for msg in view._shape_history[-2:]]  # noqa: SLF001
    assert [options["center"] for options in sphere_options] == [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]]
    assert [options["radius"] for options in sphere_options] == [2.0, 2.0]

    with pytest.raises(ValueError, match="one common radius"):
        shape_adapters.add_uniform_spheres(
            view,
            SphereGeometry(((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)), (0.2, 0.3), unit="nm"),
        )

    segments = SegmentGeometry(
        starts=((0.0, 0.0, 0.0),),
        ends=((1.0, 0.0, 0.0),),
        unit="nm",
    )
    shape_adapters.add_segments(view, segments, radius="0.1 nm", tag="seg")
    link_options = view._shape_history[-1]["options"]  # noqa: SLF001
    assert link_options["coordinate_pairs"] == [[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]]
