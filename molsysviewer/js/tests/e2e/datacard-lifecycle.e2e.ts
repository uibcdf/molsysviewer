import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { BrowserContext, Frame, Page } from "playwright";
import { chromium } from "./e2e-browser";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

const directory = dirname(fileURLToPath(import.meta.url));
const cardSelector = '[data-molsysviewer-datacard="literal-card"]';
const errors: string[] = [];

async function mount(target: Page | Frame, fixture: any) {
    await target.addScriptTag({ path: resolve(directory, "harness.bundle.js") });
    await target.evaluate(async fixture => {
        const controller = await (window as any).Harness.createController("root");
        await controller.handleMessage(fixture.load);
        await controller.handleMessage({ op: "set_trajectory_plot", options: fixture.plots.initial });
    }, fixture);
    await target.locator(cardSelector).waitFor({ state: "visible" });
}

async function show(page: Page, record: any) {
    await page.evaluate(async options => (window as any).__controller.handleMessage({ op: "set_trajectory_plot", options }), record);
}

async function withinHost(page: Page) {
    await page.waitForFunction(() => {
        const host = document.getElementById("root")!.getBoundingClientRect();
        const card = document.querySelector('[data-molsysviewer-datacard="literal-card"]')!.getBoundingClientRect();
        return card.width > 0 && card.height > 0 && card.left >= host.left && card.top >= host.top
            && card.right <= host.right + 0.1 && card.bottom <= host.bottom + 0.1;
    });
}

async function checkCards(context: BrowserContext, fixture: any) {
    const page = await context.newPage();
    page.on("pageerror", error => errors.push(String(error)));
    let popup: Page | undefined;
    try {
        await page.setContent('<div id="root" style="width:1000px;height:720px"></div>');
        await mount(page, fixture);
        const card = page.locator(cardSelector);
        await page.evaluate(() => {
            const w = window as any, add = window.addEventListener, remove = window.removeEventListener;
            const timers = new Map<number, { delay: number; stack: string }>(), set = window.setInterval, clear = window.clearInterval;
            const listeners = new Map(["mousemove", "mouseup", "blur"].map(type => [type, new Set<any>()]));
            const observers = new Map<ResizeObserver, Set<Element>>(), nativeObserver = ResizeObserver;
            w.__cardResources = { listeners, timers, observers, unrelatedMoves: 0 };
            window.addEventListener = function (type: any, listener: any, ...rest: any[]) {
                listeners.get(type)?.add(listener); return (add as any).call(this, type, listener, ...rest);
            } as any;
            window.removeEventListener = function (type: any, listener: any, ...rest: any[]) {
                listeners.get(type)?.delete(listener); return (remove as any).call(this, type, listener, ...rest);
            } as any;
            window.setInterval = ((...args: any[]) => {
                const id = (set as any)(...args); timers.set(id, { delay: args[1], stack: new Error().stack || "" }); return id;
            }) as any;
            window.clearInterval = ((id: number) => { timers.delete(id); clear(id); }) as any;
            w.ResizeObserver = class extends nativeObserver {
                constructor(callback: ResizeObserverCallback) { super(callback); observers.set(this, new Set()); }
                observe(target: Element, options?: ResizeObserverOptions) { observers.get(this)!.add(target); super.observe(target, options); }
                disconnect() { observers.delete(this); super.disconnect(); }
            };
            w.__unrelatedMove = () => w.__cardResources.unrelatedMoves++;
            window.addEventListener("mousemove", w.__unrelatedMove);
        });
        const reportResources = () => page.evaluate(() => {
            const r = (window as any).__cardResources;
            return JSON.stringify({ timers: [...r.timers.values()], observers: [...r.observers.values()]
                .map((targets: any) => [...targets].map((target: any) => ({ tag: target.tagName, connected: target.isConnected, attributes: target.getAttributeNames() }))) });
        });
        const ownedResources = () => page.evaluate(() => {
            const r = (window as any).__cardResources;
            return { timers: [...r.timers.values()].filter((timer: any) => timer.stack.includes("FloatingDataCard")).length,
                observers: [...r.observers.values()].filter((targets: any) => [...targets]
                    .some((target: any) => target.hasAttribute("data-molsysviewer-datacard"))).length };
        });
        for (const gesture of ["drag", "resize"] as const) {
            // Install a fresh real card after the resource observation starts.
            await show(page, { cards: [] }); await show(page, fixture.plots.initial);
            assert.equal((await ownedResources()).observers, 1, await reportResources());
            const locator = card.locator(gesture === "drag" ? "[data-molsysviewer-datacard-header]" : "[data-molsysviewer-datacard-resize]");
            const bounds = (await locator.boundingBox())!;
            await page.mouse.move(bounds.x + 8, bounds.y + 8); await page.mouse.down();
            assert.deepEqual(await page.evaluate(() => [...(window as any).__cardResources.listeners.values()].map((s: any) => s.size)), [2, 1, 1]);
            await show(page, { cards: [] });
            assert.deepEqual(await page.evaluate(() => [...(window as any).__cardResources.listeners.values()].map((s: any) => s.size)), [1, 0, 0]);
            assert.equal((await ownedResources()).observers, 0, await reportResources());
            const before = await page.evaluate(() => (window as any).__cardResources.unrelatedMoves);
            await page.mouse.move(bounds.x + 30, bounds.y + 25); await page.mouse.up();
            assert.ok(await page.evaluate(() => (window as any).__cardResources.unrelatedMoves) > before);
        }
        await show(page, fixture.plots.initial);
        const size = (await card.boundingBox())!;
        const resize = card.getByLabel("Resize card with arrow keys");
        await resize.focus(); await resize.press("ArrowRight"); await resize.press("ArrowDown");
        await page.waitForFunction(({ width, height }) => {
            const card = document.querySelector('[data-molsysviewer-datacard="literal-card"]')!.getBoundingClientRect();
            return card.width === width + 20 && card.height === height + 20;
        }, size);
        for (const [width, height] of [[260, 180], [180, 120], [1000, 720]]) {
            await page.evaluate(({ width, height }) => Object.assign(document.getElementById("root")!.style,
                { width: `${width}px`, height: `${height}px` }), { width, height });
            await withinHost(page);
            const slider = card.getByRole("slider");
            await slider.focus(); await slider.press("End");
            await page.waitForFunction(() => (window as any).__controller.trajectory.getTrajectoryState().currentFrame === 2);
            assert.equal(await slider.inputValue(), "2");
            await slider.press("Home");
            await page.waitForFunction(() => (window as any).__controller.trajectory.getTrajectoryState().currentFrame === 0);
        }
        await page.locator("#root").evaluate(host => host.requestFullscreen());
        await page.waitForFunction(() => !!document.fullscreenElement); await withinHost(page);
        await page.evaluate(() => document.exitFullscreen());
        await page.waitForFunction(() => !document.fullscreenElement); await withinHost(page);
        // Rename before the first popup, then update while detached.
        await show(page, fixture.plots.updated);
        const open = async () => {
            const opened = page.waitForEvent("popup");
            await card.getByTitle("Popout card to external window", { exact: true }).click();
            popup = await opened; popup.on("pageerror", error => errors.push(String(error)));
            await popup.locator("#card-pop-body svg:has(polyline)").waitFor();
            assert.deepEqual(await ownedResources(), { timers: 1, observers: 1 }, await reportResources());
            return popup;
        };
        await open();
        assert.equal(await popup!.title(), fixture.expected.titles.updated);
        await show(page, fixture.plots.restored);
        await card.waitFor({ state: "hidden" });
        assert.equal(await popup!.title(), fixture.expected.titles.restored);
        assert.equal(await popup!.locator("#card-pop-header").evaluate(node => node.childElementCount), 0);
        await popup!.setViewportSize({ width: 720, height: 420 });
        await popup!.waitForFunction(() => {
            const svg = document.querySelector("#card-pop-body svg:has(polyline)") as SVGSVGElement;
            return svg.viewBox.baseVal.width > 650 && svg.viewBox.baseVal.height > 300;
        });
        await popup!.close(); popup = undefined;
        // A new canonical projection may arrive before the close fallback.
        // It must retire the old window before another can own its poll.
        await show(page, fixture.plots.restored);
        await card.waitFor({ state: "visible" }); await withinHost(page);
        assert.equal((await ownedResources()).timers, 0, await reportResources());
        await card.getByTitle("Minimize", { exact: true }).click();
        await show(page, fixture.plots.restored);
        assert.equal(await card.locator("[data-molsysviewer-datacard-body]").evaluate(node => getComputedStyle(node).display), "none");
        await open(); // A minimized card must still open its actual graph.
        const hidden = popup!.waitForEvent("close");
        await show(page, { ...fixture.plots.restored, visible: false }); await hidden; popup = undefined;
        await card.waitFor({ state: "hidden" });
        assert.equal((await ownedResources()).timers, 0, await reportResources());
        await show(page, fixture.plots.restored); await open();
        const closed = popup!.waitForEvent("close");
        await show(page, { cards: [] }); await closed; popup = undefined;
        await card.waitFor({ state: "detached" });
        assert.deepEqual(await ownedResources(), { timers: 0, observers: 0 }, await reportResources());
        assert.equal(await page.evaluate(() => (window as any).__controller.getStructureData().elementCount), fixture.expected.atoms);
        await show(page, fixture.plots.restored); await open();
        const disposed = popup!.waitForEvent("close");
        await page.evaluate(() => (window as any).__controller.dispose()); await disposed; popup = undefined;
        assert.deepEqual(await ownedResources(), { timers: 0, observers: 0 }, await reportResources());
        console.log("[E2E DataCard] active gestures, unrelated input, host/fullscreen bounds, keyboard, popup resize/title/hide/clear/disposal received");
    } finally {
        if (popup && !popup.isClosed()) await popup.close();
        await page.evaluate(() => (window as any).__controller?.dispose()); await page.close();
    }
}

async function checkWindowPolicies(context: BrowserContext, fixture: any) {
    for (const policy of ["sandbox", "trusted-types"] as const) {
        const page = await context.newPage();
        page.on("pageerror", error => errors.push(String(error)));
        try {
            let target: Page | Frame = page;
            if (policy === "sandbox") {
                await page.setContent('<iframe sandbox="allow-scripts allow-same-origin" style="width:1000px;height:720px" srcdoc="<div id=root style=width:1000px;height:720px></div>"></iframe>');
                target = page.frames()[1];
            } else await page.setContent('<div id="root" style="width:1000px;height:720px"></div>');
            await mount(target, fixture);
            await target.evaluate(() => {
                const w = window as any, open = window.open;
                w.__nativeCardPopup = { last: null, calls: 0 };
                window.open = function (...args: any[]) {
                    const result = (open as any).apply(this, args);
                    w.__nativeCardPopup.last = result; w.__nativeCardPopup.calls++;
                    return result;
                } as any;
            });
            if (policy === "trusted-types") await target.locator(cardSelector).getByTitle("Minimize", { exact: true }).click();
            if (policy === "trusted-types") await page.evaluate(() => {
                const meta = document.createElement("meta"); meta.httpEquiv = "Content-Security-Policy";
                meta.content = "require-trusted-types-for 'script'"; document.head.appendChild(meta);
            });
            const count = context.pages().length, card = target.locator(cardSelector);
            const status = card.locator("[data-molsysviewer-datacard-status]");
            for (let retry = 0; retry < 2; retry++) {
                if (retry) {
                    await target.evaluate(() => Object.assign(document.getElementById("root")!.style,
                        { width: "180px", height: "120px" }));
                    await target.waitForFunction(() => document.querySelector('[data-molsysviewer-datacard]')!.getBoundingClientRect().width <= 172);
                    await status.getByRole("button", { name: "Try again", exact: true }).click();
                }
                else await card.getByTitle("Popout card to external window", { exact: true }).click();
                await status.waitFor({ state: "visible" });
                assert.equal(await status.getAttribute("data-molsysviewer-datacard-error"), policy === "sandbox" ? "popup_blocked" : "popup_bootstrap_failed");
                await target.waitForFunction(policy => {
                    const w = window as any;
                    return w.__controller.trajectoryPlotOverlay.entries.get("literal-card").card.popoutWindow === null
                        && (policy === "sandbox" ? w.__nativeCardPopup.last === null : w.__nativeCardPopup.last?.closed === true);
                }, policy);
                if (policy === "sandbox") assert.equal(context.pages().length, count);
                assert.equal(await card.locator("svg:has(polyline)").count(), 1);
            }
            await status.getByRole("button", { name: "Dismiss", exact: true }).click();
            await status.waitFor({ state: "hidden" });
            const slider = card.getByRole("slider"); await slider.focus(); await slider.press("End");
            await target.waitForFunction(() => (window as any).__controller.trajectory.getTrajectoryState().currentFrame === 2);
            assert.equal(await slider.inputValue(), "2");
            assert.equal(await target.evaluate(() => (window as any).__controller.getStructureData().elementCount), fixture.expected.atoms);
            console.log(`[E2E DataCard] real ${policy} blocked/bootstrap policy, retry/dismiss and preserved source received`);
        } finally { await targetDispose(page); await page.close(); }
    }
}

async function targetDispose(page: Page) {
    const results = await Promise.allSettled(page.frames().map(frame => frame.evaluate(() => (window as any).__controller?.dispose())));
    for (const result of results) if (result.status === "rejected") errors.push(`Card cleanup: ${String(result.reason)}`);
}

async function run() {
    const browser = await chromium.launch();
    try {
        const initial = await browser.newPage(); const context = initial.context(); await initial.close();
        await withFixtureWorkspace("datacard-lifecycle", async workspace => {
            const path = resolve(workspace, "fixture.json");
            execFileSync(process.env.PYTHON || "python", [resolve(directory, "datacard-title-fixture.py"), path],
                { cwd: resolve(directory, "../../../.."), env: fixtureEnvironment(workspace) });
            const fixture = JSON.parse(await readFile(path, "utf8"));
            await checkCards(context, fixture); await checkWindowPolicies(context, fixture);
        });
        assert.deepEqual(errors, []);
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
