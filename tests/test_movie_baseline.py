"""Real scene restoration and protocol lifetime; native draws have a browser guard."""

import asyncio
import os
import runpy
import subprocess
from copy import deepcopy
from pathlib import Path
from threading import Event, Thread

import pytest
from molsysviewer.interactions import _analysis_signature
from molsysviewer.viewer._movie_seek import _apply_sample, _visibility_commands, _visibility_owners
from molsysviewer.viewer.frontend_requests import FrontendRequestError

make_appearance_view = runpy.run_path(str(Path(__file__).with_name("test_movie_appearance.py")))["make_appearance_view"]


@pytest.fixture
def authored():
    with make_appearance_view() as view:
        # Protocol receiving only. The browser guard receives actual Mol* draws.
        view._ready = True
        view._frontend_capabilities = {
            "visual_state_capture": [2],
            "movie_appearance": [1],
            "movie_environment_capture": [1],
        }
        yield view


async def pending(view, coroutine):
    task = asyncio.create_task(coroutine)
    await asyncio.sleep(0)
    assert not task.done()
    assert len(view._frontend_requests._pending) == 1
    return task, next(iter(view._frontend_requests._pending.values()))


def reply(view, request, *, frame=0, camera=None):
    baseline = view.movie.to_dict()["baseline"]
    return {
        "event": "visual_state_snapshot",
        "request_id": request.request_id,
        "capture_revision": request.revision,
        "capture_version": 2,
        "movie_environment_capture": 1,
        "movie_environment": {"background": {"color": 0}, "lighting": {"ambient": 0.2, "diffuse": 0.8}},
        "ok": True,
        "snapshot": deepcopy(baseline["camera"] if camera is None else camera),
        "structure_index": frame,
        "box_structure_index": None,
        "playback": {"fps": 30, "step_size": 1, "mode": "loop", "direction": "forward", "playing": False},
    }


def test_live_baseline_uses_acknowledged_frame_and_camera_without_applying_it(authored):
    async def exercise():
        original = authored.export_state()
        observed = {"position": [3, 4, 50], "target": [3, 4, 5], "up": [0, 1, 0]}
        task, request = await pending(authored, authored.movie.capture_baseline_async(2000))
        authored._handle_frontend_event(reply(authored, request, frame=2, camera=observed))
        recipe = await task
        assert recipe["tracks"] == [] and recipe["duration_ms"] == 2000
        assert recipe["baseline"]["camera"] == observed
        assert recipe["baseline"]["scene"]["view"]["structure_index"] == 2
        assert authored.export_state() == original
        recipe["baseline"]["camera"]["position"][0] = 999
        assert authored.movie.evaluate(0)["camera"] == observed
        assert not authored._frontend_requests._pending and authored.movie._seek_request is None

    asyncio.run(exercise())


@pytest.mark.parametrize("change", ["scene", "recipe", "legacy"])
def test_intervening_edit_preserves_the_latest_work(authored, change):
    async def exercise():
        if change == "legacy":
            authored.movie.clear()
        task, request = await pending(authored, authored.movie.capture_baseline_async(2000))
        if change == "scene":
            authored.annotations.add("New work", atom_indices=[1], tag="new-work")
        elif change == "recipe":
            authored.movie.set_duration(3000)
        else:
            authored.movie.add_keyframe(100)
        expected = authored.movie.to_dict()
        observed = {"position": [0, 0, 20], "target": [0, 0, 0], "up": [0, 1, 0]}
        answer = (
            reply(authored, request, camera=observed)
            if change != "legacy"
            else {
                "event": "visual_state_snapshot",
                "request_id": request.request_id,
                "capture_revision": request.revision,
                "capture_version": 2,
                "ok": True,
            }
        )
        authored._handle_frontend_event(answer)
        with pytest.raises(FrontendRequestError):
            await task
        assert authored.movie.to_dict() == expected
        if change == "scene":
            assert authored.annotations.get("new-work") is not None
        assert not authored._frontend_requests._pending and authored.movie._seek_request is None

    asyncio.run(exercise())


@pytest.mark.parametrize("termination", ["cancel", "timeout"])
def test_baseline_wait_cannot_replace_recipe_after_termination(authored, termination):
    async def exercise():
        expected = authored.movie.to_dict()
        task, request = await pending(
            authored, authored.movie.capture_baseline_async(2000, timeout=0.02 if termination == "timeout" else 5)
        )
        if termination == "cancel":
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(FrontendRequestError, match="request_timeout"):
                await task
        authored._handle_frontend_event(reply(authored, request))
        assert authored.movie.to_dict() == expected
        assert not authored._frontend_requests._pending and authored.movie._seek_request is None

    asyncio.run(exercise())


def test_reset_restores_objects_before_zero_keys_without_replacing_science(authored):
    async def exercise():
        authored.movie.update_track("background", keys=[{"time_ms": 0, "value": 0xFFFFFF}])
        recipe = authored.movie.to_dict()
        system = authored.molsys
        science = _analysis_signature(authored.interactions.get_analysis("story-hbonds"))
        sample = authored.movie._timeline.evaluate(1000, tracked_visibility=True)
        owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
        _apply_sample(
            authored.movie, authored.movie._timeline, sample, _visibility_commands(owners, sample["visibility"])
        )
        authored.shapes["site"].delete()
        authored.annotations.add("Later", atom_indices=[2], tag="later")
        authored.history.clear()
        task, request = await pending(authored, authored.movie.reset_async(timeout=10))
        assert authored.shapes.get("site") is not None and authored.annotations.get("later") is None
        assert authored.export_state()["environment"]["background"] == {"color": 0}
        assert (
            next(row for row in authored.movie.evaluate(0)["appearance"] if row["property"] == "background")["value"]
            == 0xFFFFFF
        )
        authored._handle_frontend_event(reply(authored, request))
        restored = await task
        assert restored["view"]["structure_index"] == 0
        assert restored["environment"]["background"] == {"color": 0}
        assert authored.movie.to_dict() == recipe and authored.molsys is system
        assert _analysis_signature(authored.interactions.get_analysis("story-hbonds")) == science
        assert authored.history.undo()
        assert authored.annotations.get("later") is not None and authored.shapes.get("site") is None
        assert not authored.history.can_undo()

    asyncio.run(exercise())


def test_reset_missing_scientific_analysis_is_rejected_before_mutation(authored):
    authored.interactions.clear()
    authored.interactions.delete_analysis("story-hbonds")
    before, recipe = authored.export_state(), authored.movie.to_dict()
    with pytest.raises(KeyError, match="story-hbonds"):
        asyncio.run(authored.movie.reset_async())
    assert authored.export_state() == before and authored.movie.to_dict() == recipe
    assert not authored._frontend_requests._pending and authored.movie._seek_request is None


def test_baseline_capture_reserves_movie_owner(authored):
    async def exercise():
        task, request = await pending(authored, authored.movie.capture_baseline_async(1000))
        with pytest.raises(FrontendRequestError, match="movie_operation_pending"):
            await authored.movie.reset_async()
        authored._handle_frontend_event(reply(authored, request))
        await task

    asyncio.run(exercise())


def test_state_restore_retains_saved_priority_during_styling(authored):
    state = authored.export_state()
    order = authored.regions["site"].order
    high_water_mark = authored._region_order_counter
    authored.import_state(state)
    assert authored.regions["site"].order == order
    # Restoring a persisted identity must not advance its priority allocator.
    assert authored._region_order_counter == high_water_mark


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Explicit real Mol*/Chromium Movie receiving is required.",
)
def test_native_baseline_reset_and_capture():
    root = Path(__file__).parents[1]
    subprocess.run(["node", "tests/e2e/movie-appearance.e2e.js"], cwd=root / "molsysviewer/js", check=True, timeout=180)


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_TYPES_TEST") != "1",
    reason="Explicit frontend TypeScript compiler receiving is required.",
)
def test_movie_frontend_type_contract():
    """Compile the actual Movie request/controller graph against native declarations."""
    js = Path(__file__).parents[1] / "molsysviewer/js"
    subprocess.run(
        [
            "node",
            str(js / "node_modules/typescript/bin/tsc"),
            "--noEmit",
            "--strict",
            "--skipLibCheck",
            "--target",
            "es2022",
            "--module",
            "es2022",
            "--moduleResolution",
            "node",
            "--esModuleInterop",
            "--resolveJsonModule",
            "src/messages/frontend-requests.ts",
            "src/managers/movie-timeline.ts",
        ],
        cwd=js,
        check=True,
        timeout=120,
    )


def test_cancellation_after_preparation_grant_cannot_install_a_baseline(authored):
    async def exercise():
        expected = authored.movie.to_dict()
        task, request = await pending(authored, authored.movie.capture_baseline_async(2000))
        answer = reply(authored, request)
        entered, release = Event(), Event()

        def occupy():
            with authored._system_edits._locked():
                entered.set()
                assert release.wait(timeout=5)

        worker = Thread(target=occupy)
        worker.start()
        assert entered.wait(timeout=2)
        try:
            assert authored._frontend_requests.receive(answer, endpoint_id="primary")
            deadline = asyncio.get_running_loop().time() + 2
            while not authored._system_edits._unlock_callbacks and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.001)
            assert authored._system_edits._unlock_callbacks
            release.set()
            worker.join(timeout=2)
            assert not worker.is_alive()
            # Grant prepares the candidate first; cancellation is queued before
            # the caller can resume and install it. No live owners are replaced.
            asyncio.get_running_loop().call_soon(task.cancel)
            with pytest.raises(asyncio.CancelledError):
                await task
            assert authored.movie.to_dict() == expected
            assert not authored._frontend_requests._pending and authored.movie._seek_request is None
        finally:
            release.set()
            worker.join(timeout=2)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())
