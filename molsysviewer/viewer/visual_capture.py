"""Prepare and validate a detached scene around an explicit renderer barrier."""

from __future__ import annotations

import hashlib
import json
import math
import time
from contextvars import copy_context
from copy import deepcopy
from dataclasses import dataclass
from numbers import Real

from .frontend_requests import FrontendRequestError


def capture_endpoint(view, endpoint_id=None) -> str:
    """Resolve a connector-validated canvas, never a panel-only renderer."""
    host = f"widget-host:{view._binary_session_id}"
    if endpoint_id is None or isinstance(endpoint_id, str) and endpoint_id in {"primary", host}:
        return "primary"
    if not isinstance(endpoint_id, str) or view._endpoint_transfers.modes.get(endpoint_id) != "canvas":
        raise FrontendRequestError(reason="endpoint_closed")
    return endpoint_id


def _scene_key(state: dict, *, version: int = 1) -> str:
    comparable = deepcopy(state)
    # Passive camera telemetry may arrive while awaiting the explicit reply.
    # It must neither invalidate nor replace the requested camera.
    comparable.get("view", {}).pop("camera", None)
    if version == 2:
        temporal = comparable.get("view", {})
        temporal.pop("structure_index", None)
        temporal.pop("playback", None)
        if not temporal:
            comparable.pop("view", None)
        comparable.get("box_display", {}).pop("structure_index", None)
    return hashlib.sha256(json.dumps(comparable, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _analysis_keys(view) -> tuple:
    """Reuse the bounded saved-data fingerprint, without copying observations."""
    from ..interactions import _analysis_signature

    collection = getattr(view.molsys, "interactions", {})
    return tuple(sorted((name, _analysis_signature(result)) for name, result in collection.items()))


def _frame(view, value) -> int:
    import molsysmt as msm

    # An empty, shape-only canvas has the conventional frame zero.
    count = 0 if view.molsys is None else int(msm.get(view.molsys, n_structures=True, skip_digestion=True))
    if type(value) is not int or not 0 <= value < max(1, count):
        raise FrontendRequestError(reason="invalid_frame")
    return value


def _playback(record) -> dict:
    if not isinstance(record, dict):
        raise FrontendRequestError(reason="invalid_playback")
    if any(type(record.get(key)) is not int or not 0 < record[key] <= 2**53 - 1 for key in ("fps", "step_size")):
        raise FrontendRequestError(reason="invalid_playback")
    if (
        not isinstance(record.get("mode"), str)
        or record["mode"] not in {"loop", "once", "ping-pong"}
        or not isinstance(record.get("direction"), str)
        or record["direction"] not in {"forward", "backward"}
        or type(record.get("playing")) is not bool
    ):
        raise FrontendRequestError(reason="invalid_playback")
    return {key: record[key] for key in ("fps", "step_size", "mode", "direction", "playing")}


def _camera(snapshot) -> dict:
    if not isinstance(snapshot, dict):
        raise FrontendRequestError(reason="invalid_camera")
    for name in ("position", "target", "up"):
        values = snapshot.get(name)
        if (
            not isinstance(values, list)
            or len(values) != 3
            or any(
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in values
            )
        ):
            raise FrontendRequestError(reason="invalid_camera")
    try:
        # Reject nonportable values; round-trip also removes caller aliases.
        return json.loads(json.dumps(snapshot, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise FrontendRequestError(reason="invalid_camera") from error


@dataclass(frozen=True)
class CapturedState:
    state: dict
    molecular_system: object
    molecular_revision: int
    scene_key: str
    protocol_version: int = 1
    box_definition_revision: int = 0
    scene_edit_revision: int = 0
    analysis_keys: tuple = ()

    def validate(self, view) -> None:
        if view.closed:
            raise FrontendRequestError(reason="view_closed")
        if view._system_edits._blocked():
            raise FrontendRequestError(reason="system_edit_pending")
        if (
            view.molsys is not self.molecular_system
            or view._molecular_projection_revision != self.molecular_revision
            or (
                self.protocol_version == 2
                and (
                    view._box_definition_revision != self.box_definition_revision
                    or view.history._edit_revision != self.scene_edit_revision
                )
            )
            or _scene_key(view.export_state(), version=self.protocol_version) != self.scene_key
            or (self.protocol_version == 2 and _analysis_keys(view) != self.analysis_keys)
        ):
            raise FrontendRequestError(reason="scene_changed")


def prepare_live_capture(view, *, timeout: float, endpoint_id=None):
    """Freeze the recipe and reserve a reply before sending the barrier."""
    with view._system_edits._locked():
        if view.closed:
            raise FrontendRequestError(reason="view_closed")
        if view._system_edits._blocked():
            raise FrontendRequestError(reason="system_edit_pending")
        if not view._ready:
            raise FrontendRequestError(reason="no_live_frontend")
        versions = view._frontend_capabilities.get("visual_state_capture", [])
        version = 2 if 2 in versions else 1
        if version not in versions:
            raise FrontendRequestError(reason="capture_not_supported")
        endpoint = capture_endpoint(view, endpoint_id)
        state = deepcopy(view.export_state())
        key = _scene_key(state, version=version)
        captured = CapturedState(
            state,
            view.molsys,
            view._molecular_projection_revision,
            key,
            version,
            view._box_definition_revision,
            view.history._edit_revision,
            _analysis_keys(view) if version == 2 else (),
        )
        request = view._frontend_requests.begin(
            endpoint_id=endpoint, reply_event="visual_state_snapshot", revision=key, timeout=timeout
        )
    return captured, request


def send_live_capture(view, request, *, protocol_version: int = 1) -> None:
    """Keep a capture behind its own canvas's structural-stream gate."""
    import time

    target = None if request.endpoint_id == "primary" else request.endpoint_id
    message = {
        "op": "request_visual_state",
        "request_id": request.request_id,
        "capture_revision": request.revision,
        "capture_timeout_ms": max(1.0, min(30.0, request.deadline - time.monotonic()) * 1000),
    }
    if protocol_version == 2:
        message["capture_version"] = 2
    if target is not None:
        message["target_endpoint_id"] = target
    try:
        view._send_widget_message(message, defer_for_endpoint=target)
    except BaseException:
        view._frontend_requests.cancel(request)
        raise


def finish_live_capture(view, captured: CapturedState, reply: dict) -> CapturedState:
    with view._system_edits._locked():
        captured.validate(view)
        if captured.protocol_version == 2:
            if type(reply.get("capture_version")) is not int or reply["capture_version"] != 2:
                raise FrontendRequestError(reason="invalid_capture_version")
            frame = _frame(view, reply.get("structure_index"))
            camera = _camera(reply.get("snapshot"))
            playback = _playback(reply.get("playback"))
            box = captured.state.get("box_display")
            if box is not None:
                box_frame = _frame(view, reply.get("box_structure_index"))
            elif reply.get("box_structure_index") is not None:
                raise FrontendRequestError(reason="unexpected_box_display")
            # Validate the whole reply before touching even the detached recipe.
            captured.state.setdefault("view", {}).update(camera=camera, structure_index=frame, playback=playback)
            if box is not None:
                box["structure_index"] = box_frame
            return captured
        expected = captured.state.get("view", {}).get("structure_index")
        if expected is not None and (
            type(reply.get("structure_index")) is not int or reply["structure_index"] != expected
        ):
            raise FrontendRequestError(reason="frame_changed")
        captured.state.setdefault("view", {})["camera"] = _camera(reply.get("snapshot"))
    return captured


def write_captured_state(view, captured: CapturedState, path, *, kind: str) -> None:
    """One final validation and the same atomic writers for Python and Studio."""
    with view._system_edits._locked():
        captured.validate(view)
        if kind == "state":
            from .state import _write_state_file

            _write_state_file(path, captured.state)
        elif kind == "session":
            from ..session import _write_session

            _write_session(view, path, state=captured.state)
        else:
            raise ValueError("Unknown work-file kind.")


async def _capture_owned_call(view, operation, *, deadline):
    """Await existing scene ownership on the caller's loop, without polling."""
    import asyncio

    loop = asyncio.get_running_loop()
    result = loop.create_future()
    caller_context = copy_context()

    def retry():
        if not result.done() and not loop.is_closed():
            try:
                loop.call_soon_threadsafe(attempt, context=caller_context)
            except RuntimeError:
                if not loop.is_closed():
                    raise

    def attempt():
        if result.done():
            return
        try:
            if time.monotonic() >= deadline:
                raise FrontendRequestError(reason="request_timeout")
            with view._system_edits._locked(defer=retry) as acquired:
                if not acquired:
                    return
                value = operation()
            result.set_result(value)
        except BaseException as error:
            result.set_exception(error)

    attempt()
    try:
        return await asyncio.wait_for(result, max(0.0, deadline - time.monotonic()))
    except TimeoutError as error:
        raise FrontendRequestError(reason="request_timeout") from error


async def save_live_file(view, path, *, kind: str, timeout: float) -> None:
    """Acquire, capture and commit without holding ownership across a yield."""
    if isinstance(timeout, bool) or not isinstance(timeout, Real) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Capture timeout must be finite and positive.")
    deadline = time.monotonic() + timeout
    require_host = getattr(view.widget, "_require_async_capture_host", None)
    if callable(require_host):
        require_host()

    request = None

    def begin():
        nonlocal request
        captured, request = prepare_live_capture(view, timeout=max(1e-9, deadline - time.monotonic()))
        send_live_capture(view, request, protocol_version=captured.protocol_version)
        return captured, request

    try:
        captured, request = await _capture_owned_call(view, begin, deadline=deadline)
        reply = await view._frontend_requests.wait(request)

        def commit():
            finish_live_capture(view, captured, reply)
            write_captured_state(view, captured, path, kind=kind)

        await _capture_owned_call(view, commit, deadline=deadline)
    finally:
        if request is not None:
            view._frontend_requests.cancel(request)
