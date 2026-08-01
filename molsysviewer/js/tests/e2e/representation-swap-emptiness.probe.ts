/**
 * How long is the scene empty during a whole-representation change?
 *
 * Contract S9 mechanism A. The rebuild path removes the old representations and
 * then builds the new ones, and `commit()` returns long before the geometry
 * arrives — a blank viewport the user sees, and (before camera authority was
 * taken) the window in which Mol* collapsed the camera bounds.
 * `applyWholeRepresentationInPlace` avoids it by editing the existing
 * `StructureRepresentation3D` node's params instead, the same way
 * `applyStructuralColorInPlace` has always edited its colour.
 *
 * **The measurement that matters is first change versus second**, because the
 * fast path is not reachable for the first one and that is not obvious from
 * reading the code. The initial representations come from the *loader's* preset,
 * which builds **four** of them (polymer, ligand, water, …) — measured, not
 * assumed, and not the "none yet" one might expect. Collapsing four nodes into one
 * is a change of tree shape, no parameter edit can express it, and the rebuild is
 * the only correct answer. Only from the second change on is there a single global
 * node whose params describe the whole.
 *
 * Measured on 181L, cartoon, with the change issued while the viewer is still
 * settling — the condition that opens the window at all. A settled viewer never
 * shows it, which is why changing representations by hand always looked clean:
 *
 * | | scene empty |
 * |---|---:|
 * | first change after load (rebuild) | ~740 ms |
 * | second change, same representation (in place) | **0 ms** |
 *
 * Verified by mutation: removing the in-place branch takes that 0 ms to 2960 ms.
 * Both arms build *cartoon* on purpose — an earlier version compared cartoon
 * against spacefill and was measuring build times, not code paths.
 *
 * So mechanism A does **not** help the case that produced the bug report — the
 * first cartoon after a load. That case is made harmless by mechanism B (camera
 * authority) instead, and closing its blank window needs add-before-remove, which
 * is tracked in `devguide/pending_bugs/`.
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

    const settleMs = Number(process.env.PROBE_SETTLE_MS ?? 300);
    const out = await page.evaluate(async (cfg: any) => {
        const controller = await (window as any).Harness.createController("root");
        const plugin = (controller as any).plugin;
        const c3d: any = plugin.canvas3d;

        /** Sample the scene while `action` runs; report how long it held nothing. */
        const watch = async (action: () => Promise<any>, ms: number) => {
            const series: number[] = [];
            const end = Date.now() + ms;
            const poll = (async () => {
                while (Date.now() < end) {
                    series.push(c3d.boundingSphere?.radius ?? 0);
                    await new Promise(r => setTimeout(r, 20));
                }
            })();
            await action();
            await poll;
            return {
                emptyMs: series.filter(r => r <= 0).length * 20,
                minRadius: Math.min(...series),
                samples: series.length,
            };
        };

        await controller.handleMessage({
            op: "load_structure_from_string", data: cfg.pdb, format: "pdb", label: "probe",
        });
        for (let i = 0; i < 80; i++) {
            const s = plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
            if (s && s.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }
        await new Promise(r => setTimeout(r, cfg.settleMs));

        // Four here, not zero: the loader preset already registered its
        // representations, and collapsing four nodes into one is what makes this
        // first change a rebuild.
        const globalReprsBefore = ((controller as any).state?.globalReprs?.size) ?? -1;
        const firstSwap = await watch(
            () => controller.handleMessage({
                op: "set_whole_representation",
                representation: "cartoon", preset: null, params: {},
            }),
            3000,
        );
        const globalReprsAfter = ((controller as any).state?.globalReprs?.size) ?? -1;

        // Both arms must build the *same* representation, or the comparison is
        // between cartoon and spacefill build times rather than between the two
        // code paths. Step out to spacefill (fast, not measured), then back to
        // cartoon — which now has a single global node, so it goes in place.
        await controller.handleMessage({
            op: "set_whole_representation",
            representation: "spacefill", preset: null, params: {},
        });
        await new Promise(r => setTimeout(r, 2000));
        const secondSwap = await watch(
            () => controller.handleMessage({
                op: "set_whole_representation",
                representation: "cartoon", preset: null, params: {},
            }),
            3000,
        );

        return {
            settleMs: cfg.settleMs,
            globalReprsBefore, globalReprsAfter,
            firstSwap, secondSwap,
        };
    }, { pdb: readFileSync(process.env.PROBE_PDB!, "utf8"), settleMs });

    console.log(JSON.stringify(out, null, 1));
    if (errors.length) console.log("PAGE ERRORS:", errors);
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
