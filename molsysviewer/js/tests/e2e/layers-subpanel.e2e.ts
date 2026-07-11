import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// A minimal system so the viewer initialises and the group-panel chrome
// (the toggle) becomes visible; without a loaded structure the panel stays
// hidden and the toggle is unclickable.
const payload = {
    atoms: {
        atom_id: [1, 2, 3, 4, 5, 6],
        atom_name: ["N", "CA", "C", "N", "CA", "C"],
        element_symbol: ["N", "C", "C", "N", "C", "C"],
        residue_id: [1, 1, 1, 2, 2, 2],
        residue_name: ["ALA", "ALA", "ALA", "GLY", "GLY", "GLY"],
        chain_id: ["A", "A", "A", "B", "B", "B"],
        entity_id: ["1", "1", "1", "1", "1", "1"],
        molecule_id: [0, 0, 0, 0, 0, 0],
        molecule_name: ["protein", "protein", "protein", "protein", "protein", "protein"],
        component_id: [0, 0, 0, 0, 0, 0],
        component_name: ["protein", "protein", "protein", "protein", "protein", "protein"],
    },
    structures: [{
        coordinates: [
            [0, 0, 0], [1.4, 0, 0], [2.7, 0, 0],
            [4.0, 0, 0], [5.4, 0, 0], [6.7, 0, 0],
        ],
        time: 0,
    }],
};

async function latestAction(page: any, action: string) {
    await page.waitForFunction((name: string) =>
        ((window as any).__messages || []).some((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        ), action);
    return page.evaluate((name: string) =>
        [...((window as any).__messages || [])].reverse().find((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        ), action);
}

async function run() {
    const executablePath = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    let browser;
    try {
        browser = await chromium.launch({ headless: true, executablePath } as any);
    } catch {
        console.warn("[E2E] Chromium launch failed; skipping Layers subpanel test.");
        return;
    }

    const page = await browser.newPage({ viewport: { width: 1100, height: 800 } });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));

    try {
        await page.setContent('<div id="root" style="width:1000px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");
        await page.evaluate(async (molsysPayload: typeof payload) => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            await controller.handleMessage({
                op: "load_molsys_payload",
                payload: molsysPayload,
                label: "layers-subpanel-e2e",
            });
            await controller.handleMessage({
                op: "set_region_summaries",
                regions: [
                    { tag: "pocket", atom_count: 4, hidden: false, layer: "analysis" },
                    { tag: "surface", atom_count: 8, hidden: true, layer: "analysis" },
                    { tag: "unassigned", atom_count: 2, hidden: false, layer: null },
                ],
            });
            await controller.handleMessage({
                op: "add_label",
                tag: "note1",
                options: { text: "Note", atom_indices: [0], layer_tag: "analysis" },
            });
            await controller.handleMessage({
                op: "create_layer",
                tag: "marker",
                kind: "shape",
                meta: { shape_name: "Marker", shape_kind: "sphere", layer_tag: "geometry" },
            });
        }, payload);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="layers"]').click();

        await page.waitForSelector('[data-molsysviewer-layer-card="analysis"]');
        await page.waitForSelector('[data-molsysviewer-layer-card="geometry"]');
        assert.strictEqual(
            await page.locator('[data-molsysviewer-layer-member="pocket"]').count(),
            1,
        );
        assert.strictEqual(
            await page.locator('[data-molsysviewer-layer-member="note1"]').count(),
            1,
        );
        assert.strictEqual(
            await page.locator('[data-molsysviewer-layer-member="unassigned"]').count(),
            0,
        );

        await page.locator('[data-molsysviewer-layer-hide="analysis"]').click();
        assert.deepStrictEqual(
            await latestAction(page, "set_layer_visibility"),
            {
                event: "interaction_context_action",
                action: "set_layer_visibility",
                tag: "analysis",
                hidden: true,
            },
        );

        await page.locator('[data-molsysviewer-layer-show="analysis"]').click();
        const show = await latestAction(page, "set_layer_visibility");
        assert.strictEqual(show.tag, "analysis");
        assert.strictEqual(show.hidden, false);

        await page.locator('[data-molsysviewer-layer-remove-region="pocket"]').click();
        assert.strictEqual((await latestAction(page, "remove_region_from_layer")).tag, "pocket");

        await page.locator('[data-molsysviewer-layer-delete="geometry"]').click();
        assert.strictEqual((await latestAction(page, "delete_layer_group")).tag, "geometry");

        await page.locator('[data-molsysviewer-layer-assign-region="true"]').fill("unassigned");
        await page.locator('[data-molsysviewer-layer-assign-layer="true"]').fill("analysis");
        await page.locator('[data-molsysviewer-layer-assign-form="true"] button').click();
        const assign = await latestAction(page, "set_region_layer");
        assert.deepStrictEqual(
            { tag: assign.tag, layer: assign.layer },
            { tag: "unassigned", layer: "analysis" },
        );

        const hasWebglError = errors.some(error => error.includes("WebGL rendering context"));
        if (hasWebglError) {
            console.warn("[E2E] WebGL is unavailable; skipping Layers subpanel assertions.");
            return;
        }
        assert.strictEqual(errors.length, 0, `Browser errors: ${errors.join("; ")}`);
        console.log("[E2E] Layers subpanel integration test passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
