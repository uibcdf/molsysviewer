import assert from "node:assert";
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));
async function run() {
    const result = spawnSync(process.env.PYTHON || "python", [resolve(dir, "coordinate-edits-bridge.py")],
        { encoding: "utf8", cwd: resolve(dir, "../../../.."), maxBuffer: 16 * 1024 * 1024 });
    assert.equal(result.status, 0, result.stderr);
    const fixture = JSON.parse(result.stdout);
    const browser = await chromium.launch({ headless: true, executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"] } as any);
    const page = await browser.newPage();
    try {
        await page.setContent('<div id="root" style="width:800px;height:600px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { (window as any).__controller = await (window as any).Harness.createController("root"); });
        const apply = async (messages: unknown[]) => page.evaluate(async items => {
            for (const item of items) await (window as any).__controller.handleMessage(item);
        }, messages);
        const atom = async (frame: number) => page.evaluate(async index => {
            const controller = (window as any).__controller;
            await controller.trajectory.setTrajectoryFrame(index);
            const structure = controller.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data;
            assertStructure(structure);
            function assertStructure(value: any) { if (!value.units.length) throw new Error("No molecular structure rendered"); }
            const unit = structure.units[0], position = [0, 0, 0];
            const modelIndex = unit.model.atomicHierarchy.atomSourceIndex.toArray().indexOf(2);
            unit.conformation.position(modelIndex, position);
            return position;
        }, frame);
        const close = (actual: number[], expected: number[]) => actual.forEach((value, i) => assert.ok(Math.abs(value - expected[i] * 10) < 1e-4));
        await apply(fixture.initial);
        close(await atom(0), fixture.before[0][2]);
        await apply(fixture.stages[0].messages);
        close(await atom(0), fixture.before[0][2]);
        close(await atom(2), fixture.stages[0].after[2][2]);
        await apply(fixture.stages[1].messages);
        close(await atom(2), fixture.stages[1].after[2][2]);
        close(await atom(0), fixture.stages[1].after[0][2]);
        close(await atom(1), fixture.before[1][2]);
        const acknowledgments = await page.evaluate(() => ((window as any).__messages || []).filter((item: any) => item.event === "trajectory_frame_rendered"));
        assert.deepEqual(acknowledgments.map((item: any) => item.transaction_id), ["edit-0", "edit-1"]);
        for (const stage of fixture.box_stages) {
            await apply(stage.messages);
            for (let frame = 0; frame < 3; frame++) {
                const actual = await page.evaluate(async index => {
                    const c = (window as any).__controller;
                    await c.trajectory.setTrajectoryFrame(index);
                    const structure = c.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data;
                    const model = structure.units[0].model;
                    const cell = model._staticPropertyData.model_symmetry?.spacegroup.cell;
                    return { size: cell ? Array.from(cell.size) : null,
                        angles: cell ? Array.from(cell.anglesInRadians) : null,
                        boxShapes: (window as any).Harness.inspectTaggedRefs(c, "shape", "__msv_box").length };
                }, frame);
                // Mol*'s default nonperiodic symmetry may expose its placeholder
                // 1 Å cell. Removal must never retain the previous submitted cell.
                if (stage.cells === null) {
                    assert.ok(actual.size === null || actual.size.every((value: number) => value === 1));
                    assert.equal(actual.boxShapes, 0);
                } else {
                    const basis = stage.cells[frame] as number[][];
                    const lengths = basis.map(vector => Math.hypot(...vector));
                    close(actual.size as number[], lengths);
                    const angle = (a: number, b: number) => Math.acos(
                        basis[a].reduce((sum, value, i) => sum + value * basis[b][i], 0) / (lengths[a] * lengths[b]));
                    const expected = [angle(1, 2), angle(0, 2), angle(0, 1)];
                    (actual.angles as number[]).forEach((value, i) => assert.ok(Math.abs(value - expected[i]) < 1e-5));
                    assert.equal(actual.boxShapes, 1);
                }
                close(await atom(frame), fixture.stages[1].after[frame][2]);
            }
        }
        console.log("[E2E coordinate-edits] passed");
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
