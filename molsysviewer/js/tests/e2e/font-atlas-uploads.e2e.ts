import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace, fixtureEnvironment } from "./fixture-workspace";

async function run() {
    const directory = dirname(fileURLToPath(import.meta.url)), browser = await chromium.launch();
    try {
        const page = await browser.newPage(), errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        await page.setContent('<html><body><div id="root" style="width:800px;height:600px"></div></body></html>');
        await page.addScriptTag({ path: resolve(directory, "harness.bundle.js") });
        const lifecycle = await page.evaluate(() => (window as any).Harness.checkFontAtlasResourceLifecycle());
        assert.equal(lifecycle.changes.length, 8);
        console.log("[E2E font atlas] actual native glyphs, GPU pixels and lifecycle", lifecycle);
        await withFixtureWorkspace("font-atlas", async workspace => {
            const fixture = JSON.parse(execFileSync(process.env.PYTHON || "python", [resolve(directory, "font-atlas-bridge.py")],
                { cwd: resolve(directory, "../../../.."), env: fixtureEnvironment(workspace), encoding: "utf8" }));
            const observed = await page.evaluate(async fixture => {
                const controller = await (window as any).Harness.createController("root");
                try {
                    for (const message of fixture.messages) await controller.handleMessage(message);
                    const canvas = controller.plugin.canvas3d, gl = canvas.webgl.gl;
                    // Receive every label first: newly encountered numeric
                    // glyphs are legitimate uploads, not the regression.
                    for (const frame of [1, 2, 0]) await controller.trajectory.setTrajectoryFrame(frame);
                    let uploads = 0; const upload = gl.texImage2D;
                    const images = new Set();
                    for (const cell of controller.plugin.state.data.cells.values()) {
                        for (const object of cell.obj?.data?.repr?.renderObjects ?? []) {
                            if (object.values.tFont) images.add(object.values.tFont.ref.value.array);
                        }
                    }
                    gl.texImage2D = function (...args: any[]) { if (images.has(args[8])) uploads++; return upload.apply(this, args); };
                    const frames = [];
                    for (const frame of [1, 2, 0, 1]) {
                        await controller.trajectory.setTrajectoryFrame(frame);
                        await new Promise<void>(resolve => {
                            let replay = true;
                            const subscription = canvas.didDraw.subscribe(() => {
                                if (replay) return;
                                subscription.unsubscribe(); resolve();
                            }); replay = false; canvas.requestDraw();
                        });
                        frames.push({ frame, distance: (window as any).Harness.inspectMeasurementGeometry(controller, "font-distance") });
                    }
                    gl.texImage2D = upload;
                    return { uploads, frames };
                } finally { controller.dispose(); }
            }, fixture);
            assert.equal(observed.uploads, 0, "Native coordinate updates with already mapped glyphs must not reupload the atlas.");
            assert.equal(observed.frames.length, 4);
            assert.ok(observed.frames.every((frame: any) => frame.distance.geometry.some((item: any) => item.kind === "text")));
            for (const frame of observed.frames) {
                const line = frame.distance.geometry.find((item: any) => item.points?.length === 2);
                assert.ok(line);
                line.points.forEach((point: number[], index: number) => point.forEach((value, axis) =>
                    assert.ok(Math.abs(value - fixture.coordinates[frame.frame][index][axis]) < 2e-4,
                        "Measurement endpoints must follow the actual molecular frame.")));
            }
        });
        assert.deepEqual(errors, []);
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
