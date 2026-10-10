"""Studio persists real molecular work through the public owners (#223–#225)."""

import json
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.interactions import _to_plain
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with msv.new_view(source.molsys, structure_indices=[0, 8, 3]) as scene:
            yield scene


def request(view, action, path, *, kind="state", **details):
    dispatch_panel_action(
        view, {"action": action, "path": str(path), "file_kind": kind, "request_id": "file-review", **details}
    )


def test_coordinate_annotation_focus_uses_live_owner_and_rejects_missing_tag(view):
    annotation = view.annotations.add("site", position="[1, 2, 3] nm", tag="site")
    view.active_selection.set([4, 5])
    annotation.focus()
    expected = deepcopy(view._test_message_log[-1])
    dispatch_panel_action(view, {"action": "focus_annotation", "tag": "site"})
    assert view._test_message_log[-1] == expected
    assert view.active_selection.atom_indices == [4, 5]
    before = view.export_state()
    with pytest.raises(ValueError, match="No annotation"):
        dispatch_panel_action(view, {"action": "focus_annotation", "tag": "missing"})
    assert view.export_state() == before


def test_state_file_roundtrip_restores_scene_frame_and_camera_on_same_system(view, tmp_path):
    view.annotations.add("absolute", position="[1, 2, 3] nm", tag="site")
    view.regions.add(atom_indices=[0, 1], tag="region")
    view.player.go_to_structure(2)
    view.camera.set_snapshot({"position": [10.0, 20.0, 30.0]})
    molsys = view.molsys
    path = tmp_path / "review.json"
    request(view, "save_work_file", path)
    assert json.loads(path.read_text())["annotations"]
    view.annotations.delete("site")
    view.player.go_to_structure(0)
    request(view, "restore_work_file", path, confirmed=True)
    assert view.molsys is molsys
    assert view.annotations.tags() == ["site"]
    assert view.regions.tags() == ["region"]
    assert view.player.index == 2
    assert view.camera.get_snapshot() == {"position": [10.0, 20.0, 30.0]}
    assert not view.history.can_undo() and not view.history.can_redo()


def test_session_file_roundtrip_replaces_system_and_preserves_analysis(view, tmp_path):
    view.interactions.hbonds.get_buch_hbonds(name="science", structure_indices="all", distance_threshold="0.4 nm")
    view.interactions.add("science", tag="visual")
    view.annotations.add("absolute", position="[1, 2, 3] nm", tag="site")
    view.player.go_to_structure(2)
    coordinates = msm.get(view.molsys, coordinates=True)
    analysis = view.molsys.interactions["science"].to_dict()
    path = tmp_path / "review.msv"
    request(view, "save_work_file", path, kind="session")
    with msv.demo["dialanine"] as other:
        view.load(other.molsys, mode="replace")
    widget = view.widget
    request(view, "restore_work_file", path, kind="session", confirmed=True)
    assert view.widget is widget
    assert view.annotations.tags() == ["site"]
    assert view.interactions.tags() == ["visual"]
    assert view.player.index == 2 and view.player.n_structures == 3
    np.testing.assert_array_equal(
        puw.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm"),
        puw.get_value(coordinates, to_unit="nm"),
    )
    restored = view.molsys.interactions["science"].to_dict()
    assert _to_plain(restored) == _to_plain(analysis)
    assert not view.history.can_undo() and not view.history.can_redo()


@pytest.mark.parametrize("kind", ["state", "session"])
def test_overwrite_requires_explicit_declaration(view, tmp_path, kind):
    path = tmp_path / "already-there"
    path.write_text("keep these bytes")
    with pytest.raises(ValueError, match="already exists"):
        request(view, "save_work_file", path, kind=kind)
    assert path.read_text() == "keep these bytes"
    request(view, "save_work_file", path, kind=kind, overwrite=True)
    assert path.read_bytes() != b"keep these bytes"


@pytest.mark.parametrize("kind", ["state", "session"])
def test_restore_confirmation_and_corrupt_file_preserve_current_scene(view, tmp_path, kind):
    view.annotations.add("current", atom_indices=[0], tag="keep")
    before = view.export_state()
    molsys = view.molsys
    path = tmp_path / "invalid"
    path.write_text("invalid content")
    with pytest.raises(ValueError, match="Confirm restoration"):
        request(view, "restore_work_file", path, kind=kind)
    with pytest.raises(Exception):
        request(view, "restore_work_file", path, kind=kind, confirmed=True)
    assert view.molsys is molsys and view.export_state() == before
    assert view.history.can_undo()


@pytest.mark.parametrize(
    "details",
    [
        {"file_kind": "unknown"},
        {"path": " "},
        {"request_id": ""},
        {"overwrite": "true"},
    ],
)
def test_invalid_save_declarations_do_not_write(view, tmp_path, details):
    path = tmp_path / "absent"
    content = {"action": "save_work_file", "path": str(path), "file_kind": "state", "request_id": "invalid", **details}
    with pytest.raises(ValueError):
        dispatch_panel_action(view, content)
    assert not path.exists()


def test_file_results_are_correlated_and_not_retained_in_scene_replay(view, tmp_path):
    transmitted = []
    original = view.widget.send

    def observe(message, buffers=None):
        transmitted.append(message)
        return original(message, buffers=buffers)

    view.widget.send = observe
    view._ready = True
    path = tmp_path / "scene.json"
    request(view, "save_work_file", path)
    result = transmitted[-1]
    assert result == {
        "op": "studio_action_result",
        "action": "save_work_file",
        "request_id": "file-review",
        "domain": "export",
        "ok": True,
    }
    with pytest.raises(ValueError, match="already exists"):
        request(view, "save_work_file", path)
    assert transmitted[-1]["ok"] is False
    assert transmitted[-1]["request_id"] == "file-review"
    assert transmitted[-1]["error_message"]
    assert all(message.get("op") != "studio_action_result" for message in view._build_embedded_runtime_snapshot())
