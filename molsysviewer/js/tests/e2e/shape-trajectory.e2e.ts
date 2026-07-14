import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Minimal 2-frame MolSys payload: 3 atoms, 2 structures.
// atom_id is the required field that determines atomCount in loadStructureFromMolSysPayload.
const MOLSYS_PAYLOAD = {
    atoms: {
        atom_id: [1, 2, 3],
        element_symbol: ["N", "C", "C"],
        residue_id: [1, 1, 1],
        residue_name: ["ALA", "ALA", "ALA"],
        chain_id: ["A", "A", "A"],
    },
    structures: [
        { coordinates: [[11.1, 13.2, 8.6], [12.6, 13.3, 8.3], [13.2, 12.0, 8.0]] },
        { coordinates: [[11.5, 13.5, 8.8], [12.8, 13.5, 8.5], [13.4, 12.2, 8.2]] },
    ],
};

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const browser = await chromium.launch({
        headless: true,
        executablePath: envBin,
        chromiumSandbox: false,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    } as any);

    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width:800px;height:600px;"></div></body></html>`,
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    // ── Scenario 1: load_molsys_payload + trajectory sphere registered ────────
    console.log("[E2E shapes] Scenario: trajectory sphere stored via handleMessage");

    await page.evaluate(async (payload) => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;

        await controller.handleMessage({
            op: "load_molsys_payload",
            payload,
        });

        // Poll until trajectory has 2 frames in Mol* state
        for (let i = 0; i < 80; i++) {
            const s = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            const fc = (controller as any).trajectory?.getTrajectoryState?.()?.frameCount ?? 0;
            if (s?.elementCount > 0 && fc >= 2) break;
            await new Promise(r => setTimeout(r, 100));
        }

        await controller.handleMessage({
            op: "add_sphere",
            tag: "traj-sphere",
            options: {
                tag: "traj-sphere",
                radius: 2.0,
                color: 0x00ff00,
                alpha: 0.4,
                structures_coords: [null, [12.0, 13.0, 8.0]],
            },
        });
    }, MOLSYS_PAYLOAD);

    const hasTrajSphere = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).shapes?.trajectoryShapes?.has("traj-sphere") === true;
    });
    assert.ok(hasTrajSphere, "trajectory sphere should be stored in trajectoryShapes map");

    const sphereEntry = await page.evaluate(() => {
        const c = (window as any).__controller;
        const entry = (c as any).shapes?.trajectoryShapes?.get("traj-sphere");
        return entry ? { op: entry.op, coordsLength: entry.framesCoords.length, frame0: entry.framesCoords[0], frame1: entry.framesCoords[1] } : null;
    });
    assert.ok(sphereEntry !== null, "sphere trajectory entry should exist");
    assert.strictEqual(sphereEntry?.op, "add_sphere");
    assert.strictEqual(sphereEntry?.coordsLength, 2);
    assert.strictEqual(sphereEntry?.frame0, null, "frame 0 should be null (hidden)");
    assert.deepStrictEqual(sphereEntry?.frame1, [12.0, 13.0, 8.0], "frame 1 should have coords");

    // ── Scenario 2: all 5 trajectory shape families registered ───────────────
    console.log("[E2E shapes] Scenario: all 5 trajectory shape families stored");

    await page.evaluate(async () => {
        const c = (window as any).__controller;

        await c.handleMessage({
            op: "add_channel_tube",
            options: {
                tag: "traj-tube",
                structures_coords: [[[0, 0, 0], [1, 1, 1]], [[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]],
                radii: [1.0, 1.0],
            },
        });

        await c.handleMessage({
            op: "add_network_links",
            options: {
                tag: "traj-links",
                structures_coords: [[[[0, 0, 0], [1, 1, 1]]], [[[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]],
            },
        });

        await c.handleMessage({
            op: "add_hbonds",
            options: {
                tag: "traj-hbonds",
                structures_atom_pairs: [[[0, 1]], [[0, 2]]],
            },
        });

        await c.handleMessage({
            op: "add_triangle_faces",
            options: {
                tag: "traj-triangles",
                structures_coords: [
                    [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                    [[0, 0, 1], [1, 0, 1], [0, 1, 1]],
                ],
            },
        });
    });

    const allFamiliesStored = await page.evaluate(() => {
        const c = (window as any).__controller;
        const map = (c as any).shapes?.trajectoryShapes;
        return {
            sphere: map?.has("traj-sphere"),
            tube: map?.has("traj-tube"),
            links: map?.has("traj-links"),
            hbonds: map?.has("traj-hbonds"),
            triangles: map?.has("traj-triangles"),
            size: map?.size,
        };
    });
    assert.ok(allFamiliesStored.sphere, "traj-sphere should be in trajectoryShapes");
    assert.ok(allFamiliesStored.tube, "traj-tube should be in trajectoryShapes");
    assert.ok(allFamiliesStored.links, "traj-links should be in trajectoryShapes");
    assert.ok(allFamiliesStored.hbonds, "traj-hbonds should be in trajectoryShapes");
    assert.ok(allFamiliesStored.triangles, "traj-triangles should be in trajectoryShapes");
    assert.strictEqual(allFamiliesStored.size, 5, "all 5 trajectory shape families should be stored");

    // ── Scenario 3: frame navigation updates ShapeHandlers currentFrame ──────
    console.log("[E2E shapes] Scenario: set_trajectory_frame updates ShapeHandlers currentFrame");

    const frameBeforeNav = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).shapes?.currentFrame ?? -1;
    });
    assert.strictEqual(frameBeforeNav, 0, "initial currentFrame should be 0");

    await page.evaluate(async () => {
        const c = (window as any).__controller;
        await c.handleMessage({ op: "set_trajectory_frame", index: 1 });
        // Allow async applyFrame to complete
        await new Promise(r => setTimeout(r, 300));
    });

    // Poll for ShapeHandlers currentFrame to reflect the navigation
    let frameAfterNav = -1;
    for (let i = 0; i < 20; i++) {
        frameAfterNav = await page.evaluate(() => {
            const c = (window as any).__controller;
            return (c as any).shapes?.currentFrame ?? -1;
        });
        if (frameAfterNav === 1) break;
        await new Promise(r => setTimeout(r, 100));
    }
    assert.strictEqual(frameAfterNav, 1, "currentFrame should update to 1 after set_trajectory_frame");

    // ── Scenario 4: clear_shapes_by_tag removes rendered refs but not map entry
    console.log("[E2E shapes] Scenario: clear_shapes_by_tag removes rendered refs");

    await page.evaluate(async () => {
        const c = (window as any).__controller;
        await c.handleMessage({ op: "clear_shapes_by_tag", tag: "traj-sphere" });
    });

    // trajectoryShapes map still has the entry (by design: it re-renders on next frame change)
    const mapAfterClear = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).shapes?.trajectoryShapes?.has("traj-sphere");
    });
    assert.ok(mapAfterClear, "trajectoryShapes map entry persists after clear_shapes_by_tag (re-renders on next frame)");

    // ── Scenario 5: clear_all → reload → trajectory shapes work again ─────────
    console.log("[E2E shapes] Scenario: clear_all then reload and new trajectory shape");

    await page.evaluate(async (payload) => {
        const c = (window as any).__controller;
        await c.handleMessage({ op: "clear_all" });
        await c.handleMessage({ op: "load_molsys_payload", payload });

        for (let i = 0; i < 80; i++) {
            const s = (c as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            const fc = (c as any).trajectory?.getTrajectoryState?.()?.frameCount ?? 0;
            if (s?.elementCount > 0 && fc >= 2) break;
            await new Promise(r => setTimeout(r, 100));
        }

        await c.handleMessage({
            op: "add_sphere",
            tag: "after-reload",
            options: {
                tag: "after-reload",
                radius: 3.0,
                color: 0xff0000,
                alpha: 0.5,
                structures_coords: [[10, 10, 10], [11, 11, 11]],
            },
        });
    }, MOLSYS_PAYLOAD);

    const postReloadEntry = await page.evaluate(() => {
        const c = (window as any).__controller;
        return (c as any).shapes?.trajectoryShapes?.has("after-reload");
    });
    assert.ok(postReloadEntry, "trajectory shape should register after clear_all + reload");

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E shapes] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
