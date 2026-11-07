"""Prepare and validate a detached scene around an explicit renderer barrier."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass

from .frontend_requests import FrontendRequestError


def capture_endpoint(view, endpoint_id=None) -> str:
    """Resolve a connector-validated canvas, never a panel-only renderer."""
    host = f"widget-host:{view._binary_session_id}"
    if endpoint_id is None or isinstance(endpoint_id, str) and endpoint_id in {"primary", host}:
        return "primary"
    if not isinstance(endpoint_id, str) or view._endpoint_transfers.modes.get(endpoint_id) != "canvas":
        raise FrontendRequestError(reason="endpoint_closed")
    return endpoint_id


def _scene_key(state: dict) -> str:
    comparable = deepcopy(state)
    # Passive camera telemetry may arrive while awaiting the explicit reply.
    # It must neither invalidate nor replace the requested camera.
    comparable.get("view", {}).pop("camera", None)
    return hashlib.sha256(json.dumps(comparable, sort_keys=True, allow_nan=False).encode()).hexdigest()


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

    def validate(self, view) -> None:
        if view.closed:
            raise FrontendRequestError(reason="view_closed")
        if view._system_edits._blocked():
            raise FrontendRequestError(reason="system_edit_pending")
        if (
            view.molsys is not self.molecular_system
            or view._molecular_projection_revision != self.molecular_revision
            or _scene_key(view.export_state()) != self.scene_key
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
        if 1 not in view._frontend_capabilities.get("visual_state_capture", []):
            raise FrontendRequestError(reason="capture_not_supported")
        endpoint = capture_endpoint(view, endpoint_id)
        state = deepcopy(view.export_state())
        key = _scene_key(state)
        captured = CapturedState(state, view.molsys, view._molecular_projection_revision, key)
        request = view._frontend_requests.begin(
            endpoint_id=endpoint, reply_event="visual_state_snapshot", revision=key, timeout=timeout
        )
    return captured, request


def send_live_capture(view, request) -> None:
    """Keep a capture behind its own canvas's structural-stream gate."""
    import time

    target = None if request.endpoint_id == "primary" else request.endpoint_id
    message = {
        "op": "request_visual_state",
        "request_id": request.request_id,
        "capture_revision": request.revision,
        "capture_timeout_ms": max(1.0, min(30.0, request.deadline - time.monotonic()) * 1000),
    }
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


async def capture_live_state(view, *, timeout: float) -> CapturedState:
    """Await a coherent primary capture without retaining the edit lock."""
    captured, request = prepare_live_capture(view, timeout=timeout)
    send_live_capture(view, request)
    reply = await view._frontend_requests.wait(request)
    return finish_live_capture(view, captured, reply)
