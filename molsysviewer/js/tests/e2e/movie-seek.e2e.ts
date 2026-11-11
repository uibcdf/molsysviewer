import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";

async function run() {
    const dir = dirname(fileURLToPath(import.meta.url));
    await withFixtureWorkspace("movie-seek", async workspace => {
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined;
        let release: (() => Promise<void>) | undefined;
        try {
            bridge = new PythonFixtureBridge(resolve(dir, "movie-seek-bridge.py"), resolve(dir, "../../../.."),
                30_000, { env: fixtureEnvironment(workspace) });
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            const errors: string[] = [];
            page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            await page.evaluate(async () => { await (window as any).__popupWidgetModel.send({ movie_start_motion: true }); });
            await page.waitForFunction(() => {
                const c = (window as any).__mirrorController;
                return c.trajectory.getPlaybackSnapshot().playing && c.scene.isSpinActive;
            });
            for (const [time, frame, visible] of [[600, 2, false], [100, 0, true]] as const) {
                await page.evaluate(async time => {
                    await (window as any).__popupWidgetModel.send({ movie_seek: time });
                }, time);
                let result;
                const deadline = performance.now() + 25_000;
                do {
                    result = await page.evaluate(async () => {
                        const reply = await (window as any).__popupWidgetModel.send({ movie_seek_status: true });
                        return reply.movie_seek_result;
                    });
                    if (!result) await delay(200);
                } while (!result && performance.now() < deadline);
                assert.ok(result, "The Movie seek must produce a correlated draw verdict.");
                assert.equal(result.ok, true, result.error);
                assert.equal(result.sample.time_ms, time);
                assert.equal(result.frame, frame);
                assert.equal(result.playing, false);
                const rendered = await page.evaluate(() => {
                    const c = (window as any).__mirrorController;
                    const region = c.state.regionIndex.get("site");
                    const shapeRefs = [...c.state.tagIndex.get(c.state.taggedKey("shape", "site"))];
                    const hidden = (ref: string) => c.plugin.state.data.cells.get(ref)?.state.isHidden === true;
                    return {
                        frame: c.trajectory.getTrajectoryState().currentFrame,
                        camera: c.getCameraSnapshot(),
                        playing: c.trajectory.getPlaybackSnapshot().playing,
                        spinning: c.scene.isSpinActive || c.scene.isSwingActive,
                        region: region.representations.map(hidden),
                        shape: shapeRefs.map(hidden),
                    };
                });
                assert.equal(rendered.frame, frame);
                assert.equal(rendered.playing, false);
                assert.equal(rendered.spinning, false);
                assert.ok(rendered.region.length > 0 && rendered.region.every(hidden => hidden === !visible));
                assert.ok(rendered.shape.length > 0 && rendered.shape.every(hidden => !hidden));
                for (const key of ["position", "target", "up"] as const) {
                    assert.ok(rendered.camera[key].every((value: number, index: number) =>
                        Math.abs(value - result.sample.camera[key][index]) <= 1e-6));
                }
            }
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log("[E2E Movie seek] Forward and reverse draws agree with the authored sample.");
        } finally {
            await release?.();
            await Promise.all([browser.close(), bridge?.close()]);
        }
    });
}

run().catch(error => { console.error(error); process.exitCode = 1; });
