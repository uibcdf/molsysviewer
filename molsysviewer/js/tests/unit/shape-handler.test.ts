import assert from "node:assert";
import test from "node:test";

import { ShapeHandlers } from "../../src/managers/handlers/shape-handlers";
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
