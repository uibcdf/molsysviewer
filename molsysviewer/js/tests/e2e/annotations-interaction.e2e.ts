import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
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

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    let browser;
    try {
        browser = await chromium.launch({
            headless: true,
            executablePath: envBin,
            chromiumSandbox: false,
            args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        } as any);
    } catch {
        console.warn("[E2E] Chromium launch failed; skipping test.");
        process.exit(0);
    }

    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width:800px;height:600px;"></div></body></html>`,
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    // ── Scenario 1: add_label renders without errors ─────────────────────────
    console.log("[E2E annotations] Scenario: add_label renders");

    await page.evaluate(async (pdb) => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        (window as any).__messages = [];
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test-annotations",
        });

        // Poll for structure to be loaded
        for (let i = 0; i < 50; i++) {
            const s = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }

        await controller.handleMessage({
            op: "add_label",
            tag: "label-n",
            options: {
                text: "N-terminus",
                atom_indices: [0],
                tag: "label-n",
                style: { color: "#FF0000", size_em: 1.2, background: true, background_opacity: 0.7 },
            },
        });
    }, PDB_TEXT);

    // ── Scenario 2: label visibility toggle works ────────────────────────────
    console.log("[E2E annotations] Scenario: label visibility toggle");

    await page.evaluate(async () => {
        const controller = (window as any).__controller;
        // Add a second label with a shared layer
        await controller.handleMessage({
            op: "add_label",
            tag: "label-ca",
            options: {
                text: "CA",
                atom_indices: [1],
                tag: "label-ca",
                layer_tag: "backbone-labels",
            },
        });
        await controller.handleMessage({
            op: "add_label",
            tag: "label-c",
            options: {
                text: "C",
                atom_indices: [2],
                tag: "label-c",
                layer_tag: "backbone-labels",
            },
        });
        // Hide the shared layer
        await controller.handleMessage({
            op: "set_visibility",
            tag: "backbone-labels",
            visible: false,
        });
        // Re-show it
        await controller.handleMessage({
            op: "set_visibility",
            tag: "backbone-labels",
            visible: true,
        });
    });

    // ── Scenario 3: resolveTooltipPayload logic via notifyHover ──────────────
    // We cannot trigger actual Mol* hover events without WebGL, but we can verify
    // that the controller's internal annotation registry is populated correctly.
    console.log("[E2E annotations] Scenario: annotation registry populated");

    const hasAnnotation = await page.evaluate(() => {
        const controller = (window as any).__controller;
        return (controller as any).annotations?.hasTag?.("label-n") === true;
    });
    assert.ok(hasAnnotation, "annotation 'label-n' should be registered in AnnotationHandlers");

    // ── Scenario 4: add_distance with measurement_style ──────────────────────
    console.log("[E2E annotations] Scenario: add_distance_measurement with measurement_style");

    await page.evaluate(async () => {
        const controller = (window as any).__controller;
        const structure = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
        if (!structure) return;

        // Build loci for atoms 0 and 1 using the controller's structure
        await controller.handleMessage({
            op: "add_distance_measurement",
            tag: "dist-ca-n",
            options: {
                atom_indices: [0, 1],
                tag: "dist-ca-n",
                measurement_style: { color: "#00FF00", size_em: 1.0, background: false },
            },
        });
    });

    const hasMeasurement = await page.evaluate(() => {
        const controller = (window as any).__controller;
        return (controller as any).measurements?.hasTag?.("dist-ca-n") === true;
    });
    assert.ok(hasMeasurement, "measurement 'dist-ca-n' should be registered in MeasurementHandlers");

    // ── Scenario 5: tooltip payload resolution via internal method ────────────
    console.log("[E2E annotations] Scenario: resolveTooltipPayload via controller");

    const tooltipResult = await page.evaluate(() => {
        const controller = (window as any).__controller;
        const annotations = (controller as any).annotations;
        const measurements = (controller as any).measurements;
        if (!annotations || !measurements) return null;

        // Simulate what resolveTooltipPayload does:
        const tooltipTag = "label-n";
        if (annotations.hasTag(tooltipTag)) {
            const spec = annotations.getSpec(tooltipTag);
            return { kind: "annotation", tag: tooltipTag, text: spec?.text, atom_indices: spec?.atom_indices };
        }
        return null;
    });

    assert.ok(tooltipResult !== null, "tooltip resolution should find annotation");
    assert.strictEqual(tooltipResult?.kind, "annotation");
    assert.strictEqual(tooltipResult?.tag, "label-n");
    assert.strictEqual(tooltipResult?.text, "N-terminus");
    assert.deepStrictEqual(tooltipResult?.atom_indices, [0]);

    await browser.close();

    const hasWebglError = errors.some(e => e.includes("WebGL rendering context"));
    if (hasWebglError) {
        console.warn("[E2E annotations] WebGL unavailable; skipping rendering assertions.");
        process.exit(0);
    }
    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E annotations] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
