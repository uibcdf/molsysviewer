/**
 * Phase 14 — real-browser validation of the scene contracts.
 *
 * Everything here has been asserted before, but only against the *message* the
 * frontend emitted or the bookkeeping it kept. This file asserts against what
 * Mol* actually built: the representation cells, their `typeParams`, their
 * visibility, and the colour the per-atom theme resolves at a given atom.
 *
 * A test that reads back the message it just sent proves the message was sent.
 * These read the render tree.
 */
import assert from "node:assert";
import { execFile } from "node:child_process";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const sectionsBridge = resolve(__dirname, "scene-contracts-sections-bridge.py");

function runSectionsBridge(): Promise<any> {
    return new Promise((resolveBridge, rejectBridge) => {
        execFile(
            process.env.PYTHON || "python",
            [sectionsBridge],
            { encoding: "utf8", cwd: resolve(__dirname, "../../../.."), maxBuffer: 8 * 1024 * 1024 },
            (error, stdout, stderr) => {
                if (error) {
                    rejectBridge(new Error(stderr || stdout || String(error)));
                    return;
                }
                resolveBridge(JSON.parse(stdout));
            },
        );
    });
}

// Two chains, five residues, so `chain A` is a real topological subset and the
// per-frame trajectory scenario has somewhere to move.
const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
ATOM      5  N   ALA A   2      14.400  11.900   7.400  1.00 20.00           N
ATOM      6  CA  ALA A   2      15.100  10.650   7.100  1.00 20.00           C
ATOM      7  C   ALA A   2      16.300  10.900   6.200  1.00 20.00           C
ATOM      8  O   ALA A   2      16.900   9.980   5.700  1.00 20.00           O
ATOM      9  N   GLY B   1      18.000  12.000   9.000  1.00 20.00           N
ATOM     10  CA  GLY B   1      19.100  12.800   9.400  1.00 20.00           C
ATOM     11  C   GLY B   1      20.200  12.100  10.100  1.00 20.00           C
ATOM     12  O   GLY B   1      21.000  12.700  10.800  1.00 20.00           O
END
`;

const GREY = 0xaaaaaa; // what the old reset_colors() painted over everything

type Harness = {
    createController(target: string): Promise<any>;
    inspectScene(controller: any): any;
    probeAtomColors(controller: any, atomIndices: number[]): any;
    probePerAtomColorDecorator(controller: any, options: any): Promise<any>;
    inspectWholeRepresentationCells(controller: any): string[];
};
type BrowserWindow = Window & typeof globalThis & { __controller?: any; Harness?: Harness };

async function launch() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    // SwiftShader: these runs must not silently skip for want of a GPU. A phase
    // whose entire purpose is "confirm it on screen" cannot accept a WebGL skip.
    const glArgs = [
        "--use-gl=angle",
        "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
    ];
    return chromium.launch({ headless: true, executablePath: envBin, args: glArgs, chromiumSandbox: false } as any);
}

async function run() {
    const sectionFixture = await runSectionsBridge();
    const browser = await launch();
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 900 });

    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => { if (msg.type() === "error") errors.push(msg.text()); });

    const html = `<!doctype html><html><body><div id="root" style="width:800px;height:600px;"></div></body></html>`;
    await page.setContent(html, { waitUntil: "networkidle" });
    await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
    await page.waitForFunction(() => !!(window as any).Harness, { timeout: 30000 });

    // --- environment record (Phase 14 asks for it explicitly) -----------------
    const env = await page.evaluate(() => {
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl2") as WebGL2RenderingContext | null;
        const dbg = gl?.getExtension("WEBGL_debug_renderer_info");
        return {
            userAgent: navigator.userAgent,
            webgl2: !!gl,
            renderer: dbg && gl ? String(gl.getParameter((dbg as any).UNMASKED_RENDERER_WEBGL)) : "unknown",
            vendor: dbg && gl ? String(gl.getParameter((dbg as any).UNMASKED_VENDOR_WEBGL)) : "unknown",
        };
    });
    console.log(`[E2E scene-contracts] browser: ${browser.version()}`);
    console.log(`[E2E scene-contracts] webgl2=${env.webgl2} renderer=${env.renderer} vendor=${env.vendor}`);
    // The acceptance criterion is "no WebGL skip": if there is no context, fail loudly.
    assert.ok(env.webgl2, "WebGL2 unavailable — this run would be a silent skip, which Phase 14 forbids");

    await page.evaluate(async pdb => {
        const w = window as BrowserWindow;
        const controller = await w.Harness!.createController("root");
        w.__controller = controller;
        await controller.handleMessage({ op: "load_structure_from_string", data: pdb, format: "pdb", label: "t" });
        const n = controller.getStructureData()?.elementCount ?? 0;
        if (n <= 0) throw new Error("no structure loaded");
    }, PDB_TEXT);

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: the whole's representation succeeds, it does not accumulate");
    {
        // `areas_of_opportunity_analysis.md` §2 recorded this as deliberately
        // *additive* — "el comportamiento por defecto se mantiene de forma
        // aditiva" — and the runtime does the opposite. Nothing pinned either
        // reading, so a design record and a renderer disagreed for months.
        //
        // Counted from Mol*'s own cells, not from `globalReprs`: that set is
        // cleared on every change and would report succession even if nothing
        // survived that should not have.
        //
        // **Which mechanism this exercises.** With one representation in place,
        // a plain change is an edit of the existing node
        // (`applyWholeRepresentationInPlace`, Contract S9 mechanism A) and
        // removes nothing. The add-then-remove branch below it only runs when
        // the node set changes shape, and that state was not reachable here:
        // neither the fixture's load nor `polymer-and-ligand` on a 12-atom
        // structure produces more than one. Measured, not assumed — disabling
        // the removal left this green, which is why it says so instead of
        // implying coverage it does not have.
        const succession = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            const count = () => w.Harness!.inspectWholeRepresentationCells(w.__controller);

            await w.__controller.handleMessage({ op: "set_whole_representation", representation: "cartoon" });
            const afterFirst = count();
            await w.__controller.handleMessage({ op: "set_whole_representation", representation: "spacefill" });
            const afterSecond = count();
            return { afterFirst, afterSecond };
        });

        assert.deepStrictEqual(succession.afterFirst, ["cartoon"],
            `the whole carried more than one representation: ${JSON.stringify(succession.afterFirst)}`);
        assert.deepStrictEqual(succession.afterSecond, ["spacefill"],
            `the second representation did not replace the first: ${JSON.stringify(succession.afterSecond)}`);
        console.log("[E2E scene-contracts]   cartoon -> spacefill, one representation at a time");
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: a restored section clips the real Mol* scene");
    {
        assert.strictEqual(sectionFixture.document.sections[0].tag, "cut");
        assert.deepStrictEqual(sectionFixture.restored[0].point, [0.4, 0.2, 0.3]);
        const clipObjects = await page.evaluate(async message => {
            const controller = (window as BrowserWindow).__controller;
            await controller.handleMessage(message);
            const objects = controller.plugin.managers.structure.component.state.options.clipObjects?.objects ?? [];
            return objects.map((item: any) => ({
                type: item.type,
                invert: item.invert,
                position: Array.from(item.position as ArrayLike<number>),
            }));
        }, sectionFixture.message);
        assert.deepStrictEqual(clipObjects, [{
            type: "plane",
            invert: true,
            position: [4, 2, 3],
        }]);

        const remaining = await page.evaluate(async () => {
            const controller = (window as BrowserWindow).__controller;
            await controller.handleMessage({ op: "set_sections", sections: [] });
            return controller.plugin.managers.structure.component.state.options.clipObjects?.objects.length ?? 0;
        });
        assert.strictEqual(remaining, 0, "clearing the restored Section left Mol* clipping active");
        console.log("[E2E scene-contracts]   restored plane clips at [4, 2, 3] Å and remains controllable");
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: alpha and quality reach Mol* typeParams");
    // The headline of the phase: never confirmed on screen until now.
    {
        const snap = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({
                op: "set_whole_representation",
                representation: "ball-and-stick",
                params: { alpha: 0.55, quality: "medium" },
            });
            return w.Harness!.inspectScene(w.__controller);
        });
        assert.ok(snap.wholeReprs.length > 0, "the whole rendered no representation at all");
        const repr = snap.wholeReprs[0];
        assert.strictEqual(repr.name, "ball-and-stick", `whole rendered as ${repr.name}`);
        assert.strictEqual(repr.typeParams.alpha, 0.55, `alpha never reached Mol*: ${JSON.stringify(repr.typeParams)}`);
        assert.strictEqual(repr.typeParams.quality, "medium", `quality never reached Mol*: ${JSON.stringify(repr.typeParams)}`);
        console.log(`[E2E scene-contracts]   whole: ${repr.name} alpha=${repr.typeParams.alpha} quality=${repr.typeParams.quality}`);

        // A region's own style travels a *different* code path from the whole's
        // (component-level addRepresentation vs. structure-level params), so the
        // whole passing here says nothing about the region. Both are asserted.
        //
        // `spacefill`, not `cartoon`: Mol* cannot trace a cartoon through a
        // component with no renderable polymer backbone, and instead of failing it
        // silently substitutes ball-and-stick with default params. Asking for one
        // here would test Mol*'s fallback, not our parameter plumbing.
        const withRegion = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({
                op: "create_region", tag: "styled", atom_indices: [8, 9, 10, 11],
                representation: "spacefill", params: { alpha: 0.25, quality: "high" },
            });
            return w.Harness!.inspectScene(w.__controller);
        });
        const regionRepr = withRegion.regions.styled.reprs[0];
        assert.ok(regionRepr, "the region rendered no representation at all");
        assert.strictEqual(regionRepr.name, "spacefill",
            `Mol* substituted the region's representation: got ${regionRepr.name}`);
        assert.strictEqual(regionRepr.typeParams.alpha, 0.25,
            `a region's alpha never reached Mol*: ${JSON.stringify(regionRepr.typeParams)}`);
        assert.strictEqual(regionRepr.typeParams.quality, "high",
            `a region's quality never reached Mol*: ${JSON.stringify(regionRepr.typeParams)}`);
        console.log(`[E2E scene-contracts]   region: ${regionRepr.name} alpha=${regionRepr.typeParams.alpha} quality=${regionRepr.typeParams.quality}`);
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: an inheriting region follows the whole");
    {
        const before = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({
                op: "create_region", tag: "inheritor", atom_indices: [0, 1, 2, 3], representation: "inherit",
            });
            return w.Harness!.inspectScene(w.__controller);
        });
        assert.strictEqual(before.regions.inheritor.state, "inherit");
        assert.deepStrictEqual(
            before.regions.inheritor.reprs.map((r: any) => r.name),
            ["ball-and-stick"],
            "an Inherit region did not pick up the whole's current representation",
        );

        // Now change the whole. Contract A rule 4: the inheriting region must follow.
        const after = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({ op: "set_whole_representation", representation: "spacefill" });
            return w.Harness!.inspectScene(w.__controller);
        });
        assert.deepStrictEqual(
            after.regions.inheritor.reprs.map((r: any) => r.name),
            ["spacefill"],
            "the whole changed representation and the Inherit region did not follow it",
        );
        console.log("[E2E scene-contracts]   ball-and-stick -> spacefill, region followed");
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: uncoloured atoms keep the structural theme and do not turn grey");
    {
        const probe = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            return w.Harness!.probePerAtomColorDecorator(w.__controller, {
                coloredAtom: 0, uncoloredAtom: 9, color: 0xff0000,
            });
        });
        assert.strictEqual(probe.coloredAtomColor, 0xff0000, "the coloured atom did not take the layer colour");
        assert.notStrictEqual(probe.uncoloredAtomColor, GREY, "an uncoloured atom was painted grey (the old reset_colors behaviour)");
        assert.ok(probe.uncoloredAtomFallsThrough, "an uncoloured atom did not fall through to the structural theme");
        assert.strictEqual(probe.baseThemeName, "element-symbol", `base theme lost: ${probe.baseThemeName}`);
        console.log(`[E2E scene-contracts]   coloured=0x${probe.coloredAtomColor.toString(16)} uncoloured=0x${probe.uncoloredAtomColor.toString(16)} base=${probe.baseThemeName}`);
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: hiding the whole makes state-None regions vanish; Inherit and Own remain");
    {
        const snap = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({ op: "create_region", tag: "none_state", atom_indices: [4, 5] });
            await w.__controller.handleMessage({
                op: "create_region", tag: "owner", atom_indices: [6, 7], representation: "spacefill",
            });
            await w.__controller.handleMessage({ op: "hide_whole", target: "whole" });
            return w.Harness!.inspectScene(w.__controller);
        });

        assert.strictEqual(snap.wholeVisible, false, "the whole did not hide");
        // State None owns no visual: nothing else paints those atoms, so with the
        // whole hidden the region is simply not on screen.
        assert.strictEqual(snap.regions.none_state.state, "none");
        assert.strictEqual(snap.regions.none_state.reprs.length, 0,
            "a state-None region built a representation of its own");
        // Inherit and Own keep theirs, and they must still be rendered.
        const visible = (r: any) => r.reprs.length > 0 && r.reprs.every((x: any) => !x.hidden);
        assert.ok(visible(snap.regions.inheritor), "an Inherit region vanished when the whole was hidden");
        assert.ok(visible(snap.regions.owner), "an Own region vanished when the whole was hidden");
        console.log(`[E2E scene-contracts]   whole hidden: none=${snap.regions.none_state.reprs.length} reprs, inherit=${snap.regions.inheritor.reprs.length}, own=${snap.regions.owner.reprs.length}`);

        await page.evaluate(async () => {
            await (window as BrowserWindow).__controller.handleMessage({ op: "show_whole", target: "whole" });
        });
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: clearing colours restores the structural theme rather than greying the system");
    {
        const result = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            // Paint one atom of the base layer and one atom of a region layer.
            await w.__controller.handleMessage({
                op: "set_atom_colors", atom_indices: [0, 6], colors: [0xff0000, 0x00ff00], replace: true,
            });
            const painted = w.Harness!.probeAtomColors(w.__controller, [0, 6, 9]);
            // reset_all_colors -> Python clears every layer and sends this.
            await w.__controller.handleMessage({ op: "clear_atom_colors" });
            const cleared = w.Harness!.probeAtomColors(w.__controller, [0, 6, 9]);
            return { painted, cleared };
        });

        assert.strictEqual(result.painted.colors[0], 0xff0000, "the base-layer atom was not painted");
        assert.strictEqual(result.painted.colors[1], 0x00ff00, "the region-layer atom was not painted");

        // After the canvas-wide wipe every atom falls back to the structural theme.
        // The bug this guards is the old behaviour: wipe -> paint everything grey.
        for (const [i, atom] of [0, 6, 9].entries()) {
            assert.notStrictEqual(result.cleared.colors[i], GREY,
                `atom ${atom} turned grey after clearing colours instead of falling back to the structural theme`);
        }
        assert.notStrictEqual(result.cleared.colors[0], 0xff0000, "the base layer survived the wipe");
        assert.notStrictEqual(result.cleared.colors[1], 0x00ff00, "the region layer survived the wipe");
        console.log(`[E2E scene-contracts]   wiped: 0x${result.cleared.colors[0].toString(16)}, 0x${result.cleared.colors[1].toString(16)}, 0x${result.cleared.colors[2].toString(16)} (none grey)`);
    }

    // =========================================================================
    console.log("[E2E scene-contracts] Scenario: a dynamic region tracks the trajectory");
    {
        const frames = await page.evaluate(async () => {
            const w = window as BrowserWindow;
            await w.__controller.handleMessage({
                op: "create_region", tag: "dyn", atom_indices: [0, 1], representation: "ball-and-stick",
            });
            const f0 = w.Harness!.inspectScene(w.__controller).regions.dyn.atomCount;
            // What Python sends once per frame after re-evaluating the recipe.
            await w.__controller.handleMessage({
                op: "set_dynamic_region_atoms", frame: 1,
                regions: [{ tag: "dyn", atom_indices: [4, 5, 6, 7] }],
            });
            const f1 = w.Harness!.inspectScene(w.__controller);
            await w.__controller.handleMessage({
                op: "set_dynamic_region_atoms", frame: 2,
                regions: [{ tag: "dyn", atom_indices: [8, 9] }],
            });
            const f2 = w.Harness!.inspectScene(w.__controller);
            return { f0, f1: f1.regions.dyn, f2: f2.regions.dyn };
        });

        assert.strictEqual(frames.f0, 2, "the dynamic region did not start with its seed atoms");
        assert.strictEqual(frames.f1.atomCount, 4, "the dynamic region did not follow frame 1");
        assert.strictEqual(frames.f2.atomCount, 2, "the dynamic region did not follow frame 2");
        // Following the trajectory must not cost it its representation.
        assert.ok(frames.f1.reprs.length > 0 && frames.f2.reprs.length > 0,
            "the dynamic region lost its representation while tracking the trajectory");
        assert.strictEqual(frames.f2.reprs[0].name, "ball-and-stick");
        console.log(`[E2E scene-contracts]   atoms per frame: ${frames.f0} -> ${frames.f1.atomCount} -> ${frames.f2.atomCount}, representation kept`);
    }

    assert.deepStrictEqual(errors, [], `console/page errors during the run:\n${errors.join("\n")}`);
    await browser.close();
    console.log("[E2E scene-contracts] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
