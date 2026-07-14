/**
 * E2E: Full scientific workflow
 * load_molsys_payload → add_label → add_distance_measurement → verify all registered.
 *
 * This scenario tests the programmatic (replay-safe) API path end-to-end in a real
 * browser context, complementing the context-menu based measurements-interaction.e2e.ts.
 */
import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const MOLSYS_PAYLOAD = {
    atoms: {
        atom_id: [1, 2, 3, 4],
        element_symbol: ["N", "C", "C", "O"],
        residue_id: [1, 1, 1, 1],
        residue_name: ["ALA", "ALA", "ALA", "ALA"],
        chain_id: ["A", "A", "A", "A"],
    },
    structures: [
        { coordinates: [[11.1, 13.2, 8.6], [12.6, 13.3, 8.3], [13.2, 12.0, 8.0], [12.6, 10.9, 8.4]] },
    ],
};

// Full workflow message sequence — mirrors what Python _build_export_messages() emits
// when a label and a distance measurement are added to a loaded structure.
const WORKFLOW_SEQUENCE = [
    {
        op: "load_molsys_payload",
        payload: MOLSYS_PAYLOAD,
    },
    {
        op: "add_label",
        tag: "n-terminus",
        options: {
            text: "N-terminus",
            atom_indices: [0],
            tag: "n-terminus",
        },
    },
    {
        op: "add_distance_measurement",
        tag: "nc-dist",
        options: {
            tag: "nc-dist",
            // Single-atom picks → "atom" endpoint policy; no coordinate resolution needed
            picks_atom_indices: [[0], [1]],
            endpoint_atom_indices: [[0], [1]],
            endpoint_kinds: ["atom", "atom"],
        },
    },
];

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const browser = await chromium.launch({
        headless: true,
        executablePath: envBin,
        chromiumSandbox: false,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    } as any);

    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width:800px;height:600px;"></div></body></html>`,
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    // ── Scenario 1: full workflow replay ─────────────────────────────────────
    console.log("[E2E workflow] Scenario: full workflow — load → label → measure");

    await page.evaluate(async (sequence) => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;

        for (const msg of sequence) {
            await controller.handleMessage(msg);
        }

        // Wait until structure is present
        for (let i = 0; i < 80; i++) {
            const s = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
    }, WORKFLOW_SEQUENCE);

    // Structure loaded
    const elementCount = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data?.elementCount ?? 0;
    });
    assert.ok(elementCount > 0, "structure should be loaded");

    // Label registered
    const hasLabel = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).annotations?.hasTag?.("n-terminus") === true;
    });
    assert.ok(hasLabel, "annotation 'n-terminus' should be registered");

    // Label spec has correct text
    const labelSpec = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).annotations?.getSpec?.("n-terminus");
    });
    assert.ok(labelSpec !== null && labelSpec !== undefined, "label spec must exist");
    assert.strictEqual(labelSpec.text, "N-terminus");
    assert.deepStrictEqual(labelSpec.atom_indices, [0]);

    // Distance measurement registered
    const hasMeasurement = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).measurements?.hasTag?.("nc-dist") === true;
    });
    assert.ok(hasMeasurement, "measurement 'nc-dist' should be registered");

    // Measurement spec has correct kind and atom_indices
    const measureSpec = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).measurements?.getSpec?.("nc-dist");
    });
    assert.ok(measureSpec !== null && measureSpec !== undefined, "measurement spec must exist");
    assert.strictEqual(measureSpec.kind, "distance");
    assert.deepStrictEqual(measureSpec.atom_indices, [0, 1]);

    // ── Scenario 2: clear and replay on the same controller (export-reload simulation) ──
    console.log("[E2E workflow] Scenario: clear_all + replay");

    await page.evaluate(async (sequence) => {
        const c = (window as any).__controller;
        await c.handleMessage({ op: "clear_all" });
        for (const msg of sequence) {
            await c.handleMessage(msg);
        }
        for (let i = 0; i < 80; i++) {
            const s = (c as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
    }, WORKFLOW_SEQUENCE);

    const hasLabelAfterReplay = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).annotations?.hasTag?.("n-terminus") === true;
    });
    assert.ok(hasLabelAfterReplay, "annotation should be present after clear_all + replay");

    const hasMeasurementAfterReplay = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).measurements?.hasTag?.("nc-dist") === true;
    });
    assert.ok(hasMeasurementAfterReplay, "measurement should be present after clear_all + replay");

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E workflow] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
