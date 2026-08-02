import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
        b_factor: [10, 12, 14, 16, 18, 20],
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
    const browser = await chromium.launch({ headless: true, executablePath } as any);

    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));

    try {
        await page.setContent('<div id="root" style="width:1000px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");
        await page.evaluate(async (molsysPayload: typeof payload) => {
            const controller = await (window as any).Harness.createController("root");
            await controller.handleMessage({
                op: "load_molsys_payload",
                payload: molsysPayload,
                label: "region-subpanel-e2e",
            });
            await controller.handleMessage({
                op: "create_region",
                tag: "pocket",
                atom_indices: [0, 1, 2, 3],
            });
            await controller.handleMessage({
                op: "create_region",
                tag: "backbone",
                atom_indices: [2, 3, 4, 5],
            });
            await controller.handleMessage({
                op: "set_region_summaries",
                representations: ["cartoon", "line", "ball-and-stick"],
                presets: ["auto", "polymer-cartoon"],
                regions: [
                    {
                        tag: "pocket",
                        atom_indices: [0, 1, 2, 3],
                        atom_count: 4,
                        hidden: false,
                        representation: "line",
                        representation_params: { alpha: 1, quality: "auto" },
                        overlap_tags: ["backbone"],
                        available_attributes: ["b_factor"],
                    },
                    {
                        tag: "backbone",
                        atom_indices: [2, 3, 4, 5],
                        atom_count: 4,
                        hidden: false,
                        representation: "cartoon",
                        representation_params: {},
                        overlap_tags: ["pocket"],
                        available_attributes: ["b_factor"],
                    },
                ],
            });
        }, payload);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="regions"]').click();

        await page.locator('[data-molsysviewer-query-input="regions"]').fill("atom_index in [0, 1]");
        await page.locator('[data-molsysviewer-query-check="regions"]').click();
        const preview = await page.evaluate(() =>
            [...((window as any).__messages || [])].reverse().find((message: any) =>
                message.event === "selection_query_preview_request"
            ));
        await page.evaluate(async requestId => {
            await (window as any).__controller.handleMessage({
                op: "selection_query_preview",
                request_id: requestId,
                ok: true,
                count: 2,
            });
        }, preview.request_id);
        assert.strictEqual((await latestAction(page, "apply_selection_query")).expression, "atom_index in [0, 1]");
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_active_selection",
                atom_indices: [0, 1],
            });
        });
        await page.locator('[data-molsysviewer-region-create-btn="true"]').click();
        await page.locator('[data-molsysviewer-region-create-input="true"]').fill("query-region");
        await page.locator('[data-molsysviewer-region-create-confirm="true"]').click();
        assert.strictEqual((await latestAction(page, "create_region_from_selection")).tag, "query-region");

        await page.locator('[data-molsysviewer-region-style="pocket"]').click();
        const opacity = page.locator('[data-molsysviewer-region-style-opacity="pocket"]');
        await opacity.fill("0.55");
        assert.strictEqual((await latestAction(page, "set_region_representation")).params.alpha, 0.55);
        await page.locator('[data-molsysviewer-region-style-color-attribute="pocket"]').selectOption("b_factor");
        assert.strictEqual((await latestAction(page, "color_region_by_attribute")).attribute, "b_factor");

        await page.locator('[data-molsysviewer-region-inspect="pocket"]').click();
        const inspectRequest = await latestAction(page, "get_region_details");
        await page.evaluate(async request => {
            await (window as any).__controller.handleMessage({
                op: "region_details",
                request_id: request.request_id,
                tag: "pocket",
                atom_count: 4,
                group_count: 2,
                chain_count: 2,
                center_nm: [0.2, 0.1, 0],
                structure_index: 0,
            });
        }, inspectRequest);
        await page.locator('[data-molsysviewer-region-inspect-frame="0"]').waitFor();

        await page.locator('[data-molsysviewer-region-rename="pocket"]').click();
        await page.locator('[data-molsysviewer-region-rename-input="pocket"]').fill("site");
        await page.locator('[data-molsysviewer-region-rename-confirm="pocket"]').click();
        assert.strictEqual((await latestAction(page, "rename_region")).new_tag, "site");
        await page.locator('[data-molsysviewer-region-delete="backbone"]').click();
        assert.strictEqual((await latestAction(page, "delete_region")).tag, "backbone");

        const hasWebglError = errors.some(error => error.includes("WebGL rendering context"));
        if (hasWebglError) {
            console.warn("[E2E] WebGL unavailable; Regions transport assertions passed.");
            return;
        }
        assert.strictEqual(errors.length, 0, `Browser errors: ${errors.join("; ")}`);
        console.log("[E2E] Regions subpanel integration test passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
