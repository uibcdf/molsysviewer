import numpy as np
import pytest

from molsysviewer import demo
from molsysviewer._pyunitwizard import puw
from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys


@pytest.fixture
def dialanine_view():
    view = demo["dialanine"]
    try:
        yield view
    finally:
        view.close()


def test_array_native_payload_preserves_complete_structural_axes(dialanine_view):
    molsys = dialanine_view.molsys
    result = serialize_array_native_molsys(molsys)

    coordinates = result.arrays[0]
    expected = puw.get_value(molsys.structures.coordinates, to_unit="angstroms")
    # Planar per structure: all x, then all y, then all z, so the frontend can
    # take zero-copy per-axis views instead of de-interleaving every frame.
    planar_shape = (expected.shape[0], 3, expected.shape[1])
    assert coordinates.shape == planar_shape
    assert coordinates.dtype == np.dtype("<f4")
    assert coordinates.flags.c_contiguous
    # Same science, transposed axes: coordinates[s, axis, atom] == expected[s, atom, axis]
    np.testing.assert_allclose(
        coordinates, np.asarray(expected).transpose(0, 2, 1), rtol=1e-6, atol=1e-5
    )

    descriptor = result.metadata["structural_arrays"][0]
    assert descriptor == {
        "kind": "coordinates",
        "dtype": "float32",
        "shape": list(planar_shape),
        "layout": "structure-planar-c",
        "units": "angstrom",
        "endianness": "little",
        "buffer_index": 0,
        "byte_length": coordinates.nbytes,
    }
    assert result.metadata["n_atoms"] == molsys.get_n_atoms()
    assert result.metadata["n_structures"] == molsys.structures.n_structures
    assert "structures" not in result.metadata


def test_array_native_payload_does_not_invent_missing_box_or_time(dialanine_view):
    molsys = dialanine_view.molsys
    assert molsys.structures.box is None
    assert molsys.structures.time is None

    result = serialize_array_native_molsys(molsys)

    assert [item["kind"] for item in result.metadata["structural_arrays"]] == [
        "coordinates"
    ]
    assert len(result.arrays) == 1


def test_array_native_payload_serializes_static_topology_without_viewer_json(dialanine_view):
    result = serialize_array_native_molsys(dialanine_view.molsys)
    atoms = result.metadata["atoms"]

    assert atoms["atom_name"][:3] == ["H1", "CH3", "H2"]
    assert atoms["residue_name"][:3] == ["ACE", "ACE", "ACE"]
    assert atoms["element_symbol"][:3] == ["H", "C", "H"]
    assert len(atoms["atom_id"]) == result.metadata["n_atoms"]
    assert len(atoms["molecule_id"]) == result.metadata["n_atoms"]
    assert result.metadata["bonds"]["indexA"][:2] == [0, 1]
    assert result.metadata["bonds"]["indexB"][:2] == [1, 2]


def test_array_native_payload_preserves_aligned_box_and_time(dialanine_view):
    molsys = dialanine_view.molsys.copy()
    n_structures = molsys.structures.n_structures
    box_nm = np.broadcast_to(np.eye(3, dtype=np.float64) * 3.0, (n_structures, 3, 3)).copy()
    time_ps = np.arange(n_structures, dtype=np.float64) * 0.5
    molsys.structures.box = puw.quantity(box_nm, "nm")
    molsys.structures.time = puw.quantity(time_ps, "ps")
    result = serialize_array_native_molsys(molsys)
    by_kind = {
        descriptor["kind"]: result.arrays[descriptor["buffer_index"]]
        for descriptor in result.metadata["structural_arrays"]
    }

    assert by_kind["box"].shape == (result.metadata["n_structures"], 3, 3)
    assert by_kind["box"].dtype == np.dtype("<f4")
    np.testing.assert_allclose(
        by_kind["box"],
        puw.get_value(molsys.structures.box, to_unit="angstroms"),
        rtol=1e-6,
        atol=1e-5,
    )
    assert by_kind["time"].shape == (result.metadata["n_structures"],)
    assert by_kind["time"].dtype == np.dtype("<f8")
    np.testing.assert_allclose(
        by_kind["time"],
        puw.get_value(molsys.structures.time, to_unit="ps"),
    )
    assert len(result.buffers) == len(result.arrays)
    assert [buffer.nbytes for buffer in result.buffers] == [
        array.nbytes for array in result.arrays
    ]


def test_array_native_payload_rejects_nonfinite_coordinates(dialanine_view):
    molsys = dialanine_view.molsys.copy()
    coordinates = puw.get_value(molsys.structures.coordinates, to_unit="nm").copy()
    coordinates[0, 0, 0] = np.nan
    molsys.structures.coordinates = puw.quantity(coordinates, "nm")

    with pytest.raises(ValueError, match="coordinates must contain only finite"):
        serialize_array_native_molsys(molsys)
