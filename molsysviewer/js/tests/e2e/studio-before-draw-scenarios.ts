import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import type { Locator, Page } from "playwright";

/** Actual Mol* pause with live DOM/transport; no renderer or scientific fakes. */
export async function checkStudioCancelBeforeDraw(options: {
    page: Page; owner: Page; canvas: Page; path: string;
    openWork(owner: Page): Promise<Locator>;
    identity(endpoint: Page): Promise<{ popup: boolean; endpoint: string }>;
    drain(): Promise<void>;
}) {
    const { page, owner, canvas, path, openWork, identity, drain } = options;
    const work = await openWork(owner);
    await work.getByLabel("Work file format", { exact: true }).selectOption("state");
    await work.getByLabel("Path in Python session", { exact: true }).fill(path);
    const starts = await page.evaluate(() => {
        const t = (window as any).__studioCaptureTransport;
        return { inbound: t.inbound.length, outbound: t.outbound.length };
    });
    await canvas.evaluate(() => {
        const w = window as any, c = w.__mirrorController, live = c.plugin.canvas3d;
        const probe = w.__studioDrawCancellation = { draws: 0, requests: 0 };
        let replay = true;
        const subscription = live.didDraw.subscribe(() => { if (!replay) probe.draws++; });
        replay = false;
        const requestDraw = live.requestDraw.bind(live);
        live.requestDraw = (...args: any[]) => { probe.requests++; return requestDraw(...args); };
        w.__studioReleaseDrawCancellation = () => {
            live.requestDraw = requestDraw;
            subscription.unsubscribe();
            c.plugin.animationLoop.start();
        };
        // Mol*'s own API pauses completed draws while controls and comm stay live.
        c.plugin.animationLoop.stop({ noDraw: true });
    });
    try {
        await canvas.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        assert.equal(await canvas.evaluate(() => (window as any).__studioDrawCancellation.draws), 0);
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await page.waitForFunction(start => (window as any).__studioCaptureTransport.inbound.slice(start)
            .some((message: any) => message.op === "request_visual_state"), starts.inbound);
        await canvas.waitForFunction(() => (window as any).__studioDrawCancellation.requests > 0);
        const capture = await page.evaluate(start => (window as any).__studioCaptureTransport.inbound.slice(start)
            .find((message: any) => message.op === "request_visual_state"), starts.inbound);
        const intent = await page.evaluate(start => (window as any).__studioCaptureTransport.outbound.slice(start)
            .find((message: any) => message.action === "save_work_file"), starts.outbound);
        const ownerId = (await identity(owner)).endpoint, canvasIdentity = await identity(canvas);
        assert.equal(intent._work_file_owner_endpoint_id, ownerId);
        assert.equal(intent._capture_endpoint_id, canvasIdentity.endpoint);
        assert.notEqual(capture.request_id, intent.request_id, "broker and Studio correlations are separate");
        await work.getByRole("button", { name: "Cancel save", exact: true }).click();
        await page.waitForFunction(({ start, id }) => (window as any).__studioCaptureTransport.inbound.slice(start)
            .some((message: any) => message.op === "cancel_visual_state" && message.request_id === id),
        { start: starts.inbound, id: capture.request_id });
        await owner.waitForFunction(() => document.querySelector<HTMLInputElement>('[data-molsysviewer-work-file-path]')?.disabled === false
            && /cancelled/i.test(document.querySelector('[data-molsysviewer-work-file-status]')?.textContent ?? ""), undefined, { timeout: 2000 });
        const control = await page.evaluate(({ start, id }) => (window as any).__studioCaptureTransport.inbound.slice(start)
            .find((message: any) => message.op === "cancel_visual_state" && message.request_id === id),
        { start: starts.inbound, id: capture.request_id });
        assert.equal(control.capture_revision, capture.capture_revision);
        if (canvasIdentity.popup) assert.equal(control.target_endpoint_id, canvasIdentity.endpoint);
        const verdict = await page.evaluate(({ start, id }) => (window as any).__studioCaptureTransport.inbound.slice(start)
            .find((message: any) => message.op === "studio_action_result" && message.action === "cancel_work_file" && message.request_id === id),
        { start: starts.inbound, id: intent.request_id });
        assert.equal(verdict.ok, true);
        assert.equal(verdict.target_endpoint_id, ownerId);
        // A same-value projection of the actual camera is a scene-queue barrier.
        // It must complete while Mol* still cannot draw.
        const applied = await canvas.evaluate(() => (window as any).__studioAppliedOps.length);
        const camera = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
        await page.evaluate(snapshot => (window as any).__popupWidgetModel.send({ mirror_fixture: "camera", snapshot }), camera);
        await canvas.waitForFunction(start => (window as any).__studioAppliedOps.slice(start)
            .some((event: any) => event.phase === "message-end" && event.message?.op === "set_camera_snapshot"), applied);
        await drain();
        assert.equal(await canvas.evaluate(() => (window as any).__studioDrawCancellation.draws), 0);
        assert.equal(await page.evaluate(({ start, id }) => (window as any).__studioCaptureTransport.outbound.slice(start)
            .some((event: any) => event.event === "visual_state_snapshot" && event.request_id === id),
        { start: starts.outbound, id: capture.request_id }), false, "aborted capture sends no snapshot or renderer refusal");
        await assert.rejects(access(path), { code: "ENOENT" });
    } finally {
        await canvas.evaluate(() => (window as any).__studioReleaseDrawCancellation?.());
    }
    await drain();
    await assert.rejects(access(path), { code: "ENOENT" });
}
