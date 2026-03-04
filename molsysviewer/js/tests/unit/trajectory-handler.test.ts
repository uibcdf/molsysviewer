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
