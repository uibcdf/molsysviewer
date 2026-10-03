import assert from "node:assert";
import test from "node:test";

import { TrajectoryHandlers } from "../../src/managers/handlers/trajectory-handlers";
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
