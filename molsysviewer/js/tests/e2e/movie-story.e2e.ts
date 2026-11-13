import assert from "node:assert/strict";
import { copyFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { setTimeout as delay } from "node:timers/promises";
import type { Page } from "playwright";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { PythonFixtureBridge } from "./python-fixture-bridge";

async function operation(page: Page, event: any) {
    await page.evaluate(async value => (window as any).__popupWidgetModel.send({ movie_story: value }), event);
    const deadline = performance.now() + 120000;
    do {
        const reply = await page.evaluate(async () => (window as any).__popupWidgetModel.send({ movie_story_status: true }));
        if (reply.movie_story_result) {
            assert.equal(reply.movie_story_result.ok, true, JSON.stringify(reply.movie_story_result));
            return reply.movie_story_result;
        }
        await delay(100);
    } while (performance.now() < deadline);
    throw new Error("Molecular story did not complete its correlated operation.");
}

async function native(page: Page) {
    return page.evaluate(() => {
        const c = (window as any).__mirrorController ?? (window as any).__molsysviewerDocsController;
        const representations = (kind: string, tag: string) => [...(c.state.tagIndex.get(c.state.taggedKey(kind, tag)) ?? [])]
            .map((ref: any) => c.plugin.state.data.cells.get(ref)).filter((cell: any) => cell?.obj?.data?.repr);
        const visible = (kind: string, tag: string) => representations(kind, tag)
            .some((cell: any) => cell.obj.data.repr.renderObjects.some((object: any) => object.state.visible));
        const region = (tag: string) => { const entry = c.state.regionIndex.get(tag);
            const cells = entry.representations.map((ref: string) => c.plugin.state.data.cells.get(ref));
            return { visible: cells.some((cell: any) => cell.obj.data.repr.renderObjects.some((obj: any) => obj.state.visible)),
                representation: cells[0].params.values.type.name }; };
        const phase = representations("annotation", "phase").flatMap((cell: any) => [cell.obj.data.repr.props.customText,
            ...cell.obj.data.repr.getAllLoci().map((loci: any) => loci.shape?.sourceData?.text)]).find((v: any) => typeof v === "string");
        const interaction = c.interactions.summaries.find((row: any) => row.tag === "contacts");
        const ref = c.interactions.refs.get("contacts");
        const repr = ref ? c.plugin.state.data.cells.get(ref)?.obj?.data?.repr : undefined;
        const shape = repr?.getAllLoci().find((loci: any) => loci.shape)?.shape;
        const light = c.plugin.canvas3d.props.renderer;
        const measure = c.measurements.specsByTag.get("candidate-distance");
        return { frame: c.trajectory.getTrajectoryState().currentFrame, camera: c.getCameraSnapshot(),
            ligand: region("ligand"), pocket: region("pocket"), phase,
            labelVisible: visible("annotation", "ligand-label"), measurementVisible: visible("measurement", "candidate-distance"),
            measurementAngstrom: c.measurements.computeMeasurementValue(measure.options.picks_atom_indices, measure.options),
            interaction: { status: interaction.status, count: interaction.n_observations,
                sourceHidden: interaction.hidden, visible: !!repr?.renderObjects.some((object: any) => object.state.visible),
                links: shape?.sourceData.links ?? [], observations: shape?.sourceData.interaction?.observations ?? [] },
            lighting: { ambient: light.ambientIntensity, diffuse: light.light[0].intensity },
            plotIndex: (document.querySelector('[data-molsysviewer-plot-navigation="candidate-distance"] input') as HTMLInputElement).value };
    });
}

function check(actual: any, expected: any) {
    const sample = expected.sample;
    const visible = (domain: string, tag: string) => sample.visibility.find((row: any) => row.domain === domain && row.tag === tag).visible;
    const appearance = (domain: string, tag: string | null, property: string) => sample.appearance.find((row: any) => row.domain === domain && row.tag === tag && row.property === property).value;
    assert.equal(actual.frame, sample.structure_index);
    for (const axis of ["position", "target", "up"]) sample.camera[axis].forEach((value: number, index: number) => {
        assert.ok(Math.abs(actual.camera[axis][index] - value) < 1e-5, `${axis}[${index}]`);
    });
    assert.equal(actual.ligand.visible, visible("region", "ligand"));
    assert.equal(actual.pocket.visible, visible("region", "pocket"));
    assert.equal(actual.labelVisible, visible("annotation", "ligand-label"));
    assert.equal(actual.measurementVisible, visible("measurement", "candidate-distance"));
    assert.ok(Math.abs(actual.measurementAngstrom - expected.measurement_nm * 10) < 1e-4, "native measurement uses current coordinates and angstroms");
    assert.equal(actual.ligand.representation, appearance("region", "ligand", "representation"));
    assert.equal(actual.phase, appearance("annotation", "phase", "text"));
    assert.equal(actual.plotIndex, String(sample.structure_index));
    const light = appearance("scene", null, "lighting");
    assert.ok(Math.abs(actual.lighting.ambient - light.ambient) < 1e-7);
    assert.ok(Math.abs(actual.lighting.diffuse - light.diffuse) < 1e-7);
    assert.equal(actual.interaction.status, expected.interaction.status);
    assert.equal(actual.interaction.count, expected.interaction.n_observations);
    // Offline series retain source/baseline intent. Movie visibility is an
    // override applied to native cells; assert the physical rendering itself.
    assert.equal(actual.interaction.visible, visible("interaction", "contacts") && expected.interaction.links.length > 0,
        `physical interaction visibility at ${sample.time_ms} ms`);
    assert.equal(actual.interaction.links.length, expected.interaction.links.length);
    expected.interaction.links.forEach((link: any, index: number) => {
        assert.equal(actual.interaction.observations[index].occurrence_index, link.occurrence_index);
        for (const [axis, field] of [["start", "start"], ["end", "end"]]) link[axis].forEach((value: number, i: number) => {
            assert.ok(Math.abs(actual.interaction.links[index][field][i] - value * 10) < 1e-5, "native link endpoints use angstroms");
        });
    });
}

async function capture(page: Page) {
    return page.evaluate(async () => {
        const c = (window as any).__mirrorController;
        return c.getImageDataUri({ width: 1280, height: 720, transparent: false, preset: "current", sampleLevel: 0, signal: new AbortController().signal,
            movieOverlays: c.snapshotMovieOverlays(1280, 720, [
                { kind: "trajectory_plot", tag: "candidate-distance" }, { kind: "colour_legend", tag: "colour-legend" },
            ]) });
    });
}

async function run() {
    await withFixtureWorkspace("movie-story", async workspace => {
        const here = dirname(fileURLToPath(import.meta.url));
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined, release: (() => Promise<void>) | undefined;
        try {
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            const errors: string[] = []; page.on("pageerror", error => errors.push(String(error)));
            const env = { ...fixtureEnvironment(workspace), MOLSYSVIEWER_MOVIE_STORY_WORKSPACE: workspace };
            bridge = new PythonFixtureBridge(resolve(here, "movie-story-bridge.py"), resolve(here, "../../../.."), 30000, { env });
            release = await mountCanvasPopupFixture(page, bridge); await captureCanvasPopupControllers(page);
            await page.waitForSelector('[data-molsysviewer-plot-navigation="candidate-distance"]');
            await page.locator('[data-molsysviewer-datacard="candidate-distance"]').evaluate((el: HTMLElement) => {
                el.style.left = "14px"; el.style.top = `${el.parentElement!.clientHeight - el.getBoundingClientRect().height - 14}px`;
            });
            // Use actual Studio forms to refine the Python-authored story, then
            // consume the newly accepted recipe through all other public paths.
            await page.evaluate(() => { const c = (window as any).__mirrorController;
                c.setPanelMode("navigate", true); c.groupPanel.setExpanded(true); c.groupPanel.openSection("movie"); });
            await page.getByRole("tab", { name: "Timeline", exact: true }).waitFor();
            await page.locator('[data-molsysviewer-movie-track="phase"]').click();
            await page.getByRole("button", { name: "Edit 1.000 s", exact: true }).click();
            await page.getByLabel("Text", { exact: true }).fill("Relaxed Buch candidates: H-A <= 0.40 nm");
            await page.getByRole("button", { name: "Save key", exact: true }).click();
            await page.waitForFunction(() => { const p = (window as any).__mirrorController.groupPanel.moviePanel;
                return p?.state && !p.state.busy && p.pending === null; });
            const metadata = await operation(page, { action: "metadata" });
            assert.equal(metadata.recipe.tracks.find((track: any) => track.tag === "phase").keys[0].value,
                "Relaxed Buch candidates: H-A <= 0.40 nm");
            await page.getByRole("tab", { name: "Preview", exact: true }).click();
            await page.getByLabel("Movie time (seconds)", { exact: true }).fill("1");
            await page.getByRole("button", { name: "Go to time", exact: true }).click();
            await page.waitForFunction(() => { const p = (window as any).__mirrorController.groupPanel.moviePanel;
                return p?.state && !p.state.busy && p.pending === null; });
            check(await native(page), metadata.expected[1000]);
            await page.evaluate(() => (window as any).__mirrorController.setPanelMode("navigate", false));
            const times = [0, 500, 1000, 1500, 2000, 2500];
            const references: string[] = [], snapshots: any[] = [];
            for (const time of [...times, 2000, 1000, 0]) {
                await operation(page, { action: "seek", time_ms: time });
                const observed = await native(page); check(observed, metadata.expected[time]);
                snapshots.push({ time, observed });
                if (references.length < 6) references.push(await capture(page));
            }
            await operation(page, { action: "references", images: references });
            const played = await operation(page, { action: "play" }); assert.equal(played.sample.time_ms, 3000);
            check(await native(page), metadata.expected[3000]);
            const exports: any[] = [];
            for (const suffix of [".zip", ".mp4", ".webm"]) exports.push(await operation(page, { action: "export", suffix }));
            await operation(page, { action: "seek", time_ms: 2000 });
            const saved = await operation(page, { action: "save" }); assert.equal(saved.frame, 2);
            await operation(page, { action: "export", suffix: ".html" });
            const evidence = process.env.MOLSYSVIEWER_MOVIE_EVIDENCE_DIR;
            if (evidence) {
                await writeFile(resolve(evidence, "native-snapshots.json"), JSON.stringify({ metadata, snapshots, exports }, null, 2));
                await copyFile(resolve(workspace, "story.msv"), resolve(evidence, "story.msv"));
                await page.screenshot({ path: resolve(evidence, "live-story.png") });
            }
            await release(); release = undefined; await bridge.close(); bridge = undefined;
            await page.goto("about:blank");
            // Recover into an independent authority and native runtime. No detector runs.
            bridge = new PythonFixtureBridge(resolve(here, "movie-story-bridge.py"), resolve(here, "../../../.."), 30000,
                { env: { ...env, MOLSYSVIEWER_MOVIE_STORY_SESSION: resolve(workspace, "story.msv") } });
            release = await mountCanvasPopupFixture(page, bridge); await captureCanvasPopupControllers(page);
            const restored = await operation(page, { action: "metadata" });
            assert.equal(restored.frame, 2); assert.deepEqual(restored.recipe, metadata.recipe);
            assert.equal(restored.origin.analysis_signature, metadata.origin.analysis_signature);
            assert.deepEqual(restored.origin.analysis_signatures, metadata.origin.analysis_signatures);
            for (const time of [2000, 1500, 1000, 2500, 0]) {
                await operation(page, { action: "seek", time_ms: time }); check(await native(page), metadata.expected[time]);
            }
            await release(); release = undefined; await bridge.close(); bridge = undefined;
            // The complete story now plays offline with no scientific/Python owner.
            await page.context().setOffline(true);
            const requests: string[] = []; page.on("request", request => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
            await page.goto(pathToFileURL(resolve(workspace, "story.html")).href);
            await page.waitForFunction(() => document.querySelector('[data-molsysviewer-movie-ready="true"]'), undefined, { timeout: 45000 });
            for (const time of [...times, 2000, 1000, 0]) {
                await page.evaluate(async value => (window as any).__molsysviewerDocsMovie.seek(value), time);
                check(await native(page), metadata.expected[time]);
            }
            await page.getByRole("button", { name: "Play", exact: true }).click();
            await page.waitForFunction(() => { const state = (window as any).__molsysviewerDocsMovie.state;
                return state.time_ms === 3000 && !state.playing; }, undefined, { timeout: 30000 });
            check(await native(page), metadata.expected[3000]);
            assert.deepEqual(requests, []); assert.deepEqual(errors, []);
            if (evidence) await page.screenshot({ path: resolve(evidence, "offline-story.png") });
            console.log("PASS integrated molecular Movie: native forward/reverse/preview, explicit sparse coverage/identity/geometry, independent session recovery, PNG/MP4/WebM reference pixels, and offline full-story playback; no hidden scientific calls");
        } finally { await release?.(); await bridge?.close(); await browser.close(); }
    });
}
run().catch(error => { console.error(error); process.exit(1); });
