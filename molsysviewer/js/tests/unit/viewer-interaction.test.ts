import assert from "node:assert";
import test from "node:test";
import { ButtonsType } from "molstar/lib/mol-util/input/input-observer";

import {
    createMolSysViewerPluginSpec,
    normalizeContextInteractionEvent,
    normalizeInteractionEvent,
    registerInteractionObservers,
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
