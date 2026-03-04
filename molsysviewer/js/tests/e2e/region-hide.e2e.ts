import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN;
    const playwrightBin = process.env.PLAYWRIGHT_BROWSERS_PATH
        ? `${process.env.PLAYWRIGHT_BROWSERS_PATH}/chromium-1200/chrome-linux64/chrome`
        : undefined;
    const baseOpts = {
        headless: true,
    } satisfies Parameters<typeof chromium.launch>[0];

    const attempts: Array<{ label: string; options: Parameters<typeof chromium.launch>[0] }> = [];
    if (envBin) {
        attempts.push({
            label: "env-bin",
            options: {
                ...baseOpts,
                executablePath: envBin,
            },
        });
    }
    if (playwrightBin) {
        attempts.push({
            label: "playwright",
            options: {
                ...baseOpts,
                chromiumSandbox: false,
                executablePath: playwrightBin,
                args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            },
        });
    }
    if (attempts.length === 0) {
        attempts.push({
            label: "default",
            options: {
                ...baseOpts,
                chromiumSandbox: false,
                args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            },
        });
    }

    let browser;
    let lastErr: unknown;
    for (const attempt of attempts) {
        try {
            browser = await chromium.launch(attempt.options as any);
            break;
        } catch (err) {
            lastErr = err;
        }
    }
    if (!browser) {
        const msg = String(lastErr ?? "unknown");
        if (msg.includes("crashpad") || msg.includes("sandbox_host_linux") || msg.includes("Operation not permitted")) {
            console.warn("[E2E] Chromium launch blocked (crashpad/sandbox); skipping test.");
            process.exit(0);
        }
        throw lastErr instanceof Error ? lastErr : new Error(msg);
    }
    const page = await browser.newPage();

    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => {
        if (msg.type() === "error") errors.push(msg.text());
    });

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    const html = `
    <!doctype html>
    <html>
      <body>
        <div id="root" style="width: 600px; height: 400px;"></div>
      </body>
    </html>`;

    await page.setContent(html, { waitUntil: "networkidle" });
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => !!(window as any).Harness, { timeout: 60000 });

    await page.evaluate(async pdb => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test",
        });
        const structure = (controller as any).getStructure?.();
        const n = structure?.elementCount ?? 0;
        const atomIndices = Array.from({ length: n }, (_, i) => i);
        await controller.handleMessage({
            op: "create_region",
            tag: "region1",
            atom_indices: atomIndices,
            representation: "ball-and-stick",
        });
        await controller.handleMessage({ op: "hide_region", tag: "region1" });
    }, PDB_TEXT);

    await page.evaluate(async pdb => {
        const controller = (window as any).__controller;
        if (!controller) throw new Error("Controller not available for second scenario");

        // Add a tagged shape and clear it.
        await controller.handleMessage({
            op: "add_sphere",
            options: {
                center: [10, 10, 10],
                radius: 2.0,
                color: 0x00ff00,
                alpha: 0.35,
                tag: "shape-e2e",
            },
        });
        await controller.handleMessage({ op: "clear_shapes_by_tag", tag: "shape-e2e" });

        // Full scene reset and assert registry clear event propagated back.
        await controller.handleMessage({ op: "clear_all" });
        const lastMsg = (window as any).__lastMessage;
        if (!lastMsg || lastMsg.event !== "registry_cleared") {
            throw new Error("Expected registry_cleared event after clear_all");
        }

        // Reload to ensure controller remains usable after full reset.
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "reload-after-clear-all",
        });
    }, PDB_TEXT);

    await browser.close();

    const hasWebglError = errors.some(e => e.includes("WebGL rendering context"));
    if (hasWebglError) {
        console.warn("[E2E] WebGL is not available in this environment; skipping test.");
        process.exit(0);
    }
    assert.strictEqual(errors.length, 0, `Console errors detected: ${errors.join("; ")}`);
    console.log("[E2E] passed");
}

run().catch(err => {
    console.error(err);
    process.exitCode = 1;
});
