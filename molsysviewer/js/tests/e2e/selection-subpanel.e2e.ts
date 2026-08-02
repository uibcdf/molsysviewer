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
    const browser = await chromium.launch({ headless: true, executablePath } as any);

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

        // Query request and backend response.
        const query = page.locator('[data-molsysviewer-query-input="selection"]');
        await query.fill("atom_index in [0, 1]");
        assert.strictEqual(
            await page.evaluate(() =>
                ((window as any).__messages || []).some((message: any) =>
                    message.event === "selection_query_preview_request"
                )
            ),
            false,
        );
        await page.locator('[data-molsysviewer-query-check="selection"]').click();
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
        const queryAction = await latestAction(page, "apply_selection_query");
        assert.strictEqual(queryAction.expression, "atom_index in [0, 1]");
        assert.strictEqual(queryAction.op, "replace");
        await setActiveSelection(page, [0, 1]);

        // Compose through a real strip click. The strips live in the System tab, so
        // they are not rendered while Selection is the active tab: the click has to
        // happen there and then come back. (This is why the test used to hang on an
        // invisible element for 30 s and then time out.)
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        await page.locator('[data-molsysviewer-group-item="true"]').nth(1).click({ modifiers: ["Shift"] });
        // The backend echo preserves the exact atom subset [0, 1] inside its
        // group-level item. Shift adds the complete GLY group {3, 4, 5}, giving
        // five atoms without expanding the original subset to all of ALA.
        await page.waitForFunction(() =>
            ((window as any).__messages || []).some((message: any) =>
                message.event === "interaction_active_selection_changed"
                && message.atom_indices?.length === 5
            )
        );
        await page.locator('[data-molsysviewer-group-panel-tab="selection"]').click();

        // Expand to chain from the context menu, then save and apply the backend echoes.
        // Again: the strip's context menu is only reachable from the System tab.
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        await page.locator('[data-molsysviewer-group-item="true"]').first().click({ button: "right" });
        await page.waitForSelector('[data-molsysviewer-context-menu="true"]');
        await page.locator('[data-molsysviewer-context-menu="true"] button').filter({ hasText: "Chain" }).click();
        const expand = await latestAction(page, "expand_selection");
        assert.strictEqual(expand.level, "chain");
        await setActiveSelection(page, [0, 1, 2]);
        await page.locator('[data-molsysviewer-group-panel-tab="selection"]').click();

        await page.locator('[data-molsysviewer-active-selection-save-toggle="true"]').click();
        await page.locator('[data-molsysviewer-active-selection-save-input="true"]').fill("chain_a");
        await page.locator('[data-molsysviewer-active-selection-save-confirm="true"]').click();
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
        // Not `filter({ hasText: "Rename" })`: the card's toolbar carries a Rename
        // button too, so the text matches two elements and Playwright refuses.
        await page.locator('[data-molsysviewer-saved-selection-confirm-mode="rename"]').click();
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
        await page.locator('[data-molsysviewer-saved-selection-confirm-mode="region"]').click();
        const promote = await latestAction(page, "create_region_from_saved_selection");
        assert.deepStrictEqual(
            { selection_tag: promote.selection_tag, tag: promote.tag },
            { selection_tag: "active_chain", tag: "active_chain_region" },
        );

        // Promote the saved selection directly to an annotation.
        await page.locator('[data-molsysviewer-saved-selection-to-label="active_chain"]').click();
        await renamedCard.locator("input").fill("Active chain");
        await page.locator('[data-molsysviewer-saved-selection-confirm-mode="label"]').click();
        const label = await latestAction(page, "create_label_from_saved_selection");
        assert.deepStrictEqual(
            { selection_tag: label.selection_tag, text: label.text },
            { selection_tag: "active_chain", text: "Active chain" },
        );

        // Undo/redo are no longer a frontend-local stack: the Selection panel's
        // keyboard shortcuts drive the single scene history in Python. Their
        // enabled state is pushed from Python via set_history_state.
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_history_state", can_undo: true, can_redo: false,
            });
        });
        const selectionPanel = page.locator('[data-molsysviewer-selection-panel="true"]');
        await selectionPanel.press("Control+z");
        await page.waitForFunction(() =>
            ((window as any).__messages || []).some((m: any) => m.event === "scene_history_undo"));

        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_history_state", can_undo: true, can_redo: true,
            });
        });
        await selectionPanel.press("Control+y");
        await page.waitForFunction(() =>
            ((window as any).__messages || []).some((m: any) => m.event === "scene_history_redo"));

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
