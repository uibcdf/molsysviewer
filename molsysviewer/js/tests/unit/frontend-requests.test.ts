import assert from "node:assert/strict";
import test from "node:test";
import { BehaviorSubject } from "rxjs";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { readCanvasDraw, waitForCanvasDraw } from "../../src/managers/canvas-draw";
import { captureAtScenePrefix, handleFrontendRequest, VisualStateCaptureRequests } from "../../src/messages/frontend-requests";

test("Movie observes detached environment in the same completed draw as camera/frame", async () => {
    const didDraw = new BehaviorSubject(0), camera = new Camera();
    const renderer = { backgroundColor: 0x123456, ambientIntensity: 0.35, light: [{ intensity: 0.65 }] };
    const replies: any[] = [], requests = new VisualStateCaptureRequests();
    const message = { op: "request_visual_state", request_id: "environment", capture_revision: "scene",
        capture_version: 2, movie_environment_capture: 1 };
    const controller: any = { plugin: { canvas3d: { props: { renderer }, didDraw, requestDraw() {} } },
        readMovingVisualState: () => ({ snapshot: camera.getSnapshot(), structure_index: 2,
            playback: { fps: 30, step_size: 1, mode: "loop", direction: "forward", playing: false } }) };
    const pending = handleFrontendRequest(controller, message, reply => replies.push(reply), requests.reserve(message)!);
    const advance = didDraw.subscribe(draw => { if (draw) {
        renderer.backgroundColor = 0xffffff; renderer.ambientIntensity = 0.9; renderer.light[0].intensity = 0.1;
    } });
    try {
        didDraw.next(1); await pending;
        assert.equal(replies[0].ok, true);
        assert.equal(replies[0].movie_environment_capture, 1);
        assert.deepEqual(replies[0].movie_environment, { background: { color: 0x123456 },
            lighting: { ambient: 0.35, diffuse: 0.65 } });
        assert.equal(replies[0].structure_index, 2);
        assert.equal(renderer.ambientIntensity, 0.9);
        assert.equal(didDraw.observers.length, 1, "only the independent later subscriber remains");
    } finally { advance.unsubscribe(); requests.dispose(); }
});

test("unsupported environment versions and unsupported native values fail without a fabricated reply", async () => {
    for (const [version, requested, ambient] of [[1, 1, 0.4], [2, true, 0.4], [2, 2, 0.4], [2, 1, 2]]) {
        const didDraw = new BehaviorSubject(0), camera = new Camera(), requests = new VisualStateCaptureRequests();
        const replies: any[] = [];
        const message = { op: "request_visual_state", request_id: "unsupported", capture_revision: "scene",
            capture_version: version, movie_environment_capture: requested };
        const controller: any = { plugin: { canvas3d: { props: { renderer: {
            backgroundColor: 0, ambientIntensity: ambient, light: [{ intensity: 0.6 }] } }, didDraw, requestDraw() {} } },
            readMovingVisualState: () => ({ snapshot: camera.getSnapshot(), structure_index: 0,
                playback: { fps: 30, step_size: 1, mode: "loop", direction: "forward", playing: false } }) };
        const pending = handleFrontendRequest(controller, message, reply => replies.push(reply), requests.reserve(message)!);
        didDraw.next(1); await pending;
        assert.equal(replies.length, 1); assert.equal(replies[0].ok, false);
        assert.equal(replies[0].movie_environment, undefined);
        assert.equal(didDraw.observers.length, 0); requests.dispose();
    }
});

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

test("a filtered draw requests the next coherent frame without reading rejected draws or adding a clock", async () => {
    const didDraw = new BehaviorSubject(0);
    let ready = false, reads = 0, requests = 0;
    const canvas: any = { didDraw, requestDraw() { requests++; } };
    const pending = readCanvasDraw(canvas, () => ++reads, 1000, undefined, () => ready);
    didDraw.next(1); didDraw.next(2);
    assert.equal(reads, 0);
    assert.equal(requests, 3);
    ready = true; didDraw.next(3);
    assert.equal(await pending, 1);
    assert.equal(didDraw.observers.length, 0);
});

test("metadata becoming ready cannot strand a capture on an otherwise idle native canvas", async () => {
    const didDraw = new BehaviorSubject(0);
    let requested = false, ready = false, draws = 0;
    const canvas: any = { didDraw, requestDraw() { requested = true; } };
    const nativeTick = () => {
        if (!requested) return false;
        requested = false;
        didDraw.next(++draws);
        return true;
    };
    const pending = readCanvasDraw(canvas, () => draws, 1000, undefined, () => ready);
    assert.equal(nativeTick(), true);
    // Scientific metadata completes with no native geometry/camera change.
    ready = true;
    assert.equal(nativeTick(), true, "the waiting capture must have requested a fresh draw");
    assert.equal(await pending, 2);
    assert.equal(didDraw.observers.length, 0);
    assert.equal(nativeTick(), false, "completion must stop requesting additional frames");
});

test("a failing coherence predicate preserves its error and releases the draw subscription", async () => {
    const didDraw = new BehaviorSubject(0), original = new Error("coherence failed");
    const pending = readCanvasDraw({ didDraw, requestDraw() {} } as any, () => 1, 1000, undefined,
        () => { throw original; });
    const failure = assert.rejects(pending, error => error === original);
    didDraw.next(1); await failure;
    assert.equal(didDraw.observers.length, 0);
});

test("version 2 releases its scene prefix so dependent geometry replies can complete capture", async () => {
    const captures = new VisualStateCaptureRequests(), didDraw = new BehaviorSubject(0), camera = new Camera();
    const message = { op: "request_visual_state", request_id: "v2-prefix", capture_revision: "scene", capture_version: 2 };
    let ready = false, laterCommand = false, prepared = 0;
    const sample = { snapshot: camera.getSnapshot(), structure_index: 2,
        playback: { fps: 7, step_size: 2, mode: "ping-pong", direction: "backward", playing: true }, box_structure_index: 1 };
    const replies: any[] = [];
    const controller: any = { plugin: { canvas3d: { didDraw, requestDraw() {} } },
        prepareMovingVisualCapture() { prepared++; }, readMovingVisualState: () => ready ? sample : undefined };
    const queue = Promise.resolve().then(() => captureAtScenePrefix(controller, message, reply => replies.push(reply), captures.reserve(message)!))
        .then(() => { laterCommand = true; didDraw.next(1); ready = true; didDraw.next(2); });
    await queue;
    // The asynchronous sender completes independently of the retired prefix.
    await Promise.resolve(); await Promise.resolve();
    assert.equal(laterCommand, true);
    assert.equal(prepared, 1);
    assert.deepEqual(replies, [{ event: "visual_state_snapshot", request_id: "v2-prefix", capture_revision: "scene",
        ok: true, capture_version: 2, ...sample }]);
    assert.equal(didDraw.observers.length, 0);
    captures.dispose();
});

test("version 1 keeps its strict scene barrier and original reply shape", async () => {
    const captures = new VisualStateCaptureRequests(), didDraw = new BehaviorSubject(0), camera = new Camera();
    const message = { op: "request_visual_state", request_id: "v1-prefix", capture_revision: "scene" };
    const replies: any[] = [];
    const controller: any = { plugin: { canvas3d: { didDraw, requestDraw() {} } },
        getCameraSnapshot: () => camera.getSnapshot(),
        onTrajectoryState(read: any) { read({ currentFrame: 1 }); return () => {}; } };
    let prefixFinished = false;
    const prefix = captureAtScenePrefix(controller, message, reply => replies.push(reply), captures.reserve(message)!)
        .then(() => { prefixFinished = true; });
    await Promise.resolve(); assert.equal(prefixFinished, false);
    didDraw.next(1); await prefix;
    assert.equal(prefixFinished, true);
    assert.deepEqual(Object.keys(replies[0]).sort(), ["capture_revision", "event", "ok", "request_id", "snapshot", "structure_index"]);
    captures.dispose();
});

test("version 2 cancellation after its prefix retires the reader without blocking later commands", async () => {
    const captures = new VisualStateCaptureRequests(), didDraw = new BehaviorSubject(0);
    const message = { op: "request_visual_state", request_id: "v2-cancel", capture_revision: "scene", capture_version: 2 };
    const replies: any[] = [];
    const controller: any = { plugin: { canvas3d: { didDraw, requestDraw() {} } }, readMovingVisualState: () => undefined };
    await captureAtScenePrefix(controller, message, reply => replies.push(reply), captures.reserve(message)!);
    assert.equal(didDraw.observers.length, 1);
    captures.cancel(message);
    await Promise.resolve(); await Promise.resolve();
    assert.equal(didDraw.observers.length, 0);
    assert.deepEqual(replies, []);
    assert.equal(captures.reserve(message), null);
    captures.dispose();
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
