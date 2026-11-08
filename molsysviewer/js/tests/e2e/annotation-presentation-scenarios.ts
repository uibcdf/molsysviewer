import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Page } from "playwright";

function near(actual: number[], expected: number[], label: string) {
    assert.equal(actual?.length, expected.length, label);
    actual.forEach((value, index) => assert.ok(Math.abs(value - expected[index]) < 2e-4,
        `${label}: ${JSON.stringify(actual)} != ${JSON.stringify(expected)}`));
}

/** An independent camera-state oracle; do not call the production basis helper. */
function expectedPosition(anchor: number[], camera: any) {
    const norm = (v: number[]) => { const length = Math.hypot(...v); return v.map(x => x / length); };
    const cross = (a: number[], b: number[]) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
    const toward = norm(camera.position.map((v: number, i: number) => v-camera.target[i]));
    const right = norm(cross(camera.up, toward)), up = norm(cross(toward, right));
    return anchor.map((value, i) => value + 6*right[i] + 8*up[i] + 5*toward[i]);
}

function coherent(geometry: any[], camera: any) {
    assert.equal(geometry.length, 2, "native text and solid leader must both exist");
    const text = geometry.find(item => item.kind === "text"), line = geometry.find(item => item.kind === "lines");
    const position = expectedPosition(text.anchor, camera);
    for (const item of geometry) near(item.gpuTransform, item.shapeTransform, "CPU/GPU instance transform");
    near(text.position, position, "presented recipe position");
    near(text.textCenter, position, "GPU text center");
    near(text.cpuCenter, position, "native CPU loci/focus center");
    near(line.lineStart, text.anchor, "solid leader anchor");
    near(line.lineEnd, position, "solid leader end");
    return position;
}

async function observePresentedCamera(page: Page, mode: string,
    command: (name: string, details?: Record<string, unknown>) => Promise<void>) {
    // Mol* setState publishes the snapshot before Camera.update builds its
    // view matrix. Observe geometry and that camera in the same real didDraw,
    // rather than combining the next snapshot with the preceding GPU draw.
    await page.evaluate(() => {
        const w = window as any, c = w.__mirrorController;
        w.__annotationPresentationDraw = undefined;
        let replay = true;
        w.__annotationPresentationSubscription = c.plugin.canvas3d.didDraw.subscribe(() => {
            if (replay || !c.annotations.isGeometryCurrent()) return;
            w.__annotationPresentationDraw = {
                camera: c.getCameraSnapshot(),
                geometry: w.Harness.inspectAnnotationPresentation(c, "moving-note"),
                world: w.Harness.inspectAnnotationPresentation(c, "world-note"),
                absolute: w.Harness.inspectAnnotationPresentation(c, "absolute-note"),
            };
        });
        replay = false;
    });
    try {
        await command("projection", { mode });
        await command("camera", { snapshot: { position: [40, 30, 100], target: [0, 0, 0], up: [0, 1, 0] } });
        const received = await page.waitForFunction(mode => {
            const sample = (window as any).__annotationPresentationDraw, camera = sample?.camera;
            return camera?.mode === mode && Math.abs(camera.position[0]-40) < 1e-6 ? sample : false;
        }, mode);
        return received.jsonValue();
    } finally {
        await page.evaluate(() => {
            const w = window as any;
            w.__annotationPresentationSubscription?.unsubscribe();
            delete w.__annotationPresentationSubscription;
        });
    }
}

export async function checkAnnotationPresentation(page: Page, workspace: string,
    command: (name: string, details?: Record<string, unknown>) => Promise<void>) {
    await page.waitForFunction(() => {
        const c = (window as any).__mirrorController, camera = c.getCameraSnapshot();
        return c.trajectory.getTrajectoryState().currentFrame === 0 && Math.abs(camera.position[2]-100) < 1e-6
            && c.annotations.isGeometryCurrent();
    });
    for (const mode of ["perspective", "orthographic"]) {
        const live = await observePresentedCamera(page, mode, command);
        const labelPosition = coherent(live.geometry, live.camera);
        const world = live.world.find((item: any) => item.kind === "text");
        near(world.textCenter, world.anchor.map((value: number, index: number) => value + (index === 0 ? 10 : 0)), "world offset");
        const absolute = live.absolute.find((item: any) => item.kind === "text");
        near(absolute.textCenter, [-10, -10, 0], "absolute world label");
        const image = await page.evaluate(() => (window as any).Harness.inspectAnnotationImage((window as any).__mirrorController, "moving-note"));
        assert.deepEqual([image.width, image.height], [320, 240]);
        assert.ok(image.observations.length, "the real image renderer must consume an alternate camera");
        for (const observation of image.observations) coherent(observation.geometry, observation.camera);
        coherent(image.restored, image.liveCamera);
        const bytes = Buffer.from(image.png, "base64");
        assert.deepEqual([bytes.readUInt32BE(16), bytes.readUInt32BE(20)], [320, 240]);
        await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, `camera-callout-${mode}.png`), bytes);
        await page.bringToFront();
        const hit = await page.waitForFunction(position => {
            const c = (window as any).__mirrorController, h = (window as any).Harness;
            for (const dx of [0, 4, 8, 12, 20, 30]) for (const dy of [0, 3, -3, 6, -6]) {
                const hit = h.pickScenePosition(c, position, [dx, dy]);
                if (hit.owner?.kind === "annotation" && hit.owner.tag === "moving-note" && hit.shapeKind === "text") return hit;
            }
            return false;
        }, labelPosition);
        const picked = await hit.jsonValue() as any;
        assert.equal(picked.lociKind, "group-loci");
        near(picked.cpuCenter, labelPosition, "actual GPU-picked CPU loci center");
        await page.mouse.click(picked.point.x, picked.point.y);
        await page.waitForFunction(() => {
            const c = (window as any).__mirrorController, h = (window as any).Harness;
            return c.activeSelection.getCurrentItems().some((item: any) => item.source_kind === "annotation" && item.tag === "moving-note")
                && h.inspectAnnotationPresentation(c, "moving-note").some((item: any) => item.markers.some((value: number) => (value & 2) !== 0));
        });
        console.log(`[E2E annotation presentation] ${mode}: three-axis offset, native text/leader, CPU loci, alternate-camera PNG, live restoration and GPU selection markers received`);
    }
}
