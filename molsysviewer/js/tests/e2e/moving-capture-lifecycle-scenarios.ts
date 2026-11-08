import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Page } from "playwright";
import type { PythonFixtureBridge } from "./python-fixture-bridge";
import { armMovingDependencyHold, movingEndpointIdentity, openMovingWorkFile } from "./moving-work-file-ui";

type Context = { page: Page; dir: string; workspace: string; oracle: any; bridge: PythonFixtureBridge;
    command: (name: string, details?: Record<string, unknown>) => Promise<any>; inspect: () => Promise<any> };

async function until(read: () => Promise<any>, predicate: (value: any) => boolean, name: string, milliseconds = 5000) {
    const started = Date.now(); let last: any;
    while (Date.now() - started < milliseconds) {
        last = await read();
        if (predicate(last)) return last;
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error(`${name} did not complete: ${JSON.stringify(last)}`);
}

async function openCanvas(page: Page, errors: string[]) {
    await page.bringToFront();
    const rect = await page.locator("canvas").first().boundingBox(); assert.ok(rect);
    await page.mouse.move(rect.x + 12, rect.y + 12);
    const opened = page.waitForEvent("popup");
    await page.getByTitle("Open popup", { exact: true }).click();
    const popup = await opened;
    popup.on("pageerror", error => errors.push(String(error)));
    await popup.waitForFunction(() => !!(window as any).__mirrorController);
    await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
    return popup;
}

async function sourceJob(context: Context, path: string, milliseconds = 15000) {
    return until(context.inspect, result => result.jobs[path]?.done === true, "source save", milliseconds);
}

/** Actual missing/closed renderers must preserve destinations and release ownership. */
export async function checkCaptureLifetimes(context: Context) {
    const { page, workspace, command, inspect, bridge } = context;
    const cases: any[] = [], errors: string[] = [];
    let popup: Page | undefined, panel: Page | undefined;
    try {
        for (const mode of ["visibility", "display", "detached"] as const) {
            await page.evaluate(mode => {
                const w = window as any, canvas = w.__mirrorController.plugin.canvas3dContext.canvas;
                const parent = canvas.parentNode, next = canvas.nextSibling, style = canvas.style.cssText;
                w.__restoreAvailabilityCanvas = () => {
                    if (!canvas.isConnected) parent.insertBefore(canvas, next?.parentNode === parent ? next : null);
                    canvas.style.cssText = style;
                    w.__mirrorController.plugin.canvas3d.requestDraw(true);
                };
                if (mode === "detached") parent.removeChild(canvas);
                else if (mode === "display") canvas.style.display = "none";
                else canvas.style.visibility = "hidden";
            }, mode);
            for (const kind of ["state", "session"]) {
                const path = resolve(workspace, `${mode}.${kind === "state" ? "json" : "msv"}`);
                const sentinel = Buffer.from(`original destination ${mode} ${kind}`);
                await writeFile(path, sentinel);
                const mark = await page.evaluate(() => (window as any).__movingCapture.outbound.length);
                await command("save", { path, kind, timeout: 5 });
                const result = await sourceJob(context, path, 8000);
                assert.equal(result.jobs[path].ok, false);
                assert.equal(result.jobs[path].reason, "renderer_refused");
                assert.equal(result.pending_captures, 0); assert.equal(result.pending_studio_saves, 0);
                const replies = await page.evaluate(mark => (window as any).__movingCapture.outbound.slice(mark), mark);
                assert.equal(replies.length, 1); assert.equal(replies[0].ok, false);
                assert.equal(replies[0].error_type, "NoLiveCanvas");
                assert.deepEqual(await readFile(path), sentinel, "a refused renderer must preserve the existing destination");
                cases.push({ mode, kind, reason: result.jobs[path].reason, unchanged_destination: true });
            }
            await page.evaluate(() => (window as any).__restoreAvailabilityCanvas());
            const path = resolve(workspace, `recovered-${mode}.json`);
            await command("save", { path, kind: "state" });
            assert.equal((await sourceJob(context, path)).jobs[path].ok, true, "the same canvas must recover");
        }
        for (const close of ["canvas", "panel"] as const) {
            popup = await openCanvas(page, errors);
            let owner = popup;
            if (close === "panel") {
                await openMovingWorkFile(popup);
                const opened = popup.waitForEvent("popup");
                await popup.getByTitle("Popout panel to external window", { exact: true }).click();
                panel = await opened;
                panel.on("pageerror", error => errors.push(String(error)));
                await panel.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
                owner = panel;
            }
            const endpoint = await movingEndpointIdentity(owner);
            const work = await openMovingWorkFile(owner), path = resolve(workspace, `closed-${close}.json`);
            await work.getByLabel("Work file format", { exact: true }).selectOption("state");
            await work.getByLabel("Path in Python session", { exact: true }).fill(path);
            const save = work.getByRole("button", { name: "Save file", exact: true });
            await armMovingDependencyHold(save); await save.click();
            await until(inspect, value => value.held > 0 && value.pending_studio_saves === 1 && value.pending_captures === 1,
                "genuine pending scientific capture");
            await owner.close();
            if (close === "canvas") popup = undefined; else panel = undefined;
            await until(inspect, value => !(endpoint in value.endpoint_modes)
                && value.pending_studio_saves === 0 && value.pending_captures === 0, "closed owner cleanup");
            await assert.rejects(readFile(path), { code: "ENOENT" });
            await command("release");
            await until(inspect, value => value.held === 0 && value.pending_studio_saves === 0 && value.pending_captures === 0,
                "late scientific reply cleanup");
            await assert.rejects(readFile(path), { code: "ENOENT" });
            cases.push({ mode: `closed-${close}`, genuinely_pending: true, no_late_write: true });
            await popup?.close(); popup = undefined;
        }
        // Lose the actual transport after a real pending request. The authority's
        // async loop remains alive; no inspect/poll drives its deadline meanwhile.
        const path = resolve(workspace, "transport-lost.json");
        const sentinel = Buffer.from("original destination after transport loss"); await writeFile(path, sentinel);
        await command("hold"); await command("save", { path, kind: "state", timeout: 5 });
        await until(inspect, value => value.held > 0 && value.pending_captures === 1, "pending transport-loss capture");
        await page.close();
        await new Promise(resolve => setTimeout(resolve, 5300));
        const readDisconnected = () => bridge.request([{ moving_fixture: "inspect" }]);
        const expired = await until(readDisconnected, value => value.jobs[path]?.done === true, "disconnected request deadline");
        assert.equal(expired.jobs[path].ok, false); assert.equal(expired.jobs[path].reason, "request_timeout");
        assert.equal(expired.pending_captures, 0); assert.equal(expired.pending_studio_saves, 0);
        await bridge.request([{ moving_fixture: "release" }]);
        const late = await readDisconnected();
        assert.equal(late.pending_captures, 0); assert.equal(late.pending_studio_saves, 0);
        assert.deepEqual(await readFile(path), sentinel);
        assert.equal(late.same_molsys, true); assert.equal(late.coordinates_unchanged, true);
        cases.push({ mode: "transport-lost", autonomous_deadline: true, unchanged_destination: true });
        assert.deepEqual(errors, [], "popup lifecycle must not raise page errors");
        console.log("[E2E capture lifecycle] hidden/detached canvases, recovery, closed owners and real transport loss received");
    } finally {
        await panel?.close().catch(() => {}); await popup?.close().catch(() => {});
        await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, "capture-lifetimes.json"),
            JSON.stringify({ cases, popup_errors: errors }, null, 2));
    }
}

/** Freeze an actual scientific selection at another frame, then close a pending View. */
export async function checkDynamicFreeze(context: Context) {
    const { page, workspace, command, inspect, oracle } = context;
    const errors: string[] = [];
    const popup = await openCanvas(page, errors);
    try {
        await command("empty_frame");
        for (const canvas of [page, popup]) await canvas.waitForFunction(() => {
            const c = (window as any).__mirrorController;
            const entry = c.state.regionIndex.get("moving-near");
            return c.trajectory.getTrajectoryState().currentFrame === 1 && entry?.atomIndices.length === 0;
        });
        await command("freeze_dynamic");
        const native: any[] = [];
        for (const canvas of [page, popup]) {
            const received = await canvas.waitForFunction(() => {
                const c = (window as any).__mirrorController, entry = c.state.regionIndex.get("moving-near");
                const ref = typeof entry?.component === "string" ? entry.component : entry?.component?.ref;
                const structure = c.plugin.state.data.cells.get(ref)?.obj?.data;
                if (c.trajectory.getTrajectoryState().currentFrame !== 1 || structure?.elementCount !== 1) return false;
                const unit = structure.units[0], position = [0, 0, 0];
                unit.conformation.position(unit.elements[0], position);
                return { frame: 1, atoms: entry.atomIndices, position };
            });
            const observed = await received.jsonValue(); assert.deepEqual(observed.atoms, [1]);
            observed.position.forEach((value: number, index: number) => assert.ok(Math.abs(value - oracle.coordinates_angstrom[1][1][index]) < 2e-4));
            native.push(observed);
        }
        const frozen = await inspect(); assert.equal(frozen.region_mode, "static"); assert.deepEqual(frozen.region_atoms, [1]);
        assert.equal(frozen.same_molsys, true); assert.equal(frozen.coordinates_unchanged, true);
        await popup.close();
        await page.evaluate(() => {
            const c = (window as any).__mirrorController;
            c.plugin.animationLoop.stop({ noDraw: true });
        });
        const path = resolve(workspace, "closed-view.json");
        await command("save", { path, kind: "state" });
        await until(inspect, value => value.pending_captures === 1, "pending no-draw capture");
        await command("close_view");
        const closed = await sourceJob(context, path);
        assert.equal(closed.closed, true); assert.equal(closed.jobs[path].ok, false);
        assert.equal(closed.jobs[path].reason, "view_closed");
        assert.equal(closed.pending_captures, 0); assert.equal(closed.pending_studio_saves, 0);
        await page.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.start());
        await inspect(); await assert.rejects(readFile(path), { code: "ENOENT" });
        assert.deepEqual(errors, [], "freeze/close must not raise popup errors");
        await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, "capture-freeze-close.json"),
            JSON.stringify({ native, frozen_mode: frozen.region_mode, closed_view: closed, popup_errors: errors }, null, 2));
        console.log("[E2E capture lifecycle] cross-frame static freeze and pending View close received");
    } finally { await popup.close().catch(() => {}); }
}
