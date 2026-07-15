import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

test("viewer controller does not rebuild System chrome for non-invalidating messages", async () => {
    const controller = Object.create(MolSysViewerController.prototype) as MolSysViewerController & {
        state: { hideRegion(message: unknown): Promise<void> };
        syncStripOverlaysForMessage(message: unknown): void;
        refreshPanelWorkspaceChrome(): void;
    };
    let chromeRefreshes = 0;
    let stripSyncs = 0;

    controller.state = {
        async hideRegion(_message: unknown) {},
    };
    controller.syncStripOverlaysForMessage = (_message: unknown) => {
        stripSyncs += 1;
    };
    controller.refreshPanelWorkspaceChrome = () => {
        chromeRefreshes += 1;
    };

    const originalWarn = console.warn;
    console.warn = () => {};
    try {
        await controller.handleMessage({ op: "__does_not_exist__" } as never);
        await controller.handleMessage({ op: "hide_region", tag: "site" });
    } finally {
        console.warn = originalWarn;
    }

    assert.strictEqual(chromeRefreshes, 0);
    assert.strictEqual(stripSyncs, 2);
});

test("viewer controller maps section summaries through to the Viewport panel", async () => {
    const controller = Object.create(MolSysViewerController.prototype) as any;
    let received: any = null;
    controller.groupPanel = { setSections: (items: any, settings: any) => { received = { items, settings }; } };
    controller.refreshNavigatePanel = () => {};
    controller.refreshPanelWorkspaceChrome = () => {};
    controller.syncStripOverlaysForMessage = () => {};

    await controller.handleMessage({
        op: "set_section_summaries",
        sections: [{ tag: "cut", owner: "topomt", point: [0.1, 0.2, 0.3], normal: [1, 0, 0], invert: true, hidden: false }],
        active_selection_count: 3,
        system_loaded: true,
    });

    assert.deepStrictEqual(received, {
        items: [{ tag: "cut", owner: "topomt", point: [0.1, 0.2, 0.3], normal: [1, 0, 0], invert: true, hidden: false }],
        settings: { activeSelectionCount: 3, systemLoaded: true },
    });
});

test("viewer controller coalesces dynamic-region frame evaluation requests", () => {
    const controller = Object.create(MolSysViewerController.prototype) as MolSysViewerController & {
        state: { hasFrameDependentDynamicRegions(): boolean };
        notify?: (message: unknown) => void;
    };
    const messages: unknown[] = [];
    controller.state = { hasFrameDependentDynamicRegions: () => true };
    controller.notify = (message: unknown) => messages.push(message);
    (controller as any).dynamicRegionEvaluationInFlight = null;
    (controller as any).dynamicRegionEvaluationPendingFrame = null;

    (controller as any).requestDynamicRegionEvaluationForFrame(1);
    (controller as any).requestDynamicRegionEvaluationForFrame(2);
    (controller as any).requestDynamicRegionEvaluationForFrame(3);

    assert.deepStrictEqual(messages, [
        { event: "request_dynamic_region_evaluation", frame: 1 },
    ]);

    (controller as any).handleDynamicRegionEvaluationResponse(1);

    assert.deepStrictEqual(messages, [
        { event: "request_dynamic_region_evaluation", frame: 1 },
        { event: "request_dynamic_region_evaluation", frame: 3 },
    ]);
});

test("viewer controller does not request dynamic-region evaluation without frame-dependent regions", () => {
    const controller = Object.create(MolSysViewerController.prototype) as MolSysViewerController & {
        state: { hasFrameDependentDynamicRegions(): boolean };
        notify?: (message: unknown) => void;
    };
    const messages: unknown[] = [];
    controller.state = { hasFrameDependentDynamicRegions: () => false };
    controller.notify = (message: unknown) => messages.push(message);

    (controller as any).requestDynamicRegionEvaluationForFrame(1);

    assert.deepStrictEqual(messages, []);
});
