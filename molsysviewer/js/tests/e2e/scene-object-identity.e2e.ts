import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   GLY A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  GLY A   1      12.560  13.329   8.276  1.00 20.00           C
END
`;

async function run() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: [
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ],
    } as any);
    const page = await browser.newPage();
    await page.route("http://molsysviewer.test/", route => route.fulfill({
        contentType: "text/html",
        body: '<div id="root" style="width:800px;height:600px"></div>',
    }));
    await page.goto("http://molsysviewer.test/", { waitUntil: "networkidle" });
    await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });

    const result = await page.evaluate(async pdb => {
        const harness = (window as any).Harness;
        const controller = await harness.createController("root");
        await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "identity" });
        await controller.handleMessage({
            op: "add_sphere",
            options: { center: [11.1, 13.2, 8.5], radius: 1.5, color: 0x00ff00, alpha: 1, tag: "site1" },
        });
        await controller.handleMessage({
            op: "add_label",
            tag: "site1",
            options: { text: "site", tag: "site1", atom_indices: [0] },
        });
        const before = {
            shape: harness.inspectTaggedRefs(controller, "shape", "site1"),
            annotation: harness.inspectTaggedRefs(controller, "annotation", "site1"),
        };
        await controller.handleMessage({ op: "hide_layer", tag: "site1", kind: "shape" });
        const after = {
            shape: harness.inspectTaggedRefs(controller, "shape", "site1"),
            annotation: harness.inspectTaggedRefs(controller, "annotation", "site1"),
        };
        return { before, after };
    }, PDB_TEXT);

    assert.ok(result.before.shape.length > 0, "shape registered no Mol* nodes");
    assert.ok(result.before.annotation.length > 0, "annotation registered no Mol* nodes");
    assert.ok(result.before.shape.every((item: any) => !item.hidden), "shape started hidden");
    assert.ok(result.before.annotation.every((item: any) => !item.hidden), "annotation started hidden");
    assert.ok(result.after.shape.every((item: any) => item.hidden), "shape nodes did not hide");
    assert.ok(result.after.annotation.every((item: any) => !item.hidden), "same-tag annotation was hidden with shape");

    await browser.close();
    console.log("[E2E scene-object-identity] passed");
}

run().catch(error => {
    console.error(error);
    // process.exit, not process.exitCode: a failed assertion skips browser.close(),
    // so Chromium stays alive and the event loop never drains. Setting exitCode
    // would leave the process hanging until CI's timeout instead of failing fast.
    process.exit(1);
});
