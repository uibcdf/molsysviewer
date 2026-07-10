import assert from "node:assert";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ATOMS = 120;
const OWNED_ATOMS = 30;
const ATOMS_PER_RESIDUE = 10;

type PickingProbeCase = {
    case: "owned-region-visible" | "unowned-region-visible" | "owned-region-hidden";
    atomIndex: number;
    regionVisible: boolean;
    picked: boolean;
    source: "whole" | "region" | "other" | "none";
    representationRef: string | null;
    componentRef: string | null;
    atomIndices: number[];
};

function makePdb(atoms: number): string {
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
    for (let atom = 0; atom < atoms; atom++) {
        const serial = atom + 1;
        const residueIndex = Math.floor(atom / ATOMS_PER_RESIDUE);
        const residue = residueIndex + 1;
        const name = atomNames[atom % atomNames.length];
        const [dx, dy, dz] = localOffsets[atom % ATOMS_PER_RESIDUE];
        const baseX = (residueIndex % 20) * 8.0;
        const baseY = Math.floor(residueIndex / 20) * 8.0;
        const x = (baseX + dx).toFixed(3).padStart(8);
        const y = (baseY + dy).toFixed(3).padStart(8);
        const z = dz.toFixed(3).padStart(8);
        const element = name === "H" ? "H" : name[0];
        lines.push(`ATOM  ${String(serial).padStart(5)} ${name.padStart(4)} ALA A${String(residue).padStart(4)}    ${x}${y}${z}  1.00 20.00          ${element.padStart(2)}`);
    }
    lines.push("END");
    return lines.join("\n");
}

async function loadController(page: import("playwright").Page): Promise<void> {
    await page.setContent('<div id="root" style="width:1280px;height:900px"></div>');
    await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
    await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));
    const pdb = makePdb(ATOMS);
    await page.evaluate(async ({ pdbText }) => {
        const browserWindow = window as unknown as {
            Harness: { createController(target: string): Promise<any> };
            __controller?: any;
        };
        const controller = await browserWindow.Harness.createController("root");
        browserWindow.__controller = controller;
        await controller.handleMessage({ op: "load_structure_from_string", data: pdbText, format: "pdb", label: "ownership-picking-probe" });
    }, { pdbText: pdb });
    await page.waitForFunction((expectedAtoms) => {
        const controller = (window as unknown as { __controller?: { getStructureData(): { elementCount: number } | undefined } }).__controller;
        return controller?.getStructureData()?.elementCount === expectedAtoms;
    }, ATOMS, { timeout: 60_000 });
}

async function dispatchUserEvents(page: import("playwright").Page, pickPoint: [number, number]) {
    const box = await page.locator("#root canvas").boundingBox();
    assert.ok(box, "Mol* canvas was not found");
    const x = box.x + pickPoint[0];
    const y = box.y + pickPoint[1];
    const start = await page.evaluate(() => ((window as unknown as { __messages?: unknown[] }).__messages ?? []).length);
    await page.mouse.move(x, y);
    await page.waitForTimeout(120);
    await page.mouse.click(x, y);
    await page.mouse.click(x, y, { button: "right" });
    await page.waitForTimeout(120);
    return page.evaluate((from) => ((window as unknown as { __messages?: unknown[] }).__messages ?? []).slice(from), start);
}

async function runUserPathCase(
    browser: Awaited<ReturnType<typeof chromium.launch>>,
    caseName: PickingProbeCase["case"],
) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
        await loadController(page);
        const probe = await page.evaluate(async ({ atoms, ownedAtoms, requestedCase }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    probeExclusiveOwnershipPicking(
                        controller: any,
                        options: { atoms: number; ownedAtoms: number; cases: string[]; cleanup: boolean },
                    ): Promise<{ cases: PickingProbeCase[] }>;
                };
                __controller: any;
            };
            return browserWindow.Harness.probeExclusiveOwnershipPicking(browserWindow.__controller, {
                atoms,
                ownedAtoms,
                cases: [requestedCase],
                cleanup: false,
            });
        }, { atoms: ATOMS, ownedAtoms: OWNED_ATOMS, requestedCase: caseName });
        const result = probe.cases[0];
        const messages = await dispatchUserEvents(page, result.pickPoint);
        return { case: caseName, pickPoint: result.pickPoint, messages };
    } finally {
        await page.close();
    }
}

async function run(): Promise<void> {
    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    });
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        try {
            await loadController(page);
            const probe = await page.evaluate(async ({ atoms, ownedAtoms }) => {
                const browserWindow = window as unknown as {
                    Harness: {
                        probeExclusiveOwnershipPicking(controller: any, options: { atoms: number; ownedAtoms: number }): Promise<{ cases: PickingProbeCase[]; pickabilityNotes: string[] }>;
                    };
                    __controller: any;
                };
                return browserWindow.Harness.probeExclusiveOwnershipPicking(browserWindow.__controller, { atoms, ownedAtoms });
            }, { atoms: ATOMS, ownedAtoms: OWNED_ATOMS });
            const userPathCases = [];
            for (const caseName of ["owned-region-visible", "unowned-region-visible", "owned-region-hidden"] as const) {
                userPathCases.push(await runUserPathCase(browser, caseName));
            }

            console.log(JSON.stringify({
                type: "exclusive-ownership-picking-probe-raw",
                atoms: ATOMS,
                ownedAtoms: OWNED_ATOMS,
                cases: probe.cases,
                userPathCases,
                pickabilityNotes: probe.pickabilityNotes,
            }));

            const byCase = Object.fromEntries(probe.cases.map((item: PickingProbeCase) => [item.case, item]));
            assert.strictEqual(byCase["owned-region-visible"].source, "region");
            assert.strictEqual(byCase["unowned-region-visible"].source, "whole");
            assert.strictEqual(byCase["owned-region-hidden"].picked, false);
            assert.strictEqual(byCase["owned-region-hidden"].source, "none");

            console.log(JSON.stringify({
                type: "exclusive-ownership-picking-probe",
                atoms: ATOMS,
                ownedAtoms: OWNED_ATOMS,
                cases: probe.cases,
                userPathCases,
                pickabilityNotes: probe.pickabilityNotes,
                recommendation: "mask-based exclusive ownership preserves picking if the owned transparent whole fragments are discarded by the pick pass",
            }));
        } finally {
            await page.close();
        }
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
