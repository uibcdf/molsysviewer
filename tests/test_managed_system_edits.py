"""Host coordination is independent of a particular optional addon delivery."""

from threading import Event, Thread

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.system_edits import SystemEditPendingError
from molsysviewer.widget import MolSysViewerWidget

import molsysviewer as msv


class _ReceivingWidget(MolSysViewerWidget):
    def send(self, content, buffers=None):
        vars(self).setdefault("received", []).append(content)


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with msv.MolSysView(transport=_ReceivingWidget()) as result:
            result.load(source.molsys, structure_indices=[0, 8, 3])
            yield result


def test_uncertain_scientific_write_is_not_recognized_from_unchanged_counts(view):
    manager = view.addons.manager.system_edits

    def prepare(target):
        def run():
            coordinates = msm.get(target, element="atom", selection=[0], structure_indices=[0], coordinates=True).copy()
            coordinates += msm.pyunitwizard.quantity(0.1, "nm")
            msm.set(target, selection=[0], structure_indices=[0], coordinates=coordinates)
            raise RuntimeError("partial scientific write")

        return {"run": run, "changed": True}

    with pytest.raises(RuntimeError, match="partial scientific"):
        manager.execute(prepare, name="receiving.partial")
    assert manager.get_status()["state"] == "uncertain"
    with pytest.raises(SystemEditPendingError):
        manager.synchronize()
    with msv.demo["dialanine"] as source:
        manager.replace(source.molsys)
    assert manager.get_status()["state"] == "synchronized"


@pytest.mark.parametrize("write", [False, True])
def test_reviewed_plan_finalizes_its_effect_after_one_native_call(view, write):
    manager = view.addons.manager.system_edits
    coordinates = msm.get(view.molsys, element="atom", coordinates=True).copy()
    original = msm.pyunitwizard.get_value(coordinates).copy()
    history = (list(view.history._undo), list(view.history._redo))
    calls = []

    def prepare(target):
        def run():
            calls.append(target)
            if write:
                msm.set(target, coordinates=coordinates + msm.pyunitwizard.quantity(0.1, "nm"))
            plan["changed"] = write

        # The preflight value deliberately differs from the final outcome.
        plan = {"run": run, "changed": not write, "interactions_policy": "preserve"}
        return plan

    assert manager.execute(prepare, name="receiving.final-effect", update_view=False) is None
    assert calls == [view.molsys]
    status = manager.get_status()
    assert status["target_revision"] == int(write)
    assert status["state"] == ("pending" if write else "synchronized")
    if not write:
        assert (view.history._undo, view.history._redo) == history
        np.testing.assert_array_equal(msm.pyunitwizard.get_value(view.molsys.structures.coordinates), original)
    else:
        manager.synchronize()
        np.testing.assert_allclose(
            msm.pyunitwizard.get_value(view.molsys.structures.coordinates, to_unit="nm"),
            msm.pyunitwizard.get_value(coordinates, to_unit="nm") + 0.1,
        )


def test_conflicting_scene_calls_reject_while_science_runs(view):
    entered, release = Event(), Event()
    errors = []

    def prepare(target):
        def run():
            entered.set()
            if not release.wait(timeout=10):
                raise RuntimeError("receiving fixture did not release")

        return {"run": run, "changed": False}

    def execute():
        try:
            view.addons.manager.system_edits.execute(prepare, name="receiving.lock")
        except Exception as exc:
            errors.append(exc)

    worker = Thread(target=execute)
    worker.start()
    try:
        assert entered.wait(timeout=5)
        with pytest.raises(SystemEditPendingError, match="Another operation"):
            view.active_selection.set([0])
    finally:
        release.set()
        worker.join(timeout=10)
    assert not worker.is_alive() and errors == []


@pytest.mark.parametrize("skip", [False, True])
def test_saved_selection_revalidation_is_limited_to_synchronized_preparation(view, skip):
    manager = view.addons.manager.system_edits
    selection = view.selections.add("chosen", atom_indices=[2, 4])
    view.active_selection.set([2, 4])
    before = view.export_state()
    calls = []

    def prepare(target):
        assert view.selections.get("chosen", skip_digestion=skip) is selection
        assert selection.atom_indices == [2, 4]
        assert view.selections.info("chosen", skip_digestion=skip)["atom_indices"] == [2, 4]
        assert view.active_selection.atom_indices == [2, 4]
        # A readable selection is not permission to alter it or the scene.
        with pytest.raises(SystemEditPendingError):
            selection.delete(skip_digestion=skip)
        with pytest.raises(SystemEditPendingError):
            view.active_selection.set([0], skip_digestion=skip)

        def run():
            calls.append(target)
            with pytest.raises(SystemEditPendingError):
                view.selections.get("chosen", skip_digestion=skip)
            with pytest.raises(SystemEditPendingError):
                selection.info(skip_digestion=skip)
            with pytest.raises(SystemEditPendingError):
                view.active_selection.atom_indices

        return {"run": run, "changed": False}

    manager.execute(prepare, name="receiving.selection-confirmation")
    assert calls == [view.molsys]
    assert view.export_state() == before
    assert selection.atom_indices == [2, 4]


def test_preparation_selection_scope_resets_after_rejection_and_refuses_pending_scene(view):
    manager = view.addons.manager.system_edits
    selection = view.selections.add("chosen", atom_indices=[2, 4])

    def reject(target):
        assert selection.atom_indices == [2, 4]
        raise ValueError("stale review")

    with pytest.raises(ValueError, match="stale review"):
        manager.execute(reject, name="receiving.rejected-review")
    assert manager.get_status()["state"] == "synchronized"

    coordinates = msm.get(view.molsys, coordinates=True).copy()
    manager.execute(
        lambda target: {"run": lambda: msm.set(target, coordinates=coordinates), "changed": True},
        name="receiving.deferred",
        update_view=False,
    )
    with pytest.raises(SystemEditPendingError):
        selection.info(skip_digestion=True)
    with pytest.raises(SystemEditPendingError):
        manager.execute(lambda target: selection.info(), name="receiving.stale-scene")
    assert manager.get_status()["state"] == "pending"
    assert manager.get_status()["pending_operations"] == 1
    manager.synchronize()
    assert view.selections.get("chosen").atom_indices == [2, 4]


def test_real_deferred_coordinate_edit_blocks_stale_actions_and_syncs_from_the_gui(view):
    target = view.molsys
    before = msm.pyunitwizard.get_value(target.structures.coordinates, to_unit="nm").copy()
    manager = view.addons.manager.system_edits

    def prepare(system):
        coordinates = msm.get(system, element="atom", coordinates=True).copy()
        coordinates += msm.pyunitwizard.quantity([0.1, 0.0, 0.0], "nm")
        return {"run": lambda: msm.set(system, coordinates=coordinates), "changed": True}

    manager.execute(prepare, name="receiving.coordinates", update_view=False)
    with pytest.raises(SystemEditPendingError):
        view.active_selection.set([0], skip_digestion=True)
    view._handle_frontend_event({"event": "interaction_context_action", "action": "sync_system_edits"})
    assert manager.get_status()["state"] == "synchronized"
    assert view.molsys is target
    np.testing.assert_allclose(
        msm.pyunitwizard.get_value(target.structures.coordinates, to_unit="nm"), before + [0.1, 0, 0]
    )


def test_atomic_rejection_retains_previous_pending_state_and_native_exception(view):
    manager = view.addons.manager.system_edits
    exception = ValueError("receiving rejected request before publication")

    def prepare(target):
        def run():
            raise exception

        return {"run": run, "changed": True, "failure_atomic": True}

    with pytest.raises(ValueError) as failure:
        manager.execute(prepare, name="receiving.atomic")
    assert failure.value is exception
    assert manager.get_status()["state"] == "synchronized"
    assert manager.get_status()["target_revision"] == 0


@pytest.mark.parametrize("write", [False, True])
def test_nested_state_rejection_predicate_overrides_unchanged_molsys_dictionary(view, write):
    manager = view.addons.manager.system_edits
    target = view.molsys
    state = vars(target)
    before = msm.get(target, element="atom", selection=[0], structure_indices=[0], coordinates=True).copy()

    def prepare(system):
        def run():
            if write:
                msm.set(
                    system,
                    selection=[0],
                    structure_indices=[0],
                    coordinates=before + msm.pyunitwizard.quantity(0.1, "nm"),
                )
            raise ValueError("receiving native rejection")

        # This receiving fixture performs actual science when write=True. A
        # dictionary-identity check alone cannot prove that nested data survived.
        return {"run": run, "changed": True}

    def token(system):
        # Older public setters update storage in place; newer native storage
        # replaces blocks. Observe the edited values rather than either layout.
        sample = msm.get(system, element="atom", selection=[0], structure_indices=[0], coordinates=True)
        return tuple(msm.pyunitwizard.get_value(sample, to_unit="nm").reshape(-1).tolist())

    before_token = token(target)
    with pytest.raises(ValueError, match="receiving native rejection"):
        manager.execute(prepare, name="receiving.nested", rejection_check=token)
    assert vars(target) is state
    assert (token(target) != before_token) is write
    assert manager.get_status()["state"] == ("uncertain" if write else "synchronized")


@pytest.mark.parametrize("mode", ["canvas", "panel"])
def test_pending_popup_request_is_correlated_state_only_and_closing_it_keeps_the_edit(view, mode):
    manager = view.addons.manager.system_edits

    def prepare(target):
        coordinates = msm.get(target, element="atom", coordinates=True).copy()
        coordinates += msm.pyunitwizard.quantity(0.1, "nm")
        return {"run": lambda: msm.set(target, coordinates=coordinates), "changed": True}

    manager.execute(prepare, name="receiving.coordinates", update_view=False)
    view._ready = True
    view.widget.received = []
    router = view._runtime_router
    request = {
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,
        "sessionId": view._binary_session_id,
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": "pending-popup",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {"event": "request_popup_scene_snapshot", "mode": mode, "popup_endpoint_id": "receiving-popup"},
    }
    view._handle_inbound_message(request)
    assert len(view.widget.received) == 1
    reply = view.widget.received[0]
    assert reply["correlationId"] == "pending-popup"
    assert reply["payload"]["messages"] == [manager._message()]
    assert view._current_molecular_projection is None
    invalid = dict(request, messageId="pending-popup-invalid", payload={**request["payload"], "mode": "bogus"})
    view._handle_inbound_message(invalid)
    assert len(view.widget.received) == 1
    view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": "receiving-popup"})
    assert not view.closed and manager.get_status()["state"] == "pending"
    manager.synchronize()
    assert manager.get_status()["state"] == "synchronized"
