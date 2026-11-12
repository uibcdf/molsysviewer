import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { writeFile } from "node:fs/promises";
import { chromium } from "./e2e-browser";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import type { Page } from "playwright";

async function openMovie(page: Page) {
    await page.evaluate(() => {
        const c = (window as any).__mirrorController;
        c.setPanelMode("navigate", true); c.groupPanel.setExpanded(true); c.groupPanel.openSection("movie");
    });
    const root = page.locator('[data-molsysviewer-group-panel-section="movie"]');
    // The section owns a normal Movie tab; no private plan or verdict is supplied.
    await page.getByRole("tab", { name: "Timeline", exact: true }).waitFor();
    return root;
}
async function idle(page: Page) {
    await page.waitForFunction(() => {
        const c = (window as any).__mirrorController;
        const p = c.groupPanel.moviePanel;
        return p?.state && !p.state.busy && p.pending === null;
    });
}

async function run() {
    const dir = dirname(fileURLToPath(import.meta.url));
    await withFixtureWorkspace("movie-studio", async workspace => {
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined, release: (() => Promise<void>) | undefined;
        let primary: Page | undefined, popup: Page | undefined, panel: Page | undefined;
        const errors: string[] = [];
        try {
            bridge = new PythonFixtureBridge(resolve(dir, "movie-studio-bridge.py"), resolve(dir, "../../../.."),
                30_000, { env: fixtureEnvironment(workspace) });
            const page = primary = await browser.newPage({ viewport: { width: 1200, height: 900 } });
            page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            await page.evaluate(() => {
                const w = window as any; w.__movieEditorRequests = [];
                w.__popupWidgetModel.on("msg:custom", (event: any) => {
                    const message = event.payload ?? event;
                    if (message.op === "request_visual_state") w.__movieEditorRequests.push(message);
                });
            });
            const status = async () => (await page.evaluate(async () =>
                (window as any).__popupWidgetModel.send({ movie_editor_status: true }))).movie_editor;
            await openMovie(page); await idle(page);
            await page.getByLabel("Duration (seconds)", { exact: true }).fill("0.5");
            await page.getByRole("button", { name: "Capture initial scene", exact: true }).click(); await idle(page);
            const baseline = (await status()).recipe;
            assert.equal(baseline.molsysmovie_version, 2); assert.equal(baseline.duration_ms, 500);
            await page.getByLabel("Track name", { exact: true }).fill("frames");
            await page.getByLabel("Target", { exact: true }).selectOption("structure");
            await page.getByLabel("Key time (seconds)", { exact: true }).fill("0.25");
            await page.getByLabel("Structure", { exact: true }).fill("2");
            await page.getByRole("button", { name: "Save key", exact: true }).click(); await idle(page);
            await page.getByRole("button", { name: "New track", exact: true }).click();
            await page.getByLabel("Track name", { exact: true }).fill("hide-site");
            await page.getByLabel("Target", { exact: true }).selectOption("region");
            await page.getByLabel("Object name in the initial scene", { exact: true }).fill("site");
            await page.getByLabel("Key time (seconds)", { exact: true }).fill("0.25");
            await page.getByLabel("Visible", { exact: true }).uncheck();
            await page.getByRole("button", { name: "Save key", exact: true }).click(); await idle(page);
            assert.equal((await status()).recipe.tracks.length, 2);
            // Input drafts survive a backend summary refresh and tab navigation.
            await page.getByLabel("Track name", { exact: true }).fill("draft-kept");
            await page.evaluate(async () => (window as any).__popupWidgetModel.send({ movie_editor_duration_ms: 750 }));
            await page.getByRole("button", { name: "Use kept draft", exact: true }).waitFor();
            assert.equal(await page.getByRole("button", { name: "Save key", exact: true }).isDisabled(), true);
            await page.getByRole("button", { name: "Use kept draft", exact: true }).click(); await idle(page);
            await page.getByRole("tab", { name: "Preview", exact: true }).click();
            await page.getByLabel("Movie time (seconds)", { exact: true }).fill("0.4");
            await page.getByRole("button", { name: "Go to time", exact: true }).click(); await idle(page);
            assert.equal((await status()).frame, 2);
            await page.getByRole("tab", { name: "Timeline", exact: true }).click();
            assert.equal(await page.getByLabel("Track name", { exact: true }).inputValue(), "draft-kept");
            const diagnostics = process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR;
            if (diagnostics) await page.screenshot({ path: resolve(diagnostics, "movie-studio-editor.png") });
            const popupOpened = page.waitForEvent("popup");
            await page.getByTitle("Open popup", { exact: true }).click(); popup = await popupOpened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => !!(window as any).__mirrorController?.getStructureData());
            await openMovie(popup); await idle(popup);
            await popup.getByLabel("Track name", { exact: true }).fill("camera-end");
            await popup.getByLabel("Key time (seconds)", { exact: true }).fill("0.5");
            const mark = await page.evaluate(() => (window as any).__movieEditorRequests.length);
            await popup.getByRole("button", { name: "Capture this camera as key", exact: true }).click(); await idle(popup);
            const endpoint = await popup.evaluate(() => (window as any).molsysviewer_popup_channel.popupEndpointId);
            const requests = await page.evaluate(mark => (window as any).__movieEditorRequests.slice(mark), mark);
            assert.ok(requests.length && requests.every((request: any) => request.target_endpoint_id === endpoint));
            assert.equal((await status()).recipe.tracks.length, 3);
            // Observe the real controller created by this canvas's nested popup too.
            await captureCanvasPopupControllers(popup);
            const opened = popup.waitForEvent("popup");
            await popup.getByTitle("Popout panel to external window", { exact: true }).click(); panel = await opened;
            panel.on("pageerror", error => errors.push(String(error)));
            await panel.waitForFunction(() => !!(window as any).__mirrorController);
            await openMovie(panel); await idle(panel);
            await panel.getByRole("tab", { name: "Preview", exact: true }).click();
            await panel.getByLabel("Loop preview", { exact: true }).check();
            await panel.getByRole("button", { name: "Play", exact: true }).click();
            await panel.getByRole("button", { name: "Pause", exact: true }).waitFor({ state: "visible" });
            await panel.waitForFunction(() => (window as any).__mirrorController.groupPanel.moviePanel.state.busy === "movie_play");
            await panel.getByRole("button", { name: "Pause", exact: true }).click(); await idle(panel);
            const path = resolve(workspace, "studio-movie.zip");
            await panel.getByRole("tab", { name: "Export", exact: true }).click();
            await panel.getByLabel("Output path in Python session (.mp4, .webm or .zip)", { exact: true }).fill(path);
            await panel.getByLabel("Frames per second", { exact: true }).fill("2");
            await panel.getByLabel("Width (pixels)", { exact: true }).fill("320");
            await panel.getByLabel("Height (pixels)", { exact: true }).fill("180");
            await panel.getByRole("button", { name: "Export Movie", exact: true }).click(); await idle(panel);
            const result = await page.evaluate(async path => (window as any).__popupWidgetModel.send({ movie_editor_archive: path }), path);
            assert.equal(result.archive.frames, 2); assert.ok(result.archive.bytes > 1000);
            assert.deepEqual(result.archive.manifest.resolution, { width: 320, height: 180 });
            assert.deepEqual(result.archive.manifest.recipe, (await status()).recipe);
            const final = await status(); assert.equal(final.pending, 0); assert.equal(final.busy, false); assert.equal(final.source_unchanged, true);
            assert.deepEqual(errors, []);
            if (diagnostics) await panel.screenshot({ path: resolve(diagnostics, "movie-studio-export.png") });
            console.log("[Movie Studio] Typed scene keys, draft preservation, real seeks, popup-owned capture, detached preview/pause and native PNG export received.");
        } catch (error) {
            const output = process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR;
            if (output) {
                const target = panel ?? popup ?? primary;
                await target?.screenshot({ path: resolve(output, "movie-studio-failure.png") }).catch(() => {});
                const state = await target?.evaluate(() => {
                    const c = (window as any).__mirrorController, p = c?.groupPanel?.moviePanel;
                    return { state: p?.state, pending: p?.pending, request: p?.request,
                        text: p?.host?.textContent?.slice(0, 2500), errors: (window as any).__popupFixtureErrors };
                }).catch(() => undefined);
                await writeFile(resolve(output, "movie-studio-failure.json"), JSON.stringify({ error: String(error), state, errors }, null, 2));
            }
            throw error;
        } finally { await panel?.close(); await popup?.close(); await release?.(); await browser.close(); await bridge?.close(); }
    });
}
run().catch(error => { console.error(error); process.exit(1); });
