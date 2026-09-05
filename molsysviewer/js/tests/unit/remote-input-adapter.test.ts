import assert from "node:assert";
import test from "node:test";

import {
    RemoteInputAdapter,
    type RemoteInputEventFactory,
} from "../../src/messages/remote-input-adapter";

class RecordedEvent extends Event {
    constructor(type: string, readonly init: Record<string, unknown>) {
        super(type);
    }
}

const factory: RemoteInputEventFactory = {
    mouse: (type, init) => new RecordedEvent(type, init),
    wheel: (type, init) => new RecordedEvent(type, init),
    key: (type, init) => new RecordedEvent(type, init),
};

function target() {
    const events: RecordedEvent[] = [];
    let focused = false;
    const value = {
        focus: () => { focused = true; },
        dispatchEvent: (event: RecordedEvent) => { events.push(event); return true; },
        getBoundingClientRect: () => ({ left: 100, top: 50, width: 800, height: 400 }),
    } as unknown as HTMLElement;
    return { value, events, focused: () => focused };
}

function packet(sequence = 1, overrides: Record<string, unknown> = {}) {
    return {
        protocolVersion: 1,
        viewerId: "view-a",
        sessionId: "session-a",
        endpointId: "qt-client:a",
        sequence,
        timestampMs: 1000,
        kind: "pointer",
        viewport: { width: 1600, height: 800, devicePixelRatio: 2 },
        payload: {
            phase: "down",
            pointerType: "mouse",
            pointerId: 4,
            x: 0.25,
            y: 0.75,
            button: 0,
            buttons: 1,
            modifiers: { shift: true },
        },
        ...overrides,
    };
}

test("validated pointer input reaches the canvas with normalized coordinates", () => {
    const canvas = target();
    const adapter = new RemoteInputAdapter(canvas.value, {
        viewerId: "view-a", sessionId: "session-a", endpointId: "qt-client:a",
    }, factory);

    const result = adapter.handle(packet());

    assert.deepStrictEqual(result, { status: "accepted", sequence: 1, eventType: "mousedown" });
    assert.strictEqual(canvas.focused(), true);
    assert.strictEqual(canvas.events.length, 1);
    assert.strictEqual(canvas.events[0].init.clientX, 300);
    assert.strictEqual(canvas.events[0].init.clientY, 350);
    assert.strictEqual(canvas.events[0].init.shiftKey, true);
});

test("duplicate and out-of-order input never reaches MolStar", () => {
    const canvas = target();
    const adapter = new RemoteInputAdapter(canvas.value, {}, factory);

    assert.strictEqual(adapter.handle(packet(8)).status, "accepted");
    const duplicate = adapter.handle(packet(8));
    const older = adapter.handle(packet(7));

    assert.deepStrictEqual(duplicate, {
        status: "rejected", reason: "stale-sequence", detail: "Input sequence 8 does not follow 8",
    });
    assert.strictEqual(older.status, "rejected");
    assert.strictEqual(canvas.events.length, 1);
    assert.strictEqual(adapter.acceptedSequence, 8);
});

test("drag continuation and release use MolStar's window listeners", () => {
    const canvas = target();
    const global = target();
    const adapter = new RemoteInputAdapter(canvas.value, {}, factory, global.value);
    const payload = packet(1).payload;

    assert.strictEqual(adapter.handle(packet(1)).status, "accepted");
    assert.strictEqual(adapter.handle(packet(2, {
        payload: { ...payload, phase: "move", x: 0.5 },
    })).status, "accepted");
    assert.strictEqual(adapter.handle(packet(3, {
        payload: { ...payload, phase: "up", x: 0.6, buttons: 0 },
    })).status, "accepted");

    assert.deepStrictEqual(canvas.events.map(event => event.type), ["mousedown"]);
    assert.deepStrictEqual(global.events.map(event => event.type), ["mousemove", "mouseup"]);
});

test("foreign session is rejected before event construction", () => {
    const canvas = target();
    const adapter = new RemoteInputAdapter(canvas.value, { sessionId: "session-a" }, factory);

    const result = adapter.handle(packet(1, { sessionId: "session-old" }));

    assert.strictEqual(result.status, "rejected");
    if (result.status === "rejected") assert.strictEqual(result.reason, "identity-mismatch");
    assert.strictEqual(canvas.events.length, 0);
});

test("wheel and key packets retain bounded payload semantics", () => {
    const canvas = target();
    const adapter = new RemoteInputAdapter(canvas.value, {}, factory);
    const wheel = packet(1, {
        kind: "wheel",
        payload: { x: 0.5, y: 0.5, deltaX: 4, deltaY: -120, deltaMode: 0, modifiers: {} },
    });
    const key = packet(2, {
        kind: "key",
        payload: { phase: "down", code: "KeyR", repeat: false, modifiers: { ctrl: true } },
    });

    assert.strictEqual(adapter.handle(wheel).status, "accepted");
    assert.strictEqual(adapter.handle(key).status, "accepted");
    assert.deepStrictEqual(canvas.events.map(event => event.type), ["wheel", "keydown"]);
    assert.strictEqual(canvas.events[0].init.deltaY, -120);
    assert.strictEqual(canvas.events[1].init.ctrlKey, true);
});

test("context-menu input becomes a correlated native canvas event", () => {
    const canvas = target();
    const adapter = new RemoteInputAdapter(canvas.value, {}, factory);
    const result = adapter.handle(packet(1, {
        kind: "context-menu",
        payload: { x: 0.5, y: 0.25, requestId: "context-1", modifiers: { alt: true } },
    }));

    assert.deepStrictEqual(result, { status: "accepted", sequence: 1, eventType: "contextmenu" });
    assert.strictEqual(canvas.events[0].init.clientX, 500);
    assert.strictEqual(canvas.events[0].init.clientY, 150);
    assert.strictEqual(canvas.events[0].init.button, 2);
    assert.strictEqual((canvas.events[0] as any).molsysviewerRemoteRequestId, "context-1");
});

test("valid input is rate-limited with a deterministic injected clock", () => {
    const canvas = target();
    let now = 100;
    const adapter = new RemoteInputAdapter(
        canvas.value,
        {},
        factory,
        canvas.value,
        { maxEvents: 2, intervalMs: 1_000, now: () => now },
    );

    assert.strictEqual(adapter.handle(packet(1)).status, "accepted");
    assert.strictEqual(adapter.handle(packet(2)).status, "accepted");
    assert.deepStrictEqual(adapter.handle(packet(3)), {
        status: "rejected",
        reason: "rate-limit",
        detail: "Input exceeds 2 events per 1000 ms",
    });
    assert.strictEqual(adapter.acceptedSequence, 2);
    assert.strictEqual(canvas.events.length, 2);

    now = 1_100;
    assert.strictEqual(adapter.handle(packet(4)).status, "accepted");
    assert.strictEqual(adapter.acceptedSequence, 4);
    assert.strictEqual(canvas.events.length, 3);
});
