import assert from "node:assert";
import { execFile } from "node:child_process";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const bridge = resolve(__dirname, "measures-subpanel-bridge.py");
const PDB_TEXT = `
ATOM      1  H1  ACE A   1      10.000  10.000  10.000  1.00 20.00           H
ATOM      2  C   ACE A   1      11.090  10.000  10.000  1.00 20.00           C
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

async function run() {
    console.log("[E2E measures-subpanel] preparing Python fixture");
    const initial = await runBridge();
    console.log("[E2E measures-subpanel] launching Chromium");
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
        console.log("[E2E measures-subpanel] loading Mol* scene");
        await page.evaluate(async pdb => {
            const controller = await (window as any).Harness.createController("root");
            (window as any).__controller = controller;
            await controller.handleMessage({
                op: "load_structure_from_string", data: pdb, format: "pdb", label: "measures-panel",
            });
        }, PDB_TEXT);
        await applyMessages(page, initial.initial_messages);
        console.log("[E2E measures-subpanel] checking panel and frame value");

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="measures"]').click();
        const value = page.locator('[data-molsysviewer-measurement-value="d1"]');
        assert.strictEqual(await value.innerText(), "1.09 Å");

        await applyMessages(page, initial.frame_messages);
        assert.strictEqual(await value.innerText(), "2.18 Å", "the row kept the frame-zero value");

        await page.locator('[data-molsysviewer-measurement-visibility="d1"]').click();
        await page.locator('[data-molsysviewer-measurement-delete="d1"]').click();
        const actions = await page.evaluate(() => ((window as any).__messages || []).filter((message: any) =>
            message.event === "interaction_context_action"
            && ["toggle_measurement_visibility", "delete_measurement"].includes(message.action)
        ));
        assert.deepStrictEqual(actions.map((item: any) => item.action), [
            "toggle_measurement_visibility", "delete_measurement",
        ]);

        const lifecycleEvents = [
            actions[0],
            { ...actions[0] }, // show again so delete + undo must restore a rendered node
            actions[1],
        ];
        const lifecycle = await runBridge(lifecycleEvents);
        console.log("[E2E measures-subpanel] replaying Python lifecycle messages");
        assert.deepStrictEqual(lifecycle.states, [
            { contains: true, visible: false },
            { contains: true, visible: true },
            { contains: false, visible: null },
            { contains: true, visible: true },
        ]);

        await applyMessages(page, lifecycle.message_batches[0]);
        let refs = await page.evaluate(() =>
            (window as any).Harness.inspectTaggedRefs((window as any).__controller, "measurement", "d1")
        );
        assert.ok(refs.length > 0 && refs.every((item: any) => !item.exists), "hide left an existing measurement node in Mol*");

        await applyMessages(page, lifecycle.message_batches[1]);
        refs = await page.evaluate(() =>
            (window as any).Harness.inspectTaggedRefs((window as any).__controller, "measurement", "d1")
        );
        assert.ok(refs.some((item: any) => item.exists), "show did not rebuild the native measurement node");

        await applyMessages(page, lifecycle.message_batches[2]);
        refs = await page.evaluate(() =>
            (window as any).Harness.inspectTaggedRefs((window as any).__controller, "measurement", "d1")
        );
        assert.ok(refs.every((item: any) => !item.exists), "delete left existing measurement nodes in Mol*");

        await applyMessages(page, lifecycle.message_batches[3]);
        refs = await page.evaluate(() =>
            (window as any).Harness.inspectTaggedRefs((window as any).__controller, "measurement", "d1")
        );
        assert.ok(refs.some((item: any) => item.exists), "undo did not restore the measurement node");
        console.log("[E2E measures-subpanel] passed");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
