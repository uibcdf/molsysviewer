import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import type { Locator, Page } from "playwright";

/** A real later didDraw subscriber moves the native camera before microtasks. */
export async function checkStudioCaptureInDraw(options: {
    page: Page; path: string;
    openWork(page: Page): Promise<Locator>;
    awaitResult(page: Page, action: string, before: number): Promise<any>;
}) {
    const { page, path, openWork, awaitResult } = options;
    const work = await openWork(page);
    await work.getByLabel("Work file format", { exact: true }).selectOption("state");
    await work.getByLabel("Path in Python session", { exact: true }).fill(path);
    const before = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
    await page.evaluate(() => {
        const w = window as any, c = w.__mirrorController, canvas = c.plugin.canvas3d;
        w.__studioCaptureDraw = { observers: canvas.didDraw.observers.length, requests: 0 };
        const request = canvas.requestDraw.bind(canvas);
        canvas.requestDraw = (...args: any[]) => { w.__studioCaptureDraw.requests++; return request(...args); };
        w.__studioReleaseCaptureDraw = () => {
            w.__studioCaptureDraw.late?.unsubscribe();
            canvas.requestDraw = request;
            c.plugin.animationLoop.start();
        };
        c.plugin.animationLoop.stop({ noDraw: true });
    });
    try {
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await page.waitForFunction(start => (window as any).__studioCaptureTransport.inbound.slice(start)
            .some((message: any) => message.op === "request_visual_state"), before);
        await page.waitForFunction(() => {
            const w = window as any, probe = w.__studioCaptureDraw;
            return probe.requests > 0 && w.__mirrorController.plugin.canvas3d.didDraw.observers.length > probe.observers;
        });
        await page.evaluate(() => {
            const w = window as any, c = w.__mirrorController, canvas = c.plugin.canvas3d, probe = w.__studioCaptureDraw;
            let replay = true;
            probe.late = canvas.didDraw.subscribe(() => {
                if (replay || probe.drawn) return;
                probe.drawn = c.getCameraSnapshot();
                probe.frame = c.trajectory.getTrajectoryState().currentFrame;
                probe.mesh = structuredClone(w.__studioDrawnBox);
                canvas.camera.setState({ position: [probe.drawn.position[0] + 50,
                    probe.drawn.position[1], probe.drawn.position[2]] }, 0);
                probe.after = c.getCameraSnapshot();
            });
            replay = false;
            c.plugin.animationLoop.start();
            canvas.requestDraw();
        });
        const result = await awaitResult(page, "save_work_file", before);
        assert.equal(result.ok, true, JSON.stringify(result));
        const observation = await page.evaluate(() => {
            const probe = (window as any).__studioCaptureDraw;
            return { drawn: probe.drawn, after: probe.after, frame: probe.frame, mesh: probe.mesh };
        });
        const saved = JSON.parse(await readFile(path, "utf8"));
        assert.equal(observation.mesh.visible, true);
        assert.equal(observation.mesh.groupCount, 12);
        assert.ok(observation.mesh.vertexCount > 0);
        assert.equal(observation.mesh.frame, observation.frame);
        assert.deepEqual(observation.mesh.camera, observation.drawn);
        assert.notDeepEqual(observation.after.position, observation.drawn.position);
        assert.deepEqual(saved.view.camera, observation.drawn, "save owns the actual completed draw, not a later camera");
        assert.equal(saved.view.structure_index, observation.frame);
    } finally {
        await page.evaluate(() => (window as any).__studioReleaseCaptureDraw?.());
    }
}
