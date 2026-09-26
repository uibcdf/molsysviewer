import assert from "node:assert";
import test from "node:test";

import { MovieHandlers } from "../../src/managers/handlers/movie-handlers";

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
