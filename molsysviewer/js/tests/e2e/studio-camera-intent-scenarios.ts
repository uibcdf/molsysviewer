import assert from "node:assert/strict";
import type { Locator, Page } from "playwright";

/** Real saved camera, native held event, real render pause and native new input. */
export async function checkStudioCameraIntent(options: {
    page: Page; owner: Page; canvas: Page; saved: any;
    openWork(owner: Page): Promise<Locator>; rotate(canvas: Page): Promise<unknown>; drain(): Promise<void>;
}) {
    const { page, owner, canvas, saved, openWork, rotate, drain } = options;
    await canvas.evaluate(camera => {
        const w = window as any, c = w.__mirrorController;
        const same = (a: any, b: any) => ["position", "target", "up"].every(key => a?.[key]?.every((v: number, i: number) => Math.abs(v - b[key][i]) < 1e-5));
        const p = w.__staleCameraProbe = { saved: camera, observations: [], armed: true, held: undefined,
            draws: [], received: [] };
        const listener = (event: MessageEvent) => {
            if (event.source === window.opener && event.data?.envelope?.action === "molsysviewer-sync-camera") {
                const envelope = event.data.envelope;
                p.received.push({ at: performance.now(), envelope: structuredClone(envelope) });
                if (same(envelope.payload?.snapshot, camera)) p.expectedPacket = envelope;
            }
        };
        window.addEventListener("message", listener);
        let replay = true;
        const sub = c.plugin.canvas3d.didDraw.subscribe(() => { if (!replay) p.draws.push(c.getCameraSnapshot()); });
        replay = false;
        w.__finishCameraIntentGuard = () => {
            window.removeEventListener("message", listener);
            sub.unsubscribe();
            w.__staleReleaseMessageHooks();
            c.plugin.animationLoop.start();
        };
    }, saved.view.camera);
    try {
        await rotate(page);
        await canvas.waitForFunction(() => !!(window as any).__staleCameraProbe.held);
        const held = await canvas.evaluate(() => {
            const p = (window as any).__staleCameraProbe;
            return { envelope: structuredClone(p.held.data.envelope), actualSource: p.held.source === window.opener };
        });
        assert.equal(held.actualSource, true);
        const oldRevision = held.envelope.payload.camera_revision;
        assert.ok(Number.isSafeInteger(oldRevision) && oldRevision >= 0);
        const start = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
        await canvas.evaluate(() => {
            const w = window as any;
            w.__mirrorController.plugin.animationLoop.stop({ noDraw: true });
            w.__staleCameraProbe.draws.length = 0;
        });
        const work = await openWork(owner);
        await work.getByRole("button", { name: "Restore file…", exact: true }).click();
        await work.getByRole("button", { name: "Confirm restore", exact: true }).click();
        await page.waitForFunction(({ start, oldRevision }) => (window as any).__studioCaptureTransport.inbound.slice(start)
            .some((msg: any) => msg.op === "set_camera_snapshot" && msg.camera_revision > oldRevision), { start, oldRevision });
        const authority = await page.evaluate(start => (window as any).__studioCaptureTransport.inbound.slice(start)
            .find((msg: any) => msg.op === "set_camera_snapshot"), start);
        await canvas.waitForFunction(revision => (window as any).__studioAppliedOps.some((event: any) => event.phase === "message-end"
            && event.message?.op === "set_camera_snapshot" && event.message.camera_revision === revision), authority.camera_revision);
        await page.waitForFunction(camera => ["position", "target", "up"].every(key => (window as any).__mirrorController.getCameraSnapshot()[key]
            .every((value: number, index: number) => Math.abs(value - camera[key][index]) < 1e-5)), saved.view.camera);
        await canvas.waitForFunction(revision => (window as any).__staleCameraProbe.expectedPacket?.payload.camera_revision === revision, authority.camera_revision);
        await owner.waitForFunction(() => /Restored experimental session|Restored scene state/.test(document.querySelector('[data-molsysviewer-work-file-status]')?.textContent ?? ""));
        const applied = await canvas.evaluate(() => (window as any).__studioAppliedOps.length);
        await canvas.evaluate(() => {
            const w = window as any, p = w.__staleCameraProbe;
            if (p.held.source !== window.opener || JSON.stringify(p.held.data.envelope) !== p.heldEnvelopeJson) throw new Error("Held native camera event changed");
            if (p.received.some((item: any) => item.envelope.messageId === p.held.data.envelope.messageId)) throw new Error("Held camera event was already delivered");
            p.armed = false;
            p.delivery = w.__staleFlushOriginalCallbacks();
        });
        await canvas.waitForFunction(() => {
            const p = (window as any).__staleCameraProbe;
            return p.received.filter((item: any) => item.envelope.messageId === p.held.data.envelope.messageId).length === 1;
        });
        await canvas.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        assert.equal(await canvas.evaluate(() => (window as any).__staleCameraProbe.draws.length), 0);
        assert.equal(await canvas.evaluate(({ start, pose }) => (window as any).__studioAppliedOps.slice(start).some((event: any) =>
            event.message?.op === "set_camera_snapshot" && JSON.stringify(event.message.snapshot?.position) === JSON.stringify(pose)),
        { start: applied, pose: held.envelope.payload.snapshot.position }), false, "an old epoch cannot schedule a camera reset");
        await canvas.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.start());
        await canvas.waitForFunction(() => (window as any).__staleCameraProbe.draws.length > 0);
        const first = await canvas.evaluate(() => (window as any).__staleCameraProbe.draws[0]);
        for (const key of ["position", "target", "up"]) assert.ok(first[key].every((value: number, index: number) =>
            Math.abs(value - saved.view.camera[key][index]) < 1e-5));
        await drain();

        // A new real gesture after the newer intent is received must supersede
        // the pending reset and continue mirroring at that same authority epoch.
        await rotate(canvas);
        await canvas.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.stop({ noDraw: true }));
        const nextStart = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
        await page.evaluate(snapshot => (window as any).__popupWidgetModel.send({ mirror_fixture: "camera", snapshot }), saved.view.camera);
        await page.waitForFunction(start => (window as any).__studioCaptureTransport.inbound.slice(start)
            .some((msg: any) => msg.op === "set_camera_snapshot"), nextStart);
        const next = await page.evaluate(start => (window as any).__studioCaptureTransport.inbound.slice(start).find((msg: any) => msg.op === "set_camera_snapshot"), nextStart);
        await canvas.waitForFunction(revision => (window as any).__studioAppliedOps.some((event: any) => event.phase === "message-end"
            && event.message?.camera_revision === revision), next.camera_revision);
        await canvas.bringToFront();
        await canvas.evaluate(() => (window as any).__mirrorController.setPanelMode("navigate", false));
        const beforeInput = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
        const box = await canvas.locator("canvas").boundingBox(); assert.ok(box);
        const point = { x: box.x + box.width * .55, y: box.y + box.height * .65 };
        assert.ok(await canvas.evaluate(p => document.elementFromPoint(p.x, p.y)?.tagName === "CANVAS", point));
        await canvas.mouse.move(point.x, point.y);
        await canvas.mouse.down();
        await canvas.mouse.move(box.x + box.width * .7, box.y + box.height * .72, { steps: 14 });
        await canvas.mouse.up();
        await canvas.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.start());
        await canvas.waitForFunction(position => (window as any).__mirrorController.getCameraSnapshot().position
            .some((value: number, index: number) => Math.abs(value - position[index]) > 1e-4), beforeInput);
        await drain();
        await page.waitForFunction(revision => (window as any).__studioCaptureTransport.peerCameras.some((packet: any) => packet.camera_revision === revision), next.camera_revision);
        const current = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
        assert.notDeepEqual(current.position, saved.view.camera.position);
        await page.waitForFunction(position => (window as any).__mirrorController.getCameraSnapshot().position
            .every((value: number, index: number) => Math.abs(value - position[index]) < 1e-5), current.position);

        // Exercise the unchanged Python partial-snapshot API with a valid
        // nonunit up vector. Completion uses Mol*'s resolved full target.
        const up = current.up.map((value: number) => value * 2);
        const partialStart = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
        await page.evaluate(up => (window as any).__popupWidgetModel.send({ mirror_fixture: "camera", snapshot: { up } }), up);
        await page.waitForFunction(start => (window as any).__studioCaptureTransport.inbound.slice(start).some((msg: any) => msg.op === "set_camera_snapshot"), partialStart);
        const partial = await page.evaluate(start => (window as any).__studioCaptureTransport.inbound.slice(start).find((msg: any) => msg.op === "set_camera_snapshot"), partialStart);
        assert.deepEqual(partial.snapshot, { up });
        await page.waitForFunction(revision => (window as any).__studioCaptureTransport.peerCameras.some((packet: any) => packet.camera_revision === revision), partial.camera_revision);
        const actualUp = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().up);
        const expectedNorm = Math.hypot(...up), actualNorm = Math.hypot(...actualUp);
        assert.ok(up.every((value: number, index: number) => Math.abs(value / expectedNorm - actualUp[index] / actualNorm) < 1e-5));

        await checkStudioCameraNavigation({ page, canvas, camera: saved.view.camera, drain });
    } finally {
        await canvas.evaluate(() => (window as any).__finishCameraIntentGuard?.());
    }
}


/** A pending authority pose replaced by real Mol* navigation before any draw. */
export async function checkStudioCameraNavigation(options: {
    page: Page; canvas: Page; camera: any; drain(): Promise<void>;
}) {
    const { page, canvas, camera, drain } = options;
    let phase = "setup";
    const observe = () => {
        const w = window as any, c = w.__mirrorController, live = c.plugin.canvas3d;
        const p = w.__studioNavigationProbe = { draws: [], events: [], phase: "setup" };
        const record = (kind: string, data?: any) => p.events.push({ kind, data, phase: p.phase, at: performance.now(),
            camera: c.getCameraSnapshot(), target: structuredClone(live.camera.transition.target),
            transition: live.camera.transition.inTransition });
        const handle = c.handleMessage;
        const wrapped = async function(this: any, message: any, options?: any) {
            const hooks = options?.cameraIntent;
            record("message-begin", message);
            if (hooks) options = { ...options, cameraIntent: { ...hooks,
                beforeResolve() { record("intent-resolve", message); hooks.beforeResolve(); },
                registerCleanup(release: () => void) {
                    hooks.registerCleanup(() => { record("intent-cleanup", { message, aborted: hooks.signal.aborted }); release(); });
                },
            } };
            try { return await handle.call(this, message, options); }
            finally { record("message-end", message); }
        };
        c.handleMessage = wrapped;
        let replay = true;
        const drawn = live.didDraw.subscribe(() => {
            if (replay) return;
            p.draws.push(c.getCameraSnapshot()); record("did-draw");
        });
        replay = false;
        const changed = live.camera.stateChanged.subscribe((snapshot: any) => record("state-changed", snapshot));
        const peer = (event: MessageEvent) => {
            if (event.source === window.opener && event.data?.envelope?.action === "molsysviewer-sync-camera") {
                record("native-peer", event.data.envelope);
            }
        };
        window.addEventListener("message", peer);
        w.__finishStudioNavigationProbe = () => {
            if (c.handleMessage === wrapped) c.handleMessage = handle;
            drawn.unsubscribe(); changed.unsubscribe(); window.removeEventListener("message", peer);
            c.plugin.animationLoop.start();
        };
    };
    await page.evaluate(observe);
    await canvas.evaluate(observe);
    try {
        for (const navigation of ["reset", "zoom", "local-reset"] as const) {
            phase = navigation;
            console.log(`[E2E Studio navigation] ${navigation}: pausing both renderers`);
            const begins = await page.evaluate(() => {
                const t = (window as any).__studioCaptureTransport;
                return { inbound: t.inbound.length, peers: t.peerCameras.length };
            });
            await canvas.evaluate(navigation => {
                const w = window as any;
                w.__studioNavigationProbe.phase = navigation;
                w.__mirrorController.plugin.animationLoop.stop({ noDraw: true });
                w.__studioNavigationProbe.draws.length = 0;
            }, navigation);
            await page.evaluate(navigation => {
                const w = window as any;
                w.__studioNavigationProbe.phase = navigation;
                w.__mirrorController.plugin.animationLoop.stop({ noDraw: true });
                w.__studioNavigationProbe.draws.length = 0;
            }, navigation);
            await page.evaluate(snapshot => (window as any).__popupWidgetModel.send({ mirror_fixture: "camera", snapshot }), camera);
            await page.waitForFunction(start => (window as any).__studioCaptureTransport.inbound.slice(start)
                .some((msg: any) => msg.op === "set_camera_snapshot"), begins.inbound);
            const pending = await page.evaluate(start => (window as any).__studioCaptureTransport.inbound.slice(start)
                .find((msg: any) => msg.op === "set_camera_snapshot"), begins.inbound);
            await canvas.waitForFunction(revision => (window as any).__studioAppliedOps.some((event: any) => event.phase === "message-end"
                && event.message?.op === "set_camera_snapshot" && event.message.camera_revision === revision), pending.camera_revision);
            await page.waitForFunction(revision => (window as any).__studioNavigationProbe.events.some((event: any) => event.kind === "message-end"
                && event.data?.op === "set_camera_snapshot" && event.data.camera_revision === revision), pending.camera_revision);
            let completedRevision = pending.camera_revision;
            if (navigation === "local-reset") {
                await canvas.evaluate(() => (window as any).__mirrorController.resetView());
            } else {
                await page.evaluate(navigation => (window as any).__popupWidgetModel.send({ studio_navigation: navigation }), navigation);
                const op = navigation === "reset" ? "reset_view" : "zoom";
                await page.waitForFunction(({ start, op }) => (window as any).__studioCaptureTransport.inbound.slice(start)
                    .some((msg: any) => msg.op === op), { start: begins.inbound, op });
                const latest = await page.evaluate(({ start, op }) => (window as any).__studioCaptureTransport.inbound.slice(start)
                    .find((msg: any) => msg.op === op), { start: begins.inbound, op });
                assert.ok(latest.camera_revision > pending.camera_revision);
                completedRevision = latest.camera_revision;
                await canvas.waitForFunction(({ op, revision }) => (window as any).__studioAppliedOps.some((event: any) => event.phase === "message-end"
                    && event.message?.op === op && event.message.camera_revision === revision), { op, revision: completedRevision });
                await page.waitForFunction(({ op, revision }) => (window as any).__studioNavigationProbe.events.some((event: any) => event.kind === "message-end"
                    && event.data?.op === op && event.data.camera_revision === revision), { op, revision: completedRevision });
            }
            assert.equal(await canvas.evaluate(() => (window as any).__studioNavigationProbe.draws.length), 0);
            assert.equal(await page.evaluate(() => (window as any).__studioNavigationProbe.draws.length), 0);
            assert.equal(await page.evaluate(({ start, revision }) => (window as any).__studioCaptureTransport.peerCameras.slice(start)
                .some((packet: any) => packet.camera_revision === revision), { start: begins.peers, revision: completedRevision }), false);
            console.log(`[E2E Studio navigation] ${navigation}: resuming origin at revision ${completedRevision}`);
            await canvas.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.start());
            await page.waitForFunction(({ start, revision }) => (window as any).__studioCaptureTransport.peerCameras.slice(start)
                .some((packet: any) => packet.camera_revision === revision), { start: begins.peers, revision: completedRevision });
            console.log(`[E2E Studio navigation] ${navigation}: origin relayed revision ${completedRevision}`);
            assert.equal(await canvas.evaluate(phase => (window as any).__studioNavigationProbe.events.some((event: any) =>
                event.phase === phase && event.kind === "did-draw" && !event.transition
                && ["position", "target"].every(key => event.camera[key].every((value: number, index: number) =>
                    Math.abs(value - event.target[key][index]) < 1e-5))), navigation), true,
            "relay requires the surviving target on a real completed draw");
            assert.equal(await page.evaluate(() => (window as any).__studioNavigationProbe.draws.length), 0,
                "the origin must complete and relay before the primary renderer resumes");
            await page.waitForFunction(phase => (window as any).__studioNavigationProbe.events.some((event: any) =>
                event.phase === phase && event.kind === "message-end" && event.data?.op === "set_camera_snapshot"
                && event.data.camera_revision === undefined), navigation);
            await page.evaluate(() => (window as any).__mirrorController.plugin.animationLoop.start());
            await drain();
            const resolved = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
            await page.waitForFunction(camera => ["position", "target"].every(key => (window as any).__mirrorController.getCameraSnapshot()[key]
                .every((value: number, index: number) => Math.abs(value - camera[key][index]) < 1e-5)), resolved);
        }
    } catch (error) {
        const diagnostic = await canvas.evaluate(() => {
            const w = window as any, c = w.__mirrorController;
            return { probe: w.__studioNavigationProbe, camera: c.getCameraSnapshot(),
                target: c.plugin.canvas3d.camera.transition.target, transition: c.plugin.canvas3d.camera.transition.inTransition,
                pendingOwner: !!c.pendingCameraIntent, applied: w.__studioAppliedOps?.slice(-12) };
        });
        console.error("[E2E Studio navigation diagnostic] " + JSON.stringify({ phase, ...diagnostic }));
        throw error;
    } finally {
        await canvas.evaluate(() => (window as any).__finishStudioNavigationProbe?.());
        await page.evaluate(() => (window as any).__finishStudioNavigationProbe?.());
    }
}
