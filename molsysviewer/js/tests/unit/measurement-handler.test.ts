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

test("MeasurementHandlers.addDistance forwards style as visualParams with tooltip tag", async () => {
    const calls: any[] = [];
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, opts: any) {
            calls.push(opts);
            return { selection: { ref: "sel-ref" }, representation: { ref: "repr-ref" } };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });
    (handlers as any).buildLociFromAtomIndices = (_s: any, ai: number[]) => ({ ai });

    await handlers.addDistance({
        op: "add_distance_measurement",
        tag: "d1",
        options: { tag: "d1", picks_atom_indices: [[0], [1]], style: { color: "#00FF00", size_em: 1.2 } },
    });

    assert.strictEqual(calls.length, 1);
    const vp = calls[0].visualParams;
    assert.ok(vp !== undefined, "visualParams must be set");
    assert.strictEqual(vp.tooltip, "d1");
    assert.strictEqual(typeof vp.textColor, "number");
    assert.strictEqual(vp.textSize, 1.2);
});

test("MeasurementHandlers.addDistance without style still passes tooltip in visualParams", async () => {
    const calls: any[] = [];
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, opts: any) {
            calls.push(opts);
            return { selection: { ref: "sel-ref" }, representation: { ref: "repr-ref" } };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });
    (handlers as any).buildLociFromAtomIndices = (_s: any, ai: number[]) => ({ ai });

    await handlers.addDistance({
        op: "add_distance_measurement",
        tag: "d2",
        options: { tag: "d2", picks_atom_indices: [[0], [1]] },
    });

    assert.strictEqual(calls.length, 1);
    const vp = calls[0].visualParams;
    assert.ok(vp !== undefined, "visualParams must be set for pickability");
    assert.strictEqual(vp.tooltip, "d2");
    assert.strictEqual(vp.textColor, undefined);
});

test("MeasurementHandlers.setVisibility hides all measurements sharing a layer_tag", async () => {
    const addCalls: string[] = [];
    const removeCalls: string[] = [];
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, _opts: any) {
            const ref = `sel-${addCalls.length}`;
            addCalls.push(ref);
            return { selection: { ref }, representation: { ref: `repr-${addCalls.length - 1}` } };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const { PluginCommands } = await import("molstar/lib/mol-plugin/commands");
    const originalRemove = PluginCommands.State.RemoveObject;
    (PluginCommands.State as any).RemoveObject = async (_plugin: any, params: any) => {
        removeCalls.push(params.ref);
    };

    try {
        const handlers = new MeasurementHandlers(plugin, {
            getStructure: () => ({ units: [] } as any),
            registerRef: () => void 0,
        });
        (handlers as any).buildLociFromAtomIndices = (_s: any, ai: number[]) => ({ ai });

        await handlers.addDistance({ op: "add_distance_measurement", tag: "d-a", options: { tag: "d-a", picks_atom_indices: [[0], [1]], layer_tag: "bond_lengths" } });
        await handlers.addDistance({ op: "add_distance_measurement", tag: "d-b", options: { tag: "d-b", picks_atom_indices: [[2], [3]], layer_tag: "bond_lengths" } });

        await handlers.setVisibility("bond_lengths", false);
        assert.strictEqual(removeCalls.length, 4, "sel + repr for both measurements should be removed");

        const addCountBefore = addCalls.length;
        await handlers.setVisibility("bond_lengths", true);
        assert.strictEqual(addCalls.length - addCountBefore, 2, "both measurements should be rebuilt");
    } finally {
        (PluginCommands.State as any).RemoveObject = originalRemove;
    }
});

test("MeasurementHandlers.getSpec returns kind and flattened atom indices", async () => {
    const fakeMeasurement = {
        async addDistance(_a: any, _b: any, _opts: any) {
            return { selection: { ref: "sel-ref" }, representation: { ref: "repr-ref" } };
        },
    };
    const plugin = { managers: { structure: { measurement: fakeMeasurement } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });
    (handlers as any).buildLociFromAtomIndices = (_s: any, ai: number[]) => ({ ai });

    await handlers.addDistance({
        op: "add_distance_measurement",
        tag: "d3",
        options: { tag: "d3", picks_atom_indices: [[5], [9]], endpoint_atom_indices: [[5], [9]] },
    });

    const spec = handlers.getSpec("d3");
    assert.ok(spec !== undefined);
    assert.strictEqual(spec!.kind, "distance");
    assert.deepStrictEqual(spec!.atom_indices, [5, 9]);
    assert.strictEqual(handlers.getSpec("nonexistent"), undefined);
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

test("MeasurementHandlers.buildMeasurementOptions with centroid policy resolves multi-atom pick to centroid kind", () => {
    const plugin = { managers: { structure: { measurement: {} } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });

    // Multi-atom pick under centroid policy → endpoint_kind "centroid", empty atom_indices
    const result = handlers.buildMeasurementOptions([[0, 1, 2], [3]], "centroid");
    assert.deepStrictEqual(result.endpoint_kinds, ["centroid", "atom"]);
    assert.deepStrictEqual(result.endpoint_atom_indices, [[], [3]]);
    assert.deepStrictEqual(result.endpoint_labels, ["centroid", "atom"]);

    // Single-atom pick is always "atom" regardless of policy
    const single = handlers.buildMeasurementOptions([[5]], "centroid");
    assert.deepStrictEqual(single.endpoint_kinds, ["atom"]);
    assert.deepStrictEqual(single.endpoint_atom_indices, [[5]]);
});

test("MeasurementHandlers.setSettings switches centroid vs representative_atom for multi-atom picks", () => {
    const plugin = { managers: { structure: { measurement: {} } }, state: { data: {} } } as any;
    const handlers = new MeasurementHandlers(plugin, {
        getStructure: () => ({ units: [] } as any),
        registerRef: () => void 0,
    });
    (handlers as any).modelForAtomIndex = (_structure: any, atomIndex: number) => ({
        atomicHierarchy: {
            atoms: {
                label_atom_id: {
                    value: (i: number) => ({ 10: "N", 11: "CA", 12: "CB" }[i] ?? ""),
                },
                molsys_group_type: { value: () => "amino acid" },
            },
        },
    });

    // Default policy is centroid; multi-atom pick → centroid
    const defaultResult = handlers.buildMeasurementOptions([[10, 11, 12]]);
    assert.deepStrictEqual(defaultResult.endpoint_kinds, ["centroid"]);
    assert.deepStrictEqual(defaultResult.endpoint_atom_indices, [[]]);

    // Switch to representative_atom; multi-atom pick → representative_atom (CA for protein)
    handlers.setSettings({ endpoint_policy_default: "representative_atom" });
    const reprResult = handlers.buildMeasurementOptions([[10, 11, 12]]);
    assert.deepStrictEqual(reprResult.endpoint_kinds, ["representative_atom"]);
    assert.deepStrictEqual(reprResult.endpoint_atom_indices, [[11]]); // CA

    // Custom representative_atoms: override protein CA → CB
    handlers.setSettings({ representative_atoms: { protein: "CB" } });
    const custom = handlers.buildMeasurementOptions([[10, 11, 12]]);
    assert.deepStrictEqual(custom.endpoint_atom_indices, [[12]]); // CB
    assert.deepStrictEqual(custom.endpoint_labels, ["CB"]);

    // Switch back to centroid; custom rep_atoms no longer used for multi-atom
    handlers.setSettings({ endpoint_policy_default: "centroid" });
    const backToCentroid = handlers.buildMeasurementOptions([[10, 11, 12]]);
    assert.deepStrictEqual(backToCentroid.endpoint_kinds, ["centroid"]);
});
