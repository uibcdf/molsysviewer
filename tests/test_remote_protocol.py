"""RRS0 wire-shape guards before signaling/input reach a live endpoint."""

from __future__ import annotations

import pytest
from molsysviewer.remote import validate_input_packet, validate_signaling_packet


def signal(kind="offer", payload=None):
    return {
        "protocolVersion": 1,
        "viewerId": "view-a",
        "sessionId": "session-a",
        "endpointId": "browser-client:a",
        "messageId": "signal-1",
        "kind": kind,
        "payload": payload if payload is not None else {"sdp": "v=0\r\n"},
    }


def input_packet(kind="pointer", payload=None):
    return {
        "protocolVersion": 1,
        "viewerId": "view-a",
        "sessionId": "session-a",
        "endpointId": "browser-client:a",
        "sequence": 7,
        "timestampMs": 1234.5,
        "kind": kind,
        "viewport": {"width": 1920, "height": 1080, "devicePixelRatio": 1.5},
        "payload": payload
        if payload is not None
        else {
            "phase": "move",
            "pointerType": "mouse",
            "pointerId": 1,
            "x": 0.25,
            "y": 0.75,
            "button": -1,
            "buttons": 0,
            "modifiers": {"shift": False},
        },
    }


@pytest.mark.parametrize(
    ("kind", "payload"),
    [
        ("offer", {"sdp": "v=0\r\n"}),
        ("answer", {"sdp": "v=0\r\n"}),
        (
            "ice-candidate",
            {"candidate": "candidate:1 1 udp 1 127.0.0.1 9999 typ host", "sdpMid": "0", "sdpMLineIndex": 0},
        ),
        ("ice-complete", {}),
    ],
)
def test_signaling_vocabulary_accepts_valid_packets(kind, payload):
    result = validate_signaling_packet(
        signal(kind, payload),
        expected_viewer_id="view-a",
        expected_session_id="session-a",
        expected_endpoint_id="browser-client:a",
    )
    assert result.status == "accepted"
    assert result.packet.kind == kind


def test_signaling_rejects_stale_identity_and_malformed_candidate():
    stale = signal()
    stale["sessionId"] = "session-old"
    assert validate_signaling_packet(stale, expected_session_id="session-a").reason == "identity-mismatch"
    malformed = signal("ice-candidate", {"candidate": "", "sdpMLineIndex": -1})
    assert validate_signaling_packet(malformed).reason == "malformed-payload"


@pytest.mark.parametrize(
    ("kind", "payload"),
    [
        (
            "pointer",
            {
                "phase": "down",
                "pointerType": "pen",
                "pointerId": 2,
                "x": 0.5,
                "y": 0.25,
                "button": 0,
                "buttons": 1,
                "modifiers": {"ctrl": True},
            },
        ),
        (
            "wheel",
            {
                "x": 0.5,
                "y": 0.25,
                "deltaX": 0.0,
                "deltaY": -120.0,
                "deltaMode": 0,
                "modifiers": {},
            },
        ),
        (
            "key",
            {"phase": "down", "code": "KeyR", "repeat": False, "modifiers": {"shift": True}},
        ),
    ],
)
def test_input_vocabulary_accepts_pointer_wheel_and_key(kind, payload):
    result = validate_input_packet(input_packet(kind, payload))
    assert result.status == "accepted"
    assert result.packet.sequence == 7
    assert result.packet.kind == kind


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("sequence", -1),
        ("timestampMs", float("inf")),
        ("viewport.width", 0),
        ("viewport.devicePixelRatio", 17),
        ("payload.x", 1.01),
        ("payload.modifiers", {"shift": 1}),
    ],
)
def test_input_rejects_unbounded_or_ambiguous_values(path, value):
    packet = input_packet()
    target = packet
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    result = validate_input_packet(packet)
    assert result.status == "rejected"
    assert result.reason in {"malformed-packet", "malformed-payload"}


def test_input_identity_is_checked_before_it_can_reach_molstar():
    result = validate_input_packet(
        input_packet(),
        expected_viewer_id="view-other",
        expected_session_id="session-a",
        expected_endpoint_id="browser-client:a",
    )
    assert result.status == "rejected"
    assert result.reason == "identity-mismatch"
