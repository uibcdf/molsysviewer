import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, rename, writeFile, copyFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import type { Frame, Page } from "playwright";

async function seek(page: Page | Frame, time: number) {
    await page.evaluate(async at => (window as any).__molsysviewerDocsMovie.seek(at), time);
}
async function native(page: Page | Frame) {
    return page.evaluate(() => {
        const c = (window as any).__molsysviewerDocsController;
        const entry = c.state.regionIndex.get("site");
        const params = c.plugin.state.data.cells.get(entry.representations[0]).params.values;
        const refs = c.state.tagIndex.get(c.state.taggedKey("shape", "site"));
        const repr = [...refs].map((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr)
            .find((repr: any) => repr?.getAllLoci?.().some((loci: any) => loci.shape));
        const shape = repr.getAllLoci().find((loci: any) => loci.shape).shape;
        const labels = [...c.state.tagIndex.get(c.state.taggedKey("annotation", "note"))]
            .map((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr)
            .filter((repr: any) => typeof repr?.props.customText === "string");
        const renderer = c.plugin.canvas3d.props.renderer;
        const interaction = c.interactions.summaries.find((row: any) => row.tag === "contacts");
        const ref = c.interactions.refs.get("contacts");
        const linkRepr = ref ? c.plugin.state.data.cells.get(ref)?.obj?.data?.repr : null;
        return { frame: c.trajectory.getTrajectoryState().currentFrame, representation: params.type.name,
            alpha: params.type.params.alpha, sphereColor: shape.getColor(0), sphereAlpha: repr.state.alphaFactor,
            regionHidden: c.plugin.state.data.cells.get(entry.representations[0]).state.isHidden === true,
            caption: labels[0].props.customText, camera: c.getCameraSnapshot(),
            interaction: { status: interaction.status, frame: interaction.frame, count: interaction.n_observations,
                colour: linkRepr?.getAllLoci().find((loci: any) => loci.shape)?.shape.getColor(0) ?? null,
                alpha: linkRepr?.state.alphaFactor ?? null },
            background: renderer.backgroundColor, ambient: renderer.ambientIntensity, diffuse: renderer.light[0].intensity,
            spin: c.isSpinActive };
    });
}
function check(actual: any, expected: any) {
    const values = new Map(expected.appearance.map((row: any) => [JSON.stringify([row.domain, row.tag, row.property]), row.value]));
    const value = (domain: string, tag: string | null, property: string) => values.get(JSON.stringify([domain, tag, property]));
    assert.equal(actual.frame, expected.structure_index);
    assert.equal(actual.representation, value("region", "site", "representation"));
    assert.ok(Math.abs(actual.alpha - Number(value("region", "site", "alpha"))) < 1e-7);
    assert.equal(actual.sphereColor, value("shape", "site", "color"));
    assert.ok(Math.abs(actual.sphereAlpha - Number(value("shape", "site", "alpha"))) < 1e-7);
    assert.equal(actual.caption, value("annotation", "note", "text"));
    assert.equal(actual.background, value("scene", null, "background"));
    const light = value("scene", null, "lighting") as any;
    assert.ok(Math.abs(actual.ambient - light.ambient) < 1e-7);
    assert.ok(Math.abs(actual.diffuse - light.diffuse) < 1e-7);
    assert.equal(actual.spin, false);
    assert.equal(actual.regionHidden, !expected.visibility.find((row: any) => row.domain === "region" && row.tag === "site").visible);
    assert.equal(actual.interaction.frame, expected.structure_index);
    assert.ok(!["pending", "unavailable", "render-error"].includes(actual.interaction.status));
    if (actual.interaction.count) {
        assert.equal(actual.interaction.colour, value("interaction", "contacts", "color"));
        assert.ok(Math.abs(actual.interaction.alpha - Number(value("interaction", "contacts", "alpha"))) < 1e-7);
    }
    for (const axis of ["position", "target", "up"]) expected.camera[axis].forEach((v: number, i: number) => {
        assert.ok(Math.abs(actual.camera[axis][i] - v) < 1e-5, `${axis}[${i}]`);
    });
}

async function run() {
    await withFixtureWorkspace("movie-web", async workspace => {
        const here = dirname(fileURLToPath(import.meta.url));
        const fixture = spawnSync(process.env.PYTHON || "python", [resolve(here, "movie-web-fixture.py"), workspace], {
            cwd: resolve(here, "../.."), env: fixtureEnvironment(workspace), encoding: "utf-8", timeout: 90000,
        });
        assert.equal(fixture.status, 0, fixture.stderr + fixture.stdout);
        if (process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR) {
            await copyFile(resolve(workspace, "fixture-origin.json"), resolve(process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR, "fixture-origin.json"));
        }
        const expected = JSON.parse(await readFile(resolve(workspace, "expected.json"), "utf8"));
        const moved = resolve(workspace, "downloaded"); await mkdir(moved);
        await rename(resolve(workspace, "movie.html"), resolve(moved, "movie.html"));
        const browser = await chromium.launch();
        try {
            const page = await browser.newPage(); await page.context().setOffline(true);
            const errors: string[] = [], requests: string[] = [];
            page.on("pageerror", error => errors.push(String(error)));
            page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
            page.on("request", request => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
            await page.goto(pathToFileURL(resolve(moved, "movie.html")).href);
            await page.waitForFunction(() => document.querySelector('[data-molsysviewer-movie-ready="true"], [data-molsysviewer-error="true"]'), undefined, { timeout: 45000 });
            assert.deepEqual(errors, [], "Movie initialization failed");
            for (const at of [0, 750, 250, 1000, 500, 0]) { await seek(page, at); check(await native(page), expected.samples[at]); }
            console.log("PASS Movie web native forward/reverse samples");
            await page.evaluate(async () => (window as any).__molsysviewerDocsController.handleMessage({ op: "set_background_color", color: 0x123456 }));
            await seek(page, 0); check(await native(page), expected.samples[0]);
            // A seek storm is bounded by the one writer; the last accepted seek wins.
            await page.evaluate(async () => { const player = (window as any).__molsysviewerDocsMovie;
                await Promise.all([player.seek(1000), player.seek(750), player.seek(250)]); });
            check(await native(page), expected.samples[250]);
            await page.getByRole("button", { name: "Restart", exact: true }).click();
            await page.waitForFunction(() => (window as any).__molsysviewerDocsMovie.state.time_ms === 0);
            await seek(page, 0); await page.getByRole("button", { name: "Play", exact: true }).click();
            await page.waitForFunction(() => { const s = (window as any).__molsysviewerDocsMovie.state; return s.time_ms === 1000 && !s.playing; }, undefined, { timeout: 30000 });
            check(await native(page), expected.samples[1000]);
            if (process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR) {
                await page.screenshot({ path: resolve(process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR, "offline-movie.png") });
                await copyFile(resolve(moved, "movie.html"), resolve(process.env.MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR, "offline-movie.html"));
            }
            // Leave enough real duration to pause after a completed native draw.
            // A one-second clip can finish before a physical click reaches it.
            await page.goto(pathToFileURL(resolve(workspace, "long.html")).href);
            await page.waitForFunction(() => document.querySelector('[data-molsysviewer-movie-ready="true"]'), undefined, { timeout: 45000 });
            await page.getByRole("button", { name: "Play", exact: true }).click();
            await page.waitForFunction(() => (window as any).__molsysviewerDocsMovie.state.time_ms > 0);
            await page.getByRole("button", { name: "Pause", exact: true }).click();
            await page.evaluate(async () => (window as any).__molsysviewerDocsMovie.pause());
            assert.equal(await page.evaluate(() => (window as any).__molsysviewerDocsMovie.state.playing), false);
            // A conventional iframe receives the same independent offline player.
            await writeFile(resolve(moved, "embed.html"), '<!doctype html><iframe title="Molecular movie" src="movie.html" style="width:640px;height:420px;border:0"></iframe>');
            await page.goto(pathToFileURL(resolve(moved, "embed.html")).href);
            const frame = await page.waitForSelector("iframe").then(el => el.contentFrame()); assert.ok(frame);
            await frame.waitForFunction(() => (window as any).__molsysviewerDocsMovie?.state.time_ms === 0, undefined, { timeout: 45000 });
            await seek(frame, 500); check(await native(frame), expected.samples[500]);
            await page.goto(pathToFileURL(resolve(workspace, "gates.html")).href);
            await page.waitForFunction(() => document.querySelector('[data-molsysviewer-movie-ready="true"]'), undefined, { timeout: 45000 });
            for (const at of [0, 750, 0]) {
                await seek(page, at);
                const visible = await page.evaluate(() => { const c = (window as any).__molsysviewerDocsController;
                    return ["site", "gate-hidden"].map(tag => [...c.state.tagIndex.get(c.state.taggedKey("shape", tag))]
                        .some((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr?.renderObjects?.some((ro: any) => ro.state.visible))); });
                assert.deepEqual(visible, at < 500 ? [true, false] : [false, false]);
            }
            await page.evaluate(() => (window as any).__molsysviewerDocsMovie.dispose());
            assert.equal(await page.locator('[data-molsysviewer-movie-player]').count(), 0);
            assert.deepEqual(requests, [], "offline presentation must not request remote assets");
            assert.deepEqual(errors, []);
            console.log("PASS Movie web: relocated offline file, native forward/reverse samples, one writer, Play/Pause/Restart, final draw, iframe, layer gates and disposal");
        } finally { await browser.close(); }
    });
}
run().catch(error => { console.error(error); process.exitCode = 1; });
