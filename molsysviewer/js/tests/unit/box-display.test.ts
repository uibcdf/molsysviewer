import assert from "node:assert/strict";
import test from "node:test";
import { BoxDisplayHandler } from "../../src/managers/handlers/box-display";
import { copyJsonBoxVectors, readBoxVectors } from "../../src/plugin/box-vectors";
import { syncTrajectoryFrames } from "../../src/managers/trajectory-sync";

const cells = [
    [[3, 0, 0], [0, 4, 0], [0, 0, 5]],
    [[0, 4, 0], [-5, 0, 0], [0, 0, 6]],
    [[4, 1, 0], [1, 5, 0], [1, 1, 6]],
];

function fixture() {
    let frame = 0, follower = false;
    let loaded: any = { boxVectors: copyJsonBoxVectors(cells.map(box => ({ box }))) };
    const rendered: Array<{ options: any; previous?: string }> = [];
    const removed: string[] = [], registered: string[] = [], errors: unknown[] = [];
    let nextRender: (() => Promise<void>) | undefined;
    let removeFailure = false;
    const handler = new BoxDisplayHandler({
        getLoaded: () => loaded, getFrame: () => frame, isFollower: () => follower,
        render: async (options, previous) => {
            rendered.push({ options, previous });
            const action = nextRender; nextRender = undefined;
            await action?.();
            return previous ?? `cell-${rendered.length}`;
        },
        remove: async ref => { removed.push(ref); if (removeFailure) throw new Error("remove failed"); },
        register: ref => { registered.push(ref); },
        failure: error => { errors.push(error); },
    });
    return {
        handler, rendered, removed, registered, errors,
        define: (index = 0, revision = 1, automatic = false) => handler.define({
            mode: "coordinates", radii: 1.25, colors: 0xff0000, alpha: .7, tag: "__msv_box",
        } as any, { structure_index: index, definition_revision: revision, frame_update: automatic }),
        frame: (index: number, force = false) => { frame = index; handler.onFrame(index, force); },
        follower: () => { follower = true; },
        replace: (scale = 1) => { loaded = { boxVectors: copyJsonBoxVectors(cells.map(box => ({
            box: box.map(row => row.map(value => value * scale)),
        }))) }; },
        hold: () => {
            let release!: () => void;
            const wait = new Promise<void>(resolve => { release = resolve; });
            nextRender = () => wait;
            return release;
        },
        fail: () => { nextRender = async () => { throw new Error("native geometry failure"); }; },
        failRemoval: () => { removeFailure = true; },
    };
}

test("raw row-vector cells are detached, compact and retain orientation", () => {
    const source = structuredClone(cells);
    const table = copyJsonBoxVectors(source.map(box => ({ box })))!;
    assert.equal(table.byteLength, 3 * 9 * Float64Array.BYTES_PER_ELEMENT);
    assert.deepEqual(readBoxVectors(table, 1), cells[1]);
    source[1][0][1] = 999;
    const read = readBoxVectors(table, 1)!;
    read[0][1] = -999;
    assert.deepEqual(readBoxVectors(table, 1), cells[1]);
});

test("missing and malformed raw cells never become an invented orthogonal box", () => {
    assert.equal(copyJsonBoxVectors([{}, {}]), undefined);
    const table = copyJsonBoxVectors([{ box: cells[0] }, {}, { box: [[NaN, 0, 0]] }]);
    assert.deepEqual(readBoxVectors(table, 0), cells[0]);
    for (const index of [-1, .5, NaN, Infinity, 1, 2, 3]) assert.equal(readBoxVectors(table, index), undefined);
    assert.equal(readBoxVectors(undefined, 0), undefined);
});

test("an explicit other-frame cell survives duplicate notifications until navigation", async () => {
    const f = fixture();
    await f.define(2);
    f.frame(0);
    await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, 2);
    assert.equal(f.rendered.length, 1);
    f.frame(1);
    await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, 1);
    assert.deepEqual(f.rendered[1].options.coordinate_pairs[0], [[0, 0, 0], cells[1][0]]);
    assert.equal(f.rendered[1].previous, "cell-1");
    assert.equal(f.handler.isFrameReady(1), true);
});

test("explicit same-frame navigation resumes following after a cell override", async () => {
    const f = fixture();
    await f.define(2);
    f.frame(0, true);
    await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, 0);
});

test("overlapping refreshes retain one worker, one representation and the latest target", async () => {
    const f = fixture();
    await f.define();
    const release = f.hold();
    f.frame(1);
    const pending = f.handler.whenSettled();
    for (let index = 0; index < 1000; index++) f.frame(index % 3);
    f.frame(2);
    assert.equal(f.handler.whenSettled(), pending);
    assert.equal(f.handler.isFrameReady(2), false);
    release();
    await pending;
    assert.equal(f.handler.structureIndex, 2);
    assert.equal(f.handler.isFrameReady(2), true);
    assert.equal(f.rendered.length, 3);
    assert.deepEqual(f.rendered.map(call => call.previous), [undefined, "cell-1", "cell-1"]);
});

for (const stop of ["forget", "dispose"] as const) test(`${stop} retires a late geometry write without resurrecting the cell`, async () => {
    const f = fixture();
    const release = f.hold();
    const pending = f.define();
    f.handler[stop]();
    assert.equal(f.handler.isFrameReady(0), false, "cleanup still owns an outstanding write");
    release();
    await pending;
    assert.deepEqual(f.removed, ["cell-1"]);
    assert.deepEqual(f.registered, []);
    assert.equal(f.handler.structureIndex, undefined);
    assert.equal(f.handler.isFrameReady(0), stop === "forget");
    f.frame(1);
    await f.handler.whenSettled();
    assert.equal(f.rendered.length, 1);
});

test("a newer definition retires an in-flight older representation before rebuilding", async () => {
    const f = fixture();
    const release = f.hold();
    const old = f.define();
    const current = f.define(2, 2);
    release();
    await Promise.all([old, current]);
    assert.deepEqual(f.removed, ["cell-1"]);
    assert.deepEqual(f.registered, ["cell-2"]);
    assert.equal(f.handler.structureIndex, 2);
});

test("failed late cleanup retains ownership and refuses capture after the worker retires", async () => {
    const f = fixture();
    const release = f.hold();
    const pending = f.define();
    f.handler.forget(); f.failRemoval(); release();
    await pending;
    assert.equal(f.handler.structureIndex, undefined);
    assert.equal(f.handler.isFrameReady(0), false);
    assert.equal(f.errors.length, 1);
    assert.deepEqual(f.registered, ["cell-1"]);
    // The caller's completed explicit clear can then release that ownership.
    f.handler.forget();
    assert.equal(f.handler.isFrameReady(0), true);
});

test("replacement of the loaded cell table refreshes even at the same frame", async () => {
    const f = fixture();
    await f.define(2);
    f.replace();
    assert.equal(f.handler.isFrameReady(0), false);
    f.frame(0);
    await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, 0);
    assert.equal(f.rendered.length, 2);
});

test("a follower rebuilds its selected cell after same-frame raw-table replacement", async () => {
    const f = fixture(); f.follower();
    await f.define(2);
    f.replace(2); f.frame(0);
    await f.handler.whenSettled();
    assert.equal(f.rendered.length, 2);
    assert.equal(f.handler.structureIndex, 2);
    assert.deepEqual(f.rendered[1].options.coordinate_pairs[0], [[0, 0, 0], cells[2][0].map(value => 2 * value)]);
});

test("a failed write removes obsolete geometry and permits the next frame to recover", async () => {
    const f = fixture();
    await f.define();
    f.fail(); f.frame(1);
    await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, undefined);
    assert.equal(f.handler.isFrameReady(1), false);
    assert.deepEqual(f.removed, ["cell-1"]);
    assert.equal(f.errors.length, 1);
    f.frame(2); await f.handler.whenSettled();
    assert.equal(f.handler.structureIndex, 2);
    assert.equal(f.handler.isFrameReady(2), true);
});

test("follower frames cannot override a newer explicit cell; owner projections can", async () => {
    const f = fixture(); f.follower();
    await f.define(2, 3);
    f.frame(1);
    await f.handler.applyProjection({ definition_revision: 2, structure_index: 1 });
    assert.equal(f.handler.structureIndex, 2);
    await f.handler.applyProjection({ definition_revision: 3, structure_index: 0 });
    assert.equal(f.handler.structureIndex, 0);
    assert.equal(f.handler.isFrameReady(1), true);
    f.handler.forget();
    await f.handler.applyProjection({ definition_revision: 3, structure_index: 1 });
    assert.equal(f.handler.structureIndex, undefined);
});

test("same-generation automatic feedback does not undo an explicit cell", async () => {
    const f = fixture();
    await f.define(2, 3);
    await f.define(0, 2, true);
    await f.define(0, 3, true);
    assert.equal(f.handler.structureIndex, 2);
    assert.equal(f.rendered.length, 1);
});

test("mirror projection includes cell changes even when the molecular frame is unchanged", () => {
    let callback!: (state: { currentFrame: number }) => void;
    const sent: any[] = [];
    const controller = { onTrajectoryState: (cb: typeof callback) => { callback = cb; return () => {}; },
        boxDisplay: { projection: { definition_revision: 1, structure_index: 2 } } };
    const stop = syncTrajectoryFrames(controller, () => true, message => sent.push(message));
    callback({ currentFrame: 0 });
    callback({ currentFrame: 0 });
    controller.boxDisplay.projection = { definition_revision: 2, structure_index: 1 };
    callback({ currentFrame: 0 });
    assert.deepEqual(sent.map(message => [message.index, message.box_display]), [
        [0, { definition_revision: 1, structure_index: 2 }],
        [0, { definition_revision: 2, structure_index: 1 }],
    ]);
    stop();
});
