"""Capture a new Movie baseline through the existing coherent draw owner."""

import math
import time
from copy import deepcopy
from dataclasses import dataclass
from numbers import Real

from ._movie_endpoint import check_movie_revision, movie_endpoint
from ._movie_environment import finish_environment_capture, require_environment_capture
from ._movie_timeline import MOVIE_TIMELINE_VERSION, _duration, _MovieTimeline
from .frontend_requests import FrontendRequestError
from .visual_capture import (
    _capture_owned_call,
    live_capture_version,
    prepare_live_capture,
    send_live_capture,
)


def check_idle(movie):
    if any(
        value is not None
        for value in (movie._seek_request, movie._playback, movie._export_job, movie._view._movie_export_frames)
    ):
        raise FrontendRequestError(reason="movie_operation_pending")


@dataclass(frozen=True)
class MovieObservation:
    captured: object
    binding: dict
    original: tuple
    deadline: float
    environment_capture: dict

    def check_recipe(self, movie):
        if (
            movie._timeline is not self.original[0]
            or movie._keyframes is not self.original[1]
            or movie._keyframes != self.original[2]
        ):
            raise FrontendRequestError(reason="movie_baseline_superseded")

    def validate(self, movie, *, delivery=False):
        check_idle(movie)
        if delivery and time.monotonic() >= self.deadline:
            raise FrontendRequestError(reason="request_timeout")
        self.check_recipe(movie)
        self.captured.validate(movie._view)


async def observe_movie_scene(movie, *, timeout, require_baseline=False):
    """Own one coherent observation, without installing a recipe or review."""
    if isinstance(timeout, bool) or not isinstance(timeout, Real) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Movie baseline timeout must be finite and positive.")
    view = movie._view
    require_host = getattr(view.widget, "_require_async_capture_host", None)
    if callable(require_host):
        require_host()
    deadline = time.monotonic() + timeout
    request = None

    def begin():
        nonlocal request
        live_capture_version(view, required=2)
        check_movie_revision(movie)
        require_environment_capture(view)
        check_idle(movie)
        if require_baseline:
            movie._require_timeline()
        binding = view._source_state_binding()
        if binding is None:
            raise ValueError("Load a molecular system before capturing a Movie baseline.")
        original = movie._timeline, movie._keyframes, deepcopy(movie._keyframes)
        captured, request = prepare_live_capture(
            view, timeout=max(1e-9, deadline - time.monotonic()), endpoint_id=movie_endpoint(view)
        )
        movie._seek_request = request
        send_live_capture(view, request, protocol_version=2, movie_environment_capture=True)
        return captured, binding, original

    try:
        captured, binding, original = await _capture_owned_call(view, begin, deadline=deadline)
        reply = await view._frontend_requests.wait(request)

        def prepare():
            metadata = finish_environment_capture(view, captured, reply)
            observation = MovieObservation(captured, binding, original, deadline, metadata)
            observation.check_recipe(movie)
            return observation

        # A deferred grant prepares data only. The resumed public operation
        # validates and installs synchronously, with no subsequent kernel yield.
        return await _capture_owned_call(view, prepare, deadline=deadline)
    finally:
        if request is not None:
            try:
                view._frontend_requests.cancel(request)
            finally:
                if movie._seek_request is request:
                    movie._seek_request = None


async def capture_baseline(movie, duration_ms, *, timeout):
    duration = _duration(duration_ms)
    observation = await observe_movie_scene(movie, timeout=timeout)
    with movie._view._system_edits._locked():
        observation.validate(movie, delivery=True)
        scene = observation.captured.state
        timeline = _MovieTimeline(
            {
                "molsysmovie_version": MOVIE_TIMELINE_VERSION,
                "duration_ms": duration,
                "units": {"time": "ms", "camera_length": "angstrom"},
                "baseline": {
                    "scene": scene,
                    "camera": scene["view"]["camera"],
                    "binding": observation.binding,
                    "environment_capture": observation.environment_capture,
                },
                "tracks": [],
            }
        )
        recipe = timeline.to_dict()
        movie._install_timeline(timeline)
        return recipe
