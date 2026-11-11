"""Bounded live Movie preview driven by the primary renderer's draw clock."""

import asyncio
import math
import time
from copy import deepcopy
from functools import partial
from numbers import Real
from uuid import uuid4

from ._movie_seek import _apply_sample, _confirm_sample, _matching_pose, _visibility_commands, _visibility_owners
from .frontend_requests import FrontendRequestError
from .visual_capture import _camera, _capture_owned_call, live_capture_version, send_live_capture


def _revisions(view):
    return (
        view._molecular_projection_revision,
        view.history._edit_revision,
        view._box_definition_revision,
        view._camera_projection_revision,
        view.player._intent_revision,
    )


class _MoviePlayback:
    def __init__(self, movie, *, loop, start_time_ms):
        view = movie._view
        live_capture_version(view, required=2)
        if 1 not in view._frontend_capabilities.get("movie_preview", []):
            raise FrontendRequestError(reason="movie_preview_not_supported")
        if (
            movie._playback is not None
            or movie._seek_request is not None
            or movie._export_job is not None
            or view._movie_export_frames is not None
        ):
            raise FrontendRequestError(reason="movie_operation_pending")
        self.timeline = movie._require_timeline()
        scene = view.export_state(skip_digestion=True)
        self.timeline.check_binding(view._source_state_binding(), scene)
        self.owners = _visibility_owners(view, self.timeline.visibility_targets())
        self.sample = self.timeline.evaluate(start_time_ms, tracked_visibility=True)
        self.id = uuid4().hex
        self.loop = loop
        self.revisions = _revisions(view)
        self.done = asyncio.get_running_loop().create_future()
        self.pause_requested = False
        self.last = None
        self.error = None
        self.request = None

    def validate(self, movie):
        view = movie._view
        live_capture_version(view, required=2)
        if self.timeline is not movie._timeline or self.revisions != _revisions(view):
            raise FrontendRequestError(reason="movie_preview_superseded")

    def submit(self, movie, deadline):
        if self.pause_requested:
            return False
        self.validate(movie)
        view = movie._view
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FrontendRequestError(reason="request_timeout")
        self.request = view._frontend_requests.begin(
            endpoint_id="primary", reply_event="visual_state_snapshot", revision=self.id, timeout=remaining
        )
        initial = self.last is None
        _apply_sample(
            movie,
            self.timeline,
            self.sample,
            _visibility_commands(self.owners, self.sample["visibility"]),
            take_motion=initial,
        )
        self.revisions = _revisions(view)
        clock = {"id": self.id}
        if initial:
            clock.update(
                recipe=self.timeline.preview_recipe(),
                start_time_ms=self.sample["time_ms"],
                loop=self.loop,
            )
        send_live_capture(view, self.request, protocol_version=2, movie_preview=clock)
        return True

    def confirm(self, movie, reply):
        self.validate(movie)
        playback = reply.get("playback")
        if (
            type(reply.get("capture_version")) is not int
            or reply["capture_version"] != 2
            or not isinstance(playback, dict)
        ):
            raise FrontendRequestError(reason="invalid_capture_version")
        _confirm_sample(
            self.sample,
            camera=_camera(reply.get("snapshot")),
            structure_index=reply.get("structure_index"),
            playing=playback.get("playing"),
        )
        self.last = self.sample
        self.request = None
        if self.pause_requested or (not self.loop and self.last["time_ms"] == self.timeline.duration_ms):
            return False

        next_sample = reply.get("movie_next_sample")
        try:
            expected = self.timeline.evaluate(next_sample["time_ms"], tracked_visibility=True)
            if (
                not self.loop
                and expected["time_ms"] < self.last["time_ms"]
                or type(next_sample["structure_index"]) is not int
                or next_sample["structure_index"] != expected["structure_index"]
                or next_sample["visibility"] != expected["visibility"]
                or not _matching_pose(_camera(next_sample["camera"]), expected["camera"])
            ):
                raise ValueError("The renderer sample differs from the accepted Movie recipe.")
        except (KeyError, TypeError, ValueError, FrontendRequestError) as error:
            raise FrontendRequestError(reason="invalid_movie_preview_sample") from error
        self.sample = expected
        return True


async def play_movie(movie, *, loop, start_time_ms, timeout):
    if isinstance(timeout, bool) or not isinstance(timeout, Real) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Movie preview timeout must be finite and positive.")
    view = movie._view
    require_host = getattr(view.widget, "_require_async_capture_host", None)
    if callable(require_host):
        require_host()

    owner = None

    def begin():
        nonlocal owner
        owner = _MoviePlayback(movie, loop=loop, start_time_ms=start_time_ms)
        movie._playback = owner

    try:
        await _capture_owned_call(view, begin, deadline=time.monotonic() + timeout)
        while True:
            deadline = time.monotonic() + timeout
            submitted = await _capture_owned_call(view, partial(owner.submit, movie, deadline), deadline=deadline)
            if not submitted:
                return owner.last
            reply = await view._frontend_requests.wait(owner.request)
            if not await _capture_owned_call(view, partial(owner.confirm, movie, reply), deadline=deadline):
                return owner.last
    except asyncio.CancelledError:
        if owner is not None:
            owner.error = FrontendRequestError(reason="movie_preview_cancelled")
        raise
    except Exception as error:
        if owner is not None:
            owner.error = error
        raise
    finally:
        if owner is not None:
            try:
                if owner.request is not None:
                    view._frontend_requests.cancel(owner.request)
                if not view.closed:
                    view._send_widget_message({"op": "stop_movie", "movie_preview_id": owner.id})
            finally:
                movie._playback = None
                owner.done.set_result(None)


async def pause_movie(movie):
    owner = movie._playback
    if owner is None:
        return None
    owner.pause_requested = True
    await asyncio.shield(owner.done)
    if owner.error is not None:
        raise owner.error
    return deepcopy(owner.last)
