import assert from "node:assert/strict";
import test from "node:test";
import { BehaviorSubject } from "rxjs";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { readCanvasDraw, waitForCanvasDraw } from "../../src/managers/canvas-draw";
import { handleFrontendRequest, VisualStateCaptureRequests } from "../../src/messages/frontend-requests";

test("draw cancellation ignores a replayed frame and releases its real subscription", async () => {
    const didDraw = new BehaviorSubject(0);
    const abort = new AbortController();
    let requests = 0;
    const canvas: any = { didDraw, requestDraw() { requests++; } };
    const pending = waitForCanvasDraw(canvas, 30000, abort.signal);
    assert.equal(requests, 1);
    assert.equal(didDraw.observers.length, 1);
    abort.abort();
    await assert.rejects(pending, { name: "AbortError" });
    assert.equal(didDraw.observers.length, 0);
    didDraw.next(1);
    const beforeStart = new AbortController();
    beforeStart.abort();
    await assert.rejects(waitForCanvasDraw(canvas, 30000, beforeStart.signal), { name: "AbortError" });
    assert.equal(requests, 1, "an already canceled wait must not request another draw");
});

test("a failed draw request also releases its subscription", async () => {
    const didDraw = new BehaviorSubject(0);
    const canvas: any = { didDraw, requestDraw() { throw new Error("draw request failed"); } };
    await assert.rejects(waitForCanvasDraw(canvas), /draw request failed/);
    assert.equal(didDraw.observers.length, 0);
});

test("a failed draw reader preserves its original rejection and retires the subscription", async () => {
    for (const original of [new Error("reader failed"), undefined]) {
        const didDraw = new BehaviorSubject(0);
        let reads = 0;
        const canvas: any = { didDraw, requestDraw() {} };
        const pending = readCanvasDraw(canvas, () => { reads++; throw original; });
        const rejection = assert.rejects(pending, error => error === original);
        assert.equal(reads, 0, "a replayed draw cannot invoke the reader");
        didDraw.next(1);
        await rejection;
        assert.equal(reads, 1);
        assert.equal(didDraw.observers.length, 0);
        didDraw.next(2);
        assert.equal(reads, 1);
    }
});

test("an already cancelled draw read neither samples nor requests rendering", async () => {
    const abort = new AbortController(), didDraw = new BehaviorSubject(0);
    abort.abort();
    let reads = 0, requests = 0;
    const canvas: any = { didDraw, requestDraw() { requests++; } };
    await assert.rejects(readCanvasDraw(canvas, () => reads++, 30000, abort.signal), { name: "AbortError" });
    assert.equal(reads, 0);
    assert.equal(requests, 0);
    assert.equal(didDraw.observers.length, 0);
});

test("a capture samples camera and frame inside its completed draw before later subscribers advance", async () => {
    const didDraw = new BehaviorSubject(0), camera = new Camera();
    camera.setState({ position: [10, 20, 30], target: [1, 2, 3] } as any, 0);
    const drawn = camera.getSnapshot();
    let frame = 0;
    const controller: any = {
        plugin: { canvas3d: { didDraw, requestDraw() {} } },
        onTrajectoryState(read: any) { read({ currentFrame: frame }); return () => {}; },
        getCameraSnapshot: () => camera.getSnapshot(),
    };
    const replies: any[] = [], captures = new VisualStateCaptureRequests();
    const message = { op: "request_visual_state", request_id: "moving-draw", capture_revision: "scene" };
    const pending = handleFrontendRequest(controller, message, event => replies.push(event), captures.reserve(message)!);
    const advance = didDraw.subscribe(draw => {
        if (!draw) return;
        frame = 1;
        camera.setState({ position: [40, 50, 60], target: [4, 5, 6] } as any, 0);
    });
    try {
        didDraw.next(1);
        await pending;
        assert.equal(replies.length, 1);
        assert.equal(replies[0].structure_index, 0, "the reply belongs to the completed draw, not later state");
        assert.deepEqual(replies[0].snapshot, drawn);
        assert.equal(frame, 1, "capture must not stop subsequent trajectory work");
        assert.notDeepEqual(camera.getSnapshot().position, drawn.position);
    } finally {
        advance.unsubscribe();
        captures.dispose();
    }
    assert.equal(didDraw.observers.length, 0);
});

test("capture cancellation matches both broker id and revision before queued work begins", async () => {
    const captures = new VisualStateCaptureRequests();
    const message = { op: "request_visual_state", request_id: "broker-a", capture_revision: "scene-a" };
    const capture = captures.reserve(message)!;
    captures.cancel({ request_id: "broker-a", capture_revision: "scene-b" });
    assert.equal(capture.signal.aborted, false);
    captures.cancel(message);
    assert.equal(capture.signal.aborted, true);
    const replies: any[] = [];
    await handleFrontendRequest({ plugin: {} } as any, message, event => replies.push(event), capture);
    assert.deepEqual(replies, []);
    assert.equal(captures.reserve(message), null, "a late duplicate cannot restart the canceled draw wait");
    captures.dispose();
});

test("aborting one active capture suppresses its reply while an unrelated capture can finish", async () => {
    const captures = new VisualStateCaptureRequests();
    const didDraw = new BehaviorSubject(0);
    const first = { op: "request_visual_state", request_id: "first", capture_revision: "scene" };
    const second = { ...first, request_id: "second" };
    const firstCapture = captures.reserve(first)!;
    const secondCapture = captures.reserve(second)!;
    const replies: any[] = [];
    const controller: any = { plugin: { canvas3d: { didDraw, requestDraw() {} } },
        onTrajectoryState(fn: any) { fn({ currentFrame: 2 }); return () => {}; },
        getCameraSnapshot() { return { position: [1, 2, 3] }; } };
    const one = handleFrontendRequest(controller, first, event => replies.push(event), firstCapture);
    const two = handleFrontendRequest(controller, second, event => replies.push(event), secondCapture);
    assert.equal(didDraw.observers.length, 2);
    captures.cancel(first);
    await one;
    assert.equal(didDraw.observers.length, 1);
    assert.equal(secondCapture.signal.aborted, false);
    didDraw.next(1);
    await two;
    assert.equal(didDraw.observers.length, 0);
    assert.equal(replies.length, 1);
    assert.equal(replies[0].request_id, "second");
    captures.dispose();
});

test("cancellation after a coherent draw still suppresses its queued capture reply", async () => {
    const captures = new VisualStateCaptureRequests(), didDraw = new BehaviorSubject(0), camera = new Camera();
    const controller: any = { plugin: { canvas3d: { didDraw, requestDraw() {} } },
        onTrajectoryState(read: any) { read({ currentFrame: 2 }); return () => {}; },
        getCameraSnapshot: () => camera.getSnapshot() };
    const message = { op: "request_visual_state", request_id: "cancelled-after-draw", capture_revision: "scene" };
    const replies: any[] = [];
    const pending = handleFrontendRequest(controller, message, reply => replies.push(reply), captures.reserve(message)!);
    didDraw.next(1);
    captures.cancel(message);
    await pending;
    assert.deepEqual(replies, []);
    assert.equal(didDraw.observers.length, 0);
    captures.dispose();
});

test("retired capture bookkeeping stays bounded without evicting a live reservation", () => {
    const captures = new VisualStateCaptureRequests();
    const live = captures.reserve({ request_id: "live", capture_revision: "scene" })!;
    for (let index = 0; index < 256; index++) captures.cancel({ request_id: `retired-${index}`, capture_revision: "scene" });
    assert.ok((captures as any).retired.size <= 64);
    assert.equal(live.signal.aborted, false);
    captures.dispose();
    assert.equal(live.signal.aborted, true);
    assert.equal((captures as any).pending.size, 0);
    assert.equal((captures as any).retired.size, 0);
    assert.equal(captures.reserve({ request_id: "later", capture_revision: "scene" }), null);
});
