import assert from "node:assert";
import test from "node:test";

import { TrajectoryHandlers, canAdvancePlaybackFrame } from "../../src/managers/handlers/trajectory-handlers";
import { makeTrajectoryPluginMock } from "./helpers";

test("trajectory handler exposes expected frame count before structure is ready", () => {
    const plugin: any = makeTrajectoryPluginMock();
    const handler = new TrajectoryHandlers(plugin, {
        getLoadedStructure: () => undefined,
        notifyTrajectoryState: () => {},
    });

    const observed: Array<{ frameCount: number; hasTrajectory: boolean }> = [];
    handler.onTrajectoryState(
        (state) => observed.push({ frameCount: state.frameCount, hasTrajectory: state.hasTrajectory }),
        { immediate: false },
    );

    handler.setExpectedFrameCount(5);

    assert.strictEqual(observed.length, 1);
    assert.strictEqual(observed[0].frameCount, 5);
    assert.strictEqual(observed[0].hasTrajectory, false);
});

// Native coordinate editing is guarded against real Mol* in coordinate-edits.e2e.ts.

test("playback feedback suppresses only identical receipts within a playback episode", async () => {
    const { handler, projection } = projectedFrameFixture();
    const notifications: any[] = [];
    let box = { definition_revision: 2, structure_index: 1 };
    const context = Reflect.get(handler, "context");
    context.notify = (msg: unknown) => notifications.push(msg);
    context.getBoxProjection = () => ({ ...box });

    const report = () => (handler as any).notifyPlaybackFrameChanged(true);
    report();
    report();
    box = { definition_revision: 3, structure_index: 2 };
    report();
    await handler.setTrajectoryFrame(projection);
    report();
    await handler.setTrajectoryFrame({ ...projection, index: 2 });
    report();
    await handler.stopTrajectoryPlayback(false);
    report();
    handler.dispose();

    assert.deepStrictEqual(notifications.map(({ frame, navigation_revision, box_display }) =>
        [frame, navigation_revision, box_display.definition_revision, box_display.structure_index]), [
        [1, undefined, 2, 1],
        [1, undefined, 3, 2],
        [1, 8, 3, 2],
        [2, 8, 3, 2],
        [2, 8, 3, 2],
    ]);
    assert.ok(notifications.every(msg => msg.event === "trajectory_frame_changed" && msg.is_playing));
});

test("a follower consumes complete owner playback metadata without acquiring a timer", () => {
    const handler = new TrajectoryHandlers(makeTrajectoryPluginMock() as any, {
        getLoadedStructure: () => undefined, notifyTrajectoryState: () => {},
    });
    handler.setFollower(true);
    const owner = { fps: 7, step_size: 3, mode: "ping-pong", direction: "backward", playing: true } as const;
    handler.applyPlaybackProjection(owner, 2);
    assert.deepEqual(handler.getPlaybackSnapshot(), owner);
    assert.equal(handler.isCaptureFrameReady(2), true);
    assert.equal(handler.isCaptureFrameReady(1), false);
    assert.equal((handler as any).playbackTimer, undefined);
    handler.applySummary({ fps: 99, mode: "loop", direction: "forward" });
    assert.deepEqual(handler.getPlaybackSnapshot(), owner, "a delayed Python summary cannot replace the resolved owner snapshot");
    const copy = handler.getPlaybackSnapshot(); copy.fps = 1;
    assert.deepEqual(handler.getPlaybackSnapshot(), owner);
    handler.applyPlaybackProjection({ ...owner, playing: false }, 2);
    assert.equal(handler.getPlaybackSnapshot().playing, false);
    assert.equal((handler as any).playbackTimer, undefined);
});

test("invalid playback projections cannot make a follower capture-ready", () => {
    const handler = new TrajectoryHandlers(makeTrajectoryPluginMock() as any, {
        getLoadedStructure: () => undefined, notifyTrajectoryState: () => {},
    });
    handler.setFollower(true);
    for (const bad of [undefined, { fps: 0, step_size: 1, mode: "loop", direction: "forward", playing: true },
        { fps: 7, step_size: 1, mode: "loop", direction: "forward", playing: 1 }]) {
        handler.applyPlaybackProjection(bad as any, 0);
        assert.equal(handler.isCaptureFrameReady(0), false);
    }
});

function projectedFrameFixture(indices = [1]) {
    const plugin: any = makeTrajectoryPluginMock();
    const models = indices.map((modelIndex, index) => ({ transform: {
        ref: `model-${index}`, parent: "trajectory", params: { modelIndex },
    } }));
    let applications = 0, refreshes = 0;
    const gates: Array<Promise<void>> = [];
    plugin.state.data.cells = new Map([["trajectory", { obj: { data: { frameCount: 3 } } }]]);
    plugin.state.data.selectQ = () => models;
    plugin.state.data.build = () => {
        const edits: Array<{ model: typeof models[number]; index: number }> = [];
        return { edits, to: (model: typeof models[number]) => ({ update: (params: { modelIndex: number }) => {
            edits.push({ model, index: params.modelIndex });
        } }) };
    };
    plugin.state.data.updateTree = (update: any) => update;
    plugin.runTask = async (update: any) => {
        applications++;
        await gates.shift();
        for (const edit of update.edits) edit.model.transform.params.modelIndex = edit.index;
    };
    const handler = new TrajectoryHandlers(plugin, {
        getLoadedStructure: () => ({ trajectory: "trajectory" as any }),
        notifyTrajectoryState() {}, afterFrameApplied: async () => { refreshes++; },
    });
    handler.setFollower(true);
    const projection: any = { op: "set_trajectory_frame", index: 1, navigation_revision: 8,
        playback_projection: { fps: 2, step_size: 1, mode: "ping-pong", direction: "forward", playing: true } };
    return { handler, projection, models, gates, applications: () => applications, refreshes: () => refreshes };
}

test("repeated complete follower frames do not rebuild unchanged molecular and derived geometry", async () => {
    const f = projectedFrameFixture();
    assert.equal(f.handler.isNoOpFrameProjection(f.projection), true);
    assert.equal(f.handler.isNoOpFrameProjection(1), false, "explicit seeks retain context invalidation");
    assert.equal(f.handler.isNoOpFrameProjection({ op: "set_trajectory_frame", index: 1 }), false);
    assert.equal(f.handler.isNoOpFrameProjection({ ...f.projection, index: 2 }), false);
    assert.equal(await f.handler.setTrajectoryFrame(f.projection), true);
    assert.equal(await f.handler.setTrajectoryFrame(f.projection), true);
    assert.equal(f.applications(), 0, "an unchanged owner frame must not enter the native model task");
    assert.equal(f.refreshes(), 0, "the same owner frame must not rebuild trajectory shapes");
    assert.equal(f.handler.feedbackRevision, 8);
    assert.equal(await f.handler.setTrajectoryFrame({ ...f.projection, navigation_revision: 7 }), false);
    assert.equal(f.handler.feedbackRevision, 8, "no-op detection must retain authority-revision validation");
    await f.handler.setTrajectoryFrame(1);
    assert.equal(f.applications(), 1, "explicit numeric navigation retains its existing refresh behavior");
    await f.handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 1 });
    assert.equal(f.applications(), 2, "legacy or explicit seeks retain their existing refresh behavior");
    f.handler.dispose();
});

test("model-dependent queries start before awaited derived refresh and public frame notification", async () => {
    const f = projectedFrameFixture();
    const order: string[] = [];
    let release!: () => void;
    let started!: () => void;
    const derivedStarted = new Promise<void>(resolve => { started = resolve; });
    const context = Reflect.get(f.handler, "context");
    context.onFrameModelApplied = (frame: number) => { assert.equal(frame, 2); order.push("query"); };
    context.afterFrameApplied = async () => {
        order.push("derived-start");
        await new Promise<void>(resolve => { release = resolve; started(); });
        order.push("derived-end");
    };
    f.handler.onTrajectoryState(() => order.push("public-frame"), { immediate: false });
    const pending = f.handler.setTrajectoryFrame({ ...f.projection, index: 2 });
    await derivedStarted;
    try { assert.deepEqual([...order], ["query", "derived-start"]); }
    finally { release(); await pending; f.handler.dispose(); }
    assert.deepEqual(order, ["query", "derived-start", "derived-end", "public-frame"]);
});

test("disposing before native model application prevents new scientific queries", async () => {
    const f = projectedFrameFixture();
    let complete!: () => void, queries = 0;
    f.gates.push(new Promise<void>(resolve => { complete = resolve; }));
    Reflect.get(f.handler, "context").onFrameModelApplied = () => { queries++; };
    const pending = f.handler.setTrajectoryFrame({ ...f.projection, index: 2 });
    f.handler.dispose(); complete();
    assert.equal(await pending, false);
    assert.equal(queries, 0);
});

test("same-index follower optimization never drops a return while a different frame is in flight", async () => {
    const f = projectedFrameFixture();
    let finishFirst!: () => void, finishReturn!: () => void;
    f.gates.push(new Promise<void>(resolve => { finishFirst = resolve; }),
        new Promise<void>(resolve => { finishReturn = resolve; }));
    const first = f.handler.setTrajectoryFrame({ ...f.projection, index: 2 });
    assert.equal(f.handler.isNoOpFrameProjection(f.projection), false,
        "a pending model change prevents retaining the old context on a return projection");
    const returning = f.handler.setTrajectoryFrame(f.projection);
    assert.equal(f.applications(), 2, "the return must apply even while its index still appears current");
    finishFirst(); await first;
    finishReturn(); await returning;
    assert.equal(f.models[0].transform.params.modelIndex, 1);
    assert.equal(f.refreshes(), 2);
    f.handler.dispose();
});

test("complete follower frames reconcile every trajectory model before taking the no-op path", async () => {
    const f = projectedFrameFixture([1, 0]);
    await f.handler.setTrajectoryFrame(f.projection);
    assert.deepEqual(f.models.map(model => model.transform.params.modelIndex), [1, 1]);
    assert.equal(f.applications(), 1);
    f.handler.setFollower(false);
    await f.handler.setTrajectoryFrame(f.projection);
    assert.equal(f.applications(), 2, "an authority's explicit navigation is outside the follower fast path");
    f.handler.dispose();
});

test("identical follower playback metadata does not restart same-frame projection listeners", () => {
    const f = projectedFrameFixture();
    let notifications = 0;
    f.handler.onTrajectoryState(() => { notifications++; }, { immediate: false });
    const snapshot = f.projection.playback_projection;
    f.handler.applyPlaybackProjection(snapshot, 1);
    f.handler.applyPlaybackProjection({ ...snapshot }, 1);
    assert.equal(notifications, 1);
    f.handler.applyPlaybackProjection({ ...snapshot, direction: "backward" }, 1);
    assert.equal(notifications, 2, "a direction change still projects on the same molecular frame");
    f.handler.applyPlaybackProjection({ ...snapshot, direction: "backward" }, 2);
    assert.equal(notifications, 3, "the resolved frame is part of the projection identity");
    f.handler.dispose();
});

test("trajectory feedback retains the applied intent and rejects older commands", async () => {
    const notifications: any[] = [];
    const handler = new TrajectoryHandlers(makeTrajectoryPluginMock() as any, {
        getLoadedStructure: () => undefined, notifyTrajectoryState: () => {},
        notify: message => notifications.push(message),
    });
    await handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 0, navigation_revision: 8 });
    await handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 0, navigation_revision: 7 });
    await handler.setTrajectoryPlayback({ op: "set_trajectory_playback", action: "stop", navigation_revision: 6 });
    (handler as any).notifyPlaybackFrameChanged(true);
    assert.equal(notifications[0].navigation_revision, 8);
    for (const value of [-1, NaN, true, "8"]) await assert.rejects(
        handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 0, navigation_revision: value as any }),
        /Invalid trajectory navigation revision/);
    assert.equal(handler.feedbackRevision, 8);
});

test("a delayed stop reports its own intent even after a newer seek is accepted", async () => {
    let complete!: () => void;
    const pending = new Promise<void>(resolve => { complete = resolve; });
    const stopped: any[] = [];
    const handler = new TrajectoryHandlers(makeTrajectoryPluginMock() as any, {
        getLoadedStructure: () => undefined, notifyTrajectoryState: () => {},
        afterFrameApplied: () => pending, onPlaybackStopped: (frame, revision) => stopped.push({ frame, revision }),
    });
    await handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 0, navigation_revision: 7 });
    (handler as any).playbackTimer = setInterval(() => {}, 1000);
    try {
        const stopping = handler.stopTrajectoryPlayback();
        await handler.setTrajectoryFrame({ op: "set_trajectory_frame", index: 0, navigation_revision: 8 });
        complete(); await stopping;
        assert.deepEqual(stopped, [{ frame: 0, revision: 7 }]);
        assert.equal(handler.feedbackRevision, 8);
    } finally { complete(); }
});

test("playback preserves ready cadence and gives pending projections a bounded presentation opportunity", () => {
    // A ready 30-fps scene may advance without an extra 33-ms dwell after draw.
    assert.equal(canAdvancePlaybackFrame(0, true, 100, 110, 33), true);
    // A completed draw still awaiting replies gets one normal period.
    assert.equal(canAdvancePlaybackFrame(0, false, 100, 110, 33), false);
    assert.equal(canAdvancePlaybackFrame(0, false, 100, 133, 33), true);
    // A hidden canvas uses application time; absent replies cannot freeze it.
    assert.equal(canAdvancePlaybackFrame(0, false, 100, 1100, 500), true);
    // Native updates are never overlapped, even with ready/stale timing data.
    assert.equal(canAdvancePlaybackFrame(1, true, 0, 10000, 33), false);
    assert.equal(canAdvancePlaybackFrame(2, false, 0, 10000, 33), false);
});

test("a pending native capture retains only a coherent prefix without stranding scientific replies", () => {
    assert.equal(canAdvancePlaybackFrame(0, true, 0, 5000, 500, true), false,
        "The owner's clock must not replace a ready scene before its requested native draw.");
    assert.equal(canAdvancePlaybackFrame(0, false, 0, 500, 500, true), true,
        "Incomplete scenes still progress, including deliberately held scientific queries.");
    assert.equal(canAdvancePlaybackFrame(0, true, 0, 5000, 500, false), true,
        "Completion, cancellation or hidden-canvas fallback restores ordinary cadence.");
    assert.equal(canAdvancePlaybackFrame(1, true, 0, 5000, 500, false), false,
        "A capture may never overlap an in-flight molecular model update.");
});

test("disposing trajectory ownership closes both timers and its draw observer", () => {
    const notifications: any[] = [];
    let drawReleases = 0;
    const handler = new TrajectoryHandlers(makeTrajectoryPluginMock() as any, {
        getLoadedStructure: () => undefined, notifyTrajectoryState: () => {},
        notify: message => notifications.push(message),
    });
    (handler as any).playbackTimer = setInterval(() => {}, 1000);
    (handler as any).trajectoryPoll = setInterval(() => {}, 1000);
    (handler as any).frameDrawRelease = () => { drawReleases++; };
    handler.dispose(); handler.dispose();
    (handler as any).notifyPlaybackFrameChanged(true);
    assert.equal(drawReleases, 1);
    assert.equal((handler as any).playbackTimer, undefined);
    assert.equal((handler as any).trajectoryPoll, undefined);
    assert.deepEqual(notifications, []);
});
