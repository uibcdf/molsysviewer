import assert from "node:assert";
import test from "node:test";

import { AnnotationHandlers } from "../../src/managers/handlers/annotation-handlers";

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
