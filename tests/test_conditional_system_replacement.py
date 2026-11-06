"""Reviewed replacement uses actual demo systems and the shared edit boundary."""

from threading import Event, Thread

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.system_edits import SystemEditPendingError, _SceneCheckpoint

import molsysviewer as msv


@pytest.fixture
def case():
    with msv.demo["pentalanine"] as source, msv.demo["dialanine"] as result:
        with msv.new_view(source.molsys, structure_indices=[0, 8, 3]) as view:
            view.regions.add(selection=[0, 2], tag="reviewed-scene")
            yield view, msm.copy(result.molsys)


def snapshot(view):
    return {
        "target": view.molsys,
        "coordinates": msm.pyunitwizard.get_value(view.molsys.structures.coordinates, to_unit="nm").copy(),
        "status": view.addons.manager.system_edits.get_status(),
        "scene": _SceneCheckpoint(view),
        "history": (list(view.history._undo), list(view.history._redo)),
    }


def unchanged(view, before):
    assert view.molsys is before["target"]
    assert view.addons.manager.system_edits.get_status() == before["status"]
    np.testing.assert_array_equal(
        msm.pyunitwizard.get_value(view.molsys.structures.coordinates, to_unit="nm"), before["coordinates"]
    )
    current, previous = _SceneCheckpoint(view), before["scene"]
    np.testing.assert_equal(current.values, previous.values)
    assert current.registries == previous.registries
    current_handles = {id(obj): fields for obj, fields in current.handles}
    previous_handles = {id(obj): fields for obj, fields in previous.handles}
    np.testing.assert_equal(current_handles, previous_handles)
    assert (view.history._undo, view.history._redo) == before["history"]


@pytest.mark.parametrize("skip", [False, True])
def test_exact_review_replaces_and_resets_scene_once(case, skip):
    view, candidate = case
    manager = view.addons.manager.system_edits
    target, revision = view.molsys, manager.get_status()["target_revision"]
    assert manager.replace(candidate, expected_target=target, expected_revision=revision, skip_digestion=skip) is None
    assert view.molsys is not target
    assert view.molsys.get_n_atoms() == candidate.get_n_atoms()
    assert "reviewed-scene" not in view.regions
    assert manager.get_status()["target_revision"] == revision + 1
    assert manager.get_status()["state"] == "synchronized"
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        manager.replace(candidate, expected_target=target, expected_revision=revision, skip_digestion=skip)
    unchanged(view, before)


def test_expected_empty_primary_and_numpy_integer_revision_are_explicit():
    with msv.MolSysView() as view, msv.demo["dialanine"] as candidate:
        manager = view.addons.manager.system_edits
        manager.replace(candidate.molsys, expected_target=None, expected_revision=np.int64(0))
        assert view.molsys.get_n_atoms() == 22
        assert manager.get_status()["target_revision"] == 1


@pytest.mark.parametrize("state", ["pending", "sync_failed"])
@pytest.mark.parametrize("skip", [False, True])
def test_intervening_managed_edit_invalidates_the_review_without_other_effects(case, state, skip):
    view, candidate = case
    manager = view.addons.manager.system_edits
    target, revision = view.molsys, manager.get_status()["target_revision"]
    coordinates = msm.get(view.molsys, coordinates=True).copy() + msm.pyunitwizard.quantity(0.1, "nm")
    manager.execute(
        lambda target: {"run": lambda: msm.set(target, coordinates=coordinates), "changed": True},
        name="conditional-replacement.intervening-edit",
        update_view=False,
    )
    manager._state = state
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        manager.replace(candidate, expected_target=target, expected_revision=revision, skip_digestion=skip)
    unchanged(view, before)


def test_direct_target_reload_is_detected_even_with_the_current_revision(case):
    view, candidate = case
    manager = view.addons.manager.system_edits
    old_target = view.molsys
    view.load(msm.copy(candidate), mode="replace")
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        manager.replace(candidate, expected_target=old_target, expected_revision=before["status"]["target_revision"])
    unchanged(view, before)


@pytest.mark.parametrize("state", ["pending", "sync_failed"])
def test_matching_completed_pending_data_can_be_explicitly_replaced(case, state):
    view, candidate = case
    manager = view.addons.manager.system_edits
    coordinates = msm.get(view.molsys, coordinates=True).copy() + msm.pyunitwizard.quantity(0.1, "nm")
    manager.execute(
        lambda target: {"run": lambda: msm.set(target, coordinates=coordinates), "changed": True},
        name="conditional-replacement.current-data",
        update_view=False,
    )
    manager._state = state
    revision = manager.get_status()["target_revision"]
    manager.replace(candidate, expected_target=view.molsys, expected_revision=revision)
    status = manager.get_status()
    assert status["state"] == "synchronized" and status["pending_operations"] == 0
    assert status["target_revision"] == status["integration_revision"] == revision + 1
    assert view.molsys.get_n_atoms() == candidate.get_n_atoms()


def test_expected_empty_target_does_not_mean_any_loaded_target(case):
    view, candidate = case
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        view.addons.manager.system_edits.replace(candidate, expected_target=None, expected_revision=0)
    unchanged(view, before)


@pytest.mark.parametrize("skip", [False, True])
def test_nonempty_expected_target_requires_its_reviewed_revision(case, skip):
    view, candidate = case
    before = snapshot(view)
    with pytest.raises(ValueError, match="requires its reviewed revision"):
        view.addons.manager.system_edits.replace(candidate, expected_target=view.molsys, skip_digestion=skip)
    unchanged(view, before)


@pytest.mark.parametrize("revision", [True, False, -1, 0.5, "0", [], np.int64(-1)])
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_revision_metadata_is_never_a_matching_counter(case, revision, skip):
    view, candidate = case
    before = snapshot(view)
    with pytest.raises((ArgumentError, ValueError)):
        view.addons.manager.system_edits.replace(
            candidate, expected_target=view.molsys, expected_revision=revision, skip_digestion=skip
        )
    unchanged(view, before)


def test_expected_target_is_an_identity_reference_not_a_path_or_source_label(case):
    view, candidate = case
    before = snapshot(view)
    with pytest.raises(ArgumentError):
        view.addons.manager.system_edits.replace(candidate, expected_target="1TCD", expected_revision=0)
    unchanged(view, before)


def test_stale_review_is_rejected_before_candidate_load_even_without_digestion(case):
    view, _ = case
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        view.addons.manager.system_edits.replace(
            object(), expected_target=view.molsys, expected_revision=999, skip_digestion=True
        )
    unchanged(view, before)


@pytest.mark.parametrize("skip", [False, True])
def test_uncertain_source_cannot_match_a_review_but_unconditional_recovery_remains(case, skip):
    view, candidate = case
    manager = view.addons.manager.system_edits
    manager._state = "uncertain"
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="uncertain edit"):
        manager.replace(candidate, expected_target=view.molsys, expected_revision=0, skip_digestion=skip)
    unchanged(view, before)
    manager.replace(candidate, skip_digestion=skip)
    assert manager.get_status()["state"] == "synchronized"
    assert manager.get_status()["target_revision"] == 1


def test_competing_edit_owns_the_boundary_and_makes_the_old_review_stale(case):
    view, candidate = case
    manager = view.addons.manager.system_edits
    target, revision = view.molsys, manager.get_status()["target_revision"]
    coordinates = msm.get(target, coordinates=True).copy()
    entered, release = Event(), Event()
    errors = []

    def worker():
        try:

            def prepare(current):
                entered.set()
                if not release.wait(10):
                    raise TimeoutError("The receiving worker was not released.")
                return {
                    "run": lambda: msm.set(current, coordinates=coordinates + msm.pyunitwizard.quantity(0.1, "nm")),
                    "changed": True,
                }

            manager.execute(prepare, name="conditional-replacement.concurrent-edit", update_view=False)
        except BaseException as exc:
            errors.append(exc)

    thread = Thread(target=worker)
    thread.start()
    assert entered.wait(10)
    try:
        with pytest.raises(SystemEditPendingError, match="Another operation"):
            manager.replace(candidate, expected_target=target, expected_revision=revision, skip_digestion=True)
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive() and not errors
    before = snapshot(view)
    with pytest.raises(SystemEditPendingError, match="changed after review"):
        manager.replace(candidate, expected_target=target, expected_revision=revision)
    unchanged(view, before)


def test_closed_view_refuses_conditional_replacement(case):
    view, candidate = case
    manager = view.addons.manager.system_edits
    target = view.molsys
    view.close()
    with pytest.raises(RuntimeError, match="closed view"):
        manager.replace(candidate, expected_target=target, expected_revision=0)
