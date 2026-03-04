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
