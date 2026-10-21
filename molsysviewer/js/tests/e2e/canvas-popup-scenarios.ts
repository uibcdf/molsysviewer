import assert from "node:assert/strict";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { mountCanvasPopupFixture } from "./canvas-popup-fixture";

async function checkProportionalStudio(canvas: Page) {
    await canvas.waitForFunction(() => {
        const button = document.querySelector<HTMLButtonElement>('button[title="Popout panel to external window"]');
        const panel = button?.parentElement?.parentElement;
        const host = panel?.parentElement?.parentElement;
        if (!panel || !host) return false;
        const rect = panel.getBoundingClientRect();
        const margin = document.fullscreenElement?.contains(host) ? 72 : 48;
        return Math.abs(rect.width - Math.min(host.clientWidth * 0.86, 1200, host.clientWidth - 20)) < 1
            && Math.abs(rect.height - Math.min(host.clientHeight * 0.88, 940, host.clientHeight - 2 * Math.min(margin, host.clientHeight * 0.2))) < 1
            && getComputedStyle(panel).opacity === "0.97";
    });
}

async function checkStudioFullscreen(panel: Page, otherWindows: Page[]) {
    const button = panel.locator('[data-molsysviewer-panel-fullscreen="true"]');
    await button.waitFor({ state: "visible" });
    assert.equal(await button.getAttribute("title"), "Fullscreen");
    await button.focus();
    await panel.keyboard.press("Enter");
    await panel.waitForFunction(() => !!document.fullscreenElement
        && document.querySelector('[data-molsysviewer-panel-fullscreen="true"]')?.getAttribute("title") === "Exit Fullscreen");
    assert.equal(await button.getAttribute("title"), "Exit Fullscreen");
    assert.equal(await button.getAttribute("aria-pressed"), "true");
    for (const other of otherWindows) {
        assert.equal(await other.evaluate(() => !!document.fullscreenElement), false,
            "Studio fullscreen is local to its window");
    }
    await button.focus();
    await panel.keyboard.press("Space");
    await panel.waitForFunction(() => !document.fullscreenElement);
    await button.click();
    await panel.waitForFunction(() => !!document.fullscreenElement);
    // A browser-originated exit emits the same fullscreenchange notification.
    await panel.evaluate(() => document.exitFullscreen());
    await panel.waitForFunction(() =>
        document.querySelector('[data-molsysviewer-panel-fullscreen="true"]')?.getAttribute("title") === "Fullscreen");
    assert.equal(await button.getAttribute("aria-pressed"), "false");
}

/** Actual Python widget bootstrap, runtime-source handshake and popup snapshot. */
export async function checkNotebookCanvasPopup(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "canvas-popup-bridge.py"), resolve(dir, "../../../.."));
    const errors: string[] = [];
    let releaseFixture: (() => Promise<void>) | undefined;
    page.on("pageerror", error => errors.push(String(error)));
    try {
        releaseFixture = await mountCanvasPopupFixture(page, bridge);
        const signature = (canvas: Page) => canvas.locator(".molsysviewer-controls").evaluate(element => {
            const style = getComputedStyle(element);
            return {
                buttons: [...element.querySelectorAll("button")].map(button => ({
                    title: button.title.replace(/Open popup|Close popup/, "Popup"),
                    text: /Open popup|Close popup/.test(button.title) ? "Popup" : button.textContent,
                    icon: /Open popup|Close popup/.test(button.title) ? "Popup" : button.innerHTML,
                    width: /Open popup|Close popup/.test(button.title) ? "auto" : getComputedStyle(button).width,
                    height: getComputedStyle(button).height,
                    border: getComputedStyle(button).border, background: getComputedStyle(button).backgroundColor,
                })),
                trajectory: element.querySelector('[data-molsysviewer-trajectory-controls="true"]')?.innerHTML,
                position: { top: style.top, left: style.left, right: style.right },
            };
        });
        const pending = page.waitForEvent("popup");
        await page.getByTitle("Open popup", { exact: true }).click();
        const popup = await pending;
        popup.on("pageerror", error => errors.push(String(error)));
        await popup.evaluate(() => {
            const observer = new MutationObserver(() => {
                const controls = document.querySelector(".molsysviewer-controls");
                if (!controls?.querySelector("button")) return;
                (window as any).__firstPopupButtons = controls.textContent;
                observer.disconnect();
            });
            observer.observe(document, { childList: true, subtree: true });
        });
        await popup.waitForFunction(() => document.querySelector('[data-molsysviewer-trajectory-label="true"]')?.textContent === "1 / 3");
        await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
        await page.mouse.move(700, 400);
        await popup.mouse.move(700, 400);
        // Position right:auto may resolve differently with the larger window.
        const host = await signature(page), external = await signature(popup);
        assert.ok((await popup.evaluate(() => (window as any).__firstPopupButtons))?.includes("Reset"),
            "the first controls mount must inherit Classic before asynchronous scene sync");
        assert.deepEqual(external.buttons, host.buttons, "popup buttons and computed styles match the notebook");
        assert.equal(external.trajectory, host.trajectory, "the trajectory widgets match exactly");
        assert.equal(external.position.left, host.position.left);
        assert.equal(external.position.top, host.position.top);
        await page.evaluate(() => (window as any).__popupWidgetModel.set("controls_mode", "minimal"));
        // Clicking the empty reveal rectangle must focus a control, not create
        // a text-caret selection in its empty DIV (TcTIM dogfooding #251).
        await page.evaluate(() => (window as any).__popupWidgetModel.set("autohide_controls", true));
        const reveal = popup.getByRole("button", { name: "Show canvas controls", exact: true });
        await reveal.waitFor({ state: "visible" });
        const revealPoint = await reveal.evaluate(element => {
            const rect = element.getBoundingClientRect();
            for (const y of [rect.y + 2, rect.bottom - 2]) for (const x of [rect.x + 2, rect.right - 2]) {
                if (document.elementFromPoint(x, y) === element) return { x, y };
            }
            throw new Error("No exposed reveal-control corner");
        });
        await popup.mouse.click(revealPoint.x, revealPoint.y);
        assert.ok(await reveal.evaluate(element => element === document.activeElement));
        assert.ok(await reveal.evaluate(element => !element.contains(getSelection()?.anchorNode ?? null)),
            "The reveal control must not acquire a text caret when clicked");
        await popup.keyboard.press("Enter");
        await popup.waitForFunction(() => document.querySelector(".molsysviewer-controls")?.contains(document.activeElement));
        await page.evaluate(() => (window as any).__popupWidgetModel.set("autohide_controls", false));
        await popup.getByTitle("Help (H)", { exact: true }).waitFor({ state: "visible" });
        await popup.getByTitle("Help (H)", { exact: true }).click();
        assert.ok(await popup.getByText("Keyboard", { exact: false }).first().isVisible());
        await popup.getByTitle("Close (H or Esc)", { exact: true }).focus();
        await popup.keyboard.press("Escape");
        await popup.locator(".molsysviewer-help-card").waitFor({ state: "hidden" });
        await popup.getByTitle("Panel mode (N / W)", { exact: true }).click();
        await checkProportionalStudio(popup);
        assert.ok(await popup.getByTitle("Lock background", { exact: true }).isVisible(),
            "the canvas popup inherits the unlocked initial Studio state");
        assert.ok(await popup.locator('[data-molsysviewer-group-panel-tab="regions"]').isVisible());
        await popup.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
        assert.ok(await popup.getByText("Saved Regions", { exact: true }).isVisible());
        await popup.locator('[data-molsysviewer-group-settings-btn="true"]').click();
        const autohide = popup.getByRole("switch", { name: "Autohide Controls", exact: true });
        await autohide.click();
        await page.waitForFunction(() => (window as any).__popupWidgetModel.get("autohide_controls") === true);
        await autohide.click();
        await page.waitForFunction(() => (window as any).__popupWidgetModel.get("autohide_controls") === false);
        const notebookPopoutButton = page.getByTitle("Popout panel to external window", { exact: true });
        const notebookStudioVisible = await notebookPopoutButton.isVisible();
        const panelPending = popup.waitForEvent("popup");
        await popup.getByTitle("Popout panel to external window", { exact: true }).click();
        const panelPopup = await panelPending;
        panelPopup.on("pageerror", error => errors.push(String(error)));
        await panelPopup.locator('[data-molsysviewer-group-panel-tab="regions"]').waitFor({ state: "visible" });
        assert.equal(await panelPopup.locator(".molsysviewer-controls").count(), 0);
        assert.equal(await panelPopup.locator('[data-molsysviewer-welcome-card="true"]').count(), 0);
        await checkStudioFullscreen(panelPopup, [page, popup]);
        const sourcePopoutButton = popup.getByTitle("Popout panel to external window", { exact: true });
        await sourcePopoutButton.waitFor({ state: "hidden" });
        assert.equal(await popup.locator('[data-molsysviewer-group-panel-tab="regions"]').isVisible(), false,
            "Studio leaves the canvas that initiated its popout (#250)");
        assert.equal(await popup.locator("canvas").isVisible(), true, "the molecular canvas remains available");
        assert.equal(await notebookPopoutButton.isVisible(), notebookStudioVisible,
            "detaching Studio from the external canvas preserves notebook layout");
        await panelPopup.close();
        await sourcePopoutButton.waitFor({ state: "visible" });
        assert.ok(await autohide.isVisible(),
            "closing external Studio restores the originating Settings editor");
        assert.equal(await notebookPopoutButton.isVisible(), notebookStudioVisible,
            "returning Studio does not open a second panel in the notebook");

        // Browser popup blocking is a transport condition, not scientific data.
        await popup.evaluate(() => {
            (window as any).__unblockedWindowOpen = window.open;
            window.open = () => null;
        });
        try {
            await sourcePopoutButton.click();
            assert.equal(await sourcePopoutButton.isVisible(), true,
                "a blocked popout keeps the source Studio accessible");
        } finally {
            await popup.evaluate(() => {
                window.open = (window as any).__unblockedWindowOpen;
                delete (window as any).__unblockedWindowOpen;
            });
        }
        // A second handoff exercises a docked source and the ordinary panel control.
        await popup.getByTitle("Dock panel (Split)", { exact: true }).click();
        const secondPanelPending = popup.waitForEvent("popup");
        await sourcePopoutButton.click();
        const secondPanel = await secondPanelPending;
        secondPanel.on("pageerror", error => errors.push(String(error)));
        await secondPanel.locator('[data-molsysviewer-group-panel-tab="regions"]').waitFor({ state: "visible" });
        await sourcePopoutButton.waitFor({ state: "hidden" });
        await popup.locator("#molsysviewer-pop").focus();
        const secondPanelClosed = secondPanel.waitForEvent("close");
        await popup.getByTitle("Panel mode (N / W)", { exact: true }).click();
        await secondPanelClosed;
        await sourcePopoutButton.waitFor({ state: "visible" });
        assert.ok(await popup.getByTitle("Float panel", { exact: true }).isVisible(),
            "returning Studio preserves the originating docked layout");
        await popup.getByTitle("Float panel", { exact: true }).click();
        await popup.locator("#molsysviewer-pop").focus();
        await popup.keyboard.press("v");
        await popup.waitForFunction(() => document.querySelector("canvas")?.parentElement?.style.display === "none");
        await popup.keyboard.press("v");
        await popup.waitForFunction(() => document.querySelector("canvas")?.parentElement?.style.display === "block");
        await popup.keyboard.press("Escape");
        await popup.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "visible");
        // Escape above closed Studio. Reopen it before measuring its drawn
        // fullscreen dimensions, with the background available to controls.
        await popup.getByTitle("Panel mode (N / W)", { exact: true }).click();
        if (await popup.getByTitle("Unlock background (Ambient)", { exact: true }).isVisible()) {
            await popup.getByTitle("Unlock background (Ambient)", { exact: true }).click();
        }
        await checkProportionalStudio(popup);
        await popup.getByTitle("Fullscreen", { exact: true }).click();
        await popup.waitForFunction(() => !!document.fullscreenElement);
        await checkProportionalStudio(popup);
        await popup.getByTitle("Exit Fullscreen", { exact: true }).click();
        await popup.waitForFunction(() => !document.fullscreenElement);
        await checkProportionalStudio(popup);
        const canvas = await popup.locator("canvas").boundingBox();
        assert.ok(canvas);
        await popup.mouse.click(canvas.x + 30, canvas.y + canvas.height - 30, { button: "right" });
        const menu = popup.locator('[data-molsysviewer-context-menu="true"]');
        await menu.waitFor({ state: "visible" });
        await menu.locator('[data-molsysviewer-context-submenu="View"]').click();
        await menu.getByText("Cinema", { exact: true }).click();
        await page.waitForFunction(() => (window as any).__popupWidgetModel.get("controls_mode") === "cinema");
        // Every mode is projected into the existing popup through notebook traits.
        for (const mode of ["classic", "minimal", "cinema", "minimal"]) {
            await page.evaluate(mode => (window as any).__popupWidgetModel.set("controls_mode", mode), mode);
            if (mode === "cinema") {
                await popup.waitForFunction(() => !document.querySelector(".molsysviewer-controls"));
                assert.equal(await popup.locator('[data-molsysviewer-trajectory-controls="true"]').count(), 1);
            } else {
                await popup.waitForFunction(mode => {
                    const control = document.querySelector(".molsysviewer-controls");
                    return mode === "classic" ? control?.textContent?.includes("Reset") : !!control?.querySelector('button[title="Help (H)"]');
                }, mode);
                await page.mouse.move(700, 400);
                await popup.mouse.move(700, 400);
                const expected = await signature(page), actual = await signature(popup);
                // Classic Pop/Close labels identify the window-specific operation.
                for (const entry of [expected, actual]) for (const button of entry.buttons) {
                    if (button.title === "Popup") { button.text = "Popup"; button.icon = "Popup"; }
                }
                assert.deepEqual(actual.buttons, expected.buttons);
            }
        }
        await popup.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-trajectory-label="true"]')?.textContent === "2 / 3");
        await popup.waitForFunction(() => document.querySelector('[data-molsysviewer-trajectory-label="true"]')?.textContent === "2 / 3");
        assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
        const closed = popup.waitForEvent("close");
        await popup.getByTitle("Close popup", { exact: true }).click({ noWaitAfter: true }).catch(error => {
            // Chrome can close the target before acknowledging its final click.
            if (!popup.isClosed() || !String(error).includes("has been closed")) throw error;
        });
        await closed;
        assert.ok(popup.isClosed());
        // The same Studio header also serves a popout from the notebook itself.
        await page.getByTitle("Panel mode (N / W)", { exact: true }).click();
        assert.ok(await page.getByTitle("Lock background", { exact: true }).isVisible());
        const notebookPanelPending = page.waitForEvent("popup");
        await notebookPopoutButton.click();
        const notebookPanel = await notebookPanelPending;
        notebookPanel.on("pageerror", error => errors.push(String(error)));
        await checkStudioFullscreen(notebookPanel, [page]);
        await notebookPanel.close();
        await notebookPopoutButton.waitFor({ state: "visible" });
        // Keep the original canvas shortcut working in notebook shadow hosts.
        await page.evaluate(() => {
            const target = document.querySelector("canvas")!.parentElement!.parentElement!;
            const host = document.createElement("div");
            Object.assign(host.style, { width: "850px", height: "600px" });
            document.body.appendChild(host);
            host.attachShadow({ mode: "open" }).appendChild(target);
            target.setAttribute("data-popup-shadow-canvas", "true");
        });
        const shadowCanvas = page.locator('[data-popup-shadow-canvas="true"]');
        await shadowCanvas.focus();
        await page.keyboard.press("v");
        assert.equal(await shadowCanvas.locator("canvas").evaluate(canvas => canvas.parentElement!.style.display), "none");
        await page.keyboard.press("v");
        assert.equal(await shadowCanvas.locator("canvas").evaluate(canvas => canvas.parentElement!.style.display), "block");
        await shadowCanvas.evaluate(target => {
            const input = document.createElement("input");
            input.setAttribute("data-popup-shadow-input", "true");
            target.appendChild(input);
            input.focus();
        });
        await page.keyboard.press("v");
        assert.equal(await shadowCanvas.locator("canvas").evaluate(canvas => canvas.parentElement!.style.display), "block",
            "typing in a shadow-root input must not trigger canvas shortcuts");
        assert.deepEqual(errors, []);
        console.log("[E2E popup parity] real notebook bootstrap/authority: legacy-source isolation, first-mount modes, controls/styles, Help, V/fullscreen, Studio/panel popup, preferences, context menu and trajectory match");
    } finally {
        await page.evaluate(async () => {
            (window as any).__popupWidgetDispose?.();
            await (window as any).__popupFixtureDrain?.();
        });
        await bridge.close();
        await releaseFixture?.();
        assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors || []), [],
            "the notebook transport must drain before its Python authority closes");
    }
}
