import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   GLY A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  GLY A   1      12.560  13.329   8.276  1.00 20.00           C
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
            await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "roundtrip" });
            await controller.handleMessage({
                op: "add_label",
                tag: "note",
                options: { text: "site", tag: "note", atom_indices: [0] },
            });
            await controller.handleMessage({
                op: "set_annotation_summaries",
                annotations: [{
                    kind: "label", tag: "note", owner: "elastnetmt", text: "site", atom_indices: [0],
                    layer_tag: "note", hidden: false,
                }],
            });
        }, PDB_TEXT);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="annotations"]').click();
        const row = page.locator('[data-molsysviewer-annotation-tag="note"]');
        assert.match(
            await row.locator('[data-molsysviewer-annotation-identity="note"]').textContent() || "",
            /from elastnetmt/,
        );
        await row.locator('[data-molsysviewer-annotation-visibility="note"]').click();
        const action = await page.evaluate(() =>
            [...((window as any).__messages || [])].reverse().find((message: any) =>
                message.event === "interaction_context_action"
                && message.action === "toggle_annotation_visibility"
            )
        );
        assert.deepStrictEqual(action, {
            event: "interaction_context_action",
            action: "toggle_annotation_visibility",
            tag: "note",
        });

        const python = spawnSync(
            process.env.PYTHON || "python",
            [resolve(__dirname, "scene-object-panel-bridge.py")],
            { input: JSON.stringify(action), encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
        );
        assert.strictEqual(python.status, 0, python.stderr || python.stdout);
        const backend = JSON.parse(python.stdout);
        assert.strictEqual(backend.visible, false, "Python visibility did not change");

        const rendered = await page.evaluate(async messages => {
            const controller = (window as any).__controller;
            for (const message of messages) await controller.handleMessage(message);
            return {
                refs: (window as any).Harness.inspectTaggedRefs(controller, "annotation", "note"),
                eyeTitle: document.querySelector('[data-molsysviewer-annotation-visibility="note"]')?.getAttribute("title"),
            };
        }, backend.messages);
        assert.ok(rendered.refs.length > 0, "annotation registered no Mol* nodes");
        assert.ok(
            rendered.refs.every((item: any) => !item.exists || item.hidden),
            "Mol* annotation nodes stayed renderable",
        );
        assert.strictEqual(rendered.eyeTitle, "Show annotation", "panel did not consume Python's hidden summary");

        console.log("[E2E scene-object-panel-roundtrip] section setup");
        await page.evaluate(async () => {
            const controller = (window as any).__controller;
            await controller.handleMessage({
                op: "set_sections",
                sections: [{ tag: "cut", point: [0.1, 0.2, 0.3], normal: [1, 0, 0], invert: false }],
            });
            await controller.handleMessage({
                op: "set_section_summaries",
                sections: [{ tag: "cut", owner: "topomt", point: [1, 2, 3], unit: "angstrom", normal: [1, 0, 0], invert: false, hidden: false }],
                active_selection_count: 1,
                system_loaded: true,
            });
        });
        await page.locator('[data-molsysviewer-group-panel-tab="viewport"]').click();
        const pointInputs = [0, 1, 2].map(axis => page.locator(`[data-molsysviewer-section-point-${axis}="cut"]`));
        await pointInputs[0].fill("0.4");
        await pointInputs[1].fill("0.5");
        await pointInputs[2].fill("0.6");
        await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur());
        console.log("[E2E scene-object-panel-roundtrip] section point edited");
        const moveAction = await page.evaluate(() =>
            [...((window as any).__messages || [])].reverse().find((message: any) =>
                message.event === "interaction_context_action"
                && message.action === "set_section_point"
            )
        );
        assert.deepStrictEqual(moveAction.point, { magnitude: [0.4, 0.5, 0.6], unit: "angstrom" });
        const coalescingEvents = await page.evaluate(() =>
            ((window as any).__messages || [])
                .filter((message: any) => message.event === "scene_history_coalescing_begin" || message.event === "scene_history_coalescing_end")
                .map((message: any) => message.event)
        );
        assert.deepStrictEqual(coalescingEvents.slice(-2), [
            "scene_history_coalescing_begin", "scene_history_coalescing_end",
        ]);

        const movePython = spawnSync(
            process.env.PYTHON || "python",
            [resolve(__dirname, "scene-object-panel-bridge.py")],
            { input: JSON.stringify(moveAction), encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
        );
        assert.strictEqual(movePython.status, 0, movePython.stderr || movePython.stdout);
        const movedBackend = JSON.parse(movePython.stdout);
        assert.ok(
            movedBackend.section_point_nm.every((value: number, index: number) =>
                Math.abs(value - [0.04, 0.05, 0.06][index]) < 1e-12
            ),
            "Python did not convert the displayed angstrom point to internal nanometers",
        );
        console.log("[E2E scene-object-panel-roundtrip] Python accepted section move");
        const movedClip = await page.evaluate(async messages => {
            const controller = (window as any).__controller;
            for (const message of messages) await controller.handleMessage(message);
            const objects = controller.plugin.managers.structure.component.state.options.clipObjects?.objects ?? [];
            return objects.map((item: any) => Array.from(item.position as ArrayLike<number>));
        }, movedBackend.messages);
        assert.ok(
            movedClip.length === 1 && movedClip[0].every((value: number, index: number) =>
                Math.abs(value - [0.4, 0.5, 0.6][index]) < 1e-6
            ),
            "moving through the panel did not move Mol* clipping",
        );

        console.log("[E2E scene-object-panel-roundtrip] section moved in Mol*");
        await page.locator('[data-molsysviewer-section-delete="cut"]').click();
        const deleteAction = await page.evaluate(() =>
            [...((window as any).__messages || [])].reverse().find((message: any) =>
                message.event === "interaction_context_action"
                && message.action === "remove_section"
            )
        );
        const deletePython = spawnSync(
            process.env.PYTHON || "python",
            [resolve(__dirname, "scene-object-panel-bridge.py")],
            { input: JSON.stringify(deleteAction), encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
        );
        assert.strictEqual(deletePython.status, 0, deletePython.stderr || deletePython.stdout);
        const deletedBackend = JSON.parse(deletePython.stdout);
        assert.strictEqual(deletedBackend.section_count, 0);
        console.log("[E2E scene-object-panel-roundtrip] Python deleted section");
        const remainingClips = await page.evaluate(async messages => {
            const controller = (window as any).__controller;
            for (const message of messages) await controller.handleMessage(message);
            return controller.plugin.managers.structure.component.state.options.clipObjects?.objects.length ?? 0;
        }, deletedBackend.messages);
        assert.strictEqual(remainingClips, 0, "deleting through the panel left Mol* clipping active");

        console.log("[E2E scene-object-panel-roundtrip] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
