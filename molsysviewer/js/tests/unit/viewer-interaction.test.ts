import assert from "node:assert";
import test from "node:test";
import { ButtonsType } from "molstar/lib/mol-util/input/input-observer";

import {
    createMolSysViewerPluginSpec,
    normalizeContextInteractionEvent,
    MolSysViewerController,
    normalizeInteractionEvent,
    registerInteractionObservers,
    resolveTooltipPayload,
    suppressCanvasContextMenu,
} from "../../src/managers/viewer-controller";
import { PluginBehaviors } from "molstar/lib/mol-plugin/behavior";

test("normalizeInteractionEvent emits empty payload when no structure loci is present", () => {
    assert.deepStrictEqual(normalizeInteractionEvent("hover", { current: { loci: { kind: "shape-loci" } } }), {
        event: "interaction_hover",
        kind: "empty",
    });
});

test("normalizeInteractionEvent extracts shape metadata from shape loci", () => {
    assert.deepStrictEqual(normalizeInteractionEvent("click", {
        current: {
            loci: {
                kind: "shape-loci",
                shape: {
                    name: "Pocket Blob",
                    sourceData: { tag: "pocket", atom_indices: [8, 9] },
                },
            },
        },
    }), {
        event: "interaction_click",
        kind: "shape",
        atom_indices: [8, 9],
        shape_name: "Pocket Blob",
        tag: "pocket",
    });
});

test("normalizeInteractionEvent preserves shape group entity refs", () => {
    const entityRef = { kind: "topomt.face", id: 7, atoms: [8, 9, 10] };
    assert.deepStrictEqual(normalizeInteractionEvent("click", {
        current: {
            loci: {
                kind: "group-loci",
                groups: [{ ids: [1] }],
                shape: {
                    name: "Topo Face",
                    sourceData: {
                        tag: "faces",
                        atom_indices: [8, 9, 10, 11],
                        __groupAtoms: [[8, 9, 11], [8, 9, 10]],
                        __groupEntityRefs: [{ kind: "topomt.face", id: 6 }, entityRef],
                    },
                },
            },
        },
    }), {
        event: "interaction_click",
        kind: "shape",
        atom_indices: [8, 9, 10],
        shape_name: "Topo Face",
        tag: "faces",
        entity_ref: entityRef,
    });
});

test("normalizeInteractionEvent extracts atom indices from structure loci", () => {
    const loci: any = {
        kind: "element-loci",
        elements: [
            {
                unit: { elements: [10, 11, 12, 13] },
                indices: [1, 3],
            },
            {
                unit: { elements: [13, 14, 15] },
                indices: [0, 2],
            },
        ],
    };

    assert.deepStrictEqual(normalizeInteractionEvent("click", { current: { loci } }), {
        event: "interaction_click",
        kind: "structure",
        atom_indices: [11, 13, 15],
    });
});

test("normalizeContextInteractionEvent captures page coordinates and atom indices", () => {
    const loci: any = {
        kind: "element-loci",
        elements: [{ unit: { elements: [8, 9] }, indices: [0, 1] }],
    };

    assert.deepStrictEqual(normalizeContextInteractionEvent({
        current: { loci },
        page: [120, 240],
    }), {
        event: "interaction_context_menu",
        kind: "structure",
        atom_indices: [8, 9],
        page_x: 120,
        page_y: 240,
    });
});

test("normalizeContextInteractionEvent captures shape context targets", () => {
    assert.deepStrictEqual(normalizeContextInteractionEvent({
        current: {
            loci: {
                kind: "shape-loci",
                shape: {
                    name: "Pocket Blob",
                    sourceData: { tag: "pocket", atom_indices: [8, 9] },
                },
            },
        },
        page: [120, 240],
    }), {
        event: "interaction_context_menu",
        kind: "shape",
        atom_indices: [8, 9],
        shape_name: "Pocket Blob",
        tag: "pocket",
        page_x: 120,
        page_y: 240,
    });
});

test("normalizeContextInteractionEvent preserves shape group entity refs", () => {
    const entityRef = { kind: "topomt.edge", id: "e-1", atoms: [8, 9] };
    assert.deepStrictEqual(normalizeContextInteractionEvent({
        current: {
            loci: {
                kind: "group-loci",
                groups: [{ ids: [0] }],
                shape: {
                    name: "Topo Edge",
                    sourceData: {
                        tag: "edges",
                        atom_indices: [8, 9, 10],
                        __groupAtoms: [[8, 9]],
                        __groupEntityRefs: [entityRef],
                    },
                },
            },
        },
        page: [120, 240],
    }), {
        event: "interaction_context_menu",
        kind: "shape",
        atom_indices: [8, 9],
        shape_name: "Topo Edge",
        tag: "edges",
        entity_ref: entityRef,
        page_x: 120,
        page_y: 240,
    });
});

test("registerInteractionObservers forwards hover and click notifications", () => {
    const notifications: any[] = [];
    const menuEvents: any[] = [];
    const subscriptions: Record<string, (ev: any) => void> = {};
    const plugin: any = {
        behaviors: {
            interaction: {
                hover: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.hover = cb;
                    },
                },
                click: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.click = cb;
                    },
                },
            },
        },
    };

    registerInteractionObservers(plugin, (msg: any) => notifications.push(msg), (msg: any) => menuEvents.push(msg));

    subscriptions.hover({
        current: {
            loci: {
                kind: "element-loci",
                elements: [{ unit: { elements: [4, 5] }, indices: [0, 1] }],
            },
        },
    });
    subscriptions.click({ current: { loci: null } });
    subscriptions.click({
        button: ButtonsType.Flag.Secondary,
        current: { loci: { kind: "element-loci", elements: [{ unit: { elements: [7] }, indices: [0] }] } },
        page: [50, 60],
    });

    assert.deepStrictEqual(notifications, [
        { event: "interaction_hover", kind: "structure", atom_indices: [4, 5] },
        { event: "interaction_click", kind: "empty" },
        { event: "interaction_context_menu", kind: "structure", atom_indices: [7], page_x: 50, page_y: 60 },
    ]);
    assert.deepStrictEqual(menuEvents, [
        { event: "interaction_context_menu", kind: "structure", atom_indices: [7], page_x: 50, page_y: 60 },
    ]);
});

test("MolSysViewerController rejects image export above WebGL limits before screenshot allocation", async () => {
    let screenshotCalled = false;
    const gl: any = {
        drawingBufferWidth: 800,
        drawingBufferHeight: 600,
        MAX_RENDERBUFFER_SIZE: 0x84E8,
        MAX_VIEWPORT_DIMS: 0x0D3A,
        getParameter(param: number) {
            if (param === this.MAX_RENDERBUFFER_SIZE) return 4096;
            if (param === this.MAX_VIEWPORT_DIMS) return [4096, 4096];
            return undefined;
        },
    };
    const controller: any = Object.create(MolSysViewerController.prototype);
    controller.plugin = {
        canvas3d: { webgl: { gl } },
        helpers: {
            viewportScreenshot: {
                values: {},
                behaviors: { values: { next() { screenshotCalled = true; } } },
                async getImageDataUri() { screenshotCalled = true; return "data:image/png;base64,ok"; },
            },
        },
    };

    const result = await controller.getImageDataUri({ width: 3000, height: 2000, scale: 2, transparent: true });

    assert.strictEqual(screenshotCalled, false);
    assert.deepStrictEqual(result, {
        success: false,
        error_type: "GPU_LIMIT_EXCEEDED",
        message: "Requested image export size 6000x4000px exceeds WebGL GPU limits (MAX_RENDERBUFFER_SIZE=4096, MAX_VIEWPORT_DIMS=4096x4096). Reduce width, height, or scale.",
        requested_width: 6000,
        requested_height: 4000,
        max_renderbuffer_size: 4096,
        max_viewport_width: 4096,
        max_viewport_height: 4096,
    });
});

test("MolSysViewerController debounces hover notifications to Python", async () => {
    const notifications: any[] = [];
    const controller: any = Object.create(MolSysViewerController.prototype);
    controller.notify = (msg: any) => notifications.push(msg);
    controller.pendingHoverPayload = null;
    controller.hoverDebounceTimer = null;
    controller.hoverDebounceMs = 10;
    controller.hoverTelemetryEnabled = true;

    controller.emitDebouncedHover({ event: "interaction_hover", kind: "structure", atom_indices: [1] });
    controller.emitDebouncedHover({ event: "interaction_hover", kind: "structure", atom_indices: [2] });

    assert.deepStrictEqual(notifications, []);
    await new Promise((resolve) => setTimeout(resolve, 20));
    assert.deepStrictEqual(notifications, [
        { event: "interaction_hover", kind: "structure", atom_indices: [2] },
    ]);
});

test("MolSysViewerController suppresses hover telemetry until Python enables it", async () => {
    const notifications: any[] = [];
    const controller: any = Object.create(MolSysViewerController.prototype);
    controller.notify = (msg: any) => notifications.push(msg);
    controller.hoverTelemetryEnabled = false;
    controller.pendingHoverPayload = null;
    controller.hoverDebounceTimer = null;
    controller.hoverDebounceMs = 5;

    controller.emitDebouncedHover({ event: "interaction_hover", kind: "structure", atom_indices: [1] });
    await new Promise((resolve) => setTimeout(resolve, 10));

    assert.deepStrictEqual(notifications, []);
});

test("disabling hover telemetry cancels a pending notification", async () => {
    const notifications: any[] = [];
    const controller: any = Object.create(MolSysViewerController.prototype);
    controller.notify = (msg: any) => notifications.push(msg);
    controller.hoverTelemetryEnabled = true;
    controller.pendingHoverPayload = null;
    controller.hoverDebounceTimer = null;
    controller.hoverDebounceMs = 10;

    controller.emitDebouncedHover({ event: "interaction_hover", kind: "structure", atom_indices: [1] });
    controller.setHoverTelemetryEnabled(false);
    await new Promise((resolve) => setTimeout(resolve, 20));

    assert.deepStrictEqual(notifications, []);
    assert.strictEqual(controller.pendingHoverPayload, null);
    assert.strictEqual(controller.hoverDebounceTimer, null);
});

test("suppressCanvasContextMenu prevents the host context menu on canvas", () => {
    const listeners: Array<(event: any) => void> = [];
    const canvas: any = {
        addEventListener(type: string, cb: (event: any) => void, capture?: boolean) {
            if (type === "contextmenu" && capture === true) listeners.push(cb);
        },
        removeEventListener(_type: string, _cb: (event: any) => void, _capture?: boolean) {},
    };
    const host: any = {
        contains(target: any) { return target === hostTarget; },
        addEventListener(type: string, cb: (event: any) => void, capture?: boolean) {
            if (type === "contextmenu" && capture === true) listeners.push(cb);
        },
        removeEventListener(_type: string, _cb: (event: any) => void, _capture?: boolean) {},
    };
    const hostTarget = { kind: "host-target" };
    const globalListeners: Record<string, ((event: any) => void)[]> = {};
    const previousWindow = (globalThis as any).window;
    (globalThis as any).window = {
        addEventListener(type: string, cb: (event: any) => void, capture?: boolean) {
            if (capture !== true) return;
            (globalListeners[type] ??= []).push(cb);
        },
        removeEventListener(_type: string, _cb: (event: any) => void, _capture?: boolean) {},
    };
    const prevented = { defaultPrevented: false, propagationStopped: false };

    try {
        suppressCanvasContextMenu(host, canvas);
        for (const listener of globalListeners.pointerdown ?? []) {
            listener({ button: 2, target: hostTarget });
        }
        for (const listener of listeners) listener({
            target: hostTarget,
            preventDefault() { prevented.defaultPrevented = true; },
            stopPropagation() { prevented.propagationStopped = true; },
        });
    } finally {
        (globalThis as any).window = previousWindow;
    }

    assert.deepStrictEqual(prevented, { defaultPrevented: true, propagationStopped: true });
});

test("createMolSysViewerPluginSpec disables primary focus bindings", () => {
    const spec = createMolSysViewerPluginSpec();
    const focusBehaviors = (spec.behaviors ?? []).filter((behavior: any) =>
        behavior.transformer === PluginBehaviors.Camera.FocusLoci
        || behavior.transformer === PluginBehaviors.Representation.FocusLoci
    );

    assert.strictEqual(focusBehaviors.length, 0);
});

test("registerInteractionObservers notifyHover overrides default hover notification", () => {
    const defaultNotifications: any[] = [];
    const customNotifications: any[] = [];
    const subscriptions: Record<string, (ev: any) => void> = {};
    const plugin: any = {
        behaviors: {
            interaction: {
                hover: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.hover = cb;
                    },
                },
                click: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.click = cb;
                    },
                },
            },
        },
    };

    registerInteractionObservers(
        plugin,
        (msg: any) => defaultNotifications.push(msg),
        undefined,
        undefined,
        undefined,
        undefined,
        (ev: any) => {
            // custom notifyHover: emit annotation kind when tooltip is set
            const tag = ev?.current?.repr?.props?.tooltip;
            if (tag) {
                customNotifications.push({ event: "interaction_hover", kind: "annotation", tag });
            } else {
                customNotifications.push({ event: "interaction_hover", kind: "fallback" });
            }
        },
    );

    // Hover over annotation repr (tooltip set)
    subscriptions.hover({ current: { repr: { props: { tooltip: "ann-1" } }, loci: null } });
    // Hover over non-annotation
    subscriptions.hover({ current: { repr: null, loci: null } });

    // Default notify should NOT have been called (notifyHover overrides it)
    assert.strictEqual(defaultNotifications.length, 0);
    assert.deepStrictEqual(customNotifications, [
        { event: "interaction_hover", kind: "annotation", tag: "ann-1" },
        { event: "interaction_hover", kind: "fallback" },
    ]);
});

test("registerInteractionObservers notifyClick overrides default primary click notification", () => {
    const defaultNotifications: any[] = [];
    const customNotifications: any[] = [];
    const subscriptions: Record<string, (ev: any) => void> = {};
    const plugin: any = {
        behaviors: {
            interaction: {
                hover: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.hover = cb;
                    },
                },
                click: {
                    subscribe(cb: (ev: any) => void) {
                        subscriptions.click = cb;
                    },
                },
            },
        },
    };

    registerInteractionObservers(
        plugin,
        (msg: any) => defaultNotifications.push(msg),
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        (ev: any) => {
            // custom notifyClick: emit annotation kind when tooltip is set
            const tag = ev?.current?.repr?.props?.tooltip;
            if (tag) {
                customNotifications.push({ event: "interaction_click", kind: "annotation", tag });
            } else {
                customNotifications.push({ event: "interaction_click", kind: "fallback" });
            }
        },
    );

    // Primary click on annotation repr
    subscriptions.click({ current: { repr: { props: { tooltip: "ann-2" } }, loci: null } });
    // Primary click on non-annotation
    subscriptions.click({ current: { repr: null, loci: null } });

    // Default notify should NOT have been called for primary clicks (notifyClick overrides it)
    // But secondary-click notifications still go through default notify — no secondary clicks here
    assert.strictEqual(defaultNotifications.length, 0);
    assert.deepStrictEqual(customNotifications, [
        { event: "interaction_click", kind: "annotation", tag: "ann-2" },
        { event: "interaction_click", kind: "fallback" },
    ]);
});

// ── resolveTooltipPayload ─────────────────────────────────────────────────────

const mockAnnotations = {
    hasTag: (t: string) => t === "ann-label",
    getSpec: (t: string) => t === "ann-label" ? { text: "Catalytic Asp", atom_indices: [3, 7] } : undefined,
};
const mockMeasurements = {
    hasTag: (t: string) => t === "dist-1",
    getSpec: (t: string) => t === "dist-1" ? { kind: "distance", atom_indices: [0, 5] } : undefined,
};

test("resolveTooltipPayload returns annotation payload when tooltip matches annotation tag", () => {
    const ev = { current: { repr: { props: { tooltip: "ann-label" } } } };
    assert.deepStrictEqual(resolveTooltipPayload("hover", ev, mockAnnotations, mockMeasurements), {
        event: "interaction_hover",
        kind: "annotation",
        tag: "ann-label",
        text: "Catalytic Asp",
        atom_indices: [3, 7],
    });
});

test("resolveTooltipPayload returns measurement payload when tooltip matches measurement tag", () => {
    const ev = { current: { repr: { props: { tooltip: "dist-1" } } } };
    assert.deepStrictEqual(resolveTooltipPayload("click", ev, mockAnnotations, mockMeasurements), {
        event: "interaction_click",
        kind: "measurement",
        tag: "dist-1",
        measurement_name: "distance",
        atom_indices: [0, 5],
    });
});

test("resolveTooltipPayload returns null when tooltip is absent", () => {
    const ev = { current: { repr: { props: {} } } };
    assert.strictEqual(resolveTooltipPayload("hover", ev, mockAnnotations, mockMeasurements), null);
});

test("resolveTooltipPayload returns null when tooltip tag matches nothing", () => {
    const ev = { current: { repr: { props: { tooltip: "unknown-tag" } } } };
    assert.strictEqual(resolveTooltipPayload("hover", ev, mockAnnotations, mockMeasurements), null);
});

test("resolveTooltipPayload returns null when ev is null", () => {
    assert.strictEqual(resolveTooltipPayload("click", null, mockAnnotations, mockMeasurements), null);
});
