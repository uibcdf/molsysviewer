"""Movie's public async owners wait for scene access without retaining it."""

import asyncio
import importlib
from pathlib import Path
from threading import Event, Thread

import pytest
from molsysviewer.system_edits import SystemEditPendingError
from molsysviewer.viewer._movie_studio import MovieStudioCancelled
from molsysviewer.viewer.frontend_requests import FrontendRequestError

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as view:
            view.movie.set_baseline(1000, camera={"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]})
            view._ready = True
            view._frontend_capabilities = {
                "visual_state_capture": [2],
                "movie_environment_capture": [1],
                "movie_preview": [1],
                "movie_frame_capture": [1],
            }
            yield view


def hold_scene(view, before_release=None):
    entered, release = Event(), Event()

    def hold():
        with view._system_edits._locked():
            entered.set()
            assert release.wait(5), "The test must release its own scene owner."
            if before_release:
                before_release()

    owner = Thread(target=hold)
    owner.start()
    assert entered.wait(1)
    return owner, release


async def pending(view, task):
    for _ in range(100):
        if view._frontend_requests._pending:
            return
        if task.done():
            task.result()
        await asyncio.sleep(0.01)
    raise AssertionError("Movie did not request its owned renderer reply.")


@pytest.mark.parametrize(
    "operation",
    ["capture_baseline_async", "review_rebase_async", "reset_async", "seek_async", "play_async", "export_async"],
)
def test_public_async_movie_waits_for_foreign_scene_ownership(view, tmp_path, operation):
    async def exercise():
        args = {"capture_baseline_async": (1000,), "seek_async": (400,), "export_async": (tmp_path / "movie.zip",)}.get(
            operation, ()
        )
        if operation == "export_async":
            pytest.importorskip("imageio")
        worker, release = hold_scene(view)
        task = asyncio.create_task(getattr(view.movie, operation)(*args))
        try:
            await asyncio.sleep(0.02)
            assert not task.done(), "The async entry must wait, not reject transient scene ownership."
            assert not view._frontend_requests._pending
            release.set()
            worker.join(1)
            await pending(view, task)
        finally:
            release.set()
            worker.join(1)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert not worker.is_alive() and not view._frontend_requests._pending

    asyncio.run(exercise())


def test_pause_signal_survives_foreign_scene_ownership(view):
    async def exercise():
        play = asyncio.create_task(view.movie.play_async(loop=True))
        await pending(view, play)
        worker, release = hold_scene(view)
        pause = asyncio.create_task(view.movie.pause_async())
        try:
            await asyncio.sleep(0.02)
            assert not pause.done()
            assert view.movie._playback.pause_requested
        finally:
            release.set()
            worker.join(1)
            play.cancel()
            await asyncio.gather(play, pause, return_exceptions=True)
        assert not worker.is_alive() and not view._frontend_requests._pending

    asyncio.run(exercise())


def test_synchronous_scene_guards_are_not_bypassed(view):
    worker, release = hold_scene(view)
    try:
        for skip in (False, True):
            with pytest.raises(SystemEditPendingError):
                view.movie.info(skip_digestion=skip)
    finally:
        release.set()
        worker.join(1)
    assert not worker.is_alive()


@pytest.mark.parametrize("disposition", ["run", "stale", "close"])
def test_correlated_studio_intent_waits_for_unlock_and_revalidates(view, disposition):
    async def exercise():
        replies = []
        native_send = view.widget.send

        def observe(message, buffers=None):
            if message.get("op") == "studio_action_result":
                replies.append(message)
            return native_send(message, buffers=buffers)

        view.widget.send = observe
        # Bind the real creator loop before the other thread releases callbacks.
        view.widget._schedule_callback(0, lambda: None).cancel()
        content = {
            "event": "interaction_context_action",
            "action": "movie_seek",
            "request_id": "deferred-seek",
            "revision": view.movie._studio_revision,
            "time_ms": 400,
        }
        finish = {"stale": lambda: view.movie.set_duration(1200), "close": view.close}.get(disposition)
        worker, release = hold_scene(view, before_release=finish)
        try:
            view._handle_frontend_event(content)
            assert view.movie._studio is None and not view._frontend_requests._pending
            release.set()
            worker.join(1)
            for _ in range(100):
                owner = view.movie._studio
                if disposition == "close" or replies or owner and owner.job is not None:
                    break
                await asyncio.sleep(0.01)
            if disposition == "run":
                result = view.movie._studio.job.result
                await pending(view, asyncio.wrap_future(result))
                view.movie._studio.cancel({"job_id": "deferred-seek"})
                with pytest.raises(MovieStudioCancelled):
                    await asyncio.wrap_future(result)
            elif disposition == "stale":
                assert len(replies) == 1 and not replies[0]["ok"]
                assert "changed" in replies[0]["error_message"]
            else:
                assert view.closed and view.movie._studio is None
            assert not view._frontend_requests._pending
        finally:
            release.set()
            worker.join(1)

    asyncio.run(exercise())


@pytest.mark.parametrize("operation", ["capture_baseline_async", "review_rebase_async"])
@pytest.mark.parametrize("disposition", ["release", "timeout"])
def test_live_observation_commit_waits_within_its_original_deadline(view, monkeypatch, operation, disposition):
    async def exercise():
        module = importlib.import_module("molsysviewer.viewer._movie_baseline")
        native_observe = module.observe_movie_scene
        holder = []

        async def observe_then_contend(*args, **kwargs):
            observed = await native_observe(*args, **kwargs)
            holder.append(hold_scene(view))
            return observed

        # A scheduling barrier after the real protocol observation; no result
        # or molecular calculation is replaced by the test.
        monkeypatch.setattr(module, "observe_movie_scene", observe_then_contend)
        before = view.movie._timeline
        args = (1000,) if operation == "capture_baseline_async" else ()
        task = asyncio.create_task(getattr(view.movie, operation)(*args, timeout=0.5))
        try:
            await pending(view, task)
            request = next(iter(view._frontend_requests._pending.values()))
            view._handle_frontend_event(
                {
                    "event": "visual_state_snapshot",
                    "request_id": request.request_id,
                    "capture_revision": request.revision,
                    "capture_version": 2,
                    "ok": True,
                    "snapshot": {"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]},
                    "structure_index": 0,
                    "playback": {"fps": 30, "step_size": 1, "mode": "loop", "direction": "forward", "playing": False},
                    "movie_environment_capture": 1,
                    "movie_environment": {"background": {"color": 0}, "lighting": {"ambient": 0.4, "diffuse": 0.6}},
                }
            )
            for _ in range(100):
                if holder:
                    break
                if task.done():
                    task.result()
                await asyncio.sleep(0.001)
            assert holder and not task.done() and view.movie._timeline is before
            worker, release = holder[0]
            if disposition == "timeout":
                with pytest.raises(FrontendRequestError, match="request_timeout"):
                    await asyncio.wait_for(task, 2)
            else:
                release.set()
                worker.join(1)
                await task
        finally:
            if holder:
                holder[0][1].set()
                holder[0][0].join(1)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await asyncio.sleep(0)
        if disposition == "timeout":
            assert view.movie._timeline is before and view.movie._rebase_capture is None
        assert not view._frontend_requests._pending

    asyncio.run(exercise())


def test_export_rejects_a_plan_changed_while_the_real_encoder_is_prepared(view, tmp_path, monkeypatch):
    pytest.importorskip("imageio")

    async def exercise():
        module = importlib.import_module("molsysviewer.viewer._movie_export")
        native_encoder = module._encoder
        entered, release = asyncio.Event(), asyncio.Event()

        async def observed_encoder(*args, **kwargs):
            result = await native_encoder(*args, **kwargs)
            entered.set()
            await release.wait()
            return result

        monkeypatch.setattr(module, "_encoder", observed_encoder)
        path = tmp_path / "existing.zip"
        path.write_bytes(b"preserved destination")
        task = asyncio.create_task(view.movie.export_async(path, overwrite=True))
        try:
            await asyncio.wait_for(entered.wait(), 1)
            view.movie.set_duration(1200)
            release.set()
            with pytest.raises(FrontendRequestError, match="movie_export_superseded"):
                await asyncio.wait_for(task, 1)
        finally:
            release.set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert path.read_bytes() == b"preserved destination" and not view._frontend_requests._pending

    asyncio.run(exercise())


def test_actual_notebook_movie_guard_is_registered_in_core_ci():
    import yaml

    workflow = yaml.safe_load((Path(__file__).parents[1] / ".github/workflows/CI_e2e.yaml").read_text())
    steps = [step for job in workflow["jobs"].values() for step in job.get("steps", [])]
    selected = [step for step in steps if step.get("run") == "python tests/_jupyter_live_capture.py --profile movie"]
    assert len(selected) == 1
    assert "inputs.e2e_lane == 'core'" in selected[0]["if"]
    assert not selected[0].get("continue-on-error", False)


def test_public_pause_can_await_preview_owned_by_another_running_loop(view):
    async def exercise():
        entered, shared, errors = Event(), {}, []

        def run_preview():
            async def worker():
                task = asyncio.create_task(view.movie.play_async(loop=True))
                shared.update(loop=asyncio.get_running_loop(), task=task)
                await pending(view, task)
                entered.set()
                await task

            try:
                asyncio.run(worker())
            except asyncio.CancelledError:
                pass
            except BaseException as error:
                errors.append(error)

        worker = Thread(target=run_preview)
        worker.start()
        pause = None
        try:
            for _ in range(200):
                if entered.is_set() or errors:
                    break
                await asyncio.sleep(0.01)
            assert entered.is_set() and not errors
            pause = asyncio.create_task(view.movie.pause_async())
            await asyncio.sleep(0)
            if pause.done():
                pause.result()
            assert view.movie._playback.pause_requested
            request = next(iter(view._frontend_requests._pending.values()))
            view._handle_frontend_event(
                {
                    "event": "visual_state_snapshot",
                    "request_id": request.request_id,
                    "capture_revision": request.revision,
                    "capture_version": 2,
                    "ok": True,
                    "snapshot": {"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]},
                    "structure_index": 0,
                    "playback": {"fps": 30, "step_size": 1, "mode": "loop", "direction": "forward", "playing": False},
                }
            )
            result = await asyncio.wait_for(pause, 1)
            assert result["time_ms"] == 0 and result["structure_index"] == 0
        finally:
            if shared:
                try:
                    shared["loop"].call_soon_threadsafe(shared["task"].cancel)
                except RuntimeError:
                    pass
            if pause:
                await asyncio.gather(pause, return_exceptions=True)
            worker.join(1)
        assert not worker.is_alive() and not errors and not view._frontend_requests._pending

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("play_async", "movie_play"),
        ("seek_async", "movie_capture"),
        ("capture_baseline_async", "movie_capture"),
        ("export_async", "movie_export"),
    ],
)
def test_studio_status_receives_an_operation_started_from_python(view, tmp_path, operation, expected):
    async def exercise():
        if operation == "export_async":
            pytest.importorskip("imageio")
        projections = []
        native_send = view.widget.send

        def observe(message, buffers=None):
            if message.get("op") == "set_movie_state":
                projections.append(message)
            return native_send(message, buffers=buffers)

        view.widget.send = observe
        view.movie._studio_owner().inspect({"request_id": "runtime-reader"})
        args = {"seek_async": (400,), "capture_baseline_async": (1000,), "export_async": (tmp_path / "movie.zip",)}.get(
            operation, ()
        )
        task = asyncio.create_task(getattr(view.movie, operation)(*args))
        try:
            await pending(view, task)
            state = view.movie._studio_owner().state()
            assert state["busy"] == expected and state["job_id"] is None
            assert any(message["busy"] == expected for message in projections)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert projections[-1]["busy"] is None

    asyncio.run(exercise())
