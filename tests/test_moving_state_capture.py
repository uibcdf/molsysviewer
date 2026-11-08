"""Moving-capture protocol and real-system persistence; native draws are separate."""

import asyncio
import json
import zipfile
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.viewer.frontend_requests import FrontendRequestError
from molsysviewer.viewer.panel_actions import dispatch_panel_action
from molsysviewer.viewer.visual_capture import (
    finish_live_capture,
    prepare_live_capture,
    send_live_capture,
    write_captured_state,
)

import molsysviewer as msv

CAMERA = {"position": [20.0, 30.0, 40.0], "target": [2.0, 3.0, 4.0], "up": [0.0, 1.0, 0.0]}
PLAYBACK = {"fps": 6, "step_size": 1, "mode": "loop", "direction": "forward", "playing": True}


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with source.extract(structure_indices=[0, 8, 3]) as result:
            coordinates = msv.pyunitwizard.get_value(result.get_coordinates(), to_unit="nm").copy()
            coordinates[1, 1] += [100.0, 100.0, 100.0]
            cells = np.array([np.diag([length, length + 1, length + 2]) for length in [3.0, 4.0, 5.0]])
            msm.set(result.molsys, coordinates=msv.pyunitwizard.quantity(coordinates, "nm"))
            msm.set(result.molsys, box=msv.pyunitwizard.quantity(cells, "nm"))
            result.apply_system_edit(result.molsys, skip_digestion=True)
            result.show_box(color="red", width=0.2, alpha=0.7)
            result.measurements.add_distance([0], [5], tag="distance")
            result.annotations.add("retained", atom_indices=[0], tag="note")
            result.shapes.add_sphere(
                structure_centers="[[1, 2, 3], [2, 3, 4], [3, 4, 5]] nm",
                radius="0.1 nm",
                tag="marker",
            )
            result._dynamic_region_evaluation_budget_ms = float("inf")
            region = result.regions.add(selection="atom_index==1 within 1 nm without pbc of atom_index==0", tag="near")
            region.mode = "dynamic"
            result._ready = True
            result._frontend_capabilities = {"visual_state_capture": [1, 2]}
            yield result


@pytest.mark.parametrize("kind", ["state", "session"])
@pytest.mark.parametrize("frame", [0, 1, 2])
def test_dynamic_region_recovery_uses_the_saved_structure(view, tmp_path, kind, frame):
    view.regions.add(selection=[1], tag="fixed")
    view.player.go_to_structure(frame)
    view._handle_dynamic_region_evaluation_request({"frame": frame})
    expected = () if frame == 1 else (1,)
    assert view.regions["near"].atom_indices == expected
    path = tmp_path / ("state.json" if kind == "state" else "session.msv")
    if kind == "session":
        view.save_session(path)
        restored = msv.load_session(path)
    else:
        view.save_state(path)
        restored = msv.new_view(view.molsys)
        restored.player.go_to_structure((frame + 1) % 3)
        restored.load_state(path)
    with restored:
        assert restored.player.index == frame
        assert restored.regions["near"].mode == "dynamic"
        assert restored.regions["near"].uid == view.regions["near"].uid
        assert restored.regions["near"].atom_indices == expected
        assert restored.regions["fixed"].atom_indices == (1,)


def reply(ticket, frame, *, box_frame=None):
    return {
        "event": "visual_state_snapshot",
        "request_id": ticket.request_id,
        "capture_revision": ticket.revision,
        "capture_version": 2,
        "ok": True,
        "snapshot": deepcopy(CAMERA),
        "structure_index": frame,
        "box_structure_index": frame if box_frame is None else box_frame,
        "playback": deepcopy(PLAYBACK),
    }


@pytest.mark.parametrize("kind", ["state", "session"])
@pytest.mark.parametrize("entry", ["python", "studio", "studio-popup"])
def test_save_retains_sampled_frame_context_while_the_live_view_advances(view, tmp_path, kind, entry):
    async def run():
        view.interactions.hbonds.get_buch_hbonds(
            name="moving-review", structure_indices="all", distance_threshold="0.4 nm"
        )
        view.interactions.add("moving-review", tag="contacts")
        view.player.play(fps=6)
        events = []
        view.on_frame_change(events.append)
        system = view.molsys
        original = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm").copy()
        path = tmp_path / ("moving.json" if kind == "state" else "moving.msv")
        operation = view.save_state_async if kind == "state" else view.save_session_async
        endpoint = "capture-popup" if entry == "studio-popup" else "primary"
        if endpoint != "primary":
            view._endpoint_transfers.register(endpoint, "canvas")

        async def save():
            if entry == "python":
                await operation(path)
            else:
                future = dispatch_panel_action(
                    view,
                    {
                        "action": "save_work_file",
                        "request_id": "moving-review",
                        "path": str(path),
                        "file_kind": kind,
                        "_capture_endpoint_id": endpoint,
                        "_work_file_owner_endpoint_id": endpoint,
                    },
                )
                await asyncio.wrap_future(future)

        task = asyncio.create_task(save())
        await asyncio.sleep(0)
        assert not task.done()
        ticket = next(iter(view._frontend_requests._pending.values()))
        # This is ordinary accepted authority feedback, not capture navigation.
        view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 1, "is_playing": True})
        view._handle_frontend_event({"event": "request_dynamic_region_evaluation", "frame": 1})
        assert view.player.index == 1 and view.regions["near"].atom_indices == ()
        message = reply(ticket, 2)
        if endpoint != "primary":
            message["_capture_endpoint_id"] = endpoint
        view._handle_frontend_event(message)
        await task
        assert view.molsys is system
        assert view.player.index == 1 and view.player.is_playing
        assert events == [{"event": "frame_changed", "frame": 1, "is_playing": True}]
        assert not view._frontend_requests._pending
        assert not view._work_file_saves._pending
        assert not view.widget._scheduled_callbacks
        np.testing.assert_array_equal(msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm"), original)
        if kind == "state":
            saved = json.loads(path.read_text())
            restored = msv.new_view(view.molsys)
            restored._dynamic_region_evaluation_budget_ms = float("inf")
            restored.load_state(path)
        else:
            with zipfile.ZipFile(path) as archive:
                saved = json.loads(archive.read("state.json"))
            restored = msv.new_view()
            restored._dynamic_region_evaluation_budget_ms = float("inf")
            msv.load_session(path, view=restored)
        with restored:
            assert saved["view"]["camera"] == CAMERA
            assert saved["view"]["structure_index"] == restored.player.index == 2
            assert saved["view"]["playback"] == PLAYBACK
            assert restored.player.is_playing
            assert saved["box_display"]["structure_index"] == 2
            assert restored.export_state()["box_display"] == saved["box_display"]
            assert restored.regions["near"].atom_indices == (1,)
            measured = msv.pyunitwizard.get_value(restored.measurements.info("distance")["value"], to_unit="nm")
            assert float(measured) == pytest.approx(np.linalg.norm(original[2, 0] - original[2, 5]))
            assert restored.annotations.tags() == ["note"]
            assert restored.shapes.tags() == ["marker"]
            assert restored.interactions.tags() == ["contacts"]
            assert saved["shapes"][0]["options"]["structures_coords"] == [[10, 20, 30], [20, 30, 40], [30, 40, 50]]
            np.testing.assert_array_equal(
                msv.pyunitwizard.get_value(restored.get_coordinates(), to_unit="nm"), original
            )

    asyncio.run(run())


@pytest.mark.parametrize("versions,expected", [([1], 1), ([1, 2], 2), ([2], 2)])
def test_capture_negotiates_the_wire_version_without_changing_legacy_messages(view, versions, expected):
    view._frontend_capabilities = {"visual_state_capture": versions}
    sent = []
    original = view.widget.send

    def observe(message, buffers=None):
        sent.append(deepcopy(message))
        return original(message, buffers=buffers)

    view.widget.send = observe
    captured, ticket = prepare_live_capture(view, timeout=5)
    send_live_capture(view, ticket, protocol_version=captured.protocol_version)
    message = next(message for message in sent if message.get("op") == "request_visual_state")
    assert captured.protocol_version == expected
    assert message.get("capture_version", 1) == expected
    if expected == 1:
        assert "capture_version" not in message


@pytest.mark.parametrize(
    "field,value",
    [
        ("capture_version", None),
        ("capture_version", 1),
        ("capture_version", True),
        ("capture_version", 2.0),
        ("structure_index", None),
        ("structure_index", True),
        ("structure_index", -1),
        ("structure_index", 3),
        ("structure_index", 1.5),
        ("box_structure_index", None),
        ("box_structure_index", True),
        ("box_structure_index", -1),
        ("box_structure_index", 3),
        ("playback", None),
        ("playback", {}),
        ("playback.fps", True),
        ("playback.fps", 0),
        ("playback.fps", 1.5),
        ("playback.fps", 2**53),
        ("playback.step_size", True),
        ("playback.step_size", 0),
        ("playback.mode", []),
        ("playback.mode", "unknown"),
        ("playback.direction", []),
        ("playback.direction", "unknown"),
        ("playback.playing", 1),
    ],
)
def test_invalid_moving_reply_cannot_partially_change_the_detached_recipe(view, field, value):
    captured, ticket = prepare_live_capture(view, timeout=5)
    original = deepcopy(captured.state)
    message = reply(ticket, 2)
    owner, _, nested = field.partition(".")
    if nested:
        message[owner][nested] = value
    else:
        message[owner] = value
    with pytest.raises(FrontendRequestError):
        finish_live_capture(view, captured, message)
    assert captured.state == original
    assert view.player.index == 0


@pytest.mark.parametrize("kind", ["state", "session"])
@pytest.mark.parametrize(
    "change",
    [
        "annotation",
        "shape",
        "region",
        "box_style",
        "box_frame",
        "annotation_aba",
        "suspended_aba",
        "box_aba",
        "analysis_added",
        "analysis_metadata",
        "system",
    ],
)
def test_non_temporal_edits_preserve_existing_work_files(view, tmp_path, kind, change):
    async def run():
        if change == "analysis_metadata":
            view.interactions.hbonds.get_buch_hbonds(name="capture-review", structure_indices="all")
        original_scene = deepcopy(view.export_state())
        path = tmp_path / ("keep.json" if kind == "state" else "keep.msv")
        path.write_bytes(b"preserved original bytes")
        operation = view.save_state_async if kind == "state" else view.save_session_async
        task = asyncio.create_task(operation(path))
        await asyncio.sleep(0)
        ticket = next(iter(view._frontend_requests._pending.values()))
        if change == "annotation":
            view.annotations["note"].set_text("changed")
        elif change == "shape":
            view.shapes["marker"].set_radius("0.2 nm")
        elif change == "region":
            view.regions["near"].mode = "static"
        elif change == "box_style":
            view.show_box(color="blue", width=0.2, alpha=0.7)
        elif change == "box_frame":
            view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=1)
        elif change == "annotation_aba":
            with view.history.coalescing():
                view.annotations["note"].set_text("changed")
                view.annotations["note"].set_text("retained")
        elif change == "suspended_aba":
            with view.history.suspended():
                view.annotations["note"].set_text("changed")
                view.annotations["note"].set_text("retained")
        elif change == "box_aba":
            view.show_box(color="blue", width=0.2, alpha=0.7)
            view.show_box(color="red", width=0.2, alpha=0.7)
        elif change == "analysis_added":
            view.interactions.hbonds.get_buch_hbonds(name="new-analysis", structure_indices="all")
        elif change == "analysis_metadata":
            view.molsys.interactions["capture-review"].parameters["capture_regression"] = "changed"
        else:
            view.apply_system_edit(view.molsys)
        if change in {"annotation_aba", "suspended_aba", "box_aba"}:
            # The rejection must protect an intervening edit, rather than be
            # an incidental consequence of a different final serialized value.
            assert view.export_state() == original_scene
        view._handle_frontend_event(reply(ticket, 2))
        with pytest.raises(FrontendRequestError):
            await task
        assert path.read_bytes() == b"preserved original bytes"
        assert not view._frontend_requests._pending
        assert not list(tmp_path.glob("*.tmp"))

    asyncio.run(run())


def test_automatic_box_following_preserves_definition_and_scene_edit_revisions(view):
    revisions = (view._box_definition_revision, view.history._edit_revision)
    view.player.go_to_structure(1)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 2, "is_playing": True})
    assert view.export_state()["box_display"]["structure_index"] == 2
    assert (view._box_definition_revision, view.history._edit_revision) == revisions


def test_intentionally_selected_other_cell_is_retained_in_a_moving_capture(view):
    view.player.go_to_structure(2)
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=0)
    captured, ticket = prepare_live_capture(view, timeout=5)
    finish_live_capture(view, captured, reply(ticket, 2, box_frame=0))
    assert captured.state["view"]["structure_index"] == 2
    assert captured.state["box_display"]["structure_index"] == 0


def test_a_rejected_box_width_does_not_invalidate_an_unchanged_pending_capture(view):
    captured, ticket = prepare_live_capture(view, timeout=5)
    with pytest.raises(Exception):
        view.show_box(width=-1)
    finish_live_capture(view, captured, reply(ticket, 2))
    assert captured.state["view"]["camera"] == CAMERA


def test_renderer_box_metadata_cannot_invent_an_unrequested_cell_display(view):
    view.hide_box()
    captured, ticket = prepare_live_capture(view, timeout=5)
    original = deepcopy(captured.state)
    with pytest.raises(FrontendRequestError, match="unexpected_box_display"):
        finish_live_capture(view, captured, reply(ticket, 2))
    assert captured.state == original


def test_a_later_frame_does_not_rewrite_the_already_sampled_file_context(view, tmp_path):
    captured, ticket = prepare_live_capture(view, timeout=5)
    finish_live_capture(view, captured, reply(ticket, 2))
    view.player.go_to_structure(1)
    path = tmp_path / "sampled.json"
    write_captured_state(view, captured, path, kind="state")
    assert json.loads(path.read_text())["view"]["structure_index"] == 2
    assert view.player.index == 1


def test_a_later_scene_edit_is_rechecked_before_writing(view, tmp_path):
    captured, ticket = prepare_live_capture(view, timeout=5)
    finish_live_capture(view, captured, reply(ticket, 2))
    view.annotations["note"].set_text("changed after sampling")
    path = tmp_path / "keep.json"
    path.write_text("keep")
    with pytest.raises(FrontendRequestError, match="scene_changed"):
        write_captured_state(view, captured, path, kind="state")
    assert path.read_text() == "keep"


def test_shape_only_capture_accepts_first_camera_telemetry_without_a_molecular_system(tmp_path):
    async def run():
        with msv.new_view() as scene:
            scene.shapes.add_sphere(center="[1, 2, 3] nm", tag="absolute")
            scene._ready = True
            scene._frontend_capabilities = {"visual_state_capture": [2]}
            path = tmp_path / "shape.json"
            task = asyncio.create_task(scene.save_state_async(path))
            await asyncio.sleep(0)
            ticket = next(iter(scene._frontend_requests._pending.values()))
            scene._handle_frontend_event({"event": "camera_snapshot", "snapshot": deepcopy(CAMERA)})
            message = reply(ticket, 0)
            message["box_structure_index"] = None
            message["playback"]["playing"] = False
            scene._handle_frontend_event(message)
            await task
            state = json.loads(path.read_text())
            assert state["view"]["camera"] == CAMERA
            assert state["shapes"][0]["tag"] == "absolute"
            assert not scene._frontend_requests._pending

    asyncio.run(run())
