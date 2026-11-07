"""Protocol/lifetime receiving; real renderer/Jupyter receiving is separate."""

import asyncio
import inspect
import json
import zipfile
from copy import deepcopy
from threading import Thread

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
