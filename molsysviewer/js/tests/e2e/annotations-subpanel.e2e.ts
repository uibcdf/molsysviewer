import assert from "node:assert";
import { execFile } from "node:child_process";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const bridge = resolve(__dirname, "annotations-subpanel-bridge.py");
const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

function runBridge(input?: unknown): Promise<any> {
    return new Promise((resolveBridge, rejectBridge) => {
        const child = execFile(
            process.env.PYTHON || "python",
            [bridge],
            { encoding: "utf8", cwd: resolve(__dirname, "../../../.."), maxBuffer: 8 * 1024 * 1024 },
            (error, stdout, stderr) => {
                if (error) {
                    rejectBridge(new Error(stderr || stdout || String(error)));
                    return;
                }
                resolveBridge(JSON.parse(stdout));
            },
        );
        child.stdin?.end(input === undefined ? "" : JSON.stringify(input));
    });
}

async function applyMessages(page: any, messages: unknown[]) {
    await page.evaluate(async payload => {
        const controller = (window as any).__controller;
        for (const message of payload) await controller.handleMessage(message);
    }, messages);
}

async function renderedLabelText(page: any, tag: string): Promise<string | null> {
    return page.evaluate(annotationTag => {
        const controller = (window as any).__controller;
        const refs = (window as any).Harness.inspectTaggedRefs(controller, "annotation", annotationTag);
        for (const item of refs) {
            const cell = controller.plugin.state.data.cells.get(item.ref);
            const text = cell?.transform?.params?.customText;
            if (typeof text === "string") return text;
        }
        return null;
    }, tag);
}

async function run() {
    console.log("[E2E annotations-subpanel] preparing Python fixture");
    const initial = await runBridge();
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
            await controller.handleMessage({
                op: "load_structure_from_string", data: pdb, format: "pdb", label: "annotations-panel",
            });
        }, PDB_TEXT);
        await applyMessages(page, initial.initial_messages);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="annotations"]').click();
        assert.strictEqual(
            await page.locator('[data-molsysviewer-annotation-text="note"]').innerText(),
            "Catalytic site",
        );
        assert.strictEqual(await renderedLabelText(page, "note"), "Catalytic site");

        await page.locator('[data-molsysviewer-annotation-text="note"]').click();
        const editor = page.locator('[data-molsysviewer-annotation-text-input="note"]');
        await editor.fill("Gate closed");
        await editor.press("Enter");
        await page.locator('[data-molsysviewer-annotation-visibility="note"]').click();

        const events = await page.evaluate(() => ((window as any).__messages || []).filter((message: any) =>
            message.event === "scene_history_coalescing_begin"
            || message.event === "scene_history_coalescing_end"
            || (message.event === "interaction_context_action"
                && ["set_annotation_text", "toggle_annotation_visibility"].includes(message.action))
        ));
        assert.deepStrictEqual(events.map((event: any) => event.event === "interaction_context_action" ? event.action : event.event), [
            "scene_history_coalescing_begin",
            "set_annotation_text",
            "scene_history_coalescing_end",
            "toggle_annotation_visibility",
        ]);

        const lifecycle = await runBridge(events);
        assert.deepStrictEqual(lifecycle.states.map((state: any) => state.undo_depth), [0, 1, 1, 2]);
        assert.strictEqual(lifecycle.states[1].text, "Gate closed", "Python did not receive the edited text");
        assert.strictEqual(lifecycle.states[3].visible, false, "Python visibility stayed true");

        await applyMessages(page, lifecycle.message_batches[1]);
        assert.strictEqual(
            await renderedLabelText(page, "note"),
            "Gate closed",
            "the Mol* label kept its old customText",
        );
        await applyMessages(page, lifecycle.message_batches[3]);
        const refs = await page.evaluate(() =>
            (window as any).Harness.inspectTaggedRefs((window as any).__controller, "annotation", "note")
        );
        assert.ok(refs.length > 0 && refs.every((item: any) => !item.exists || item.hidden), "hide left the label renderable");
        console.log("[E2E annotations-subpanel] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
