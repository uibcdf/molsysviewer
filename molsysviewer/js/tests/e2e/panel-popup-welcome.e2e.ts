/**
 * The popped-out Studio/Add-ons window must show its panels, not the welcome card.
 *
 * Reported by hand on 2026-07-31: the panel popup opened with the Studio and
 * Add-ons buttons in its header and nothing underneath them — only the welcome
 * card, which does not belong there at all.
 *
 * The same premise, one level in, was hiding the panels themselves: both are
 * revealed by `captureCurrentStructure`, which a panel-only endpoint never reaches,
 * so the window showed its two header buttons over nothing. That is asserted here
 * too, because the two defects are one mistake made twice.
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

        return {
            panelCards, viewerCards, panelReady: !!panel, viewerReady: !!viewer,
            panelStudioVisible: (panel as any).groupPanel?.isVisible?.() ?? null,
            panelAddonsVisible: (panel as any).addonsPanel?.isVisible?.() ?? null,
            // The pop-out window should open at the size of the panel it came out
            // of. The viewer host here is 800x600, so the floating panel's own rule
            // gives 800 * 0.75 = 600 wide.
            popupSize: (viewer as any).getPanelPopupSize?.() ?? null,
            floatingWidthRule: Math.min(800 * 0.75, 950),
            screenWidth: window.screen?.availWidth ?? null,
        };
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
    assert.strictEqual(
        result.panelStudioVisible, true,
        "the Studio panel must be visible in a panel-only window: it is revealed by "
        + "captureCurrentStructure, which never runs there, so it waited for a "
        + "structure that is not coming and showed nothing",
    );
    assert.strictEqual(
        result.panelAddonsVisible, true,
        "the Add-ons panel must be visible in a panel-only window, for the same reason",
    );
    assert.ok(
        result.popupSize && result.popupSize.width >= result.floatingWidthRule,
        `the panel popup opens ${result.popupSize?.width}px wide where the floating `
        + `panel it came from is ${result.floatingWidthRule}px: the same content `
        + "arrives in a shape it was not laid out for",
    );
    assert.ok(
        result.popupSize.width <= (result.screenWidth ?? Infinity),
        "the popup must still fit on the screen",
    );
    assert.deepStrictEqual(errors, [], `page errors: ${errors.join(" | ")}`);

    console.log("[E2E panel-popup-welcome] PASS");
    await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
