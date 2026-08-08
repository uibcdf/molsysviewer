from __future__ import annotations

import ast
from pathlib import Path

from molsysviewer import MolSysView


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
    present = sorted({
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in forbidden
    })
    assert not present, (
        "endpoint lifecycle state escaped EndpointTransferRegistry: "
        f"{present}"
    )


def test_static_export_snapshot_has_one_constructor():
    definitions: list[Path] = []
    for path in VIEWER_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_build_static_export_snapshot"
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
