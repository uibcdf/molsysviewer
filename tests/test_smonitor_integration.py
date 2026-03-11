import pytest

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
        view.write_html(str(tmp_path / "smonitor.html"), include_popout=False, skip_digestion=True)

        timeline = manager.report()["timeline"]
        keys = [entry["key"] for entry in timeline]
        tags_by_key = {entry["key"]: set(entry.get("tags", [])) for entry in timeline}

        assert "molsysviewer.regions.hide" in keys
        assert "molsysviewer.whole.hide" in keys
        assert "molsysviewer.shapes.clear" in keys
        assert "molsysviewer.viewer.reset_camera" in keys
        assert "molsysviewer.viewer.get_camera_snapshot" in keys
        assert "molsysviewer.viewer.set_camera_snapshot" in keys
        assert "molsysviewer.viewer.write_html" in keys

        assert "region" in tags_by_key["molsysviewer.regions.hide"]
        assert "whole" in tags_by_key["molsysviewer.whole.hide"]
        assert "shape" in tags_by_key["molsysviewer.shapes.clear"]
        assert "camera" in tags_by_key["molsysviewer.viewer.reset_camera"]
        assert "export" in tags_by_key["molsysviewer.viewer.write_html"]
    finally:
        manager.configure(
            profiling=previous_profiling,
            profiling_sample_rate=previous_sample,
            profiling_buffer_size=previous_buffer,
        )
