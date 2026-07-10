import assert from "node:assert";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ATOMS = 95_000;
const ATOMS_PER_RESIDUE = 10;
const UNKNOWN_OP_BUDGET_MS = 5;
const HIDE_REGION_BUDGET_MS = 20;
const GROUP_NODE_CEILING = ATOMS / ATOMS_PER_RESIDUE;

function makePdb(): string {
    const lines: string[] = [];
    const atomNames = ["N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "H"];
    const localOffsets: Array<[number, number, number]> = [
        [0.00, 0.00, 0.00],
        [1.45, 0.00, 0.00],
        [2.15, 1.25, 0.00],
        [3.35, 1.25, 0.00],
        [1.45, -0.75, 1.20],
        [2.75, -1.20, 1.40],
        [3.85, -0.35, 1.10],
        [5.10, -0.65, 1.25],
        [6.15, 0.20, 1.10],
        [-0.55, -0.65, 0.00],
    ];
    for (let atom = 0; atom < ATOMS; atom++) {
        const serial = atom + 1;
        const residueIndex = Math.floor(atom / ATOMS_PER_RESIDUE);
        const residue = residueIndex + 1;
        const name = atomNames[atom % atomNames.length];
        const [dx, dy, dz] = localOffsets[atom % ATOMS_PER_RESIDUE];
        const baseX = (residueIndex % 100) * 8.0;
        const baseY = (Math.floor(residueIndex / 100) % 100) * 8.0;
        const baseZ = Math.floor(residueIndex / 10_000) * 8.0;
        const x = (baseX + dx).toFixed(3).padStart(8);
        const y = (baseY + dy).toFixed(3).padStart(8);
        const z = (baseZ + dz).toFixed(3).padStart(8);
        const element = name === "H" ? "H" : name[0];
        lines.push(`ATOM  ${String(serial).padStart(5)} ${name.padStart(4)} ALA A${String(residue).padStart(4)}    ${x}${y}${z}  1.00 20.00          ${element.padStart(2)}`);
    }
    lines.push("END");
    return lines.join("\n");
}

async function medianMs(page: import("playwright").Page, expression: string, iterations = 5): Promise<number> {
    const samples: number[] = [];
    for (let index = 0; index < iterations; index++) {
        samples.push(await page.evaluate(async source => {
            const started = performance.now();
            await (0, eval)(source);
            return performance.now() - started;
        }, expression));
    }
    samples.sort((left, right) => left - right);
    return samples[Math.floor(samples.length / 2)];
}

async function run(): Promise<void> {
    let browser: Awaited<ReturnType<typeof chromium.launch>>;
    try {
        browser = await chromium.launch({
            headless: true,
            executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
            args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        });
    } catch (error) {
        const message = String(error);
        if (
            process.env.PERF_SKIP === "1"
            && (message.includes("crashpad") || message.includes("sandbox") || message.includes("Operation not permitted"))
        ) {
            console.warn("[perf] Chromium launch blocked by the host sandbox; PERF_SKIP=1 requested, skipping performance budgets.");
            return;
        }
        throw error;
    }
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        await page.setContent('<div id="root" style="width:1280px;height:900px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));
        const pdb = makePdb();
        const loadMs = await page.evaluate(async pdbText => {
            const browserWindow = window as unknown as { Harness: { createController(target: string): Promise<any> }; __controller?: any };
            const controller = await browserWindow.Harness.createController("root");
            browserWindow.__controller = controller;
            const started = performance.now();
            await controller.handleMessage({ op: "load_structure_from_string", data: pdbText, format: "pdb", label: "perf-95k" });
            return performance.now() - started;
        }, pdb);
        await page.waitForFunction(() => {
            const controller = (window as unknown as { __controller?: { getStructureData(): { elementCount: number } | undefined } }).__controller;
            return controller?.getStructureData()?.elementCount === 95_000;
        }, undefined, { timeout: 60_000 });
        await page.evaluate(() => {
            const controller = (window as unknown as { __controller: { plugin: { canvas3d?: { pause(value: boolean): void } } } }).__controller;
            controller.plugin.canvas3d?.pause(true);
        });
        await page.evaluate(async () => {
            const controller = (window as unknown as { __controller: { handleMessage(message: Record<string, unknown>): Promise<void> } }).__controller;
            await controller.handleMessage({ op: "create_region", tag: "perf-region", atom_indices: [0, 1, 2], representation: "ball-and-stick" });
        });
        const unknownMs = await medianMs(page, "window.__controller.handleMessage({ op: '__does_not_exist__' })");
        const hideMs = await medianMs(page, "window.__controller.handleMessage({ op: 'hide_region', tag: 'perf-region' })");
        const groupNodes = await page.locator('[data-molsysviewer-group-item="true"]').count();
        console.log(JSON.stringify({ machine: process.platform, atoms: ATOMS, loadMs, unknownMs, hideMs, groupNodes }));
        assert.ok(unknownMs < UNKNOWN_OP_BUDGET_MS, `unknown op ${unknownMs.toFixed(2)}ms exceeds ${UNKNOWN_OP_BUDGET_MS}ms`);
        assert.ok(hideMs < HIDE_REGION_BUDGET_MS, `hide_region ${hideMs.toFixed(2)}ms exceeds ${HIDE_REGION_BUDGET_MS}ms`);
        assert.ok(groupNodes > 0, "expected the hierarchy strip to contain residue nodes");
        assert.ok(groupNodes <= GROUP_NODE_CEILING, `System panel created ${groupNodes} group nodes; ceiling is ${GROUP_NODE_CEILING}`);
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
