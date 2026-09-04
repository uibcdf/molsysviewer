"""RRS0 remote connector seam through a real MolSysView."""

from __future__ import annotations

import base64

import pytest
from molsysviewer.demo import demo
from molsysviewer.remote import RemoteViewChannel
from molsysviewer.viewer import MolSysView


def make_channel(render_on="server"):
    control = []
    data = []
    channel = RemoteViewChannel(
        control.append,
        render_on=render_on,
        send_data=lambda message, buffers: data.append((message, buffers)),
    )
    return channel, control, data


def register_browser(channel: RemoteViewChannel) -> str:
    endpoint_id = "browser-client:test"
    capabilities = {"command-origin", "input-send", "workbench"}
    if channel.render_on == "client":
        capabilities.update({"render", "structure-receive"})
    else:
        capabilities.add("video-receive")
    channel.router.register_endpoint(
        endpoint_id,
        "browser-client",
        capabilities,
        actor_id="human:test",
        actor_kind="human",
    )
    return endpoint_id


def register_worker(channel: RemoteViewChannel) -> str:
    endpoint_id = "render-worker:test"
    channel.router.register_endpoint(
        endpoint_id,
        "render-worker",
        {"input-receive", "render", "structure-receive", "video-send"},
        actor_id=endpoint_id,
        actor_kind="system",
    )
    return endpoint_id


def command(channel: RemoteViewChannel, endpoint_id: str, message_id="command-1") -> dict:
    return {
        "protocolVersion": 1,
        "viewerId": channel.router.viewer_id,
        "sessionId": channel.router.session_id,
        "endpointId": endpoint_id,
        "targetEndpointId": channel.router.python_endpoint,
        "messageId": message_id,
        "direction": "command",
        "action": "interaction_active_selection_changed",
        "payload": {
            "event": "interaction_active_selection_changed",
            "atom_indices": [0, 1, 2],
        },
        "actorId": "human:test",
        "actorKind": "human",
        "operationId": "selection-operation-1",
    }


def test_molsysview_binds_its_runtime_identity_to_remote_channel():
    channel, _control, _data = make_channel()
    view = MolSysView(transport=channel)
    try:
        assert channel.router.viewer_id == view._binary_viewer_id  # noqa: SLF001
        assert channel.router.session_id == view._binary_session_id  # noqa: SLF001
        assert channel.router.render_on == "server"
    finally:
        view.close()


def test_remote_command_crosses_real_view_seam_once_and_duplicate_is_acknowledged():
    channel, control, _data = make_channel()
    view = MolSysView(transport=channel)
    try:
        endpoint_id = register_browser(channel)
        view._ready = True  # noqa: SLF001 - exercise live remote projection fanout
        depth = len(view.history._undo)  # noqa: SLF001
        message = command(channel, endpoint_id)

        first = channel.receive_control(message)
        second = channel.receive_control(message)

        assert first.status == "accepted"
        assert second.status == "duplicate"
        assert sorted(view.active_selection.atom_indices) == [0, 1, 2]
        assert len(view.history._undo) == depth + 1  # noqa: SLF001
        duplicate_acks = [
            item for item in control
            if item.get("action") == "command_duplicate_ack"
        ]
        assert len(duplicate_acks) == 1
        assert duplicate_acks[0]["correlationId"] == "command-1"
        assert duplicate_acks[0]["targetEndpointId"] == endpoint_id
        assert duplicate_acks[0]["operationId"] == "selection-operation-1"
        selection_projections = [
            item for item in control if item.get("action") == "set_active_selection"
        ]
        assert len(selection_projections) == 1
        assert selection_projections[0]["payload"]["atom_indices"] == [0, 1, 2]
    finally:
        view.close()


def test_remote_channel_separates_control_envelopes_from_raw_binary_data():
    channel, control, data = make_channel(render_on="client")
    view = MolSysView(transport=channel)
    try:
        assert channel.supports_array_native_buffers is True
        projection = {"op": "set_region_summaries", "summaries": []}
        channel.send(projection)
        buffers = [memoryview(b"coordinates")]
        raw = {"event": "structure_data_chunk", "generation": 1}
        channel.send(raw, buffers=buffers)

        assert control[-1]["payload"] is projection
        assert control[-1]["direction"] == "projection"
        assert data[-1] == (raw, buffers)
    finally:
        view.close()


def test_remote_channel_refuses_to_drop_data_without_a_data_plane_sender():
    channel = RemoteViewChannel(lambda _message: None, render_on="server")
    view = MolSysView(transport=channel)
    try:
        with pytest.raises(NotImplementedError, match="refusing to drop"):
            channel.send(
                {"event": "structure_data_chunk", "generation": 1},
                buffers=[memoryview(b"coordinates")],
            )
    finally:
        view.close()


def test_closed_remote_channel_rejects_new_inbound_messages():
    channel, _control, _data = make_channel()
    view = MolSysView(transport=channel)
    endpoint_id = register_browser(channel)
    channel.close()

    result = channel.receive_control(command(channel, endpoint_id))
    assert result.status == "rejected"
    assert result.reason == "channel-closed"
    view.close()


def test_remote_channel_accepts_authenticated_raw_and_array_native_events():
    channel, _control, _data = make_channel()
    view = MolSysView(transport=channel)
    try:
        endpoint_id = register_worker(channel)

        ready = channel.receive_data(
            {"event": "ready", "capabilities": {"binary_structure_data": [1]}},
            source_endpoint_id=endpoint_id,
        )
        foreign = channel.receive_data(
            {
                "event": "structure_data_begin_ack",
                "viewer_id": "another-viewer",
                "session_id": channel.router.session_id,
            },
            source_endpoint_id=endpoint_id,
        )

        assert ready.status == "accepted"
        assert view._ready is True  # noqa: SLF001
        assert foreign.status == "rejected"
        assert foreign.reason == "viewer-mismatch"
    finally:
        view.close()


def test_remote_channel_rejects_data_from_unregistered_endpoint_or_control_action():
    channel, _control, _data = make_channel()
    view = MolSysView(transport=channel)
    try:
        unknown = channel.receive_data(
            {"event": "ready"}, source_endpoint_id="render-worker:unknown"
        )
        endpoint_id = register_worker(channel)
        wrong_plane = channel.receive_data(
            {"event": "interaction_click"}, source_endpoint_id=endpoint_id
        )

        assert unknown.status == "rejected"
        assert unknown.reason == "unknown-source"
        assert wrong_plane.status == "rejected"
        assert wrong_plane.reason == "unknown-data-action"
    finally:
        view.close()


def test_remote_png_download_routes_worker_artifact_to_the_human_client():
    channel, control, _data = make_channel()
    view = MolSysView(transport=channel)
    source = demo["pentalanine"]
    published = []
    try:
        view.load(source.molsys, skip_digestion=True)
        browser = register_browser(channel)
        worker = register_worker(channel)
        channel.download_publisher = lambda filename, media_type, data: (
            published.append((filename, media_type, data)) or "/session/download/artifact"
        )
        view._ready = True  # noqa: SLF001
        control.clear()

        inbound = {
            "protocolVersion": 1,
            "viewerId": channel.router.viewer_id,
            "sessionId": channel.router.session_id,
            "endpointId": browser,
            "targetEndpointId": channel.router.python_endpoint,
            "messageId": "download-command-1",
            "direction": "command",
            "action": "interaction_context_action",
            "payload": {
                "event": "interaction_context_action",
                "action": "download_image",
            },
            "actorId": "human:test",
            "actorKind": "human",
        }
        assert channel.receive_control(inbound).status == "accepted"
        request = control[-1]
        assert request["action"] == "request_image_export"
        assert request["targetEndpointId"] == worker
        request_id = request["payload"]["request_id"]

        png = b"\x89PNG\r\n\x1a\nremote-image"
        result = {
            "protocolVersion": 1,
            "viewerId": channel.router.viewer_id,
            "sessionId": channel.router.session_id,
            "endpointId": worker,
            "targetEndpointId": channel.router.python_endpoint,
            "messageId": "worker-image-1",
            "direction": "ack",
            "action": "image_export",
            "payload": {
                "event": "image_export",
                "request_id": request_id,
                "success": True,
                "data_uri": "data:image/png;base64," + base64.b64encode(png).decode(),
            },
            "actorId": worker,
            "actorKind": "system",
        }
        assert channel.receive_control(result).status == "accepted"

        assert published == [("molsysviewer.png", "image/png", png)]
        ready = control[-1]
        assert ready["action"] == "remote_download_ready"
        assert ready["targetEndpointId"] == browser
        assert ready["payload"]["url"] == "/session/download/artifact"
    finally:
        view.close()
        source.close()
