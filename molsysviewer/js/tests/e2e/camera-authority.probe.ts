/**
 * Can we own the camera bounds outright instead of guarding them per mutation?
 *
 * Contract S9 currently proposes a per-mutation guard (`camera.manualReset` held
 * for the duration), which carries an unsolved question — when has the mutation
 * finished? — and a hole: `requestCameraReset` is not gated by that flag, so a
 * "Reset view" landing mid-mutation still pins the trackball bound.
 *
 * This probes a standing configuration instead:
 *   - `camera.manualReset: true` — Mol* never re-derives `radiusMax` from a
 *     transient scene (`canvas3d.js:744` is gated on it);
 *   - `trackball.autoAdjustMinMaxDistance: off` — `p.maxDistance` stays at its
 *     1e150 default instead of being set from the *visible* bounding sphere
 *     (`canvas3d.js:678-685`), which also makes `resolveCameraReset` a no-op on an
 *     empty scene, closing the reset hole;
 *   - one explicit `requestCameraReset()` once the load has settled, which frames
 *     the structure *and* sets `radiusMax` from a finished scene
 *     (`canvas3d.js:691`, not gated by manualReset).
 *
 * Compares default configuration against that one, both swapping while the viewer
 * is still settling — the condition that opens the empty window.
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

        if (cfg.ownAuthority) {
            c3d.setProps({
                camera: { manualReset: true },
                trackball: { autoAdjustMinMaxDistance: { name: "off", params: {} } },
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

        await controller.handleMessage({
            op: "load_structure_from_string", data: cfg.pdb, format: "pdb", label: "probe",
        });
        for (let i = 0; i < 80; i++) {
            const s = plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (s && s.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
        // With authority taken, framing is ours to ask for, once, on a settled scene.
        if (cfg.ownAuthority) {
            for (let i = 0; i < 100; i++) {
                if ((c3d.boundingSphere?.radius ?? 0) > 0) break;
                await new Promise(r => setTimeout(r, 20));
            }
            c3d.requestCameraReset?.({ durationMs: 0 });
        }
        await new Promise(r => setTimeout(r, 1000));
        const afterLoad = { distance: dist(), ...bounds() };

        // The swap, issued while the viewer is still settling.
        await new Promise(r => setTimeout(r, 300));
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

        return { afterLoad, worst, final: { distance: dist(), ...bounds() } };
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

    const pdb = readFileSync(process.env.PROBE_PDB!, "utf8");
    console.log("default config    :", JSON.stringify(await measure(page, pdb, false)));
    console.log("authority taken   :", JSON.stringify(await measure(page, pdb, true)));
    if (errors.length) console.log("PAGE ERRORS:", errors);
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
