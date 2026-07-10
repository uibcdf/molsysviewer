import assert from "node:assert";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ATOMS = 120;
const OWNED_ATOMS = 30;
const ATOMS_PER_RESIDUE = 10;

type ProbeResult = {
    globalRepresentationRefs: string[];
    wholeComponentRepresentationCount: number;
    wholeTransparencyRecords: Array<{
        representationRef: string;
        layerValues: number[];
        atomCount: number;
        atomSetMatchesExpected: boolean;
    }>;
    regionTransparencyRecords: unknown[];
    expectedMaskedAtoms: number;
    wholeOwnedAtomsTransparent: boolean;
    regionOwnedAtomsOpaque: boolean;
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
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdbText,
            format: "pdb",
            label: "global-representation-ownership-mask-probe",
        });
    }, { pdbText: pdb });
    await page.waitForFunction((expectedAtoms) => {
        const controller = (window as unknown as { __controller?: { getStructureData(): { elementCount: number } | undefined } }).__controller;
        return controller?.getStructureData()?.elementCount === expectedAtoms;
    }, ATOMS, { timeout: 60_000 });
}

async function runCase(
    browser: Awaited<ReturnType<typeof chromium.launch>>,
    name: "direct" | "user-preset",
    globalMessage: Record<string, unknown>,
): Promise<{ name: string; result: ProbeResult }> {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
        await loadController(page);
        const result = await page.evaluate(async ({ atoms, ownedAtoms, message }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    probeGlobalRepresentationOwnershipMask(
                        controller: any,
                        options: { atoms: number; ownedAtoms: number; globalMessage: Record<string, unknown> },
                    ): Promise<ProbeResult>;
                };
                __controller: any;
            };
            return browserWindow.Harness.probeGlobalRepresentationOwnershipMask(browserWindow.__controller, {
                atoms,
                ownedAtoms,
                globalMessage: message,
            });
        }, { atoms: ATOMS, ownedAtoms: OWNED_ATOMS, message: globalMessage });
        return { name, result };
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
        const cases = [
            await runCase(browser, "direct", { representation: "spacefill", params: {} }),
            await runCase(browser, "user-preset", {
                user_preset: {
                    name: "probe-user-preset",
                    base: "auto",
                    rules: [],
                },
                params: {},
            }),
        ];

        for (const item of cases) {
            assert.ok(item.result.globalRepresentationRefs.length > 0, `${item.name}: expected global representation refs`);
            assert.strictEqual(item.result.wholeOwnedAtomsTransparent, true, `${item.name}: whole owned atoms must be transparent`);
            assert.strictEqual(item.result.regionOwnedAtomsOpaque, true, `${item.name}: region component must stay opaque`);
            assert.strictEqual(
                item.result.wholeTransparencyRecords.some(record => (
                    record.atomCount === OWNED_ATOMS
                    && record.layerValues.every(value => value === 1)
                    && record.atomSetMatchesExpected
                )),
                true,
                `${item.name}: expected a full transparency layer on global representation refs`,
            );
        }

        console.log(JSON.stringify({
            type: "global-representation-ownership-mask-probe",
            atoms: ATOMS,
            ownedAtoms: OWNED_ATOMS,
            cases,
        }));
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
