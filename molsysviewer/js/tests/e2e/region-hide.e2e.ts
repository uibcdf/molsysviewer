import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
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

type BrowserController = {
    getStructureData(): { elementCount: number } | undefined;
    hasRegion(tag: string): boolean;
    isRegionHidden(tag: string): boolean | undefined;
    handleMessage(message: Record<string, unknown>): Promise<void>;
};

type BrowserWindow = Window & typeof globalThis & { __controller?: BrowserController };

async function run() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 900 });

    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => {
        if (msg.type() === "error") errors.push(msg.text());
    });

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    const html = `
    <!doctype html>
    <html>
      <body>
        <div id="root" style="width: 800px; height: 600px;"></div>
      </body>
    </html>`;

    await page.setContent(html, { waitUntil: "networkidle" });
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => !!(window as any).Harness, { timeout: 30000 });

    await page.evaluate(async pdb => {
        const browserWindow = window as BrowserWindow;
        const controller = await (browserWindow.Harness as { createController(target: string): Promise<BrowserController> }).createController("root");
        browserWindow.__controller = controller;
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test",
        });
        const structure = controller.getStructureData();
        const n = structure?.elementCount ?? 0;
        if (n <= 0) throw new Error("Expected a loaded structure before creating the region");
        const atomIndices = Array.from({ length: n }, (_, i) => i);
        await controller.handleMessage({
            op: "create_region",
            tag: "region1",
            atom_indices: atomIndices,
            representation: "ball-and-stick",
        });
        if (!controller.hasRegion("region1")) throw new Error("Expected region1 to exist before hiding it");
        await controller.handleMessage({ op: "hide_region", tag: "region1" });
        if (controller.isRegionHidden("region1") !== true) throw new Error("Expected region1 to be hidden");
        await controller.handleMessage({ op: "set_panel_mode", panel: "navigate", expanded: true });
        // Wait for panel CSS transition to complete
        await new Promise(r => setTimeout(r, 300));
    }, PDB_TEXT);

    await page.waitForSelector('[data-molsysviewer-group-strip="true"]', { timeout: 30000 });
    const firstGroup = page.locator('[data-molsysviewer-group-item="true"]').first();
    await firstGroup.click({ button: "right" });
    await page.waitForSelector('[data-molsysviewer-context-menu="true"]', { timeout: 30000 });
    const menuTitle = await page.locator('[data-molsysviewer-context-menu-title="true"]').textContent();
    assert.ok(menuTitle && menuTitle !== "Canvas", `Expected a group context menu title, got: ${menuTitle}`);
    assert.ok(!String(menuTitle).includes("No target under cursor"), `Unexpected empty-target menu title: ${menuTitle}`);

    await page.evaluate(async pdb => {
        const controller = (window as BrowserWindow).__controller;
        if (!controller) throw new Error("Controller not available for second scenario");

        // Add a tagged shape and clear it.
        await controller.handleMessage({
            op: "add_sphere",
            options: {
                center: [10, 10, 10],
                radius: 2.0,
                color: 0x00ff00,
                alpha: 0.35,
                tag: "shape-e2e",
            },
        });
        await controller.handleMessage({ op: "clear_shapes_by_tag", tag: "shape-e2e" });

        // Full scene reset and assert registry clear event propagated back.
        const msgsBefore: number = ((window as any).__messages ?? []).length;
        await controller.handleMessage({ op: "clear_all" });
        const msgsAfterClear: any[] = (window as any).__messages ?? [];
        const hadRegistryCleared = msgsAfterClear.slice(msgsBefore).some((m: any) => m?.event === "registry_cleared");
        if (!hadRegistryCleared) {
            throw new Error("Expected registry_cleared event after clear_all");
        }

        // Reload to ensure controller remains usable after full reset.
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "reload-after-clear-all",
        });
    }, PDB_TEXT);

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors detected: ${errors.join("; ")}`);
    console.log("[E2E] passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
