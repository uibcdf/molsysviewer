import assert from "node:assert/strict";
import { mkdir, readFile, writeFile, copyFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import type { Page } from "playwright";

const command = (page: Page, event: any) => page.evaluate(async value => (window as any).__popupWidgetModel.send(value), event);
async function finished(page: Page) {
    const until = performance.now() + 90000;
    do { const result = (await command(page, { movie_export_status: true })).movie_export_result;
        if (result) return result; await delay(100);
    } while (performance.now() < until);
    throw new Error("Composited Movie did not finish.");
}
async function probes(page: Page, images: string[], width: number, height: number) {
    return page.evaluate(async ({ images, width, height }) => {
        const c = (window as any).__mirrorController;
        const viewport = c.host.getBoundingClientRect();
        const rect = (element: Element) => { const r = element.getBoundingClientRect();
            return { x: r.left - viewport.left, y: r.top - viewport.top, width: r.width, height: r.height }; };
        const legend = document.querySelector("[data-molsysviewer-legend]")!;
        const lb = rect(legend), chip = rect(legend.firstElementChild!.firstElementChild!);
        const plot = document.querySelector('[data-molsysviewer-datacard="control"]')!;
        const pb = rect(plot);
        // The chart SVG is the body SVG, not one of the header button icons.
        const chart = plot.querySelector('[data-molsysviewer-datacard-body] svg') as SVGSVGElement | null;
        const source = chart ?? [...plot.querySelectorAll<SVGSVGElement>("svg")].find(node => node.querySelector("polyline"))!;
        const v = source.viewBox.baseVal;
        const scale = Math.min(width / viewport.width, height / viewport.height);
        const map = (bounds: typeof lb, x: number, y: number) => [
            (bounds.x + bounds.width / 2) / viewport.width * width + (x - bounds.x - bounds.width / 2) * scale,
            (bounds.y + bounds.height / 2) / viewport.height * height + (y - bounds.y - bounds.height / 2) * scale,
        ];
        const fit = Math.min((pb.width - 16) / v.width, (pb.height - 34) / v.height);
        const px = pb.x + 8 + (pb.width - 16 - v.width * fit) / 2;
        const py = pb.y + 26 + (pb.height - 34 - v.height * fit) / 2;
        const points = { red: map(lb, chip.x + chip.width / 2, chip.y + chip.height / 2),
            first: map(pb, px + 40 * fit, py + v.height / 2 * fit),
            last: map(pb, px + (v.width - 14) * fit, py + v.height / 2 * fit) };
        const results = [];
        for (const uri of images) {
            const image = new Image(); image.src = uri; await image.decode();
            const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = height;
            const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0);
            const patch = (point: number[]) => Array.from(context.getImageData(Math.round(point[0]) - 2, Math.round(point[1]) - 2, 5, 5).data);
            const first = map(pb, pb.x, pb.y + 26), last = map(pb, pb.x + pb.width, pb.y + pb.height - 8);
            const pixels = context.getImageData(Math.ceil(first[0]), Math.ceil(first[1]),
                Math.floor(last[0] - first[0]), Math.floor(last[1] - first[1])).data;
            let green = 0;
            for (let i = 0; i < pixels.length; i += 4) if (pixels[i + 1] > pixels[i] + 70 && pixels[i + 1] > pixels[i + 2] + 70) green++;
            results.push({ red: patch(points.red), first: patch(points.first), last: patch(points.last), green });
        }
        return { points, results, sourceBounds: { legend: lb, plot: pb } };
    }, { images, width, height });
}
const brightest = (patch: number[]) => Math.max(...Array.from({ length: patch.length / 4 }, (_, i) => Math.min(...patch.slice(i * 4, i * 4 + 3))));

async function run() {
    await withFixtureWorkspace("movie-composition", async workspace => {
        const here = dirname(fileURLToPath(import.meta.url));
        const bridge = new PythonFixtureBridge(resolve(here, "movie-export-bridge.py"), resolve(here, "../../../.."), 30000,
            { env: fixtureEnvironment(workspace) });
        const browser = await chromium.launch(); let release: (() => Promise<void>) | undefined;
        try {
            const page = await browser.newPage({ viewport: { width: 1000, height: 800 } });
            const errors: string[] = []; page.on("pageerror", error => errors.push(String(error)));
            release = await mountCanvasPopupFixture(page, bridge); await captureCanvasPopupControllers(page);
            await command(page, { movie_composition_setup: true });
            await page.waitForSelector('[data-molsysviewer-plot-navigation="control"]');
            await page.locator('[data-molsysviewer-datacard="control"]').evaluate((el: HTMLElement) => {
                el.style.left = "20px"; el.style.top = `${Math.max(12, el.parentElement!.clientHeight - el.getBoundingClientRect().height - 20)}px`;
            });
            const evidence = process.env.MOLSYSVIEWER_MOVIE_EVIDENCE_DIR;
            for (const suffix of [".zip", ".mp4"]) {
                const path = resolve(workspace, "included" + suffix);
                await command(page, { movie_export: { path, width: 1280, height: 720 } });
                const result = await finished(page); assert.equal(result.ok, true, JSON.stringify(result));
                const inspection = await command(page, { movie_composition_inspect: suffix });
                const composition = inspection.manifest.composition;
                assert.equal(composition.dom_overlays, "svg-composited@1");
                assert.equal(composition.layout.layers.length, 2);
                assert.equal(composition.source_context.plots[0].series[0].observation.units.y, "nm");
                assert.deepEqual(composition.source_context.plots[0].series[0].observation.original_structure_indices, [4999, 0, 73]);
                const pixels = await probes(page, inspection.images, 1280, 720);
                for (const row of pixels.results) {
                    assert.ok(row.red.filter((_: number, i: number) => i % 4 === 0).some((v: number) => v > 230), "legend chip must be painted");
                    assert.ok(row.green > 20, "the control curve must be painted");
                }
                assert.ok(brightest(pixels.results[0].first) > 185);
                assert.ok(brightest(pixels.results[0].last) < 170);
                assert.ok(brightest(pixels.results[1].last) > 185);
                assert.ok(brightest(pixels.results[1].first) < 170);
                if (evidence) { await mkdir(evidence, { recursive: true });
                    await copyFile(path, resolve(evidence, "composited" + suffix));
                    await writeFile(resolve(evidence, `pixels${suffix}.json`), JSON.stringify(pixels));
                    for (const [index, uri] of inspection.images.entries()) await writeFile(resolve(evidence, `frame${index}${suffix}.png`), Buffer.from(uri.split(",")[1], "base64"));
                }
            }
            const sentinel = resolve(workspace, "preserve.zip"); await writeFile(sentinel, "original");
            // Change the real card after frame zero was captured, before delivery.
            for (const mutation of ["position", "opacity"]) {
            await page.evaluate(mode => { const model = (window as any).__popupWidgetModel, send = model.send.bind(model); let changed = false;
                model.send = (value: any) => { const content = value.payload ?? value;
                    if (!changed && content.movie_frame?.frame_index === 0) { changed = true;
                        const card = document.querySelector('[data-molsysviewer-datacard="control"]') as HTMLElement;
                        if (mode === "position") card.style.left = `${parseFloat(card.style.left) + 20}px`;
                        else (card.querySelector('[aria-label="Toggle opacity"]') as HTMLButtonElement).click(); }
                    return send(value);
                }; }, mutation);
            await command(page, { movie_export: { path: sentinel, overwrite: true, width: 1280, height: 720 } });
            const moved = await finished(page); assert.equal(moved.ok, false); assert.match(moved.error, /layout/);
            assert.equal(await readFile(sentinel, "utf8"), "original");
            }
            await page.locator('[data-molsysviewer-datacard="control"]').getByRole("button", { name: "Minimize", exact: true }).click();
            await command(page, { movie_export: { path: sentinel, overwrite: true, width: 1280, height: 720 } });
            const minimized = await finished(page); assert.equal(minimized.ok, false); assert.match(minimized.error, /expand/i);
            assert.equal(await readFile(sentinel, "utf8"), "original");
            await command(page, { movie_export: { path: resolve(workspace, "excluded.zip"), include_overlays: false, width: 1280, height: 720 } });
            const excluded = await finished(page); assert.equal(excluded.ok, true, JSON.stringify(excluded));
            assert.equal(excluded.export.manifest.composition.excluded_dom_overlays.length, 2);
            assert.deepEqual(errors, []);
            console.log("PASS Movie composition: actual PNG/MP4 legend, curve, units/context and frame-specific playhead; changed/minimized layout preserves destination; explicit exclusion succeeds");
        } finally { await release?.(); await bridge.close(); await browser.close(); }
    });
}
run().catch(error => { console.error(error); process.exit(1); });
