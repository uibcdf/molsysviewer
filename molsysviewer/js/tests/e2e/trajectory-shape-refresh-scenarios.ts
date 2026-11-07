import assert from "node:assert/strict";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";

/** Real public Python shapes and native Mol* meshes, with only clear timing held. */
export async function checkTrajectoryShapeRefresh(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "studio-usability-bridge.py"), resolve(dir, "../../../.."));
    try {
        const fixture = await bridge.request([], "trajectory-shapes");
        await page.goto("about:blank");
        await page.setContent('<div id="root" style="width:850px;height:600px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async messages => {
            const w = window as any;
            const c = w.__shapeRefreshController = await w.Harness.createController("root");
            w.__shapeRefreshMessages = messages;
            w.__shapeRefreshLate = messages.find((message: any) => message.op === "add_sphere" && message.options?.tag === "refresh-late");
            for (const message of messages) if (message !== w.__shapeRefreshLate) await c.handleMessage(message, { throwOnError: true });
            const mesh = (tag: string, owner = c) => {
                const refs = owner.state.tagIndex.get(`shape\u0000${tag}`) ?? new Set();
                const shapes: any[] = [];
                for (const ref of refs) {
                    const repr = owner.plugin.state.data.cells.get(ref)?.obj?.data?.repr;
                    for (const loci of repr?.getAllLoci?.() ?? []) {
                        const geometry = loci.shape?.geometry;
                        if (geometry?.kind !== "mesh") continue;
                        const lower = [Infinity, Infinity, Infinity], upper = [-Infinity, -Infinity, -Infinity];
                        for (let i = 0; i < geometry.vertexCount; i++) for (let axis = 0; axis < 3; axis++) {
                            const value = geometry.vertexBuffer.ref.value[i * 3 + axis];
                            lower[axis] = Math.min(lower[axis], value); upper[axis] = Math.max(upper[axis], value);
                        }
                        shapes.push({ center: lower.map((value, axis) => (value + upper[axis]) / 2),
                            vertexCount: geometry.vertexCount,
                            visible: repr.renderObjects.length > 0 && repr.renderObjects.every((object: any) => object.state.visible) });
                    }
                }
                return shapes;
            };
            w.__shapeRefreshMesh = mesh;
            w.__shapeRefreshRead = () => {
                const structure = c.plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
                const conf = structure?.model.atomicConformation;
                return { frame: c.trajectory.getTrajectoryState().currentFrame,
                    model: conf ? [conf.x[0], conf.y[0], conf.z[0]] : null,
                    point: mesh("refresh-point"), atoms: mesh("refresh-atoms"), late: mesh("refresh-late") };
            };
            w.__shapeRefreshDrawCount = 0;
            let replay = true;
            w.__shapeRefreshDraws = c.plugin.canvas3d.didDraw.subscribe(() => {
                if (replay) return;
                w.__shapeRefreshDrawCount++;
                w.__shapeRefreshDrawn = w.__shapeRefreshRead();
            });
            replay = false;
            const clear = c.shapes.context.clearByTag;
            let held = false;
            c.shapes.context.clearByTag = async (tag: string) => {
                if (tag === "refresh-point" && !held) {
                    held = true;
                    await new Promise<void>(release => { w.__shapeRefreshRelease = release; });
                }
                return clear(tag);
            };
            w.__shapeRefreshRestoreClear = () => { c.shapes.context.clearByTag = clear; };
            await c.trajectory.setTrajectoryFrame(1);
            if (!w.__shapeRefreshRelease) throw new Error("The real first frame refresh did not reach its asynchronous clear");
            await c.trajectory.setTrajectoryFrame(2);
            w.__shapeRefreshRelease();
            // Old handlers expose only their busy flag; keep the same bounded
            // semantic completion observation for the failing-before control.
        }, fixture.initial_messages);
        await page.waitForFunction(() => !(window as any).__shapeRefreshController.shapes.frameUpdateInProgress);
        const drawn = async () => {
            const before = await page.evaluate(() => {
                const w = window as any, count = w.__shapeRefreshDrawCount;
                w.__shapeRefreshController.plugin.canvas3d.requestDraw();
                return count;
            });
            await page.waitForFunction(before => (window as any).__shapeRefreshDrawCount > before, before);
            return page.evaluate(() => (window as any).__shapeRefreshDrawn);
        };
        const compare = (shapes: any[], center: number[]) => {
            assert.equal(shapes.length, 1, JSON.stringify(shapes));
            assert.ok(shapes[0].visible && shapes[0].vertexCount > 0);
            shapes[0].center.forEach((value: number, axis: number) => assert.ok(Math.abs(value - center[axis]) < 2e-5,
                `Native sphere center ${JSON.stringify(shapes[0].center)} differs from frame-2 oracle ${JSON.stringify(center)}`));
        };
        const overlap = await drawn();
        assert.equal(overlap.frame, 2);
        overlap.model.forEach((value: number, axis: number) => assert.ok(Math.abs(value - fixture.oracle.point[2][axis]) < 2e-5));
        compare(overlap.point, fixture.oracle.point[2]);
        compare(overlap.atoms, fixture.oracle.atoms[2]);
        // Initial creation after navigating must use frame 2 immediately.
        const late = await page.evaluate(async () => {
            const w = window as any;
            w.__shapeRefreshRestoreClear();
            w.__shapeRefreshDraws.unsubscribe();
            w.__shapeRefreshController.dispose();
            document.getElementById("root")!.replaceChildren();
            const c = w.__shapeRefreshController = await w.Harness.createController("root");
            for (const message of w.__shapeRefreshMessages) if (message.op !== "add_sphere") {
                await c.handleMessage(message, { throwOnError: true });
            }
            await c.trajectory.setTrajectoryFrame(2);
            await c.handleMessage(w.__shapeRefreshLate, { throwOnError: true });
            return new Promise<any[]>((resolve, reject) => {
                let replay = true;
                const timer = setTimeout(() => { subscription.unsubscribe(); reject(new Error("Late shape draw timed out")); }, 15000);
                const subscription = c.plugin.canvas3d.didDraw.subscribe(() => {
                    if (replay) return;
                    clearTimeout(timer); subscription.unsubscribe();
                    resolve(w.__shapeRefreshMesh("refresh-late", c));
                });
                replay = false;
                c.plugin.canvas3d.requestDraw();
            });
        });
        compare(late, fixture.oracle.point[2]);
        console.log("[E2E shapes] overlapping native refreshes and late creation match the real pentalanine frame-2 meshes");
    } finally {
        await page.evaluate(() => {
            const w = window as any;
            w.__shapeRefreshRestoreClear?.();
            w.__shapeRefreshRelease?.();
            w.__shapeRefreshDraws?.unsubscribe();
            w.__shapeRefreshController?.dispose();
        }).catch(() => {});
        await bridge.close();
    }
}
