"""Real Movie model/host-loop protocol controls; native draws are received separately."""

import asyncio
import json
import os
import runpy
from concurrent.futures import Future
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from molsysviewer.viewer._movie_studio import MovieStudioCancelled
from molsysviewer.viewer.frontend_requests import FrontendRequestError
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv

CAMERA = {"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]}


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as view:
            view.whole.set_representation("ball-and-stick")
            view.regions.add(tag="site", atom_indices=[0, 1], representation="ball-and-stick")
            view.movie.set_baseline(1000, camera=CAMERA)
            view._ready = True
            view._frontend_capabilities = {
                "visual_state_capture": [2],
                "movie_appearance": [1],
                "movie_environment_capture": [1],
                "movie_preview": [1],
            }
            yield view


def send(view, action, **details):
    return dispatch_panel_action(
        view, {"action": action, "revision": view.movie._studio_revision, "request_id": action + "-review", **details}
    )


def key(**details):
    return {
        "tag": "frames",
        "target": {"domain": "structure"},
        "property": "index",
        "time_ms": 500,
        "value": 2,
        "easing": "linear",
        **details,
    }


async def request(view, future):
    assert isinstance(future, Future)
    for _ in range(30):
        if view._frontend_requests._pending:
            return next(iter(view._frontend_requests._pending.values()))
        if future.done():
            future.result()
        await asyncio.sleep(0)
    raise AssertionError("The Movie operation did not submit its owned capture.")


def reply(view, request, *, camera=CAMERA, endpoint="primary"):
    view._handle_frontend_event(
        {
            "event": "visual_state_snapshot",
            "request_id": request.request_id,
            "capture_revision": request.revision,
            "capture_version": 2,
            "ok": True,
            "snapshot": deepcopy(camera),
            "structure_index": 0,
            "playback": {"fps": 30, "step_size": 1, "mode": "loop", "direction": "forward", "playing": False},
            "movie_environment_capture": 1,
            "movie_environment": {"background": {"color": 0}, "lighting": {"ambient": 0.4, "diffuse": 0.6}},
            "_capture_endpoint_id": endpoint,
        }
    )


def test_editor_uses_public_movie_semantics_without_applying_scene(view):
    before = view.export_state()
    before.pop("movie", None)
    coordinates = view.get_coordinates().copy()
    send(view, "movie_set_key", **key())
    assert view.movie.evaluate(500)["structure_index"] == 2
    after = view.export_state()
    after.pop("movie", None)
    assert after == before
    np.testing.assert_array_equal(
        msv.pyunitwizard.get_value(view.get_coordinates()), msv.pyunitwizard.get_value(coordinates)
    )
    with pytest.raises(ValueError, match="Confirm replacement"):
        send(view, "movie_set_key", **key(value=1))
    send(view, "movie_set_key", **key(value=1, replace=True))
    assert view.movie.evaluate(500)["structure_index"] == 1
    send(view, "movie_set_key", **key(time_ms=800, value=2))
    send(view, "movie_remove_key", tag="frames", time_ms=500)
    assert view.movie.evaluate(500)["structure_index"] == 0
    send(view, "movie_remove_track", tag="frames", confirmed=True)
    assert view.movie.info()["n_tracks"] == 0


@pytest.mark.parametrize("value", [-1, 3, True, None, float("nan")])
def test_invalid_keys_leave_the_last_valid_recipe_intact(view, value):
    before = view.movie.to_dict()
    with pytest.raises((ValueError, TypeError)):
        send(view, "movie_set_key", **key(value=value))
    assert view.movie.to_dict() == before


def test_stale_drafts_and_unconfirmed_replacements_preserve_the_recipe(view):
    revision = view.movie._studio_revision
    view.movie.set_duration(1200)
    expected = view.movie.to_dict()
    with pytest.raises(ValueError, match="changed"):
        send(view, "movie_set_key", revision=revision, **key())
    with pytest.raises(ValueError, match="Confirm"):
        send(view, "movie_start", duration_ms=1000)
    with pytest.raises(ValueError, match="Confirm"):
        send(view, "movie_clear")
    assert view.movie.to_dict() == expected


@pytest.mark.parametrize("endpoint", ["primary", "canvas-review"])
def test_camera_key_capture_has_its_own_canvas_and_detached_intent(view, endpoint):
    async def exercise():
        if endpoint != "primary":
            view._endpoint_transfers.register(endpoint, "canvas")
        content = key(tag="camera", target={"domain": "camera"}, property="pose")
        observed = {**CAMERA, "position": [8, 0, 30]}
        result = send(view, "movie_capture_key", _capture_endpoint_id=endpoint, **content)
        content["target"]["domain"] = "structure"
        pending = await request(view, result)
        assert pending.endpoint_id == endpoint
        reply(view, pending, camera=observed, endpoint=endpoint)
        await asyncio.wrap_future(result)
        assert view.movie.evaluate(500)["camera"]["position"] == observed["position"]
        assert not view._frontend_requests._pending and view.movie._seek_request is None

    asyncio.run(exercise())


@pytest.mark.parametrize("when", ["queued", "capturing", "endpoint_close", "view_close"])
def test_cancellation_and_close_retire_owned_jobs_without_late_recipe_writes(view, when):
    async def exercise():
        before = view.movie.to_dict()
        endpoint = "canvas-review"
        view._endpoint_transfers.register(endpoint, "canvas")
        result = send(
            view,
            "movie_capture_key",
            _capture_endpoint_id=endpoint,
            **key(tag="camera", target={"domain": "camera"}, property="pose"),
        )
        pending = None if when == "queued" else await request(view, result)
        if when == "endpoint_close":
            view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": endpoint})
        elif when == "view_close":
            view.close()
        else:
            send(view, "movie_cancel", job_id="movie_capture_key-review")
        with pytest.raises((MovieStudioCancelled, asyncio.CancelledError, FrontendRequestError)):
            await asyncio.wrap_future(result)
        if pending is not None:
            reply(view, pending, camera={**CAMERA, "position": [9, 0, 30]}, endpoint=endpoint)
        assert view.movie.to_dict() == before
        assert not view._frontend_requests._pending
        assert view.movie._studio.job is None
        assert not view.widget._scheduled_callbacks

    asyncio.run(exercise())


def test_inspection_pages_are_bounded_detached_and_endpoint_owned(view):
    track = {
        "tag": "frames",
        "target": {"domain": "structure"},
        "property": "index",
        "keys": [{"time_ms": at, "value": at % 3} for at in range(250)],
    }
    view.movie.add_track(track)
    sent = []
    native_send = view.widget.send

    def observe(message, buffers=None):
        if message.get("op") == "set_movie_state":
            sent.append(message)
        return native_send(message, buffers=buffers)

    view.widget.send = observe
    view._endpoint_transfers.register("panel-review", "panel")
    send(view, "movie_inspect", tag="frames", key_offset=100, _studio_owner_endpoint_id="panel-review")
    message = sent[-1]
    assert message["target_endpoint_id"] == "panel-review"
    assert len(message["editor"]["track"]["keys"]) == 100
    assert message["editor"]["track"]["n_keys"] == 250
    message["editor"]["track"]["keys"][0]["value"] = 999
    assert view.movie.evaluate(100)["structure_index"] == 1
    assert "baseline" not in message and "coordinates" not in message


def test_plain_python_refuses_live_gui_work_without_creating_a_loop(view):
    before = view.movie.to_dict()
    with pytest.raises(RuntimeError, match="running"):
        send(view, "movie_start", duration_ms=1000, confirmed=True)
    assert view.movie._studio.job is None and not view.widget._scheduled_callbacks
    assert view.movie.to_dict() == before


@pytest.mark.parametrize("action", ["movie_start", "movie_pause"])
@pytest.mark.parametrize("request_id", [None, "", "   ", 42])
def test_live_operations_require_a_correlated_request_before_scheduling(view, action, request_id):
    before = view.movie.to_dict()
    with pytest.raises(ValueError, match="request identifier"):
        send(view, action, request_id=request_id, duration_ms=1000, confirmed=True)
    assert view.movie._studio.job is None and view.movie._studio.pause_job is None
    assert not view.widget._scheduled_callbacks and view.movie.to_dict() == before


def test_legacy_builder_edits_invalidate_editor_drafts(view):
    view.movie.clear()
    revision = view.movie._studio_revision
    view.movie.add_structure_sweep(to_index=2, duration_ms=500)
    assert view.movie._studio_revision == revision + 1
    with pytest.raises(ValueError, match="changed"):
        send(view, "movie_start", revision=revision, duration_ms=1000, confirmed=True)


@pytest.mark.parametrize(
    "target,prop", [({"domain": "whole"}, "alpha"), ({"domain": "region", "tag": "site"}, "visible")]
)
def test_a_track_name_cannot_silently_retarget_a_new_key(view, target, prop):
    send(view, "movie_set_key", **key())
    before = view.movie.to_dict()
    with pytest.raises(ValueError, match="another target or property"):
        send(view, "movie_set_key", **key(target=target, property=prop, time_ms=600, value=1))
    assert view.movie.to_dict() == before


@pytest.mark.jupyter_runtime
def test_live_jupyter_movie_authoring(tmp_path):
    if os.environ.get("MOLSYSVIEWER_JUPYTER_TEST") != "1":
        pytest.skip("Select MOLSYSVIEWER_JUPYTER_TEST=1 for actual Jupyter Movie receiving.")
    output = tmp_path / "jupyter-movie"
    owner = runpy.run_path(str(Path(__file__).with_name("_jupyter_live_capture.py")))
    assert owner["run"](output, profile="movie") == 0, f"Private Movie diagnostics: {output}"
    receipt = json.loads((output / "command-result.json").read_text())
    assert receipt["profile"] == "movie" and receipt["browser_summary"]["movie_authoring_cases"] == 8
    observed = json.loads((output / "observations.json").read_text())
    assert observed["outcome"] == "passed" and observed["movie_source_unchanged"]
    assert observed["movie_cancel_late_reply_preserved"]
    assert observed["movie_python_studio_pause"]
    assert receipt["process_cleanup"]["survivors"] == [] and receipt["process_cleanup"]["errors"] == []
    assert not (output / "settings.json").exists()
    assert not (output / "config/jupyter_server_config.py").exists()
