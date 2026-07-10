import assert from "node:assert";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SIZES = [2_000, 20_000, 95_000] as const;
const FRACTIONS = [0.10, 0.50, 0.90] as const;
const ATOMS_PER_RESIDUE = 10;
const TOGGLES = 10;

type MaskToggleProfile = {
    index: number;
    regionVisible: boolean;
    maskedAtoms: number;
    regionToggleMs: number;
    clearTransparencyMs: number;
    buildSelectionMs: number;
    lociMs: number;
    applyTransparencyMs: number;
    totalMs: number;
};

type ComponentProbe = {
    wholeComponentRefsBeforeRegion: string[];
    wholeComponentRefsAfterRegion: string[];
    targetWholeComponentRefs: string[];
    regionComponentRef: string | null;
    regionIncludedInGetComponents: boolean;
};

type TransparencyRecord = {
    componentRef: string;
    representationRef: string;
    layerCount: number;
    layerValues: number[];
    atomCount: number;
};

type InvariantProbe = {
    targetWholeComponentRefs: string[];
    regionComponentRef: string | null;
    wholeTransparencyRecords: TransparencyRecord[];
    regionTransparencyRecords: TransparencyRecord[];
    wholeMaskedAtoms: number;
    regionMaskedAtoms: number;
    expectedMaskedAtoms: number;
    wholeOwnedAtomsTransparent: boolean;
    regionOwnedAtomsOpaque: boolean;
    wholeUnownedAtomsOpaque: boolean;
};

type ScenarioSummary = {
    type: "exclusive-ownership-mask" | "exclusive-ownership-control" | "exclusive-ownership-rebuild-reference";
    atoms: number;
    fraction: number;
    ownedAtoms: number;
    rasterizer: "paused" | "live";
    loadMs: number;
    componentProbe?: ComponentProbe;
    invariantProbe?: InvariantProbe | null;
    medians: Record<keyof Omit<MaskToggleProfile, "index" | "regionVisible" | "maskedAtoms">, number>;
    toggles: MaskToggleProfile[];
};

type RebuildToggleProfile = {
    index: number;
    regionVisible: boolean;
    wholeAtoms: number;
    regionToggleMs: number;
    removeMs: number;
    buildSelectionMs: number;
    bundleMs: number;
    componentCommitMs: number;
    addRepresentationMs: number;
    totalMs: number;
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

function median(values: number[]): number {
    const sorted = [...values].sort((left, right) => left - right);
    return sorted[Math.floor(sorted.length / 2)];
}

function summarize(
    type: ScenarioSummary["type"],
    atoms: number,
    fraction: number,
    paused: boolean,
    loadMs: number,
    toggles: MaskToggleProfile[],
    componentProbe?: ComponentProbe,
    invariantProbe?: InvariantProbe | null,
): ScenarioSummary {
    assert.strictEqual(toggles.length, TOGGLES);
    const keys: Array<keyof ScenarioSummary["medians"]> = [
        "regionToggleMs",
        "clearTransparencyMs",
        "buildSelectionMs",
        "lociMs",
        "applyTransparencyMs",
        "totalMs",
    ];
    const medians = Object.fromEntries(
        keys.map((key) => [key, median(toggles.map((item) => item[key]))]),
    ) as ScenarioSummary["medians"];
    return {
        type,
        atoms,
        fraction,
        ownedAtoms: Math.floor(atoms * fraction),
        rasterizer: paused ? "paused" : "live",
        loadMs,
        componentProbe,
        invariantProbe,
        medians,
        toggles,
    };
}

function summarizeRebuild(atoms: number, paused: boolean, loadMs: number, toggles: RebuildToggleProfile[]) {
    const medians = {
        regionToggleMs: median(toggles.map((item) => item.regionToggleMs)),
        removeMs: median(toggles.map((item) => item.removeMs)),
        buildSelectionMs: median(toggles.map((item) => item.buildSelectionMs)),
        bundleMs: median(toggles.map((item) => item.bundleMs)),
        componentCommitMs: median(toggles.map((item) => item.componentCommitMs)),
        addRepresentationMs: median(toggles.map((item) => item.addRepresentationMs)),
        totalMs: median(toggles.map((item) => item.totalMs)),
    };
    return {
        type: "exclusive-ownership-rebuild-reference",
        atoms,
        fraction: 0.10,
        ownedAtoms: Math.floor(atoms * 0.10),
        rasterizer: paused ? "paused" : "live",
        loadMs,
        medians,
        toggles,
    };
}

function recommendation(ms: number): string {
    if (ms < 150) return "adopt exclusive ownership fully with whole masking";
    if (ms <= 500) return "adopt exclusive ownership with deferred/debounced whole masking";
    return "keep ownership between regions only; leave whole underneath";
}

async function loadController(page: import("playwright").Page, atoms: number): Promise<number> {
    await page.setContent('<div id="root" style="width:1280px;height:900px"></div>');
    await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
    await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));
    const pdb = makePdb(atoms);
    const loadMs = await page.evaluate(async ({ pdbText }) => {
        const browserWindow = window as unknown as {
            Harness: { createController(target: string): Promise<any> };
            __controller?: any;
        };
        const controller = await browserWindow.Harness.createController("root");
        browserWindow.__controller = controller;
        const started = performance.now();
        await controller.handleMessage({ op: "load_structure_from_string", data: pdbText, format: "pdb", label: `ownership-${pdbText.length}` });
        return performance.now() - started;
    }, { pdbText: pdb });
    await page.waitForFunction((expectedAtoms) => {
        const controller = (window as unknown as { __controller?: { getStructureData(): { elementCount: number } | undefined } }).__controller;
        return controller?.getStructureData()?.elementCount === expectedAtoms;
    }, atoms, { timeout: 60_000 });
    return loadMs;
}

async function runMaskScenario(browser: Awaited<ReturnType<typeof chromium.launch>>, atoms: number, fraction: number, paused: boolean): Promise<ScenarioSummary> {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
        const loadMs = await loadController(page, atoms);
        const result = await page.evaluate(async ({ expectedAtoms, ownedAtoms, nToggles, pauseRasterizer }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    profileExclusiveOwnershipMask(
                        controller: any,
                        options: { atoms: number; ownedAtoms: number; toggles: number; paused: boolean },
                    ): Promise<{ componentProbe: ComponentProbe; invariantProbe: InvariantProbe | null; toggles: MaskToggleProfile[] }>;
                };
                __controller: any;
            };
            return browserWindow.Harness.profileExclusiveOwnershipMask(browserWindow.__controller, {
                atoms: expectedAtoms,
                ownedAtoms,
                toggles: nToggles,
                paused: pauseRasterizer,
            });
        }, {
            expectedAtoms: atoms,
            ownedAtoms: Math.floor(atoms * fraction),
            nToggles: TOGGLES,
            pauseRasterizer: paused,
        });
        assert.ok(result.invariantProbe, "mask scenario did not produce an invariant probe");
        assert.strictEqual(result.invariantProbe.wholeOwnedAtomsTransparent, true);
        assert.strictEqual(result.invariantProbe.regionOwnedAtomsOpaque, true);
        assert.strictEqual(result.invariantProbe.wholeUnownedAtomsOpaque, true);
        return summarize("exclusive-ownership-mask", atoms, fraction, paused, loadMs, result.toggles, result.componentProbe, result.invariantProbe);
    } finally {
        await page.close();
    }
}

async function runControlScenario(browser: Awaited<ReturnType<typeof chromium.launch>>, atoms: number, fraction: number, paused: boolean): Promise<ScenarioSummary> {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
        const loadMs = await loadController(page, atoms);
        const toggles = await page.evaluate(async ({ expectedAtoms, ownedAtoms, nToggles, pauseRasterizer }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    profileRegionVisibilityControl(
                        controller: any,
                        options: { atoms: number; ownedAtoms: number; toggles: number; paused: boolean },
                    ): Promise<MaskToggleProfile[]>;
                };
                __controller: any;
            };
            return browserWindow.Harness.profileRegionVisibilityControl(browserWindow.__controller, {
                atoms: expectedAtoms,
                ownedAtoms,
                toggles: nToggles,
                paused: pauseRasterizer,
            });
        }, {
            expectedAtoms: atoms,
            ownedAtoms: Math.floor(atoms * fraction),
            nToggles: TOGGLES,
            pauseRasterizer: paused,
        });
        return summarize("exclusive-ownership-control", atoms, fraction, paused, loadMs, toggles);
    } finally {
        await page.close();
    }
}

async function runRebuildReferenceScenario(browser: Awaited<ReturnType<typeof chromium.launch>>, atoms: number, paused: boolean) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
        const loadMs = await loadController(page, atoms);
        const toggles = await page.evaluate(async ({ expectedAtoms, ownedAtoms, nToggles, pauseRasterizer }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    profileExclusiveOwnership(
                        controller: any,
                        options: { atoms: number; ownedAtoms: number; toggles: number; paused: boolean },
                    ): Promise<RebuildToggleProfile[]>;
                };
                __controller: any;
            };
            return browserWindow.Harness.profileExclusiveOwnership(browserWindow.__controller, {
                atoms: expectedAtoms,
                ownedAtoms,
                toggles: nToggles,
                paused: pauseRasterizer,
            });
        }, {
            expectedAtoms: atoms,
            ownedAtoms: Math.floor(atoms * 0.10),
            nToggles: TOGGLES,
            pauseRasterizer: paused,
        });
        return summarizeRebuild(atoms, paused, loadMs, toggles);
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
        const summaries: ScenarioSummary[] = [];
        for (const atoms of SIZES) {
            for (const paused of [true, false]) {
                for (const fraction of FRACTIONS) {
                    const mask = await runMaskScenario(browser, atoms, fraction, paused);
                    summaries.push(mask);
                    console.log(JSON.stringify(mask));
                }
                const control = await runControlScenario(browser, atoms, 0.10, paused);
                console.log(JSON.stringify(control));
            }
        }
        for (const paused of [true, false]) {
            const rebuild = await runRebuildReferenceScenario(browser, 95_000, paused);
            console.log(JSON.stringify(rebuild));
        }
        const live95 = summaries.find((item) => item.atoms === 95_000 && item.fraction === 0.10 && item.rasterizer === "live");
        const paused95 = summaries.find((item) => item.atoms === 95_000 && item.fraction === 0.10 && item.rasterizer === "paused");
        if (!live95 || !paused95) throw new Error("Missing 95k ownership mask benchmark result.");
        console.log(JSON.stringify({
            type: "exclusive-ownership-recommendation",
            decisionMetric: "median per-toggle totalMs for mask-based ownership at n=95,000, 10% owned atoms, live rasterizer",
            live95TotalMs: live95.medians.totalMs,
            paused95TotalMs: paused95.medians.totalMs,
            componentProbe: live95.componentProbe,
            invariantProbe: live95.invariantProbe,
            geometryMemory: "unchanged: masking transparency does not remove whole geometry, it only prevents owned atoms from drawing opaquely in the whole component",
            recommendation: recommendation(live95.medians.totalMs),
        }));
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
