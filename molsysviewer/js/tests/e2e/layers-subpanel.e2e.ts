import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       1.450   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       2.800   0.000   0.000  1.00 20.00           C
ATOM      4  N   GLY A   2       4.000   0.000   0.000  1.00 20.00           N
ATOM      5  CA  GLY A   2       5.450   0.000   0.000  1.00 20.00           C
ATOM      6  C   GLY A   2       6.800   0.000   0.000  1.00 20.00           C
END
`;

async function latestAction(page: any, action: string) {
    await page.waitForFunction((name: string) =>
        ((window as any).__messages || []).some((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        ), action);
    return page.evaluate((name: string) => {
        const messages = (window as any).__messages || [];
        const index = messages.findIndex((message: any) =>
            message.event === "interaction_context_action" && message.action === name
        );
        return messages.splice(index, 1)[0];
    }, action);
}

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
            await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "layers" });
            await controller.handleMessage({ op: "create_region", tag: "pocket", atom_indices: [0, 1, 2] });
            await controller.handleMessage({
                op: "set_region_representation", tag: "pocket", representation: "ball-and-stick", params: {},
            });
            await controller.handleMessage({
                op: "add_sphere",
                options: { center: [0, 0, 0], radius: 1.5, color: 0x00ff00, alpha: 1, tag: "marker" },
            });
            await controller.handleMessage({
                op: "set_region_summaries",
                regions: [{ tag: "pocket", atom_count: 3, hidden: false, layer: null }],
            });
            await controller.handleMessage({
                op: "set_shape_summaries",
                shapes: [{ op: "add_sphere", kind: "sphere", tag: "marker", title: "Marker", layer_tag: "marker", hidden: false }],
            });
            await controller.handleMessage({
                op: "set_layer_summaries",
                layers: [{ tag: "marker", provenance: "auto", hidden: false }],
            });
        }, PDB_TEXT);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="layers"]').click();

        await page.locator('[data-molsysviewer-layer-create-input="true"]').fill("analysis");
        await page.locator('[data-molsysviewer-layer-create-form="true"] button').click();
        const actions = [await latestAction(page, "create_layer")];

        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_layer_summaries",
                layers: [
                    { tag: "analysis", provenance: "user", hidden: false },
                    { tag: "marker", provenance: "auto", hidden: false },
                ],
            });
        });
        await page.locator('[data-molsysviewer-layer-details="analysis"]').click();
        await page.locator('[data-molsysviewer-layer-member-picker="analysis"]').selectOption(JSON.stringify(["region", "pocket"]));
        await page.locator('[data-molsysviewer-layer-add-member="analysis"]').click();
        actions.push(await latestAction(page, "add_member_to_layer"));

        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_region_summaries",
                regions: [{ tag: "pocket", atom_count: 3, hidden: false, layer: "analysis" }],
            });
        });
        await page.locator('[data-molsysviewer-layer-member-picker="analysis"]').selectOption(JSON.stringify(["shape", "marker"]));
        await page.locator('[data-molsysviewer-layer-add-member="analysis"]').click();
        actions.push(await latestAction(page, "add_member_to_layer"));

        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({
                op: "set_shape_summaries",
                shapes: [{ op: "add_sphere", kind: "sphere", tag: "marker", title: "Marker", layer_tag: "analysis", hidden: false }],
            });
        });
        await page.locator('[data-molsysviewer-layer-visibility="analysis"]').click();
        actions.push(await latestAction(page, "set_layer_visibility"));
        await page.locator('[data-molsysviewer-layer-ungroup="analysis"]').click();
        actions.push(await latestAction(page, "ungroup_layer"));

        const python = spawnSync(
            process.env.PYTHON || "python",
            [resolve(__dirname, "layers-subpanel-bridge.py")],
            { input: JSON.stringify(actions), encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
        );
        assert.strictEqual(python.status, 0, python.stderr || python.stdout);
        const backend = JSON.parse(python.stdout);
        assert.strictEqual(backend.states[1].region_layer, "analysis", "region used the wrong membership channel");
        assert.strictEqual(backend.states[1].shape_layer, "marker", "region assignment touched its shape namesake");
        assert.strictEqual(backend.states[2].shape_layer, "analysis");
        assert.strictEqual(backend.states[3].region_visible, false);
        assert.strictEqual(backend.states[3].shape_visible, false);
        assert.deepStrictEqual(backend.states[4], {
            layer_exists: false,
            region_exists: true,
            region_layer: null,
            region_visible: false,
            shape_exists: true,
            shape_layer: "marker",
            shape_visible: false,
        });

        const hidden = await page.evaluate(async messages => {
            const controller = (window as any).__controller;
            for (const message of messages) await controller.handleMessage(message);
            return {
                region: (window as any).Harness.inspectScene(controller).regions.pocket,
                shape: (window as any).Harness.inspectTaggedRefs(controller, "shape", "marker"),
            };
        }, backend.batches[3]);
        assert.strictEqual(hidden.region.hidden, true, "region remained visible in Mol*");
        assert.ok(hidden.shape.length > 0 && hidden.shape.every((ref: any) => ref.hidden), "shape remained visible in Mol*");

        const preserved = await page.evaluate(async messages => {
            const controller = (window as any).__controller;
            for (const message of messages) await controller.handleMessage(message);
            return {
                region: (window as any).Harness.inspectScene(controller).regions.pocket,
                shape: (window as any).Harness.inspectTaggedRefs(controller, "shape", "marker"),
            };
        }, backend.batches[4]);
        assert.ok(preserved.region, "ungroup deleted the region from Mol*");
        assert.ok(preserved.shape.length > 0 && preserved.shape.every((ref: any) => ref.exists), "ungroup deleted the shape from Mol*");

        console.log("[E2E layers-subpanel] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
