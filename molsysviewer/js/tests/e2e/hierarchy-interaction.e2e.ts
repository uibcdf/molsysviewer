import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// PDB with two molecules in chain A (MET 1-4 and ALA 5-6)
// We'll simulate the MolSysMT hierarchy in the test if needed, 
// but since we're using load_structure_from_string, the Python backend 
// (which we don't have here) would normally provide the indices.
// To test this E2E, we need to mock the payload correctly.

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
        console.log("[E2E] Scenario: Hierarchical GroupPanel Selection");
        
        await page.evaluate(async () => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            
            // Mock a MolSysPayload with 2 molecules and 2 components
            const payload = {
                atoms: {
                    atom_id: [1, 2, 3, 4],
                    atom_name: ["N", "CA", "C", "O"],
                    element_symbol: ["N", "C", "C", "O"],
                    residue_id: [1, 1, 2, 2],
                    residue_name: ["MET", "MET", "ALA", "ALA"],
                    chain_id: ["A", "A", "A", "A"],
                    entity_id: ["1", "1", "1", "1"],
                    molecule_id: [0, 0, 1, 1],
                    molecule_name: ["ProtA", "ProtA", "LigB", "LigB"],
                    component_id: [0, 0, 1, 1],
                    component_name: ["Comp1", "Comp1", "Comp2", "Comp2"]
                },
                structures: [{
                    coordinates: [[0,0,0], [1,1,1], [2,2,2], [3,3,3]],
                    time: 0
                }]
            };

            await controller.handleMessage({
                op: "load_molsys_payload",
                payload: payload,
                label: "test-hierarchy",
            });
        });

        // 1. Open GroupPanel
        const toggle = page.locator('[data-molsysviewer-group-panel-toggle="true"]');
        await toggle.click();
        
        console.log("[E2E] Waiting for hierarchy boxes...");
        const molBoxes = page.locator('div[title^="Molecule:"]');
        await assert.doesNotReject(molBoxes.first().waitFor({ state: "visible", timeout: 10000 }));
        const countMols = await molBoxes.count();
        assert.strictEqual(countMols, 2, `Should have 2 molecule boxes, found ${countMols}`);

        // 2. Click Molecule 2 Handle (the second one, which has molId = 1)
        console.log("[E2E] Clicking Molecule handle...");
        const molHandle = page.locator('[data-molsysviewer-group-strip-molecule-handle="1"]');
        await molHandle.click();

        // 3. Verify selection contains atoms from Molecule 2 (indices 2, 3)
        console.log("[E2E] Verifying selection...");
        await page.waitForFunction(() => {
            const msgs = (window as any).__messages || [];
            return msgs.some((m: any) => m.event === "interaction_active_selection_changed" && m.atom_indices.length > 0);
        }, { timeout: 5000 });

        const selection = await page.evaluate(() => {
            const msgs = (window as any).__messages || [];
            return msgs.reverse().find((m: any) => m.event === "interaction_active_selection_changed");
        });

        assert.ok(selection.atom_indices.includes(2));
        assert.ok(selection.atom_indices.includes(3));
        assert.strictEqual(selection.atom_indices.length, 2);

        console.log("[E2E] Hierarchy interaction test passed");
    } finally {
        await browser.close();
    }
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
