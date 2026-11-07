from __future__ import annotations

import ast
from pathlib import Path

from molsysviewer import MolSysView, demo

ROOT = Path(__file__).parents[1]
VIEWER_PACKAGE = ROOT / "molsysviewer" / "viewer"


def test_core_has_no_parallel_endpoint_lifecycle_containers():
    path = VIEWER_PACKAGE / "core.py"
    tree = ast.parse(path.read_text(), filename=str(path))

    forbidden = {
        "_popup_structure_transfers",
        "_popup_endpoint_modes",
        "_deferred_widget_messages",
        "_flushing_deferred_widget_messages",
    }
    present = sorted(
        {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr in forbidden}
    )
    assert not present, f"endpoint lifecycle state escaped EndpointTransferRegistry: {present}"


def test_static_export_snapshot_has_one_constructor():
    definitions: list[Path] = []
    for path in VIEWER_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_build_static_export_snapshot"
            for node in ast.walk(tree)
        ):
            definitions.append(path)

    assert definitions == [VIEWER_PACKAGE / "popup_snapshot.py"]


def test_closing_one_endpoint_removes_its_complete_bundle_only():
    view = MolSysView()
    canvas_id = "canvas-popup"
    panel_id = "panel-popup"
    registry = view._endpoint_transfers  # noqa: SLF001

    registry.register(canvas_id, "canvas")
    registry.register(panel_id, "panel")
    canvas_manager = registry.manager(canvas_id, create=True)
    registry.defer(canvas_id, {"op": "canvas-scene"}, None)
    registry.defer(panel_id, {"op": "panel-scene"}, None)

    removed = registry.close(panel_id)

    assert removed is not None
    assert removed.mode == "panel"
    assert [message[0]["op"] for message in removed.deferred] == ["panel-scene"]
    canvas = registry.state(canvas_id)
    assert canvas is not None
    assert canvas.manager is canvas_manager
    assert canvas.mode == "canvas"
    assert [message[0]["op"] for message in canvas.deferred] == ["canvas-scene"]
    view.close()


def test_scene_ops_have_each_renderers_order_and_wait_for_its_own_structure():
    """A fast popup must not load first and later receive the host's clear."""
    with demo["pentalanine"] as seed, seed.extract(structure_indices=[0, 8, 3]) as view:
        view._ready = True
        view._frontend_capabilities = {"binary_structure_data": [1], "max_buffer_bytes": 16 * 1024 * 1024}
        endpoint = "canvas-owner"
        host = f"widget-host:{view._binary_session_id}"
        view._endpoint_transfers.register(endpoint, "canvas")
        sent = []
        view.widget.send = lambda message, buffers=None: sent.append(dict(message))
        view._send({"op": "clear_all", "awaiting_structure": True})
        assert [
            (message["op"], message.get("target_endpoint_id")) for message in sent if message["op"] == "clear_all"
        ] == [
            ("clear_all", host),
            ("clear_all", endpoint),
        ]
        view._deliver_transport_message(view._current_molecular_projection)
        begins = [message for message in sent if message["op"] == "structure_data_begin"]
        assert len(begins) == 2
        view._send_runtime_only({"op": "set_trajectory_frame", "index": 2})
        assert not any(message["op"] == "set_trajectory_frame" for message in sent)

        def complete(begin):
            identity = {key: begin[key] for key in ("viewer_id", "session_id", "stream_id", "generation")}
            if begin.get("target_endpoint_id"):
                identity["target_endpoint_id"] = begin["target_endpoint_id"]
            view._handle_frontend_event({"event": "structure_data_begin_ack", **identity})
            for chunk in [
                message
                for message in sent
                if message["op"] == "structure_data_chunk" and message["stream_id"] == begin["stream_id"]
            ]:
                view._handle_frontend_event(
                    {"event": "structure_data_chunk_ack", "chunk_id": chunk["chunk_id"], **identity}
                )
            view._handle_frontend_event({"event": "structure_data_complete", **identity})

        # Deliberately complete the popup first; its following scene work must
        # not depend on the primary renderer's processing speed or ack.
        complete(next(begin for begin in begins if begin.get("target_endpoint_id") == endpoint))
        frames = [message for message in sent if message["op"] == "set_trajectory_frame"]
        assert frames == [{"op": "set_trajectory_frame", "index": 2, "target_endpoint_id": endpoint}]
        complete(next(begin for begin in begins if begin.get("target_endpoint_id") is None))
        frames = [message for message in sent if message["op"] == "set_trajectory_frame"]
        assert frames == [
            {"op": "set_trajectory_frame", "index": 2, "target_endpoint_id": endpoint},
            {"op": "set_trajectory_frame", "index": 2, "target_endpoint_id": host},
        ]


def test_json_projection_is_sent_once_to_each_canvas_without_primary_fanout():
    with demo["dialanine"] as view:
        view._ready = True
        view._frontend_capabilities = {}
        view._endpoint_transfers.register("canvas-owner", "canvas")
        view._endpoint_transfers.register("panel-owner", "panel")
        sent = []
        view.widget.send = lambda message, buffers=None: sent.append(dict(message))
        view._deliver_transport_message(view._current_molecular_projection)
        assert [message["target_endpoint_id"] for message in sent] == [
            f"widget-host:{view._binary_session_id}",
            "canvas-owner",
        ]
        assert all(message["op"] == "load_molsys_payload" for message in sent)
