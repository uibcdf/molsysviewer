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

        console.log("[E2E scene-object-panel-roundtrip] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
