import assert from "node:assert";
import test from "node:test";

import { StateHandlers } from "../../src/managers/handlers/state-handlers";

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

test("state handler clears orphan default global representations before applying a new global representation", async () => {
    const removed: string[] = [];
    const structureRef = "structure-ref";
    const plugin: any = {
        managers: {
            structure: {
                hierarchy: {
                    current: {
                        structures: [
                            {
                                representations: [{ cell: { transform: { ref: "default-repr" } } }],
                                components: [],
                            },
                        ],
                    },
                },
            },
        },
        builders: {
            structure: {
                representation: {
                    async applyPreset(_ref: any, _preset: any, _params: any) {
                        return { representations: { main: { ref: "new-global-repr" } } };
                    },
                },
            },
        },
        state: {
            data: {
                cells: new Map([
                    ["default-repr", {}],
                    ["new-global-repr", {}],
                ]),
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: structureRef } as any),
        getCurrentStructureRef: () => structureRef as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    plugin.state.data.cells.has = (ref: string) => ref === "default-repr" || ref === "new-global-repr";
    (handler as any).removeStateObject = async (ref?: string) => {
        if (ref) removed.push(ref);
    };
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setGlobalRepresentation({
        op: "set_global_representation",
        preset: "auto",
        params: {},
    } as any);

    assert.deepStrictEqual(removed, ["default-repr"]);
    const globalReprs = (handler as any).globalReprs as Set<string>;
    assert.deepStrictEqual(Array.from(globalReprs), ["new-global-repr"]);
});

test("state handler captures initial global representations on structure load", async () => {
    const plugin: any = {
        managers: {
            structure: {
                hierarchy: {
                    current: {
                        structures: [
                            {
                                representations: [{ cell: { transform: { ref: "default-repr" } } }],
                                components: [],
                            },
                        ],
                    },
                },
            },
        },
        state: { data: {} },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" } as any),
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).ensureDefaultGlobalRepresentation = async () => {};
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.onStructureLoaded();

    const globalReprs = (handler as any).globalReprs as Set<string>;
    assert.deepStrictEqual(Array.from(globalReprs), ["default-repr"]);
});

test("state handler maps structural color_scheme to a Mol* color theme for direct global representations", async () => {
    const applied: any[] = [];
    const structureRef = "structure-ref";
    const plugin: any = {
        state: {
            data: {
                build() {
                    return {
                        to(ref: string) {
                            assert.strictEqual(ref, structureRef);
                            return {
                                apply(_transform: any, params: any, opts: any) {
                                    applied.push({ params, opts });
                                    return { ref: "repr-ref" };
                                },
                            };
                        },
                        async commit() {},
                    };
                },
                cells: new Map(),
            },
        },
        representation: {
            structure: {
                registry: {
                    default: { provider: { defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) } },
                    get: () => ({ name: "cartoon", defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) }),
                },
                themes: {
                    colorThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                    sizeThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                },
            },
        },
        managers: {
            structure: {
                hierarchy: {
                    current: { structures: [{ representations: [], components: [] }] },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: structureRef } as any),
        getCurrentStructureRef: () => structureRef as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setGlobalRepresentation({
        op: "set_global_representation",
        representation: "cartoon",
        params: { color_scheme: "secondary_structure_default" },
    } as any);

    assert.strictEqual(applied.length, 1);
    assert.strictEqual(applied[0].params.type.name, "cartoon");
    assert.strictEqual(applied[0].params.colorTheme.name, "secondary-structure");
    assert.deepStrictEqual(applied[0].opts, { tags: "global" });
});

test("state handler maps curated structural color and size schemes for direct global representations", async () => {
    const applied: any[] = [];
    const structureRef = "structure-ref";
    const plugin: any = {
        state: {
            data: {
                build() {
                    return {
                        to(ref: string) {
                            assert.strictEqual(ref, structureRef);
                            return {
                                apply(_transform: any, params: any, opts: any) {
                                    applied.push({ params, opts });
                                    return { ref: "repr-ref" };
                                },
                            };
                        },
                        async commit() {},
                    };
                },
                cells: new Map(),
            },
        },
        representation: {
            structure: {
                registry: {
                    default: { provider: { defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) } },
                    get: () => ({ name: "cartoon", defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) }),
                },
                themes: {
                    colorThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                    sizeThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                },
            },
        },
        managers: {
            structure: {
                hierarchy: {
                    current: { structures: [{ representations: [], components: [] }] },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: structureRef } as any),
        getCurrentStructureRef: () => structureRef as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setGlobalRepresentation({
        op: "set_global_representation",
        representation: "cartoon",
        params: { color_scheme: "residue_name", size_scheme: "physical" },
    } as any);

    assert.strictEqual(applied.length, 1);
    assert.strictEqual(applied[0].params.type.name, "cartoon");
    assert.strictEqual(applied[0].params.colorTheme.name, "residue-name");
    assert.strictEqual(applied[0].params.sizeTheme.name, "physical");
    assert.deepStrictEqual(applied[0].opts, { tags: "global" });
});

test("state handler accepts advanced Mol* color and size themes for direct global representations", async () => {
    const applied: any[] = [];
    const structureRef = "structure-ref";
    const plugin: any = {
        state: {
            data: {
                build() {
                    return {
                        to(ref: string) {
                            assert.strictEqual(ref, structureRef);
                            return {
                                apply(_transform: any, params: any, opts: any) {
                                    applied.push({ params, opts });
                                    return { ref: "repr-ref" };
                                },
                            };
                        },
                        async commit() {},
                    };
                },
                cells: new Map(),
            },
        },
        representation: {
            structure: {
                registry: {
                    default: { provider: { defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) } },
                    get: () => ({ name: "cartoon", defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) }),
                },
                themes: {
                    colorThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                    sizeThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                },
            },
        },
        managers: {
            structure: {
                hierarchy: {
                    current: { structures: [{ representations: [], components: [] }] },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: structureRef } as any),
        getCurrentStructureRef: () => structureRef as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setGlobalRepresentation({
        op: "set_global_representation",
        representation: "cartoon",
        params: {
            molstar_color_theme: { name: "residue-name", params: { saturation: 0 } },
            molstar_size_theme: { name: "uniform", params: { value: 2.0 } },
        },
    } as any);

    assert.strictEqual(applied.length, 1);
    assert.strictEqual(applied[0].params.colorTheme.name, "residue-name");
    assert.deepStrictEqual(applied[0].params.colorTheme.params, { saturation: 0 });
    assert.strictEqual(applied[0].params.sizeTheme.name, "uniform");
    assert.deepStrictEqual(applied[0].params.sizeTheme.params, { value: 2.0 });
});

test("state handler gives curated structural color and size schemes priority over advanced Mol* themes", async () => {
    const applied: any[] = [];
    const structureRef = "structure-ref";
    const plugin: any = {
        state: {
            data: {
                build() {
                    return {
                        to(ref: string) {
                            assert.strictEqual(ref, structureRef);
                            return {
                                apply(_transform: any, params: any, opts: any) {
                                    applied.push({ params, opts });
                                    return { ref: "repr-ref" };
                                },
                            };
                        },
                        async commit() {},
                    };
                },
                cells: new Map(),
            },
        },
        representation: {
            structure: {
                registry: {
                    default: { provider: { defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) } },
                    get: () => ({ name: "cartoon", defaultColorTheme: { name: "chain-id", props: {} }, defaultSizeTheme: { name: "uniform", props: {} }, getParams: () => ({}) }),
                },
                themes: {
                    colorThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                    sizeThemeRegistry: {
                        get: (name: string) => ({ name, getParams: () => ({}), defaultValues: {} }),
                    },
                },
            },
        },
        managers: {
            structure: {
                hierarchy: {
                    current: { structures: [{ representations: [], components: [] }] },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({ units: [] }) as any,
        getLoadedStructure: () => ({ structure: structureRef } as any),
        getCurrentStructureRef: () => structureRef as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setGlobalRepresentation({
        op: "set_global_representation",
        representation: "cartoon",
        params: {
            color_scheme: "secondary_structure_default",
            size_scheme: "physical",
            molstar_color_theme: "residue-name",
            molstar_size_theme: "uniform",
        },
    } as any);

    assert.strictEqual(applied.length, 1);
    assert.strictEqual(applied[0].params.colorTheme.name, "secondary-structure");
    assert.strictEqual(applied[0].params.sizeTheme.name, "physical");
});

test("state handler renameRegion preserves hidden state in the renamed entry", async () => {
    const plugin: any = { state: { data: {} } };
    const notifications: any[] = [];
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });

    // Inject a hidden region entry directly
    const regionIndex = (handler as any).regionIndex as Map<string, any>;
    regionIndex.set("pocket", {
        component: "comp-ref",
        representations: ["repr-ref"],
        atomIndices: [0, 1, 2],
        selection: undefined,
        hidden: true,
    });

    await handler.renameRegion({ op: "rename_region", tag: "pocket", new_tag: "binding-site" });

    assert.strictEqual(regionIndex.has("pocket"), false, "old tag must be removed");
    const renamed = regionIndex.get("binding-site");
    assert.ok(renamed !== undefined, "new tag must exist");
    assert.strictEqual(renamed.hidden, true, "hidden flag must be preserved after rename");
    assert.deepStrictEqual(notifications, [
        { event: "region_renamed", tag: "pocket", new_tag: "binding-site" },
    ]);
});

test("state handler createRegion without loaded structure queues to pendingRegions", async () => {
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    const msg = { op: "create_region" as const, tag: "site", atom_indices: [0, 1] };
    await handler.createRegion(msg);

    const pending = (handler as any).pendingRegions as any[];
    assert.strictEqual(pending.length, 1);
    assert.strictEqual(pending[0].tag, "site");
    assert.deepStrictEqual(pending[0].atom_indices, [0, 1]);
});
