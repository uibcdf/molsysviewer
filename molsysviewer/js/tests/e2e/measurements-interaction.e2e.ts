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
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    console.log("[E2E] Scenario: Distance measurement from context menu");
    
    await page.evaluate(async pdb => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test-measurements",
        });
        
        // Wait for Mol* to process the structure
        let attempts = 0;
        while (attempts < 50) {
            const structure = (controller as any).plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (structure && structure.elementCount > 0) break;
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
    }, PDB_TEXT);

    // 1. Open GroupPanel to find items to click
    const toggle = page.locator('[data-molsysviewer-group-panel-toggle="true"]');
    await toggle.click();
    
    // 2. Right click on first item (MET 1) to start distance measurement
    const items = page.locator('[data-molsysviewer-group-item="true"]');
    await items.first().click({ button: "right" });
    
    const distanceAction = page.locator('[data-molsysviewer-context-menu="true"] button:text-is("Distance")');
    await distanceAction.click();
    
    // 3. Verify tool state: started
    console.log("[E2E] Verifying tool state: started");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        return msgs.some((m: any) => m.event === "interaction_tool_state" && m.action === "distance" && m.status === "started");
    }, { timeout: 5000 });

    // 4. Click on the same item or another one to complete (simplified for E2E)
    // In a real scenario we'd click on the 3D canvas, but clicking the GroupStrip item 
    // also triggers the controller's selection logic which we can use if we simulate the event properly.
    // However, the measurement tool specifically listens to handlePrimaryClick(ev).
    
    console.log("[E2E] Simulating second pick using the first pick's loci...");
    await page.evaluate(() => {
        const controller = (window as any).__controller;
        const loci = controller.lastContextLoci;
        if (!loci) {
            console.error("[Browser] No lastContextLoci found!");
            return;
        }
        console.log("[Browser] Using loci for second pick:", loci.kind);
        controller.measurementTools.handlePrimaryClick(loci);
    });

    // 5. Verify measurement created
    console.log("[E2E] Waiting for interaction_measurement_created event...");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        return msgs.some((m: any) => m.event === "interaction_measurement_created" && m.action === "distance");
    }, { timeout: 5000 });
    
    const measurement = await page.evaluate(() => {
        const msgs = (window as any).__messages || [];
        return msgs.reverse().find((m: any) => m.event === "interaction_measurement_created");
    });
    
    assert.strictEqual(measurement.action, "distance");
    assert.strictEqual(measurement.picked_count, 2);
    assert.ok(measurement.picks_atom_indices.length === 2);

    console.log("[E2E] Scenario: Angle measurement from context menu");
    
    // 6. Right click on first item again to start angle measurement
    await items.first().click({ button: "right" });
    const angleAction = page.locator('[data-molsysviewer-context-menu="true"] button:text-is("Angle")');
    await angleAction.click();
    
    // 7. Verify tool state: started (angle)
    console.log("[E2E] Verifying tool state: started (angle)");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        // We look for the last started event for 'angle'
        return msgs.some((m: any) => m.event === "interaction_tool_state" && m.action === "angle" && m.status === "started");
    }, { timeout: 5000 });

    // 8. Simulate two more picks for angle (total 3)
    console.log("[E2E] Simulating second and third picks for angle...");
    await page.evaluate(() => {
        const controller = (window as any).__controller;
        const loci = controller.lastContextLoci;
        // Pick 2
        controller.measurementTools.handlePrimaryClick(loci);
        // Pick 3
        controller.measurementTools.handlePrimaryClick(loci);
    });

    // 9. Verify angle measurement created
    console.log("[E2E] Waiting for interaction_measurement_created event (angle)...");
    await page.waitForFunction(() => {
        const msgs = (window as any).__messages || [];
        return msgs.some((m: any) => m.event === "interaction_measurement_created" && m.action === "angle");
    }, { timeout: 5000 });

    await browser.close();
    
    const hasWebglError = errors.some(e => e.includes("WebGL rendering context"));
    if (hasWebglError) {
        console.warn("[E2E] WebGL is not available; skipping test.");
        process.exit(0);
    }
    
    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E] Measurements interaction test passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
