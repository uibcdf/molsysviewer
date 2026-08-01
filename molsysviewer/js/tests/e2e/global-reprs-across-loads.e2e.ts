/**
 * Loading a second structure must not leave the whole pointing at the first.
 *
 * `LoaderHandlers` calls `clearGlobalRepresentations()` on all four load paths,
 * and the controller supplies it as a **no-op** whose comment admits the question
 * was never settled: `/* handled by state via events usually, but direct call
 * needed? state handles globals *\/`. Contract S9 item 8.
 *
 * `globalReprs` is only ever populated and cleared inside `setWholeRepresentation`
 * (and wholesale in `clearState`), so nothing on the load path touches it. This
 * measures whether that matters: after loading a second structure, how many refs
 * does the set still hold, and how many of those still exist as cells?
 *
 * Measured before the fix: after a second load the set held one ref whose cell no
 * longer existed, and that had two consequences.
 *
 * `setSubtreeVisibility` walks the state tree from the ref it is given and throws
 * on one that is gone (`TypeError: Cannot read properties of undefined (reading
 * 'ref')`), so showing or hiding the whole after a second load crashed.
 *
 * Worse, `captureInitialGlobalRepresentations` adopts the loader preset's
 * representations **only when the set is empty**. One dead ref kept it permanently
 * non-empty, so the new structure's representations were never adopted and every
 * read of `globalReprs` went on describing a structure that had been destroyed.
 *
 * The page-error assertion is not decoration here: the crash is the symptom a user
 * would hit first, and it is thrown inside Mol\* rather than by our own code.
 */
import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_A = [
    "ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N",
    "ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C",
    "ATOM      3  N   ALA A   2      13.189  11.956   8.001  1.00 20.00           N",
    "ATOM      4  CA  ALA A   2      12.589  10.935   8.353  1.00 20.00           C",
    "END",
].join("\n");

const PDB_B = [
    "ATOM      1  N   GLY B   1       5.104   3.207   2.551  1.00 20.00           N",
    "ATOM      2  CA  GLY B   1       6.560   3.329   2.276  1.00 20.00           C",
    "ATOM      3  N   SER B   2       7.189   1.956   2.001  1.00 20.00           N",
    "ATOM      4  CA  SER B   2       6.589   0.935   2.353  1.00 20.00           C",
    "END",
].join("\n");

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const browser = await chromium.launch({ headless: true, executablePath: envBin } as any);
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => {
        const stack = String((err as any).stack ?? err);
        errors.push(stack.split("\n").slice(0, 6).join(" | "));
    });

    await page.goto("about:blank");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width:800px;height:600px"></div></body></html>`,
    );
    await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    const report = await page.evaluate(async (cfg: any) => {
        const controller = await (window as any).Harness.createController("root");
        const plugin = (controller as any).plugin;
        const state = (controller as any).state;

        const load = async (pdb: string) => {
            await controller.handleMessage({
                op: "load_structure_from_string", data: pdb, format: "pdb", label: "probe",
            });
            for (let i = 0; i < 60; i++) {
                const s = plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj?.data;
                if (s && s.elementCount > 0) break;
                await new Promise(r => setTimeout(r, 100));
            }
            await new Promise(r => setTimeout(r, 600));
        };

        const census = (label: string) => {
            const refs: string[] = Array.from(state.globalReprs ?? []);
            const alive = refs.filter(ref => plugin.state.data.cells.has(ref)).length;
            return { label, held: refs.length, alive, dead: refs.length - alive };
        };

        const out: any[] = [];
        await load(cfg.a);
        out.push(census("after load A"));

        await controller.handleMessage({
            op: "set_whole_representation", representation: "spacefill", preset: null, params: {},
        });
        await new Promise(r => setTimeout(r, 800));
        out.push(census("after set_whole_representation on A"));

        await load(cfg.b);
        out.push(census("after load B"));

        return out;
    }, { a: PDB_A, b: PDB_B });

    for (const row of report) console.log(`[E2E global-reprs] ${JSON.stringify(row)}`);

    const afterSecondLoad = report[report.length - 1];
    assert.ok(
        afterSecondLoad.held > 0,
        "the whole's representations must be adopted after the second load; an empty "
        + "set means captureInitialGlobalRepresentations never ran",
    );
    assert.strictEqual(
        afterSecondLoad.dead, 0,
        `globalReprs still holds ${afterSecondLoad.dead} ref(s) whose cell is gone. `
        + "setSubtreeVisibility throws on those, and one of them keeps the set "
        + "non-empty so the new structure's representations are never adopted.",
    );
    assert.deepStrictEqual(errors, [], `page errors: ${errors.join(" | ")}`);

    console.log("[E2E global-reprs] PASS");
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
