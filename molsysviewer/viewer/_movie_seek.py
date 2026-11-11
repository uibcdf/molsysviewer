"""Apply an evaluated Movie sample through the live scene owners."""

import math
import time
from numbers import Real
from uuid import uuid4

from ._movie_appearance import appearance_commands
from ._movie_timeline import _VISIBILITY_DOMAINS
from .frontend_requests import FrontendRequestError
from .visual_capture import (
    _capture_owned_call,
    finish_live_capture,
    freeze_live_capture,
    live_capture_version,
    send_live_capture,
)


def _visibility_owners(view, targets):
    owners = {}
    for domain, tag in targets:
        target = view.whole if domain == "whole" else getattr(view, _VISIBILITY_DOMAINS[domain]).get(tag)
        if target is None:
            raise ValueError(f"Movie scene target {(domain, tag)!r} is missing.")
        owners[domain, tag] = target
    return owners


def _visibility_commands(owners, visibility):
    commands = []
    for row in visibility:
        domain, tag = row["domain"], row["tag"]
        target = owners[domain, tag]
        visible = target.visible if domain == "whole" else not target._hidden
        if visible == row["visible"]:
            continue
        commands.append(target.show if row["visible"] else target.hide)
    return commands


def _apply_sample(movie, timeline, sample, visibility_commands, *, take_motion=True):
    view = movie._view
    molecular_revision = view._molecular_projection_revision
    camera_revision = view._camera_projection_revision

    def navigate(operation, *args):
        scene_revision = view.history._edit_revision
        navigation_revision = view.player._intent_revision + 1
        operation(*args, skip_digestion=True)
        # Player callbacks can issue their own scene commands synchronously.
        # Retire the seek before sending more commands for an obsolete target.
        if (
            view.closed
            or movie._timeline is not timeline
            or view._molecular_projection_revision != molecular_revision
            or view._camera_projection_revision != camera_revision
            or view.history._edit_revision != scene_revision
            or view.player._intent_revision != navigation_revision
        ):
            raise FrontendRequestError(reason="movie_seek_superseded")

    if take_motion:
        view._send_runtime_only({"op": "stop_movie"})
        # Disabling spin also disables swing in the existing scene motion owner.
        view.scene.spin(False, skip_digestion=True)
        navigate(view.player.pause)
    appearance = appearance_commands(view, timeline, sample)
    if appearance or visibility_commands:
        with view.history._atomic_operation(("movie", "", "seek" if take_motion else "preview")):
            for command in appearance:
                command()
            for command in visibility_commands:
                command(skip_digestion=True)
    # Send even at the same cached Python index: the canvas may have advanced
    # during playback. Ordinary frame notifications still ignore a no-op.
    if take_motion or view.player.index != sample["structure_index"]:
        navigate(view.player.go_to_structure, sample["structure_index"])
    view.camera.set_snapshot(sample["camera"], skip_digestion=True)


def _matching_pose(actual, expected):
    return all(
        math.isclose(value, target, rel_tol=1e-9, abs_tol=1e-6)
        for axis, vector in expected.items()
        for value, target in zip(actual[axis], vector, strict=True)
    )


def _confirm_sample(sample, *, camera, structure_index, playing):
    if type(structure_index) is not int or structure_index != sample["structure_index"] or playing is not False:
        raise FrontendRequestError(reason="movie_structure_not_applied")
    if not _matching_pose(camera, sample["camera"]):
        raise FrontendRequestError(reason="movie_camera_not_applied")


async def seek_movie(movie, time_ms, *, timeout, export_job=None, movie_frame=None):
    if isinstance(timeout, bool) or not isinstance(timeout, Real) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Movie seek timeout must be finite and positive.")
    view = movie._view
    deadline = time.monotonic() + timeout
    require_host = getattr(view.widget, "_require_async_capture_host", None)
    if callable(require_host):
        require_host()

    request = None

    def begin():
        nonlocal request
        version = live_capture_version(view, required=2)
        if (
            movie._seek_request is not None
            or movie._playback is not None
            or view._movie_export_frames is not None
            or movie._export_job is not export_job
        ):
            raise FrontendRequestError(reason="movie_operation_pending")
        timeline = movie._require_timeline()
        if timeline.has_appearance and 1 not in view._frontend_capabilities.get("movie_appearance", []):
            raise FrontendRequestError(reason="movie_appearance_not_supported")
        if export_job is not None:
            export_job.validate(movie)
        scene = view.export_state(skip_digestion=True)
        timeline.check_binding(view._source_state_binding(), scene)
        sample = timeline.evaluate(time_ms, tracked_visibility=True)
        owners = _visibility_owners(view, timeline.visibility_targets())
        commands = _visibility_commands(owners, sample["visibility"])

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FrontendRequestError(reason="request_timeout")
        request = view._frontend_requests.begin(
            endpoint_id="primary", reply_event="visual_state_snapshot", revision=uuid4().hex, timeout=remaining
        )
        movie._seek_request = request
        _apply_sample(movie, timeline, sample, commands)
        captured = freeze_live_capture(view, version=version)
        revisions = (view._camera_projection_revision, view.player._intent_revision)
        send_live_capture(view, request, protocol_version=version, movie_frame=movie_frame)
        return timeline, sample, captured, revisions

    try:
        timeline, sample, captured, revisions = await _capture_owned_call(view, begin, deadline=deadline)
        reply = await view._frontend_requests.wait(request)

        def confirm():
            if timeline is not movie._timeline or revisions != (
                view._camera_projection_revision,
                view.player._intent_revision,
            ):
                raise FrontendRequestError(reason="movie_seek_superseded")
            drawn = finish_live_capture(view, captured, reply).state["view"]
            _confirm_sample(
                sample,
                camera=drawn["camera"],
                structure_index=drawn["structure_index"],
                playing=drawn["playback"]["playing"],
            )
            if movie_frame is not None:
                frame = reply.get("movie_frame")
                if not isinstance(frame, dict) or any(
                    type(frame.get(key)) is not type(value) or frame.get(key) != value
                    for key, value in movie_frame.items()
                ):
                    raise FrontendRequestError(reason="invalid_movie_frame")
                from ._movie_playback import _revisions

                export_job.revisions = _revisions(view)
                return sample, frame
            return sample

        return await _capture_owned_call(view, confirm, deadline=deadline)
    finally:
        if request is not None:
            try:
                view._frontend_requests.cancel(request)
            finally:
                if movie._seek_request is request:
                    movie._seek_request = None
