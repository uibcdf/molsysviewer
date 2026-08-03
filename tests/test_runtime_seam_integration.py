"""R1 seam integration: envelopes across the real MolSysView send/receive path.

Unlike test_runtime_router.py (the browser-independent authority unit), these
exercise the wiring: _handle_inbound_message dedup and MolSysViewerWidget.send
enveloping through an actual view.
"""

from __future__ import annotations

from unittest.mock import patch

import anywidget
import pytest

from molsysviewer import MolSysView


def _command_envelope(view, message_id, action="scene_history_coalescing_begin"):
    router = view._runtime_router  # noqa: SLF001
    return {
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": message_id,
        "direction": "command",
        "action": action,
        "payload": {"event": action},
    }


def test_a_duplicated_command_envelope_mutates_once_and_is_acked(monkeypatch):
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]

    applied: list = []
    real_handler = view._handle_frontend_event  # noqa: SLF001

    def spy(content):
        applied.append(content)
        return real_handler(content)

    monkeypatch.setattr(view, "_handle_frontend_event", spy)

    envelope = _command_envelope(view, "cmd-1")
    view._handle_inbound_message(envelope)          # noqa: SLF001
    view._handle_inbound_message(dict(envelope))    # noqa: SLF001  same messageId

    # The mutation runs exactly once despite two deliveries...
    assert len(applied) == 1
    # ...with exactly the domain message the handler expected before envelopes.
    assert applied[0] == {"event": "scene_history_coalescing_begin"}
    # ...and the duplicate produced an observable ack instead of re-applying.
    acks = [m for m in sent if m.get("action") == "command_duplicate_ack"]
    assert len(acks) == 1
    assert acks[0]["correlationId"] == "cmd-1"


def test_the_widget_connector_envelopes_control_messages_on_the_wire():
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    # Capture BELOW the widget's enveloping (the anywidget base send), so we see
    # exactly what reaches the wire after MolSysViewerWidget.send wraps it.
    with patch.object(anywidget.AnyWidget, "send") as base_send:
        view._send_widget_message({"op": "set_region_summaries", "summaries": []})  # noqa: SLF001

    assert base_send.call_count == 1
    envelope = base_send.call_args.args[0]
    assert envelope["direction"] == "projection"
    assert envelope["action"] == "set_region_summaries"
    assert envelope["payload"] == {"op": "set_region_summaries", "summaries": []}
    assert envelope["endpointId"] == f"python:{view._binary_viewer_id}"  # noqa: SLF001


def test_a_popup_snapshot_request_is_answered_with_a_correlated_projection():
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]

    router = view._runtime_router  # noqa: SLF001
    request = {
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": "req-7",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {
            "event": "request_popup_scene_snapshot",
            "mode": "panel",
            "popup_endpoint_id": "panel-popup-42",
        },
    }
    view._handle_inbound_message(request)  # noqa: SLF001

    assert len(sent) == 1
    answer = sent[0]
    assert answer["direction"] == "projection"
    assert answer["correlationId"] == "req-7"          # correlated to the request
    assert answer["targetEndpointId"] == router.widget_host_endpoint
    assert answer["action"] == "popup_scene_snapshot"
    body = answer["payload"]
    assert body["event"] == answer["action"]           # coherence guard
    assert body["popup_endpoint_id"] == "panel-popup-42"
    ops = {m.get("op") for m in body["messages"]}
    assert "set_region_summaries" in ops               # a panel projection
    assert "load_molsys_payload" not in ops            # and no molecular data


def test_an_invalid_popup_snapshot_mode_answers_nothing():
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]
    router = view._runtime_router  # noqa: SLF001
    view._handle_inbound_message({  # noqa: SLF001
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": "req-8",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {"event": "request_popup_scene_snapshot", "mode": "bogus"},
    })
    assert sent == []


@pytest.mark.parametrize(
    ("action", "payload", "catalog_key"),
    [
        (
            "camera_stranded_inside_scene",
            {
                "event": "camera_stranded_inside_scene",
                "distance": 2.0,
                "scene_radius": 10.0,
                "after": "load",
            },
            "camera_stranded_inside_scene",
        ),
        (
            "runtime_contract_rejected",
            {
                "event": "runtime_contract_rejected",
                "seam": "widget-inbound",
                "reason": "session-mismatch",
                "detail": "other-session",
            },
            "runtime_contract_rejected",
        ),
    ],
)
def test_frontend_transport_diagnostics_cross_the_envelope_and_reach_smonitor(
    monkeypatch,
    action,
    payload,
    catalog_key,
):
    import molsysviewer.viewer.core as core_module

    view = MolSysView()
    emitted: list[tuple[dict, dict]] = []
    monkeypatch.setattr(
        core_module,
        "emit_from_catalog",
        lambda catalog, **kwargs: emitted.append((catalog, kwargs)),
    )
    router = view._runtime_router  # noqa: SLF001
    view._handle_inbound_message({  # noqa: SLF001
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": f"diagnostic-{action}",
        "direction": "error",
        "action": action,
        "payload": payload,
    })

    assert len(emitted) == 1
    assert emitted[0][0] is core_module.CATALOG[catalog_key]


def test_raw_and_data_plane_messages_reach_the_wire_unwrapped():
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    with patch.object(anywidget.AnyWidget, "send") as base_send:
        # data-plane op with buffers, and a raw bootstrap op
        view._send_widget_message({"op": "structure_data_begin", "generation": 1}, buffers=[b"x"])  # noqa: SLF001
        view._send_widget_message({"op": "widget_runtime_source", "source": "..."})  # noqa: SLF001

    first = base_send.call_args_list[0].args[0]
    second = base_send.call_args_list[1].args[0]
    assert first == {"op": "structure_data_begin", "generation": 1}  # unwrapped
    assert base_send.call_args_list[0].kwargs.get("buffers") == [b"x"]  # buffers preserved
    assert second == {"op": "widget_runtime_source", "source": "..."}  # bootstrap raw


def test_a_canvas_popup_snapshot_streams_the_molecular_generation_to_its_endpoint(
    complete_structure_stream,
):
    """D4: the canvas popup gets typed buffers addressed to it, not JSON."""
    import molsysmt as msm

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append((content, buffers))  # type: ignore[assignment]

    router = view._runtime_router  # noqa: SLF001
    view._handle_inbound_message({  # noqa: SLF001
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": "req-canvas",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {
            "event": "request_popup_scene_snapshot",
            "mode": "canvas",
            "popup_endpoint_id": "canvas-popup-7",
        },
    })

    # The binary stream begins, addressed to the popup endpoint so the host
    # relays it instead of consuming it.
    begins = [m for m, _ in sent if m.get("op") == "structure_data_begin"]
    assert len(begins) == 1
    assert begins[0]["target_endpoint_id"] == "canvas-popup-7"

    # ...and the snapshot does not overtake it. The popup builds its structure
    # from the last chunk, so a scene projection that arrived first would be
    # applied against an empty canvas and silently dropped — the same defect a
    # human hit on the host path on 2026-07-31.
    assert not [m for m, _ in sent if m.get("action") == "popup_scene_snapshot"], (
        "the scene must not be projected before the popup has a structure"
    )

    complete_structure_stream(view, target_endpoint_id="canvas-popup-7")

    # The snapshot answer therefore carries no JSON molecular copy.
    answers = [m for m, _ in sent if m.get("action") == "popup_scene_snapshot"]
    assert len(answers) == 1
    ops = {msg.get("op") for msg in answers[0]["payload"]["messages"]}
    assert "load_molsys_payload" not in ops, "the molecular generation must not be duplicated as JSON"
    # The whole here is pristine, so its representation op is deliberately
    # withheld (projecting an explicit None would blank the popup). Visibility
    # still travels, which is what proves the rest of the scene is projected.
    assert "show_whole" in ops, "the rest of the scene is still projected"


def test_a_popup_targeted_stream_fallback_cancels_and_loads_the_same_endpoint():
    import molsysmt as msm

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    sent: list[tuple[dict, list]] = []
    view.widget.send = lambda content, buffers=None: sent.append((content, list(buffers or [])))  # type: ignore[assignment]

    assert view._try_send_array_native_molsys(  # noqa: SLF001
        view._current_molecular_projection,  # noqa: SLF001
        target_endpoint_id="canvas-popup-7",
    )
    sent.clear()

    with pytest.warns(RuntimeWarning, match="using JSON fallback"):
        view._fallback_binary_structure_stream(  # noqa: SLF001
            "forced test fallback",
            target_endpoint_id="canvas-popup-7",
        )

    cancel = next(message for message, _ in sent if message.get("op") == "structure_data_cancel")
    fallback = next(message for message, _ in sent if message.get("op") == "load_molsys_payload")
    assert cancel["target_endpoint_id"] == "canvas-popup-7"
    assert fallback["target_endpoint_id"] == "canvas-popup-7"


def test_a_failed_stream_cancel_is_reported_without_masking_the_json_fallback(monkeypatch):
    import molsysmt as msm
    import molsysviewer.viewer.core as core_module

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    sent: list[dict] = []

    def transmit(message, buffers=None):
        if message.get("op") == "structure_data_cancel":
            raise OSError("cancel wire failed")
        sent.append(dict(message))

    view.widget.send = transmit  # type: ignore[assignment]
    assert view._try_send_array_native_molsys(  # noqa: SLF001
        view._current_molecular_projection,  # noqa: SLF001
        target_endpoint_id="canvas-popup-7",
    )
    diagnostics: list[tuple[tuple, dict]] = []
    monkeypatch.setattr(
        core_module,
        "emit_suppressed_exception",
        lambda *args, **kwargs: diagnostics.append((args, kwargs)),
    )

    with pytest.warns(RuntimeWarning, match="using JSON fallback"):
        view._fallback_binary_structure_stream(  # noqa: SLF001
            "forced test fallback",
            target_endpoint_id="canvas-popup-7",
        )

    assert diagnostics
    assert diagnostics[0][0][0] == "MolSysView._fallback_binary_structure_stream.cancel"
    assert diagnostics[0][1]["context"]["target_endpoint_id"] == "canvas-popup-7"
    assert any(message.get("op") == "load_molsys_payload" for message in sent)


def test_a_panel_popup_snapshot_never_starts_a_molecular_stream():
    import molsysmt as msm

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append((content, buffers))  # type: ignore[assignment]
    router = view._runtime_router  # noqa: SLF001
    view._handle_inbound_message({  # noqa: SLF001
        "protocolVersion": 1,
        "viewerId": view._binary_viewer_id,  # noqa: SLF001
        "sessionId": view._binary_session_id,  # noqa: SLF001
        "endpointId": router.widget_host_endpoint,
        "targetEndpointId": router.python_endpoint,
        "messageId": "req-panel",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {
            "event": "request_popup_scene_snapshot",
            "mode": "panel",
            "popup_endpoint_id": "panel-popup-7",
        },
    })
    assert not [m for m, _ in sent if m.get("op") == "structure_data_begin"]


def test_popup_transfer_does_not_block_the_embedded_host_and_close_releases_it():
    import molsysmt as msm

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    sent: list[dict] = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]

    assert view._try_send_array_native_molsys(  # noqa: SLF001
        view._current_molecular_projection,  # noqa: SLF001
        target_endpoint_id="canvas-popup-7",
    )
    manager = view._structure_transfer_manager("canvas-popup-7")  # noqa: SLF001
    transfer = manager.active
    assert transfer is not None

    view._send_widget_message({"op": "set_region_summaries", "summaries": []})  # noqa: SLF001
    view._send_widget_message(  # noqa: SLF001
        {"op": "popup-only-scene"},
        defer_for_endpoint="canvas-popup-7",
    )
    assert any(message.get("op") == "set_region_summaries" for message in sent)
    assert not any(message.get("op") == "popup-only-scene" for message in sent)

    sent.clear()
    view._handle_frontend_event({  # noqa: SLF001
        "event": "popup_endpoint_closed",
        "mode": "canvas",
        "popup_endpoint_id": "canvas-popup-7",
    })

    assert transfer.release_count == 1
    assert transfer.payload is None
    assert view._structure_transfer_manager("canvas-popup-7") is None  # noqa: SLF001
    assert "canvas-popup-7" not in view._deferred_widget_messages  # noqa: SLF001
    assert not any(message.get("op") == "structure_data_cancel" for message in sent)
    assert not any(message.get("op") == "popup-only-scene" for message in sent)


@pytest.mark.parametrize("state", ["begin", "chunk", "completion_wait"])
def test_popup_close_releases_every_active_transfer_state(state):
    from molsysviewer.transport import AckDisposition

    view = MolSysView()
    endpoint_id = "canvas-popup-close"
    manager = view._structure_transfer_manager(endpoint_id, create=True)  # noqa: SLF001
    transfer = manager.start(
        begin_message={"op": "structure_data_begin", "chunk_count": 1},
        chunks=[(
            {"op": "structure_data_chunk", "chunk_id": 0},
            [memoryview(b"coordinates")],
        )],
        fallback_factory=lambda _generation: {"op": "load_molsys_payload"},
        payload=object(),
        target_endpoint_id=endpoint_id,
    )
    identity = {
        "viewer_id": transfer.viewer_id,
        "session_id": transfer.session_id,
        "stream_id": transfer.stream_id,
        "generation": transfer.generation,
        "target_endpoint_id": endpoint_id,
    }
    if state in {"chunk", "completion_wait"}:
        result = manager.handle_event({"event": "structure_data_begin_ack", **identity})
        assert result.disposition is AckDisposition.SEND_CHUNK
    if state == "completion_wait":
        result = manager.handle_event({
            "event": "structure_data_chunk_ack",
            "chunk_id": 0,
            **identity,
        })
        assert result.disposition is AckDisposition.WAIT_COMPLETE

    view._handle_frontend_event({  # noqa: SLF001
        "event": "popup_endpoint_closed",
        "mode": "canvas",
        "popup_endpoint_id": endpoint_id,
    })

    assert transfer.release_count == 1
    assert transfer.payload is None
    assert view._structure_transfer_manager(endpoint_id) is None  # noqa: SLF001


def test_live_molecular_reload_starts_independent_host_and_canvas_generations(
    complete_structure_stream,
):
    import molsysmt as msm

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": 16 * 1024 * 1024,
    }
    view._popup_endpoint_modes["canvas-popup-live"] = "canvas"  # noqa: SLF001
    view._popup_endpoint_modes["panel-popup-live"] = "panel"  # noqa: SLF001
    sent: list[dict] = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]

    view._deliver_transport_message(view._current_molecular_projection)  # noqa: SLF001

    begins = [message for message in sent if message.get("op") == "structure_data_begin"]
    assert len(begins) == 2
    assert {message.get("target_endpoint_id") for message in begins} == {
        None,
        "canvas-popup-live",
    }
    assert not any(
        message.get("target_endpoint_id") == "panel-popup-live" for message in begins
    )

    complete_structure_stream(view)
    assert view._structure_transfer_manager("canvas-popup-live").has_active  # noqa: SLF001
    complete_structure_stream(view, target_endpoint_id="canvas-popup-live")
    assert not view._structure_transfers.has_active  # noqa: SLF001
    assert view._structure_transfer_manager("canvas-popup-live") is None  # noqa: SLF001
