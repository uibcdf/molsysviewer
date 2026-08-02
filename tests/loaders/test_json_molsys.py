import numpy as np
import pytest

from molsysviewer import demo
from molsysviewer._pyunitwizard import puw
from molsysviewer.loaders.json_molsys import serialize_json_molsys


def test_json_payload_uses_the_same_canonical_topology_as_array_native():
    from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys

    view = demo["dialanine"]
    json_payload = serialize_json_molsys(view.molsys)
    array_payload = serialize_array_native_molsys(view.molsys)

    assert json_payload["atoms"] == array_payload.metadata["atoms"]
    assert json_payload["bonds"] == array_payload.metadata["bonds"]


def test_json_payload_preserves_coordinates_without_inventing_box_or_time():
    view = demo["dialanine"]
    payload = serialize_json_molsys(view.molsys)
    expected = puw.get_value(view.molsys.structures.coordinates, to_unit="angstroms")

    assert len(payload["structures"]) == view.molsys.structures.n_structures
    np.testing.assert_allclose(payload["structures"][0]["coordinates"], expected[0])
    assert "box" not in payload["structures"][0]
    assert "time" not in payload["structures"][0]


def test_json_payload_preserves_aligned_box_and_time_with_explicit_units():
    view = demo["dialanine"]
    molsys = view.molsys.copy()
    n_structures = molsys.structures.n_structures
    box_nm = np.broadcast_to(np.eye(3) * 3.0, (n_structures, 3, 3)).copy()
    time_ps = np.arange(n_structures, dtype=np.float64) * 0.5
    molsys.structures.box = puw.quantity(box_nm, "nm")
    molsys.structures.time = puw.quantity(time_ps, "ps")

    payload = serialize_json_molsys(molsys)

    np.testing.assert_allclose(payload["structures"][0]["box"], np.eye(3) * 30.0)
    assert [record["time"] for record in payload["structures"]] == time_ps.tolist()


def test_json_payload_rejects_nonfinite_coordinates():
    view = demo["dialanine"]
    molsys = view.molsys.copy()
    coordinates = puw.get_value(molsys.structures.coordinates, to_unit="nm").copy()
    coordinates[0, 0, 0] = np.nan
    molsys.structures.coordinates = puw.quantity(coordinates, "nm")

    with pytest.raises(ValueError, match="coordinates must contain only finite"):
        serialize_json_molsys(molsys)
