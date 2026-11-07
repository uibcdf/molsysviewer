"""Prepare and validate a detached scene around an explicit renderer barrier."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass

from .frontend_requests import FrontendRequestError


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


async def capture_live_state(view, *, timeout: float) -> CapturedState:
    """Capture the primary renderer without blocking comm dispatch.

    A scene/frame change during the wait is explicitly refused. The molecular
    trajectory is borrowed, never copied; managed edits are checked before
    persistence. Arbitrary raw-array edits retain their existing explicit-sync
    contract and are not made observable by this helper.
    """
    with view._system_edits._locked():
        if view.closed:
            raise FrontendRequestError(reason="view_closed")
        if view._system_edits._blocked():
            raise FrontendRequestError(reason="system_edit_pending")
        if not view._ready:
            raise FrontendRequestError(reason="no_live_frontend")
        if 1 not in view._frontend_capabilities.get("visual_state_capture", []):
            raise FrontendRequestError(reason="capture_not_supported")
        state = deepcopy(view.export_state())
        key = _scene_key(state)
        captured = CapturedState(state, view.molsys, view._molecular_projection_revision, key)
        request = view._frontend_requests.begin(
            endpoint_id="primary", reply_event="visual_state_snapshot", revision=key, timeout=timeout
        )
        try:
            # Uses the normal structural-stream gate: capture cannot overtake
            # the trajectory whose frame it is meant to describe.
            view._send_runtime_only(
                {
                    "op": "request_visual_state",
                    "request_id": request.request_id,
                    "capture_revision": key,
                    "capture_timeout_ms": timeout * 1000,
                }
            )
        except BaseException:
            request.future.cancel()
            raise
    reply = await view._frontend_requests.wait(request)
    with view._system_edits._locked():
        captured.validate(view)
        expected = state.get("view", {}).get("structure_index")
        if expected is not None and (
            type(reply.get("structure_index")) is not int or reply["structure_index"] != expected
        ):
            raise FrontendRequestError(reason="frame_changed")
        state.setdefault("view", {})["camera"] = _camera(reply.get("snapshot"))
    return captured
