import assert from "node:assert";
import test from "node:test";

import {
    INPUT_KINDS,
    SIGNALING_KINDS,
    validateInputPacket,
    validateSignalingPacket,
} from "../../src/messages/remote-protocol";

const identity = {
    protocolVersion: 1,
    viewerId: "view-a",
    sessionId: "session-a",
    endpointId: "browser-client:a",
};

test("remote protocol vocabulary is loaded from the packaged manifest", () => {
    assert.deepStrictEqual([...SIGNALING_KINDS], ["offer", "answer", "ice-candidate", "ice-complete"]);
    assert.deepStrictEqual([...INPUT_KINDS], ["pointer", "wheel", "key"]);
});

test("signaling validates identity and ICE payload", () => {
    const packet = {
        ...identity,
        messageId: "signal-1",
        kind: "ice-candidate",
        payload: { candidate: "candidate:1 1 udp 1 127.0.0.1 9999 typ host", sdpMid: "0", sdpMLineIndex: 0 },
    };
    assert.strictEqual(validateSignalingPacket(packet, {
        viewerId: "view-a", sessionId: "session-a", endpointId: "browser-client:a",
    }).status, "accepted");
    assert.deepStrictEqual(validateSignalingPacket({ ...packet, sessionId: "stale" }, { sessionId: "session-a" }).status, "rejected");
    assert.deepStrictEqual(validateSignalingPacket({
        ...packet, payload: { candidate: "", sdpMLineIndex: -1 },
    }).status, "rejected");
});

test("input validates normalized coordinates, viewport, sequence and modifiers", () => {
    const packet = {
        ...identity,
        sequence: 7,
        timestampMs: 1234.5,
        kind: "pointer",
        viewport: { width: 1920, height: 1080, devicePixelRatio: 1.5 },
        payload: {
            phase: "move", pointerType: "mouse", pointerId: 1,
            x: 0.25, y: 0.75, button: -1, buttons: 0,
            modifiers: { shift: false },
        },
    };
    assert.strictEqual(validateInputPacket(packet).status, "accepted");
    assert.strictEqual(validateInputPacket({
        ...packet, payload: { ...packet.payload, x: 1.1 },
    }).status, "rejected");
    assert.strictEqual(validateInputPacket({
        ...packet, sequence: -1,
    }).status, "rejected");
    assert.strictEqual(validateInputPacket({
        ...packet, payload: { ...packet.payload, modifiers: { shift: 1 } },
    }).status, "rejected");
});
