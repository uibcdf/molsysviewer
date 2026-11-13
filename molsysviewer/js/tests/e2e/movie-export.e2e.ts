import assert from "node:assert/strict";
import { readFile, writeFile, readdir, mkdir, copyFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import type { Page } from "playwright";

async function command(page: Page, value: Record<string, unknown>) {
    return page.evaluate(async event => (window as any).__popupWidgetModel.send(event), value);
}

async function finished(page: Page) {
    const deadline = performance.now() + Math.max(60_000, Number(process.env.MOLSYSVIEWER_MOVIE_FRAME_TIMEOUT ?? 15) * 6000);
    do {
        const result = (await command(page, { movie_export_status: true })).movie_export_result;
        if (result) return result;
        await delay(100);
    } while (performance.now() < deadline);
    throw new Error("Movie export did not reach a terminal result.");
}

async function run() {
    await withFixtureWorkspace("movie-export", async workspace => {
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined;
        let release: (() => Promise<void>) | undefined;
        let diagnosticPage: Page | undefined;
        try {
            bridge = new PythonFixtureBridge(resolve(dirname(fileURLToPath(import.meta.url)), "movie-export-bridge.py"),
                resolve(dirname(fileURLToPath(import.meta.url)), "../../../.."), 30_000,
                { env: fixtureEnvironment(workspace) });
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            diagnosticPage = page;
            const errors: string[] = [];
            page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            await page.addScriptTag({ path: resolve(dirname(fileURLToPath(import.meta.url)), "harness.bundle.js") });
            await page.evaluate(() => {
                const w = window as any;
                const controller = w.__mirrorController;
                const image = controller.getImageDataUri.bind(controller);
                w.__movieImageTimings = [];
                controller.getImageDataUri = async (options: any) => {
                    const timing = { width: options?.width, height: options?.height, start: performance.now(), elapsed: -1 };
                    w.__movieImageTimings.push(timing);
                    try { return await image(options); }
                    finally { timing.elapsed = performance.now() - timing.start; }
                };
                const model = w.__popupWidgetModel;
                const send = model.send.bind(model);
                w.__movieExportCaptures = [];
                model.send = (value: any) => {
                    const content = value.payload ?? value;
                    if (content.event === "visual_state_snapshot" && content.movie_frame) {
                        const frame = content.movie_frame;
                        w.__movieExportCaptures.push({ index: frame.frame_index, job: frame.job_id,
                            structure: content.structure_index, camera: content.snapshot });
                        if (w.__movieExportFault === "hold") {
                            w.__movieExportHeld = value;
                            return Promise.resolve({});
                        }
                        if (w.__movieExportFault === "corrupt") {
                            const corrupt = { ...content, movie_frame: { ...frame, data_uri: "data:image/png;base64,broken" } };
                            return send(value.payload ? { ...value, payload: corrupt } : corrupt);
                        }
                    }
                    return send(value);
                };
                w.__movieExportDeliverHeld = () => send(w.__movieExportHeld);
            });
            const nativeCancellation = await page.evaluate(async () => {
                const w = window as any;
                const c = w.__mirrorController;
                let release!: () => void;
                const held = new Promise<void>(resolve => { release = resolve; });
                const unrelated = c.plugin.runTask(w.Harness.Task.create("Unrelated Movie control", async (ctx: any) => {
                    await held;
                    await ctx.update("Unrelated task remains healthy");
                    return true;
                }), { createNewContext: true });
                const signal = new AbortController();
                let observed = false;
                const subscription = c.plugin.managers.task.events.progress.subscribe((event: any) => {
                    if (event.progress.root.progress.taskName === "Render Movie frame") {
                        observed = true;
                        signal.abort();
                    }
                });
                let aborted = false;
                try {
                    await c.getImageDataUri({ width: 640, height: 360, sampleLevel: 0, signal: signal.signal });
                } catch (error: any) {
                    aborted = error?.isAborted === true || error?.name === "AbortError";
                } finally {
                    subscription.unsubscribe();
                    release();
                }
                return { observed, aborted, unrelatedHealthy: await unrelated,
                    imageReserved: c.imageExportPending,
                    sampleLevel: c.plugin.helpers.viewportScreenshot.imagePass.props.multiSample.sampleLevel };
            });
            assert.deepEqual(nativeCancellation, { observed: true, aborted: true, unrelatedHealthy: true,
                imageReserved: false, sampleLevel: 4 });

            if (process.env.MOLSYSVIEWER_MOVIE_NATIVE_ONLY === "1") {
                console.log("[Movie native cancellation] " + JSON.stringify(nativeCancellation));
                return;
            }
            const sentinel = resolve(workspace, "preserve.mp4");
            await writeFile(sentinel, "keep existing movie");
            if (process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTIC === "1") {
                await command(page, { movie_export: { path: resolve(workspace, "fresh.zip"), width: 1280, height: 720,
                    timeout: Number(process.env.MOLSYSVIEWER_MOVIE_FRAME_TIMEOUT ?? 15) } });
                const result = await finished(page);
                assert.equal(result.ok, true, JSON.stringify(result));
                console.log(`[Movie reduced diagnostic] ${JSON.stringify(result.frames)}`);
                return;
            }
            await page.evaluate(() => { (window as any).__movieExportFault = "hold"; });
            const timeout = Number(process.env.MOLSYSVIEWER_MOVIE_FRAME_TIMEOUT ?? 15);
            await command(page, { movie_export: { path: sentinel, overwrite: true, timeout } });
            const started = performance.now();
            while (!await page.evaluate(() => !!(window as any).__movieExportHeld)) {
                const status = (await command(page, { movie_export_status: true })).movie_export_result;
                assert.equal(status, null, `Movie terminated before pending-frame cancellation: ${JSON.stringify(status)}`);
                assert.ok(performance.now() - started < 15_000, "No correlated Movie frame arrived.");
                await delay(100);
            }
            await command(page, { movie_export_cancel: true });
            const cancelled = await finished(page);
            assert.equal(cancelled.cancelled, true, JSON.stringify(cancelled));
            assert.equal(cancelled.owner_retired, true);
            assert.equal(await readFile(sentinel, "utf8"), "keep existing movie");
            await page.evaluate(async () => {
                const w = window as any;
                w.__movieExportFault = "corrupt";
                await w.__movieExportDeliverHeld();
            });
            await command(page, { movie_export: { path: sentinel, overwrite: true, timeout } });
            const corrupt = await finished(page);
            assert.equal(corrupt.ok, false);
            assert.match(corrupt.error, /PNG/);
            assert.equal(corrupt.owner_retired, true);
            assert.equal(await readFile(sentinel, "utf8"), "keep existing movie");

            await page.evaluate(() => { (window as any).__movieExportFault = undefined; });
            await command(page, { movie_export_legend: true });
            await page.locator("[data-molsysviewer-legend]").waitFor({ state: "visible" });
            // Declared data that is absent from the requesting canvas cannot
            // quietly disappear from a successful Movie.
            await page.locator("[data-molsysviewer-legend]").evaluate((element: HTMLElement) => { element.style.display = "none"; });
            await command(page, { movie_export: { path: sentinel, overwrite: true, timeout } });
            const overlay = await finished(page);
            assert.equal(overlay.ok, false);
            assert.match(overlay.error, /expand|overlay/i);
            assert.equal(await readFile(sentinel, "utf8"), "keep existing movie");
            await command(page, { movie_export_legend: false });
            await command(page, { movie_export: { path: sentinel, overwrite: true, format: "pngs", timeout: 0.05 } });
            const expired = await finished(page);
            assert.equal(expired.ok, false);
            assert.match(expired.error, /timeout|deadline/i);
            assert.equal(expired.owner_retired, true);
            assert.equal(await readFile(sentinel, "utf8"), "keep existing movie");
            for (const suffix of ["zip", "mp4"]) {
                const canvasSamples = await page.evaluate(() => JSON.stringify((window as any).__mirrorController.plugin.canvas3d.props.multiSample));
                await page.evaluate(() => { (window as any).__movieExportCaptures = []; });
                await command(page, { movie_export: { path: resolve(workspace, `movie.${suffix}`), width: 1280, height: 720, timeout } });
                const result = await finished(page);
                assert.equal(result.ok, true, JSON.stringify({ ...result, suffix,
                    image_timings: await page.evaluate(() => (window as any).__movieImageTimings) }));
                assert.equal(result.owner_retired, true);
                assert.deepEqual(result.frames.map((row: any) => row.time_ms), [0, 250, 500, 750]);
                assert.deepEqual(result.frames.map((row: any) => row.frames_written), [1, 2, 3, 4]);
                const captures = await page.evaluate(() => (window as any).__movieExportCaptures);
                assert.deepEqual(captures.map((row: any) => row.structure), [0, 0, 2, 2]);
                assert.equal(new Set(captures.map((row: any) => row.job)).size, 1);
                assert.equal(result.export.manifest.sampling.frame_count, 4);
                assert.equal(result.export.manifest.sampling.last_time_ms, 750);
                assert.equal(result.export.manifest.rendering.sample_level, 2);
                assert.equal(await page.evaluate(() => JSON.stringify((window as any).__mirrorController.plugin.canvas3d.props.multiSample)), canvasSamples);
                assert.equal(await page.evaluate(() => (window as any).__mirrorController.plugin.helpers.viewportScreenshot.imagePass.props.multiSample.sampleLevel), 4);
            }
            const evidence = process.env.MOLSYSVIEWER_MOVIE_EVIDENCE_DIR;
            if (evidence) {
                await mkdir(evidence, { recursive: true });
                for (const suffix of ["zip", "mp4"]) await copyFile(resolve(workspace, `movie.${suffix}`), resolve(evidence, `movie.${suffix}`));
            }
            const inspection = await command(page, { movie_export_verify: true });
            const verified = inspection.verified_video;
            if (evidence) {
                await writeFile(resolve(evidence, "browser-reference.json"), JSON.stringify(inspection.browser_reference));
            }
            const browserVideo = await page.evaluate(async ({ source, reference }) => {
                const video = document.createElement("video");
                video.muted = true;
                video.preload = "auto";
                video.src = "data:video/mp4;base64," + source;
                const wait = (event: string) => new Promise<void>((resolve, reject) => {
                    const timer = setTimeout(() => { done(); reject(new Error("Browser video decode timed out.")); }, 10_000);
                    const complete = () => { done(); resolve(); };
                    const fail = () => { done(); reject(new Error("Browser rejected the generated MP4.")); };
                    const done = () => { clearTimeout(timer); video.removeEventListener(event, complete); video.removeEventListener("error", fail); };
                    video.addEventListener(event, complete, { once: true });
                    video.addEventListener("error", fail, { once: true });
                });
                const ready = wait("loadeddata");
                video.load();
                try {
                    await ready;
                    const canvas = document.createElement("canvas");
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const context = canvas.getContext("2d")!;
                    let error = 0, count = 0;
                    const samples: unknown[] = [];
                    for (const frame of reference) {
                        const seeked = wait("seeked");
                        video.currentTime = frame.time;
                        await seeked;
                        context.drawImage(video, 0, 0);
                        const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
                        samples.push({ time: video.currentTime, pixels: frame.pixels.map((point: any) => ({ ...point,
                            actual: Array.from(pixels.slice((point.y * canvas.width + point.x) * 4, (point.y * canvas.width + point.x) * 4 + 3)) })) });
                        for (const point of frame.pixels) for (let channel = 0; channel < 3; channel++) {
                            error += Math.abs(pixels[(point.y * canvas.width + point.x) * 4 + channel] - point.rgb[channel]);
                            count++;
                        }
                    }
                    return { mean_color_error: error / count, sampled_channels: count,
                        width: canvas.width, height: canvas.height, duration: video.duration, samples };
                } finally { video.removeAttribute("src"); video.load(); }
            }, { source: (await readFile(resolve(workspace, "movie.mp4"))).toString("base64"), reference: inspection.browser_reference });
            if (evidence) await writeFile(resolve(evidence, "browser-decode.json"), JSON.stringify(browserVideo));
            assert.ok(browserVideo.mean_color_error < 12, JSON.stringify({ ...browserVideo, samples: undefined }));
            assert.equal(browserVideo.sampled_channels, 384);
            assert.equal(verified.frames, 4);
            assert.deepEqual(verified.size, [1280, 720]);
            assert.ok(verified.scene_change > 0.1);
            assert.equal(verified.embedded_recipe, true);
            assert.deepEqual((await readdir(workspace)).filter(name => name.includes(".movie-")), []);
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            if (evidence) {
                await writeFile(resolve(evidence, "verified.json"), JSON.stringify({ ...verified, timeout, nativeCancellation, browserVideo,
                    image_timings: await page.evaluate(() => (window as any).__movieImageTimings) }, null, 2));
            }
            console.log(`[E2E Movie export] ${JSON.stringify({ ...verified, timeout, nativeCancellation,
                browserVideo: { ...browserVideo, samples: undefined },
                image_timings: await page.evaluate(() => (window as any).__movieImageTimings) })}; cancellation, late reply, invalid PNG and overlays preserve destination.`);
        } catch (error) {
            if (diagnosticPage && !diagnosticPage.isClosed()) {
                console.error("Movie diagnostic", JSON.stringify(await diagnosticPage.evaluate(() => {
                    const w = window as any;
                    const c = w.__mirrorController;
                    const frame = c.trajectory.getTrajectoryState().currentFrame;
                    return { image_timings: w.__movieImageTimings, captures: w.__movieExportCaptures,
                        frame, updating: c.plugin.state.data.behaviors.isUpdating.value,
                        frameReady: c.trajectory.isCaptureFrameReady(frame), boxReady: c.boxDisplay.isFrameReady(frame),
                        shapesReady: c.shapes.isFrameReady(frame), interactionsReady: c.interactions.isFrameReady(frame),
                        labelsReady: c.annotations.isGeometryCurrent(), movieSafe: c.movie.isCaptureSafe,
                        canvasLive: !!c.readMovingVisualState(), errors: w.__popupFixtureErrors };
                })));
                console.error("Movie authority", JSON.stringify((await command(diagnosticPage, { movie_export_status: true })).movie_export_result));
            }
            throw error;
        } finally {
            await release?.();
            await Promise.all([browser.close(), bridge?.close()]);
        }
    });
}

run().catch(error => { console.error(error); process.exitCode = 1; });
