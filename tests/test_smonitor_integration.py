import pytest
import ast
from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.demo import demo
from molsysviewer._private.smonitor import CATALOG, PACKAGE_ROOT, META
from smonitor import get_manager
from smonitor.integrations import emit_from_catalog


def test_smonitor_catalog_emit():
    event = emit_from_catalog(
        CATALOG["viewer_init_failed"],
        package_root=PACKAGE_ROOT,
        meta=META,
        extra={"reason": "test", "message": "failed"},
    )
    assert event.get("code") == "MOLSYSVIEWER-VIEWER-INIT-FAILED"


def test_argument_error_message():
    exc = ArgumentError("selection", value="bad", caller="molsysviewer.test")
    assert str(exc)


def test_public_wrappers_emit_signal_timeline_entries(tmp_path):
    manager = get_manager()
    previous_profiling = manager.config.profiling
    previous_sample = manager.config.profiling_sample_rate
    previous_buffer = manager.config.profiling_buffer_size
    manager._timeline.clear()
    manager._timings.clear()
    manager.configure(profiling=True, profiling_sample_rate=1.0, profiling_buffer_size=64)

    try:
        view = demo["dialanine"]
        view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

        region = view.new_region(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
        region.hide(skip_digestion=True)
        view.whole.hide(skip_digestion=True)
        view.shapes.clear(skip_digestion=True)
        view.reset_camera(skip_digestion=True)
        view.get_camera_snapshot(skip_digestion=True)
        view.set_camera_snapshot({"target": [0, 0, 0]}, skip_digestion=True)
        view.export.html(str(tmp_path / "smonitor.html"), include_popout=False, skip_digestion=True)

        timeline = manager.report()["timeline"]
        keys = [entry["key"] for entry in timeline]
        tags_by_key = {entry["key"]: set(entry.get("tags", [])) for entry in timeline}
        meta_by_key = {entry["key"]: entry.get("meta", {}) for entry in timeline}

        assert "molsysviewer.regions.hide" in keys
        assert "molsysviewer.whole.hide" in keys
        assert "molsysviewer.shapes.clear" in keys
        assert "molsysviewer.viewer.reset_camera" in keys
        assert "molsysviewer.viewer.get_camera_snapshot" in keys
        assert "molsysviewer.viewer.set_camera_snapshot" in keys
        assert "molsysviewer.exports.html" in keys

        assert "region" in tags_by_key["molsysviewer.regions.hide"]
        assert "whole" in tags_by_key["molsysviewer.whole.hide"]
        assert "shape" in tags_by_key["molsysviewer.shapes.clear"]
        assert "camera" in tags_by_key["molsysviewer.viewer.reset_camera"]
        assert "export" in tags_by_key["molsysviewer.exports.html"]
        assert meta_by_key["molsysviewer.viewer.get_camera_snapshot"].get("pretty") is None
        assert meta_by_key["molsysviewer.viewer.set_camera_snapshot"].get("snapshot_keys") == ["target"]
        assert meta_by_key["molsysviewer.exports.html"].get("include_popout") is False
    finally:
        manager.configure(
            profiling=previous_profiling,
            profiling_sample_rate=previous_sample,
            profiling_buffer_size=previous_buffer,
        )


def test_public_digest_entrypoints_have_signal_decorators():
    targets = [
        Path("molsysviewer/viewer.py"),
        Path("molsysviewer/new_view.py"),
        Path("molsysviewer/whole.py"),
        Path("molsysviewer/regions.py"),
        Path("molsysviewer/layers.py"),
    ]
    targets.extend(sorted(Path("molsysviewer/shapes").glob("*.py")))

    missing: list[str] = []

    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                decorators = [ast.unparse(deco) for deco in node.decorator_list]
                if any("digest" in deco for deco in decorators) and not any("signal" in deco for deco in decorators):
                    missing.append(f"{path}:{node.name}")
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if not isinstance(item, ast.FunctionDef):
                        continue
                    decorators = [ast.unparse(deco) for deco in item.decorator_list]
                    if any("digest" in deco for deco in decorators) and not any("signal" in deco for deco in decorators):
                        missing.append(f"{path}:{node.name}.{item.name}")

    assert missing == []
