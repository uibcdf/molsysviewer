import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));

async function run() {
    // The actual Python export, embedded runtime, real trajectory and popup boot.
    const fixture = spawnSync(process.env.PYTHON || process.env.PYTHON_BIN || "python", ["-c", `
import json, tempfile
from pathlib import Path
import molsysviewer as msv
view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
view.set_controls_visible(True, autohide=True)
output = Path(tempfile.mkdtemp(prefix="msv-controls-review-")) / "controls.html"
view.export.html(str(output), include_popout=True)
print(json.dumps({"page": str(output)}))
view.close()
`], { cwd: resolve(dir, "../../../.."), encoding: "utf8" });
    assert.equal(fixture.status, 0, fixture.stderr || fixture.stdout);
    const artifact = JSON.parse(fixture.stdout);
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 1100, height: 720 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (["error", "warning"].includes(message.type())) console.error(`[host ${message.type()}] ${message.text()}`);
        });
        await page.goto(pathToFileURL(artifact.page).href);
        await page.waitForFunction(() => (window as any).__molsysviewerDocsController?.plugin.canvas3d?.reprCount.value > 0);
        await page.locator("#molsysviewer-root").evaluate(el => {
            el.style.width = "850px"; el.style.height = "560px";
        });
        await page.waitForFunction(() => document.querySelector("canvas")!.clientWidth <= 850);
        const controls = page.locator(".molsysviewer-controls");
        const host = await page.locator("canvas").boundingBox();
        assert.ok(host);
        const away = async () => { await page.mouse.move(host.x + host.width * 0.8, host.y + host.height / 2); };
        const reveal = async () => {
            const area = await page.getByRole("button", { name: "Show canvas controls", exact: true }).boundingBox();
            assert.ok(area);
            await page.mouse.move(area.x + area.width / 2, area.y + area.height / 2);
            await page.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "visible");
        };
        const hidden = () => page.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "hidden");
        await away();
        await hidden();
        await reveal();
        await away();
        await hidden();

        // A frame update must not override the visibility preference.
        await page.evaluate(async () => {
            const c = (window as any).__molsysviewerDocsController;
            await c.handleMessage({ op: "set_trajectory_frame", index: 1 });
        });
        await hidden();
        await reveal();
        await controls.locator('[title="Panel mode (N / W)"]').click();
        await page.locator('[data-molsysviewer-group-settings-btn="true"]').click();
        await page.getByLabel("Controls reveal area").selectOption("canvas");
        await page.getByTitle("Close (Esc)", { exact: true }).click();
        await away();
        await page.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "visible");
        await page.mouse.move(1098, 718);
        await hidden();

        // Explicit visibility overrides hover; disabling autohide is persistent.
        await page.evaluate(() => {
            const model = (window as any).__molsysviewerDocsController.model;
            model.set("show_controls", false);
        });
        await away();
        await hidden();
        await page.evaluate(() => {
            const model = (window as any).__molsysviewerDocsController.model;
            model.set("show_controls", true);
            model.set("autohide_controls", false);
        });
        await page.mouse.move(1098, 718);
        assert.equal(await controls.evaluate(el => (el as HTMLElement).style.visibility), "visible");
        await page.evaluate(() => {
            const model = (window as any).__molsysviewerDocsController.model;
            model.set("autohide_scope", "controls");
            model.set("autohide_controls", true);
        });

        // Dock/float and fullscreen retain the same explicit reveal scope.
        await reveal();
        await controls.locator('[title="Panel mode (N / W)"]').click();
        await page.getByTitle("Dock panel (Split)", { exact: true }).click();
        await away();
        await hidden();
        await reveal();
        await page.getByTitle("Float panel", { exact: true }).click();
        await page.getByTitle("Close (Esc)", { exact: true }).click();
        await away();
        await hidden();
        await reveal();
        await controls.getByTitle("Fullscreen", { exact: true }).click();
        await page.waitForFunction(() => !!document.fullscreenElement);
        await away();
        await hidden();
        await reveal();
        await controls.getByTitle("Exit Fullscreen", { exact: true }).click();
        await page.waitForFunction(() => !document.fullscreenElement);

        // A keyboard user can discover the hidden controls and reach a button.
        await away();
        await hidden();
        await page.keyboard.press("Tab");
        await page.getByRole("button", { name: "Show canvas controls", exact: true }).focus();
        await page.keyboard.press("Enter");
        assert.equal(await controls.evaluate(el => el.contains(document.activeElement)), true);
        await away();
        await hidden();

        const baseline = await page.evaluate(() => {
            const c = (window as any).__molsysviewerDocsController;
            return { trajectory: c.trajectory.trajectoryListeners.size, layout: c.layoutChangeListeners.length };
        });
        const selectMode = async (mode: string) => {
            await page.mouse.click(host.x + host.width - 20, host.y + host.height / 2, { button: "right" });
            const menu = page.locator('[data-molsysviewer-context-menu="true"]');
            await menu.locator('[data-molsysviewer-context-submenu="View"]').click();
            await menu.getByRole("menuitem", { name: new RegExp(`^${mode}(?: ✓)?$`) }).click();
        };
        for (let iteration = 0; iteration < 3; iteration++) {
            await selectMode("Cinema");
            assert.equal(await controls.count(), 0);
            assert.equal(await page.locator('[data-molsysviewer-trajectory-controls="true"]').count(), 1);
            await page.keyboard.press("h");
            assert.equal(await page.locator(".molsysviewer-help-card").count(), 1);
            assert.equal(await page.locator(".molsysviewer-help-card").isVisible(), true);
            await page.keyboard.press("h");
            await selectMode("Classic");
            assert.equal(await controls.count(), 1);
            await selectMode("Integrated");
            assert.equal(await controls.count(), 1);
        }
        assert.deepEqual(await page.evaluate(() => {
            const c = (window as any).__molsysviewerDocsController;
            return { trajectory: c.trajectory.trajectoryListeners.size, layout: c.layoutChangeListeners.length };
        }), baseline);
        assert.equal(await page.locator('[data-molsysviewer-controls-hotspot="true"]').count(), 1);

        // The production popup consumes the same preferences and renderer.
        await reveal();
        const popupReady = page.waitForEvent("popup");
        await page.evaluate(() => {
            (window as any).__controlsReviewMessages = [];
            window.addEventListener("message", event => {
                const envelope = event.data?.envelope;
                if (envelope) (window as any).__controlsReviewMessages.push(envelope.action);
            });
        });
        await controls.getByTitle("Open popup", { exact: true }).click();
        const popup = await popupReady;
        popup.on("pageerror", error => errors.push(String(error)));
        popup.on("console", message => {
            if (["error", "warning"].includes(message.type())) console.error(`[popup ${message.type()}] ${message.text()}`);
        });
        try {
            await popup.waitForFunction(() => document.querySelector('[data-molsysviewer-trajectory-controls="true"]')?.textContent?.includes("/ 3"));
        } catch (error) {
            console.error({ pageErrors: errors, popupText: await popup.locator("body").innerText(),
                received: await page.evaluate(() => (window as any).__controlsReviewMessages) });
            throw error;
        }
        await popup.mouse.move(500, 300);
        await popup.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "hidden");
        const popupReveal = await popup.getByRole("button", { name: "Show canvas controls", exact: true }).boundingBox();
        assert.ok(popupReveal);
        // Revealing deliberately puts the actual controls above the hotspot.
        await popup.mouse.move(popupReveal.x + popupReveal.width / 2, popupReveal.y + popupReveal.height / 2);
        await popup.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "visible");
        await selectMode("Cinema");
        await popup.waitForFunction(() => !document.querySelector(".molsysviewer-controls"));
        assert.equal(await popup.locator('[data-molsysviewer-trajectory-controls="true"]').count(), 1);
        await popup.close();
        assert.deepEqual(errors, []);
        console.log("[E2E controls] actual Python export/popup: Cinema cycles, control/canvas scope, Settings, Dock/fullscreen, keyboard, hidden-frame updates and stable subscriptions pass");
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
