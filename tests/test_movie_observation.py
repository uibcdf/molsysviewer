"""Protocol receiving on real molecular Views; actual native draws are separate."""

import asyncio
import json
import runpy
from copy import deepcopy
from pathlib import Path
from threading import Event, Thread

import pytest
from molsysviewer.interactions import _analysis_signature
from molsysviewer.viewer._movie_seek import _apply_sample, _visibility_commands, _visibility_owners
from molsysviewer.viewer.frontend_requests import FrontendRequestError

import molsysviewer as msv

helpers = runpy.run_path(str(Path(__file__).with_name("test_movie_baseline.py")))
pending, reply = helpers["pending"], helpers["reply"]
ENVIRONMENT = {"background": {"color": 0x123456}, "lighting": {"ambient": 0.35, "diffuse": 0.65}}


@pytest.fixture
def authored():
    with helpers["make_appearance_view"]() as view:
        view._ready = True
        view._frontend_capabilities = {
            "visual_state_capture": [2],
            "movie_appearance": [1],
            "movie_environment_capture": [1],
        }
        yield view


async def observe(view, method=None, *, frame=2):
    task, request = await pending(view, (method or view.movie.review_rebase_async)())
    answer = reply(view, request, frame=frame)
    answer["snapshot"] = {"position": [2, 3, 40], "target": [2, 3, 0], "up": [0, 1, 0]}
    answer["movie_environment"] = deepcopy(ENVIRONMENT)
    view._handle_frontend_event(answer)
    return await task


def test_live_review_is_detached_observed_and_explicitly_accepted(authored):
    before, recipe = authored.export_state(), authored.movie.to_dict()
    science = _analysis_signature(authored.interactions.get_analysis("story-hbonds"))
    review = asyncio.run(observe(authored))
    baseline = review["candidate"]["baseline"]
    assert review["can_apply"] and baseline["scene"]["environment"] == ENVIRONMENT
    assert baseline["scene"]["view"]["structure_index"] == 2
    assert baseline["camera"]["position"] == [2, 3, 40]
    assert baseline["environment_capture"] == {"version": 1, "intent": before["environment"]}
    assert authored.export_state() == before and authored.movie.to_dict() == recipe
    authored.movie.rebase(json.loads(json.dumps(review)))
    assert authored.movie.to_dict()["tracks"] == recipe["tracks"]
    assert authored.movie.to_dict()["baseline"] == baseline
    assert authored.export_state() == before
    assert _analysis_signature(authored.interactions.get_analysis("story-hbonds")) == science
    authored.movie.validate()
    assert authored.movie._rebase_capture is None
    review["candidate"]["baseline"]["scene"]["environment"]["lighting"]["ambient"] = 1
    assert authored.movie.to_dict()["baseline"]["scene"]["environment"] == ENVIRONMENT


@pytest.mark.parametrize("change", ["edited", "scene", "recipe", "foreign", "superseded"])
def test_live_reviews_reject_edits_changes_foreign_and_old_tickets(authored, change):
    review = asyncio.run(observe(authored))
    if change == "edited":
        review["candidate"]["baseline"]["scene"]["environment"]["background"]["color"] += 1
    elif change == "scene":
        authored.annotations.add("New work", atom_indices=[1], tag="later")
    elif change == "recipe":
        authored.movie.set_duration(2000)
    elif change == "foreign":
        review["capture"]["id"] = "another-view-ticket"
    else:
        asyncio.run(observe(authored))
    before, recipe = authored.export_state(), authored.movie.to_dict()
    with pytest.raises((ValueError, FrontendRequestError)):
        authored.movie.rebase(review)
    assert authored.export_state() == before and authored.movie.to_dict() == recipe


def test_navigation_keeps_the_reviewed_moment_instead_of_recapturing_it(authored):
    review = asyncio.run(observe(authored))
    expected = deepcopy(review["candidate"]["baseline"])
    authored.player.go_to_structure(1)
    authored.camera.set_snapshot({"position": [0, 0, 50], "target": [0, 0, 0], "up": [0, 1, 0]})
    authored.movie.rebase(review)
    assert authored.movie.to_dict()["baseline"] == expected
    authored.movie.validate()


def test_serialized_observation_metadata_rejects_invalid_records_without_replacing(authored):
    original = authored.movie.to_dict()
    for metadata in [
        {"version": True, "intent": {}},
        {"version": 2, "intent": {}},
        {"version": 1, "intent": {}, "extra": True},
        {"version": 1, "intent": {"lighting": {"ambient": 2}}},
    ]:
        invalid = deepcopy(original)
        invalid["baseline"]["environment_capture"] = metadata
        with pytest.raises(ValueError):
            authored.movie.from_dict(invalid)
        assert authored.movie.to_dict() == original


@pytest.mark.parametrize("termination", ["cancel", "timeout", "scene", "recipe", "close"])
def test_failed_live_review_preserves_previous_review_and_latest_recipe(authored, termination):
    previous = asyncio.run(observe(authored))
    cached = authored.movie._rebase_capture

    async def exercise():
        task, request = await pending(
            authored, authored.movie.review_rebase_async(timeout=0.02 if termination == "timeout" else 5)
        )
        if termination == "scene":
            authored.annotations.add("New work", atom_indices=[1], tag="later")
        elif termination == "recipe":
            authored.movie.set_duration(2000)
        elif termination == "close":
            authored.close()
        expected = deepcopy(authored.movie._timeline.to_dict())
        if termination == "cancel":
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            if termination != "timeout":
                authored._handle_frontend_event(reply(authored, request))
            with pytest.raises(FrontendRequestError):
                await task
        assert authored.movie._timeline.to_dict() == expected
        assert not authored._frontend_requests._pending and authored.movie._seek_request is None
        if termination != "close":
            authored._handle_frontend_event(reply(authored, request))
        if termination in {"cancel", "timeout", "scene"}:
            assert authored.movie._rebase_capture is cached
        if termination in {"cancel", "timeout"}:
            authored.movie.rebase(previous)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        {},
        {"background": {"mode": "dark"}},
        {"background": {"color": True}, "lighting": {"ambient": 0.4, "diffuse": 0.6}},
        {"background": {"color": 0}, "lighting": {"ambient": 2, "diffuse": 0.6}},
    ],
)
def test_bad_observed_environment_cannot_replace_recipe(authored, invalid):
    async def exercise():
        before = authored.movie.to_dict()
        task, request = await pending(authored, authored.movie.capture_baseline_async(1000))
        answer = reply(authored, request)
        answer["movie_environment"] = invalid
        authored._handle_frontend_event(answer)
        with pytest.raises(FrontendRequestError, match="invalid_movie_environment_capture"):
            await task
        assert authored.movie.to_dict() == before and authored.movie._seek_request is None

    asyncio.run(exercise())


@pytest.mark.parametrize("versions", [None, [], [True], [2], 1])
def test_missing_capability_refuses_before_reserving_or_replacing(authored, versions):
    authored._frontend_capabilities["movie_environment_capture"] = versions
    before = authored.movie.to_dict()
    for operation in [authored.movie.review_rebase_async(), authored.movie.capture_baseline_async(1000)]:
        with pytest.raises(FrontendRequestError, match="movie_environment_capture_not_supported"):
            asyncio.run(operation)
    assert authored.movie.to_dict() == before and not authored._frontend_requests._pending


@pytest.mark.parametrize("operation", ["reload", "reset", "close"])
def test_stale_observation_releases_its_system_reference(authored, operation):
    asyncio.run(observe(authored))
    assert authored.movie._rebase_capture is not None
    if operation == "reload":
        with msv.demo["dialanine"] as source:
            authored.load(source.molsys, mode="replace")
    elif operation == "reset":
        authored.reset_viewer()
    else:
        authored.close()
    assert authored.movie._rebase_capture is None


def test_observed_constants_replay_and_survive_session_without_declared_defaults(tmp_path):
    async def exercise(view):
        # A real demo View has no explicitly configured environment.
        assert not view.export_state().get("environment")
        view._ready = True
        view._frontend_capabilities = {"visual_state_capture": [2], "movie_environment_capture": [1]}
        task, request = await pending(view, view.movie.capture_baseline_async(1000))
        answer = {
            **reply(view, request),
            "movie_environment": deepcopy(ENVIRONMENT),
        }
        view._handle_frontend_event(answer)
        await task

    with msv.demo["pentalanine"] as view:
        # reply() obtains its reference pose from this ordinary headless recipe.
        view.movie.set_baseline(1000, camera={"position": [0, 0, 40], "target": [0, 0, 0], "up": [0, 1, 0]})
        asyncio.run(exercise(view))
        view.movie.validate()
        path = tmp_path / "observed.msv"
        view.save_session(path)
    with msv.load_session(path) as restored:
        restored.movie.validate()
        sample = restored.movie.evaluate(0)
        _apply_sample(restored.movie, restored.movie._timeline, sample, [])
        assert restored.export_state()["environment"] == ENVIRONMENT
        restored.movie.validate()
        restored.scene.set_lighting(ambient=0.9)
        with pytest.raises(ValueError, match="untracked changes"):
            restored.movie.validate()


def test_cancellation_after_preparation_cannot_publish_a_review(authored):
    async def exercise():
        task, request = await pending(authored, authored.movie.review_rebase_async())
        expected = authored.movie.to_dict()
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
            asyncio.get_running_loop().call_soon(task.cancel)
            with pytest.raises(asyncio.CancelledError):
                await task
            assert authored.movie.to_dict() == expected and authored.movie._rebase_capture is None
            assert authored.movie._seek_request is None and not authored._frontend_requests._pending
        finally:
            release.set()
            worker.join(timeout=2)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


def test_observed_environment_tracks_override_captured_constants(authored):
    review = asyncio.run(observe(authored))
    authored.movie.rebase(review)
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    sample = authored.movie._timeline.evaluate(500, tracked_visibility=True)
    _apply_sample(
        authored.movie,
        authored.movie._timeline,
        sample,
        _visibility_commands(owners, sample["visibility"], authored.movie._timeline),
    )
    actual = authored.export_state()["environment"]
    desired = {row["property"]: row["value"] for row in sample["appearance"] if row["domain"] == "scene"}
    assert actual == {"background": {"color": desired["background"]}, "lighting": desired["lighting"]}
    authored.movie.validate()
