"""Protocol/lifetime receiving; real renderer/Jupyter receiving is separate."""

import asyncio
import inspect
import json
import time
import zipfile
from copy import deepcopy
from threading import Event, Thread

import numpy as np
import pytest
from molsysviewer.system_edits import SystemEditPendingError
from molsysviewer.viewer.frontend_requests import FrontendRequestError, FrontendRequests

import molsysviewer as msv

CAMERA = {"position": [10.0, 20.0, 30.0], "target": [1.0, 2.0, 3.0], "up": [0.0, 1.0, 0.0], "mode": "perspective"}


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with source.extract(structure_indices=[0, 8, 3]) as scene:
            # These tests drive the protocol, not a rendered frontend.
            scene._ready = True
            scene._frontend_capabilities = {"visual_state_capture": [1]}
            yield scene


def response(request, *, frame=0, camera=None):
    return {
        "event": "visual_state_snapshot",
        "request_id": request.request_id,
        "capture_revision": request.revision,
        "ok": True,
        "snapshot": deepcopy(CAMERA if camera is None else camera),
        "structure_index": frame,
    }


def coordinates(view):
    return msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="angstrom").copy()


async def pending(view, coroutine):
    task = asyncio.create_task(coroutine)
    await asyncio.sleep(0)  # Schedule the owner until its explicit renderer wait.
    assert not task.done()
    assert len(view._frontend_requests._pending) == 1
    return task, next(iter(view._frontend_requests._pending.values()))


@pytest.mark.parametrize("kind", ["state", "session"])
def test_async_save_waits_for_transient_foreign_scene_ownership(view, tmp_path, kind):
    async def exercise():
        entered, release = Event(), Event()

        def occupy():
            with view._system_edits._locked():
                entered.set()
                assert release.wait(timeout=5)

        worker = Thread(target=occupy)
        worker.start()
        assert entered.wait(timeout=2)
        task = None
        try:
            path = tmp_path / ("owned.json" if kind == "state" else "owned.msv")
            method = view.save_state_async if kind == "state" else view.save_session_async
            task = asyncio.create_task(method(path))
            await asyncio.sleep(0)
            assert not task.done(), "A brief frame callback must not reject the public async save."
            assert not view._frontend_requests._pending and not path.exists()
            release.set()
            worker.join(timeout=2)
            assert not worker.is_alive()
            deadline = asyncio.get_running_loop().time() + 2
            while not view._frontend_requests._pending and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.001)
            ticket = next(iter(view._frontend_requests._pending.values()))
            view._handle_frontend_event(response(ticket))
            await task
            assert path.is_file() and not view._frontend_requests._pending
        finally:
            release.set()
            worker.join(timeout=2)
            if task is not None:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


@pytest.mark.parametrize("termination", ["timeout", "cancel"])
def test_waiting_for_scene_owner_is_bounded_and_cannot_write_later(view, tmp_path, termination):
    async def exercise():
        entered, release = Event(), Event()

        def occupy():
            with view._system_edits._locked():
                entered.set()
                assert release.wait(timeout=5)

        worker = Thread(target=occupy)
        worker.start()
        assert entered.wait(timeout=2)
        path = tmp_path / "must-not-exist.json"
        task = asyncio.create_task(view.save_state_async(path, timeout=0.02 if termination == "timeout" else 5))
        try:
            await asyncio.sleep(0)
            if termination == "cancel":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                with pytest.raises(FrontendRequestError, match="request_timeout"):
                    await task
        finally:
            release.set()
            worker.join(timeout=2)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await asyncio.sleep(0)
        assert not path.exists() and not view._frontend_requests._pending
        assert not view._system_edits._unlock_callbacks

    asyncio.run(exercise())


def test_cancelling_after_owner_grant_before_consumer_resume_releases_capture(view, tmp_path):
    async def exercise():
        entered, release = Event(), Event()

        def occupy():
            with view._system_edits._locked():
                entered.set()
                assert release.wait(timeout=5)

        worker = Thread(target=occupy)
        worker.start()
        assert entered.wait(timeout=2)
        path = tmp_path / "cancel-at-grant.json"
        task = asyncio.create_task(view.save_state_async(path))
        try:
            await asyncio.sleep(0)
            assert not task.done()
            release.set()
            worker.join(timeout=2)
            assert not worker.is_alive()
            # The real grant is already queued. Cancel after it creates the
            # broker request, but before the waiting caller resumes.
            asyncio.get_running_loop().call_soon(task.cancel)
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not view._frontend_requests._pending
            assert not path.exists()
        finally:
            release.set()
            worker.join(timeout=2)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


def test_reply_notification_does_not_retain_the_molecular_lock(view):
    request = view._frontend_requests.begin(
        endpoint_id="primary", reply_event="visual_state_snapshot", revision="v1", timeout=5
    )
    observed = []

    def acquire():
        try:
            with view._system_edits._locked():
                observed.append("acquired")
        except SystemEditPendingError:
            observed.append("still_locked")

    def completed(_):
        worker = Thread(target=acquire)
        worker.start()
        worker.join(timeout=1)
        assert not worker.is_alive()

    request.future.add_done_callback(completed)
    view._handle_frontend_event(response(request))
    assert observed == ["acquired"]


@pytest.mark.parametrize("termination", ["endpoint", "close", "expiration"])
def test_capture_failure_notifications_wait_for_the_outer_molecular_guard(view, termination):
    observed = []
    view._endpoint_transfers.register("popup-review", "canvas")
    request = view._frontend_requests.begin(
        endpoint_id="popup-review",
        reply_event="visual_state_snapshot",
        revision="v1",
        timeout=0.001 if termination == "expiration" else 5,
    )

    def completed(_):
        def acquire():
            try:
                with view._system_edits._locked():
                    observed.append("acquired")
            except SystemEditPendingError:
                observed.append("still_locked")

        worker = Thread(target=acquire)
        worker.start()
        worker.join(timeout=1)
        assert not worker.is_alive()

    request.future.add_done_callback(completed)
    with view._system_edits._locked():
        if termination == "close":
            view.close()
        elif termination == "endpoint":
            view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": "popup-review"})
        else:
            time.sleep(max(0, request.deadline - time.monotonic()) + 0.001)
            # A new reservation expires old requests while preparing a scene.
            with view._system_edits._locked():
                next_request = view._frontend_requests.begin(
                    endpoint_id="primary", reply_event="visual_state_snapshot", revision="v2", timeout=5
                )
                view._frontend_requests.cancel(next_request)
        assert observed == []
    assert observed == ["acquired"]
    assert not view._frontend_requests._pending


def test_studio_cancel_future_resumes_after_the_connector_releases_scene_ownership(view, tmp_path):
    from molsysviewer.viewer.panel_actions import dispatch_panel_action

    observed = []

    async def receive():
        future = dispatch_panel_action(
            view,
            {
                "action": "save_work_file",
                "request_id": "cancel-review",
                "file_kind": "state",
                "path": str(tmp_path / "cancelled.json"),
                "_work_file_owner_endpoint_id": "primary",
            },
        )

        def completed(_):
            def acquire():
                try:
                    with view._system_edits._locked():
                        observed.append("acquired")
                except SystemEditPendingError:
                    observed.append("still_locked")

            worker = Thread(target=acquire)
            worker.start()
            worker.join(timeout=1)
            assert not worker.is_alive()

        future.add_done_callback(completed)
        view._handle_frontend_event(
            {
                "event": "interaction_context_action",
                "action": "cancel_work_file",
                "request_id": "cancel-review",
                "_work_file_owner_endpoint_id": "primary",
            }
        )
        with pytest.raises(FrontendRequestError):
            await asyncio.wrap_future(future)
        assert observed == ["acquired"]
        assert not (tmp_path / "cancelled.json").exists()
        assert not view._frontend_requests._pending and not view._work_file_saves._pending

    asyncio.run(receive())


@pytest.mark.parametrize(
    "field,value", [("event", "camera_snapshot"), ("request_id", "other"), ("capture_revision", "older")]
)
def test_unsolicited_and_mismatched_replies_do_not_complete_capture(field, value):
    owner = FrontendRequests()
    request = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    message = response(request)
    message[field] = value
    assert not owner.receive(message, endpoint_id="canvas")
    assert not request.future.done()
    assert not owner.receive(response(request), endpoint_id="other-window")
    owner.close()
    with pytest.raises(FrontendRequestError, match="view_closed"):
        request.future.result()


def test_replies_are_single_use_detached_and_resolve_out_of_order():
    owner = FrontendRequests()
    first = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    second = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    message = response(second)
    assert owner.receive(message, endpoint_id="canvas")
    message["snapshot"]["position"][0] = -100
    assert second.future.result()["snapshot"] == CAMERA
    assert not first.future.done()
    assert not owner.receive(response(second), endpoint_id="canvas")
    assert owner.receive(response(first), endpoint_id="canvas")
    assert not owner._pending
    assert asyncio.run(owner.wait(second))["snapshot"] == CAMERA
    with pytest.raises(FrontendRequestError, match="unknown_request"):
        asyncio.run(FrontendRequests().wait(second))


def test_endpoint_loss_and_capacity_preserve_unrelated_requests():
    owner = FrontendRequests(capacity=2)
    first = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    second = owner.begin(endpoint_id="popup", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    with pytest.raises(FrontendRequestError, match="request_capacity"):
        owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="v1", timeout=5)
    owner.cancel_endpoint("popup")
    with pytest.raises(FrontendRequestError, match="endpoint_closed"):
        second.future.result()
    assert not first.future.done()
    first.future.cancel()
    assert not owner._pending


@pytest.mark.parametrize("termination", ["cancel", "future", "endpoint", "expiry", "close"])
def test_abandoned_capture_notifies_its_exact_renderer_once_after_unlock(termination):
    notifications = []
    published = []
    owner = FrontendRequests(publish=published.append, abandon=lambda ticket: notifications.append(ticket))
    request = owner.begin(endpoint_id="canvas-a", reply_event="visual_state_snapshot", revision="r1", timeout=5)
    other = owner.begin(endpoint_id="canvas-b", reply_event="visual_state_snapshot", revision="r2", timeout=5)
    if termination == "cancel":
        owner.cancel(request)
        owner.cancel(request)
    elif termination == "future":
        request.future.cancel()
    elif termination == "endpoint":
        owner.cancel_endpoint("canvas-a")
    elif termination == "expiry":
        # A represented expired deadline avoids a test sleep or a second clock.
        object.__setattr__(request, "deadline", time.monotonic() - 1)
        owner.expire()
    else:
        owner.close()
    assert not notifications
    while published:
        published.pop(0)()
    expected = [request, other] if termination == "close" else [request]
    assert notifications == expected
    assert not owner.receive(response(request), endpoint_id="canvas-a")
    if termination != "close":
        assert not other.future.done()
    owner.cancel(request)
    while published:
        published.pop(0)()
    assert notifications == expected
    owner.close()


def test_successful_capture_wait_does_not_abort_its_renderer():
    abandoned = []
    owner = FrontendRequests(abandon=abandoned.append)
    request = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="r1", timeout=5)
    assert owner.receive(response(request), endpoint_id="canvas")
    assert asyncio.run(owner.wait(request))["snapshot"] == CAMERA
    owner.cancel(request)
    owner.close()
    assert abandoned == []


@pytest.mark.parametrize("termination", ["cancel", "expiry"])
def test_failed_abort_transport_still_completes_and_releases_the_capture(termination):
    def unavailable(_):
        raise RuntimeError("Transport closed during cancellation")

    owner = FrontendRequests(abandon=unavailable)
    request = owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="r1", timeout=5)
    with pytest.raises(RuntimeError, match="Transport closed"):
        if termination == "cancel":
            owner.cancel(request)
        else:
            object.__setattr__(request, "deadline", time.monotonic() - 1)
            owner.expire()
    assert request.future.done()
    assert not owner._pending
    owner.close()


@pytest.mark.parametrize("termination", ["endpoint", "expiry", "close"])
def test_failed_abort_transport_does_not_strand_other_retired_captures(termination):
    abandoned = []

    def unavailable(request):
        abandoned.append(request.request_id)
        raise RuntimeError("Transport closed during cancellation")

    owner = FrontendRequests(abandon=unavailable)
    requests = [
        owner.begin(endpoint_id="canvas", reply_event="visual_state_snapshot", revision="r1", timeout=5)
        for _ in range(3)
    ]
    with pytest.raises(ExceptionGroup) as errors:
        if termination == "endpoint":
            owner.cancel_endpoint("canvas")
        elif termination == "expiry":
            for request in requests:
                object.__setattr__(request, "deadline", time.monotonic() - 1)
            owner.expire()
        else:
            owner.close()
    assert len(errors.value.exceptions) == 3
    assert all(isinstance(error, RuntimeError) for error in errors.value.exceptions)
    assert abandoned == [request.request_id for request in requests]
    assert all(request.future.done() for request in requests)
    assert not owner._pending
    owner.close()


@pytest.mark.parametrize("endpoint", [None, "popup-review"])
def test_abandoned_capture_removes_only_its_matching_deferred_barrier(view, endpoint):
    if endpoint is not None:
        view._endpoint_transfers.register(endpoint, "canvas")
    request = view._frontend_requests.begin(
        endpoint_id=endpoint or "primary", reply_event="visual_state_snapshot", revision="r1", timeout=5
    )
    barrier = {"op": "request_visual_state", "request_id": request.request_id, "capture_revision": "r1"}
    another = {**barrier, "capture_revision": "r2"}
    scene = {"op": "clear_all"}
    for message in (scene, barrier, another):
        view._endpoint_transfers.defer(endpoint, message, None)
    view._frontend_requests.cancel(request)
    assert [m for m, _ in view._endpoint_transfers.state(endpoint).deferred] == [scene, another]


@pytest.mark.parametrize("kind", ["state", "session"])
def test_async_save_uses_exact_reply_despite_unrelated_camera_telemetry(view, tmp_path, kind):
    async def run():
        view.player.go_to_structure(2)
        view.annotations.add("saved", atom_indices=[0], tag="site")
        old = deepcopy(CAMERA)
        old["position"][0] = -500
        view.camera.set_snapshot(old)
        before = coordinates(view)
        path = tmp_path / ("saved.json" if kind == "state" else "saved.msv")
        operation = view.save_state_async if kind == "state" else view.save_session_async
        task, ticket = await pending(view, operation(path))
        other_window = {**response(ticket, frame=2), "_capture_endpoint_id": "another-popup"}
        view._handle_frontend_event(other_window)
        assert not ticket.future.done()
        view._handle_frontend_event(response(ticket, frame=2))
        # A newer ordinary push arrives before the waiting task resumes. The
        # writer must use the correlated reply, not re-read this mutable cache.
        view._handle_frontend_event({"event": "camera_snapshot", "snapshot": old})
        await task
        if kind == "state":
            saved = json.loads(path.read_text())
        else:
            with zipfile.ZipFile(path) as archive:
                saved = json.loads(archive.read("state.json"))
            with msv.load_session(path) as restored:
                assert restored.player.index == 2
                assert restored.camera.get_snapshot() == CAMERA
                np.testing.assert_array_equal(coordinates(restored), before)
        assert saved["view"]["camera"] == CAMERA
        assert saved["view"]["structure_index"] == 2
        assert saved["annotations"][0]["tag"] == "site"
        assert view.camera.get_snapshot() == old
        assert not view._frontend_requests._pending
        np.testing.assert_array_equal(coordinates(view), before)

    asyncio.run(run())


@pytest.mark.parametrize("change", ["scene", "frame", "reply_frame", "invalid_camera", "renderer_refused", "close"])
def test_rejected_capture_preserves_destination_and_releases_request(view, tmp_path, change):
    async def run():
        path = tmp_path / "keep.json"
        path.write_text("original bytes")
        task, ticket = await pending(view, view.save_state_async(path))
        message = response(ticket)
        if change == "scene":
            view.annotations.add("new", atom_indices=[0])
        elif change == "frame":
            view.player.go_to_structure(1)
        elif change == "reply_frame":
            message["structure_index"] = 1
        elif change == "invalid_camera":
            message["snapshot"]["target"][0] = float("nan")
        elif change == "renderer_refused":
            message["ok"] = False
        else:
            view.close()
        view._handle_frontend_event(message)
        with pytest.raises(FrontendRequestError):
            await task
        assert path.read_text() == "original bytes"
        assert not view._frontend_requests._pending

    asyncio.run(run())


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_or_cancellation_never_writes_later(view, tmp_path, cancel):
    async def run():
        path = tmp_path / "untouched.json"
        path.write_text("keep")
        if cancel:
            task, ticket = await pending(view, view.save_state_async(path))
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not view._frontend_requests.receive(response(ticket), endpoint_id="primary")
        else:
            with pytest.raises(FrontendRequestError, match="request_timeout"):
                await view.save_state_async(path, timeout=0.001)
        assert path.read_text() == "keep"
        assert not view._frontend_requests._pending
        assert not list(tmp_path.glob("*.tmp"))

    asyncio.run(run())


@pytest.mark.parametrize("timeout", [0, -1, True, "5", float("inf"), float("nan")])
def test_public_async_arguments_are_digested_before_dispatch(view, tmp_path, timeout):
    assert inspect.iscoroutinefunction(view.save_state_async)
    with pytest.raises(Exception):
        asyncio.run(view.save_state_async(tmp_path / "absent", timeout=timeout))
    assert not view._frontend_requests._pending
    assert not list(tmp_path.iterdir())


def test_live_capture_requires_explicit_frontend_capability_but_sync_saving_is_headless(view, tmp_path):
    view._ready = False
    with pytest.raises(FrontendRequestError, match="no_live_frontend"):
        asyncio.run(view.save_state_async(tmp_path / "no-live.json"))
    view._ready = True
    view._frontend_capabilities = {}
    with pytest.raises(FrontendRequestError, match="capture_not_supported"):
        asyncio.run(view.save_state_async(tmp_path / "unsupported.json"))
    view._ready = False
    view.save_state(tmp_path / "headless.json")
    assert json.loads((tmp_path / "headless.json").read_text())["version"] == 2
