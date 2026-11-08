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

test("trajectory handler emits throttled frame changes while playback is active", () => {
    const trajRef = "traj-ref";
    const plugin: any = makeTrajectoryPluginMock();
    plugin.state.data.cells = {
        get(ref: any) {
            if (ref === trajRef) return { obj: { data: { frameCount: 5 } } };
            return null;
        },
    };
    plugin.state.data.selectQ = () => [{ transform: { parent: trajRef, params: { modelIndex: 3 } } }];

    const notifications: any[] = [];
    const handler = new TrajectoryHandlers(plugin, {
        getLoadedStructure: () => ({ trajectory: trajRef as any, structure: "struct-ref" as any }),
        notifyTrajectoryState: () => {},
        notify: (msg) => notifications.push(msg),
    });

    (handler as any).notifyPlaybackFrameChanged(true);

    assert.deepStrictEqual(notifications, [
        { event: "trajectory_frame_changed", frame: 3, is_playing: true },
    ]);
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
