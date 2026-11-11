"""Track evaluation and session persistence with bundled molecular systems."""

import asyncio
import json
import zipfile
from copy import deepcopy
from pathlib import Path

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.session import SessionFormatError
from molsysviewer.viewer.frontend_requests import FrontendRequestError

import molsysviewer as msv

CAMERA = {"position": [0, 0, 10], "target": [0, 0, 0], "up": [0, 1, 0]}
END = {"position": [2, 0, 20], "target": [2, 0, 0], "up": [0, -1, 0]}


def _track(tag, domain, prop, *keys, target=None):
    return {
        "tag": tag,
        "target": {"domain": domain, **({"tag": target} if target is not None else {})},
        "property": prop,
        "keys": [{"time_ms": time, "value": value} for time, value in keys],
    }


@pytest.fixture
def authored():
    source = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    with msv.new_view(source, structure_indices=[4999, 0, 73]) as view:
        view.regions.add(tag="site", atom_indices=[0, 1, 2])
        view.shapes.add_sphere(center="[0,0,0] angstrom", radius="1 angstrom", tag="site")
        view.movie.set_baseline(1000, camera=CAMERA)
        yield view


def test_camera_structure_and_visibility_tracks_are_independent(authored):
    movie = authored.movie
    assert movie.evaluate(500)["camera"] == CAMERA
    camera_track = _track("camera", "camera", "pose", (1000, END))
    movie.add_track(camera_track)
    before = movie.evaluate(500)["camera"]
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("hide-region", "region", "visible", (200, False), target="site"))
    movie.add_track(_track("hide-shape", "shape", "visible", (700, False), target="site"))
    result = movie.evaluate(500)
    assert result["camera"] == before
    np.testing.assert_allclose(result["camera"]["position"], [1, 0, 15], atol=1e-12)
    assert result["structure_index"] == 2
    visible = {(row["domain"], row["tag"]): row["visible"] for row in result["visibility"]}
    assert visible[("region", "site")] is False
    assert visible[("shape", "site")] is True
    assert np.linalg.norm(result["camera"]["up"]) == pytest.approx(1)
    assert result["camera"]["up"][2] == pytest.approx(0)
    assert movie.evaluate(1000)["camera"] == END
    assert movie.evaluate(500) == result
    assert authored.player.index == 0

    camera_track["keys"][0]["value"] = CAMERA
    result["camera"]["position"][0] = 99
    recipe = movie.to_dict()
    recipe["baseline"]["scene"]["whole"]["visible"] = False
    assert movie.evaluate(500)["camera"] == before
    assert movie.to_dict()["baseline"]["scene"]["whole"]["visible"] is True


def test_edits_and_imports_are_transactional(authored):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (700, 2)))
    before = movie.to_dict()
    with pytest.raises(ValueError, match="one track per target property"):
        movie.add_track(_track("duplicate", "structure", "index", (700, 1)))
    with pytest.raises(ValueError, match="Structure index"):
        movie.update_track("frame", keys=[{"time_ms": 100, "value": 3}])
    with pytest.raises(ValueError, match="Key time"):
        movie.set_duration(699)
    invalid = movie.to_dict()
    invalid["baseline"]["camera"]["up"] = [0, 0, 1]
    with pytest.raises(ValueError, match="parallel"):
        movie.from_dict(invalid)
    invalid = movie.to_dict()
    invalid["baseline"]["scene"]["structure"]["fingerprint"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="different ordered structure"):
        movie.from_dict(invalid)
    assert movie.to_dict() == before

    movie.update_track("frame", keys=[{"time_ms": 400, "value": 1}])
    assert movie.evaluate(500)["structure_index"] == 1
    movie.remove_track("frame")
    assert movie.evaluate(500)["structure_index"] == 0


def test_recipe_and_session_preserve_tracks_without_reapplying_them(authored, tmp_path):
    movie = authored.movie
    movie.add_track(_track("orbit", "camera", "pose", (1000, END)))
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("visibility", "region", "visible", (400, False), target="site"))
    expected = movie.to_dict()
    evaluated = movie.evaluate(500)
    recipe_path = tmp_path / "movie.json"
    movie.save(recipe_path)
    movie.clear()
    movie.load(recipe_path)
    assert movie.to_dict() == expected

    path = tmp_path / "work.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == expected
        assert restored.movie.evaluate(500) == evaluated
        assert restored.player.index == authored.player.index
        restored.movie.validate()

    broken = tmp_path / "broken.msv"
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(broken, "w") as destination:
        for member in source.namelist():
            content = source.read(member)
            if member == "movie.json":
                invalid = json.loads(content)
                invalid["baseline"]["binding"]["fingerprint"] = "sha256:" + "0" * 64
                if "sources" in invalid["baseline"]["scene"]:
                    invalid["baseline"]["scene"]["sources"]["binding"] = invalid["baseline"]["binding"]
                content = json.dumps(invalid)
            destination.writestr(member, content)
    with msv.demo["dialanine"] as destination:
        original = destination.molsys
        with pytest.raises(SessionFormatError, match="Movie recipe does not match"):
            msv.load_session(broken, view=destination)
        assert destination.molsys is original


def test_recipe_binding_and_scene_target_are_checked(authored, tmp_path):
    authored.movie.add_track(_track("visibility", "region", "visible", (100, False), target="site"))
    with msv.demo["dialanine"] as another:
        with pytest.raises(ValueError, match="molecular binding"):
            another.movie.from_dict(authored.movie.to_dict())
    authored.regions["site"].delete()
    with pytest.raises(ValueError, match="missing or changed"):
        authored.movie.validate()
    destination = tmp_path / "unchanged.msv"
    destination.write_bytes(b"existing file")
    with pytest.raises(ValueError, match="missing or changed"):
        authored.save_session(destination)
    assert destination.read_bytes() == b"existing file"


def test_announced_coordinate_edit_invalidates_a_same_size_binding(authored):
    authored.movie.add_track(_track("frame", "structure", "index", (700, 2)))
    coordinates = authored.molsys.structures.coordinates.copy()
    coordinates[0, 0, 0] *= 2
    authored.molsys.structures.coordinates = coordinates
    authored.apply_system_edit(authored.molsys)
    with pytest.raises(ValueError, match="molecular binding"):
        authored.movie.evaluate(500)


def test_shared_movie_oracle_matches_real_python_recipe(authored):
    path = Path(__file__).resolve().parents[1] / "molsysviewer/js/tests/fixtures/movie-timeline-oracle.json"
    oracle = json.loads(path.read_text(encoding="utf-8"))
    recipe = oracle["recipe"]
    # Use this environment's system binding and full scene. The shared fixture
    # contains only the fields needed to evaluate a recipe away from the view.
    authored.movie.set_baseline(recipe["duration_ms"], camera=recipe["baseline"]["camera"])
    for track in recipe["tracks"]:
        authored.movie.add_track(track)

    def check(expected):
        observed = authored.movie.evaluate(expected["time_ms"])
        np.testing.assert_allclose(
            list(observed.pop("camera").values()), list(expected["camera"].values()), atol=1e-12, rtol=0
        )
        assert observed == {key: value for key, value in expected.items() if key != "camera"}

    for expected in oracle["samples"]:
        check(expected)

    half_turn = oracle["half_turn"]
    authored.movie.set_baseline(recipe["duration_ms"], camera=half_turn["begin"])
    authored.movie.add_track(_track("half-turn", "camera", "pose", (1000, half_turn["end"])))
    check(half_turn["sample"])


def _draw_reply(ticket, sample):
    return {
        "event": "visual_state_snapshot",
        "request_id": ticket.request_id,
        "capture_revision": ticket.revision,
        "capture_version": 2,
        "ok": True,
        "snapshot": deepcopy(sample["camera"]),
        "structure_index": sample["structure_index"],
        "playback": {"fps": 12, "step_size": 1, "mode": "loop", "direction": "forward", "playing": False},
    }


def test_seek_preflights_live_support_before_changing_scene(authored):
    authored.movie.add_track(_track("frame", "structure", "index", (300, 2)))
    before = authored.export_state()
    with pytest.raises(FrontendRequestError, match="no_live_frontend"):
        asyncio.run(authored.movie.seek_async(500))
    authored._ready = True
    authored._frontend_capabilities = {"visual_state_capture": [1]}
    with pytest.raises(FrontendRequestError, match="capture_not_supported"):
        asyncio.run(authored.movie.seek_async(500))
    assert authored.export_state() == before
    assert not authored._frontend_requests._pending


def test_seek_applies_typed_visibility_and_awaits_correlated_draw(authored, tmp_path):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("camera", "camera", "pose", (1000, END)))
    movie.add_track(_track("region", "region", "visible", (200, False), target="site"))
    movie.add_track(_track("shape", "shape", "visible", (700, False), target="site"))
    authored.shapes.add_sphere(center="[1, 1, 1] angstrom", radius="1 angstrom", tag="other")
    authored.shapes.hide("other")
    authored._ready = True
    authored._frontend_capabilities = {"visual_state_capture": [2]}
    authored.player.play(fps=12)

    async def seek(time):
        desired = movie.evaluate(time)
        task = asyncio.create_task(movie.seek_async(time))
        await asyncio.sleep(0)
        ticket = next(iter(authored._frontend_requests._pending.values()))
        assert not task.done()
        reply = _draw_reply(ticket, desired)
        authored._handle_frontend_event({**reply, "capture_revision": "another-revision"})
        assert not ticket.future.done()
        authored._handle_frontend_event(reply)
        result = await task
        assert result["camera"] == desired["camera"]
        assert result["structure_index"] == desired["structure_index"] == authored.player.index
        assert not authored.player.is_playing
        assert not authored._frontend_requests._pending and movie._seek_request is None
        assert len(result["visibility"]) == 2
        return result

    first = asyncio.run(seek(800))
    assert not authored.regions["site"].visible
    assert next(row for row in first["visibility"] if row["domain"] == "shape")["visible"] is False
    assert authored.shapes["site"]._hidden
    asyncio.run(seek(100))
    assert authored.regions["site"].visible and not authored.shapes["site"]._hidden
    assert authored.shapes["other"]._hidden
    path = tmp_path / "after-seek.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == movie.to_dict()
        assert restored.player.index == authored.player.index
        assert restored.regions["site"].visible and not restored.shapes["site"]._hidden


@pytest.mark.parametrize("failure", ["wrong-camera", "wrong-frame", "recipe-edited", "cancelled"])
def test_seek_refuses_stale_draw_and_releases_its_request(authored, failure):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    authored._ready = True
    authored._frontend_capabilities = {"visual_state_capture": [2]}

    async def run():
        sample = movie.evaluate(500)
        task = asyncio.create_task(movie.seek_async(500))
        await asyncio.sleep(0)
        ticket = next(iter(authored._frontend_requests._pending.values()))
        with pytest.raises(FrontendRequestError, match="movie_operation_pending"):
            await movie.seek_async(0)
        assert authored.player.index == 2
        reply = _draw_reply(ticket, sample)
        if failure == "cancelled":
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            authored._handle_frontend_event(reply)
        else:
            if failure == "wrong-camera":
                reply["snapshot"]["position"][0] += 1
                reason = "movie_camera_not_applied"
            elif failure == "wrong-frame":
                reply["structure_index"] = 1
                reason = "movie_structure_not_applied"
            else:
                movie.set_duration(2000)
                reason = "movie_seek_superseded"
            authored._handle_frontend_event(reply)
            with pytest.raises(FrontendRequestError, match=reason):
                await task
        assert not authored._frontend_requests._pending and movie._seek_request is None

    asyncio.run(run())


def test_reentrant_navigation_during_pause_retires_the_seek(authored):
    authored.movie.add_track(_track("frame", "structure", "index", (300, 2)))
    authored._ready = True
    authored._frontend_capabilities = {"visual_state_capture": [2]}
    authored.player.play(fps=12)

    def navigate(event):
        if not event["is_playing"] and event["frame"] == 0:
            authored.player.go_to_structure(1)

    authored.on_frame_change(navigate)
    with pytest.raises(FrontendRequestError, match="movie_seek_superseded"):
        asyncio.run(authored.movie.seek_async(500))
    assert authored.player.index == 1
    assert authored.camera.get_snapshot() is None
    assert not authored._frontend_requests._pending and authored.movie._seek_request is None


def _preview_ready(view):
    view._ready = True
    view._frontend_capabilities = {"visual_state_capture": [2], "movie_preview": [1]}


async def _preview_ticket(view):
    async with asyncio.timeout(2):
        while not view._frontend_requests._pending:
            await asyncio.sleep(0)
    assert len(view._frontend_requests._pending) == 1
    return next(iter(view._frontend_requests._pending.values()))


def test_preview_finishes_at_endpoint_and_keeps_the_authored_state(authored, tmp_path):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("camera", "camera", "pose", (1000, END)))
    movie.add_track(_track("region", "region", "visible", (200, False), target="site"))
    _preview_ready(authored)
    timeline = movie._timeline

    async def run():
        play = asyncio.create_task(movie.play_async(start_time_ms=100))
        first = await _preview_ticket(authored)
        authored._handle_frontend_event(
            {
                **_draw_reply(first, timeline.evaluate(100)),
                "movie_next_sample": timeline.evaluate(1000, tracked_visibility=True),
            }
        )
        final = await _preview_ticket(authored)
        assert final.request_id != first.request_id and final.revision == first.revision
        assert authored.player.index == 2 and not authored.regions["site"].visible
        assert not play.done()
        authored._handle_frontend_event(_draw_reply(final, timeline.evaluate(1000)))
        result = await play
        assert result == timeline.evaluate(1000, tracked_visibility=True)
        assert movie._playback is None and not authored._frontend_requests._pending

    asyncio.run(run())
    path = tmp_path / "preview.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == movie.to_dict()
        assert restored.player.index == 2 and not restored.regions["site"].visible
        assert restored.camera.get_snapshot() == END


def test_backward_seek_drains_preview_before_applying_a_new_frame(authored):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    _preview_ready(authored)

    async def run():
        play = asyncio.create_task(movie.play_async(loop=True, start_time_ms=500))
        playing = await _preview_ticket(authored)
        seek = asyncio.create_task(movie.seek_async(100))
        await asyncio.sleep(0)
        assert not seek.done() and authored.player.index == 2
        authored._handle_frontend_event(_draw_reply(playing, movie.evaluate(500)))
        assert (await play)["time_ms"] == 500
        seeking = await _preview_ticket(authored)
        assert seeking.revision != playing.revision
        authored._handle_frontend_event(_draw_reply(playing, movie.evaluate(500)))
        assert not seeking.future.done()
        authored._handle_frontend_event(_draw_reply(seeking, movie.evaluate(100)))
        assert (await seek)["structure_index"] == 0

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["invalid-sample", "intervening-edit"])
def test_preview_retires_when_the_source_or_clock_reply_changes(authored, failure):
    movie = authored.movie
    _preview_ready(authored)

    async def run():
        play = asyncio.create_task(movie.play_async())
        ticket = await _preview_ticket(authored)
        reply = _draw_reply(ticket, movie.evaluate(0))
        reply["movie_next_sample"] = {**movie._timeline.evaluate(100, tracked_visibility=True), "structure_index": 1}
        expected = "invalid_movie_preview_sample"
        if failure == "intervening-edit":
            authored.whole.hide()
            expected = "movie_preview_superseded"
        authored._handle_frontend_event(reply)
        with pytest.raises(FrontendRequestError, match=expected):
            await play
        assert movie._playback is None and not authored._frontend_requests._pending

    asyncio.run(run())
