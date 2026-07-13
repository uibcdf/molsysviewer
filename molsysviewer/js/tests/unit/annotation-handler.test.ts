import assert from "node:assert";
import test from "node:test";

import { AnnotationHandlers } from "../../src/managers/handlers/annotation-handlers";

test("AnnotationHandlers renameTag moves only the addressed annotation bookkeeping", () => {
    const handler = new AnnotationHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        registerRef: () => void 0,
    });
    const refsByTag = (handler as any).refsByTag as Map<string, Set<string>>;
    const specsByTag = (handler as any).specsByTag as Map<string, any>;
    refsByTag.set("site1", new Set(["annotation-ref"]));
    specsByTag.set("site1", { text: "site", atom_indices: [0], tag: "site1", layer_tag: "site1" });

    handler.renameTag("site1", "label1");

    assert.strictEqual(refsByTag.has("site1"), false);
    assert.deepStrictEqual(Array.from(refsByTag.get("label1") ?? []), ["annotation-ref"]);
    assert.strictEqual(specsByTag.get("label1")?.tag, "label1");
    assert.strictEqual(specsByTag.get("label1")?.layer_tag, "label1");
});

test("AnnotationHandlers.addLabel creates a Mol* label from atom indices and registers refs under the tag", async () => {
    const calls: any[] = [];
    const refs: Array<{ ref: string; tag?: string }> = [];
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(loci: any, options: any) {
                        calls.push({ loci, options });
                        return {
                            selection: { ref: "sel-1" },
                            representation: { ref: "repr-1" },
                        };
                    },
                },
            },
        },
        state: { data: {} },
    };

    const handler = new AnnotationHandlers(plugin, {
        getStructure: () => ({}) as any,
        registerRef: (ref?: string, tag?: string) => {
            if (ref) refs.push({ ref, tag });
        },
    });
    (handler as any).buildLociFromAtomIndices = () => ({
        structure: {},
        elements: [{ unit: { elements: [0, 1] }, indices: [0, 1] }],
    });

    await handler.addLabel({
        op: "add_label",
        tag: "notes",
        options: { text: "Catalytic Asp", atom_indices: [0, 1], tag: "notes" },
    });

    assert.strictEqual(calls.length, 1);
    assert.strictEqual(calls[0].options.selectionTags[0], "notes");
    assert.strictEqual(calls[0].options.reprTags[0], "notes");
    assert.strictEqual(calls[0].options.labelParams.customText, "Catalytic Asp");
    assert.deepStrictEqual(refs, [
        { ref: "sel-1", tag: "notes" },
        { ref: "repr-1", tag: "notes" },
    ]);
});

test("AnnotationHandlers.addLabel forwards style as visualParams to Mol*", async () => {
    const calls: any[] = [];
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(loci: any, options: any) {
                        calls.push({ loci, options });
                        return { selection: { ref: "sel-1" }, representation: { ref: "repr-1" } };
                    },
                },
            },
        },
        state: { data: {} },
    };

    const handler = new AnnotationHandlers(plugin, {
        getStructure: () => ({}) as any,
        registerRef: () => void 0,
    });
    (handler as any).buildLociFromAtomIndices = () => ({ structure: {}, elements: [] });

    await handler.addLabel({
        op: "add_label",
        tag: "styled",
        options: {
            text: "Label",
            atom_indices: [0],
            tag: "styled",
            style: { color: "#FF0000", size_em: 1.5, background: true, background_opacity: 0.7 },
        },
    });

    assert.strictEqual(calls.length, 1);
    const vp = calls[0].options.visualParams;
    assert.ok(vp !== undefined, "visualParams should be set");
    assert.strictEqual(vp.tooltip, "styled");
    assert.strictEqual(typeof vp.textColor, "number");
    assert.strictEqual(vp.textSize, 1.5);
    assert.strictEqual(vp.background, true);
    assert.strictEqual(vp.backgroundOpacity, 0.7);
});

test("AnnotationHandlers.addLabel without style passes only tooltip in visualParams", async () => {
    const calls: any[] = [];
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(loci: any, options: any) {
                        calls.push({ loci, options });
                        return { selection: { ref: "sel-1" }, representation: { ref: "repr-1" } };
                    },
                },
            },
        },
        state: { data: {} },
    };

    const handler = new AnnotationHandlers(plugin, {
        getStructure: () => ({}) as any,
        registerRef: () => void 0,
    });
    (handler as any).buildLociFromAtomIndices = () => ({ structure: {}, elements: [] });

    await handler.addLabel({
        op: "add_label",
        tag: "plain",
        options: { text: "Label", atom_indices: [0], tag: "plain" },
    });

    assert.strictEqual(calls.length, 1);
    const vp = calls[0].options.visualParams;
    assert.ok(vp !== undefined, "visualParams should be set (tooltip required for pickability)");
    assert.strictEqual(vp.tooltip, "plain");
    assert.strictEqual(vp.textColor, undefined);
    assert.strictEqual(vp.textSize, undefined);
});

test("AnnotationHandlers.setVisibility hides all annotations sharing a layer_tag", async () => {
    const addCalls: string[] = [];
    const removeCalls: string[] = [];
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(_loci: any, _options: any) {
                        const ref = `sel-${addCalls.length}`;
                        addCalls.push(ref);
                        return { selection: { ref }, representation: { ref: `repr-${addCalls.length - 1}` } };
                    },
                },
            },
        },
        state: { data: {} },
    };
    const { PluginCommands } = await import("molstar/lib/mol-plugin/commands");
    const originalRemove = PluginCommands.State.RemoveObject;
    (PluginCommands.State as any).RemoveObject = async (_plugin: any, params: any) => {
        removeCalls.push(params.ref);
    };

    try {
        const handler = new AnnotationHandlers(plugin, {
            getStructure: () => ({}) as any,
            registerRef: () => void 0,
        });
        (handler as any).buildLociFromAtomIndices = () => ({
            structure: {},
            elements: [{ unit: { elements: [0] }, indices: [0] }],
        });

        await handler.addLabel({
            op: "add_label",
            tag: "ann-a",
            options: { text: "A", atom_indices: [0], tag: "ann-a", layer_tag: "analysis" },
        });
        await handler.addLabel({
            op: "add_label",
            tag: "ann-b",
            options: { text: "B", atom_indices: [0], tag: "ann-b", layer_tag: "analysis" },
        });

        // Hiding the shared layer should hide both annotations.
        await handler.setVisibility("analysis", false);
        assert.strictEqual(removeCalls.length, 4, "both sel + repr refs for ann-a and ann-b should be removed");

        // Showing the shared layer should re-add both annotations.
        const addCountBefore = addCalls.length;
        await handler.setVisibility("analysis", true);
        assert.strictEqual(addCalls.length - addCountBefore, 2, "both annotations should be rebuilt");
    } finally {
        (PluginCommands.State as any).RemoveObject = originalRemove;
    }
});

test("AnnotationHandlers.setVisibility rebuilds labels from stored spec", async () => {
    const addCalls: any[] = [];
    const removeCalls: any[] = [];
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(_loci: any, _options: any) {
                        addCalls.push(true);
                        return {
                            selection: { ref: "sel-1" },
                            representation: { ref: "repr-1" },
                        };
                    },
                },
            },
        },
        state: { data: {} },
    };
    const { PluginCommands } = await import("molstar/lib/mol-plugin/commands");
    const originalRemove = PluginCommands.State.RemoveObject;
    (PluginCommands.State as any).RemoveObject = async (_plugin: any, params: any) => {
        removeCalls.push(params.ref);
    };

    try {
        const handler = new AnnotationHandlers(plugin, {
            getStructure: () => ({}) as any,
            registerRef: () => void 0,
        });
        (handler as any).buildLociFromAtomIndices = () => ({
            structure: {},
            elements: [{ unit: { elements: [0, 1] }, indices: [0, 1] }],
        });

        await handler.addLabel({
            op: "add_label",
            tag: "notes",
            options: { text: "Catalytic Asp", atom_indices: [0, 1], tag: "notes" },
        });
        await handler.setVisibility("notes", false);
        await handler.setVisibility("notes", true);

        assert.deepStrictEqual(removeCalls, ["sel-1", "repr-1"]);
        assert.strictEqual(addCalls.length, 2);
    } finally {
        (PluginCommands.State as any).RemoveObject = originalRemove;
    }
});

test("AnnotationHandlers.updateLabel preserves layer and style when visibility rebuilds the label", async () => {
    const addCalls: Array<{ text: string; textColor?: number }> = [];
    const overlays: Array<{ layerTag?: string; color?: string }> = [];
    const removeCalls: string[] = [];
    let callCount = 0;
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(_loci: any, options: any) {
                        addCalls.push({
                            text: options.labelParams?.customText ?? "",
                            textColor: options.visualParams?.textColor,
                        });
                        const ref = `sel-${callCount}`;
                        callCount++;
                        return { selection: { ref }, representation: { ref: `repr-${callCount - 1}` } };
                    },
                },
            },
        },
        state: { data: {} },
    };
    const { PluginCommands } = await import("molstar/lib/mol-plugin/commands");
    const originalRemove = PluginCommands.State.RemoveObject;
    (PluginCommands.State as any).RemoveObject = async (_plugin: any, params: any) => {
        removeCalls.push(params.ref);
    };

    try {
        const handler = new AnnotationHandlers(plugin, {
            getStructure: () => ({}) as any,
            registerRef: () => void 0,
            addLabelOverlay: msg => overlays.push({
                layerTag: msg.options?.layer_tag,
                color: msg.options?.style?.color,
            }),
        });
        (handler as any).buildLociFromAtomIndices = () => ({
            structure: {},
            elements: [{ unit: { elements: [0] }, indices: [0] }],
        });

        await handler.addLabel({
            op: "add_label",
            tag: "ann",
            options: {
                text: "Original text",
                atom_indices: [0],
                tag: "ann",
                layer_tag: "notes",
                style: { color: "#123456" },
            },
        });
        assert.strictEqual(addCalls[0].text, "Original text");

        await handler.updateLabel({
            op: "update_label",
            tag: "ann",
            options: { text: "Updated text", atom_indices: [1] },
        });
        // updateLabel clears the old refs and re-adds; second addLabel call has new text
        assert.strictEqual(addCalls[1].text, "Updated text");

        // Spec should reflect the new text; hide + show rebuilds with new text
        await handler.setVisibility("ann", false);
        await handler.setVisibility("ann", true);
        assert.strictEqual(addCalls[2].text, "Updated text");
        assert.strictEqual(addCalls[2].textColor, 0x123456);
        assert.deepStrictEqual(overlays.at(-1), { layerTag: "notes", color: "#123456" });
    } finally {
        (PluginCommands.State as any).RemoveObject = originalRemove;
    }
});

test("AnnotationHandlers.getSpec returns stored text and atom_indices, undefined for unknown tags", async () => {
    const plugin: any = {
        managers: {
            structure: {
                measurement: {
                    async addLabel(_loci: any, _options: any) {
                        return { selection: { ref: "sel-1" }, representation: { ref: "repr-1" } };
                    },
                },
            },
        },
        state: { data: {} },
    };

    const handler = new AnnotationHandlers(plugin, {
        getStructure: () => ({}) as any,
        registerRef: () => void 0,
    });
    (handler as any).buildLociFromAtomIndices = () => ({ structure: {}, elements: [] });

    assert.strictEqual(handler.getSpec("nonexistent"), undefined);

    await handler.addLabel({
        op: "add_label",
        tag: "lbl",
        options: { text: "Pocket", atom_indices: [4, 5, 6], tag: "lbl" },
    });

    const spec = handler.getSpec("lbl");
    assert.ok(spec !== undefined, "getSpec must return spec after addLabel");
    assert.strictEqual(spec!.text, "Pocket");
    assert.deepStrictEqual(spec!.atom_indices, [4, 5, 6]);
});
