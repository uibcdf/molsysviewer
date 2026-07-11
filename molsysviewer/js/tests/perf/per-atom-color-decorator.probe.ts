import assert from "node:assert";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ATOMS = 40;
const ATOMS_PER_RESIDUE = 10;

function makePdb(atoms: number): string {
    const lines: string[] = [];
    const atomNames = ["N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "H"];
    for (let atom = 0; atom < atoms; atom++) {
        const serial = atom + 1;
        const residue = Math.floor(atom / ATOMS_PER_RESIDUE) + 1;
        const name = atomNames[atom % atomNames.length];
        const x = ((atom % ATOMS_PER_RESIDUE) * 1.5).toFixed(3).padStart(8);
        const y = (Math.floor(atom / ATOMS_PER_RESIDUE) * 4.0).toFixed(3).padStart(8);
        const z = "0.000".padStart(8);
        const element = name === "H" ? "H" : name[0];
        lines.push(`ATOM  ${String(serial).padStart(5)} ${name.padStart(4)} ALA A${String(residue).padStart(4)}    ${x}${y}${z}  1.00 20.00          ${element.padStart(2)}`);
    }
    lines.push("END");
    return lines.join("\n");
}

async function run(): Promise<void> {
    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    });
    try {
        const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
        await page.setContent('<div id="root" style="width:900px;height:700px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));
        const pdb = makePdb(ATOMS);
        const result = await page.evaluate(async ({ pdbText }) => {
            const browserWindow = window as unknown as {
                Harness: {
                    createController(target: string): Promise<any>;
                    probePerAtomColorDecorator(
                        controller: any,
                        options: { coloredAtom: number; uncoloredAtom: number; color: number },
                    ): Promise<any>;
                };
            };
            const controller = await browserWindow.Harness.createController("root");
            await controller.handleMessage({
                op: "load_structure_from_string",
                data: pdbText,
                format: "pdb",
                label: "per-atom-color-decorator-probe",
            });
            return browserWindow.Harness.probePerAtomColorDecorator(controller, {
                coloredAtom: 0,
                uncoloredAtom: 1,
                color: 0xff0000,
            });
        }, { pdbText: pdb });

        assert.strictEqual(result.themeName, "msv-per-atom");
        assert.strictEqual(result.baseThemeName, "element-symbol");
        assert.strictEqual(result.coloredAtomUsesLayer, true);
        assert.strictEqual(result.uncoloredAtomFallsThrough, true);

        console.log(JSON.stringify({
            type: "per-atom-color-decorator-probe",
            atoms: ATOMS,
            result,
        }));
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
