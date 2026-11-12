import assert from "node:assert";
import test from "node:test";

import { MovieHandlers } from "../../src/managers/handlers/movie-handlers";
import { compileMovieTimeline } from "../../src/managers/movie-timeline";
import legacyMigration from "../fixtures/movie-legacy-oracle.json";

for (const [index, control] of legacyMigration.entries()) {
    test(`public legacy migration agrees with the original renderer at binary64 thresholds ${index}`, async () => {
        let structure = -1, camera: any;
        const movie = new MovieHandlers({
            getCameraSnapshot: () => undefined,
            waitForDraw: async () => {},
            setCameraSnapshot: async value => { camera = value; },
            setTrajectoryFrame: async value => { structure = value; },
            getImageDataUri: async () => undefined,
            showLayer: async () => {}, hideLayer: async () => {}, notify: undefined,
        });
        const timeline = compileMovieTimeline(control.recipe);
        for (const at of [...control.times].reverse()) {
            // Invoke the existing export sampler, not a copy of its rounding,
            // easing or interpolation formulas. This is an algorithm control;
            // the native browser guard separately receives actual Mol* draws.
            await (movie as any).applyStateForExport(control.legacy.keyframes, at, undefined, {}, undefined);
            const migrated = timeline.evaluate(at);
            assert.strictEqual(migrated.structure_index, structure, `${index} at ${at}`);
            for (const vector of ["position", "target", "up"] as const) {
                migrated.camera[vector].forEach((component, i) => {
                    assert.ok(Math.abs(component - camera[vector][i]) < 1e-12, `${index} ${vector} at ${at}`);
                });
            }
        }
    });
}

test("legacy migration provenance preserves unknown origin and refuses invented identity", () => {
    const original = legacyMigration[0].recipe;
    assert.strictEqual(original.provenance.source_binding, null);
    for (const [field, value] of [["source_binding", {}], ["source_version", 2], ["schema", "molsysviewer.movie_import@1"]] as const) {
        const changed = JSON.parse(JSON.stringify(original));
        changed.provenance[field] = value;
        assert.throws(() => compileMovieTimeline(changed));
    }
});

test("the original sampler ignores a JSON boolean __proto__ visibility tag", async () => {
    const actions: string[] = [];
    const movie = new MovieHandlers({
        getCameraSnapshot: () => undefined, waitForDraw: async () => {},
        setCameraSnapshot: async () => {}, setTrajectoryFrame: async () => {},
        getImageDataUri: async () => undefined,
        showLayer: async tag => { actions.push(tag); },
        hideLayer: async tag => { actions.push(tag); }, notify: undefined,
    });
    const keyframes = JSON.parse('[{"time_ms":0,"layer_visibility":{"__proto__":false}},{"time_ms":1000}]');
    assert.ok(Object.hasOwn(keyframes[0].layer_visibility, "__proto__"));
    await (movie as any).applyStateForExport(keyframes, 1000, undefined, {}, undefined);
    assert.deepStrictEqual(actions, []);
});

test("stop_movie drains an in-flight camera write and restores the stopped position", async () => {
    const originalRequest = globalThis.requestAnimationFrame;
    const originalCancel = globalThis.cancelAnimationFrame;
    let tick: FrameRequestCallback | undefined;
    let releaseWrite: (() => void) | undefined;
    let position = [0, 0, 60];
    const written: number[][] = [];

    globalThis.requestAnimationFrame = callback => {
        tick = callback;
        return 1;
    };
    globalThis.cancelAnimationFrame = () => { tick = undefined; };

    try {
        const movie = new MovieHandlers({
            getCameraSnapshot: () => ({ position: [...position] }) as any,
            waitForDraw: async () => {},
            setCameraSnapshot: async snapshot => {
                const next = [...snapshot.position];
                written.push(next);
                if (written.length === 1) {
                    await new Promise<void>(resolve => { releaseWrite = resolve; });
                }
                position = next;
            },
            setTrajectoryFrame: async () => {},
            getImageDataUri: async () => undefined,
            showLayer: async () => {},
            hideLayer: async () => {},
            notify: undefined,
        });
        await movie.play([
            { time_ms: 0, camera: { position: [0, 0, 60], target: [0, 0, 0], up: [0, 1, 0] } },
            { time_ms: 900, camera: { position: [60, 0, 0], target: [0, 0, 0], up: [0, 1, 0] } },
        ]);
        assert.ok(tick);
        tick(performance.now() + 300);

        const stopping = movie.stop();
        assert.deepStrictEqual(position, [0, 0, 60]);
        assert.ok(releaseWrite);
        releaseWrite();
        await stopping;

        assert.strictEqual(written.length, 2);
        assert.deepStrictEqual(position, [0, 0, 60]);
        assert.strictEqual(tick, undefined);
    } finally {
        globalThis.requestAnimationFrame = originalRequest;
        globalThis.cancelAnimationFrame = originalCancel;
    }
});

test("movie_playback_done waits for the final camera write", async () => {
    const originalRequest = globalThis.requestAnimationFrame;
    const originalCancel = globalThis.cancelAnimationFrame;
    let tick: FrameRequestCallback | undefined;
    let releaseWrite: (() => void) | undefined;
    let releaseDraw: (() => void) | undefined;
    let position = [0, 0, 60];
    const events: string[] = [];

    globalThis.requestAnimationFrame = callback => { tick = callback; return 1; };
    globalThis.cancelAnimationFrame = () => { tick = undefined; };

    try {
        const movie = new MovieHandlers({
            getCameraSnapshot: () => ({ position: [...position] }) as any,
            waitForDraw: () => new Promise<void>(resolve => { releaseDraw = resolve; }),
            setCameraSnapshot: async snapshot => {
                await new Promise<void>(resolve => { releaseWrite = resolve; });
                position = [...snapshot.position];
            },
            setTrajectoryFrame: async () => {},
            getImageDataUri: async () => undefined,
            showLayer: async () => {},
            hideLayer: async () => {},
            notify: message => events.push(message.event),
        });
        await movie.play([
            { time_ms: 0, camera: { position: [0, 0, 60], target: [0, 0, 0], up: [0, 1, 0] } },
            { time_ms: 900, camera: { position: [60, 0, 0], target: [0, 0, 0], up: [0, 1, 0] } },
        ]);
        assert.ok(tick);
        tick(performance.now() + 1000);
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.deepStrictEqual(events, []);
        assert.ok(releaseWrite);
        releaseWrite();
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.deepStrictEqual(position, [60, 0, 0]);
        assert.deepStrictEqual(events, []);
        assert.ok(releaseDraw);
        releaseDraw();
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.deepStrictEqual(events, ["movie_playback_done"]);
    } finally {
        globalThis.requestAnimationFrame = originalRequest;
        globalThis.cancelAnimationFrame = originalCancel;
    }
});

test("stop_movie waits for a restored draw after the command promise already resolved", async () => {
    const originalRequest = globalThis.requestAnimationFrame;
    const originalCancel = globalThis.cancelAnimationFrame;
    let tick: FrameRequestCallback | undefined;
    let releaseDraw: (() => void) | undefined;
    let position = [60, 0, 0];
    let pending: number[] | undefined;
    const requested: number[][] = [];
    globalThis.requestAnimationFrame = callback => { tick = callback; return 1; };
    globalThis.cancelAnimationFrame = () => { tick = undefined; };

    try {
        const movie = new MovieHandlers({
            getCameraSnapshot: () => ({ position: [...position] }) as any,
            setCameraSnapshot: async snapshot => {
                pending = [...snapshot.position];
                requested.push(pending);
            },
            waitForDraw: () => new Promise<void>(resolve => {
                releaseDraw = () => { position = pending!; resolve(); };
            }),
            setTrajectoryFrame: async () => {},
            getImageDataUri: async () => undefined,
            showLayer: async () => {},
            hideLayer: async () => {},
            notify: undefined,
        });
        await movie.play([
            { time_ms: 0, camera: { position: [0, 0, 60], target: [0, 0, 0], up: [0, 1, 0] } },
            { time_ms: 900, camera: { position: [60, 0, 0], target: [0, 0, 0], up: [0, 1, 0] } },
        ]);
        assert.ok(tick);
        tick(performance.now() + 300);
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.strictEqual(requested.length, 1);
        assert.notDeepStrictEqual(pending, position);

        let stopped = false;
        const stopping = movie.stop().then(() => { stopped = true; });
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.strictEqual(stopped, false, "stop returned before the camera was drawn");
        assert.strictEqual(requested.length, 2, "resolved-but-unapplied command was not replaced");
        assert.deepStrictEqual(pending, [60, 0, 0]);
        assert.ok(releaseDraw);
        releaseDraw();
        await stopping;
        assert.deepStrictEqual(position, [60, 0, 0]);
        assert.strictEqual(tick, undefined);
    } finally {
        globalThis.requestAnimationFrame = originalRequest;
        globalThis.cancelAnimationFrame = originalCancel;
    }
});
