import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";


test("scene-object summaries drive panels and visibility goes through Python", async () => {
    const controller: any = Object.create(MolSysViewerController.prototype);
    const notifications: unknown[] = [];
    let annotationRows: any[] = [];
    let layerRows: any[] = [];

    controller.annotationSummaries = [];
    controller.measurementSummaries = [];
    controller.shapeSummaries = [];
    controller.addonsAnnotations = new Map();
    controller.addonsMeasurements = new Map();
    controller.addonsShapes = new Map();
    controller.addonsActive = null;
    controller.addonsContext = null;
    controller.addonsScene = null;
    controller.addonsList = [];
    controller.addonDiagnostics = [];
    controller.currentWorkspace = "core";
    controller.notify = (message: unknown) => notifications.push(message);
    controller.plugin = { canvas3d: undefined };
    controller.scene = {
        isDarkMode: false,
        isSpinActive: false,
        isSwingActive: false,
    };
    controller.groupPanel = {
        setAnnotations: (items: any[]) => { annotationRows = items; },
        setMeasurements: (_items: any[]) => {},
        setShapes: (_items: any[]) => {},
        setLayerObjects: (items: any[]) => { layerRows = items; },
        setScene: (_summary: unknown) => {},
    };
    controller.addonsPanel = {
        setActiveWorkspacePanel: (_panel: unknown) => {},
        setAddons: (_items: unknown[]) => {},
        setAddonDiagnostics: (_items: unknown[]) => {},
        setAddonWorkbenchSections: (_items: unknown[]) => {},
    };
    controller.applyWorkbenchMessage = () => {};
    controller.refreshNavigatePanel = () => {};
    controller.syncStripOverlaysForMessage = () => {};
    controller.refreshPanelWorkspaceChrome = () => {};

    const originalError = console.error;
    console.error = (...args: unknown[]) => {
        throw new Error(`unexpected console.error: ${String(args[0])}`);
    };
    try {
        await controller.handleMessage({
            op: "set_annotation_summaries",
            annotations: [{
                tag: "note",
                kind: "label",
                text: "Binding site",
                layer_tag: "analysis",
                atom_indices: [1, 2],
                hidden: false,
            }],
        });
    } finally {
        console.error = originalError;
    }

    assert.strictEqual(annotationRows.length, 1);
    assert.strictEqual(annotationRows[0].title, "Binding site");
    assert.deepStrictEqual(layerRows.map(item => item.tag), ["note"]);

    let localDispatches = 0;
    controller.handleMessage = async () => { localDispatches += 1; };
    annotationRows[0].onToggleVisibility();

    assert.strictEqual(localDispatches, 0);
    assert.deepStrictEqual(notifications, [{
        event: "interaction_context_action",
        action: "toggle_annotation_visibility",
        tag: "note",
    }]);
});
