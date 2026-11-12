import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { mkdir, writeFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import type { Page } from "playwright";

async function command(page: Page, message: Record<string, unknown>) {
    return page.evaluate(async value => (window as any).__popupWidgetModel.send(value), message);
}

async function movieResult(page: Page, message: Record<string, unknown>, read: (reply: any) => any) {
    const deadline = performance.now() + 25_000;
    do {
        const result = read(await command(page, message));
        if (result) {
            assert.equal(result.ok, true, result.error);
            return result;
        }
        await delay(200);
    } while (performance.now() < deadline);
    throw new Error("Movie operation did not produce a correlated draw verdict.");
}

async function run() {
    const dir = dirname(fileURLToPath(import.meta.url));
    await withFixtureWorkspace("movie-seek", async workspace => {
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined;
        let release: (() => Promise<void>) | undefined;
        let popup: Page | undefined;
        try {
            bridge = new PythonFixtureBridge(resolve(dir, "movie-seek-bridge.py"), resolve(dir, "../../../.."),
                30_000, { env: fixtureEnvironment(workspace) });
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            const errors: string[] = [];
            page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            await command(page, { movie_start_motion: true });
            await page.waitForFunction(() => {
                const c = (window as any).__mirrorController;
                return c.trajectory.getPlaybackSnapshot().playing && c.scene.isSpinActive;
            });
            for (const [time, frame, visible] of [[600, 2, false], [100, 0, true]] as const) {
                await command(page, { movie_seek: time });
                const result = await movieResult(page, { movie_seek_status: true }, reply => reply.movie_seek_result);
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

            const popupOpened = page.waitForEvent("popup");
            await page.getByTitle("Open popup", { exact: true }).click();
            popup = await popupOpened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => (window as any).__mirrorController?.getStructureData()?.elementCount === 62);

            // Observe samples issued by the real primary renderer's clock.
            await page.evaluate(() => {
                const w = window as any;
                const model = w.__popupWidgetModel;
                const send = model.send.bind(model);
                w.__moviePreviewTimes = [];
                model.send = (message: any) => {
                    const payload = message.payload ?? message;
                    if (payload.event === "visual_state_snapshot" && payload.movie_next_sample) {
                        w.__moviePreviewTimes.push(payload.movie_next_sample.time_ms);
                    }
                    return send(message);
                };
            });
            const previewResult = (kind: string) => movieResult(page, { movie_preview_status: true },
                reply => reply.movie_preview_result[kind]);
            await command(page, { movie_preview_play: { loop: true, start: 400 } });
            try {
                await page.waitForFunction(() => (window as any).__moviePreviewTimes.length >= 3);
            } catch (error) {
                const status = await command(page, { movie_preview_status: true });
                const observation = await page.evaluate(() => {
                    const w = window as any, c = w.__mirrorController;
                    const rect = c.canvasHost.getBoundingClientRect();
                    return { samples: w.__moviePreviewTimes, errors: w.__popupFixtureErrors,
                        visibility: document.visibilityState, connected: c.canvasHost.isConnected,
                        canvas: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                        viewport: { width: innerWidth, height: innerHeight },
                        camera: c.getCameraSnapshot(), trajectory: c.trajectory.getTrajectoryState(),
                        clock: c.moviePreviewClock.current };
                });
                const diagnostic = { stage: "original-preview", status, observation, page_errors: errors };
                if (process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR) {
                    await mkdir(process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR, { recursive: true });
                    await writeFile(resolve(process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR, "preview-failure.json"),
                        JSON.stringify(diagnostic, null, 2));
                }
                console.error("[Movie original preview failure] " + JSON.stringify(diagnostic));
                throw error;
            }
            await command(page, { movie_preview_pause: true });
            const paused = (await previewResult("pause")).sample;
            assert.deepEqual((await previewResult("play")).sample, paused);
            const observed = await page.evaluate(() => {
                const w = window as any;
                return { frame: w.__mirrorController.trajectory.getTrajectoryState().currentFrame,
                    position: w.__mirrorController.getCameraSnapshot().position,
                    samples: w.__moviePreviewTimes.length };
            });
            assert.equal(observed.frame, paused.structure_index);
            assert.ok(observed.position.every((value: number, index: number) =>
                Math.abs(value - paused.camera.position[index]) <= 1e-6));
            await popup.waitForFunction(sample => {
                const c = (window as any).__mirrorController;
                const drawn = c.getCameraSnapshot();
                const region = c.state.regionIndex.get("site");
                return c.trajectory.getTrajectoryState().currentFrame === sample.structure_index
                    && region?.hidden === !sample.visibility[0].visible
                    && drawn?.position.every((value: number, index: number) => Math.abs(value - sample.camera.position[index]) <= 1e-6)
                    && c.moviePreviewClock.current === undefined;
            }, paused);
            await command(page, { movie_preview_save: resolve(workspace, "paused.msv") });
            const restored = await previewResult("save");
            assert.ok(restored.same_recipe);
            assert.equal(restored.frame, paused.structure_index);
            assert.equal(restored.visible, paused.visibility[0].visible);
            for (const key of ["position", "target", "up"] as const) {
                assert.ok(restored.camera[key].every((value: number, index: number) =>
                    Math.abs(value - paused.camera[key][index]) <= 1e-6));
            }
            // The next independent seek will get its own receipt. Late clocks
            // cannot resume the retired preview while it rewinds the scene.
            await command(page, { movie_seek: 0 });
            const rewound = await movieResult(page, { movie_seek_status: true }, reply => reply.movie_seek_result);
            assert.equal(rewound.frame, 0);
            assert.equal(await page.evaluate(() => (window as any).__moviePreviewTimes.length), observed.samples);
            await command(page, { movie_preview_play: { loop: false, start: 650 } });
            const finished = (await previewResult("play")).sample;
            assert.equal(finished.time_ms, 1000);
            assert.equal(finished.structure_index, 2);
            assert.deepEqual(finished.camera.position, [30, 0, 0]);

            // The same scene and authority now declare a different camera path.
            // Receive actual native chords rather than accepting the old arc.
            await command(page, { movie_use_cartesian: true });
            for (const at of [500, 100, 900]) {
                await command(page, { movie_seek: at });
                const received = await movieResult(page, { movie_seek_status: true }, reply => reply.movie_seek_result);
                const expected = [30 * at / 1000, 0, 30 * (1 - at / 1000)];
                assert.ok(received.sample.camera.position.every((value: number, i: number) =>
                    Math.abs(value - expected[i]) <= 1e-12));
                const native = await page.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
                assert.ok(native.every((value: number, i: number) => Math.abs(value - expected[i]) <= 1e-6));
                await popup.waitForFunction(position => (window as any).__mirrorController.getCameraSnapshot().position
                    .every((value: number, i: number) => Math.abs(value - position[i]) <= 1e-6), expected);
                const mirrored = await popup.evaluate(async () => {
                    const c = (window as any).__mirrorController;
                    await new Promise<void>(resolve => {
                        let requested = false;
                        const subscription = c.plugin.canvas3d.didDraw.subscribe(() => {
                            if (!requested) return;
                            subscription.unsubscribe(); resolve();
                        });
                        requested = true;
                        c.plugin.canvas3d.requestDraw();
                    });
                    return c.getCameraSnapshot().position;
                });
                assert.ok(mirrored.every((value: number, i: number) => Math.abs(value - expected[i]) <= 1e-6));
            }
            await command(page, { movie_preview_save: resolve(workspace, "cartesian.msv") });
            const cartesianRestored = await previewResult("save");
            assert.ok(cartesianRestored.same_recipe);
            assert.equal(cartesianRestored.camera_interpolation, "cartesian-constant-up@1");
            await command(page, { movie_preview_play: { loop: false, start: 200 } });
            const cartesianFinished = (await previewResult("play")).sample;
            assert.equal(cartesianFinished.time_ms, 1000);
            assert.deepEqual(cartesianFinished.camera.position, [30, 0, 0]);

            await command(page, { movie_use_legacy: true });
            for (const [at, frame] of [[0, 0], [249, 0], [250, 1], [749, 1], [750, 2], [1000, 2], [100, 0]]) {
                await command(page, { movie_seek: at });
                const migrated = await movieResult(page, { movie_seek_status: true }, reply => reply.movie_seek_result);
                assert.equal(migrated.frame, frame);
                assert.equal(migrated.sample.structure_index, frame);
                const expected = [30 * at / 1000, 0, 30 * (1 - at / 1000)];
                for (const surface of [page, popup]) {
                    await surface.waitForFunction(({ frame, expected, visible }) => {
                        const c = (window as any).__mirrorController;
                        const hidden = (ref: string) => c.plugin.state.data.cells.get(ref)?.state.isHidden === true;
                        const region = c.state.regionIndex.get("site").representations;
                        const shapes = [...c.state.tagIndex.get(c.state.taggedKey("shape", "site"))] as string[];
                        return c.trajectory.getTrajectoryState().currentFrame === frame
                            && c.getCameraSnapshot().position.every((v: number, i: number) => Math.abs(v - expected[i]) <= 1e-6)
                            && region.length > 0 && region.every((ref: string) => hidden(ref) === !visible)
                            && shapes.length > 0 && shapes.every(ref => !hidden(ref));
                    }, { frame, expected, visible: at < 1000 });
                    await surface.evaluate(async () => {
                        const c = (window as any).__mirrorController;
                        await new Promise<void>(resolve => {
                            let requested = false;
                            const subscription = c.plugin.canvas3d.didDraw.subscribe(() => {
                                if (!requested) return;
                                subscription.unsubscribe(); resolve();
                            });
                            requested = true;
                            c.plugin.canvas3d.requestDraw();
                        });
                    });
                }
            }
            await command(page, { movie_preview_save: resolve(workspace, "legacy.msv") });
            assert.ok((await previewResult("save")).same_recipe);
            await command(page, { movie_preview_play: { loop: false, start: 200 } });
            const legacyFinished = (await previewResult("play")).sample;
            assert.equal(legacyFinished.time_ms, 1000);
            assert.equal(legacyFinished.structure_index, 2);
            assert.deepEqual(legacyFinished.camera.position, [30, 0, 0]);
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log("[E2E Movie] Default/Cartesian preview and reviewed legacy steps, popup mirror and restored sessions agree.");
        } finally {
            await popup?.close();
            await release?.();
            await Promise.all([browser.close(), bridge?.close()]);
        }
    });
}

run().catch(error => { console.error(error); process.exitCode = 1; });
