import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Page, Download } from "playwright";
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";

const dir = dirname(fileURLToPath(import.meta.url));
const pngButton = (page: Page) => page.getByRole("button", { name: "Download PNG Image", exact: true });
const status = (page: Page) => page.locator("[data-molsysviewer-export-image-status]");

async function openExport(page: Page) {
    await page.evaluate(() => {
        const c = (window as any).__mirrorController;
        c.setPanelMode("navigate", true); c.groupPanel.openSection("export");
    });
    await pngButton(page).waitFor();
}

async function detach(source: Page) {
    await openExport(source);
    const opened = source.waitForEvent("popup");
    await source.getByTitle("Popout panel to external window", { exact: true }).click();
    const panel = await opened;
    await panel.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
    await panel.waitForFunction(() => !!(window as any).__mirrorController);
    await openExport(panel);
    assert.match(await panel.locator("[data-molsysviewer-export-dimensions]").innerText(), /originating canvas/);
    return panel;
}

async function nativeState(page: Page) {
    return page.evaluate(() => {
        const c = (window as any).__mirrorController, gl = c.plugin.canvas3d.webgl.gl;
        return { atoms: c.getStructureData()?.elementCount ?? 0, representations: c.plugin.canvas3d.reprCount.value,
            size: [gl.drawingBufferWidth, gl.drawingBufferHeight], animating: c.plugin.animationLoop.isAnimating,
            camera: c.getCameraSnapshot(), background: c.plugin.canvas3d.props.renderer.backgroundColor };
    });
}

async function decode(page: Page, uri: string) {
    const decoded = await page.evaluate(async uri => {
        const image = new Image(); image.src = uri; await image.decode();
        const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
        const ctx = canvas.getContext("2d")!; ctx.drawImage(image, 0, 0);
        const bytes = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        let visible = 0, transparent = 0, binary = "";
        for (let i = 3; i < bytes.length; i += 4) { if (bytes[i]) visible++; else transparent++; }
        for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
        return { width: image.width, height: image.height, visible, transparent, pixels: btoa(binary) };
    }, uri);
    const { pixels, ...summary } = decoded;
    return { ...summary, sha256: createHash("sha256").update(Buffer.from(pixels, "base64")).digest("hex") };
}

async function capture(panel: Page, source: Page, authority: Page, workspace: string, name: string, transparent: boolean) {
    await panel.getByLabel("Resolution Scale", { exact: true }).selectOption("1");
    await panel.getByLabel("Transparent Background", { exact: true }).setChecked(transparent);
    await authority.evaluate(() => (window as any).__popupFixtureDrain());
    await panel.waitForFunction(expected => (window as any).__mirrorController.addonsScene.figureBackground
        === (expected ? "transparent" : "white"), transparent);
    await source.evaluate(() => {
        const w = window as any, c = w.__mirrorController, helper = c.plugin.helpers.viewportScreenshot;
        const getter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(helper), "imagePass")!.get!;
        w.__pngAssetObservations = [];
        w.__observedImagePasses ??= new WeakSet();
        Object.defineProperty(helper, "imagePass", { configurable: true, get() {
            const pass = getter.call(this);
            const sizes = () => {
                const values = (pass.drawPass.antialiasing as any).smaa.weightsRenderable.values;
                return [values.tArea, values.tSearch].map(cell => [cell.ref.value.getWidth(), cell.ref.value.getHeight()]);
            };
            w.__pngAssetObservations.push({ stage: "get", dimensions: sizes() });
            if (!w.__observedImagePasses.has(pass)) {
                w.__observedImagePasses.add(pass);
                const render = pass.render;
                pass.render = function(...args: any[]) {
                    w.__pngAssetObservations.push({ stage: "render", dimensions: sizes() });
                    return render.apply(this, args);
                };
            }
            return pass;
        } });
    });
    const before = await nativeState(source), ready = panel.waitForEvent("download", { timeout: 120000 });
    await pngButton(panel).click(); const download = await ready;
    assert.equal(download.suggestedFilename(), "molsysviewer.png");
    const path = resolve(workspace, name + ".png"); await download.saveAs(path);
    await panel.waitForFunction(() => document.querySelector("[data-molsysviewer-export-image-status]")?.textContent === "PNG download started.");
    const bytes = await readFile(path), uri = "data:image/png;base64," + bytes.toString("base64");
    const actual = await decode(panel, uri), captured = await nativeState(source);
    assert.deepEqual([actual.width, actual.height], before.size);
    assert.ok(actual.visible > 100, "the image must contain the real molecular scene");
    if (transparent) assert.ok(actual.transparent > 100); else assert.equal(actual.transparent, 0);
    // Compare decoded pixels with an independent public/native export from the
    // associated canvas, preserving the normal sampling quality.
    const reference = await source.evaluate(async transparent => (window as any).__mirrorController.getImageDataUri({
        scale: 1, transparent, preset: "publication-light",
    }), transparent);
    assert.equal(typeof reference, "string");
    const referencePixels = await decode(panel, reference);
    const assets = await source.evaluate(() => (window as any).__pngAssetObservations);
    assert.ok(assets.some((row: any) => row.stage === "render"));
    assert.ok(assets.filter((row: any) => row.stage === "render")
        .every((row: any) => JSON.stringify(row.dimensions) === JSON.stringify([[160, 560], [66, 33]])),
        "the first real PNG pass must wait for both native SMAA uploads");
    if (process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR) {
        const out = process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR;
        await writeFile(resolve(out, name + ".png"), bytes);
        await writeFile(resolve(out, name + "-reference.png"), Buffer.from(reference.split(",")[1], "base64"));
        await writeFile(resolve(out, name + ".json"), JSON.stringify({ before, captured,
            afterReference: await nativeState(source), actual, reference: referencePixels, nativeAssets: assets }, null, 2));
    }
    assert.deepEqual(actual, referencePixels);
    const after = await nativeState(source), local = await nativeState(panel);
    assert.deepEqual(after.camera, before.camera); assert.equal(after.background, before.background);
    assert.equal(after.animating, true); assert.equal(local.atoms, 0); assert.equal(local.representations, 0);
    assert.equal(local.animating, false, "export must never restart the hidden Studio renderer");
    console.log("[E2E Studio PNG] " + name + ": exact native pixels, stopped panel");
}

/** Delay only a genuine completed native result; never replace image data. */
async function holdNativeReply(source: Page) {
    await source.evaluate(() => {
        const w = window as any, c = w.__mirrorController, original = c.getImageDataUri;
        w.__pngReplyReady = false;
        c.getImageDataUri = async function(options: any) {
            const result = await original.call(this, options);
            if (options?.nativeViewport) {
                await new Promise<void>(resolve => { w.__pngRelease = resolve; w.__pngReplyReady = true; });
            }
            return result;
        };
        w.__pngRestore = () => { c.getImageDataUri = original; w.__pngRelease?.(); };
    });
}

async function run() {
    await withFixtureWorkspace("studio-image-export", async workspace => {
        const root = resolve(dir, "../../../.."), browser = await chromium.launch();
        const bridge = new PythonFixtureBridge(resolve(dir, "studio-live-capture-bridge.py"), root);
        const witnessBridge = new PythonFixtureBridge(resolve(dir, "studio-live-capture-bridge.py"), root);
        let release: (() => Promise<void>) | undefined, releaseWitness: (() => Promise<void>) | undefined;
        try {
            const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, acceptDownloads: true });
            page.context().on("page", endpoint => endpoint.on("pageerror", error => console.error("[E2E Studio PNG page]", error)));
            release = await mountCanvasPopupFixture(page, bridge); await captureCanvasPopupControllers(page);
            const witness = await page.context().newPage();
            releaseWitness = await mountCanvasPopupFixture(witness, witnessBridge); await captureCanvasPopupControllers(witness);
            const witnessBefore = await nativeState(witness), downloads: Download[] = [], unrelated: Download[] = [];
            page.on("download", d => unrelated.push(d)); witness.on("download", d => unrelated.push(d));
            let panel = await detach(page); panel.on("download", d => downloads.push(d));
            await capture(panel, page, page, workspace, "primary-transparent", true);

            await holdNativeReply(page); await pngButton(panel).click();
            await page.waitForFunction(() => (window as any).__pngReplyReady, null, { timeout: 120000 });
            await panel.getByRole("button", { name: "Cancel PNG", exact: true }).click();
            assert.match(await status(panel).innerText(), /cancelled/);
            await page.evaluate(() => (window as any).__pngRestore());
            // The next source export queues behind the released genuine reply.
            await capture(panel, page, page, workspace, "primary-after-cancel", true);
            assert.equal(downloads.length, 2);
            await panel.close();

            await page.evaluate(() => (window as any).__mirrorController.setPanelMode("navigate", false));
            const opened = page.waitForEvent("popup"); await page.getByTitle("Open popup", { exact: true }).click();
            const popup = await opened; popup.on("download", d => unrelated.push(d));
            await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
            await popup.waitForFunction(() => (window as any).__mirrorController?.getStructureData()?.elementCount > 0);
            await captureCanvasPopupControllers(popup, false);
            // Distinct sizes make origin substitution detectable.
            await popup.setViewportSize({ width: 680, height: 510 });
            panel = await detach(popup); panel.on("download", d => downloads.push(d));
            await capture(panel, popup, page, workspace, "popup-opaque", false);

            await holdNativeReply(popup); await pngButton(panel).click();
            await popup.waitForFunction(() => (window as any).__pngReplyReady, null, { timeout: 120000 });
            await popup.close();
            await panel.waitForFunction(() => /closed/.test(document.querySelector("[data-molsysviewer-export-image-status]")?.textContent || ""));
            assert.equal(await pngButton(panel).isEnabled(), true);
            await pngButton(panel).click();
            await panel.waitForFunction(() => /unavailable/.test(document.querySelector("[data-molsysviewer-export-image-status]")?.textContent || ""));
            assert.equal(downloads.length, 3, "a closed origin must not fall back to another canvas");
            assert.equal(unrelated.length, 0, "only the requesting panel may download");
            assert.deepEqual(await nativeState(witness), witnessBefore);
            assert.equal((await nativeState(panel)).animating, false);
            await panel.close();
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
            console.log("[E2E Studio PNG] origin, requester isolation, cancel/late reply, retry and closed origin passed");
        } finally {
            await release?.(); await releaseWitness?.();
            await bridge.close(); await witnessBridge.close(); await browser.close();
        }
    });
}
run().catch(error => { console.error(error); process.exit(1); });
