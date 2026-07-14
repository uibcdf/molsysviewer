import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";


test("scene-object summaries drive panels and visibility goes through Python", async () => {
    const controller: any = Object.create(MolSysViewerController.prototype);
    const notifications: unknown[] = [];
    let annotationRows: any[] = [];
    let annotationSettings: any = null;
    let measurementRows: any[] = [];
    let measurementSettings: any = null;
    let shapeRows: any[] = [];
    let layerRows: any[] = [];
    let layers: any[] = [];

    controller.annotationSummaries = [];
    controller.measurementSummaries = [];
    controller.shapeSummaries = [];
    controller.layerSummaries = [];
    controller.shapeRenderStatuses = new Map();
    controller.addonsAnnotations = new Map();
    controller.addonsMeasurements = new Map();
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
        setAnnotations: (items: any[], settings: any) => { annotationRows = items; annotationSettings = settings; },
        setMeasurements: (items: any[], settings: any) => { measurementRows = items; measurementSettings = settings; },
        updateMeasurementSeries: (_payload: any) => {},
        setShapes: (items: any[]) => { shapeRows = items; },
        setLayerObjects: (items: any[]) => { layerRows = items; },
        setLayers: (items: any[]) => { layers = items; },
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
            op: "set_layer_summaries",
            layers: [
                { tag: "analysis", provenance: "user", hidden: true },
                { tag: "site", provenance: "auto", hidden: false },
            ],
        });
        await controller.handleMessage({
            op: "set_annotation_summaries",
            annotations: [{
                tag: "note",
                kind: "label",
                text: "Binding site",
                layer_tag: "analysis",
                style: { color: "#123456", size_em: 1.25, background: true, background_opacity: 0.6 },
                n_atoms: 2,
                atom_indices: [1, 2],
                anchor: { type: "atoms", indices: [1, 2] },
                hidden: false,
                broken: true,
                broken_reason: "Missing anchor atom indices: [3]",
            }],
            active_selection_count: 2,
            system_loaded: true,
        });
        await controller.handleMessage({
            op: "set_shape_summaries",
            shapes: [{
                op: "add_sphere",
                kind: "sphere",
                tag: "site",
                layer_tag: "analysis",
                title: "Sphere",
                subtitle: "sphere",
                atom_indices: [1],
                hidden: false,
                color: "#ABCDEF",
                radius: { magnitude: 3, unit: "angstrom" },
                alpha: 0.65,
                radius_scale: null,
                length_scale: null,
                broken: false,
                broken_reason: null,
            }],
        });
        await controller.handleMessage({
            op: "set_measurement_summaries",
            measurements: [{
                tag: "distance",
                kind: "distance",
                n_picks: 2,
                value: null,
                unit: null,
                endpoint_labels: ["CA (ALA 1)", "CA (ALA 2)"],
                endpoint_policy: "centroid",
                atom_indices: [1],
                hidden: false,
                broken: true,
                broken_reason: "Anchor contains no atoms.",
            }],
            endpoint_policy_default: "representative_atom",
            representative_atoms: { protein: "CB", nucleic: "P", lipid: "P", other: "" },
            structure_index: 3,
            system_loaded: true,
        });
    } finally {
        console.error = originalError;
    }

    assert.strictEqual(annotationRows.length, 1);
    assert.strictEqual(annotationRows[0].text, "Binding site");
    assert.strictEqual(annotationRows[0].nAtoms, 2);
    assert.deepStrictEqual(annotationRows[0].style, {
        color: "#123456", size_em: 1.25, background: true, background_opacity: 0.6,
    });
    assert.deepStrictEqual(annotationRows[0].anchor, { type: "atoms", indices: [1, 2] });
    assert.strictEqual(annotationRows[0].broken, true);
    assert.strictEqual(annotationRows[0].brokenReason, "Missing anchor atom indices: [3]");
    assert.strictEqual(annotationSettings.systemLoaded, true);
    assert.strictEqual(annotationSettings.activeSelectionCount, 2);
    assert.strictEqual(measurementRows[0].broken, true);
    assert.strictEqual(measurementRows[0].brokenReason, "Anchor contains no atoms.");
    assert.deepStrictEqual(measurementRows[0].endpointLabels, ["CA (ALA 1)", "CA (ALA 2)"]);
    assert.strictEqual(measurementSettings.endpointPolicyDefault, "representative_atom");
    assert.strictEqual(measurementSettings.representativeAtoms.protein, "CB");
    assert.strictEqual(measurementSettings.structureIndex, 3);
    assert.strictEqual(measurementSettings.systemLoaded, true);
    assert.deepStrictEqual(shapeRows[0], {
        op: "add_sphere",
        kind: "sphere",
        tag: "site",
        layerTag: "analysis",
        title: "Sphere",
        subtitle: "sphere",
        hidden: false,
        atomIndices: [1],
        color: "#abcdef",
        nColors: undefined,
        radius: { magnitude: 3, unit: "angstrom" },
        nRadii: undefined,
        alpha: 0.65,
        radiusScale: undefined,
        lengthScale: undefined,
        broken: false,
        brokenReason: undefined,
    });
    assert.deepStrictEqual(layerRows.map(item => item.tag), ["note", "distance", "site"]);
    assert.deepStrictEqual(layers, [
        { tag: "analysis", provenance: "user", hidden: true },
        { tag: "site", provenance: "auto", hidden: false },
    ]);

    assert.deepStrictEqual(notifications, []);
});

test("shape render diagnostics stay local while remaining queryable from Python", () => {
    const controller: any = Object.create(MolSysViewerController.prototype);
    const notifications: unknown[] = [];
    let panelStatus: unknown = null;
    controller.shapeRenderStatuses = new Map();
    controller.groupPanel = { updateShapeRenderStatus: (status: unknown) => { panelStatus = status; } };
    controller.notify = (message: unknown) => notifications.push(message);

    controller.handleShapeRenderStatus({
        tag: "site",
        op: "add_sphere_from_atoms",
        frame: 42,
        status: "invalid-indices",
        requested_atoms: 3,
        used_atoms: 0,
        reason: "coordinates invalid in frame 42",
    });

    assert.deepStrictEqual(controller.shapeRenderStatuses.get("site"), {
        tag: "site",
        op: "add_sphere_from_atoms",
        frame: 42,
        status: "invalid-indices",
        requestedAtoms: 3,
        usedAtoms: 0,
        reason: "coordinates invalid in frame 42",
    });
    assert.deepStrictEqual(panelStatus, controller.shapeRenderStatuses.get("site"));
    assert.deepStrictEqual(notifications, [{
        event: "shape_render_status",
        tag: "site",
        op: "add_sphere_from_atoms",
        frame: 42,
        status: "invalid-indices",
        requested_atoms: 3,
        used_atoms: 0,
        reason: "coordinates invalid in frame 42",
    }]);
});
