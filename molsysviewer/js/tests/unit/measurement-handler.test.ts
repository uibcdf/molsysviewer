import assert from "node:assert";
import test from "node:test";

import { MeasurementHandlers } from "../../src/managers/handlers/measurement-handlers";

test("MeasurementHandlers delegates replayable distance measurement to Mol*", async () => {
    const calls: any[] = [];
    const fakeMeasurement = {
        async addDistance(a: any, b: any, opts: any) {
            calls.push({ a, b, opts });
            return {
                selection: { ref: "sel-ref" },
                representation: { ref: "repr-ref" },
            };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const registered: Array<{ ref?: string; tag?: string }> = [];
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: (ref, tag) => {
            registered.push({ ref: ref as any, tag });
        },
    });
    (handlers as any).buildLociFromAtomIndices = (_structure: any, atomIndices: number[]) => ({ atomIndices });

    await handlers.addDistance({
        op: "add_distance_measurement",
        tag: "m1",
        options: {
            tag: "m1",
            picks_atom_indices: [[0], [1]],
        },
    });

    assert.strictEqual(calls.length, 1);
    assert.deepStrictEqual(calls[0].opts.selectionTags, ["m1"]);
    assert.deepStrictEqual(calls[0].opts.reprTags, ["m1"]);
    assert.deepStrictEqual(registered, [
        { ref: "sel-ref", tag: "m1" },
        { ref: "repr-ref", tag: "m1" },
    ]);
});

test("MeasurementHandlers.setVisibility rebuilds persisted measurements from stored spec", async () => {
    const calls: any[] = [];
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, _opts: any) {
            calls.push(true);
            return {
                selection: { ref: "sel-ref" },
                representation: { ref: "repr-ref" },
            };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const { PluginCommands } = await import("molstar/lib/mol-plugin/commands");
    const removed: string[] = [];
    const originalRemove = PluginCommands.State.RemoveObject;
    (PluginCommands.State as any).RemoveObject = async (_plugin: any, params: any) => {
        removed.push(params.ref);
    };

    try {
        const handlers = new MeasurementHandlers(plugin, {
            getStructure: () => ({ units: [] } as any),
            registerRef: () => void 0,
        });
        (handlers as any).buildLociFromAtomIndices = (_structure: any, atomIndices: number[]) => ({ atomIndices });

        await handlers.addDistance({
            op: "add_distance_measurement",
            tag: "m1",
            options: {
                tag: "m1",
                picks_atom_indices: [[0], [1]],
            },
        });

        await handlers.setVisibility("m1", false);
        await handlers.setVisibility("m1", true);

        assert.deepStrictEqual(removed, ["sel-ref", "repr-ref"]);
        assert.strictEqual(calls.length, 2);
    } finally {
        (PluginCommands.State as any).RemoveObject = originalRemove;
    }
});

test("MeasurementHandlers can rename and drop measurement tags", async () => {
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, _opts: any) {
            return {
                selection: { ref: "sel-ref" },
                representation: { ref: "repr-ref" },
            };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });
    (handlers as any).buildLociFromAtomIndices = (_structure: any, atomIndices: number[]) => ({ atomIndices });

    await handlers.addDistance({
        op: "add_distance_measurement",
        tag: "m1",
        options: {
            tag: "m1",
            picks_atom_indices: [[0], [1]],
        },
    });

    assert.strictEqual(handlers.hasTag("m1"), true);
    handlers.renameTag("m1", "m2");
    assert.strictEqual(handlers.hasTag("m1"), false);
    assert.strictEqual(handlers.hasTag("m2"), true);
    handlers.dropTag("m2");
    assert.strictEqual(handlers.hasTag("m2"), false);
});

test("MeasurementHandlers resolves representative atoms from molsys_group_type metadata", () => {
    const plugin = { managers: { structure: { measurement: {} } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });

    (handlers as any).modelForAtomIndex = (_structure: any, atomIndex: number) => ({
        atomicHierarchy: {
            atoms: {
                label_atom_id: {
                    value: (index: number) => {
                        const names: Record<number, string> = { 10: "N", 11: "CA", 12: "C", 20: "O1", 21: "P", 22: "O2" };
                        return names[index];
                    },
                },
                molsys_group_type: {
                    value: (index: number) => {
                        const types: Record<number, string> = { 10: "amino acid", 11: "amino acid", 12: "amino acid", 20: "lipid", 21: "lipid", 22: "lipid" };
                        return types[index];
                    },
                },
            },
        },
    });

    const protein = handlers.buildMeasurementOptions([[10, 11, 12], [21]], "representative_atom");
    assert.deepStrictEqual(protein.endpoint_kinds, ["representative_atom", "atom"]);
    assert.deepStrictEqual(protein.endpoint_labels, ["CA", "P"]);
    assert.deepStrictEqual(protein.endpoint_atom_indices, [[11], [21]]);

    const lipid = handlers.buildMeasurementOptions([[20, 21, 22]], "representative_atom");
    assert.deepStrictEqual(lipid.endpoint_labels, ["P"]);
    assert.deepStrictEqual(lipid.endpoint_atom_indices, [[21]]);
});
