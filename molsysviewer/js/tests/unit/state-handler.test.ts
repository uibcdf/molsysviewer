import assert from "node:assert";
import test from "node:test";

import { StructureElement } from "molstar/lib/mol-model/structure";
import { StateHandlers } from "../../src/managers/handlers/state-handlers";

test("visibility delta applies on matching version and self-heals on drift", async () => {
    const notifications: any[] = [];
    const plugin: any = { state: { data: {} } };
    const handler = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });
    const resyncCount = () => notifications.filter((n) => n?.event === "request_visibility_resync").length;

    // Full sync establishes the version baseline (version 1).
    await handler.updateVisibility({ op: "update_visibility", options: { visible_atom_indices: [0, 1, 2], version: 1 } });

    // A delta on top of the held version applies and advances the version to 2.
    await handler.updateVisibilityDelta({ op: "update_visibility_delta", options: { base_version: 1, version: 2, shown: [3], hidden: [0] } });
    assert.strictEqual(resyncCount(), 0);

    // Re-sending the stale delta (base_version 1) no longer matches: drift detected,
    // a resync is requested rather than applying blindly.
    await handler.updateVisibilityDelta({ op: "update_visibility_delta", options: { base_version: 1, version: 2, shown: [3], hidden: [0] } });
    assert.strictEqual(resyncCount(), 1);

    // A delta against the current version (2) applies cleanly again.
    await handler.updateVisibilityDelta({ op: "update_visibility_delta", options: { base_version: 2, version: 3, shown: [4], hidden: [] } });
    assert.strictEqual(resyncCount(), 1);

    // A delta arriving before any full state also asks for a resync.
    const fresh = new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (msg: any) => notifications.push(msg),
    });
    await fresh.updateVisibilityDelta({ op: "update_visibility_delta", options: { base_version: 0, version: 1, shown: [1], hidden: [] } });
    assert.strictEqual(notifications.filter((n) => n?.event === "request_visibility_resync").length, 2);
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

test("state handler applies one batch region visibility message to every tag", async () => {
    const handler = new StateHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    const calls: Array<{ tag: string | undefined; hidden: boolean }> = [];
    (handler as any).toggleRegionVisibility = async (tag: string | undefined, hidden: boolean) => {
        calls.push({ tag, hidden });
    };

    await handler.setRegionsVisibility({
        op: "set_regions_visibility",
        tags: ["first", "second"],
        hidden: true,
    });

    assert.deepStrictEqual(calls, [
        { tag: "first", hidden: true },
        { tag: "second", hidden: true },
    ]);
});

test("state handler accepts authoritative enriched region summaries", () => {
    const handler = new StateHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    handler.setRegionSummaries({
        op: "set_region_summaries",
        representations: ["line", "cartoon"],
        presets: ["auto"],
        regions: [{
            tag: "site",
            atom_indices: [0, 1],
            atom_count: 2,
            hidden: false,
            layer: "analysis",
            representation: "line",
            preset: null,
            representation_params: { alpha: 0.5 },
            overlap_tags: ["backbone"],
            available_attributes: ["b_factor"],
        }],
    });

    assert.deepStrictEqual(handler.getRegionSummaries(), [{
        tag: "site",
        atom_indices: [0, 1],
        atom_count: 2,
        hidden: false,
        // Layer membership (Phase 9) must survive the summary mapping so the
        // Layers subpanel can group the region under its layer.
        layer: "analysis",
        representation: "line",
        preset: undefined,
        selection: undefined,
        representation_params: { alpha: 0.5 },
        overlap_tags: ["backbone"],
        available_attributes: ["b_factor"],
        mode: "static",
        frame_dependent: false,
    }]);
    assert.deepStrictEqual(handler.getRegionStyleOptions(), {
        representations: ["line", "cartoon"],
        presets: ["auto"],
    });
});

test("state handler tracks dynamic frame-dependent summaries for request gating", () => {
    const handler = new StateHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });

    handler.setRegionSummaries({
        op: "set_region_summaries",
        regions: [
            { tag: "topological", atom_count: 3, hidden: false, mode: "dynamic", frame_dependent: false },
        ],
    });
    assert.strictEqual(handler.hasFrameDependentDynamicRegions(), false);

    handler.setRegionSummaries({
        op: "set_region_summaries",
        regions: [
            { tag: "shell", atom_count: 3, hidden: false, mode: "dynamic", frame_dependent: true },
        ],
    });
    assert.strictEqual(handler.hasFrameDependentDynamicRegions(), true);
});

test("state handler applies consolidated dynamic region atom deltas", async () => {
    const handler = new StateHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    const regionIndex = (handler as any).regionIndex as Map<string, any>;
    regionIndex.set("shell", {
        atomIndices: [0],
        representations: [],
        representationState: "none",
        params: {},
        order: 0,
    });
    const updates: Array<{ tag: string; atoms: number[] }> = [];
    (handler as any).updateRegionComponentAtomIndices = async (tag: string, entry: any, atoms: number[]) => {
        entry.atomIndices = [...atoms];
        updates.push({ tag, atoms: [...atoms] });
    };

    await handler.setDynamicRegionAtoms({
        op: "set_dynamic_region_atoms",
        frame: 7,
        regions: [
            { tag: "shell", atom_indices: [2, 3] },
            { tag: "missing", atom_indices: [9] },
        ],
    });

    assert.deepStrictEqual(updates, [{ tag: "shell", atoms: [2, 3] }]);
    assert.deepStrictEqual(regionIndex.get("shell").atomIndices, [2, 3]);
});

test("state handler applies batched region operations in order", async () => {
    const handler = new StateHandlers({ state: { data: {} } } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    const calls: string[] = [];
    (handler as any).createRegion = async (message: any) => calls.push(`create:${message.tag}`);
    (handler as any).setRegionRepresentation = async (message: any) => calls.push(`style:${message.tag}`);

    await handler.applyRegionOperations({
        op: "batch_region_operations",
        operations: [
            { op: "create_region", tag: "A", atom_indices: [0] },
            { op: "set_region_representation", tag: "A", representation: "line" },
            { op: "create_region", tag: "B", atom_indices: [1] },
        ],
    });

    assert.deepStrictEqual(calls, ["create:A", "style:A", "create:B"]);
});

test("state handler styles a newly-created bare region without rebuilding its component", async () => {
    const originalFromSelection = StructureElement.Bundle.fromSelection;
    let componentCommits = 0;
    let representationAdds = 0;
    const plugin: any = {
        state: {
            data: {
                cells: { has: () => true },
                build: () => ({
                    to: (_ref: unknown) => ({
                        apply: (_transform: unknown, _params: unknown) => ({
                            selector: { ref: "component-ref", isOk: true },
                            async commit(_options: unknown) {
                                componentCommits += 1;
                            },
                        }),
                    }),
                }),
            },
        },
        builders: {
            structure: {
                representation: {
                    async addRepresentation(_componentRef: unknown, spec: any, options: any) {
                        representationAdds += 1;
                        assert.strictEqual(_componentRef, "component-ref");
                        assert.deepStrictEqual(spec, {
                            type: "line",
                            typeParams: {},
                            color: "uniform",
                            colorParams: { value: 16711680 },
                        });
                        assert.deepStrictEqual(options, { tag: "site" });
                        return { ref: "repr-ref" };
                    },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({}) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).buildSelectionFromAtomIndices = () => ({ fake: "selection" });
    (StructureElement.Bundle as any).fromSelection = (_selection: unknown) => ({ fake: "bundle" });

    try {
        await handler.createRegion({ op: "create_region", tag: "site", atom_indices: [0, 1] });
        await handler.setRegionRepresentation({
            op: "set_region_representation",
            tag: "site",
            representation: "line",
            params: {
                molstar_color_theme: {
                    name: "uniform",
                    params: { value: 16711680 },
                },
            },
        });
    } finally {
        (StructureElement.Bundle as any).fromSelection = originalFromSelection;
    }

    assert.strictEqual(componentCommits, 1);
    assert.strictEqual(representationAdds, 1);
});

test("state handler creates a state-None region without adding a representation", async () => {
    const originalFromSelection = StructureElement.Bundle.fromSelection;
    let representationAdds = 0;
    const plugin: any = {
        state: {
            data: {
                cells: { has: () => true },
                build: () => ({
                    to: (_ref: unknown) => ({
                        apply: (_transform: unknown, _params: unknown) => ({
                            selector: { ref: "component-ref", isOk: true },
                            async commit(_options: unknown) {},
                        }),
                    }),
                }),
            },
        },
        builders: {
            structure: {
                representation: {
                    async addRepresentation() {
                        representationAdds += 1;
                        return { ref: "repr-ref" };
                    },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({}) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).buildSelectionFromAtomIndices = () => ({ fake: "selection" });
    (StructureElement.Bundle as any).fromSelection = (_selection: unknown) => ({ fake: "bundle" });

    try {
        await handler.createRegion({
            op: "create_region",
            tag: "none-region",
            atom_indices: [0, 1],
            params: { alpha: 0.4 },
        });
    } finally {
        (StructureElement.Bundle as any).fromSelection = originalFromSelection;
    }

    assert.strictEqual(representationAdds, 0);
});

test("state handler reset_representation removes the visual instead of adding cartoon", async () => {
    const originalFromSelection = StructureElement.Bundle.fromSelection;
    const addedTypes: string[] = [];
    let removed = 0;
    const plugin: any = {
        state: {
            data: {
                cells: { has: () => true },
                build: () => ({
                    to: (_ref: unknown) => ({
                        apply: (_transform: unknown, _params: unknown) => ({
                            selector: { ref: `component-ref-${removed}`, isOk: true },
                            async commit(_options: unknown) {},
                        }),
                    }),
                }),
            },
        },
        builders: {
            structure: {
                representation: {
                    async addRepresentation(_componentRef: unknown, spec: any) {
                        addedTypes.push(String(spec.type));
                        return { ref: `repr-${addedTypes.length}` };
                    },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({}) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    (handler as any).removeStateObject = async () => { removed += 1; };
    (handler as any).buildSelectionFromAtomIndices = () => ({ fake: "selection" });
    (StructureElement.Bundle as any).fromSelection = (_selection: unknown) => ({ fake: "bundle" });

    try {
        await handler.createRegion({ op: "create_region", tag: "styled", atom_indices: [0, 1] });
        await handler.setRegionRepresentation({
            op: "set_region_representation",
            tag: "styled",
            representation: "line",
            params: {},
        });
        await handler.setRegionRepresentation({
            op: "set_region_representation",
            tag: "styled",
            representation: undefined,
            params: {},
        });
    } finally {
        (StructureElement.Bundle as any).fromSelection = originalFromSelection;
    }

    assert.deepStrictEqual(addedTypes, ["line"]);
    assert.strictEqual(removed, 1);
});

test("state handler inherit region follows the live whole representation type", async () => {
    const originalFromSelection = StructureElement.Bundle.fromSelection;
    const addedTypes: string[] = [];
    // The whole's rendered representation, read by wholeRepresentationTypes() from
    // globalReprs → the cell's transform.params.type.name. Mutating wholeType here
    // models the user restyling the whole; the inherit region must follow.
    let wholeType = "line";
    const plugin: any = {
        state: {
            data: {
                cells: {
                    has: () => true,
                    get: (_ref: unknown) => ({ transform: { params: { type: { name: wholeType, params: {} } } } }),
                },
                build: () => ({
                    to: (_ref: unknown) => ({
                        apply: (_transform: unknown, _params: unknown) => ({
                            selector: { ref: "component-ref", isOk: true },
                            async commit(_options: unknown) {},
                        }),
                    }),
                    async commit() {},
                }),
            },
        },
        builders: {
            structure: {
                representation: {
                    async addRepresentation(_componentRef: unknown, spec: any) {
                        addedTypes.push(String(spec.type));
                        return { ref: `repr-${addedTypes.length}` };
                    },
                },
            },
        },
    };
    const handler = new StateHandlers(plugin, {
        getStructure: () => ({}) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => [],
        notify: (_msg: any) => {},
    });
    // The whole is drawing one representation; the inherit path reads it from globalReprs.
    (handler as any).globalReprs = new Set(["whole-repr"]);
    (handler as any).buildSelectionFromAtomIndices = () => ({ fake: "selection" });
    (StructureElement.Bundle as any).fromSelection = (_selection: unknown) => ({ fake: "bundle" });

    try {
        await handler.createRegion({
            op: "create_region",
            tag: "inherited",
            atom_indices: [0, 1],
            representation: "inherit",
            params: { alpha: 1 },
        });
        wholeType = "spacefill";
        (handler as any).removeStateObject = async () => {};
        await (handler as any).repaintInheritedRegions();
    } finally {
        (StructureElement.Bundle as any).fromSelection = originalFromSelection;
    }

    assert.deepStrictEqual(addedTypes, ["line", "spacefill"]);
});

function makeOwnershipHarness() {
    const wholeComponent = {
        ref: "whole-component",
        representations: [{ cell: { transform: { ref: "whole-repr" }, params: { values: { type: { name: "cartoon" } } } } }],
    };
    const regionComponentA = {
        ref: "region-a-component",
        representations: [{ cell: { transform: { ref: "region-a-repr" }, params: { values: { type: { name: "line" } } } } }],
    };
    const regionComponentB = {
        ref: "region-b-component",
        representations: [{ cell: { transform: { ref: "region-b-repr" }, params: { values: { type: { name: "line" } } } } }],
    };
    const update: any = {
        to() { return update; },
        update() { return update; },
        apply() { return update; },
        delete() { return update; },
        async commit() {},
    };
    const plugin: any = {
        state: {
            data: {
                build: () => update,
                select: () => [],
                cells: { has: () => true },
            },
        },
    };
    const componentByRef: Record<string, any> = {
        "region-a-component": regionComponentA,
        "region-b-component": regionComponentB,
    };
    let handler: StateHandlers;
    handler = new StateHandlers(plugin, {
        getStructure: () => ({}) as any,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => "structure-ref" as any,
        getComponents: () => {
            const regionIndex = (handler as any).regionIndex as Map<string, any>;
            const regionComponents = Array.from(regionIndex.values())
                .map(entry => componentByRef[String(entry.component)])
                .filter(Boolean);
            return [wholeComponent, ...regionComponents] as any;
        },
        notify: (_msg: any) => {},
    });
    const calls: Array<{ components: string[]; atomIndices: number[]; value: number }> = [];
    (handler as any).allAtomIndices = () => [0, 1, 2, 3, 4, 5];
    (handler as any).applyTransparencyLayer = async (
        components: Array<{ ref: string }>,
        atomIndices: number[] | undefined,
        value: number,
    ) => {
        calls.push({
            components: components.map(component => component.ref),
            atomIndices: [...(atomIndices ?? [])],
            value,
        });
    };
    const regionIndex = (handler as any).regionIndex as Map<string, any>;
    const setRegion = (
        tag: string,
        component: string,
        atomIndices: number[],
        params: Record<string, unknown> = {},
    ) => {
        regionIndex.set(tag, {
            component,
            representations: [],
            atomIndices,
            selection: tag,
            hidden: false,
            representationState: "own",
            representation: "line",
            preset: undefined,
            userPreset: undefined,
            params,
        });
    };
    return { handler, calls, setRegion };
}

test("state handler ownership masks opaque region atoms on the whole component only", async () => {
    const { handler, calls, setRegion } = makeOwnershipHarness();
    setRegion("site", "region-a-component", [0, 1]);

    await (handler as any).applyComposedTransparency();

    assert.deepStrictEqual(calls, [
        { components: ["whole-component"], atomIndices: [0, 1], value: 1 },
    ]);
});

test("state handler translucent regions do not own atoms", async () => {
    const { handler, calls, setRegion } = makeOwnershipHarness();
    setRegion("site", "region-a-component", [0, 1], { alpha: 0.95 });

    await (handler as any).applyComposedTransparency();

    assert.deepStrictEqual(calls, []);
});

test("state handler ownership updates the whole mask by atom deltas", async () => {
    const { handler, calls, setRegion } = makeOwnershipHarness();
    setRegion("site", "region-a-component", [0, 1]);

    await (handler as any).applyComposedTransparency();
    calls.length = 0;
    const entry = ((handler as any).regionIndex as Map<string, any>).get("site");
    entry.atomIndices = [0, 1, 2];
    await (handler as any).applyComposedTransparency();

    assert.deepStrictEqual(calls, [
        { components: ["whole-component"], atomIndices: [2], value: 1 },
    ]);
});

test("state handler composes user mask, focus fade, and ownership on the right components", async () => {
    const { handler, calls, setRegion } = makeOwnershipHarness();
    setRegion("site", "region-a-component", [0, 1]);
    (handler as any).currentVisibleIndices = [0, 1, 3, 4, 5];
    (handler as any).focusFadeIndices = [0, 1];
    (handler as any).focusFadeValue = 0.4;

    await (handler as any).applyComposedTransparency();

    assert.deepStrictEqual(calls, [
        { components: ["region-a-component"], atomIndices: [2], value: 1 },
        { components: ["whole-component"], atomIndices: [2, 3, 4, 5], value: 0.4 },
        { components: ["whole-component"], atomIndices: [0, 1, 2], value: 1 },
    ]);
});

test("state handler show_only hides other regions and masks the whole component", async () => {
    const { handler, calls, setRegion } = makeOwnershipHarness();
    setRegion("site", "region-a-component", [0, 1]);
    setRegion("other", "region-b-component", [2, 3]);

    await handler.showOnlyRegion({ op: "show_only_region", tag: "site" });

    const regionIndex = (handler as any).regionIndex as Map<string, any>;
    assert.strictEqual(regionIndex.get("site").hidden, false);
    assert.strictEqual(regionIndex.get("other").hidden, true);
    assert.deepStrictEqual(calls.at(-1), {
        components: ["whole-component"],
        atomIndices: [0, 1, 2, 3, 4, 5],
        value: 1,
    });
});

test("state handler applies preset alpha to every generated representation", async () => {
    const updated: Array<{ ref: string; alpha: number }> = [];
    let commits = 0;
    const update: any = {
        to(ref: string) {
            return {
                update(_transform: unknown, mutate: (params: any) => void) {
                    const params = { type: { params: {} } };
                    mutate(params);
                    updated.push({ ref, alpha: params.type.params.alpha });
                    return update;
                },
            };
        },
        async commit(options: any) {
            commits += 1;
            assert.deepStrictEqual(options, { doNotUpdateCurrent: true });
        },
    };
    const handler = new StateHandlers({
        state: { data: { build: () => update } },
    } as any, {
        getStructure: () => undefined,
        getLoadedStructure: () => undefined,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: () => {},
    });

    await (handler as any).applyAlphaToRepresentations(["repr-a", "repr-b"], 0.35);

    assert.deepStrictEqual(updated, [
        { ref: "repr-a", alpha: 0.35 },
        { ref: "repr-b", alpha: 0.35 },
    ]);
    assert.strictEqual(commits, 1);
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

    await handler.hideWhole({ op: "hide_whole" });
    const pendingOpsA = (handler as any).pendingGlobalOps as Array<{ hide: boolean; target: string }>;
    const requestedA = (handler as any).requestedGlobalHidden as boolean | null;
    assert.strictEqual(pendingOpsA.length, 1);
    assert.deepStrictEqual(pendingOpsA[0], { hide: true, target: "whole" });
    assert.strictEqual(requestedA, true);

    await handler.showWhole({ op: "show_whole", target: "all" });
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
                                components: [
                                    { representations: [{ cell: { transform: { ref: "default-repr" } } }] },
                                ],
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

    await handler.setWholeRepresentation({
        op: "set_whole_representation",
        preset: "auto",
        params: {},
    } as any);

    assert.deepStrictEqual(removed, ["default-repr"]);
    const globalReprs = (handler as any).globalReprs as Set<string>;
    assert.deepStrictEqual(Array.from(globalReprs), ["new-global-repr"]);
});


test("state handler replaces prior explicit global representation on subsequent global representation", async () => {
    const removed: string[] = [];
    const structureRef = "structure-ref";
    const createdRefs = ["first-global-repr", "second-global-repr"];
    const plugin: any = {
        managers: {
            structure: {
                hierarchy: {
                    current: { structures: [{ representations: [], components: [] }] },
                },
            },
        },
        builders: {
            structure: {
                representation: {
                    async applyPreset(_ref: any, _preset: any, _params: any) {
                        return { representations: { main: { ref: createdRefs.shift() } } };
                    },
                },
            },
        },
        state: {
            data: {
                cells: new Map(),
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

    plugin.state.data.cells.has = (ref: string) => ref === "first-global-repr" || ref === "second-global-repr";
    (handler as any).removeStateObject = async (ref?: string) => {
        if (ref) removed.push(ref);
    };
    (handler as any).handleShowHideGlobal = async () => {};

    await handler.setWholeRepresentation({ op: "set_whole_representation", preset: "auto", params: {} } as any);
    await handler.setWholeRepresentation({ op: "set_whole_representation", preset: "polymer-cartoon", params: {} } as any);

    assert.deepStrictEqual(removed, ["first-global-repr"]);
    const globalReprs = (handler as any).globalReprs as Set<string>;
    assert.deepStrictEqual(Array.from(globalReprs), ["second-global-repr"]);
});

test("state handler captures initial global representations on structure load", async () => {
    const plugin: any = {
        managers: {
            structure: {
                hierarchy: {
                    current: {
                        structures: [
                            {
                                components: [
                                    { representations: [{ cell: { transform: { ref: "default-repr" } } }] },
                                ],
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

    await handler.setWholeRepresentation({
        op: "set_whole_representation",
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

    await handler.setWholeRepresentation({
        op: "set_whole_representation",
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

    await handler.setWholeRepresentation({
        op: "set_whole_representation",
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

    await handler.setWholeRepresentation({
        op: "set_whole_representation",
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
