from __future__ import annotations

import pytest

from molsysviewer.demo import demo
from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys
import molsysviewer.viewer.core as viewer_core


def _capture_widget_send(view):
    sent: list[tuple[dict, list[memoryview]]] = []

    def send(message, buffers=None):
        sent.append((dict(message), list(buffers or [])))

    view.widget.send = send  # type: ignore[method-assign]
    return sent


def test_anywidget_binary_capability_never_builds_the_json_fallback(monkeypatch):
    view = demo["dialanine"]
    json_builds: list[int] = []
    original_build = viewer_core.build_json_molsys_message

    def recording_build(*args, **kwargs):
        json_builds.append(1)
        return original_build(*args, **kwargs)

    monkeypatch.setattr(viewer_core, "build_json_molsys_message", recording_build)
    sent = _capture_widget_send(view)
    recorded_load = next(
        message
        for message in view._test_message_log  # noqa: SLF001
        if message.get("op") == "load_molsys_payload"
    )

    view._handle_frontend_event({  # noqa: SLF001
        "event": "ready",
        "capabilities": {
            "binary_structure_data": [1],
            "max_buffer_bytes": 16 * 1024 * 1024,
        },
    })

    begin, begin_buffers = next(
        item for item in sent if item[0].get("op") == "structure_data_begin"
    )
    assert begin["metadata"]["n_atoms"] == view.molsys.get_n_atoms()
    assert begin["metadata"]["n_structures"] == view.molsys.structures.n_structures
    assert view.widget.runtime_viewer_id == begin["viewer_id"]
    assert view.widget.runtime_session_id == begin["session_id"]
    assert begin_buffers == []
    assert not any(message.get("op") == "structure_data_chunk" for message, _ in sent)

    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_begin_ack",
        "viewer_id": begin["viewer_id"],
        "session_id": begin["session_id"],
        "stream_id": begin["stream_id"],
        "generation": begin["generation"],
    })
    binary_message, buffers = next(
        item for item in sent if item[0].get("op") == "structure_data_chunk"
    )
    assert binary_message["structure_count"] == view.molsys.structures.n_structures
    assert buffers
    assert all(buffer.format == "B" and buffer.contiguous for buffer in buffers)
    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_chunk_ack",
        "viewer_id": begin["viewer_id"],
        "session_id": begin["session_id"],
        "stream_id": begin["stream_id"],
        "generation": begin["generation"],
        "chunk_id": binary_message["chunk_id"],
    })
    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_complete",
        "viewer_id": begin["viewer_id"],
        "session_id": begin["session_id"],
        "stream_id": begin["stream_id"],
        "generation": begin["generation"],
    })
    assert json_builds == []
    assert not recorded_load.is_materialized
    assert recorded_load in view._test_message_log  # noqa: SLF001
    assert all(
        message.get("op") not in {"structure_data_begin", "structure_data_chunk"}
        for message in view._test_message_log  # noqa: SLF001
    )
    view.close()


def test_anywidget_without_binary_capability_builds_json_once(monkeypatch):
    view = demo["dialanine"]
    json_builds: list[int] = []
    original_build = viewer_core.build_json_molsys_message

    def recording_build(*args, **kwargs):
        json_builds.append(1)
        return original_build(*args, **kwargs)

    monkeypatch.setattr(viewer_core, "build_json_molsys_message", recording_build)
    sent = _capture_widget_send(view)

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    assert any(message.get("op") == "load_molsys_payload" for message, _ in sent)
    assert all(message.get("op") != "structure_data_begin" for message, _ in sent)
    assert json_builds == [1]
    view.close()


def test_anywidget_binary_transport_limit_keeps_oversized_payload_on_json_fallback():
    view = demo["dialanine"]
    sent = _capture_widget_send(view)

    view._handle_frontend_event({  # noqa: SLF001
        "event": "ready",
        "capabilities": {
            "binary_structure_data": [1],
            "max_buffer_bytes": 1,
        },
    })

    assert any(message.get("op") == "load_molsys_payload" for message, _ in sent)
    assert all(message.get("op") != "structure_data_begin" for message, _ in sent)
    view.close()


def test_anywidget_stream_sends_one_bounded_chunk_per_ack_and_releases_on_completion():
    view = demo["dialanine"]
    molsys = view.molsys
    one_structure = molsys.structures.copy()
    for _ in range(4):
        molsys.structures.append_structures(one_structure, skip_digestion=True)
    payload = serialize_array_native_molsys(molsys)
    bytes_per_structure = payload.arrays[0].nbytes // 5
    sent = _capture_widget_send(view)
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = {  # noqa: SLF001
        "binary_structure_data": [1],
        "max_buffer_bytes": bytes_per_structure * 2,
    }
    recorded_load = next(
        message
        for message in view._test_message_log  # noqa: SLF001
        if message.get("op") == "load_molsys_payload"
    )
    view._deliver_transport_message(recorded_load)  # noqa: SLF001
    begin = next(message for message, _ in sent if message["op"] == "structure_data_begin")
    assert begin["chunk_count"] == 3

    identity = {
        "viewer_id": begin["viewer_id"],
        "session_id": begin["session_id"],
        "stream_id": begin["stream_id"],
        "generation": begin["generation"],
    }
    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_begin_ack",
        **identity,
    })
    assert [message["chunk_id"] for message, _ in sent if message["op"] == "structure_data_chunk"] == [0]

    for chunk_id in range(3):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "structure_data_chunk_ack",
            "chunk_id": chunk_id,
            **identity,
        })
        chunk_ids = [
            message["chunk_id"]
            for message, _ in sent
            if message["op"] == "structure_data_chunk"
        ]
        assert chunk_ids == list(range(min(chunk_id + 2, 3)))

    assert view._structure_transfer_manager(None).active is not None  # noqa: SLF001
    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_complete",
        **identity,
    })
    assert view._structure_transfer_manager(None).active is None  # noqa: SLF001
    view.close()


def test_anywidget_stream_rejects_foreign_ack_without_advancing():
    view = demo["dialanine"]
    sent = _capture_widget_send(view)
    view._handle_frontend_event({  # noqa: SLF001
        "event": "ready",
        "capabilities": {
            "binary_structure_data": [1],
            "max_buffer_bytes": 16 * 1024 * 1024,
        },
    })
    begin = next(message for message, _ in sent if message["op"] == "structure_data_begin")

    with pytest.warns(RuntimeWarning, match="another endpoint or generation"):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "structure_data_begin_ack",
            "viewer_id": "another-view",
            "session_id": begin["session_id"],
            "stream_id": begin["stream_id"],
            "generation": begin["generation"],
        })

    assert not any(message.get("op") == "structure_data_chunk" for message, _ in sent)
    view.close()


def test_anywidget_stream_connector_failure_releases_buffers_and_falls_back_to_json():
    view = demo["dialanine"]
    sent: list[dict] = []

    def send(message, buffers=None):
        if message.get("op") == "structure_data_chunk":
            raise OSError("comm closed")
        sent.append(dict(message))

    view.widget.send = send  # type: ignore[method-assign]
    view._handle_frontend_event({  # noqa: SLF001
        "event": "ready",
        "capabilities": {
            "binary_structure_data": [1],
            "max_buffer_bytes": 16 * 1024 * 1024,
        },
    })
    begin = next(message for message in sent if message["op"] == "structure_data_begin")

    with pytest.warns(RuntimeWarning, match="connector failed while sending chunk"):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "structure_data_begin_ack",
            "viewer_id": begin["viewer_id"],
            "session_id": begin["session_id"],
            "stream_id": begin["stream_id"],
            "generation": begin["generation"],
        })

    assert view._structure_transfer_manager(None).active is None  # noqa: SLF001
    assert any(message.get("op") == "load_molsys_payload" for message in sent)
    view.close()
