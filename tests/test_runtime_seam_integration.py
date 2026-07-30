"""R1 seam integration: envelopes across the real MolSysView send/receive path.

Unlike test_runtime_router.py (the browser-independent authority unit), these
exercise the wiring: _handle_inbound_message dedup and MolSysViewerWidget.send
enveloping through an actual view.
"""

from __future__ import annotations

from unittest.mock import patch

import anywidget

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


def test_a_canvas_popup_snapshot_streams_the_molecular_generation_to_its_endpoint():
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

    # The snapshot answer therefore carries no JSON molecular copy.
    answers = [m for m, _ in sent if m.get("action") == "popup_scene_snapshot"]
    assert len(answers) == 1
    ops = {msg.get("op") for msg in answers[0]["payload"]["messages"]}
    assert "load_molsys_payload" not in ops, "the molecular generation must not be duplicated as JSON"
    assert "set_whole_representation" in ops, "the rest of the scene is still projected"


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
