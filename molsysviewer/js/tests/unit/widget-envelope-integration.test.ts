import assert from "node:assert";
import test from "node:test";

import { WidgetEnvelopeAdapter } from "../../src/messages/widget-envelope";

const VIEWER = "view-a";
const SESSION = "session-a";

// Faithful mirror of the index.ts `onCustomMsg` seam: unwrap, drop rejects,
// consume the duplicate-command ack, otherwise deliver the domain message to the
// controller (raw bootstrap/data-plane also reaches the existing dispatch). Kept
// in lock-step with the production 4-line decision.
function seam(
    adapter: WidgetEnvelopeAdapter,
    controller: { handleMessage: (m: Record<string, unknown>) => void },
    msg: Record<string, unknown>,
): void {
    const inbound = adapter.unwrapInbound(msg);
    if (inbound.kind === "rejected") return;
    if (inbound.kind === "message") {
        if ((inbound.message as any).event === "command_duplicate_ack") return;
        controller.handleMessage(inbound.message);
        return;
    }
    controller.handleMessage(msg); // raw path (bootstrap/data-plane)
}

function envelope(overrides: Record<string, unknown> = {}) {
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

function spyController() {
    const calls: Record<string, unknown>[] = [];
    return { calls, handleMessage: (m: Record<string, unknown>) => { calls.push(m); } };
}

test("an enveloped projection reaches the controller exactly once, as the domain message", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    seam(adapter, controller, envelope());
    assert.strictEqual(controller.calls.length, 1);
    assert.deepStrictEqual(controller.calls[0], { op: "set_region_summaries", summaries: [] });
});

test("the duplicate-command ack is consumed at the seam and never reaches the controller", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    seam(adapter, controller, envelope({
        direction: "ack",
        action: "command_duplicate_ack",
        correlationId: "cmd-1",
        payload: { event: "command_duplicate_ack", message_id: "cmd-1" },
    }));
    assert.strictEqual(controller.calls.length, 0);
});

test("a projection for another session never reaches the controller", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    seam(adapter, controller, envelope({ sessionId: "session-other" }));
    assert.strictEqual(controller.calls.length, 0);
});

// R2: the canonical snapshot answer is correlated and consumed at the seam.
// Mirrors the index.ts branch that resolves a pending scene-snapshot request.
function seamWithSnapshots(
    adapter: WidgetEnvelopeAdapter,
    controller: { handleMessage: (m: Record<string, unknown>) => void },
    pending: Map<string, (messages: unknown[]) => void>,
    msg: Record<string, unknown>,
): void {
    const inbound = adapter.unwrapInbound(msg);
    if (inbound.kind === "rejected") return;
    if (inbound.kind === "message") {
        const event = (inbound.message as any).event;
        if (event === "command_duplicate_ack") return;
        if (event === "popup_scene_snapshot") {
            const correlationId = inbound.envelope.correlationId;
            const settle = correlationId ? pending.get(correlationId) : undefined;
            if (settle) settle(((inbound.message as any).messages ?? []) as unknown[]);
            return;
        }
        controller.handleMessage(inbound.message);
        return;
    }
    controller.handleMessage(msg);
}

test("a correlated popup scene snapshot resolves its request and never reaches the controller", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    const pending = new Map<string, (messages: unknown[]) => void>();
    let resolved: unknown[] | null = null;
    pending.set("req-1", (messages) => { resolved = messages; });

    seamWithSnapshots(adapter, controller, pending, envelope({
        action: "popup_scene_snapshot",
        correlationId: "req-1",
        payload: {
            event: "popup_scene_snapshot",
            mode: "panel",
            messages: [{ op: "set_region_summaries", regions: [] }],
        },
    }));

    assert.deepStrictEqual(resolved, [{ op: "set_region_summaries", regions: [] }]);
    assert.strictEqual(controller.calls.length, 0, "the snapshot answer is consumed at the seam");
});

test("a snapshot answer for an unknown correlation is dropped, not applied", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    seamWithSnapshots(adapter, controller, new Map(), envelope({
        action: "popup_scene_snapshot",
        correlationId: "req-does-not-exist",
        payload: { event: "popup_scene_snapshot", mode: "canvas", messages: [] },
    }));
    assert.strictEqual(controller.calls.length, 0);
});

test("a raw data-plane message still reaches the existing dispatch once", () => {
    const adapter = new WidgetEnvelopeAdapter(VIEWER, SESSION);
    const controller = spyController();
    const raw = { op: "structure_data_begin", generation: 1 };
    seam(adapter, controller, raw);
    assert.strictEqual(controller.calls.length, 1);
    assert.strictEqual(controller.calls[0], raw);
});
