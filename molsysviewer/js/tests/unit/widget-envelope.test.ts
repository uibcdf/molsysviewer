import assert from "node:assert";
import test from "node:test";

import { WidgetEnvelopeAdapter } from "../../src/messages/widget-envelope";
import {
    ACTION_CATEGORIES,
    DATA_PLANE_ACTIONS,
    OUTBOUND_REQUESTS,
    RAW_ACTIONS,
    categoryOf,
} from "../../src/messages/runtime-actions";

const VIEWER = "view-a";
const SESSION = "session-a";

function adapter() {
    return new WidgetEnvelopeAdapter(VIEWER, SESSION);
}

// -- manifest agrees with the Python side (same file, single source) ---------

test("manifest categories are all valid and groups are disjoint", () => {
    assert.ok(ACTION_CATEGORIES.size > 0);
    for (const category of ACTION_CATEGORIES.values()) {
        assert.ok(["command", "event", "request", "ack", "error"].includes(category));
    }
    const groups = [new Set(ACTION_CATEGORIES.keys()), OUTBOUND_REQUESTS, RAW_ACTIONS, DATA_PLANE_ACTIONS];
    const total = groups.reduce((sum, g) => sum + g.size, 0);
    const union = new Set(groups.flatMap((g) => [...g]));
    assert.strictEqual(total, union.size);
});

// -- outbound wrapping (browser -> Python) -----------------------------------

test("wrapOutbound stamps a command envelope with the seam identity", () => {
    const domain = { event: "interaction_context_action", op: "add_region", tag: "A" };
    const res = adapter().wrapOutbound(domain);
    assert.strictEqual(res.kind, "send");
    const env = (res as any).message;
    assert.strictEqual(env.direction, "command");
    assert.strictEqual(env.endpointId, `widget-host:${SESSION}`);
    assert.strictEqual(env.targetEndpointId, `python:${VIEWER}`);
    assert.strictEqual(env.action, "interaction_context_action");
    assert.strictEqual(env.payload, domain);
});

test("wrapOutbound classifies an ephemeral event as an event", () => {
    const res = adapter().wrapOutbound({ event: "interaction_hover" });
    assert.strictEqual(res.kind, "send");
    assert.strictEqual((res as any).message.direction, "event");
    assert.strictEqual(categoryOf("interaction_hover"), "event");
});

test("wrapOutbound sends raw and data-plane messages unwrapped", () => {
    const a = adapter();
    for (const action of [...RAW_ACTIONS, ...DATA_PLANE_ACTIONS]) {
        const msg = { event: action };
        const res = a.wrapOutbound(msg);
        assert.strictEqual(res.kind, "send", `should send: ${action}`);
        assert.strictEqual((res as any).message, msg, `should be unwrapped: ${action}`);
    }
});

// Mutation target: returning the raw message here must fail this test.
test("wrapOutbound rejects an unknown action as a contract defect", () => {
    const res = adapter().wrapOutbound({ event: "totally_made_up" });
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "unknown-action");
});

// Mutation target: accepting an outbound-only request from the browser must fail.
test("wrapOutbound refuses to originate an outbound-only request from the browser", () => {
    for (const action of OUTBOUND_REQUESTS) {
        const res = adapter().wrapOutbound({ op: action, event: action });
        assert.strictEqual(res.kind, "rejected");
        if (res.kind === "rejected") assert.strictEqual(res.reason, "outbound-only");
    }
});

test("message ids are unique per wrapped message", () => {
    const a = adapter();
    const first = a.wrapOutbound({ event: "interaction_hover" });
    const second = a.wrapOutbound({ event: "interaction_hover" });
    assert.notStrictEqual((first as any).message.messageId, (second as any).message.messageId);
});

// -- inbound unwrapping (Python -> browser) ----------------------------------

function projection(overrides: Record<string, unknown> = {}) {
    return {
        protocolVersion: 1,
        viewerId: VIEWER,
        sessionId: SESSION,
        endpointId: `python:${VIEWER}`,
        targetEndpointId: `widget-host:${SESSION}`,
        messageId: "py-1",
        direction: "projection",
        action: "set_region_summaries",
        payload: { op: "set_region_summaries", summaries: [] },
        ...overrides,
    };
}

test("unwrapInbound returns the domain projection message", () => {
    const res = adapter().unwrapInbound(projection());
    assert.strictEqual(res.kind, "message");
    if (res.kind === "message") assert.strictEqual((res.message as any).op, "set_region_summaries");
});

test("a non-envelope raw/data-plane action is reported as raw", () => {
    const res = adapter().unwrapInbound({ op: "structure_data_begin", generation: 1 });
    assert.strictEqual(res.kind, "raw");
});

// Mutation target: reporting this as raw (bypassing R1) must fail this test.
test("an unenveloped domain projection is rejected, not passed through as raw", () => {
    const res = adapter().unwrapInbound({ op: "set_region_summaries", summaries: [] });
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "unenveloped-control-message");
});

test("a projection for another session never yields a message", () => {
    const res = adapter().unwrapInbound(projection({ sessionId: "session-other" }));
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "session-mismatch");
});

test("a projection for another viewer is rejected", () => {
    const res = adapter().unwrapInbound(projection({ viewerId: "view-other" }));
    assert.strictEqual(res.kind, "rejected");
});

test("a message not originating from python is rejected", () => {
    const res = adapter().unwrapInbound(projection({ endpointId: "canvas-popup:9" }));
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "unknown-source");
});

test("the browser refuses to receive a command", () => {
    const res = adapter().unwrapInbound(projection({ direction: "command", action: "scene_history_undo", payload: { event: "scene_history_undo" } }));
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "direction-not-allowed");
});

test("an envelope whose action mismatches its payload is rejected", () => {
    const res = adapter().unwrapInbound(projection({ action: "set_region_summaries", payload: { op: "load_molsys_payload" } }));
    assert.strictEqual(res.kind, "rejected");
    if (res.kind === "rejected") assert.strictEqual(res.reason, "action-payload-mismatch");
});

test("an outbound request unwraps as a request-direction message", () => {
    const res = adapter().unwrapInbound(projection({
        direction: "request",
        action: "request_camera_snapshot",
        payload: { op: "request_camera_snapshot" },
    }));
    assert.strictEqual(res.kind, "message");
});

// --- gate 25: the popup channel has the same guard as the widget seam -------

test("every popup wire action is declared with the directions it may carry", () => {
    const { POPUP_ACTIONS, popupActionAllows } = require("../../src/messages/runtime-actions");
    assert.ok(POPUP_ACTIONS.size >= 11, "the popup vocabulary must be enumerated");

    // sync-op is deliberately bidirectional: a projection from the host, a
    // command from the popup. That ambiguity is the reason direction has to be
    // declared in the envelope instead of inferred from the sender.
    assert.equal(popupActionAllows("molsysviewer-sync-op", "projection"), true);
    assert.equal(popupActionAllows("molsysviewer-sync-op", "command"), true);

    // Camera sync is ephemeral and must never pass as a reproducible projection.
    assert.equal(popupActionAllows("molsysviewer-sync-camera", "event"), true);
    assert.equal(popupActionAllows("molsysviewer-sync-camera", "projection"), false);

    // A readiness event is not a command.
    assert.equal(popupActionAllows("molsysviewer-pop-ready", "event"), true);
    assert.equal(popupActionAllows("molsysviewer-pop-ready", "command"), false);
});

test("an action nobody declared is refused on the popup channel", () => {
    const { popupActionAllows } = require("../../src/messages/runtime-actions");
    assert.equal(popupActionAllows("molsysviewer-made-up", "projection"), false);
    assert.equal(popupActionAllows("", "event"), false);
});
