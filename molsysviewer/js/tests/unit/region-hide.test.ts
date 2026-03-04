import assert from "node:assert";
import test from "node:test";
import { StateHandlers } from "../../src/managers/handlers/state-handlers";
import { TrajectoryHandlers } from "../../src/managers/handlers/trajectory-handlers";

function makeTrajectoryPluginMock() {
    return {
        managers: {
            animation: {
                isAnimating: false,
                stop() {
                    return;
                },
            },
        },
        state: {
            data: {
                selectQ() {
                    return [];
                },
            },
        },
    };
}

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

test("state handler emits layer ack and keeps metadata through retag", async () => {
    const notifications: any[] = [];
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });

    await handler.createLayer({
        op: "create_layer",
        tag: "layer-a",
        kind: "shape",
        meta: { source: "unit-test" },
    });

    assert.deepStrictEqual(notifications, [
        { event: "layer_ack", tag: "layer-a", kind: "shape", meta: { source: "unit-test" } },
    ]);

    await handler.setLayerTag({
        op: "set_layer_tag",
        tag: "layer-a",
        new_tag: "layer-b",
    });

    const layerMeta = (handler as any).layerMeta as Map<string, any>;
    assert.strictEqual(layerMeta.has("layer-a"), false);
    assert.strictEqual(layerMeta.has("layer-b"), true);
    assert.deepStrictEqual(layerMeta.get("layer-b"), { kind: "shape", meta: { source: "unit-test" } });
});
