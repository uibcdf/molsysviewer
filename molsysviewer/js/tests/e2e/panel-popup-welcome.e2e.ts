/**
 * The popped-out Studio/Add-ons window must show its panels, not the welcome card.
 *
 * Reported by hand on 2026-07-31: the panel popup opened with the Studio and
 * Add-ons buttons in its header and nothing underneath them — only the welcome
 * card, which does not belong there at all.
 *
 * The cause is a premise that holds for a viewer and not for this window.
 * `updateWelcomeState` reads "no structure" as "empty viewer, invite the user to
 * load something". A panel-only endpoint has its canvas hidden and never loads a
 * structure — the panel snapshot carries UI state and deliberately no geometry
 * (`popup_snapshot.py::_build_panel_snapshot`), so having none is its normal
 * condition. The card is absolutely positioned over the host element, so it
 * covers the panels; its "Load Crambin" button would load into a canvas the user
 * cannot see.
 */
import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

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
        `<!doctype html><html><body>`
        + `<div id="panel" style="width: 420px; height: 600px;"></div>`
        + `<div id="viewer" style="width: 800px; height: 600px;"></div>`
        + `</body></html>`,
    );
    await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    console.log("[E2E panel-popup-welcome] Scenario: panel-only endpoint shows no welcome card");

    const result = await page.evaluate(async () => {
        const panel = await (window as any).Harness.createController("panel", {
            isPanelOnly: true,
            panelModeStyle: "split",
        });
        await new Promise(r => setTimeout(r, 400));
        const panelCards = document
            .getElementById("panel")!
            .querySelectorAll('[data-molsysviewer-welcome-card="true"]').length;

        // A real viewer with nothing loaded still gets the card: the fix must not
        // remove the affordance where it belongs.
        const viewer = await (window as any).Harness.createController("viewer");
        await new Promise(r => setTimeout(r, 400));
        const viewerCards = document
            .getElementById("viewer")!
            .querySelectorAll('[data-molsysviewer-welcome-card="true"]').length;

        return { panelCards, viewerCards, panelReady: !!panel, viewerReady: !!viewer };
    });

    assert.strictEqual(
        result.panelCards,
        0,
        "the panel-only popup must not show the welcome card: it covers the panels "
        + "that are the whole reason the window exists",
    );
    assert.strictEqual(
        result.viewerCards,
        1,
        "an empty viewer must still show the welcome card",
    );
    assert.deepStrictEqual(errors, [], `page errors: ${errors.join(" | ")}`);

    console.log("[E2E panel-popup-welcome] PASS");
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
