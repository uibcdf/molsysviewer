"""Capture a new Movie baseline through the existing coherent draw owner."""

import math
import time
from copy import deepcopy
from numbers import Real

from ._movie_timeline import MOVIE_TIMELINE_VERSION, _duration, _MovieTimeline
from .frontend_requests import FrontendRequestError
from .visual_capture import (
    _capture_owned_call,
    finish_live_capture,
    live_capture_version,
    prepare_live_capture,
    send_live_capture,
)


async def capture_baseline(movie, duration_ms, *, timeout):
    duration = _duration(duration_ms)
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
        if any(
            value is not None
            for value in (movie._seek_request, movie._playback, movie._export_job, view._movie_export_frames)
        ):
            raise FrontendRequestError(reason="movie_operation_pending")
        binding = view._source_state_binding()
        if binding is None:
            raise ValueError("Load a molecular system before capturing a Movie baseline.")
        original = movie._timeline, movie._keyframes, deepcopy(movie._keyframes)
        captured, request = prepare_live_capture(view, timeout=max(1e-9, deadline - time.monotonic()))
        movie._seek_request = request
        send_live_capture(view, request, protocol_version=2)
        return captured, binding, original

    try:
        captured, binding, original = await _capture_owned_call(view, begin, deadline=deadline)
        reply = await view._frontend_requests.wait(request)

        def check_recipe():
            if (
                movie._timeline is not original[0]
                or movie._keyframes is not original[1]
                or movie._keyframes != original[2]
            ):
                raise FrontendRequestError(reason="movie_baseline_superseded")

        def prepare():
            check_recipe()
            scene = finish_live_capture(view, captured, reply).state
            timeline = _MovieTimeline(
                {
                    "molsysmovie_version": MOVIE_TIMELINE_VERSION,
                    "duration_ms": duration,
                    "units": {"time": "ms", "camera_length": "angstrom"},
                    "baseline": {"scene": scene, "camera": scene["view"]["camera"], "binding": binding},
                    "tracks": [],
                }
            )
            return timeline, timeline.to_dict()

        timeline, recipe = await _capture_owned_call(view, prepare, deadline=deadline)
        # No mutation inside a deferred grant: cancellation can be delivered
        # after the owner prepares data but before this caller resumes.
        # Revalidate and install synchronously, with no subsequent kernel yield.
        with view._system_edits._locked():
            if time.monotonic() >= deadline:
                raise FrontendRequestError(reason="request_timeout")
            check_recipe()
            captured.validate(view)
            movie._install_timeline(timeline)
            return recipe
    finally:
        if request is not None:
            try:
                view._frontend_requests.cancel(request)
            finally:
                if movie._seek_request is request:
                    movie._seek_request = None
