/**
 * Camera authority (Contract S9): does the standing configuration hold the camera
 * bounds through a scene mutation that would otherwise collapse them?
 *
 * Runs the same scenario twice — swap the whole representation while the viewer is
 * still settling from the load, the condition the S8 burst replay creates — once
 * with the controller's configuration (`camera.manualReset`,
 * `trackball.autoAdjustMinMaxDistance: off`) and once with it handed back to stock
 * Mol*.
 *
 * **What it establishes.** Both bounds that `checkDistances` takes the smaller of:
 *
 * | | `radiusMax` (min) | trackball `maxDistance` |
 * |---|---:|---:|
 * | stock Mol* | **0.01** | **20** |
 * | authority taken | 10 (the untouched default) | **1e150** |
 *
 * Reproducible: three runs of three. The collapse is the precondition for the
 * defect, and the configuration removes it.
 *
 * **What it does not establish.** That the collapsed bound then drags the camera.
 * That half needs frames to land inside the window where the scene is *fully
 * committed and empty*, and this harness coalesces the removal and addition
 * commits so the window rarely exists as a drawn state. It was measured
 * separately, on a settled scene with `radiusMax` forced to 0.01: the camera moved
 * from 79.79 to exactly 10 — `radiusMax * 1000` — within five frames. That number
 * is recorded in Contract S9.
 *
 * So: this probe covers the link the fix acts on, and S9 records the link that
 * makes it matter. Neither is inferred.
 *
 * `framedAtMs` also tracks framing latency, because taking authority means Mol*
 * no longer frames anything and `frameLoadedStructure` becomes the only thing
 * that does: ~965ms here against ~1600ms for stock Mol*.
 */
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function measure(page: any, pdb: string, ownAuthority: boolean) {
    return page.evaluate(async (cfg: any) => {
        document.getElementById("root")!.innerHTML = "";
        const controller = await (window as any).Harness.createController("root");
        const plugin = (controller as any).plugin;
        const c3d: any = plugin.canvas3d;

        if (!cfg.ownAuthority) {
            // The controller now takes authority at init (Contract S9), so the
            // comparison arm has to hand it back to reproduce stock Mol* behaviour.
            c3d.setProps({
                camera: { manualReset: false },
                trackball: {
                    autoAdjustMinMaxDistance: {
                        name: "on",
                        params: {
                            minDistanceFactor: 0, minDistancePadding: 5,
                            maxDistanceFactor: 10, maxDistanceMin: 20,
                        },
                    },
                },
            });
        }

        const dist = () => {
            const st = c3d.camera.state;
            return +Math.hypot(
                st.position[0] - st.target[0],
                st.position[1] - st.target[1],
                st.position[2] - st.target[2],
            ).toFixed(2);
        };
        const bounds = () => ({
            radiusMax: +(c3d.camera.state.radiusMax ?? -1).toFixed(3),
            trackballMax: (c3d.props?.trackball?.maxDistance ?? -1),
            sceneRadius: +(c3d.boundingSphere?.radius ?? 0).toFixed(2),
        });

        // A visible canvas draws continuously; this harness draws only when asked.
        // Camera resets are *resolved* during a draw, so without a pump the framing
        // sits pending and the measurement blames the code for the harness.
        let pumping = true;
        const pump = (async () => {
            while (pumping) {
                c3d.requestDraw?.();
                await new Promise(r => setTimeout(r, 16));
            }
        })();
        const framedAt = { ms: -1 };
        const t0 = Date.now();
        const watchFraming = (async () => {
            while (Date.now() - t0 < 6000) {
                if (framedAt.ms < 0 && dist() < 95 && (c3d.boundingSphere?.radius ?? 0) > 0) {
                    framedAt.ms = Date.now() - t0;
                }
                await new Promise(r => setTimeout(r, 20));
            }
        })();

        await controller.handleMessage({
            op: "load_structure_from_string", data: cfg.pdb, format: "pdb", label: "probe",
        });
        for (let i = 0; i < 80; i++) {
            const s = plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (s && s.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
        // With authority taken, framing is ours to ask for, once, on a settled scene.
        // Framing is `frameLoadedStructure`'s job now, in the controller itself.
        const afterLoad = { distance: dist(), ...bounds() };

        // The swap, issued while the viewer is still settling — the condition that
        // opens the empty window, and the one the S8 burst replay creates.
        await new Promise(r => setTimeout(r, Number((window as any).__swapDelayMs ?? 300)));
        const worst = { radiusMax: Infinity, trackballMax: Infinity, distance: Infinity };
        const watching = (async () => {
            for (let i = 0; i < 150; i++) {
                const b = bounds();
                worst.radiusMax = Math.min(worst.radiusMax, b.radiusMax);
                worst.trackballMax = Math.min(worst.trackballMax, b.trackballMax);
                worst.distance = Math.min(worst.distance, dist());
                c3d.requestDraw?.();
                await new Promise(r => setTimeout(r, 20));
            }
        })();
        await controller.handleMessage({
            op: "set_whole_representation", representation: "cartoon", preset: null, params: {},
        });
        await watching;

        pumping = false;
        await pump;
        await watchFraming;
        return { framedAtMs: framedAt.ms, afterLoad, worst, final: { distance: dist(), ...bounds() } };
    }, { pdb, ownAuthority });
}

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
    const swapDelayMs = Number(process.env.PROBE_SWAP_DELAY_MS ?? 300);
    await page.evaluate((v: number) => { (window as any).__swapDelayMs = v; }, swapDelayMs);

    const pdb = readFileSync(process.env.PROBE_PDB!, "utf8");
    console.log("default config    :", JSON.stringify(await measure(page, pdb, false)));
    console.log("authority taken   :", JSON.stringify(await measure(page, pdb, true)));
    if (errors.length) console.log("PAGE ERRORS:", errors);
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
