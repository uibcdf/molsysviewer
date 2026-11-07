import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";

/** Actual widget/authority receiving, including correlated canvas and file bytes. */
export async function checkStudioLiveCapture(page: Page, dir: string, workspace: string) {
    const progress = (phase: string) => console.log(`[E2E Studio live] ${phase}`);
    const bridge = new PythonFixtureBridge(resolve(dir, "studio-live-capture-bridge.py"), resolve(dir, "../../../.."));
    const errors: string[] = [];
    const onError = (error: Error) => errors.push(String(error));
    page.on("pageerror", onError);
    let release: (() => Promise<void>) | undefined;
    let popup: Page | undefined;
    let panel: Page | undefined;
    try {
        release = await mountCanvasPopupFixture(page, bridge);
        await captureCanvasPopupControllers(page);
        progress("persistent widget authority loaded");
        await page.evaluate(() => {
            const w = window as any, model = w.__popupWidgetModel;
            const transport: any = w.__studioCaptureTransport = { inbound: [], outbound: [], held: [], hold: false };
            const send = model.send.bind(model);
            // Only the transport is observed/delayed. Every held reply was
            // sampled by the real renderer through the production handler.
            model.send = (message: any) => {
                const event = message.payload ?? message;
                if (event.action === "save_work_file") transport.lastSaveEnvelope = structuredClone(message);
                if (event.event === "visual_state_snapshot" || ["structure_data_begin_ack", "structure_data_chunk_ack", "structure_data_complete", "structure_data_failed"].includes(event.event)
                    || (event.event === "interaction_context_action"
                    && typeof event.request_id === "string")) transport.outbound.push(structuredClone(event));
                if (transport.hold && event.event === "visual_state_snapshot") transport.held.push(message);
                else send(message);
            };
            model.on("msg:custom", (message: any) => {
                const content = message.payload ?? message;
                if (["request_visual_state", "studio_action_result", "set_camera_snapshot", "set_trajectory_frame",
                    "structure_data_begin", "structure_data_chunk", "structure_data_cancel"].includes(content.op)) transport.inbound.push(structuredClone(content));
            });
            w.__studioReleaseCapture = () => {
                transport.hold = false;
                for (const message of transport.held.splice(0)) send(message);
            };
            w.__studioDeliverCapture = (requestId: string) => {
                const index = transport.held.findIndex((message: any) => message.payload.request_id === requestId);
                if (index < 0) throw new Error("The requested real capture reply is not held.");
                send(transport.held.splice(index, 1)[0]);
            };
        });
        const drain = async () => {
            await page.evaluate(() => (window as any).__popupFixtureDrain());
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
        };
        const identity = (endpoint: Page) => endpoint.evaluate(() => {
            const channel = (window as any).molsysviewer_popup_channel;
            return { popup: !!channel, endpoint: channel?.popupEndpointId
                ?? `widget-host:${(window as any).__popupWidgetModel.get("runtime_session_id")}` };
        });
        const observeRuntime = async (endpoint: Page) => endpoint.evaluate(() => {
            const w = window as any, c = w.__mirrorController;
            const operations = w.__studioAppliedOps = [];
            const observe = (phase: string, message?: any) => {
                const bounds = c.plugin.canvas3d?.boundingSphere;
                operations.push({ phase, message, at: performance.now(),
                    camera: c.getCameraSnapshot(), trajectory: c.trajectory.getTrajectoryState(),
                    transition: c.plugin.canvas3d?.camera.transition.inTransition,
                    sceneBounds: bounds ? { center: [...bounds.center], radius: bounds.radius } : undefined,
                });
            };
            const handle = c.handleMessage.bind(c);
            c.handleMessage = async (...args: any[]) => {
                const relevant = ["clear_all", "set_camera_snapshot", "set_trajectory_frame"].includes(args[0]?.op);
                if (relevant) observe("message-begin", args[0]);
                try { return await handle(...args); }
                finally { if (relevant) observe("message-end", args[0]); }
            };
            const load = c.loadArrayNativeMolSysPayload.bind(c);
            c.loadArrayNativeMolSysPayload = async (...args: any[]) => {
                observe("array-load-begin");
                try { return await load(...args); }
                finally { observe("array-load-end"); }
            };
        });
        await observeRuntime(page);
        const openWork = async (owner: Page) => {
            await owner.bringToFront();
            if (await owner.evaluate(() => !!(window as any).molsysviewer_init_options?.isPanelOnly)) {
                // The adopted panel uses the popup's native window.open, so it
                // deliberately needs no controller instrumentation of its own.
                const navigation = owner.getByLabel("Studio section", { exact: true });
                if (await navigation.isVisible()) await navigation.selectOption("export");
                else await owner.locator('[data-molsysviewer-group-panel-tab="export"]').click();
            } else {
                await owner.evaluate(() => {
                    const c = (window as any).__mirrorController;
                    c.setPanelMode("navigate", true);
                    c.groupPanel.openSection("export");
                });
            }
            const work = owner.locator('[data-molsysviewer-work-files]');
            await work.waitFor({ state: "visible" });
            return work;
        };
        const rotate = async (canvas: Page) => {
            await canvas.bringToFront();
            await canvas.evaluate(() => (window as any).__mirrorController.setPanelMode("navigate", false));
            const before = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
            const box = await canvas.locator("canvas").boundingBox(); assert.ok(box);
            const start = { x: box.x + box.width * .55, y: box.y + box.height * .65 };
            assert.ok(await canvas.evaluate(point => document.elementFromPoint(point.x, point.y)?.tagName === "CANVAS", start),
                "rotation must hit the visible molecular canvas");
            await canvas.mouse.move(start.x, start.y);
            await canvas.mouse.down();
            await canvas.mouse.move(box.x + box.width * .7, box.y + box.height * .72, { steps: 14 });
            await canvas.mouse.up();
            await canvas.waitForFunction(previous => (window as any).__mirrorController.getCameraSnapshot().position
                .some((value: number, index: number) => Math.abs(value - previous[index]) > 1e-4), before);
            return before;
        };
        const changeFrame = async (canvas: Page) => {
            const current = await canvas.evaluate(() => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame);
            const next = current === 2 ? current - 1 : current + 1;
            await canvas.locator(`[data-molsysviewer-trajectory-step="${current === 2 ? "previous" : "next"}"]`).click();
            await canvas.waitForFunction(index => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame === index, next);
            await drain();
            return next;
        };
        const awaitResult = async (owner: Page, action: string, before: number) => {
            await page.waitForFunction(({ action, before }) => (window as any).__studioCaptureTransport.inbound.slice(before)
                .some((message: any) => message.op === "studio_action_result" && message.action === action), { action, before });
            await drain();
            await owner.getByLabel("Path in Python session", { exact: true }).waitFor({ state: "visible" });
            await owner.waitForFunction(() => document.querySelector<HTMLInputElement>('[data-molsysviewer-work-file-path]')?.disabled === false);
            assert.ok(await owner.getByLabel("Path in Python session", { exact: true }).isEnabled());
            return page.evaluate(({ action, before }) => (window as any).__studioCaptureTransport.inbound.slice(before)
                .find((message: any) => message.op === "studio_action_result" && message.action === action), { action, before });
        };
        const submit = async (owner: Page, action: "save_work_file" | "restore_work_file") => {
            const before = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
            const work = await openWork(owner);
            if (action === "save_work_file") await work.getByRole("button", { name: "Save file", exact: true }).click();
            else {
                await work.getByRole("button", { name: "Restore file…", exact: true }).click();
                await work.getByRole("button", { name: "Confirm restore", exact: true }).click();
            }
            return awaitResult(owner, action, before);
        };
        const restoreAndCompare = async (owner: Page, canvas: Page, saved: any) => {
            const work = await openWork(owner);
            const draft = {
                path: await work.getByLabel("Path in Python session", { exact: true }).inputValue(),
                kind: await work.getByLabel("Work file format", { exact: true }).inputValue(),
                overwrite: await work.getByLabel("Allow overwriting an existing file", { exact: true }).isChecked(),
            };
            await rotate(canvas);
            const changed = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
            assert.notDeepEqual(changed.position, saved.view.camera.position);
            const result = await submit(owner, "restore_work_file");
            assert.equal(result.ok, true);
            const ownerIdentity = await identity(owner);
            const intent = await page.evaluate(requestId => (window as any).__studioCaptureTransport.outbound
                .find((event: any) => event.action === "restore_work_file" && event.request_id === requestId), result.request_id);
            assert.equal(intent._studio_owner_endpoint_id, ownerIdentity.endpoint);
            assert.equal(result.target_endpoint_id, ownerIdentity.endpoint);
            try {
                await canvas.waitForFunction(saved => {
                    const c = (window as any).__mirrorController, camera = c.getCameraSnapshot();
                    return c.trajectory.getTrajectoryState().currentFrame === saved.view.structure_index
                        && ["position", "target", "up"].every(key => camera[key].every((value: number, index: number) =>
                            Math.abs(value - saved.view.camera[key][index]) < 1e-5));
                }, saved);
            } catch (error) {
                const windows = await Promise.all([page, popup, panel].filter((endpoint): endpoint is Page => !!endpoint)
                    .map(endpoint => endpoint.evaluate(() => {
                        const w = window as any, c = w.__mirrorController;
                        const channel = w.molsysviewer_popup_channel;
                        return { channel: channel ? { mode: channel.mode, popupEndpointId: channel.popupEndpointId,
                            hostEndpointId: channel.hostEndpointId, viewerId: channel.viewerId, sessionId: channel.sessionId } : undefined,
                            camera: c?.getCameraSnapshot(),
                            trajectory: c?.trajectory.getTrajectoryState(), transition: c?.plugin.canvas3d?.camera.transition.inTransition,
                            sceneBounds: c?.plugin.canvas3d?.boundingSphere, frameRequestToken: c?.frameRequestToken,
                            hasIntentionalViewpoint: c?.state?.hasIntentionalViewpoint(),
                            structures: c?.plugin.managers.structure.hierarchy.current.structures.map((entry: any) => ({
                                ref: entry.cell.transform.ref, elements: entry.cell.obj?.data.elementCount,
                                modelNums: entry.cell.obj?.data.models.map((model: any) => model.modelNum),
                            })), applied: w.__studioAppliedOps, transport: w.__studioCaptureTransport,
                        };
                    })));
                const authority = await bridge.request([{ studio_inspect: true }]);
                console.error("[E2E Studio live restore diagnostic]", JSON.stringify({ draft, expected: saved.view, windows,
                    authority: authority.authority_state.view }));
                await page.screenshot({ path: resolve(dir, "../../../../.pytest_cache/robustness-20261106/studio-live-restore-primary-failure.png") });
                await popup?.screenshot({ path: resolve(dir, "../../../../.pytest_cache/robustness-20261106/studio-live-restore-popup-failure.png") });
                throw error;
            }
            assert.ok(await owner.locator('[data-molsysviewer-work-files]').isVisible(), "restore returns to its requesting controls");
            assert.equal(await work.getByLabel("Path in Python session", { exact: true }).inputValue(), draft.path);
            assert.equal(await work.getByLabel("Work file format", { exact: true }).inputValue(), draft.kind);
            assert.equal(await work.getByLabel("Allow overwriting an existing file", { exact: true }).isChecked(), draft.overwrite);
            assert.ok((await work.locator('[data-molsysviewer-work-file-status]').innerText())
                .includes(`Restored ${draft.kind === "state" ? "scene state" : "experimental session"}`));
        };
        const saveAndInspect = async (owner: Page, canvas: Page, path: string, kind: "state" | "session") => {
            await rotate(canvas);
            const frame = await changeFrame(canvas);
            const work = await openWork(owner);
            await work.getByLabel("Work file format", { exact: true }).selectOption(kind);
            await work.getByLabel("Path in Python session", { exact: true }).fill(path);
            const outboundStart = await page.evaluate(() => (window as any).__studioCaptureTransport.outbound.length);
            const result = await submit(owner, "save_work_file");
            assert.equal(result.ok, true, JSON.stringify(result));
            assert.ok((await work.locator('[data-molsysviewer-work-file-status]').innerText())
                .includes(`Saved ${kind === "state" ? "scene state" : "experimental session"}`));
            const observed = await page.evaluate(start => {
                const t = (window as any).__studioCaptureTransport;
                const outbound = t.outbound.slice(start);
                const save = outbound.find((event: any) => event.action === "save_work_file");
                const snapshot = outbound.find((event: any) => event.event === "visual_state_snapshot");
                const request = t.inbound.find((message: any) => message.op === "request_visual_state" && message.request_id === snapshot?.request_id);
                return { save, snapshot, request };
            }, outboundStart);
            assert.ok(observed.request && observed.snapshot, "save must obtain its own real renderer reply");
            assert.equal(observed.snapshot.capture_revision, observed.request.capture_revision);
            assert.equal(observed.snapshot.ok, true);
            assert.equal(observed.snapshot.structure_index, frame);
            const canvasIdentity = await identity(canvas), ownerIdentity = await identity(owner);
            assert.equal(observed.save._capture_endpoint_id, canvasIdentity.endpoint);
            assert.equal(observed.save._work_file_owner_endpoint_id, ownerIdentity.endpoint);
            assert.equal(observed.save._studio_owner_endpoint_id, ownerIdentity.endpoint);
            if (canvasIdentity.popup) {
                assert.equal(observed.request.target_endpoint_id, canvasIdentity.endpoint);
                assert.equal(observed.snapshot._capture_endpoint_id, canvasIdentity.endpoint);
            } else {
                assert.equal(observed.request.target_endpoint_id ?? canvasIdentity.endpoint, canvasIdentity.endpoint);
                assert.equal(observed.snapshot._capture_endpoint_id ?? canvasIdentity.endpoint, canvasIdentity.endpoint);
            }
            assert.equal(result.request_id, observed.save.request_id);
            assert.equal(result.target_endpoint_id ?? (ownerIdentity.popup ? undefined : ownerIdentity.endpoint), ownerIdentity.endpoint);
            const inspected = await bridge.request([{ studio_artifact: path, file_kind: kind }]);
            const saved = inspected.saved_state;
            assert.deepEqual(saved.view.camera, observed.snapshot.snapshot, "disk camera equals the correlated live reply exactly");
            assert.equal(saved.view.structure_index, frame);
            assert.ok(saved.annotations.some((annotation: any) => annotation.tag === "live-note"));
            if (kind === "state") assert.deepEqual(JSON.parse(await readFile(path, "utf8")), saved);
            else {
                assert.equal((await readFile(path)).subarray(0, 2).toString(), "PK");
                assert.equal(inspected.session_manifest.format, "molsysviewer-session");
                assert.ok(inspected.session_members.includes("structure.h5msm"));
            }
            return saved;
        };

        let work = await openWork(page);
        const missing = resolve(workspace, "missing-directory", "review.json");
        await work.getByLabel("Path in Python session", { exact: true }).fill(missing);
        assert.equal((await submit(page, "save_work_file")).ok, false);
        assert.equal(await work.locator('[data-molsysviewer-work-file-status]').getAttribute("role"), "alert");
        assert.equal(await work.getByLabel("Path in Python session", { exact: true }).inputValue(), missing);

        const primaryState = resolve(workspace, "primary-review.json");
        const saved = await saveAndInspect(page, page, primaryState, "state");
        const bytes = await readFile(primaryState, "utf8");
        assert.equal((await submit(page, "save_work_file")).ok, false, "existing files require explicit overwrite");
        assert.equal(await readFile(primaryState, "utf8"), bytes);
        await work.getByLabel("Allow overwriting an existing file", { exact: true }).check();
        await page.evaluate(() => {
            const c = (window as any).__mirrorController;
            c.groupPanel.openSection("viewport"); c.groupPanel.openSection("export");
        });
        assert.equal(await work.getByLabel("Path in Python session", { exact: true }).inputValue(), primaryState);
        assert.equal(await work.getByLabel("Work file format", { exact: true }).inputValue(), "state");
        assert.equal(await work.getByLabel("Allow overwriting an existing file", { exact: true }).isChecked(), true);
        const restoreCount = await page.evaluate(() => (window as any).__studioCaptureTransport.outbound.filter((event: any) => event.action === "restore_work_file").length);
        await work.getByRole("button", { name: "Restore file…", exact: true }).click();
        await work.getByRole("button", { name: "Cancel", exact: true }).click();
        assert.equal(await work.getByRole("button", { name: "Confirm restore", exact: true }).count(), 0);
        assert.equal(await page.evaluate(() => (window as any).__studioCaptureTransport.outbound.filter((event: any) => event.action === "restore_work_file").length), restoreCount);
        await restoreAndCompare(page, page, saved);
        const overwritten = await saveAndInspect(page, page, primaryState, "state");
        assert.notDeepEqual(overwritten.view.camera.position, saved.view.camera.position);
        const primarySession = await saveAndInspect(page, page, resolve(workspace, "primary-review.msv"), "session");
        await restoreAndCompare(page, page, primarySession);
        progress("primary state/session roundtrips and file controls passed");

        // Cancel a pending capture, then deliver its real late reply. No writer
        // may be entered after the authoritative cancellation acknowledgment.
        work = await openWork(page);
        const cancelled = resolve(workspace, "cancelled-review.json");
        await work.getByLabel("Work file format", { exact: true }).selectOption("state");
        await work.getByLabel("Path in Python session", { exact: true }).fill(cancelled);
        await page.evaluate(() => { (window as any).__studioCaptureTransport.hold = true; });
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await page.waitForFunction(() => (window as any).__studioCaptureTransport.held.length === 1);
        assert.ok(await work.getByLabel("Path in Python session", { exact: true }).isDisabled());
        await work.getByRole("button", { name: "Cancel save", exact: true }).click();
        await work.locator('[data-molsysviewer-work-file-status]').filter({ hasText: /cancelled/i }).waitFor();
        assert.ok(await work.getByLabel("Path in Python session", { exact: true }).isEnabled());
        await page.evaluate(() => (window as any).__studioReleaseCapture());
        await drain();
        await assert.rejects(access(cancelled), { code: "ENOENT" });
        assert.equal(await work.getByLabel("Path in Python session", { exact: true }).inputValue(), cancelled);
        progress("pending cancellation rejected its late renderer reply without writing");

        await page.evaluate(() => (window as any).__mirrorController.setPanelMode("navigate", false));
        const opened = page.waitForEvent("popup");
        await page.getByTitle("Open popup", { exact: true }).click();
        popup = await opened;
        popup.on("pageerror", onError);
        await popup.waitForFunction(() => !!(window as any).__mirrorController);
        await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
        await popup.waitForFunction(() => {
            const c = (window as any).__mirrorController;
            return c.getStructureData()?.elementCount > 0 && c.plugin.canvas3d?.reprCount.value > 0;
        });
        await observeRuntime(popup);

        // A primary verdict with the same id must not complete another
        // window's pending GUI save. Both snapshots come from real renderers.
        const collisionPopupPath = resolve(workspace, "collision-popup.json");
        const collisionPrimaryPath = resolve(workspace, "collision-primary.json");
        const popupWork = await openWork(popup);
        await popupWork.getByLabel("Path in Python session", { exact: true }).fill(collisionPopupPath);
        await popup.evaluate(() => {
            const w = window as any, c = w.__mirrorController;
            const handle = c.handleMessage.bind(c);
            w.__studioCollisionCameraReceived = false;
            c.handleMessage = async (...args: any[]) => {
                const result = await handle(...args);
                if (args[0]?.op === "set_camera_snapshot") w.__studioCollisionCameraReceived = true;
                return result;
            };
        });
        await page.evaluate(() => { (window as any).__studioCaptureTransport.hold = true; });
        await popupWork.getByRole("button", { name: "Save file", exact: true }).click();
        await page.waitForFunction(() => (window as any).__studioCaptureTransport.held.length === 1);
        const collision = await page.evaluate(path => {
            const w = window as any, t = w.__studioCaptureTransport;
            const envelope = t.lastSaveEnvelope;
            const owner = envelope.payload._work_file_owner_endpoint_id;
            if (!owner || owner === envelope.endpointId) throw new Error("The pending save must belong to the real popup.");
            const requestId = envelope.payload.request_id, primary = envelope.endpointId;
            // This is another authenticated host intention over the fixture's
            // real comm, deliberately sharing only the domain request id.
            w.__popupWidgetModel.send({ ...envelope, messageId: `primary-collision:${envelope.messageId}`,
                payload: { ...envelope.payload, request_id: requestId, path,
                    _studio_owner_endpoint_id: primary, _work_file_owner_endpoint_id: primary, _capture_endpoint_id: primary } });
            return { requestId, popup: owner, primary };
        }, collisionPrimaryPath);
        await page.waitForFunction(() => (window as any).__studioCaptureTransport.held.length === 2);
        const collisionReplies = await page.evaluate(popupId => {
            const t = (window as any).__studioCaptureTransport;
            const popup = t.held.find((message: any) => message.payload._capture_endpoint_id === popupId)?.payload;
            const primary = t.held.find((message: any) => message.payload._capture_endpoint_id !== popupId)?.payload;
            if (!popup || !primary) throw new Error("Both real renderer replies are required.");
            (window as any).__studioDeliverCapture(primary.request_id);
            return { popup, primary };
        }, collision.popup);
        await page.waitForFunction(collision => (window as any).__studioCaptureTransport.inbound.some((message: any) =>
            message.op === "studio_action_result" && message.request_id === collision.requestId
            && message.target_endpoint_id === collision.primary && message.ok), collision);
        // A same-value camera projection supplies a real popup queue barrier.
        // Any incorrectly broadcast primary verdict would precede this op.
        await page.evaluate(snapshot => (window as any).__popupWidgetModel.send({ mirror_fixture: "camera", snapshot }), collisionReplies.primary.snapshot);
        await popup.waitForFunction(() => (window as any).__studioCollisionCameraReceived);
        await drain();
        assert.ok(await popupWork.getByLabel("Path in Python session", { exact: true }).isDisabled(), "a primary result cannot unlock a popup save with the same id");
        assert.doesNotMatch(await popupWork.locator('[data-molsysviewer-work-file-status]').innerText(), /Saved scene state/);
        await assert.rejects(access(collisionPopupPath), { code: "ENOENT" });
        assert.deepEqual(JSON.parse(await readFile(collisionPrimaryPath, "utf8")).view.camera, collisionReplies.primary.snapshot);
        await page.evaluate(() => (window as any).__studioReleaseCapture());
        await popup.waitForFunction(() => document.querySelector<HTMLInputElement>('[data-molsysviewer-work-file-path]')?.disabled === false);
        await drain();
        assert.ok((await popupWork.locator('[data-molsysviewer-work-file-status]').innerText()).includes("Saved scene state"));
        assert.deepEqual(JSON.parse(await readFile(collisionPopupPath, "utf8")).view.camera, collisionReplies.popup.snapshot);
        progress("same-id primary verdict left the popup save pending until its own reply");

        for (const kind of ["state", "session"] as const) {
            const file = resolve(workspace, `popup-review.${kind === "state" ? "json" : "msv"}`);
            const captured = await saveAndInspect(popup, popup, file, kind);
            await restoreAndCompare(popup, popup, captured);
            progress(`canvas popup ${kind} roundtrip passed`);
        }

        // Correlated Studio ownership also applies to ordinary list actions.
        // Their controls must receive the verdict after Python changes the real scene.
        await popup.evaluate(() => (window as any).__mirrorController.groupPanel.openSection("annotations"));
        const management = popup.locator('[data-molsysviewer-list-management="annotations"]');
        if (!await management.evaluate((element: HTMLDetailsElement) => element.open)) await management.locator(":scope > summary").click();
        const marked = popup.locator('[data-molsysviewer-list-mark="annotations:live-note"]');
        for (const operation of ["hide", "show"]) {
            await marked.check();
            const before = await page.evaluate(() => (window as any).__studioCaptureTransport.inbound.length);
            await popup.locator(`[data-molsysviewer-list-batch="annotations:${operation}"]`).click();
            await page.waitForFunction(before => (window as any).__studioCaptureTransport.inbound.slice(before)
                .some((message: any) => message.op === "studio_action_result" && message.action === "batch_scene_objects"), before);
            const received = await page.evaluate(before => {
                const t = (window as any).__studioCaptureTransport;
                const result = t.inbound.slice(before).find((message: any) => message.op === "studio_action_result" && message.action === "batch_scene_objects");
                return { result, intent: t.outbound.find((event: any) => event.action === "batch_scene_objects" && event.request_id === result.request_id) };
            }, before);
            assert.equal(received.result.ok, true, JSON.stringify(received.result));
            const owner = await identity(popup);
            assert.equal(received.intent._studio_owner_endpoint_id, owner.endpoint);
            assert.equal(received.result.target_endpoint_id, owner.endpoint);
            await popup.waitForFunction(hidden => {
                const c = (window as any).__mirrorController;
                return c.annotationSummaries.find((annotation: any) => annotation.tag === "live-note")?.hidden === hidden
                    && document.querySelector<HTMLInputElement>('[data-molsysviewer-list-mark="annotations:live-note"]')?.disabled === false
                    && document.querySelector<HTMLElement>('[data-molsysviewer-group-panel-section="annotations"]')?.innerText.includes("Completed.");
            }, operation === "hide");
        }
        progress("popup correlated batch hide/show received only its owning verdicts");
        await openWork(popup);
        const detached = popup.waitForEvent("popup");
        await popup.getByTitle("Popout panel to external window", { exact: true }).click();
        panel = await detached;
        panel.on("pageerror", onError);
        await panel.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
        await panel.locator('[data-molsysviewer-group-panel-tab="export"]').waitFor({ state: "attached" });
        assert.equal(await panel.locator("canvas").isVisible(), false);
        for (const kind of ["state", "session"] as const) {
            const file = resolve(workspace, `detached-review.${kind === "state" ? "json" : "msv"}`);
            const captured = await saveAndInspect(panel, popup, file, kind);
            await restoreAndCompare(panel, popup, captured);
            progress(`detached Studio ${kind} roundtrip used its originating canvas`);
        }
        assert.deepEqual(errors, []);
        console.log("[E2E Studio] persistent primary/popup/detached saves captured exact camera/frame, restored perturbed scenes, and cancelled without writing");
    } finally {
        await panel?.close();
        await popup?.close();
        await page.evaluate(async () => {
            (window as any).__popupWidgetDispose?.();
            await (window as any).__popupFixtureDrain?.();
        }).catch(() => {});
        await release?.();
        await bridge.close();
        page.off("pageerror", onError);
    }
}
