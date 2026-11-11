import assert from "node:assert/strict";
import { copyFile, mkdir, writeFile } from "node:fs/promises";
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

async function operation(page: Page, event: Record<string, unknown>) {
    await command(page, { movie_appearance: event });
    const deadline = performance.now() + 80_000;
    do {
        const result = (await command(page, { movie_appearance_status: true })).movie_appearance_result;
        if (result) { assert.equal(result.ok, true, result.traceback ?? result.error); return result; }
        await delay(100);
    } while (performance.now() < deadline);
    throw new Error("Movie appearance did not complete.");
}

async function native(page: Page) {
    return page.evaluate(() => {
        const c = (window as any).__mirrorController;
        const region = c.state.regionIndex.get("site");
        const regionRef = region.representations[0];
        const values = c.plugin.state.data.cells.get(regionRef).params.values;
        const sphereRefs = c.state.tagIndex.get(c.state.taggedKey("shape", "site"));
        const sphere = [...sphereRefs].map((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr)
            .find((repr: any) => repr?.getAllLoci?.().some((loci: any) => loci.shape));
        const shape = sphere.getAllLoci().find((loci: any) => loci.shape).shape;
        const captions = [...c.state.tagIndex.get(c.state.taggedKey("annotation", "note"))]
            .map((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr)
            .filter((repr: any) => typeof repr?.props.customText === "string");
        const caption = captions[0];
        const glyphs = caption.getAllLoci().find((loci: any) => loci.shape?.geometry.kind === "text")?.shape.geometry.charCount ?? 0;
        const interactionRef = c.interactions.refs.get("contacts");
        const interaction = interactionRef ? c.plugin.state.data.cells.get(interactionRef)?.obj?.data?.repr : undefined;
        const links = interaction?.getAllLoci().find((loci: any) => loci.shape)?.shape;
        let boundary: { expected: number; drawn: number } | null = null;
        if (values.type.name === "ball-and-stick" || values.type.name === "line") {
            const repr = c.plugin.state.data.cells.get(regionRef).obj.data.repr;
            const root = c.getStructureData();
            if (root.units.length !== 1) throw new Error("Boundary control requires one molecular unit.");
            const selected = new Set(region.atomIndices), expected = new Set<string>();
            const unit = root.units[0];
            for (let edge = 0; edge < unit.bonds.a.length; edge++) {
                const a = unit.elements[unit.bonds.a[edge]], b = unit.elements[unit.bonds.b[edge]];
                if (selected.has(a) && !selected.has(b)) expected.add(`${a}:${b}`);
            }
            const child = repr.getAllLoci()[0].structure;
            const drawnUnit = (repr.props.includeParent ? child.asParent() : child).units[0];
            const groups = new Set<number>();
            for (const ro of repr.renderObjects) if (ro.values.aStart) {
                for (const group of ro.values.aGroup.ref.value.subarray(0, ro.values.uVertexCount.ref.value)) groups.add(group);
            }
            let drawn = 0;
            for (let edge = 0; edge < drawnUnit.bonds.a.length; edge++) {
                const a = drawnUnit.elements[drawnUnit.bonds.a[edge]], b = drawnUnit.elements[drawnUnit.bonds.b[edge]];
                if (expected.has(`${a}:${b}`) && groups.has(edge)) drawn++;
            }
            boundary = { expected: expected.size, drawn };
        }
        const renderer = c.plugin.canvas3d.props.renderer;
        return { frame: c.trajectory.getTrajectoryState().currentFrame, regionRef, component: region.component,
            representation: values.type.name, alpha: values.type.params.alpha, regionOrder: region.order,
            regionHidden: c.plugin.state.data.cells.get(regionRef).state.isHidden === true,
            sphereColor: shape.getColor(0), sphereAlpha: sphere.state.alphaFactor,
            caption: caption.props.customText, glyphs, boundary,
            interactionColor: links?.getColor(0) ?? null, interactionAlpha: interaction?.state.alphaFactor ?? null,
            background: renderer.backgroundColor, ambient: renderer.ambientIntensity, diffuse: renderer.light[0].intensity };
    });
}

async function run() {
    await withFixtureWorkspace("movie-appearance", async workspace => {
        const browser = await chromium.launch();
        let bridge: PythonFixtureBridge | undefined, release: (() => Promise<void>) | undefined;
        try {
            bridge = new PythonFixtureBridge(resolve(dirname(fileURLToPath(import.meta.url)), "movie-appearance-bridge.py"),
                resolve(dirname(fileURLToPath(import.meta.url)), "../../../.."), 30_000, { env: fixtureEnvironment(workspace) });
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            const errors: string[] = [];
            page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            const original = await native(page);
            await page.evaluate(() => {
                const w = window as any, c = w.__mirrorController;
                w.__movieRegionDrawOrders = [];
                w.__movieRegionOrderObserver = c.plugin.canvas3d.didDraw.subscribe(() => {
                    const region = c.state.regionIndex.get("site");
                    if (region) w.__movieRegionDrawOrders.push(region.order);
                });
            });
            const opened = page.waitForEvent("popup");
            await page.getByTitle("Open popup", { exact: true }).click();
            const popup = await opened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => (window as any).__mirrorController?.state.regionIndex.get("site")?.representations.length === 1);
            const snapshots: any[] = [];
            for (const time of [500, 1000, 250, 0]) {
                const result = await operation(page, { seek: time });
                const expected = new Map(result.sample.appearance.map((row: any) => [`${row.domain}:${row.property}`, row.value]));
                const rendered = await native(page);
                assert.equal(rendered.regionRef, original.regionRef);
                assert.equal(rendered.component, original.component);
                assert.equal(rendered.regionOrder, original.regionOrder);
                assert.equal(rendered.regionHidden, time >= 750);
                assert.equal(rendered.representation, expected.get("region:representation"));
                if (rendered.boundary) {
                    assert.ok(rendered.boundary.expected > 0);
                    assert.equal(rendered.boundary.drawn, rendered.boundary.expected);
                }
                assert.ok(Math.abs(rendered.alpha - Number(expected.get("region:alpha"))) < 1e-10);
                assert.equal(rendered.sphereColor, expected.get("shape:color"));
                assert.ok(Math.abs(rendered.sphereAlpha - Number(expected.get("shape:alpha"))) < 1e-10);
                assert.equal(rendered.background, expected.get("scene:background"));
                const lighting: any = expected.get("scene:lighting");
                assert.equal(rendered.ambient, lighting.ambient);
                assert.equal(rendered.diffuse, lighting.diffuse);
                assert.equal(rendered.caption, expected.get("annotation:text"));
                assert.ok(rendered.glyphs > 0);
                if (rendered.interactionColor !== null) {
                    assert.equal(rendered.interactionColor, expected.get("interaction:color"));
                    assert.ok(Math.abs(rendered.interactionAlpha - Number(expected.get("interaction:alpha"))) < 1e-10);
                }
                await popup.waitForFunction(({ frame, background, ambient, representation, alpha }) => {
                    const c = (window as any).__mirrorController;
                    const region = c.state.regionIndex.get("site");
                    const values = c.plugin.state.data.cells.get(region.representations[0])?.params?.values;
                    return c.trajectory.getTrajectoryState().currentFrame === frame && c.plugin.canvas3d.props.renderer.backgroundColor === background
                        && c.plugin.canvas3d.props.renderer.ambientIntensity === ambient && values?.type.name === representation
                        && Math.abs(values.type.params.alpha - alpha) < 1e-10;
                }, rendered);
                snapshots.push({ time, ...rendered });
            }
            const played = await operation(page, { play: true });
            assert.equal(played.sample.time_ms, 1000);
            assert.equal((await native(page)).representation, "spacefill");
            await operation(page, { save: resolve(workspace, "appearance.msv") });
            await popup.close();
            const exported = await operation(page, { export: resolve(workspace, "appearance.mp4") });
            const drawOrders = await page.evaluate(() => {
                const w = window as any;
                w.__movieRegionOrderObserver.unsubscribe();
                return w.__movieRegionDrawOrders as number[];
            });
            assert.ok(drawOrders.length > 4);
            assert.deepEqual([...new Set(drawOrders)], [original.regionOrder]);
            assert.deepEqual(errors, []);
            if (process.env.MOLSYSVIEWER_MOVIE_EVIDENCE_DIR) {
                const out = process.env.MOLSYSVIEWER_MOVIE_EVIDENCE_DIR;
                await mkdir(out, { recursive: true });
                await copyFile(resolve(workspace, "appearance.mp4"), resolve(out, "appearance.mp4"));
                await copyFile(resolve(workspace, "appearance.msv"), resolve(out, "appearance.msv"));
                await writeFile(resolve(out, "verified.json"), JSON.stringify({ snapshots, exported, drawOrders }, null, 2));
            }
            console.log("[Movie appearance] Native materials, stable region nodes/order, popup, preview, session and 720p MP4 agree.");
        } finally {
            await release?.();
            await Promise.all([browser.close(), bridge?.close()]);
        }
    });
}
run().catch(error => { console.error(error); process.exitCode = 1; });
