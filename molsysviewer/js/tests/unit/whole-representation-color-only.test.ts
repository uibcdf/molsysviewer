import assert from "node:assert";
import test from "node:test";

import { StateHandlers } from "../../src/managers/handlers/state-handlers";

function makeHandler(plugin: any) {
    return new StateHandlers(plugin, {
        getStructure: () => undefined,
        getLoadedStructure: () => ({ structure: "structure-ref" }) as any,
        getCurrentStructureRef: () => undefined,
        getComponents: () => [],
        notify: () => {},
    } as any);
}

const BASE = {
    op: "set_whole_representation" as const,
    representation: "cartoon",
    params: { color_scheme: "chain_default" },
};

test("only a pure color change takes the in-place path", () => {
    const handler: any = makeHandler({ state: { data: {} } });
    handler.lastWholeRepresentation = { ...BASE };

    const isColorOnly = (msg: any) => handler.isColorOnlyRepresentationChange(msg);

    // same representation and params, different scheme → in-place recolor
    assert.strictEqual(isColorOnly({ ...BASE, params: { color_scheme: "residue_name" } }), true);
    // advanced Mol* theme is also a color-only key
    assert.strictEqual(
        isColorOnly({ ...BASE, params: { molstar_color_theme: { name: "uniform" } } }),
        true,
    );

    // a different representation must rebuild
    assert.strictEqual(
        isColorOnly({ ...BASE, representation: "spacefill", params: { color_scheme: "residue_name" } }),
        false,
    );
    // a non-color param change must rebuild
    assert.strictEqual(
        isColorOnly({ ...BASE, params: { color_scheme: "chain_default", alpha: 0.5 } }),
        false,
    );
    // a preset change must rebuild
    assert.strictEqual(isColorOnly({ ...BASE, preset: "publication" }), false);
    // rule-based user presets always rebuild
    assert.strictEqual(isColorOnly({ ...BASE, user_preset: { base: "cartoon" } }), false);
});

test("no previous representation means there is nothing to recolor in place", () => {
    const handler: any = makeHandler({ state: { data: {} } });
    assert.strictEqual(handler.isColorOnlyRepresentationChange({ ...BASE }), false);
});

test("in-place recolor updates the color theme without rebuilding", async () => {
    const updated: any[] = [];
    let committed = 0;
    const plugin: any = {
        state: {
            data: {
                cells: new Map([["repr-1", {}]]),
                build: () => ({
                    to: (_ref: string) => ({
                        update: (_transformer: any, fn: (params: any) => void) => {
                            const params: any = { colorTheme: { name: "element-symbol", params: {} } };
                            fn(params);
                            updated.push(params);
                        },
                    }),
                    commit: async () => { committed += 1; },
                }),
            },
        },
    };

    const handler: any = makeHandler(plugin);
    handler.globalReprs.add("repr-1");

    const applied = await handler.applyStructuralColorInPlace({
        ...BASE,
        params: { color_scheme: "residue_name" },
    });

    assert.strictEqual(applied, true);
    assert.strictEqual(committed, 1);
    assert.strictEqual(updated.length, 1);
    // chain_default/residue_name resolve to Mol* theme names before reaching here
    assert.strictEqual(updated[0].colorTheme.name, "residue-name");
});

test("in-place recolor keeps per-atom colors as the overlay", async () => {
    const updated: any[] = [];
    const plugin: any = {
        state: {
            data: {
                cells: new Map([["repr-1", {}]]),
                build: () => ({
                    to: (_ref: string) => ({
                        update: (_transformer: any, fn: (params: any) => void) => {
                            const params: any = {
                                colorTheme: { name: "msv-per-atom", params: { base: { name: "element-symbol" } } },
                            };
                            fn(params);
                            updated.push(params);
                        },
                    }),
                    commit: async () => {},
                }),
            },
        },
    };

    const handler: any = makeHandler(plugin);
    handler.globalReprs.add("repr-1");

    await handler.applyStructuralColorInPlace({ ...BASE, params: { color_scheme: "residue_name" } });

    // the per-atom theme must survive; only its base changes
    assert.strictEqual(updated[0].colorTheme.name, "msv-per-atom");
    assert.strictEqual(updated[0].colorTheme.params.base.name, "residue-name");
});

test("an explicitly applied viewpoint is marked as intentional", () => {
    const handler: any = makeHandler({ state: { data: {} } });
    assert.strictEqual(handler.intentionalViewpoint, false);

    // Applying a camera snapshot (or focusing a selection) is deliberate, even
    // though no mouse interaction happened. Tracking only pointer input would
    // discard those viewpoints on the next representation rebuild.
    handler.markIntentionalViewpoint();
    assert.strictEqual(handler.intentionalViewpoint, true);
});

test("pointer interaction marks an intentional viewpoint", () => {
    const subs: Record<string, (() => void) | undefined> = {};
    const plugin: any = {
        state: { data: {} },
        canvas3d: {
            input: {
                drag: { subscribe: (fn: () => void) => { subs.drag = fn; } },
                wheel: { subscribe: (fn: () => void) => { subs.wheel = fn; } },
                pinch: { subscribe: (fn: () => void) => { subs.pinch = fn; } },
            },
        },
    };
    const handler: any = makeHandler(plugin);

    handler.ensureCameraInputTracking();
    assert.strictEqual(handler.intentionalViewpoint, false);

    // orbiting/panning the structure counts as the user owning the viewpoint
    subs.drag?.();
    assert.strictEqual(handler.intentionalViewpoint, true);
});

test("tracking established before any representation change still catches the viewpoint", () => {
    // Regression: tracking used to be wired lazily inside setWholeRepresentation,
    // so a camera the user moved *before* the first representation change went
    // unnoticed and their framing was discarded on the following rebuild.
    let dragFn: (() => void) | undefined;
    const plugin: any = {
        state: { data: {} },
        canvas3d: { input: { drag: { subscribe: (fn: () => void) => { dragFn = fn; } } } },
    };
    const handler: any = makeHandler(plugin);

    // tracking is turned on up front (as the controller now does per message)
    handler.ensureCameraInputTracking();
    // user moves the camera before touching any representation
    dragFn?.();

    assert.strictEqual(handler.intentionalViewpoint, true);
});

test("camera input tracking retries while the canvas does not exist yet", () => {
    const plugin: any = { state: { data: {} } };  // no canvas3d yet
    const handler: any = makeHandler(plugin);

    handler.ensureCameraInputTracking();
    assert.strictEqual(handler.cameraInputTracked, false);

    // once the canvas appears, tracking can be established
    let dragFn: (() => void) | undefined;
    plugin.canvas3d = { input: { drag: { subscribe: (fn: () => void) => { dragFn = fn; } } } };
    handler.ensureCameraInputTracking();
    assert.strictEqual(handler.cameraInputTracked, true);
    dragFn?.();
    assert.strictEqual(handler.intentionalViewpoint, true);
});

test("a never-focused camera snapshot is not restored after a swap", () => {
    const handler: any = makeHandler({ state: { data: {} } });
    const shouldRestore = (snap: any) => handler.shouldRestoreCameraSnapshot(snap);

    // Mol*'s default snapshot has radius 0: the camera never framed anything.
    // Restoring it leaves the structure rendered but off-screen, which is what
    // made the view look blank when the representation was applied before the
    // widget was displayed.
    assert.strictEqual(shouldRestore({ radius: 0 }), false);
    assert.strictEqual(shouldRestore(undefined), false);
    assert.strictEqual(shouldRestore({}), false);

    // A real, focused camera must be preserved across the swap.
    assert.strictEqual(shouldRestore({ radius: 24.5 }), true);
    assert.strictEqual(shouldRestore({ radius: 0.01 }), true);
});

test("in-place recolor declines when there are no global representations", async () => {
    const handler: any = makeHandler({ state: { data: { cells: new Map(), build: () => { throw new Error("must not build"); } } } });
    const applied = await handler.applyStructuralColorInPlace({ ...BASE });
    assert.strictEqual(applied, false);
});
