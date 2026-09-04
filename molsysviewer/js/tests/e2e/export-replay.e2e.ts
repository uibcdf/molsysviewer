import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Minimal fallback payload. The Phase 4a closure passes a complete canonical
// Python projection through MSV_E2E_EXPORT_MESSAGES instead.
const DEFAULT_MOLSYS_PAYLOAD = {
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

const externalPayloadPath = process.env.MSV_E2E_MOLSYS_PAYLOAD;
const externalMessage = externalPayloadPath
    ? JSON.parse(readFileSync(externalPayloadPath, "utf8"))
    : undefined;
const MOLSYS_PAYLOAD = externalMessage?.op === "load_molsys_payload"
    ? externalMessage.payload
    : (externalMessage ?? DEFAULT_MOLSYS_PAYLOAD);

const DEFAULT_EXPORT_SEQUENCE = [
    {
        op: "load_molsys_payload",
        payload: MOLSYS_PAYLOAD,
    },
    {
        op: "create_region",
        tag: "exported-region",
        atom_indices: [0, 1],
        representation: "ball-and-stick",
    },
    {
        op: "hide_region",
        tag: "exported-region",
    },
    {
        op: "add_label",
        tag: "exported-label",
        options: {
            text: "Exported label",
            atom_indices: [0],
            tag: "exported-label",
        },
    },
    {
        op: "set_camera_snapshot",
        snapshot: { target: [12.0, 12.0, 8.0], position: [20.0, 20.0, 20.0], up: [0, 1, 0] },
        duration_ms: 0,
    },
];

const exportFixturePath = process.env.MSV_E2E_EXPORT_MESSAGES;
const exportFixture = exportFixturePath
    ? JSON.parse(readFileSync(exportFixturePath, "utf8"))
    : undefined;
const EXPORT_SEQUENCE = Array.isArray(exportFixture?.messages)
    ? exportFixture.messages
    : DEFAULT_EXPORT_SEQUENCE;
const EXPECTED = exportFixture?.expected ?? {
    atomCount: MOLSYS_PAYLOAD.atoms.atom_id.length,
    frame: 0,
    wholeRepresentation: null,
    regionRepresentation: "ball-and-stick",
    regionHidden: true,
    annotationTag: "exported-label",
    measurementTag: null,
    shapeTag: null,
};

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

    // ── Scenario 1: replay export sequence in order, verify end state ─────────
    console.log("[E2E export-replay] Scenario: replay export sequence");

    await page.evaluate(async (sequence) => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        (window as any).__messages = [];

        for (const msg of sequence) {
            await controller.handleMessage(msg);
        }

        // Poll until structure is present in Mol* hierarchy
        for (let i = 0; i < 80; i++) {
            const s = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
    }, EXPORT_SEQUENCE);

    // 1a. Structure loaded
    const elementCount = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data?.elementCount ?? 0;
    });
    assert.strictEqual(
        elementCount,
        EXPECTED.atomCount,
        "Mol* should render every atom produced by the Python JSON serializer",
    );

    // 1b. Annotation registered
    const hasLabel = await page.evaluate((tag) => {
        const c = (window as any).__controller;
        return (c as any).annotations?.hasTag?.(tag) === true;
    }, EXPECTED.annotationTag);
    assert.ok(hasLabel, "annotation 'exported-label' should be registered after replay");

    // 1c. Camera snapshot was applied (controller stores it)
    const cameraApplied = await page.evaluate(() => {
        const c = (window as any).__controller;
        const snap = c.getCameraSnapshot?.();
        return snap !== null && snap !== undefined;
    });
    assert.ok(cameraApplied, "camera snapshot should be applied after set_camera_snapshot op");

    // 1d. The canonical projection drives the real Mol* render tree.
    const renderedScene = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (window as any).Harness.inspectScene(c);
    });
    const renderedRegion = renderedScene.regions["exported-region"];
    assert.ok(renderedRegion, "canonical export should create exported-region");
    assert.strictEqual(renderedRegion.hidden, EXPECTED.regionHidden);
    assert.strictEqual(renderedRegion.reprs[0]?.name, EXPECTED.regionRepresentation);
    if (EXPECTED.wholeRepresentation) {
        assert.strictEqual(renderedScene.wholeReprs[0]?.name, EXPECTED.wholeRepresentation);
    }

    await page.waitForFunction((expectedFrame) => {
        const c = (window as any).__controller;
        return (c as any).trajectory?.getTrajectoryState?.()?.currentFrame === expectedFrame;
    }, EXPECTED.frame);
    const currentFrame = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).trajectory?.getTrajectoryState?.()?.currentFrame ?? -1;
    });
    assert.strictEqual(currentFrame, EXPECTED.frame, "canonical export should restore the current structure index");

    if (EXPECTED.measurementTag) {
        const hasMeasurement = await page.evaluate((tag) => {
            const c = (window as any).__controller;
            return (c as any).measurements?.hasTag?.(tag) === true;
        }, EXPECTED.measurementTag);
        assert.ok(hasMeasurement, `measurement '${EXPECTED.measurementTag}' should survive static export`);
    }
    if (EXPECTED.shapeTag) {
        const shapeRefs = await page.evaluate((tag) => {
            const c = (window as any).__controller;
            return (window as any).Harness.inspectTaggedRefs(c, "shape", tag);
        }, EXPECTED.shapeTag);
        assert.ok(
            shapeRefs.some((ref: any) => ref.exists && !ref.hidden),
            `shape '${EXPECTED.shapeTag}' should exist and be visible in Mol*`,
        );
    }

    // ── Scenario 2: replay order — load_molsys_payload must precede other ops ─
    console.log("[E2E export-replay] Scenario: replay order preserved");

    const messagesReceived = await page.evaluate(() => (window as any).__messages ?? []);
    const loadIndex = messagesReceived.findIndex((m: any) => m?.event === "registry_cleared");
    // After load_molsys_payload, a registry_cleared event is emitted (from clear_all in rebuild).
    // If no clear_all happened (single fresh load), just verify no errors occurred during replay.
    // The key invariant is that no op throws because it ran before the structure was ready.
    assert.strictEqual(errors.filter(e => e.includes("Cannot read properties")).length, 0,
        "no null-dereference errors should occur during ordered replay");

    // ── Scenario 3: re-replay on a fresh controller (simulates standalone HTML reload) ──
    console.log("[E2E export-replay] Scenario: standalone-like fresh replay");

    await page.evaluate(async () => {
        // Fully reset state
        const c = (window as any).__controller;
        await c.handleMessage({ op: "clear_all" });
    });

    await page.evaluate(async (sequence) => {
        const c = (window as any).__controller;
        for (const msg of sequence) {
            await c.handleMessage(msg);
        }
        for (let i = 0; i < 80; i++) {
            const s = (c as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
    }, EXPORT_SEQUENCE);

    const hasLabelAfterReload = await page.evaluate((tag) => {
        const c = (window as any).__controller;
        return (c as any).annotations?.hasTag?.(tag) === true;
    }, EXPECTED.annotationTag);
    assert.ok(hasLabelAfterReload, "annotation should be present after second replay (standalone reload)");

    // Scenario 4 checked that a canonical `update_visibility` replayed without error. The
    // op was removed with the atom mask in uibcdf/molsysviewer#75 phase E2, and an exported
    // page no longer carries one.

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E export-replay] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
