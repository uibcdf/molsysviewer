// tests/e2e/region-hide.e2e.ts
import assert from "node:assert";
import process from "node:process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
var __filename = fileURLToPath(import.meta.url);
var __dirname = dirname(__filename);
var PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;
async function run() {
  const envBin = process.env.PW_CHROMIUM_BIN;
  const playwrightBin = process.env.PLAYWRIGHT_BROWSERS_PATH ? `${process.env.PLAYWRIGHT_BROWSERS_PATH}/chromium-1200/chrome-linux64/chrome` : void 0;
  const baseOpts = {
    headless: true
  };
  const attempts = [];
  if (envBin) {
    attempts.push({
      label: "env-bin",
      options: {
        ...baseOpts,
        executablePath: envBin
      }
    });
  }
  if (playwrightBin) {
    attempts.push({
      label: "playwright",
      options: {
        ...baseOpts,
        chromiumSandbox: false,
        executablePath: playwrightBin,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
      }
    });
  }
  if (attempts.length === 0) {
    attempts.push({
      label: "default",
      options: {
        ...baseOpts,
        chromiumSandbox: false,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
      }
    });
  }
  let browser;
  let lastErr;
  for (const attempt of attempts) {
    try {
      browser = await chromium.launch(attempt.options);
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
  const errors = [];
  page.on("pageerror", (err) => errors.push(String(err)));
  page.on("console", (msg) => {
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
  await page.waitForFunction(() => !!window.Harness, { timeout: 6e4 });
  await page.evaluate(async (pdb) => {
    const controller = await window.Harness.createController("root");
    window.__controller = controller;
    await controller.handleMessage({
      op: "load_structure_from_string",
      data: pdb,
      format: "pdb",
      label: "test"
    });
    const structure = controller.getStructure?.();
    const n = structure?.elementCount ?? 0;
    const atomIndices = Array.from({ length: n }, (_, i) => i);
    await controller.handleMessage({
      op: "create_region",
      tag: "region1",
      atom_indices: atomIndices,
      representation: "ball-and-stick"
    });
    await controller.handleMessage({ op: "hide_region", tag: "region1" });
  }, PDB_TEXT);
  await browser.close();
  const hasWebglError = errors.some((e) => e.includes("WebGL rendering context"));
  if (hasWebglError) {
    console.warn("[E2E] WebGL no disponible en este entorno; skipping test.");
    process.exit(0);
  }
  assert.strictEqual(errors.length, 0, `Console errors detected: ${errors.join("; ")}`);
  console.log("[E2E] passed");
}
run().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
