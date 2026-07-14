import assert from "node:assert";
import { execFile } from "node:child_process";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const bridge = resolve(__dirname, "shapes-subpanel-bridge.py");
const PDB_TEXT = `
ATOM      1  N   MET A   1       0.000   0.000   0.000  1.00 20.00           N
ATOM      2  CA  MET A   1       1.500   0.000   0.000  1.00 20.00           C
END
`;

function runBridge(input?: unknown): Promise<any> {
    return new Promise((resolveBridge, rejectBridge) => {
        const child = execFile(
            process.env.PYTHON || "python",
            [bridge],
            { encoding: "utf8", cwd: resolve(__dirname, "../../../.."), maxBuffer: 8 * 1024 * 1024 },
            (error, stdout, stderr) => {
                if (error) return rejectBridge(new Error(stderr || stdout || String(error)));
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

async function renderedShape(page: any, tag: string) {
    return page.evaluate(shapeTag => {
        const controller = (window as any).__controller;
        return (window as any).Harness.inspectTaggedRefs(controller, "shape", shapeTag).map((item: any) => {
            const cell = controller.plugin.state.data.cells.get(item.ref);
            return { ...item, color: cell?.transform?.params?.color };
        });
    }, tag);
}

async function run() {
    console.log("[E2E shapes-subpanel] preparing Python fixture");
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
            await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "shapes-panel" });
        }, PDB_TEXT);
        await applyMessages(page, initial.initial_messages);

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="shapes"]').click();
        assert.strictEqual(await page.locator('[data-molsysviewer-shape-no-style="alpha-set"]').count(), 1);
        assert.strictEqual(await page.locator('[data-molsysviewer-shape-style="alpha-set"] input').count(), 0);

        const color = page.locator('[data-molsysviewer-shape-color="site"]');
        await color.fill("#336699");
        await page.locator('[data-molsysviewer-shape-visibility="site"]').click();
        await page.locator('[data-molsysviewer-shape-delete="site"]').click();

        const events = await page.evaluate(() => ((window as any).__messages || []).filter((message: any) =>
            message.event === "scene_history_coalescing_begin"
            || message.event === "scene_history_coalescing_end"
            || (message.event === "interaction_context_action"
                && ["set_shape_color", "toggle_shape_visibility", "delete_shape"].includes(message.action))
        ));
        events.push({ event: "scene_history_undo" });
        assert.deepStrictEqual(events.map((event: any) => event.action || event.event), [
            "scene_history_coalescing_begin", "set_shape_color", "scene_history_coalescing_end",
            "toggle_shape_visibility", "delete_shape", "scene_history_undo",
        ]);

        const lifecycle = await runBridge(events);
        assert.strictEqual(lifecycle.states[1].color, "#336699", "Python did not receive the colour");
        assert.strictEqual(lifecycle.states[3].visible, false, "Python visibility stayed true");
        assert.strictEqual(lifecycle.states[4].exists, false, "Python did not delete the shape");
        assert.strictEqual(lifecycle.states[5].exists, true, "undo did not restore the shape");

        await applyMessages(page, lifecycle.message_batches[1]);
        const recolored = await renderedShape(page, "site");
        assert.ok(recolored.some((item: any) => item.exists && item.color === 0x336699), "Mol* kept the old sphere colour");

        await applyMessages(page, lifecycle.message_batches[3]);
        const hidden = await renderedShape(page, "site");
        assert.ok(hidden.length > 0 && hidden.every((item: any) => !item.exists || item.hidden), "Mol* shape stayed renderable");

        await applyMessages(page, lifecycle.message_batches[4]);
        assert.ok((await renderedShape(page, "site")).every((item: any) => !item.exists), "delete left a Mol* node");
        await applyMessages(page, lifecycle.message_batches[5]);
        assert.ok((await renderedShape(page, "site")).some((item: any) => item.exists), "undo did not restore the Mol* node");
        console.log("[E2E shapes-subpanel] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
