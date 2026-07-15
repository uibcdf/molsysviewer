import assert from "node:assert";
import test from "node:test";

import { SceneHandlers } from "../../src/managers/handlers/scene-handlers";
import { getPerAtomColor, setPerAtomColors } from "../../src/themes/per-atom-color";

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

test("scene clearAll clears the per-atom color map", async () => {
    const handler = new SceneHandlers({} as any, {} as any, {
        clearShapes: async () => {},
        clearLabels: async () => {},
        getComponents: () => [],
        clearShapesByTag: async () => {},
        removeLoadedStructure: async () => {},
        notify: (_msg: any) => {},
    });

    setPerAtomColors([0, 1], [0x111111, 0x222222], true);
    assert.strictEqual(getPerAtomColor(0), 0x111111);

    await handler.clearAll();

    assert.strictEqual(getPerAtomColor(0), undefined);
    assert.strictEqual(getPerAtomColor(1), undefined);
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

test("scene clipping excludes hidden sections while retaining visible sections", async () => {
    let clipObjects: any[] = [];
    const plugin: any = {
        managers: { structure: { component: { state: { options: {} }, setOptions: async (options: any) => {
            clipObjects = options.clipObjects.objects;
        } } } },
    };
    const handler = new SceneHandlers(plugin, {} as any, {
        clearShapes: async () => {}, clearLabels: async () => {}, getComponents: () => [],
        clearShapesByTag: async () => {}, removeLoadedStructure: async () => {}, notify: () => {},
        registerShapeRef: () => {},
    });
    (handler as any)._updateSectionGizmos = async () => {};
    (handler as any)._syncHandles = () => {};
    (handler as any)._ensureCameraSubscription = () => {};
    (handler as any)._repositionHandles = () => {};

    await handler.setSections({
        op: "set_sections",
        sections: [
            { tag: "visible", point: [0.1, 0.2, 0.3], normal: [1, 0, 0], hidden: false },
            { tag: "hidden", point: [0.4, 0.5, 0.6], normal: [0, 1, 0], hidden: true },
        ],
    });

    assert.strictEqual(clipObjects.length, 1);
    assert.deepStrictEqual(Array.from(clipObjects[0].position), [1, 2, 3]);
});
