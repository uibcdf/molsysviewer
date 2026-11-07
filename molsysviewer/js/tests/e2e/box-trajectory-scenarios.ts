import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import type { Page } from "playwright";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";

/** An actual exported HTML has no Python authority to refresh a static cage. */
export async function checkBoxTrajectory(page: Page, dir: string) {
    await withFixtureWorkspace("box-trajectory", async workspace => {
        const command = spawnSync(process.env.PYTHON || "python", [resolve(dir, "box-trajectory-bridge.py"), workspace], {
            cwd: resolve(dir, "../../../.."), env: fixtureEnvironment(workspace), encoding: "utf8", maxBuffer: 1024 * 1024,
        });
        assert.equal(command.status, 0, command.stderr);
        const fixture = JSON.parse(await readFile(resolve(workspace, "fixture.json"), "utf8"));
        await page.goto(pathToFileURL(fixture.page).href);
        await page.waitForFunction(() => !!(window as any).__molsysviewerDocsController?.plugin.canvas3d);
        await page.waitForFunction(() => (window as any).__molsysviewerDocsController.trajectory.getTrajectoryState().frameCount === 3);
        await page.evaluate(() => {
            const w = window as any, c = w.__molsysviewerDocsController;
            let replay = true;
            w.__boxTrajectoryCount = 0;
            w.__boxTrajectorySubscription = c.plugin.canvas3d.didDraw.subscribe(() => {
                if (replay) return;
                const refs = c.state.tagIndex.get("shape\u0000__msv_box") ?? new Set();
                const boxes: any[] = [];
                for (const ref of refs) {
                    const repr = c.plugin.state.data.cells.get(ref)?.obj?.data?.repr;
                    if (!repr) continue;
                    const shape = repr.getAllLoci().find((loci: any) => loci.shape?.geometry.kind === "mesh")?.shape;
                    const geometry = shape?.geometry;
                    const bounds = Array.from({ length: 12 }, () => ({ lower: [Infinity, Infinity, Infinity], upper: [-Infinity, -Infinity, -Infinity] }));
                    if (geometry) for (let vertex = 0; vertex < geometry.vertexCount; vertex++) {
                        const group = geometry.groupBuffer.ref.value[vertex];
                        if (!bounds[group]) continue;
                        for (let axis = 0; axis < 3; axis++) {
                            const value = geometry.vertexBuffer.ref.value[3 * vertex + axis];
                            bounds[group].lower[axis] = Math.min(bounds[group].lower[axis], value);
                            bounds[group].upper[axis] = Math.max(bounds[group].upper[axis], value);
                        }
                    }
                    boxes.push({ ref, links: shape?.sourceData.links,
                        meshCenters: bounds.map(group => group.lower.map((value, axis) => (value + group.upper[axis]) / 2)),
                        vertices: shape?.geometry.vertexCount,
                        visible: repr.renderObjects.length > 0 && repr.renderObjects.every((object: any) => object.state.visible),
                        alpha: repr.state.alphaFactor });
                }
                w.__boxTrajectoryDraw = { count: ++w.__boxTrajectoryCount,
                    frame: c.trajectory.getTrajectoryState().currentFrame, boxes };
            });
            replay = false;
        });
        try {
            for (const frame of [0, 1, 2, 0]) {
                const before = await page.evaluate(async frame => {
                    const w = window as any, c = w.__molsysviewerDocsController;
                    await c.trajectory.setTrajectoryFrame(frame);
                    // This wait is supplementary for the new handler; the old
                    // runtime still reaches its real failing geometry assertion.
                    if (c.boxDisplay?.whenSettled) await c.boxDisplay.whenSettled();
                    const count = w.__boxTrajectoryCount;
                    c.plugin.canvas3d.requestDraw();
                    return count;
                }, frame);
                await page.waitForFunction(before => (window as any).__boxTrajectoryCount > before, before);
                const actual = await page.evaluate(() => (window as any).__boxTrajectoryDraw);
                assert.equal(actual.frame, frame);
                assert.equal(actual.boxes.length, 1);
                const box = actual.boxes[0];
                assert.ok(box.visible && box.vertices > 0);
                assert.ok(Math.abs(box.alpha - .7) < 1e-6);
                assert.equal(box.links.length, 12);
                const expected: number[][][] = [];
                const rows: number[][] = fixture.boxes_angstrom[frame];
                // Each basis direction connects the four other-axis corners.
                for (let axis = 0; axis < 3; axis++) {
                    const other = [0, 1, 2].filter(index => index !== axis);
                    for (let bits = 0; bits < 4; bits++) {
                        const start = [0, 1, 2].map(dimension => other.reduce((sum, index, bit) =>
                            sum + ((bits >> bit) & 1) * rows[index][dimension], 0));
                        expected.push([start, start.map((value, dimension) => value + rows[axis][dimension])]);
                    }
                }
                const key = (pair: number[][]) => JSON.stringify(pair.map(point => point.map(value => Math.round(value * 1e5) / 1e5)));
                assert.deepEqual(box.links.map((link: any) => key([link.start, link.end])).sort(), expected.map(key).sort(),
                    `Exported box geometry must follow actual frame ${frame}, including rotated row vectors`);
                assert.ok(box.links.every((link: any) => link.color === 0xff0000 && Math.abs(link.radius - 1.25) < 1e-6));
                box.meshCenters.forEach((center: number[], group: number) => center.forEach((value, axis) =>
                    assert.ok(Math.abs(value - (box.links[group].start[axis] + box.links[group].end[axis]) / 2) < 2e-4,
                        "The actual mesh vertices must match the native link endpoints on this draw")));
            }
            console.log("[E2E box] exported real pentalanine follows orthogonal, rotated and triclinic cells without Python");
        } finally {
            await page.evaluate(() => (window as any).__boxTrajectorySubscription?.unsubscribe()).catch(() => {});
        }
    });
    await checkWidgetBoxTrajectory(page, dir);
}

/** Native-buffer widget and actual popup; Python owns definitions and editing. */
async function checkWidgetBoxTrajectory(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "box-trajectory-bridge.py"), resolve(dir, "../../../.."));
    let popup: Page | undefined, releaseFixture: (() => Promise<void>) | undefined;
    try {
        releaseFixture = await mountCanvasPopupFixture(page, bridge);
        await captureCanvasPopupControllers(page);
        const openPopup = async () => {
            const opened = page.waitForEvent("popup");
            await page.getByTitle("Open popup", { exact: true }).click();
            const peer = await opened;
            await peer.waitForFunction(() => !!(window as any).__mirrorController);
            await peer.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
            return peer;
        };
        popup = await openPopup();
        const command = async (action: string, index?: number) => {
            await page.evaluate(message => (window as any).__popupWidgetModel.send(message), { box_fixture: action, index });
            await page.evaluate(() => (window as any).__popupFixtureDrain());
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
        };
        const boxes = async (frame: number, cell: number | null, scale = 1,
            style = { color: 0xff0000, radius: 1.25, alpha: .7 }) => {
            for (const endpoint of [page, popup!]) {
                await endpoint.waitForFunction(({ frame, cell }) => {
                    const c = (window as any).__mirrorController;
                    const refs = c.state.tagIndex.get("shape\u0000__msv_box") ?? new Set();
                    return c.trajectory.getTrajectoryState().currentFrame === frame
                        && c.boxDisplay.isFrameReady(frame)
                        && (cell === null ? refs.size === 0 : c.boxDisplay.structureIndex === cell && refs.size === 1);
                }, { frame, cell });
                const actual = await endpoint.evaluate(() => new Promise<any[]>((resolve, reject) => {
                    const c = (window as any).__mirrorController, canvas = c.plugin.canvas3d;
                    let replay = true;
                    const timer = setTimeout(() => { subscription.unsubscribe(); reject(new Error("Box draw timed out")); }, 15000);
                    const subscription = canvas.didDraw.subscribe(() => {
                        if (replay) return;
                        clearTimeout(timer); subscription.unsubscribe();
                        const refs = c.state.tagIndex.get("shape\u0000__msv_box") ?? new Set();
                        const boxes: any[] = [];
                        for (const ref of refs) {
                            const repr = c.plugin.state.data.cells.get(ref)?.obj?.data?.repr;
                            const shape = repr?.getAllLoci().find((loci: any) => loci.shape?.geometry.kind === "mesh")?.shape;
                            boxes.push({ links: shape?.sourceData.links, vertices: shape?.geometry.vertexCount, alpha: repr?.state.alphaFactor,
                                visible: repr?.renderObjects.length > 0 && repr.renderObjects.every((object: any) => object.state.visible) });
                        }
                        resolve(boxes);
                    });
                    replay = false; canvas.requestDraw();
                }));
                if (cell === null) { assert.deepEqual(actual, []); continue; }
                assert.equal(actual.length, 1);
                assert.ok(actual[0].visible && actual[0].vertices > 0);
                const rows = [
                    [[30, 0, 0], [0, 40, 0], [0, 0, 50]],
                    [[0, 40, 0], [-50, 0, 0], [0, 0, 60]],
                    [[40, 10, 0], [10, 50, 0], [10, 10, 60]],
                ][cell].map(row => row.map(value => value * scale));
                const vectors = actual[0].links.map((link: any) => link.end.map((value: number, axis: number) => value - link.start[axis]));
                for (const row of rows) assert.equal(vectors.filter((vector: number[]) =>
                    vector.every((value, axis) => Math.abs(value - row[axis]) < 1e-5)).length, 4);
                assert.ok(Math.abs(actual[0].alpha - style.alpha) < 1e-6);
                assert.ok(actual[0].links.every((link: any) => link.color === style.color && Math.abs(link.radius - style.radius) < 1e-6));
            }
        };
        await boxes(0, 0);
        await popup.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await boxes(1, 1);
        await command("show", 2);
        await boxes(1, 2);
        console.log("[E2E box] widget/popup navigation and explicit cell received");
        // Bootstrap must keep the selected cell, even when it differs from the
        // molecular frame and the Python snapshot contains a navigation op.
        await popup.close();
        popup = await openPopup();
        await boxes(1, 2);
        await command("frame", 1);
        await boxes(1, 1);
        await page.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await boxes(2, 2);
        await popup.locator('[data-molsysviewer-trajectory-step="previous"]').click();
        await boxes(1, 1);
        await command("replace");
        await boxes(1, 1, 2);
        await command("style");
        await boxes(1, 0, 2, { color: 0x0000ff, radius: .8, alpha: .4 });
        console.log("[E2E box] rebootstrap, same-frame navigation and replacement received");
        await command("hide");
        await boxes(1, null);
        await popup.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await boxes(2, null);
        await command("show", 0);
        await boxes(2, 0, 2);
        await command("clear");
        await boxes(2, null);
        console.log("[E2E box] native widget/popup converge across navigation, explicit cells, rebootstrap, cell edits, hide and clear");
    } finally {
        await popup?.close().catch(() => {});
        await releaseFixture?.();
        await bridge.close();
    }
}
