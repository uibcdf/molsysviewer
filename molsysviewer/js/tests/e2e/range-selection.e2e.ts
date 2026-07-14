import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const baseOpts = { headless: true };
    const launchOptions = { ...baseOpts, executablePath: envBin };

    const browser = await chromium.launch(launchOptions as any);
    
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => console.log(`[Browser] ${msg.text()}`));
    
    const harnessPath = resolve(__dirname, "harness.bundle.js");
    const html = `<!doctype html><html><body><div id="root" style="width: 800px; height: 600px;"></div></body></html>`;

    await page.goto("about:blank");
    await page.setContent(html);
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    try {
        console.log("[E2E] Scenario: Range Selection with Shift + Alt");
        
        await page.evaluate(async () => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            
            // Mock a MolSysPayload with 10 atoms in one chain
            const atom_ids = Array.from({length: 10}, (_, i) => i + 1);
            const payload = {
                atoms: {
                    atom_id: atom_ids,
                    atom_name: atom_ids.map(i => `A${i}`),
                    element_symbol: atom_ids.map(_ => "C"),
                    residue_id: atom_ids,
                    residue_name: atom_ids.map(_ => "GLY"),
                    chain_id: atom_ids.map(_ => "A"),
                    entity_id: atom_ids.map(_ => "1"),
                    molecule_id: atom_ids.map(_ => 0),
                    molecule_name: atom_ids.map(_ => "Prot"),
                    component_id: atom_ids.map(_ => 0),
                    component_name: atom_ids.map(_ => "Comp")
                },
                structures: [{
                    coordinates: atom_ids.map((_, i) => [i, i, i]),
                    time: 0
                }]
            };

            await controller.handleMessage({
                op: "load_molsys_payload",
                payload: payload,
                label: "test-range",
            });
        });

        // 1. Open GroupPanel
        const toggle = page.locator('[data-molsysviewer-group-panel-toggle="true"]');
        await toggle.click();
        
        const items = page.locator('[data-molsysviewer-group-item="true"]');
        await items.first().waitFor({ state: "visible", timeout: 10000 });

        // 2. Click on Residue 2 (index 1) to set anchor
        console.log("[E2E] Setting anchor on Residue 2...");
        await items.nth(1).click();

        // 3. Shift + Alt + Click on Residue 5 (index 4)
        console.log("[E2E] Performing Range Selection (Residue 2 to 5)...");
        // Clear messages to capture the specific event
        await page.evaluate(() => { (window as any).__messages = []; });
        await items.nth(4).click({ modifiers: ["Alt", "Shift"] });

        // 4. Verify selection contains residues 2, 3, 4, 5 (atom indices 1, 2, 3, 4)
        console.log("[E2E] Verifying range selection...");
        await page.waitForFunction(() => {
            const msgs = (window as any).__messages || [];
            return msgs.some((m: any) => m.event === "interaction_active_selection_changed" && m.atom_indices.length > 1);
        }, { timeout: 5000 });

        const selection = await page.evaluate(() => {
            const msgs = (window as any).__messages || [];
            return msgs.reverse().find((m: any) => m.event === "interaction_active_selection_changed");
        });

        // Atoms are 0-indexed in JS. Range [1, 4] means atoms at index 1, 2, 3, 4
        const expected = [1, 2, 3, 4];
        for (const idx of expected) {
            assert.ok(selection.atom_indices.includes(idx), `Should include atom index ${idx}`);
        }
        assert.strictEqual(selection.atom_indices.length, 4, "Should have exactly 4 atoms selected");

        console.log("[E2E] Range selection interaction test passed");
    } finally {
        await browser.close();
    }
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
