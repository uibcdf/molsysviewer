/**
 * uibcdf/molsysviewer#64 — a repeated chain label must not cost the copies their cartoon.
 *
 * A bioassembly reuses the asymmetric unit's chain labels: 2BUK's 60 copies all call
 * their chains A-E, so the payload carries 300 chains under 5 distinct `chain_id`
 * values, and 95 280 atoms under 1 588 distinct `atom_id` values. `structure.ts` feeds
 * `chain_id` into both `label_asym_id` and `auth_asym_id`, and `residue_id` into
 * `label_seq_id` and `auth_seq_id`, which is where Mol* builds its chain and residue
 * hierarchy from.
 *
 * It could not be settled by reading. The copies are contiguous, so the label sequence
 * still changes at every copy boundary (A B A B ...), and Mol* might have segmented on the
 * change rather than on the value. Measured, it does not: two copies under one label built
 * one chain and four residues instead of two and eight, with all 32 atoms present. The
 * hierarchy was lost, not the data, which is why the waters -- per-atom points needing no
 * hierarchy -- kept rendering while the cartoon did not.
 *
 * So the internal identity now travels beside the label: `chain_index` and `residue_index`
 * feed `label_asym_id` and `label_seq_id`, while `chain_id` and `residue_id` stay in
 * `auth_*` where the user reads and selects them.
 */

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import assert from "node:assert/strict";

import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run(): Promise<void> {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.setContent(
            '<!doctype html><html><body><div id="root" style="width:800px;height:600px"></div></body></html>',
        );
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as any).Harness));

        const result = await page.evaluate(async () => {
            const harness = (window as any).Harness;

            // Four residues of backbone, twice: copy 1 at the origin, copy 2 translated
            // by 20 A. Enough for a cartoon trace, small enough to read the answer.
            const RESIDUES = 4;
            const PER_RESIDUE = ["N", "CA", "C", "O"];
            const build = (uniqueLabels: boolean) => {
                const atom_id: number[] = [];
                const atom_name: string[] = [];
                const element_symbol: string[] = [];
                const residue_id: number[] = [];
                const residue_name: string[] = [];
                const chain_id: string[] = [];
                const entity_id: string[] = [];
                const group_type: string[] = [];
                const chain_index: number[] = [], residue_index: number[] = [];
                const xs: number[] = [], ys: number[] = [], zs: number[] = [];
                for (let copy = 0; copy < 2; copy++) {
                    for (let r = 0; r < RESIDUES; r++) {
                        for (let a = 0; a < PER_RESIDUE.length; a++) {
                            // The bioassembly case: identifiers restart with every copy.
                            const serial = r * PER_RESIDUE.length + a + 1;
                            atom_id.push(uniqueLabels ? copy * 100 + serial : serial);
                            atom_name.push(PER_RESIDUE[a]);
                            element_symbol.push(PER_RESIDUE[a][0]);
                            residue_id.push(uniqueLabels ? copy * 100 + r + 1 : r + 1);
                            residue_name.push("ALA");
                            chain_id.push(uniqueLabels ? (copy === 0 ? "A" : "B") : "A");
                            entity_id.push("1");
                            group_type.push("amino acid");
                            chain_index.push(copy);
                            residue_index.push(copy * RESIDUES + r);
                            xs.push(copy * 20 + r * 3.8 + a * 0.6);
                            ys.push(a * 0.4);
                            zs.push(0);
                        }
                    }
                }
                const n = atom_id.length;
                const coordinates = new Float32Array([...xs, ...ys, ...zs]);
                return {
                    protocol_version: 1,
                    n_atoms: n,
                    n_structures: 1,
                    atoms: { atom_id, atom_name, element_symbol, residue_id,
                             residue_name, chain_id, entity_id, group_type,
                             chain_index, residue_index },
                    structural_arrays: [{
                        kind: "coordinates" as const,
                        dtype: "float32" as const,
                        shape: [1, n, 3],
                        buffer_index: 0,
                    }],
                    buffers: [coordinates.buffer],
                    coordinates,
                };
            };

            const measure = async (uniqueLabels: boolean) => {
                const controller = await harness.createController("root");
                const meta = build(uniqueLabels);
                await controller.handleMessage({
                    op: "load_molsys_payload",
                    payload: {
                        atoms: meta.atoms,
                        structures: [{
                            coordinates: Array.from({ length: meta.n_atoms }, (_, i) => [
                                meta.coordinates[i],
                                meta.coordinates[meta.n_atoms + i],
                                meta.coordinates[2 * meta.n_atoms + i],
                            ]),
                        }],
                    },
                    multiple_structures: false,
                });
                await controller.handleMessage({ op: "show_whole", target: "whole" });
                await new Promise(r => setTimeout(r, 400));

                const plugin = (controller as any).plugin ?? (controller as any)._plugin;
                const cells = plugin?.state?.data?.select
                    ? plugin.state.data.selectQ((q: any) => q.ofType)
                    : null;
                // Read Mol*'s own model rather than our bookkeeping.
                let chains = -1, residues = -1, atoms = -1;
                const structures = plugin?.managers?.structure?.hierarchy?.current?.structures ?? [];
                const model = structures[0]?.model?.cell?.obj?.data;
                if (model) {
                    chains = model.atomicHierarchy.chains._rowCount;
                    residues = model.atomicHierarchy.residues._rowCount;
                    atoms = model.atomicHierarchy.atoms._rowCount;
                }
                return { chains, residues, atoms };
            };

            const repeated = await measure(false);
            const unique = await measure(true);
            return { repeated, unique };
        });

        assert.deepEqual(errors, []);
        // Both must build the same hierarchy. The point of the fix is that repeating the
        // author's labels -- which is what a bioassembly does -- costs nothing, because
        // the internal identity travels separately.
        assert.deepEqual(
            result.repeated,
            { chains: 2, residues: 8, atoms: 32 },
            "copies sharing an author chain label collapsed into one chain's hierarchy; "
            + "every atom arrives, but only one copy can be traced as cartoon (#64)",
        );
        assert.deepEqual(result.unique, { chains: 2, residues: 8, atoms: 32 });
        console.log("bioassembly-chain-identity: ok");
    } finally {
        await browser.close();
    }
}

run().catch(error => { console.error(error); process.exit(1); });
