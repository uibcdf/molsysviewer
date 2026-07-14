import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   ALA A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  ALA A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   ALA A   1      13.111  12.010   7.724  1.00 20.00           C
END
`;

async function run() {
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
        await page.evaluate(async pdb => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "history" });
            await controller.handleMessage({
                op: "set_region_summaries",
                regions: [{
                    tag: "pocket", atom_count: 3, atom_indices: [0, 1, 2], hidden: false,
                    representation: "line", preset: null, representation_params: { alpha: 0.2 },
                    overlap_tags: [], available_attributes: [],
                }],
            });
        }, PDB_TEXT);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
        await page.locator('[data-molsysviewer-region-style="pocket"]').click();
        const opacity = page.locator('[data-molsysviewer-region-style-opacity="pocket"]');
        await opacity.evaluate(async (element: HTMLInputElement) => {
            const controller = (window as any).__controller;
            element.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
            for (const value of ["0.3", "0.4", "0.5", "0.6", "0.7", "0.8"]) {
                element.value = value;
                element.dispatchEvent(new Event("input", { bubbles: true }));
                await controller.handleMessage({
                    op: "set_region_summaries",
                    regions: [{
                        tag: "pocket", atom_count: 3, atom_indices: [0, 1, 2], hidden: false,
                        representation: "line", preset: null, representation_params: { alpha: Number(value) },
                        overlap_tags: [], available_attributes: [],
                    }],
                });
                const current = document.querySelector('[data-molsysviewer-region-style-opacity="pocket"]');
                if (current !== element) throw new Error("region summary replaced the active opacity control");
            }
            element.dispatchEvent(new PointerEvent("pointerup", { bubbles: true }));
        });

        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({ op: "set_history_state", can_undo: true, can_redo: false });
        });
        await page.locator('[data-molsysviewer-group-panel-tab="selection"]').click();
        await page.locator('[data-molsysviewer-selection-undo="true"]').click();

        const events = await page.evaluate(() => ((window as any).__messages || []).filter((message: any) =>
            message.event === "scene_history_coalescing_begin"
            || message.event === "scene_history_coalescing_end"
            || message.event === "scene_history_undo"
            || (message.event === "interaction_context_action" && message.action === "set_region_representation")
        ));
        assert.strictEqual(events.filter((event: any) => event.event === "scene_history_coalescing_begin").length, 1);
        assert.strictEqual(events.filter((event: any) => event.action === "set_region_representation").length, 6);
        assert.strictEqual(events.filter((event: any) => event.event === "scene_history_coalescing_end").length, 1);
        assert.strictEqual(events.at(-1)?.event, "scene_history_undo");

        const python = spawnSync(
            process.env.PYTHON || "python",
            [resolve(__dirname, "history-coalescing-bridge.py")],
            { input: JSON.stringify(events), encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
        );
        assert.strictEqual(python.status, 0, python.stderr || python.stdout);
        const result = JSON.parse(python.stdout);
        assert.deepStrictEqual(result, {
            depth_before_undo: 1,
            alpha_before_undo: 0.8,
            alpha_after_undo: 0.2,
        });
        console.log("[E2E history-coalescing] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
