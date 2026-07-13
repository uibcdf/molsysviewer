import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function run() {
    const python = spawnSync(
        process.env.PYTHON || "python",
        [resolve(__dirname, "broken-anchors-bridge.py")],
        { encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
    );
    assert.strictEqual(python.status, 0, python.stderr || python.stdout);
    const backend = JSON.parse(python.stdout);
    assert.strictEqual(backend.annotation.broken, true);
    assert.strictEqual(backend.measurement.broken, true);
    assert.strictEqual(backend.measurement.value, null);

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"],
    } as any);
    const page = await browser.newPage({ viewport: { width: 1100, height: 800 } });
    try {
        await page.setContent('<div id="root" style="width:1000px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.evaluate(async messages => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            for (const message of messages) await controller.handleMessage(message);
        }, backend.messages);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="annotations"]').click();
        const annotationRow = page.locator('[data-molsysviewer-scene-object-tag="broken-note"]');
        assert.strictEqual(await annotationRow.getAttribute("data-molsysviewer-scene-object-broken"), "true");
        assert.match(await annotationRow.innerText(), /Missing anchor atom indices/);

        await page.locator('[data-molsysviewer-group-panel-tab="measures"]').click();
        const measurementRow = page.locator('[data-molsysviewer-measurement-tag="broken-distance"]');
        assert.strictEqual(await measurementRow.getAttribute("data-molsysviewer-measurement-broken"), "true");
        assert.strictEqual(await measurementRow.locator('[data-molsysviewer-measurement-value="broken-distance"]').innerText(), "—");
        assert.match(await measurementRow.getAttribute("title") || "", /Missing anchor atom indices/);

        const refs = await page.evaluate(() => {
            const controller = (window as any).__controller;
            return {
                annotation: (window as any).Harness.inspectTaggedRefs(controller, "annotation", "broken-note"),
                measurement: (window as any).Harness.inspectTaggedRefs(controller, "measurement", "broken-distance"),
            };
        });
        assert.deepStrictEqual(refs.annotation, [], "broken annotation still has Mol* nodes");
        assert.deepStrictEqual(refs.measurement, [], "broken measurement still has Mol* nodes");

        console.log("[E2E broken-anchors] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
