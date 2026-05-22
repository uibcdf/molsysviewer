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
ATOM      5  N   ALA B   2      14.000  14.000  14.000  1.00 20.00           N
ATOM      6  CA  ALA B   2      15.000  15.000  15.000  1.00 20.00           C
END
`;

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const baseOpts = { headless: true };
    const launchOptions = { ...baseOpts, executablePath: envBin };

    let browser;
    try {
        browser = await chromium.launch(launchOptions as any);
    } catch (err) {
        console.warn("[E2E] Chromium launch failed; skipping test.");
        process.exit(0);
    }
    
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    
    const harnessPath = resolve(__dirname, "harness.bundle.js");
    const html = `<!doctype html><html><body><div id="root" style="width: 800px; height: 600px;"></div></body></html>`;

    await page.goto("about:blank");
    await page.setContent(html);
    
    console.log("[E2E] Injecting harness...");
    await page.addScriptTag({ path: harnessPath });
    
    console.log("[E2E] Waiting for Harness to be ready...");
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined", { timeout: 30000 });

    console.log("[E2E] Scenario: Loading structure...");
    
    await page.evaluate(async pdb => {
        console.log("[Browser] Creating controller...");
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        console.log("[Browser] Loading structure...");
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test-group-panel",
        });
        
        // Wait for Mol* to process the structure
        let attempts = 0;
        while (attempts < 50) {
            const structure = (controller as any).plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (structure && structure.elementCount > 0) {
                console.log(`[Browser] Structure ready with ${structure.elementCount} atoms and ${structure.units.length} units.`);
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
    }, PDB_TEXT);

    console.log("[E2E] Waiting for GroupPanel to be visible...");
    const panel = page.locator('[data-molsysviewer-group-panel="true"]');
    await panel.waitFor({ state: "visible", timeout: 30000 });
    
    console.log("[E2E] GroupPanel is visible. Opening...");
    const toggle = page.locator('[data-molsysviewer-group-panel-toggle="true"]');
    await toggle.click();
    
    console.log("[E2E] Waiting for Chain A strip...");
    await page.waitForSelector('[data-molsysviewer-group-strip-title="A"]', { timeout: 30000 });
    await page.waitForSelector('[data-molsysviewer-group-strip-title="B"]');
    
    console.log("[E2E] Clicking on an item in Chain A...");
    // Clear previous messages to avoid race conditions with initial empty selections
    await page.evaluate(() => { (window as any).__messages = []; });
    
    const itemA = page.locator('[data-molsysviewer-group-item="true"]').first();
    await itemA.click();
    
    console.log("[E2E] Waiting for interaction_active_selection_changed event...");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        return msgs.some((m: any) => m.event === "interaction_active_selection_changed" && m.items.length > 0);
    }, { timeout: 5000 });
    
    const selection = await page.evaluate(() => {
        const msgs = (window as any).__messages || [];
        // Get the latest one that has items
        return msgs.reverse().find((m: any) => m.event === "interaction_active_selection_changed" && m.items.length > 0);
    });
    
    assert.ok(selection, "Should have found a selection event with items");
    assert.strictEqual(selection.items.length, 1, "Should have exactly 1 item selected");
    assert.ok(selection.atom_indices.length > 0, "Atom indices should not be empty");
    
    // 6. Right click on an item and check context menu
    await itemA.click({ button: "right" });
    await page.waitForSelector('[data-molsysviewer-context-menu="true"]');
    
    // 7. Verify "Add Label" action in context menu and click it
    const addLabelAction = page.locator('button:has-text("Add Label")');
    await addLabelAction.click();
    
    // 8. Fill the label composer
    const labelInput = page.locator('input[placeholder="Label text"]');
    await labelInput.fill("My Test Label");
    await page.keyboard.press("Enter");
    
    // 9. SIMULATE PYTHON BACKEND: 
    // Wait for the action message, then send back the add_label command
    console.log("[E2E] Simulating Python response for add_label_from_selection...");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        return msgs.some((m: any) => m.event === "interaction_context_action" && m.action === "add_label_from_selection");
    }, { timeout: 5000 });
    
    const lastAction = await page.evaluate(() => {
        const msgs = (window as any).__messages || [];
        return msgs.reverse().find((m: any) => m.event === "interaction_context_action" && m.action === "add_label_from_selection");
    });
    
    await page.evaluate(async (action) => {
        const controller = (window as any).__controller;
        await controller.handleMessage({
            op: "add_label",
            tag: "e2e-label",
            options: {
                text: action.text,
                atom_indices: action.context.atom_indices,
                tag: "e2e-label"
            }
        });
    }, lastAction);

    // 10. Verify the label was added and the badge appears in the strip
    console.log("[E2E] Waiting for label badge to appear...");
    const badge = page.locator('[data-molsysviewer-group-item="true"]').first().locator('span:has-text("L")');
    await badge.waitFor({ state: "visible", timeout: 10000 });
    
    assert.strictEqual(lastAction.text, "My Test Label");

    await browser.close();
    
    const hasWebglError = errors.some(e => e.includes("WebGL rendering context"));
    if (hasWebglError) {
        console.warn("[E2E] WebGL is not available in this environment; skipping test.");
        process.exit(0);
    }
    
    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E] GroupPanel interaction test passed");
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
