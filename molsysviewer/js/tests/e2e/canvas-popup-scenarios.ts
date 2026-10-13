import assert from "node:assert/strict";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";

/** Actual Python widget bootstrap, runtime-source handshake and popup snapshot. */
export async function checkNotebookCanvasPopup(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "canvas-popup-bridge.py"), resolve(dir, "../../../.."));
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));
    try {
        const fixture = await bridge.request();
        await page.goto("about:blank");
        await page.setContent('<div id="notebook" style="width:850px;height:600px"></div>');
        await page.exposeFunction("__popupFixtureRequest", (message: unknown) => bridge.request([message]));
        await page.evaluate(async fixture => {
            const w = window as any;
            const traits = fixture.traits;
            // Legacy notebook state must not override the runtime actually loaded.
            traits.popup_js_source = 'throw new Error("obsolete popup runtime selected");';
            const listeners = new Map<string, Set<(...args: any[]) => void>>();
            let queue = Promise.resolve();
            const model = w.__popupWidgetModel = {
                get: (key: string) => traits[key],
                set(key: string, value: unknown) {
                    if (JSON.stringify(traits[key]) === JSON.stringify(value)) return;
                    traits[key] = value;
                    for (const callback of listeners.get(`change:${key}`) || []) callback();
                },
                on(event: string, callback: (...args: any[]) => void) {
                    if (!listeners.has(event)) listeners.set(event, new Set());
                    listeners.get(event)!.add(callback);
                },
                off(event: string, callback: (...args: any[]) => void) { listeners.get(event)?.delete(callback); },
                save_changes() {
                    model.send({ review_traits: Object.fromEntries([
                        "viewer_mode", "controls_mode", "panel_mode_style", "show_controls", "autohide_controls",
                        "autohide_scope", "controls_position", "controls_position_fullscreen",
                    ].map(trait => [trait, traits[trait]])) });
                },
                send(message: unknown) {
                    queue = queue.then(async () => {
                        const result = await w.__popupFixtureRequest(message);
                        // Simulate only the notebook transport, with real Python responses.
                        for (const { content, buffers } of result.messages) {
                            const views = buffers.map((encoded: string) => new DataView(
                                Uint8Array.from(atob(encoded), char => char.charCodeAt(0)).buffer));
                            for (const callback of listeners.get("msg:custom") || []) callback(content, views);
                        }
                    }).catch(error => { errors.push(String(error)); console.error(error); });
                },
            };
            const errors = w.__popupFixtureErrors = [];
            w.__popupFixtureDrain = async () => {
                // Responses may enqueue further stream acknowledgments.
                while (true) {
                    const pending = queue;
                    await pending;
                    if (pending === queue) return;
                }
            };
            const url = URL.createObjectURL(new Blob([traits._esm], { type: "text/javascript" }));
            try {
                const bootstrap = await import(url);
                w.__popupWidgetDispose = await bootstrap.default.render({ model, el: document.getElementById("notebook") });
            } finally { URL.revokeObjectURL(url); }
        }, fixture);
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-trajectory-label="true"]')?.textContent === "1 / 3");
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
        await popup.getByTitle("Help (H)", { exact: true }).waitFor({ state: "visible" });
        await popup.getByTitle("Help (H)", { exact: true }).click();
        assert.ok(await popup.getByText("Keyboard", { exact: false }).first().isVisible());
        await popup.getByTitle("Close (H or Esc)", { exact: true }).focus();
        await popup.keyboard.press("Escape");
        await popup.locator(".molsysviewer-help-card").waitFor({ state: "hidden" });
        await popup.getByTitle("Panel mode (N / W)", { exact: true }).click();
        assert.ok(await popup.locator('[data-molsysviewer-group-panel-tab="regions"]').isVisible());
        await popup.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
        assert.ok(await popup.getByText("Saved Regions", { exact: true }).isVisible());
        await popup.locator('[data-molsysviewer-group-settings-btn="true"]').click();
        const autohide = popup.getByRole("switch", { name: "Autohide Controls", exact: true });
        await autohide.click();
        await page.waitForFunction(() => (window as any).__popupWidgetModel.get("autohide_controls") === true);
        await autohide.click();
        await page.waitForFunction(() => (window as any).__popupWidgetModel.get("autohide_controls") === false);
        const panelPending = popup.waitForEvent("popup");
        await popup.getByTitle("Popout panel to external window", { exact: true }).click();
        const panelPopup = await panelPending;
        panelPopup.on("pageerror", error => errors.push(String(error)));
        await panelPopup.locator('[data-molsysviewer-group-panel-tab="regions"]').waitFor({ state: "visible" });
        assert.equal(await panelPopup.locator(".molsysviewer-controls").count(), 0);
        assert.equal(await panelPopup.locator('[data-molsysviewer-welcome-card="true"]').count(), 0);
        await panelPopup.close();
        await popup.locator("#molsysviewer-pop").focus();
        await popup.keyboard.press("v");
        await popup.waitForFunction(() => document.querySelector("canvas")?.parentElement?.style.display === "none");
        await popup.keyboard.press("v");
        await popup.waitForFunction(() => document.querySelector("canvas")?.parentElement?.style.display === "block");
        await popup.keyboard.press("Escape");
        await popup.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-controls")?.style.visibility === "visible");
        await popup.getByTitle("Fullscreen", { exact: true }).click();
        await popup.waitForFunction(() => !!document.fullscreenElement);
        await popup.getByTitle("Exit Fullscreen", { exact: true }).click();
        await popup.waitForFunction(() => !document.fullscreenElement);
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
        assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors || []), [],
            "the notebook transport must drain before its Python authority closes");
    }
}
