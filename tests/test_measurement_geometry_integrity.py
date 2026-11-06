"""Live measures agree with independent coordinates and native torsion orientation."""

from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    with puw.context(standard_units=["pm", "ps", "radian"]):
        with msv.demo["pentalanine"] as seed:
            result = msv.new_view(seed.molsys, structure_indices=[0, 8, 3])
        with result:
            yield result


def points(view, endpoints):
    coordinates = puw.get_value(view.get_coordinates(), to_unit="angstrom")
    return np.stack([coordinates[:, atoms].mean(axis=1) for atoms in endpoints], axis=1)


def torsions(positions):
    axis = positions[:, 2] - positions[:, 1]
    axis /= np.linalg.norm(axis, axis=1)[:, None]
    a, b = positions[:, 0] - positions[:, 1], positions[:, 3] - positions[:, 2]
    a -= np.einsum("ij,ij->i", a, axis)[:, None] * axis
    b -= np.einsum("ij,ij->i", b, axis)[:, None] * axis
    return np.degrees(np.arctan2(np.einsum("ij,ij->i", np.cross(axis, a), b), np.einsum("ij,ij->i", a, b)))


@pytest.mark.parametrize("endpoints", [[[0], [5], [9], [18]], [[0, 2, 4], [5, 6, 7], [9, 11, 12], [18, 21, 25]]])
@pytest.mark.parametrize("reverse_axis", [False, True])
def test_signed_dihedral_matches_projected_bonds_and_native_atoms(view, endpoints, reverse_axis):
    if reverse_axis:
        endpoints = [endpoints[0], endpoints[2], endpoints[1], endpoints[3]]
    view.measurements.add_dihedral(*endpoints, tag="torsion", endpoint_policy="centroid")
    expected = torsions(points(view, endpoints))
    np.testing.assert_allclose(puw.get_value(view.measurements.series("torsion"), to_unit="degrees"), expected)
    if all(len(atoms) == 1 for atoms in endpoints):
        native = msm.structure.get_dihedral_angles(
            view.molsys, dihedral_quartets=[[a[0] for a in endpoints]], pbc=False
        )
        np.testing.assert_allclose(puw.get_value(native, to_unit="degrees")[:, 0], expected)
    assert np.all(expected < 0) if reverse_axis else np.all(expected > 0)


@pytest.mark.parametrize("route", ["state", "session"])
def test_recovery_recomputes_legacy_opposite_sign_values(view, tmp_path, route):
    endpoints = [[0], [5], [9], [18]]
    view.measurements.add_dihedral(*endpoints, tag="torsion")
    expected = torsions(points(view, endpoints))
    # Emulate the cached values of an actual old state, without altering atoms.
    view._measurement_history[0]["options"]["value_series"] = (-expected).tolist()
    view._measurement_history[0]["options"]["value"] = float(-expected[0])
    if route == "session":
        path = tmp_path / "old-torsion.msv"
        view.save_session(path)
        restored = msv.load_session(path)
    else:
        restored = msv.new_view(view.molsys)
        restored.import_state(deepcopy(view.export_state()))
    with restored:
        np.testing.assert_allclose(puw.get_value(restored.measurements.series("torsion"), to_unit="degrees"), expected)


@pytest.mark.parametrize("method", ["set_coordinates", "partial_coordinates_update"])
@pytest.mark.parametrize("hidden", [False, True])
def test_coordinate_edits_refresh_live_measurement_values(view, method, hidden):
    endpoints = [[0, 2, 4], [5]]
    view.measurements.add_distance(*endpoints, tag="distance", endpoint_policy="centroid")
    if hidden:
        view.measurements.hide("distance")
    original = puw.get_value(view.measurements.series("distance"), to_unit="angstrom").copy()
    coordinates = puw.get_value(view.get_coordinates(selection=[0, 2, 4], structure_indices=[2, 0]), to_unit="angstrom")
    getattr(view, method)(
        puw.quantity(coordinates + [1.3, -0.6, 0.9], "angstrom"), selection=[0, 2, 4], structure_indices=[2, 0]
    )
    expected = np.linalg.norm(np.diff(points(view, endpoints), axis=1)[:, 0], axis=1)
    actual = puw.get_value(view.measurements.series("distance"), to_unit="angstrom")
    np.testing.assert_allclose(actual, expected)
    assert actual[1] == original[1]
    assert actual[0] != original[0] and actual[2] != original[2]
    assert view.measurements.info("distance")["visible"] is not hidden
    for index in [2, 0, 1]:
        view.player.go_to_structure(index)
        assert puw.get_value(view.measurements.info("distance")["value"], to_unit="angstrom") == pytest.approx(
            expected[index]
        )


@pytest.mark.parametrize("endpoints", [[[0, 2, 4], [5]], [[0, 0, 2, 4], [5, 6, 7]]])
def test_endpoint_positions_are_current_effective_centroids(view, endpoints):
    measurement = view.measurements.add_distance(*endpoints, tag="distance", endpoint_policy="centroid")
    expected = points(view, endpoints)
    for frame in [0, 2, 1]:
        view.player.go_to_structure(frame)
        actual = puw.get_value(measurement.get_coordinates(), to_unit="angstrom")
        assert actual.shape == (2, 3)
        np.testing.assert_allclose(actual, expected[frame])


def test_focus_includes_mixed_centroid_population_in_visible_structure(view):
    measurement = view.measurements.add_distance([0, 2, 4], [5], tag="distance")
    view.player.go_to_structure(2)
    sent = []
    view._ready = True
    view.widget.send = sent.append
    measurement.focus()
    zoom = next(message for message in sent if message.get("op") == "zoom_to_position")
    coordinates = puw.get_value(
        view.get_coordinates(selection=[0, 2, 4, 5], structure_indices=[2]), to_unit="angstrom"
    )[0]
    # The documented focus bounds include participant atoms, not only centers.
    assert np.linalg.norm(coordinates - zoom["center"], axis=1).max() <= zoom["radius"]
    assert not np.allclose(zoom["center"], coordinates[-1])


def test_rejected_edit_keeps_measurement_cache_and_degenerate_edit_discards_value(view):
    view.measurements.add_angle([0], [5], [9], tag="angle")
    original = puw.get_value(view.get_coordinates(), to_unit="angstrom").copy()
    cached = deepcopy(view.measurements.records())
    with pytest.raises(Exception):
        view.partial_coordinates_update(puw.quantity(original[0, 0], "angstrom"), selection=[0], structure_indices=[3])
    assert view.measurements.records() == cached
    np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="angstrom"), original)
    # Coincident endpoints make the angle undefined. No prior plausible number
    # can remain cached; repairing the same frame makes the series usable again.
    view.partial_coordinates_update(puw.quantity(np.zeros((2, 3)), "angstrom"), selection=[0, 5], structure_indices=[2])
    assert view.measurements.series("angle") is None
    assert view.measurements.info("angle")["value"] is None
    view.partial_coordinates_update(
        puw.quantity(original[2, [0, 5]], "angstrom"), selection=[0, 5], structure_indices=[2]
    )
    np.testing.assert_allclose(
        puw.get_value(view.measurements.series("angle"), to_unit="degrees"), cached[0]["options"]["value_series"]
    )


def test_representative_coordinates_follow_effective_atoms_and_retired_handles_fail(view):
    endpoints = [[0, 2, 4], [5, 6, 7]]
    measurement = view.measurements.add_distance(
        *endpoints, tag="representative", endpoint_policy="representative_atom"
    )
    expected = points(view, [[0], [5]])
    for frame in [2, 0]:
        view.player.go_to_structure(frame)
        np.testing.assert_allclose(puw.get_value(measurement.get_coordinates(), to_unit="angstrom"), expected[frame])
    view.measurements.delete("representative")
    with pytest.raises(Exception):
        measurement.get_coordinates()
    with pytest.raises(Exception):
        measurement.focus()


def test_incomplete_extraction_retains_broken_measure_without_inventing_positions(view):
    view.measurements.add_distance([0, 2, 4], [5], tag="distance")
    with view.extract(selection=[5]) as extracted:
        measurement = extracted.measurements["distance"]
        assert measurement.broken
        with pytest.raises(ValueError, match="no resolvable endpoint atoms"):
            measurement.get_coordinates()
        with pytest.raises(ValueError, match="no resolvable endpoint atoms"):
            measurement.focus()


def test_player_navigation_projects_current_measurement_values(view):
    view.measurements.add_distance([0, 2, 4], [5], tag="distance")
    expected = puw.get_value(view.measurements.series("distance"), to_unit="pm")
    sent = []
    view._ready = True
    view.widget.send = sent.append
    for operation, index in [
        (lambda: view.player.go_to_structure(2), 2),
        (view.player.step_forward, 0),
        (view.player.step_backward, 2),
    ]:
        sent.clear()
        operation()
        summaries = [message for message in sent if message.get("op") == "set_measurement_summaries"]
        assert len(summaries) == 1
        assert summaries[0]["structure_index"] == index
        assert summaries[0]["measurements"][0]["unit"] == "picometer"
        assert summaries[0]["measurements"][0]["value"] == pytest.approx(expected[index])
