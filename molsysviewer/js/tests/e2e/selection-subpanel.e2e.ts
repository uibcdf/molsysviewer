import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
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
    await page.waitForFunction((name: string) => {
        const messages = (window as any).__messages || [];
        return messages.some((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        );
    }, action);
    return page.evaluate((name: string) => {
        const messages = (window as any).__messages || [];
        return [...messages].reverse().find((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        );
    }, action);
}

async function setActiveSelection(page: any, atomIndices: number[]) {
    await page.evaluate(async (indices: number[]) => {
        await (window as any).__controller.handleMessage({
            op: "set_active_selection",
            atom_indices: indices,
        });
    }, atomIndices);
}

async function run() {
    const executablePath = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    let browser;
    try {
        browser = await chromium.launch({ headless: true, executablePath } as any);
    } catch {
        console.warn("[E2E] Chromium launch failed; skipping Selection subpanel test.");
        return;
    }

    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));

    try {
        await page.setContent('<div id="root" style="width: 1000px; height: 760px;"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");
        await page.evaluate(async (molsysPayload: typeof payload) => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            await controller.handleMessage({
                op: "load_molsys_payload",
                payload: molsysPayload,
                label: "selection-subpanel-e2e",
            });
        }, payload);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="selection"]').click();

        // Active-selection quick operations are independent of the query composer.
        await page.locator('[data-molsysviewer-selection-all="true"]').click();
        assert.strictEqual((await latestAction(page, "set_active_selection_operation")).operation, "all");
        await setActiveSelection(page, [0, 1, 2, 3, 4, 5]);
        await page.locator('[data-molsysviewer-selection-none="true"]').click();
        assert.strictEqual((await latestAction(page, "set_active_selection_operation")).operation, "none");
        await setActiveSelection(page, []);
        await page.locator('[data-molsysviewer-selection-invert="true"]').click();
        assert.strictEqual((await latestAction(page, "set_active_selection_operation")).operation, "invert");
        await setActiveSelection(page, [0, 1, 2, 3, 4, 5]);

        // Query request and backend response.
        const query = page.locator('[data-molsysviewer-selection-query-input="true"]');
        await query.fill("atom_index in [0, 1]");
        await page.waitForFunction(() =>
            ((window as any).__messages || []).some((message: any) =>
                message.event === "selection_query_preview_request"
            )
        );
        await page.locator('[data-molsysviewer-selection-query-apply="replace"]').click();
        const queryAction = await latestAction(page, "apply_selection_query");
        assert.strictEqual(queryAction.expression, "atom_index in [0, 1]");
        assert.strictEqual(queryAction.op, "replace");
        await setActiveSelection(page, [0, 1]);

        // Compose through a real strip click.
        await page.locator('[data-molsysviewer-group-item="true"]').nth(1).click({ modifiers: ["Shift"] });
        await page.waitForFunction(() =>
            ((window as any).__messages || []).some((message: any) =>
                message.event === "interaction_active_selection_changed"
                && message.atom_indices?.length === 5
            )
        );

        // Register a saved selection and exercise union and subtraction.
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "save_selection",
                tag: "tail",
                atom_indices: [3, 4, 5],
                element_level: "group",
            });
        });
        await page.locator('[data-molsysviewer-saved-selection-compose-add="tail"]').click();
        const union = await latestAction(page, "compose_saved_selection");
        assert.deepStrictEqual({ tag: union.tag, op: union.op }, { tag: "tail", op: "add" });
        await setActiveSelection(page, [0, 1, 2, 3, 4, 5]);

        await page.locator('[data-molsysviewer-saved-selection-compose-subtract="tail"]').click();
        const subtract = await latestAction(page, "compose_saved_selection");
        assert.deepStrictEqual({ tag: subtract.tag, op: subtract.op }, { tag: "tail", op: "subtract" });
        await setActiveSelection(page, [0, 1, 2]);

        // Expand to chain, then save and apply the backend echoes.
        await page.locator('[data-molsysviewer-selection-expand-level="chain"]').click();
        const expand = await latestAction(page, "expand_selection");
        assert.strictEqual(expand.level, "chain");
        await setActiveSelection(page, [0, 1, 2]);

        await page.locator('[data-molsysviewer-selection-save="true"]').click();
        await page.locator('[data-molsysviewer-selection-inline-input="true"]').fill("chain_a");
        await page.locator('[data-molsysviewer-selection-inline-form="true"] button').filter({ hasText: "Save" }).click();
        const save = await latestAction(page, "save_selection");
        assert.strictEqual(save.tag, "chain_a");
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "save_selection",
                tag: "chain_a",
                atom_indices: [0, 1, 2],
                element_level: "chain",
            });
        });

        // Rename and promote the saved selection to a region.
        await page.locator('[data-molsysviewer-saved-selection-rename="chain_a"]').click();
        const chainCard = page.locator('[data-molsysviewer-saved-selection-card="chain_a"]');
        await chainCard.locator("input").fill("active_chain");
        await chainCard.locator("button").filter({ hasText: "Rename" }).click();
        const rename = await latestAction(page, "rename_selection");
        assert.deepStrictEqual(
            { tag: rename.tag, new_tag: rename.new_tag },
            { tag: "chain_a", new_tag: "active_chain" },
        );
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_selection_tag",
                tag: "chain_a",
                new_tag: "active_chain",
            });
        });

        await page.locator('[data-molsysviewer-saved-selection-to-region="active_chain"]').click();
        const renamedCard = page.locator('[data-molsysviewer-saved-selection-card="active_chain"]');
        await renamedCard.locator("input").fill("active_chain_region");
        await renamedCard.locator("button").filter({ hasText: "Create" }).click();
        const promote = await latestAction(page, "create_region_from_saved_selection");
        assert.deepStrictEqual(
            { selection_tag: promote.selection_tag, tag: promote.tag },
            { selection_tag: "active_chain", tag: "active_chain_region" },
        );

        // Promote the active selection directly to a label.
        await page.locator('[data-molsysviewer-selection-to-label="true"]').click();
        await page.locator('[data-molsysviewer-selection-inline-input="true"]').fill("Active chain");
        await page.locator('[data-molsysviewer-selection-inline-form="true"] button')
            .filter({ hasText: "Add Label" })
            .click();
        const label = await latestAction(page, "add_label_from_selection");
        assert.strictEqual(label.text, "Active chain");

        // Undo and redo are frontend-local and emit the restored selection.
        await page.locator('[data-molsysviewer-selection-undo="true"]').click();
        await page.locator('[data-molsysviewer-selection-redo="true"]').click();
        assert.strictEqual(
            await page.locator('[data-molsysviewer-selection-redo="true"]').isDisabled(),
            true,
        );

        const hasWebglError = errors.some(error => error.includes("WebGL rendering context"));
        if (hasWebglError) {
            console.warn("[E2E] WebGL is unavailable; skipping Selection subpanel assertions.");
            return;
        }
        assert.strictEqual(errors.length, 0, `Browser errors: ${errors.join("; ")}`);
        console.log("[E2E] Selection subpanel integration test passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
