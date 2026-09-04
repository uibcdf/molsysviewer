import assert from "node:assert";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

const PDB_TEXT = `
ATOM      1  N   MET A   1      -4.104   0.207   0.551  1.00 20.00           N
ATOM      2  CA  MET A   1      -2.560   0.329   0.276  1.00 20.00           C
ATOM      3  C   MET A   1      -1.189  -0.956   0.001  1.00 20.00           C
ATOM      4  O   MET A   1      -0.589  -1.935   0.353  1.00 20.00           O
ATOM      5  N   ALA A   2       0.400  -0.900  -0.400  1.00 20.00           N
ATOM      6  CA  ALA A   2       1.100   0.650  -0.100  1.00 20.00           C
ATOM      7  C   ALA A   2       2.300   0.900  -1.200  1.00 20.00           C
ATOM      8  O   ALA A   2       3.100  -0.080  -1.700  1.00 20.00           O
END
`;

async function run() {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.setContent('<div id="root" style="width:1000px;height:700px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });

        const result = await page.evaluate(async pdb => {
            const harness = (window as any).Harness;
            const controller = await harness.createController("root");
            await controller.handleMessage({
                op: "load_structure_from_string", data: pdb, format: "pdb", label: "remote-input",
            });
            await controller.handleMessage({ op: "set_whole_representation", representation: "spacefill" });
            await controller.resetView();
            await new Promise(resolveWait => setTimeout(resolveWait, 500));

            const canvas = document.querySelector("#root canvas") as HTMLCanvasElement | null;
            if (!canvas) throw new Error("Mol* did not create its canvas");
            const gl = canvas.getContext("webgl2");
            const extension = gl?.getExtension("WEBGL_debug_renderer_info");
            const renderer = gl
                ? String(gl.getParameter(extension ? (extension as any).UNMASKED_RENDERER_WEBGL : gl.RENDERER))
                : "";
            const adapter = new harness.RemoteInputAdapter(canvas, {
                viewerId: "view-a", sessionId: "session-a", endpointId: "qt-client:a",
            });
            let sequence = 0;
            const send = (phase: string, x: number, y: number, buttons: number) => adapter.handle({
                protocolVersion: 1,
                viewerId: "view-a",
                sessionId: "session-a",
                endpointId: "qt-client:a",
                sequence: ++sequence,
                timestampMs: performance.now(),
                kind: "pointer",
                viewport: {
                    width: canvas.clientWidth,
                    height: canvas.clientHeight,
                    devicePixelRatio: window.devicePixelRatio,
                },
                payload: {
                    phase, pointerType: "mouse", pointerId: 1,
                    x, y, button: phase === "move" ? -1 : 0, buttons, modifiers: {},
                },
            });

            const before = controller.getCameraSnapshot();
            send("down", 0.5, 0.5, 1);
            for (let step = 1; step <= 12; step += 1) {
                send("move", 0.5 + step * 0.015, 0.5 + step * 0.006, 1);
            }
            send("up", 0.68, 0.572, 0);
            await new Promise(resolveWait => setTimeout(resolveWait, 400));
            const after = controller.getCameraSnapshot();

            let picked = null;
            for (const y of [0.4, 0.5, 0.6]) {
                for (const x of [0.35, 0.45, 0.5, 0.55, 0.65]) {
                    send("down", x, y, 1);
                    send("up", x, y, 0);
                    await new Promise(resolveWait => setTimeout(resolveWait, 80));
                    picked = (window as any).__messages.find(
                        (message: any) => message?.event === "interaction_click" && message?.kind !== "empty",
                    ) ?? null;
                    if (picked) break;
                }
                if (picked) break;
            }
            const duplicate = adapter.handle({
                protocolVersion: 1,
                viewerId: "view-a",
                sessionId: "session-a",
                endpointId: "qt-client:a",
                sequence,
                timestampMs: performance.now(),
                kind: "key",
                viewport: { width: 1000, height: 700, devicePixelRatio: window.devicePixelRatio },
                payload: { phase: "down", code: "KeyR", repeat: false, modifiers: {} },
            });
            return {
                renderer,
                webgl2: !!gl,
                cameraChanged: JSON.stringify(before) !== JSON.stringify(after),
                picked,
                duplicate,
            };
        }, PDB_TEXT);

        assert.ok(result.webgl2, "remote input test has no WebGL2");
        assert.ok(result.cameraChanged, "remote drag did not change the real Mol* camera");
        assert.ok(result.picked, "remote click did not produce a real Mol* pick");
        assert.strictEqual(result.duplicate.status, "rejected");
        assert.strictEqual(result.duplicate.reason, "stale-sequence");
        assert.deepStrictEqual(errors, []);
        console.log(`[E2E remote-input] renderer=${result.renderer}`);
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
