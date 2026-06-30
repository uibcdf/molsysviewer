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

test("partialCoordinatesUpdate updates model atomicConformation and sends transaction ACK", async () => {
    const model = {
        atomicConformation: {
            x: new Float32Array([1, 2, 3]),
            y: new Float32Array([4, 5, 6]),
            z: new Float32Array([7, 8, 9]),
        }
    };
    const structure = {
        models: [model],
        conformation: {
            id: "0"
        }
    };
    const plugin: any = {
        state: {
            data: {
                cells: {
                    get(ref: any) {
                        if (ref === "struct-ref") {
                            return { obj: { data: structure } };
                        }
                        return null;
                    }
                },
                build() {
                    return {
                        to() {
                            return this;
                        }
                    };
                },
                updateTree() {
                    return Promise.resolve({});
                }
            }
        },
        runTask(task: any) {
            return Promise.resolve(task);
        }
    };

    const notifications: any[] = [];
    const handler = new TrajectoryHandlers(plugin, {
        getLoadedStructure: () => ({ trajectory: {} as any, structure: "struct-ref" as any }),
        notifyTrajectoryState: () => {},
        notify: (msg) => notifications.push(msg),
    });

    await handler.partialCoordinatesUpdate({
        op: "partial_coordinates_update",
        atom_indices: [1, 2],
        coordinates: [
            [20, 21, 22],
            [30, 31, 32]
        ],
        transaction_id: "tx-123"
    });

    // Check that coordinates in model were mutated correctly
    assert.strictEqual(model.atomicConformation.x[0], 1);
    assert.strictEqual(model.atomicConformation.x[1], 20);
    assert.strictEqual(model.atomicConformation.y[1], 21);
    assert.strictEqual(model.atomicConformation.z[1], 22);
    assert.strictEqual(model.atomicConformation.x[2], 30);
    assert.strictEqual(model.atomicConformation.y[2], 31);
    assert.strictEqual(model.atomicConformation.z[2], 32);

    // Check that conformation ID was updated
    assert.strictEqual(structure.conformation.id, "0_upd");

    // Check that transaction ACK was notified
    assert.strictEqual(notifications.length, 1);
    assert.strictEqual(notifications[0].event, "trajectory_frame_rendered");
    assert.strictEqual(notifications[0].transaction_id, "tx-123");
});

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
