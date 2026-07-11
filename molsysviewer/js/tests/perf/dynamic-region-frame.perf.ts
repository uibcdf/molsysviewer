import assert from "node:assert";
import { performance } from "node:perf_hooks";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

const FRAMES = 1_000;
const FRAME_REQUEST_BUDGET_MS = 0.05;

function makeController(hasDynamicRegions: boolean) {
    const controller = Object.create(MolSysViewerController.prototype) as MolSysViewerController & {
        state: { hasFrameDependentDynamicRegions(): boolean };
        notify?: (message: unknown) => void;
    };
    const messages: unknown[] = [];
    controller.state = { hasFrameDependentDynamicRegions: () => hasDynamicRegions };
    controller.notify = (message: unknown) => messages.push(message);
    (controller as any).dynamicRegionEvaluationInFlight = null;
    (controller as any).dynamicRegionEvaluationPendingFrame = null;
    return { controller, messages };
}

function run(): void {
    const silent = makeController(false);
    for (let frame = 0; frame < FRAMES; frame++) {
        (silent.controller as any).requestDynamicRegionEvaluationForFrame(frame);
    }
    assert.strictEqual(silent.messages.length, 0, "plain trajectories must not emit dynamic-region requests");

    const active = makeController(true);
    const started = performance.now();
    for (let frame = 0; frame < FRAMES; frame++) {
        (active.controller as any).requestDynamicRegionEvaluationForFrame(frame);
        (active.controller as any).handleDynamicRegionEvaluationResponse(frame);
    }
    const elapsed = performance.now() - started;
    const perFrameMs = elapsed / FRAMES;

    assert.strictEqual(active.messages.length, FRAMES, "expected exactly one dynamic-region request per displayed frame");
    assert.ok(
        perFrameMs < FRAME_REQUEST_BUDGET_MS,
        `dynamic-region request gate ${perFrameMs.toFixed(4)}ms/frame exceeds ${FRAME_REQUEST_BUDGET_MS}ms/frame`,
    );
    console.log(JSON.stringify({ frames: FRAMES, perFrameMs, messages: active.messages.length }));
}

try {
    run();
} catch (error) {
    console.error(error);
    process.exitCode = 1;
}
