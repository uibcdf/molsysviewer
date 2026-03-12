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
