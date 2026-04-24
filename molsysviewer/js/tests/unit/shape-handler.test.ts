import assert from "node:assert";
import test from "node:test";

import { ShapeHandlers, ShapeHandlersContext } from "../../src/managers/handlers/shape-handlers";
import { withWarnCapture } from "./helpers";

test("shape handlers reject invalid overlay payloads without registering refs", async () => {
    const plugin: any = {};
    const registered: Array<{ ref: any; tag?: string }> = [];
    const handler = new ShapeHandlers(plugin, (ref, tag) => {
        registered.push({ ref, tag });
    });

    await withWarnCapture(async (warnings) => {
        await handler.addAlphaSphereSet({ op: "add_alpha_sphere_set", options: {} as any });
        await handler.addPocketSurface({ op: "add_pocket_surface", options: {} as any });
        await handler.addPocketBlob({ op: "add_pocket_blob", options: {} as any });
        await handler.addChannelTube({ op: "add_channel_tube", options: { centers: [[0, 0, 0]], radii: [1] } as any });
        await handler.addAnisotropyEllipsoids({ op: "add_anisotropy_ellipsoids", options: {} as any });
        await handler.addPharmacophore({ op: "add_pharmacophore_features", options: { centers: [[0, 0, 0]], kinds: [] } as any });
        await handler.addDisplacementVectors({ op: "add_displacement_vectors", options: {} as any });
        await handler.addTetrahedra({ op: "add_tetrahedra", options: {} as any });
        await handler.addTriangleFaces({ op: "add_triangle_faces", options: {} as any });

        assert.strictEqual(warnings.length, 9);
        assert.ok(warnings.some((w) => w.includes("add_alpha_sphere_set missing alpha_spheres")));
        assert.ok(warnings.some((w) => w.includes("add_pocket_surface without atom_indices")));
        assert.ok(warnings.some((w) => w.includes("add_pocket_blob without centers or radii")));
        assert.ok(warnings.some((w) => w.includes("add_channel_tube requires at least two centers and radii")));
        assert.ok(warnings.some((w) => w.includes("add_anisotropy_ellipsoids requires centers or atom_indices")));
        assert.ok(warnings.some((w) => w.includes("add_pharmacophore_features requires centers and kinds of same length")));
        assert.ok(warnings.some((w) => w.includes("add_displacement_vectors without vectors")));
        assert.ok(warnings.some((w) => w.includes("add_tetrahedra without tetraCoords or atom_quads")));
        assert.ok(warnings.some((w) => w.includes("add_triangle_faces without vertices or atom_triplets")));
    });

    assert.deepStrictEqual(registered, []);
});

// ---------------------------------------------------------------------------
// structures_coords storage (tag-index lifecycle)
// ---------------------------------------------------------------------------

test("addSphere with structures_coords stores trajectory entry under the given tag", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await handler.addSphere({
        op: "add_sphere",
        tag: "site",
        options: { tag: "site", structures_coords: [null, [1, 2, 3]] } as any,
    });

    const entry = (handler as any).trajectoryShapes.get("site");
    assert.ok(entry !== undefined, "entry should be stored");
    assert.strictEqual(entry.op, "add_sphere");
    assert.deepStrictEqual(entry.framesCoords, [null, [1, 2, 3]]);
});

test("addChannelTube with structures_coords stores trajectory entry", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await handler.addChannelTube({
        op: "add_channel_tube",
        options: { tag: "tube1", structures_coords: [null, [[0, 0, 0], [1, 1, 1]]] } as any,
    });

    const entry = (handler as any).trajectoryShapes.get("tube1");
    assert.ok(entry !== undefined);
    assert.strictEqual(entry.op, "add_channel_tube");
});

test("addTriangleFaces with structures_coords stores trajectory entry", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await handler.addTriangleFaces({
        op: "add_triangle_faces",
        options: { tag: "face1", structures_coords: [null, [[0, 0, 0], [1, 0, 0], [0, 1, 0]]] } as any,
    });

    const entry = (handler as any).trajectoryShapes.get("face1");
    assert.ok(entry !== undefined);
    assert.strictEqual(entry.op, "add_triangle_faces");
});

test("addNetworkLinks with structures_coords stores trajectory entry", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await handler.addNetworkLinks({
        op: "add_network_links",
        options: { tag: "links1", structures_coords: [null, [[[0, 0, 0], [1, 1, 1]]]] } as any,
    });

    const entry = (handler as any).trajectoryShapes.get("links1");
    assert.ok(entry !== undefined);
    assert.strictEqual(entry.op, "add_network_links");
});

test("addHbonds stores trajectory entry under given tag", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await handler.addHbonds({
        op: "add_hbonds",
        options: { tag: "hb1", structures_atom_pairs: [null, [[0, 1]]] } as any,
    });

    const entry = (handler as any).trajectoryShapes.get("hb1");
    assert.ok(entry !== undefined);
    assert.strictEqual(entry.op, "add_hbonds");
    assert.deepStrictEqual(entry.framesCoords, [null, [[0, 1]]]);
});

// ---------------------------------------------------------------------------
// addHbonds validation (warn path)
// ---------------------------------------------------------------------------

test("addHbonds warns and does not store when structures_atom_pairs is missing", async () => {
    const plugin: any = {};
    const handler = new ShapeHandlers(plugin, () => void 0);

    await withWarnCapture(async (warnings) => {
        await handler.addHbonds({ op: "add_hbonds", options: {} as any });
        assert.strictEqual(warnings.length, 1);
        assert.ok(warnings[0].includes("add_hbonds"));
    });

    assert.strictEqual((handler as any).trajectoryShapes.size, 0);
});

// ---------------------------------------------------------------------------
// Frame switching via subscription
// ---------------------------------------------------------------------------

test("frame subscription fires clearByTag and renderTrajectoryFrame on frame change", async () => {
    const plugin: any = {};
    const cleared: string[] = [];
    const rendered: Array<{ tag: string; coords: any }> = [];

    let subscriptionCallback: ((frame: number) => void) | null = null;

    const context: ShapeHandlersContext = {
        clearByTag: async (tag) => { cleared.push(tag); },
        subscribeToTrajectoryState: (cb) => {
            subscriptionCallback = cb;
            return () => { subscriptionCallback = null; };
        },
    };

    const handler = new ShapeHandlers(plugin, () => void 0, context);

    (handler as any).renderTrajectoryFrame = async (tag: string, _op: string, _baseOptions: any, frameCoords: any) => {
        rendered.push({ tag, coords: frameCoords });
    };

    await handler.addSphere({
        op: "add_sphere",
        tag: "sphere-a",
        options: { tag: "sphere-a", structures_coords: [null, [5, 5, 5]] } as any,
    });

    assert.ok(subscriptionCallback !== null, "subscription should be registered");

    subscriptionCallback!(1);
    await new Promise((res) => setTimeout(res, 10));

    assert.ok(cleared.includes("sphere-a"), "clearByTag should have been called");
    assert.strictEqual(rendered.length, 1);
    assert.deepStrictEqual(rendered[0].coords, [5, 5, 5]);
});

test("frame subscription skips render when framesCoords entry is null", async () => {
    const plugin: any = {};
    const cleared: string[] = [];
    const rendered: string[] = [];

    let subscriptionCallback: ((frame: number) => void) | null = null;
    const context: ShapeHandlersContext = {
        clearByTag: async (tag) => { cleared.push(tag); },
        subscribeToTrajectoryState: (cb) => {
            subscriptionCallback = cb;
            return () => void 0;
        },
    };

    const handler = new ShapeHandlers(plugin, () => void 0, context);
    (handler as any).renderTrajectoryFrame = async (tag: string) => { rendered.push(tag); };

    await handler.addSphere({
        op: "add_sphere",
        tag: "hidden-sphere",
        options: { tag: "hidden-sphere", structures_coords: [null, null] } as any,
    });

    subscriptionCallback!(1);
    await new Promise((res) => setTimeout(res, 10));

    assert.ok(cleared.includes("hidden-sphere"), "clearByTag must be called even for null frame");
    assert.strictEqual(rendered.length, 0, "renderTrajectoryFrame must not be called for null frame");
});

test("frame subscription fires same frame index does not trigger re-render", async () => {
    const plugin: any = {};
    const cleared: string[] = [];

    let subscriptionCallback: ((frame: number) => void) | null = null;
    const context: ShapeHandlersContext = {
        clearByTag: async (tag) => { cleared.push(tag); },
        subscribeToTrajectoryState: (cb) => {
            subscriptionCallback = cb;
            return () => void 0;
        },
    };

    const handler = new ShapeHandlers(plugin, () => void 0, context);
    (handler as any).renderTrajectoryFrame = async () => void 0;

    await handler.addSphere({
        op: "add_sphere",
        tag: "s",
        options: { tag: "s", structures_coords: [null] } as any,
    });

    subscriptionCallback!(0);
    await new Promise((res) => setTimeout(res, 10));
    assert.strictEqual(cleared.length, 0, "no clear should happen when frame index does not change");
});

// ---------------------------------------------------------------------------
// Single subscription guarantee
// ---------------------------------------------------------------------------

test("subscribeToTrajectoryState is called only once even when multiple trajectory shapes are added", async () => {
    const plugin: any = {};
    let subCount = 0;

    const context: ShapeHandlersContext = {
        clearByTag: async () => void 0,
        subscribeToTrajectoryState: (_cb) => {
            subCount++;
            return () => void 0;
        },
    };

    const handler = new ShapeHandlers(plugin, () => void 0, context);
    (handler as any).renderTrajectoryFrame = async () => void 0;

    await handler.addSphere({ op: "add_sphere", tag: "s1", options: { tag: "s1", structures_coords: [null] } as any });
    await handler.addSphere({ op: "add_sphere", tag: "s2", options: { tag: "s2", structures_coords: [null] } as any });
    await handler.addChannelTube({ op: "add_channel_tube", options: { tag: "t1", structures_coords: [null] } as any });

    assert.strictEqual(subCount, 1, "subscribeToTrajectoryState must be called exactly once");
});

// ---------------------------------------------------------------------------
// frameUpdateInProgress guard
// ---------------------------------------------------------------------------

test("applyFrame skips concurrent invocation via frameUpdateInProgress guard", async () => {
    const plugin: any = {};
    const cleared: string[] = [];
    let resolveFirst: (() => void) | null = null;

    const context: ShapeHandlersContext = {
        clearByTag: async (tag) => {
            cleared.push(tag);
            if (cleared.length === 1) {
                await new Promise<void>((res) => { resolveFirst = res; });
            }
        },
        subscribeToTrajectoryState: () => () => void 0,
    };

    const handler = new ShapeHandlers(plugin, () => void 0, context);
    (handler as any).renderTrajectoryFrame = async () => void 0;

    (handler as any).trajectoryShapes.set("s", { op: "add_sphere", baseOptions: {}, framesCoords: [null, null, null] });
    (handler as any).currentFrame = 0;

    const first = (handler as any).applyFrame(2);
    const second = (handler as any).applyFrame(2);

    resolveFirst!();
    await first;
    await second;

    assert.strictEqual(cleared.length, 1, "second applyFrame should be skipped while first is in progress");
});

test("shape handler rejects inconsistent alpha sphere arrays without registering refs", async () => {
    const plugin: any = {};
    const registered: Array<{ ref: any; tag?: string }> = [];
    const handler = new ShapeHandlers(plugin, (ref, tag) => {
        registered.push({ ref, tag });
    });

    await withWarnCapture(async (warnings) => {
        await handler.addAlphaSphereSet({
            op: "add_alpha_sphere_set",
            options: {
                alpha_spheres: {
                    centers: [[0, 0, 0], [1, 1, 1]],
                    radii: [1],
                },
            } as any,
        });

        assert.strictEqual(warnings.length, 1);
        assert.ok(warnings[0].includes("add_alpha_sphere_set inconsistent data"));
    });

    assert.deepStrictEqual(registered, []);
});
