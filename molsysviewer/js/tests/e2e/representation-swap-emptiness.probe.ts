/**
 * Does an in-place representation update keep the scene populated?
 *
 * `setWholeRepresentation` currently removes the old representations and then
 * builds the new ones, which leaves the scene empty for as long as the build
 * takes (~1.25s for 181L's cartoon). That empty window collapses
 * `camera.state.radiusMax` and the trackball then clamps the camera inside the
 * molecule — see
 * `devguide/pending_bugs/camera_zoom_out_blocked_after_scene_replay.md`.
 *
 * The codebase already updates the *colour* of a representation in place
 * (`applyStructuralColorInPlace`), and colour changes visibly do not flash. The
 * representation type lives in the same transform's params, so the question is
 * whether swapping it the same way avoids the empty window entirely.
 *
 * Measures both paths on the same structure: minimum scene radius and how long
 * the scene stays empty.
 */
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const browser = await chromium.launch({ headless: true, executablePath: envBin } as any);
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    await page.goto("about:blank");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width: 800px; height: 600px;"></div></body></html>`,
    );
    await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");
    const settleMs = Number(process.env.PROBE_SETTLE_MS ?? 1500);
    await page.evaluate((v: number) => { (window as any).__settleMs = v; }, settleMs);
    console.log("settleMs:", settleMs);

    const out = await page.evaluate(async (pdb: string) => {
        const controller = await (window as any).Harness.createController("root");
        const plugin = (controller as any).plugin;
        const c3d: any = plugin.canvas3d;

        const sample = () => ({
            radius: c3d.boundingSphere?.radius ?? 0,
            reprCount: c3d.reprCount?.value ?? 0,
            radiusMax: c3d.camera?.state?.radiusMax ?? 0,
        });

        /** Watch the scene while `action` runs, for `ms` total. */
        const watch = async (action: () => Promise<any>, ms: number) => {
            const series: any[] = [];
            let done = false;
            const poll = (async () => {
                const end = Date.now() + ms;
                while (Date.now() < end) {
                    series.push({ t: Date.now(), ...sample() });
                    await new Promise(r => setTimeout(r, 20));
                    if (done && Date.now() > end - ms * 0.4) break;
                }
            })();
            await action();
            done = true;
            await poll;
            const emptySamples = series.filter(s => s.radius <= 0).length;
            return {
                minRadius: Math.min(...series.map(s => s.radius)),
                minReprCount: Math.min(...series.map(s => s.reprCount)),
                zeroReprSamples: series.filter(s => s.reprCount === 0).length,
                minRadiusMax: Math.min(...series.map(s => s.radiusMax)),
                emptyMs: emptySamples * 20,
                samples: series.length,
            };
        };

        await controller.handleMessage({
            op: "load_structure_from_string", data: pdb, format: "pdb", label: "probe",
        });
        for (let i = 0; i < 80; i++) {
            const s = plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (s && s.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
        await new Promise(r => setTimeout(r, Number((window as any).__settleMs ?? 1500)));
        const baseline = sample();

        // --- current path: remove, then add -------------------------------
        const removeThenAdd = await watch(
            () => controller.handleMessage({
                op: "set_whole_representation",
                representation: "cartoon", preset: null, params: {},
            }),
            3000,
        );
        // Back to a non-cartoon state so the second measurement builds the very
        // same representation from the very same starting point.
        await controller.handleMessage({
            op: "set_whole_representation",
            representation: "ball_and_stick", preset: null, params: {},
        });
        await new Promise(r => setTimeout(r, 2500));

        // --- candidate path: update the existing transform in place -------
        const reprRefs: string[] = [];
        plugin.state.data.cells.forEach((cell: any, ref: string) => {
            const id = String(cell?.transform?.transformer?.id ?? "");
            if (id.includes("structure-representation-3d")) reprRefs.push(ref);
        });

        const inPlace = await watch(
            async () => {
                const update = plugin.state.data.build();
                for (const ref of reprRefs) {
                    update.to(ref).update((params: any) => {
                        params.type = { name: "cartoon", params: {} };
                    });
                }
                await update.commit({ doNotUpdateCurrent: true });
            },
            3000,
        );

        // --- third arm: the current path, but with Mol* told not to re-derive
        // the camera from a half-built scene while the mutation is in flight ---
        await controller.handleMessage({
            op: "set_whole_representation",
            representation: "ball_and_stick", preset: null, params: {},
        });
        await new Promise(r => setTimeout(r, 2500));
        const guarded = await watch(
            async () => {
                c3d.setProps({ camera: { manualReset: true } });
                try {
                    await controller.handleMessage({
                        op: "set_whole_representation",
                        representation: "cartoon", preset: null, params: {},
                    });
                    // Wait for the scene to come back before handing authority over.
                    for (let i = 0; i < 200; i++) {
                        if ((c3d.boundingSphere?.radius ?? 0) > 0 && (c3d.reprCount?.value ?? 0) > 0) break;
                        await new Promise(r => setTimeout(r, 20));
                    }
                } finally {
                    c3d.setProps({ camera: { manualReset: false } });
                }
            },
            3000,
        );

        return { baseline, removeThenAdd, inPlace, guarded, reprRefCount: reprRefs.length };
    }, readFileSync(process.env.PROBE_PDB!, "utf8"));

    console.log(JSON.stringify(out, null, 1));
    if (errors.length) console.log("PAGE ERRORS:", errors);
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
