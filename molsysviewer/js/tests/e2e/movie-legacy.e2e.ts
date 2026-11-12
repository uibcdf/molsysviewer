/** Independent receiving of reviewed legacy migration; retains movie-seek's separate verdict. */
import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import type { Page } from "playwright";

async function command(page: Page, value: Record<string, unknown>) {
    return page.evaluate(async message => (window as any).__popupWidgetModel.send(message), value);
}

async function result(page: Page, request: Record<string, unknown>, select: (reply: any) => any) {
    const deadline = performance.now() + 25_000;
    do {
        const reply = select(await command(page, request));
        if (reply) {
            assert.equal(reply.ok, true, reply.error);
            return reply;
        }
        await delay(200);
    } while (performance.now() < deadline);
    throw new Error("Legacy migration operation did not return its draw verdict.");
}

async function drawn(page: Page, at: number, frame: number) {
    await page.waitForFunction(({ at, frame }) => {
        const c = (window as any).__mirrorController;
        const hidden = (ref: string) => c.plugin.state.data.cells.get(ref)?.state.isHidden === true;
        const region = c.state.regionIndex.get("site")?.representations ?? [];
        const shapes = [...(c.state.tagIndex.get(c.state.taggedKey("shape", "site")) ?? [])] as string[];
        const position = [30 * at / 1000, 0, 30 * (1 - at / 1000)];
        return c.trajectory.getTrajectoryState().currentFrame === frame
            && c.getCameraSnapshot().position.every((value: number, i: number) => Math.abs(value - position[i]) < 1e-6)
            && region.length > 0 && region.every((ref: string) => hidden(ref) === (at === 1000))
            && shapes.length > 0 && shapes.every(ref => !hidden(ref));
    }, { at, frame });
    await page.evaluate(async () => {
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

async function run() {
    const dir = dirname(fileURLToPath(import.meta.url));
    await withFixtureWorkspace("movie-legacy", async workspace => {
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
            await command(page, { movie_use_legacy: true });
            await command(page, { movie_seek: 0 });
            await result(page, { movie_seek_status: true }, r => r.movie_seek_result);
            const opened = page.waitForEvent("popup");
            await page.getByTitle("Open popup", { exact: true }).click();
            popup = await opened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => (window as any).__mirrorController?.getStructureData()?.elementCount === 62);
            for (const [at, frame] of [[250, 1], [249, 0], [750, 2], [1000, 2], [100, 0], [0, 0]]) {
                await command(page, { movie_seek: at });
                const received = await result(page, { movie_seek_status: true }, r => r.movie_seek_result);
                assert.equal(received.frame, frame);
                assert.equal(received.sample.structure_index, frame);
                await drawn(page, at, frame);
                await drawn(popup, at, frame);
            }
            await command(page, { movie_preview_save: resolve(workspace, "legacy.msv") });
            const saved = await result(page, { movie_preview_status: true }, r => r.movie_preview_result.save);
            assert.ok(saved.same_recipe);
            assert.equal(saved.import_schema, "molsysviewer.movie_import@2");
            assert.equal(saved.source_version, 1);
            assert.equal(saved.source_binding, null);
            await command(page, { movie_preview_play: { loop: false, start: 200 } });
            const played = await result(page, { movie_preview_status: true }, r => r.movie_preview_result.play);
            assert.equal(played.sample.time_ms, 1000);
            assert.equal(played.sample.structure_index, 2);
            await drawn(page, 1000, 2);
            await drawn(popup, 1000, 2);
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log("[E2E Movie legacy] Reviewed migration, rounded steps, actual primary/popup draws, preview and session agree.");
        } finally {
            await popup?.close();
            await release?.();
            await Promise.all([browser.close(), bridge?.close()]);
        }
    });
}

run().catch(error => { console.error(error); process.exitCode = 1; });
