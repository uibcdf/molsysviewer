import assert from "node:assert";
import test from "node:test";

import { normalizeInteractionEvent, registerInteractionObservers } from "../../src/managers/viewer-controller";

test("normalizeInteractionEvent emits empty payload when no structure loci is present", () => {
    assert.deepStrictEqual(normalizeInteractionEvent("hover", { current: { loci: { kind: "shape-loci" } } }), {
        event: "interaction_hover",
        kind: "empty",
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

test("registerInteractionObservers forwards hover and click notifications", () => {
    const notifications: any[] = [];
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

    registerInteractionObservers(plugin, (msg: any) => notifications.push(msg));

    subscriptions.hover({
        current: {
            loci: {
                kind: "element-loci",
                elements: [{ unit: { elements: [4, 5] }, indices: [0, 1] }],
            },
        },
    });
    subscriptions.click({ current: { loci: null } });

    assert.deepStrictEqual(notifications, [
        { event: "interaction_hover", kind: "structure", atom_indices: [4, 5] },
        { event: "interaction_click", kind: "empty" },
    ]);
});
