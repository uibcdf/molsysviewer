import assert from "node:assert";
import test from "node:test";

import { LoaderHandlers } from "../../src/managers/handlers/loader-handlers";
import { withWarnCapture } from "./helpers";

test("loader handlers reject invalid payloads without triggering callbacks", async () => {
    const plugin: any = {};
    const calls: string[] = [];
    const callbacks = {
        clearGlobalRepresentations: async () => {
            calls.push("clear");
        },
        captureCurrentStructure: () => {
            calls.push("capture");
        },
        setLoadedStructure: (_ls: any) => {
            calls.push("setLoaded");
        },
        getLoadedStructure: () => undefined,
        setExpectedFrameCount: (_n: number | undefined) => {
            calls.push("setExpected");
        },
    };
    const handler = new LoaderHandlers(plugin, callbacks);

    await withWarnCapture(async (warnings) => {
        await handler.loadFromString({ op: "load_structure_from_string" } as any);
        await handler.loadMolSysPayload({ op: "load_molsys_payload" } as any);
        await handler.loadFromUrl({ op: "load_structure_from_url", url: "" } as any);
        await handler.loadPdbId({ op: "load_pdb_id", pdb_id: "   " } as any);

        assert.strictEqual(warnings.length, 4);
        assert.ok(warnings.some((w) => w.includes("load message without data/pdb/pdb_text")));
        assert.ok(warnings.some((w) => w.includes("load_molsys_payload without payload")));
        assert.ok(warnings.some((w) => w.includes("load_structure_from_url without url")));
        assert.ok(warnings.some((w) => w.includes("load_pdb_id without pdb_id")));
    });

    assert.deepStrictEqual(calls, []);
});

test("loader handlers forward valid inputs to internal methods with defaults", async () => {
    const plugin: any = {};
    const callbacks = {
        clearGlobalRepresentations: async () => {},
        captureCurrentStructure: () => {},
        setLoadedStructure: (_ls: any) => {},
        getLoadedStructure: () => undefined,
        setExpectedFrameCount: (_n: number | undefined) => {},
    };
    const handler: any = new LoaderHandlers(plugin, callbacks);

    const observed: Array<{ method: string; args: any[] }> = [];
    handler.loadFromStringInternal = async (...args: any[]) => {
        observed.push({ method: "loadFromStringInternal", args });
    };
    handler.loadFromUrlInternal = async (...args: any[]) => {
        observed.push({ method: "loadFromUrlInternal", args });
    };
    handler.loadFromMolSysPayloadInternal = async (...args: any[]) => {
        observed.push({ method: "loadFromMolSysPayloadInternal", args });
    };

    await handler.loadFromString({
        op: "load_structure_from_string",
        pdb_text: "ATOM ...",
    });
    await handler.loadFromUrl({
        op: "load_structure_from_url",
        url: "https://example.org/a.pdb",
    });
    await handler.loadMolSysPayload({
        op: "load_molsys_payload",
        payload: { atoms: { atom_id: [1] }, structures: [{ coordinates: [[0, 0, 0]] }] } as any,
        label: "payload-label",
    });
    await handler.loadPdbId({
        op: "load_pdb_id",
        pdb_id: " 1tcd ",
    });

    assert.deepStrictEqual(observed[0], {
        method: "loadFromStringInternal",
        args: ["ATOM ...", "pdb", "Structure"],
    });
    assert.deepStrictEqual(observed[1], {
        method: "loadFromUrlInternal",
        args: ["https://example.org/a.pdb", undefined, undefined],
    });
    assert.deepStrictEqual(observed[2], {
        method: "loadFromMolSysPayloadInternal",
        args: [{ atoms: { atom_id: [1] }, structures: [{ coordinates: [[0, 0, 0]] }] }, "payload-label"],
    });
    assert.deepStrictEqual(observed[3], {
        method: "loadFromUrlInternal",
        args: ["https://files.rcsb.org/download/1TCD.pdb", "pdb", "PDB 1TCD"],
    });
});
