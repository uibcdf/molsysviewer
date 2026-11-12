"""Real View, typed transfers and cross-thread callbacks; no renderer claims."""

import asyncio
from contextvars import ContextVar
from threading import Event, Thread

import pytest
from molsysviewer.system_edits import SystemEditPendingError
from molsysviewer.transport import TransferState

import molsysviewer as msv


@pytest.mark.parametrize("event", ["request_dynamic_region_evaluation", "request_interaction_frame"])
@pytest.mark.parametrize(
    "endpoint,terminal",
    [
        ("primary", "deliver"),
        ("popup-review", "deliver"),
        ("primary", "close"),
        ("popup-review", "close"),
        ("popup-review", "retire"),
    ],
)
def test_frame_queries_survive_foreign_scene_ownership(event, endpoint, terminal):
    async def exercise():
        with msv.demo["dialanine"] as view:
            original = view.molsys
            region = view.regions.add(
                selection="atom_index==1 within 1 nm without pbc of atom_index==0", tag="query-region"
            )
            region.mode = "dynamic"
            view.interactions.hbonds.get_buch_hbonds(name="query-analysis", structure_indices="all")
            view.interactions.add("query-analysis", tag="query-hbonds")
            view._ready = True
            if endpoint != "primary":
                view._endpoint_transfers.register(endpoint, "canvas")
            sent, errors, contexts = [], [], []
            scope = ContextVar("frame_query_context", default="scene-owner")
            native_send = view.widget.send

            def observe(message, buffers=None):
                if message.get("request_id") == 17:
                    sent.append(dict(message))
                    contexts.append(scope.get())
                return native_send(message, buffers=buffers)

            view.widget.send = observe

            def receive():
                scope.set("connector")
                try:
                    view._handle_frontend_event(
                        {"event": event, "frame": 0, "request_id": 17, "_query_endpoint_id": endpoint}
                    )
                except Exception as error:
                    errors.append(error)

            with view._system_edits._locked():
                worker = Thread(target=receive)
                worker.start()
                worker.join(timeout=2)
                assert not worker.is_alive(), "Scientific callbacks must not block the connector thread."
                assert not errors, errors
                assert not sent, "Scientific queries must wait for the current scene owner."
                if terminal == "close":
                    view.close()
                elif terminal == "retire":
                    view._endpoint_transfers.close(endpoint)
            if terminal == "close":
                assert not sent and not view.widget._scheduled_callbacks
                return
            expected = (
                ["set_dynamic_region_atoms"]
                if event.endswith("evaluation")
                else ["set_interaction_frame", "interaction_frame_complete"]
            )
            deadline = asyncio.get_running_loop().time() + 2
            if terminal == "retire":
                while view.widget._scheduled_callbacks and asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(0.001)
                assert not sent and not view.widget._scheduled_callbacks
                return
            while len(sent) < len(expected) and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.001)
            assert [message["op"] for message in sent] == expected
            owner = f"widget-host:{view._binary_session_id}" if endpoint == "primary" else endpoint
            assert all(message["target_endpoint_id"] == owner for message in sent)
            assert sent[0]["frame"] == 0
            assert contexts == ["connector"] * len(expected)
            assert view.molsys is original and not view.widget._scheduled_callbacks

    asyncio.run(exercise())


@pytest.mark.parametrize("endpoint,terminal", [(None, "deliver"), ("popup-review", "deliver"), (None, "close")])
def test_transfer_ack_waits_for_foreign_edit_owner_without_losing_identity(endpoint, terminal):
    async def exercise():
        with msv.demo["dialanine"] as view:
            sent, errors, scene_errors, contexts = [], [], [], []
            scope = ContextVar("receiving_transport_scope", default="scene-owner")
            native_send = view.widget.send

            def observe(message, buffers=None):
                sent.append((dict(message), list(buffers or [])))
                if message["op"] == "structure_data_chunk":
                    contexts.append(scope.get())
                return native_send(message, buffers=buffers)

            view.widget.send = observe
            view._ready = True
            view._frontend_capabilities = {"binary_structure_data": [1], "max_buffer_bytes": 16 * 1024 * 1024}
            if endpoint:
                view._endpoint_transfers.register(endpoint, "canvas")
            assert view._try_send_array_native_molsys(view._current_molecular_projection, target_endpoint_id=endpoint)
            manager = view._structure_transfer_manager(endpoint)
            transfer = manager.active
            event = {"event": "structure_data_begin_ack", **transfer.begin_message}
            event.pop("op")

            def receive():
                scope.set("connector")
                try:
                    view._handle_inbound_message(event)
                except Exception as error:
                    errors.append(error)
                try:
                    view.active_selection.set([0])
                except SystemEditPendingError:
                    scene_errors.append("rejected")

            with view._system_edits._locked():
                worker = Thread(target=receive)
                worker.start()
                worker.join(timeout=2)
                assert not worker.is_alive(), "The connector must not block behind molecular work."
                assert not errors, errors
                assert scene_errors == ["rejected"]
                assert transfer.state is TransferState.WAITING_BEGIN_ACK
                assert not any(message["op"] == "structure_data_chunk" for message, _ in sent)
                if terminal == "close":
                    view.close()
            if terminal == "close":
                assert view.closed and not view.widget._scheduled_callbacks
                assert not any(message["op"] == "structure_data_chunk" for message, _ in sent)
                return
            deadline = asyncio.get_running_loop().time() + 2
            while transfer.state is TransferState.WAITING_BEGIN_ACK and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.001)
            assert transfer.state is TransferState.WAITING_CHUNK_ACK
            chunks = [(message, buffers) for message, buffers in sent if message["op"] == "structure_data_chunk"]
            assert len(chunks) == 1 and chunks[0][1]
            assert chunks[0][0]["generation"] == transfer.generation
            assert chunks[0][0].get("target_endpoint_id") == endpoint
            assert contexts == ["connector"]
            assert not view.widget._scheduled_callbacks

    asyncio.run(exercise())


def test_async_ownership_retry_keeps_the_callers_context():
    import time

    from molsysviewer.viewer.visual_capture import _capture_owned_call

    async def exercise():
        with msv.demo["dialanine"] as scene:
            entered, release = Event(), Event()
            scope = ContextVar("receiving_capture_scope", default="unset")
            scope.set("caller")

            def occupy():
                scope.set("foreign-owner")
                with scene._system_edits._locked():
                    entered.set()
                    assert release.wait(timeout=5)

            worker = Thread(target=occupy)
            worker.start()
            assert entered.wait(timeout=2)
            task = asyncio.create_task(_capture_owned_call(scene, scope.get, deadline=time.monotonic() + 5))
            try:
                await asyncio.sleep(0)
                assert not task.done()
                release.set()
                worker.join(timeout=2)
                assert await task == "caller"
            finally:
                release.set()
                worker.join(timeout=2)
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


def test_endpoint_close_precedes_capture_completion_queued_behind_the_same_edit():
    from molsysviewer.viewer.frontend_requests import FrontendRequestError

    async def exercise():
        with msv.demo["dialanine"] as view:
            view._ready = True
            view._endpoint_transfers.register("popup-review", "canvas")
            request = view._frontend_requests.begin(
                endpoint_id="popup-review", reply_event="visual_state_snapshot", revision="v1", timeout=5
            )
            errors = []

            def receive():
                try:
                    view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": "popup-review"})
                    view._handle_frontend_event(
                        {
                            "event": "visual_state_snapshot",
                            "request_id": request.request_id,
                            "capture_revision": "v1",
                            "_capture_endpoint_id": "popup-review",
                            "ok": True,
                            "snapshot": {"position": [10, 20, 30], "target": [0, 0, 0], "up": [0, 1, 0]},
                            "structure_index": 0,
                        }
                    )
                except Exception as error:
                    errors.append(error)

            with view._system_edits._locked():
                worker = Thread(target=receive)
                worker.start()
                worker.join(timeout=2)
                assert not worker.is_alive() and not errors
                assert not request.future.done()
            with pytest.raises(FrontendRequestError) as caught:
                await asyncio.wrap_future(request.future)
            assert caught.value.extra["reason"] == "endpoint_closed"

    asyncio.run(exercise())
