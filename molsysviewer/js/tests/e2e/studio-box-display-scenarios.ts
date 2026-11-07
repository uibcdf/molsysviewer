import type { Page } from "playwright";

/** Observe actual completed Mol* draws without changing rendering or geometry. */
export async function observeBoxDraws(page: Page) {
    await page.evaluate(() => {
        const w = window as any, c = w.__mirrorController;
        w.__studioBoxDrawCount = 0;
        let replay = true;
        w.__studioBoxDrawSubscription = c.plugin.canvas3d.didDraw.subscribe(() => {
            if (replay) return;
            const drawCount = ++w.__studioBoxDrawCount;
            try {
                const cells = Array.from(c.plugin.state.data.cells.values()) as any[];
                const boxes = cells.filter(cell => cell.obj?.data?.sourceData?.tag === "__msv_box");
                const repr = boxes[0]?.obj?.data?.repr;
                const shape = repr?.getAllLoci?.().find((loci: any) => loci.shape?.geometry.kind === "mesh")?.shape;
                const mesh = shape?.geometry;
                const lower = [Infinity, Infinity, Infinity], upper = [-Infinity, -Infinity, -Infinity];
                if (mesh) for (let vertex = 0; vertex < mesh.vertexCount; vertex++) for (let axis = 0; axis < 3; axis++) {
                    const value = mesh.vertexBuffer.ref.value[vertex * 3 + axis];
                    lower[axis] = Math.min(lower[axis], value); upper[axis] = Math.max(upper[axis], value);
                }
                w.__studioDrawnBox = {
                    drawCount, frame: c.trajectory.getTrajectoryState().currentFrame,
                    camera: c.getCameraSnapshot(), boxCount: boxes.length,
                    vertexCount: mesh?.vertexCount ?? 0, groupCount: shape?.groupCount,
                    lower, upper, alpha: repr?.state.alphaFactor,
                    colors: shape ? Array.from({ length: shape.groupCount }, (_, group) => shape.getColor(group)) : [],
                    widths: shape ? Array.from({ length: shape.groupCount }, (_, group) => shape.getSize(group)) : [],
                    visible: !!repr?.renderObjects.length && repr.renderObjects.every((object: any) => object.state.visible),
                };
            } catch (error) {
                w.__studioDrawnBox = { drawCount, observerError: error instanceof Error ? error.name : "Error" };
            }
        });
        replay = false;
    });
}

export async function boxDrawMark(page: Page): Promise<number> {
    return page.evaluate(() => (window as any).__studioBoxDrawCount);
}

/** Independent 3/4/5 nm orthogonal cells and 0.125 nm stroke from the real fixture. */
export async function expectBoxDraw(page: Page, frame: number, after: number, camera?: any) {
    await page.waitForFunction(({ frame, after, camera }) => {
        const box = (window as any).__studioDrawnBox;
        const near = (a: number, b: number) => Number.isFinite(a) && Math.abs(a - b) < 5e-5;
        const cameraMatches = !camera || ["position", "target", "up"].every(key =>
            box?.camera?.[key]?.every((value: number, axis: number) => near(value, camera[key][axis])));
        return box?.drawCount > after && box.frame === frame && box.boxCount === 1
            && box.vertexCount > 0 && box.groupCount === 12 && box.visible && near(box.alpha, .7)
            && box.colors.length === 12 && box.colors.every((value: number) => value === 0xff0000)
            && box.widths.length === 12 && box.widths.every((value: number) => near(value, 1.25))
            && box.lower.every((value: number) => near(value, -1.25))
            && box.upper.every((value: number, axis: number) => near(value, 10 * (3 + frame + axis) + 1.25))
            && cameraMatches;
    }, { frame, after, camera }).catch(async error => {
        const observed = await page.evaluate(() => (window as any).__studioDrawnBox).catch(() => undefined);
        throw new Error(`Restored box did not reach a coherent native draw: ${JSON.stringify({ frame, after, observed })}`, { cause: error });
    });
}

export async function disposeBoxDraws(page: Page) {
    await page.evaluate(() => (window as any).__studioBoxDrawSubscription?.unsubscribe()).catch(() => {});
}
