import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

/**
 * Browser observation for the trajectory plot (uibcdf/molsysviewer#65).
 *
 * The capability audit derived `contract-tested` for this row and nothing else: no
 * browser had ever watched it draw. For a viewer that is the sharpest gap there is,
 * so this asserts what appeared in the document, not that a message was accepted --
 * a runtime that swallowed `set_trajectory_plot` entirely would satisfy the latter.
 */
async function run() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 900 });

    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => {
        if (msg.type() === "error") errors.push(msg.text());
    });

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width: 800px; height: 600px;"></div></body></html>`,
        { waitUntil: "networkidle" },
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => !!(window as any).Harness, { timeout: 30000 });

    await page.evaluate(async pdb => {
        const w = window as any;
        const controller = await w.Harness.createController("root");
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "traj-plot",
        });
        await controller.handleMessage({
            op: "set_trajectory_plot",
            options: {
                tag: "rmsd",
                visible: true,
                title: "RMSD",
                x_label: "frame",
                y_label: "nm",
                n_frames: 5,
                x: [0, 1, 2, 3, 4],
                series: [
                    { label: "backbone", values: [0.0, 0.4, 0.9, 0.6, 1.2] },
                    { label: "sidechain", values: [0.1, 0.2, 0.5, 0.8, 0.7] },
                ],
            },
        });
    }, PDB_TEXT);

    // The card is a real element with the tag it was given.
    const card = page.locator('[data-molsysviewer-datacard="rmsd"]');
    await card.waitFor({ state: "visible", timeout: 30000 });

    // Two series were sent, so two polylines must have been drawn. A card that
    // appeared empty would pass a visibility check and fail here.
    const polylines = card.locator("svg polyline");
    await polylines.first().waitFor({ state: "attached", timeout: 30000 });
    assert.strictEqual(
        await polylines.count(),
        2,
        "Expected one polyline per series in the trajectory plot",
    );

    // Each polyline must carry five points, one per frame: a series drawn from an
    // empty or truncated array still produces an element.
    const pointCounts = await polylines.evaluateAll(nodes =>
        nodes.map(n => (n.getAttribute("points") ?? "").trim().split(/\s+/).filter(Boolean).length),
    );
    assert.deepStrictEqual(
        pointCounts,
        [5, 5],
        `Expected five points per series, got ${JSON.stringify(pointCounts)}`,
    );

    // The labels the caller asked for reached the document.
    const text = (await card.textContent()) ?? "";
    for (const label of ["RMSD", "frame", "nm"]) {
        assert.ok(text.includes(label), `Expected the plot to render ${JSON.stringify(label)}`);
    }

    // Hiding it removes what was drawn, rather than leaving a stale card behind.
    await page.evaluate(async () => {
        const controller = (window as any).__controller;
        await controller.handleMessage({
            op: "set_trajectory_plot",
            options: { tag: "rmsd", visible: false },
        });
    });
    await card.waitFor({ state: "detached", timeout: 30000 });

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors detected: ${errors.join("; ")}`);
    console.log("[E2E] passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
