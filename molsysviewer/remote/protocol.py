"""RRS0 validators for remote signaling and input packets."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

REMOTE_PROTOCOL_VERSION = 1
_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "remote_protocol.json"
_MANIFEST = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
if _MANIFEST.get("protocol_version") != REMOTE_PROTOCOL_VERSION:
    raise ValueError(
        f"remote_protocol.json protocol_version must be {REMOTE_PROTOCOL_VERSION}"
    )

SIGNALING_KINDS = frozenset(_MANIFEST["signaling_kinds"])
INPUT_KINDS = frozenset(_MANIFEST["input_kinds"])
POINTER_PHASES = frozenset(_MANIFEST["pointer_phases"])
POINTER_TYPES = frozenset(_MANIFEST["pointer_types"])
KEY_PHASES = frozenset(_MANIFEST["key_phases"])
MAX_KEY_CODE_LENGTH = int(_MANIFEST["max_key_code_length"])
MAX_VIEWPORT_DIMENSION = int(_MANIFEST["max_viewport_dimension"])
MAX_DEVICE_PIXEL_RATIO = float(_MANIFEST["max_device_pixel_ratio"])
MAX_SAFE_SEQUENCE = 2**53 - 1


@dataclass(frozen=True)
class RemotePacket:
    viewer_id: str
    session_id: str
    endpoint_id: str
    kind: str
    payload: Mapping[str, Any]
    message_id: str | None = None
    sequence: int | None = None
    timestamp_ms: float | None = None


@dataclass(frozen=True)
class PacketValidation:
    status: str  # accepted | rejected
    packet: RemotePacket | None = None
    reason: str | None = None
    detail: str | None = None


def _accepted(packet: RemotePacket) -> PacketValidation:
    return PacketValidation("accepted", packet=packet)


def _rejected(reason: str, detail: str) -> PacketValidation:
    return PacketValidation("rejected", reason=reason, detail=detail)


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _common_identity(
    value: Any,
    *,
    expected_viewer_id: str | None,
    expected_session_id: str | None,
    expected_endpoint_id: str | None,
) -> tuple[Mapping[str, Any], PacketValidation | None]:
    if not isinstance(value, Mapping):
        return {}, _rejected("malformed-packet", "Packet must be a mapping")
    version = value.get("protocolVersion")
    if not isinstance(version, int) or isinstance(version, bool):
        return value, _rejected("malformed-packet", "protocolVersion must be an integer")
    if version != REMOTE_PROTOCOL_VERSION:
        return value, _rejected("protocol-mismatch", f"Unsupported protocol {version}")
    for key in ("viewerId", "sessionId", "endpointId", "kind"):
        if not _non_empty(value.get(key)):
            return value, _rejected("malformed-packet", f"{key} must be a non-empty string")
    expected = {
        "viewerId": expected_viewer_id,
        "sessionId": expected_session_id,
        "endpointId": expected_endpoint_id,
    }
    for key, wanted in expected.items():
        if wanted is not None and value.get(key) != wanted:
            return value, _rejected(
                "identity-mismatch", f"{key} belongs to {value.get(key)!r}, expected {wanted!r}"
            )
    if not isinstance(value.get("payload"), Mapping):
        return value, _rejected("malformed-payload", "payload must be a mapping")
    return value, None


def validate_signaling_packet(
    value: Any,
    *,
    expected_viewer_id: str | None = None,
    expected_session_id: str | None = None,
    expected_endpoint_id: str | None = None,
) -> PacketValidation:
    value, failure = _common_identity(
        value,
        expected_viewer_id=expected_viewer_id,
        expected_session_id=expected_session_id,
        expected_endpoint_id=expected_endpoint_id,
    )
    if failure is not None:
        return failure
    if not _non_empty(value.get("messageId")):
        return _rejected("malformed-packet", "messageId must be a non-empty string")
    kind = value["kind"]
    payload = value["payload"]
    if kind not in SIGNALING_KINDS:
        return _rejected("unknown-kind", f"Unknown signaling kind {kind!r}")
    if kind in {"offer", "answer"}:
        if not _non_empty(payload.get("sdp")):
            return _rejected("malformed-payload", f"{kind} requires non-empty sdp")
    elif kind == "ice-candidate":
        if not _non_empty(payload.get("candidate")):
            return _rejected("malformed-payload", "ice-candidate requires candidate")
        sdp_mid = payload.get("sdpMid")
        if sdp_mid is not None and not _non_empty(sdp_mid):
            return _rejected("malformed-payload", "sdpMid must be null or non-empty")
        line = payload.get("sdpMLineIndex")
        if line is not None and (
            not isinstance(line, int) or isinstance(line, bool) or line < 0
        ):
            return _rejected("malformed-payload", "sdpMLineIndex must be null or non-negative")
    return _accepted(
        RemotePacket(
            viewer_id=value["viewerId"],
            session_id=value["sessionId"],
            endpoint_id=value["endpointId"],
            message_id=value["messageId"],
            kind=kind,
            payload=payload,
        )
    )


def validate_input_packet(
    value: Any,
    *,
    expected_viewer_id: str | None = None,
    expected_session_id: str | None = None,
    expected_endpoint_id: str | None = None,
) -> PacketValidation:
    value, failure = _common_identity(
        value,
        expected_viewer_id=expected_viewer_id,
        expected_session_id=expected_session_id,
        expected_endpoint_id=expected_endpoint_id,
    )
    if failure is not None:
        return failure
    sequence = value.get("sequence")
    if (
        not isinstance(sequence, int)
        or isinstance(sequence, bool)
        or not 0 <= sequence <= MAX_SAFE_SEQUENCE
    ):
        return _rejected("malformed-packet", "sequence must be a non-negative safe integer")
    timestamp_ms = value.get("timestampMs")
    if not _number(timestamp_ms) or timestamp_ms < 0:
        return _rejected("malformed-packet", "timestampMs must be finite and non-negative")
    viewport = value.get("viewport")
    if not isinstance(viewport, Mapping):
        return _rejected("malformed-packet", "viewport must be a mapping")
    for dimension in ("width", "height"):
        item = viewport.get(dimension)
        if not _number(item) or not 0 < item <= MAX_VIEWPORT_DIMENSION:
            return _rejected("malformed-packet", f"viewport.{dimension} is out of bounds")
    dpr = viewport.get("devicePixelRatio")
    if not _number(dpr) or not 0 < dpr <= MAX_DEVICE_PIXEL_RATIO:
        return _rejected("malformed-packet", "viewport.devicePixelRatio is out of bounds")

    kind = value["kind"]
    payload = value["payload"]
    if kind not in INPUT_KINDS:
        return _rejected("unknown-kind", f"Unknown input kind {kind!r}")
    payload_failure = _validate_input_payload(kind, payload)
    if payload_failure is not None:
        return payload_failure
    return _accepted(
        RemotePacket(
            viewer_id=value["viewerId"],
            session_id=value["sessionId"],
            endpoint_id=value["endpointId"],
            sequence=sequence,
            timestamp_ms=float(timestamp_ms),
            kind=kind,
            payload=payload,
        )
    )


def _validate_input_payload(kind: str, payload: Mapping[str, Any]) -> PacketValidation | None:
    modifiers = payload.get("modifiers", {})
    if not isinstance(modifiers, Mapping) or any(
        key not in {"alt", "ctrl", "meta", "shift"} or not isinstance(value, bool)
        for key, value in modifiers.items()
    ):
        return _rejected("malformed-payload", "modifiers must contain only boolean modifier keys")
    if kind in {"pointer", "wheel", "context-menu"}:
        for coordinate in ("x", "y"):
            item = payload.get(coordinate)
            if not _number(item) or not 0 <= item <= 1:
                return _rejected("malformed-payload", f"{coordinate} must be normalized to [0, 1]")
    if kind == "pointer":
        if payload.get("phase") not in POINTER_PHASES:
            return _rejected("malformed-payload", "pointer phase is invalid")
        if payload.get("pointerType") not in POINTER_TYPES:
            return _rejected("malformed-payload", "pointerType is invalid")
        pointer_id = payload.get("pointerId")
        if not isinstance(pointer_id, int) or isinstance(pointer_id, bool) or pointer_id < 0:
            return _rejected("malformed-payload", "pointerId must be non-negative")
        button = payload.get("button")
        buttons = payload.get("buttons")
        if not isinstance(button, int) or isinstance(button, bool) or not -1 <= button <= 5:
            return _rejected("malformed-payload", "button is out of bounds")
        if not isinstance(buttons, int) or isinstance(buttons, bool) or buttons < 0:
            return _rejected("malformed-payload", "buttons must be non-negative")
    elif kind == "wheel":
        for delta in ("deltaX", "deltaY"):
            if not _number(payload.get(delta)):
                return _rejected("malformed-payload", f"{delta} must be finite")
        if payload.get("deltaMode") not in {0, 1, 2}:
            return _rejected("malformed-payload", "deltaMode must be 0, 1 or 2")
    elif kind == "key":
        if payload.get("phase") not in KEY_PHASES:
            return _rejected("malformed-payload", "key phase is invalid")
        code = payload.get("code")
        if not _non_empty(code) or len(code) > MAX_KEY_CODE_LENGTH:
            return _rejected("malformed-payload", "key code is invalid")
        if not isinstance(payload.get("repeat"), bool):
            return _rejected("malformed-payload", "key repeat must be boolean")
    else:
        request_id = payload.get("requestId")
        if not _non_empty(request_id) or len(request_id) > 128:
            return _rejected("malformed-payload", "context-menu requestId is invalid")
    return None


__all__ = [
    "INPUT_KINDS",
    "KEY_PHASES",
    "POINTER_PHASES",
    "POINTER_TYPES",
    "REMOTE_PROTOCOL_VERSION",
    "SIGNALING_KINDS",
    "PacketValidation",
    "RemotePacket",
    "validate_input_packet",
    "validate_signaling_packet",
]
