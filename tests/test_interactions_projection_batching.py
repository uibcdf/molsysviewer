"""Real public geometry calls, bounded batches and independent centroid oracles."""

import inspect
import sys
from contextlib import contextmanager
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from devtools.benchmarks.interactions_residency import build_analysis, build_molsys
from devtools.interaction_family_fixtures import make_family_view

import molsysviewer as msv


@contextmanager
def geometry_calls():
    """Observe actual provider calls without substituting their implementations."""
    targets = {
        inspect.unwrap(msm.structure.get_center).__code__: "centers",
        inspect.unwrap(msm.structure.get_distances).__code__: "distances",
    }
    calls = []
    previous = sys.getprofile()

    def observe(frame, event, arg):
        if previous is not None:
            previous(frame, event, arg)
        if event == "call" and frame.f_code in targets:
            calls.append(
                {
                    "operation": targets[frame.f_code],
                    **{
                        key: deepcopy(frame.f_locals[key])
                        for key in ("selection", "structure_indices", "heavy_mode", "pairs", "pbc")
                        if key in frame.f_locals
                    },
                }
            )

    sys.setprofile(observe)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


def assert_centroid_links(view, result, payload):
    """Direct atom means plus declared images; never call the batch helper."""
    frame = payload["frame"]
    data = result.query(structure_indices=[frame]).to_dict()
    xyz = msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True, structure_indices=[frame]), to_unit="nm")[0]
    raw_box = msm.get(view.molsys, box=True, structure_indices=[frame])
    box = None if raw_box is None else msm.pyunitwizard.get_value(raw_box, to_unit="nm")[0]
    assert payload["status"] == "evaluated"
    assert payload["n_supported"] == payload["n_observations"] == len(data["occurrence_indices"])
    assert payload["n_segments"] == len(payload["links"]) == payload["n_observations"]
    for row, link in enumerate(payload["links"]):
        assert link["occurrence_index"] == int(data["occurrence_indices"][row])
        parts = result.relation(int(data["relation_indices"][row]))["participants"]
        positions = np.array([xyz[p["atom_indices"]].mean(axis=0) for p in parts])
        if data["image_vectors"] is not None:
            lo, hi = data["image_offsets"][row : row + 2]
            images = data["image_vectors"][lo:hi]
            positions += (images - images[0]) @ box
        np.testing.assert_allclose(link["start"], positions[0], atol=1e-8)
        np.testing.assert_allclose(link["end"], positions[1], atol=1e-8)
        assert link["participants"] == [{"role": p["role"], "atom_indices": p["atom_indices"].tolist()} for p in parts]


def assert_grouped_calls(calls, expected_frames):
    centers = [call for call in calls if call["operation"] == "centers"]
    assert centers
    for call in calls:
        assert list(call["structure_indices"]) in [[frame] for frame in expected_frames]
        assert call["heavy_mode"] == "off"
        selection = call["selection"]
        if call["operation"] == "centers":
            assert all(np.asarray(group).ndim == 1 and len(group) > 1 for group in selection)
            assert sum(len(group) for group in selection) <= 16384
        else:
            assert call["pairs"] is True and call["pbc"] is True
            assert np.asarray(selection).ndim == 2 and np.asarray(selection).shape[1] == 2
            assert len(selection) <= 16384
    return centers


@pytest.mark.parametrize("kind", ["ionic_contact", "pi_pi", "cation_pi"])
@pytest.mark.parametrize("periodic", [False, True])
@pytest.mark.parametrize("length_unit", ["nm", "angstrom"])
def test_real_compound_families_batch_geometry_and_keep_nm_images_and_frame_identity(kind, periodic, length_unit):
    with msm.pyunitwizard.context(standard_units=[length_unit, "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        case = make_family_view(kind, periodic=periodic)
        view = case.view
        try:
            result = case.calculate(structure_indices="all", pbc=periodic)
            with geometry_calls() as calls:
                view.interactions.add("contacts", tag="groups")
                if not periodic:
                    view.interactions._messages(2)
                    view.interactions._messages(1)  # evaluated-empty: no geometry calls
            centers = assert_grouped_calls(calls, [0] if periodic else [0, 2])
            assert len(centers) == (1 if periodic else 2)
            if kind == "pi_pi":
                assert all(len(call["selection"]) == 2 for call in centers)
            if periodic:
                assert len([call for call in calls if call["operation"] == "distances"]) == 1
            else:
                assert not any(call["operation"] == "distances" for call in calls)
            for frame in [0] if periodic else [2, 0]:
                assert_centroid_links(view, result, view.interactions._messages(frame)[0])
        finally:
            view.close()


def test_many_distinct_groups_use_bounded_calls_and_preserve_every_occurrence():
    view = msv.new_view(build_molsys(30, 4))
    try:
        result = build_analysis(1860, 4, 300, "churn", "rings")
        view.interactions.attach(result, name="groups", assume_aligned=True)
        with geometry_calls() as calls:
            view.interactions.add("groups", tag="groups")
        centers = assert_grouped_calls(calls, [0])
        assert len(centers) == 3  # 300 rows; at most 128 decoded per batch
        assert sum(len(call["selection"]) for call in centers) == 600
        assert_centroid_links(view, result, view.interactions._messages(0)[0])
    finally:
        view.close()


def test_large_participant_memberships_bound_total_atoms_in_each_geometry_call():
    view = msv.new_view(build_molsys(40, 1))
    try:
        records = [
            {
                "structure_index": 0,
                "interaction_type": "ionic_contact",
                "participants": [
                    {"role": "positive", "atom_indices": list(range(offset, offset + 2050))},
                    {"role": "negative", "atom_indices": [2400]},
                ],
            }
            for offset in range(16)
        ]
        result = msm.Interactions.from_records(
            records, n_atoms=2480, n_structures=1, evaluated_structure_indices=[0], method="synthetic_large_group_probe"
        )
        view.interactions.attach(result, name="groups", assume_aligned=True)
        with geometry_calls() as calls:
            view.interactions.add("groups", tag="groups")
        centers = assert_grouped_calls(calls, [0])
        assert [len(call["selection"]) for call in centers] == [7, 7, 2]
        assert_centroid_links(view, result, view.interactions._messages(0)[0])
    finally:
        view.close()


def test_split_periodic_group_is_refused_before_its_center_is_calculated():
    case = make_family_view("pi_pi", periodic=True)
    view = case.view
    try:
        result = case.calculate(pbc=True)
        broken_atom = int(result.relation(0)["participants"][0]["atom_indices"][1])
        box = msm.get(view.molsys, box=True, structure_indices=[0])
        # Deliberately construct an incomplete stored-image fixture: translating
        # one ring atom requires internal unwrapping that the result cannot encode.
        msm.structure.translate(view.molsys, selection=[broken_atom], translation=box[0, 0], in_place=True)
        # Public geometry edits invalidate stored analyses. Deliberately import
        # the original observation against the edited geometry so this guard
        # exercises malformed-image projection rather than setter invalidation.
        view.interactions.attach(result, name="malformed", assume_aligned=True)
        with geometry_calls() as calls:
            view.interactions.add("malformed", tag="groups")
        assert_grouped_calls(calls, [0])
        payload = view.interactions._messages(0)[0]
        assert payload["status"] == "unsupported" and payload["n_skipped"] == result.n_interactions
        assert payload["n_supported"] == payload["n_segments"] == 0
        assert all(
            broken_atom not in group for call in calls if call["operation"] == "centers" for group in call["selection"]
        )
    finally:
        view.close()


@pytest.mark.parametrize("structure_indices", [[0], [2], [2, 0]])
def test_provider_coordinate_edit_invalidates_only_changed_frames_and_refreshes_cached_projection(structure_indices):
    case = make_family_view("pi_pi")
    view = case.view
    try:
        original = case.calculate(structure_indices="all")
        assert original.n_interactions == 2
        np.testing.assert_array_equal(original.evaluated_structure_indices, [0, 1, 2])
        view.interactions.add("contacts", tag="groups")
        before = [deepcopy(view.interactions._messages(frame)[0]) for frame in range(3)]
        assert before[0]["links"] and before[2]["links"]
        assert before[1]["status"] == "evaluated" and before[1]["links"] == []
        view.interactions._messages(0)  # Leave the visible frame cached before the provider edit.
        xyz = msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm").copy()
        atom = int(original.relation(0)["participants"][0]["atom_indices"][1])
        delta = msm.pyunitwizard.quantity([0.01, 0, 0], "nm")
        msm.structure.translate(
            view.molsys, selection=[atom], structure_indices=structure_indices, translation=delta, in_place=True
        )
        expected = xyz.copy()
        expected[structure_indices, atom] += [0.01, 0, 0]
        np.testing.assert_allclose(
            msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm"), expected
        )
        current = view.interactions.get_analysis("contacts")
        assert current is not original
        np.testing.assert_array_equal(current.evaluated_structure_indices, sorted({0, 1, 2} - set(structure_indices)))
        # The detached scientific result stays valid for its original geometry.
        assert original.n_interactions == 2
        np.testing.assert_array_equal(original.evaluated_structure_indices, [0, 1, 2])
        for frame in range(3):
            payload = view.interactions._messages(frame)[0]
            assert payload["analysis_revision"] != before[frame]["analysis_revision"]
            if frame in structure_indices:
                assert payload["status"] == "unevaluated"
                assert payload["n_observations"] == payload["n_supported"] == payload["n_segments"] == 0
                assert payload["links"] == []
            else:
                assert payload["status"] == "evaluated"
                # Editing creates a new analysis, so its occurrence identifiers
                # may be reassigned. Preserve geometry/chemistry and use the
                # identifiers declared by the new result.
                current_ids = current.query(structure_indices=[frame]).to_dict()["occurrence_indices"].tolist()
                assert [link["occurrence_index"] for link in payload["links"]] == current_ids
                assert [
                    {key: value for key, value in link.items() if key != "occurrence_index"}
                    for link in payload["links"]
                ] == [
                    {key: value for key, value in link.items() if key != "occurrence_index"}
                    for link in before[frame]["links"]
                ]
                assert payload["n_observations"] == before[frame]["n_observations"]
    finally:
        view.close()


def test_nonfinite_groups_are_excluded_from_real_provider_calls():
    case = make_family_view("pi_pi")
    view = case.view
    try:
        coordinates = msm.pyunitwizard.get_value(
            msm.get(view.molsys, coordinates=True, structure_indices=[0]), to_unit="nm"
        )[0].copy()
        coordinates[1] = np.nan
        groups = [tuple(range(6)), tuple(range(6, 12))]
        with geometry_calls() as calls:
            centers = view.interactions._participant_centers(groups, 0, coordinates, periodic=False)
        assert centers[groups[0]] is None
        np.testing.assert_allclose(centers[groups[1]], coordinates[6:12].mean(axis=0))
        assert len(calls) == 1 and [list(group) for group in calls[0]["selection"]] == [list(range(6, 12))]
    finally:
        view.close()
