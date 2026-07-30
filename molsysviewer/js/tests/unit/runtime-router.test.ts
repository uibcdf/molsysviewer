import assert from "node:assert";
import test from "node:test";

import {
    RUNTIME_PROTOCOL_VERSION,
    RuntimeEnvelope,
    RuntimeMessageRouter,
} from "../../src/messages/runtime-router";

function makeRouter(maxProcessedCommands = 1024) {
    const router = new RuntimeMessageRouter("view-a", "session-a", maxProcessedCommands);
    router.registerEndpoint({ endpointId: "python", role: "python" });
    router.registerEndpoint({ endpointId: "host", role: "widget-host" });
    router.registerEndpoint({ endpointId: "canvas", role: "canvas" });
    router.registerEndpoint({ endpointId: "popup", role: "canvas-popup" });
    return router;
}

function envelope(
    overrides: Partial<RuntimeEnvelope> = {},
): RuntimeEnvelope {
    return {
        protocolVersion: RUNTIME_PROTOCOL_VERSION,
        viewerId: "view-a",
        sessionId: "session-a",
        endpointId: "popup",
        messageId: "message-1",
        direction: "command",
        action: "panel-action",
        payload: { action: "hide_region" },
        ...overrides,
    };
}

test("runtime router sends a UI command to Python exactly once", () => {
    const router = makeRouter();
    const command = envelope();

    assert.deepStrictEqual(router.route(command), {
        status: "accepted",
        envelope: command,
        recipientEndpointIds: ["python"],
    });
    assert.deepStrictEqual(router.route(command), {
        status: "duplicate",
        envelope: command,
        recipientEndpointIds: [],
    });
});

test("runtime router fans Python projections out to rendering endpoints", () => {
    const router = makeRouter();
    const projection = envelope({
        endpointId: "python",
        messageId: "projection-1",
        direction: "projection",
        action: "viewer-message",
        payload: { op: "hide_region", tag: "site" },
    });

    assert.deepStrictEqual(router.route(projection), {
        status: "accepted",
        envelope: projection,
        recipientEndpointIds: ["host", "canvas", "popup"],
    });
});

test("runtime router rejects cross-viewer and stale-session envelopes", () => {
    const router = makeRouter();

    assert.deepStrictEqual(router.route(envelope({ viewerId: "view-b" })), {
        status: "rejected",
        reason: "viewer-mismatch",
        detail: "Envelope belongs to viewer view-b",
    });
    assert.deepStrictEqual(router.route(envelope({
        messageId: "message-2",
        sessionId: "session-old",
    })), {
        status: "rejected",
        reason: "session-mismatch",
        detail: "Envelope belongs to session session-old",
    });
});

test("runtime router rejects malformed, unknown, and unauthorized sources", () => {
    const router = makeRouter();

    assert.deepStrictEqual(router.route("not-an-envelope"), {
        status: "rejected",
        reason: "malformed-envelope",
        detail: "Runtime envelope is malformed",
    });
    assert.deepStrictEqual(router.route(envelope({
        endpointId: "unknown",
        messageId: "message-2",
    })), {
        status: "rejected",
        reason: "unknown-source",
        detail: "Unknown runtime endpoint: unknown",
    });
    assert.deepStrictEqual(router.route(envelope({
        endpointId: "popup",
        messageId: "message-3",
        direction: "projection",
    })), {
        status: "rejected",
        reason: "direction-not-allowed",
        detail: "canvas-popup cannot originate projection",
    });
});

test("runtime router rejects duplicate endpoint identities", () => {
    const router = makeRouter();

    assert.throws(
        () => router.registerEndpoint({ endpointId: "popup", role: "panel-popup" }),
        /Runtime endpoint already registered: popup/,
    );
});

test("runtime router targets acknowledgements and forgets closed endpoints", () => {
    const router = makeRouter();
    const ack = envelope({
        endpointId: "python",
        targetEndpointId: "popup",
        messageId: "ack-1",
        correlationId: "message-1",
        direction: "ack",
        action: "command-accepted",
        payload: null,
    });

    assert.deepStrictEqual(router.route(ack), {
        status: "accepted",
        envelope: ack,
        recipientEndpointIds: ["popup"],
    });
    assert.strictEqual(router.unregisterEndpoint("popup"), true);
    assert.strictEqual(router.hasEndpoint("popup"), false);
    assert.deepStrictEqual(router.route({ ...ack, messageId: "ack-2" }), {
        status: "rejected",
        reason: "unknown-target",
        detail: "Unknown target endpoint: popup",
    });
});

test("runtime router bounds command deduplication state", () => {
    const router = makeRouter(2);
    const first = envelope({ messageId: "command-1" });
    const second = envelope({ messageId: "command-2" });
    const third = envelope({ messageId: "command-3" });

    assert.strictEqual(router.route(first).status, "accepted");
    assert.strictEqual(router.route(second).status, "accepted");
    assert.strictEqual(router.route(third).status, "accepted");
    assert.strictEqual(router.route(first).status, "accepted");
    assert.strictEqual(router.route(third).status, "duplicate");
});
