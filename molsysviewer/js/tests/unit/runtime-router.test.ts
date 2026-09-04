import assert from "node:assert";
import test from "node:test";

import {
    RUNTIME_PROTOCOL_VERSION,
    RuntimeEnvelope,
    RuntimeMessageRouter,
} from "../../src/messages/runtime-router";
import {
    ENDPOINT_CAPABILITIES,
    ENDPOINT_ROLE_CAPABILITIES,
    RENDER_PLACEMENTS,
} from "../../src/messages/runtime-actions";

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

test("remote placement, roles, and capabilities come from the shared manifest", () => {
    assert.deepStrictEqual([...RENDER_PLACEMENTS].sort(), ["client", "server"]);
    assert.strictEqual(ENDPOINT_ROLE_CAPABILITIES.has("browser-client"), true);
    assert.strictEqual(ENDPOINT_ROLE_CAPABILITIES.has("qt-client"), true);
    assert.strictEqual(ENDPOINT_ROLE_CAPABILITIES.has("render-worker"), true);
    assert.strictEqual(ENDPOINT_ROLE_CAPABILITIES.get("qt-client")?.has("native-host"), true);
    assert.strictEqual(ENDPOINT_CAPABILITIES.has("video-send"), true);
});

test("runtime router recognizes remote endpoints as projection recipients", () => {
    const router = makeRouter();
    router.registerEndpoint({ endpointId: "browser", role: "browser-client" });
    router.registerEndpoint({ endpointId: "worker", role: "render-worker" });
    const projection = envelope({
        endpointId: "python",
        messageId: "projection-remote",
        direction: "projection",
    });

    const result = router.route(projection);
    assert.strictEqual(result.status, "accepted");
    if (result.status === "accepted") {
        assert.deepStrictEqual(result.recipientEndpointIds, [
            "host", "canvas", "popup", "browser", "worker",
        ]);
    }
});

test("runtime envelope provenance fields are paired and typed", () => {
    const router = makeRouter();
    assert.deepStrictEqual(router.route(envelope({ actorId: "human:one" })), {
        status: "rejected",
        reason: "malformed-envelope",
        detail: "Runtime envelope is malformed",
    });
    assert.deepStrictEqual(router.route(envelope({
        actorId: "human:one",
        actorKind: "human",
        causationId: "request-1",
        operationId: "operation-1",
        deadlineUnixMs: 2_000_000_000_000,
    })).status, "accepted");
    assert.deepStrictEqual(router.route(envelope({
        messageId: "bad-deadline",
        actorId: "human:one",
        actorKind: "human",
        deadlineUnixMs: -1,
    })), {
        status: "rejected",
        reason: "malformed-envelope",
        detail: "Runtime envelope is malformed",
    });
});
