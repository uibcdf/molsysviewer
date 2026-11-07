"""Studio protocol receiving with real scene/file owners, not browser evidence."""

import asyncio
import json
import zipfile
from copy import deepcopy

import numpy as np
import pytest
from molsysviewer.viewer import work_file_saves
from molsysviewer.viewer.frontend_requests import FrontendRequestError
from molsysviewer.viewer.panel_actions import dispatch_panel_action
from molsysviewer.viewer.work_file_saves import WorkFileSaveCancelled

import molsysviewer as msv

CAMERA = {"position": [10.0, 20.0, 30.0], "target": [1.0, 2.0, 3.0], "up": [0.0, 1.0, 0.0], "mode": "perspective"}


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with source.extract(structure_indices=[0, 8, 3]) as scene:
            scene._ready = True
            scene._frontend_capabilities = {"visual_state_capture": [1]}
            yield scene


@pytest.fixture
def messages(view):
    sent = []
    original = view.widget.send

    def observe(message, buffers=None):
        sent.append(deepcopy(message))
        return original(message, buffers=buffers)

    view.widget.send = observe
    return sent


def intent(path, *, owner="primary", canvas="primary", request_id="save-review", kind="state", **details):
    return {
        "action": "save_work_file",
        "path": str(path),
        "file_kind": kind,
        "request_id": request_id,
        "_work_file_owner_endpoint_id": owner,
        "_capture_endpoint_id": canvas,
        **details,
    }


def begin(view, content):
    future = dispatch_panel_action(view, content)
    operation = next(operation for operation in view._work_file_saves._pending.values() if operation.result is future)
    return future, operation.ticket


def reply(view, ticket, *, camera=CAMERA, frame=None, endpoint=None):
    view._handle_frontend_event(
        {
            "event": "visual_state_snapshot",
            "request_id": ticket.request_id,
            "capture_revision": ticket.revision,
            "ok": True,
            "snapshot": deepcopy(camera),
            "structure_index": view.player.index if frame is None else frame,
            "_capture_endpoint_id": ticket.endpoint_id if endpoint is None else endpoint,
        }
    )


def results(messages):
    return [message for message in messages if message.get("op") == "studio_action_result"]


def read_state(path, kind):
    if kind == "state":
        return json.loads(path.read_text())
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read("state.json"))


@pytest.mark.parametrize("action", ["restore_work_file", "batch_scene_objects"])
def test_other_correlated_studio_actions_keep_their_popup_owner(view, messages, tmp_path, action):
    view._endpoint_transfers.register("studio-owner", "canvas")
    content = {
        "event": "interaction_context_action",
        "action": action,
        "request_id": "shared-id",
        "_studio_owner_endpoint_id": "studio-owner",
    }
    if action == "restore_work_file":
        content.update(path=str(tmp_path / "missing.json"), file_kind="state", confirmed=True)
    else:
        content.update(domain="regions", operation="hide", tags=["missing-region"])
    view._handle_frontend_event(content)
    verdict = results(messages)
    assert len(verdict) == 1 and verdict[0]["ok"] is False
    assert verdict[0]["target_endpoint_id"] == "studio-owner"
    error = [message for message in messages if message.get("op") == "backend_error_occurred"]
    assert len(error) == 1 and error[0]["target_endpoint_id"] == "studio-owner"
    assert error[0]["request_id"] == verdict[0]["request_id"] == "shared-id"


def coordinates(view):
    return msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="angstrom").copy()


@pytest.mark.parametrize("kind", ["state", "session"])
def test_save_success_follows_actual_bytes_with_exact_captured_camera_and_frame(view, messages, tmp_path, kind):
    async def receive():
        view.player.go_to_structure(2)
        view.annotations.add("saved", atom_indices=[0], tag="site")
        before = coordinates(view)
        path = tmp_path / ("scene.json" if kind == "state" else "scene.msv")
        success_bytes = []
        original = view.widget.send

        def observe(message, buffers=None):
            if message.get("op") == "studio_action_result" and message.get("ok"):
                success_bytes.append(read_state(path, kind))
            return original(message, buffers=buffers)

        view.widget.send = observe
        future, ticket = begin(view, intent(path, kind=kind))
        assert not future.done() and not path.exists()
        assert results(messages) == []
        latest = deepcopy(CAMERA)
        latest["position"][0] = -500
        view._handle_frontend_event({"event": "camera_snapshot", "snapshot": latest})
        reply(view, ticket, frame=2)
        await asyncio.wait_for(asyncio.wrap_future(future), timeout=1)
        saved = read_state(path, kind)
        assert saved["view"]["camera"] == CAMERA
        assert saved["view"]["structure_index"] == 2
        assert saved["annotations"][0]["tag"] == "site"
        assert success_bytes == [saved]
        assert view.camera.get_snapshot() == latest
        np.testing.assert_array_equal(coordinates(view), before)
        assert not view._work_file_saves._pending and not view._frontend_requests._pending
        assert not view.widget._scheduled_callbacks
        assert results(messages) == [
            {
                "op": "studio_action_result",
                "action": "save_work_file",
                "request_id": "save-review",
                "ok": True,
                "domain": "export",
                "target_endpoint_id": f"widget-host:{view._binary_session_id}",
            }
        ]

    asyncio.run(receive())


@pytest.mark.parametrize("first_owner", ["first", "primary", "host"])
def test_identical_request_ids_in_distinct_windows_remain_independent_and_targeted(
    view, messages, tmp_path, first_owner
):
    async def receive():
        for endpoint in ("first", "second"):
            view._endpoint_transfers.register(endpoint, "canvas")
        first_path, second_path = tmp_path / "first.json", tmp_path / "second.json"
        owner = f"widget-host:{view._binary_session_id}" if first_owner == "host" else first_owner
        canvas = "primary" if first_owner in {"primary", "host"} else "first"
        target = f"widget-host:{view._binary_session_id}" if canvas == "primary" else owner
        first, first_ticket = begin(view, intent(first_path, owner=owner, canvas=canvas))
        second, second_ticket = begin(view, intent(second_path, owner="second", canvas="second"))
        assert first_ticket.request_id != second_ticket.request_id
        reply(view, second_ticket, endpoint="first")
        assert not first.done() and not second.done()
        reply(view, second_ticket)
        await asyncio.wrap_future(second)
        assert not first.done() and not first_path.exists()
        assert second_path.exists()
        assert [message.get("target_endpoint_id") for message in results(messages)] == ["second"]
        other_camera = deepcopy(CAMERA)
        other_camera["position"][0] = 99
        reply(view, first_ticket, camera=other_camera)
        await asyncio.wrap_future(first)
        assert read_state(first_path, "state")["view"]["camera"] == other_camera
        assert read_state(second_path, "state")["view"]["camera"] == CAMERA
        assert [message.get("target_endpoint_id") for message in results(messages)] == ["second", target]

    asyncio.run(receive())


def test_cancel_is_owner_scoped_and_late_capture_cannot_write(view, messages, tmp_path):
    async def receive():
        for endpoint in ("first", "second"):
            view._endpoint_transfers.register(endpoint, "canvas")
        path = tmp_path / "keep.json"
        path.write_bytes(b"original bytes")
        first, ticket = begin(view, intent(path, owner="first", canvas="first", overwrite=True))
        second_path = tmp_path / "other.json"
        second, other_ticket = begin(view, intent(second_path, owner="second", canvas="second"))
        dispatch_panel_action(
            view, {"action": "cancel_work_file", "request_id": "save-review", "_work_file_owner_endpoint_id": "first"}
        )
        with pytest.raises(WorkFileSaveCancelled):
            await asyncio.wrap_future(first)
        assert not second.done()
        assert [(message["action"], message["ok"], message.get("cancelled")) for message in results(messages)] == [
            ("save_work_file", False, True),
            ("cancel_work_file", True, None),
        ]
        assert all(message.get("target_endpoint_id") == "first" for message in results(messages))
        aborts = [message for message in messages if message.get("op") == "cancel_visual_state"]
        assert aborts == [
            {
                "op": "cancel_visual_state",
                "request_id": ticket.request_id,
                "capture_revision": ticket.revision,
                "target_endpoint_id": "first",
            }
        ]
        assert ticket.request_id != "save-review", "capture correlation is not the Studio domain id"
        reply(view, ticket)
        assert path.read_bytes() == b"original bytes"
        reply(view, other_ticket)
        await asyncio.wrap_future(second)
        assert second_path.exists()
        assert not view._work_file_saves._pending and not view._frontend_requests._pending
        assert not view.widget._scheduled_callbacks

    asyncio.run(receive())


def test_cancel_after_commit_is_refused_after_the_original_success(view, messages, tmp_path):
    async def receive():
        path = tmp_path / "saved.json"
        future, ticket = begin(view, intent(path))
        reply(view, ticket)
        await asyncio.wrap_future(future)
        saved = path.read_bytes()
        cancellation = dispatch_panel_action(view, {"action": "cancel_work_file", "request_id": "save-review"})
        with pytest.raises(FrontendRequestError, match="cancellation_too_late"):
            await asyncio.wrap_future(cancellation)
        assert [(message["action"], message["ok"]) for message in results(messages)] == [
            ("save_work_file", True),
            ("cancel_work_file", False),
        ]
        assert path.read_bytes() == saved

    asyncio.run(receive())


def test_view_close_releases_renderer_capture_before_closing_its_connector(view, messages, tmp_path):
    async def receive():
        path = tmp_path / "closed.json"
        future, ticket = begin(view, intent(path))
        view.close()
        with pytest.raises(FrontendRequestError):
            await asyncio.wrap_future(future)
        aborts = [message for message in messages if message.get("op") == "cancel_visual_state"]
        assert aborts == [
            {"op": "cancel_visual_state", "request_id": ticket.request_id, "capture_revision": ticket.revision}
        ]
        assert view.widget._callbacks_closed
        assert not path.exists()
        assert not view._frontend_requests._pending and not view._work_file_saves._pending

    asyncio.run(receive())


@pytest.mark.parametrize("closed", ["owner", "renderer"])
def test_owner_or_associated_renderer_closure_cancels_only_its_save(view, messages, tmp_path, closed):
    async def receive():
        view._endpoint_transfers.register("owner", "panel")
        view._endpoint_transfers.register("renderer", "canvas")
        path = tmp_path / "keep.json"
        path.write_bytes(b"original bytes")
        future, ticket = begin(view, intent(path, owner="owner", canvas="renderer", overwrite=True))
        other_path = tmp_path / "primary.json"
        other, other_ticket = begin(view, intent(other_path))
        view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": closed})
        with pytest.raises(FrontendRequestError, match="endpoint_closed"):
            await asyncio.wrap_future(future)
        assert not other.done()
        reply(view, ticket)
        assert path.read_bytes() == b"original bytes"
        reply(view, other_ticket)
        await asyncio.wrap_future(other)
        assert other_path.exists()
        assert not view._work_file_saves._pending and not view._frontend_requests._pending
        assert not view.widget._scheduled_callbacks

    asyncio.run(receive())


def test_no_host_loop_refuses_save_without_falling_back_to_cached_state(view, messages, tmp_path):
    path = tmp_path / "keep.json"
    path.write_bytes(b"original bytes")
    with pytest.raises(FrontendRequestError, match="scheduler_unavailable"):
        dispatch_panel_action(view, intent(path, overwrite=True))
    assert path.read_bytes() == b"original bytes"
    assert not view._work_file_saves._pending and not view._frontend_requests._pending
    assert not view.widget._scheduled_callbacks
    assert len(results(messages)) == 1 and results(messages)[0]["ok"] is False


def test_host_timer_autonomously_expires_capture_without_more_frontend_traffic(view, messages, tmp_path, monkeypatch):
    monkeypatch.setattr(work_file_saves, "CAPTURE_TIMEOUT", 0.01)

    async def receive():
        path = tmp_path / "keep.json"
        path.write_bytes(b"original bytes")
        future, ticket = begin(view, intent(path, overwrite=True))
        with pytest.raises(FrontendRequestError, match="request_timeout"):
            await asyncio.wait_for(asyncio.wrap_future(future), timeout=1)
        assert path.read_bytes() == b"original bytes"
        assert not view._work_file_saves._pending and not view._frontend_requests._pending
        assert not view.widget._scheduled_callbacks
        assert len(results(messages)) == 1 and results(messages)[0]["ok"] is False
        reply(view, ticket)
        assert path.read_bytes() == b"original bytes"
        assert len(results(messages)) == 1

    asyncio.run(receive())


@pytest.mark.parametrize("outcome", ["saved", "cancelled", "timeout", "invalid_camera"])
def test_popup_verdicts_bypass_unrelated_primary_stream_and_keep_diagnostics_requester_only(
    view, messages, tmp_path, monkeypatch, outcome
):
    monkeypatch.setattr(work_file_saves, "CAPTURE_TIMEOUT", 0.01 if outcome == "timeout" else 1)

    async def receive():
        view._endpoint_transfers.register("requester", "canvas")
        view._endpoint_transfers.register("unrelated", "canvas")
        view._frontend_capabilities.update(binary_structure_data=[1], max_buffer_bytes=16 * 1024 * 1024)
        assert view._try_send_array_native_molsys(view._current_molecular_projection)
        manager = view._structure_transfer_manager(None)
        transfer = manager.active
        assert transfer is not None
        # A real ordinary scene command must remain behind the unacknowledged
        # primary structure, while the other endpoint's control verdict escapes.
        view.camera.set_snapshot(CAMERA)
        assert view._endpoint_transfers.state(None).deferred
        path = tmp_path / "keep.json"
        path.write_bytes(b"original bytes")
        future, ticket = begin(view, intent(path, owner="requester", canvas="requester", overwrite=True))
        if outcome == "cancelled":
            dispatch_panel_action(
                view,
                {
                    "action": "cancel_work_file",
                    "request_id": "save-review",
                    "_work_file_owner_endpoint_id": "requester",
                },
            )
            with pytest.raises(WorkFileSaveCancelled):
                await asyncio.wrap_future(future)
        elif outcome in {"timeout", "invalid_camera"}:
            if outcome == "invalid_camera":
                reply(view, ticket, camera={"position": [1, 2, 3]})
            with pytest.raises(
                FrontendRequestError, match="request_timeout" if outcome == "timeout" else "invalid_camera"
            ):
                await asyncio.wait_for(asyncio.wrap_future(future), timeout=1)
        else:
            reply(view, ticket)
            await asyncio.wrap_future(future)
        verdicts = results(messages)
        assert len(verdicts) == (2 if outcome == "cancelled" else 1)
        assert all(message["target_endpoint_id"] == "requester" for message in verdicts)
        diagnostics = [message for message in messages if message.get("op") == "backend_error_occurred"]
        assert len(diagnostics) == (1 if outcome in {"timeout", "invalid_camera"} else 0)
        assert all(message.get("target_endpoint_id") == "requester" for message in diagnostics)
        assert all(message.get("request_id") == "save-review" for message in diagnostics)
        assert manager.active is transfer, "No primary stream acknowledgement was supplied"
        assert all(
            message.get("op") not in {"studio_action_result", "backend_error_occurred"}
            for message, _buffers in view._endpoint_transfers.state(None).deferred
        )
        if outcome == "saved":
            assert read_state(path, "state")["view"]["camera"] == CAMERA
        else:
            assert path.read_bytes() == b"original bytes"

    asyncio.run(receive())


@pytest.mark.parametrize("owner", ["primary", "host", "requester"])
def test_async_save_failure_diagnostic_preserves_requester_and_correlation(view, messages, tmp_path, owner):
    async def receive():
        view._endpoint_transfers.register("requester", "canvas")
        host = f"widget-host:{view._binary_session_id}"
        requester = host if owner == "host" else owner
        canvas = "requester" if owner == "requester" else "primary"
        path = tmp_path / "absent.json"
        future, ticket = begin(view, intent(path, owner=requester, canvas=canvas))
        reply(view, ticket, camera={"position": [1, 2, 3]})
        with pytest.raises(FrontendRequestError, match="invalid_camera"):
            await asyncio.wrap_future(future)
        diagnostics = [message for message in messages if message.get("op") == "backend_error_occurred"]
        assert len(diagnostics) == 1
        assert diagnostics[0]["target_endpoint_id"] == ("requester" if owner == "requester" else host)
        assert diagnostics[0]["request_id"] == "save-review"
        assert diagnostics[0]["action"] == "save_work_file"
        assert "invalid_camera" in diagnostics[0]["error_message"]
        assert not path.exists()

    asyncio.run(receive())
