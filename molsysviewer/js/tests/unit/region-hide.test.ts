import assert from "node:assert";
import test from "node:test";
import { LoaderHandlers } from "../../src/managers/handlers/loader-handlers";
import { SceneHandlers } from "../../src/managers/handlers/scene-handlers";
import { StateHandlers } from "../../src/managers/handlers/state-handlers";
import { TrajectoryHandlers } from "../../src/managers/handlers/trajectory-handlers";

function makeTrajectoryPluginMock() {
    return {
        managers: {
            animation: {
                isAnimating: false,
                stop() {
                    return;
                },
            },
        },
        state: {
            data: {
                selectQ() {
                    return [];
                },
            },
        },
    };
}

function withWarnCapture<T>(fn: (warnings: string[]) => Promise<T> | T): Promise<T> | T {
    const originalWarn = console.warn;
    const warnings: string[] = [];
    console.warn = (...args: any[]) => {
        warnings.push(args.map(String).join(" "));
    };
    const finalize = () => {
        console.warn = originalWarn;
    };
    try {
        const out = fn(warnings);
        if (out && typeof (out as Promise<T>).then === "function") {
            return (out as Promise<T>).finally(finalize);
        }
        finalize();
        return out;
    } catch (err) {
        finalize();
        throw err;
    }
}

test("trajectory handler exposes expected frame count before structure is ready", () => {
    const plugin: any = makeTrajectoryPluginMock();
    const handler = new TrajectoryHandlers(plugin, {
        getLoadedStructure: () => undefined,
        notifyTrajectoryState: () => {},
    });

    const observed: Array<{ frameCount: number; hasTrajectory: boolean }> = [];
    handler.onTrajectoryState(
        (state) => observed.push({ frameCount: state.frameCount, hasTrajectory: state.hasTrajectory }),
        { immediate: false },
    );

    handler.setExpectedFrameCount(5);

    assert.strictEqual(observed.length, 1);
    assert.strictEqual(observed[0].frameCount, 5);
    assert.strictEqual(observed[0].hasTrajectory, false);
});

test("state handler emits layer ack and keeps metadata through retag", async () => {
    const notifications: any[] = [];
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });

    await handler.createLayer({
        op: "create_layer",
        tag: "layer-a",
        kind: "shape",
        meta: { source: "unit-test" },
    });

    assert.deepStrictEqual(notifications, [
        { event: "layer_ack", tag: "layer-a", kind: "shape", meta: { source: "unit-test" } },
    ]);

    await handler.setLayerTag({
        op: "set_layer_tag",
        tag: "layer-a",
        new_tag: "layer-b",
    });

    const layerMeta = (handler as any).layerMeta as Map<string, any>;
    assert.strictEqual(layerMeta.has("layer-a"), false);
    assert.strictEqual(layerMeta.has("layer-b"), true);
    assert.deepStrictEqual(layerMeta.get("layer-b"), { kind: "shape", meta: { source: "unit-test" } });
});

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

test("scene clearScene obeys option flags and clearAll emits registry reset", async () => {
    const plugin: any = {};
    const events: any[] = [];
    const calls = {
        clearShapes: 0,
        clearLabels: 0,
        clearShapesByTag: 0,
        removeLoadedStructure: 0,
    };
    const handler = new SceneHandlers(plugin, {} as any, {
        clearShapes: async () => {
            calls.clearShapes += 1;
        },
        clearLabels: async () => {
            calls.clearLabels += 1;
        },
        getComponents: () => [],
        clearShapesByTag: async (_tag?: string) => {
            calls.clearShapesByTag += 1;
        },
        removeLoadedStructure: async () => {
            calls.removeLoadedStructure += 1;
        },
        notify: (msg: any) => events.push(msg),
    });

    await handler.clearScene({ op: "clear_scene", options: { shapes: true, styles: false, labels: true } });
    assert.strictEqual(calls.clearShapes, 1);
    assert.strictEqual(calls.clearLabels, 1);

    await handler.clearShapesByTag({ op: "clear_shapes_by_tag", tag: "layer-x" });
    assert.strictEqual(calls.clearShapesByTag, 1);

    await handler.clearAll();
    assert.strictEqual(calls.removeLoadedStructure, 1);
    assert.ok(events.some((e) => e?.event === "registry_cleared"));
});

test("scene toggles spin and swing with mutual exclusion", async () => {
    const setPropsCalls: any[] = [];
    const plugin: any = {
        canvas3d: {
            props: {
                trackball: { animate: { name: "off", params: {} } },
            },
            setProps: (props: any) => {
                setPropsCalls.push(props);
            },
        },
    };
    const handler = new SceneHandlers(plugin, {} as any, {
        clearShapes: async () => {},
        clearLabels: async () => {},
        getComponents: () => [],
        clearShapesByTag: async () => {},
        removeLoadedStructure: async () => {},
        notify: (_msg: any) => {},
    });

    await handler.toggleSpin(true);
    assert.strictEqual(handler.isSpinActive, true);
    assert.strictEqual(handler.isSwingActive, false);

    await handler.toggleSwing(true);
    assert.strictEqual(handler.isSpinActive, false);
    assert.strictEqual(handler.isSwingActive, true);

    const animateNames = setPropsCalls
        .map((p) => p?.trackball?.animate?.name)
        .filter((x) => typeof x === "string");
    assert.ok(animateNames.includes("spin"));
    assert.ok(animateNames.includes("rock"));
});

test("state handler stores pending layer visibility when layer refs do not exist", async () => {
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    await handler.hideLayer({ op: "hide_layer", tag: "layer-pending" });
    const pending = (handler as any).pendingLayerVisibility as Map<string, boolean>;
    assert.strictEqual(pending.get("layer-pending"), true);

    await handler.showLayer({ op: "show_layer", tag: "layer-pending" });
    assert.strictEqual(pending.get("layer-pending"), false);
});

test("state handler queues global visibility ops when structure is not ready", async () => {
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    await handler.hideGlobal({ op: "hide_global" });
    const pendingOpsA = (handler as any).pendingGlobalOps as Array<{ hide: boolean; target: string }>;
    const requestedA = (handler as any).requestedGlobalHidden as boolean | null;
    assert.strictEqual(pendingOpsA.length, 1);
    assert.deepStrictEqual(pendingOpsA[0], { hide: true, target: "global" });
    assert.strictEqual(requestedA, true);

    await handler.showGlobal({ op: "show_global", target: "all" });
    const pendingOpsB = (handler as any).pendingGlobalOps as Array<{ hide: boolean; target: string }>;
    const requestedB = (handler as any).requestedGlobalHidden as boolean | null;
    assert.strictEqual(pendingOpsB.length, 2);
    assert.deepStrictEqual(pendingOpsB[1], { hide: false, target: "all" });
    // target=all should not overwrite requestedGlobalHidden
    assert.strictEqual(requestedB, true);
});

test("state handler registerShapeRef indexes ref and emits layer ack for new tag", () => {
    const notifications: any[] = [];
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });

    handler.registerShapeRef("ref-1" as any, "shape-tag");

    const tagIndex = (handler as any).tagIndex as Map<string, Set<any>>;
    const layerMeta = (handler as any).layerMeta as Map<string, any>;
    assert.strictEqual(tagIndex.has("shape-tag"), true);
    assert.strictEqual(tagIndex.get("shape-tag")?.has("ref-1"), true);
    assert.strictEqual(layerMeta.has("shape-tag"), true);
    assert.deepStrictEqual(notifications, [
        { event: "layer_ack", tag: "shape-tag", kind: "shape", meta: {} },
    ]);
});

test("scene toggleBackground flips dark mode and reuses cached renderer snapshots", async () => {
    const setPropsCalls: any[] = [];
    const plugin: any = {
        canvas3d: {
            props: {
                renderer: { backgroundColor: 0xffffff, lightIntensity: 0.8, ambientIntensity: 0.6 },
                camera: { radius: 12 },
            },
            setProps: (props: any) => setPropsCalls.push(props),
        },
    };
    const handler = new SceneHandlers(plugin, {} as any, {
        clearShapes: async () => {},
        clearLabels: async () => {},
        getComponents: () => [],
        clearShapesByTag: async () => {},
        removeLoadedStructure: async () => {},
        notify: (_msg: any) => {},
    });

    await handler.toggleBackground("dark");
    assert.strictEqual(handler.isDarkMode, true);
    const darkRenderer = setPropsCalls[0]?.renderer ?? {};
    assert.strictEqual(darkRenderer.backgroundColor, 0x101010);

    await handler.toggleBackground("light");
    assert.strictEqual(handler.isDarkMode, false);
    const lightRenderer = setPropsCalls[1]?.renderer ?? {};
    assert.strictEqual(lightRenderer.backgroundColor, 0xffffff);
});
