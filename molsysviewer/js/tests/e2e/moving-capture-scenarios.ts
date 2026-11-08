import assert from "node:assert/strict";
import { copyFile, readFile, writeFile } from "node:fs/promises";
import { basename, resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { checkAnnotationPresentation } from "./annotation-presentation-scenarios";
import { observeMovingCaptureCanvas, observeMovingPopupBootstrap, releaseMovingCaptureObserver } from "./moving-canvas-observer";
import { movingEndpointIdentity, openMovingWorkFile } from "./moving-work-file-ui";

/** Exercise the unadvertised v2 receiver against a genuinely moving authority. */
export async function checkMovingCapture(page: Page, dir: string,
    phase: "all" | "empty" | "presentation" | "state" | "popup" | "endpoints" | "bootstrap" = "all") {
    await withFixtureWorkspace("moving-capture", async workspace => {
        const bridge = new PythonFixtureBridge(resolve(dir, "moving-capture-bridge.py"), resolve(dir, "../../../.."),
            90000, { env: fixtureEnvironment(workspace), observeTransport: true });
        let release: (() => Promise<void>) | undefined;
        let popup: Page | undefined, panel: Page | undefined;
        let inspectSource: (() => Promise<any>) | undefined;
        const endpointErrors: string[] = [];
        const endpointWarnings: string[] = [];
        const consoleObserver = (message: any) => {
            if (endpointWarnings.length < 16 && /scene snapshot|Popout sync error|popup message queue error/.test(message.text())) {
                endpointWarnings.push(message.text().slice(0, 2048));
            }
        };
        page.on("console", consoleObserver);
        const closePeers = async () => {
            await panel?.close().catch(() => {}); panel = undefined;
            await popup?.evaluate(releaseMovingCaptureObserver).catch(() => {});
            await popup?.close().catch(() => {}); popup = undefined;
        };
        try {
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page, true, `(${observeMovingPopupBootstrap.toString()})(module)`);
            await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
            console.log("[E2E moving capture] real widget and annotation inspector ready");
            await page.evaluate(() => {
                const w = window as any, c = w.__mirrorController, model = w.__popupWidgetModel;
                const monitor: any = w.__movingCapture = { inbound: [], commands: [], intents: [], outbound: [], captures: [], draws: [], frames: [], gates: {},
                    captureErrors: [], annotationOffsets: [], readiness: [], timing: [], bootstraps: [], activeCapture: null as any, heldSource: null as any };
                const releaseHeldWhenObserved = () => {
                    const active = monitor.activeCapture;
                    if (!active?.requestSeen || !monitor.heldSource || active.released
                        || (active.playing && active.frameChanges < 2)) return;
                    active.released = { ms: performance.now(), frameChanges: active.frameChanges,
                        heldSource: { ...monitor.heldSource }, repliesBeforeRelease: monitor.outbound.length - active.outboundStart };
                    // This existing frame/transport observer releases only the
                    // genuine held envelopes. It never supplies geometry or
                    // changes playback, and avoids another slow CDP round trip.
                    void model.send({ moving_fixture: "release" }).catch((error: any) => {
                        active.releaseError = String(error);
                    });
                };
                monitor.releaseHeldWhenObserved = releaseHeldWhenObserved;
                const send = model.send.bind(model);
                model.send = (message: any) => {
                    const payload = message.payload ?? message;
                    if (payload.action === "save_work_file") {
                        monitor.intents.push(structuredClone(payload));
                        if (monitor.activeCapture) monitor.activeCapture.intentAt = performance.now();
                        if (monitor.intents.length > 32) monitor.intents.shift();
                    }
                    if (payload.moving_fixture || ["request_dynamic_region_evaluation", "visual_state_snapshot"].includes(payload.event)) {
                        monitor.timing.push({ ms: performance.now(), stage: "send", name: payload.moving_fixture ?? payload.event, frame: payload.frame });
                        if (monitor.timing.length > 128) monitor.timing.shift();
                    }
                    if (payload.event === "visual_state_snapshot") {
                        monitor.outbound.push(structuredClone(payload));
                        if (payload.ok) monitor.captures.push({ reply: structuredClone(payload),
                            endpointId: payload._capture_endpoint_id ?? "primary",
                            draw: (monitor.monitors.get(payload._capture_endpoint_id ?? "primary")?.draws ?? []).findLast((draw: any) => draw.structure_index === payload.structure_index
                                && JSON.stringify(draw.snapshot) === JSON.stringify(payload.snapshot)) });
                        if (monitor.captures.length > 32) monitor.captures.shift();
                    }
                    return Promise.resolve(send(message)).then(result => {
                        if (result?.moving_fixture_held) {
                            monitor.heldSource = result.moving_fixture_held;
                            releaseHeldWhenObserved();
                        }
                        return result;
                    });
                };
                model.on("msg:custom", (message: any) => {
                    const payload = message.payload ?? message;
                    if (payload.event === "popup_scene_snapshot") monitor.bootstraps.push({ ms: performance.now(),
                        mode: payload.mode, messages: payload.messages?.map((item: any) => ({ op: item.op, tag: item.tag ?? item.options?.tag })) });
                    monitor.commands.push({ ms: performance.now(), op: payload.op, index: payload.index, frame: payload.frame, action: payload.action });
                    if (monitor.commands.length > 128) monitor.commands.shift();
                    if (["request_visual_state", "set_dynamic_region_atoms", "cancel_visual_state", "studio_action_result"].includes(payload.op)) {
                        monitor.inbound.push(structuredClone(payload));
                    }
                    if (payload.op === "request_visual_state" && monitor.activeCapture) {
                        monitor.activeCapture.sourceRequestAt = performance.now();
                        monitor.activeCapture.timeoutMs = payload.capture_timeout_ms;
                    }
                    if (payload.op === "request_visual_state" && payload.capture_version === 2
                        && monitor.activeCapture?.endpointId === "primary" && !payload.target_endpoint_id) {
                        const active = monitor.activeCapture;
                        active.requestSeen = true; active.requestId = payload.request_id;
                        active.receivedAt = performance.now();
                        active.lastFrame = c.trajectory.getTrajectoryState().currentFrame;
                        releaseHeldWhenObserved();
                    }
                });
            });
            await page.evaluate(observeMovingCaptureCanvas);
            const command = async (moving_fixture: string, details = {}) => {
                const result = await page.evaluate(async message => {
                    const result = await (window as any).__popupWidgetModel.send(message);
                    const monitor = (window as any).__movingCapture;
                    monitor.timing.push({ ms: performance.now(), stage: "ack", name: message.moving_fixture });
                    if (monitor.timing.length > 128) monitor.timing.shift();
                    return result;
                }, { moving_fixture, ...details });
                assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
                return result;
            };
            // Every response shares the same comm delivery path, including
            // diagnostics. A direct bridge read could consume async scientific
            // messages without delivering them to the real widget.
            const inspect = async () => command("inspect");
            inspectSource = inspect;
            const awaitJob = async (path: string) => {
                for (let count = 0; count < 160; count++) {
                    const result = await inspect();
                    if (result.jobs[path]?.done) return result;
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error("Moving save did not complete its bounded source request");
            };
            if (phase !== "bootstrap") await command("enable");
            await command("play");
            await page.waitForFunction(() => (window as any).__movingCapture.frames.length >= 3);
            console.log("[E2E moving capture] uninterrupted camera and trajectory observed");
            const oracle = await inspect();
            const near = (point: number[], expected: number[], label: string) => {
                assert.equal(point?.length, expected.length, label);
                point.forEach((value, index) => assert.ok(Math.abs(value - expected[index]) < 2e-4,
                    `${label}: ${JSON.stringify(point)} != ${JSON.stringify(expected)}`));
            };
            if (phase === "bootstrap") {
                // Fault only the comm delivery of an actual canonical reply;
                // Python still builds the real scene and receives native acks.
                await command("hold_bootstrap");
                const bounds = await page.locator("canvas").boundingBox(); assert.ok(bounds);
                await page.mouse.move(bounds.x + 12, bounds.y + 12);
                const opened = page.waitForEvent("popup");
                await page.getByTitle("Open popup", { exact: true }).click();
                popup = await opened;
                popup.on("pageerror", error => endpointErrors.push(String(error)));
                await popup.waitForFunction(() => !!(window as any).__mirrorController);
                await popup.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
                await popup.evaluate(observeMovingCaptureCanvas);
                const retry = popup.getByRole("button", { name: "Try again", exact: true });
                await retry.waitFor({ state: "visible" });
                assert.ok((await inspect()).held_bootstraps > 0, "a genuine Python canonical snapshot must be withheld");
                await command("release_bootstrap");
                await page.evaluate(() => (window as any).__popupFixtureDrain());
                assert.equal(await retry.isVisible(), true, "a late expired reply cannot turn failure into an empty success");
                await retry.click();
                await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
                // This is a bootstrap/recovery control, not moving-capture
                // qualification. Stop explicitly for a stable native oracle.
                await command("empty_frame");
                await popup.waitForFunction(() => (window as any).__movingCapture.draws.at(-1)?.structure_index === 1);
                const recovered = await popup.evaluate(() => ({ draw: (window as any).__movingCapture.draws.at(-1),
                    bootstrap: (window as any).__movingBootstrap,
                    follower: (window as any).__mirrorController.trajectory.isFollower,
                    timer: (window as any).__mirrorController.trajectory.playbackTimer }));
                near(recovered.draw.center, [10, 0, 0], "recovered trajectory sphere");
                near(recovered.draw.boxEnd, oracle.cells_angstrom[1][0], "recovered box basis");
                near(recovered.draw.annotation.anchor, oracle.coordinates_angstrom[1][0], "recovered annotation anchor");
                const distance = recovered.draw.measurement.geometry.find((item: any) => item.points?.length === 2);
                assert.ok(distance, "the recovered native distance must exist");
                distance.points.forEach((point: number[], index: number) => near(point, oracle.coordinates_angstrom[1][index], "recovered distance endpoint"));
                assert.equal(recovered.draw.regionAtoms, 0);
                assert.equal(recovered.follower, true);
                assert.equal(recovered.timer, undefined);
                assert.ok(recovered.bootstrap.some((item: any) => item.stage === "received-bootstrap" && item.error === "request_timeout"));
                assert.ok(recovered.bootstrap.some((item: any) => item.stage === "received-bootstrap"
                    && item.messages?.some((message: any) => message.op === "add_sphere")));
                const source = await inspect();
                assert.equal(source.same_molsys, true);
                assert.equal(source.coordinates_unchanged, true);
                assert.deepEqual(endpointErrors, []);
                await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, "bootstrap-recovery.json"),
                    JSON.stringify({ recovered, same_molsys: source.same_molsys, coordinates_unchanged: source.coordinates_unchanged }, null, 2));
                console.log("[E2E popup bootstrap] real lost/late reply, visible retry and native frame-1 geometry recovered; v1 production capabilities retained");
                return;
            }
            const endpointSamples = ["popup-state", "popup-session", "detached-state", "detached-session"];
            const samples = phase === "presentation" ? [] : phase === "empty" ? ["empty-state"]
                : phase === "state" ? ["state"] : phase === "popup" ? ["popup-state"]
                : phase === "endpoints" ? endpointSamples : ["state", "session", ...endpointSamples, "empty-state"];
            for (const sample of samples) {
                const kind = sample.endsWith("session") ? "session" : "state", playing = sample !== "empty-state";
                const role = sample.startsWith("detached-") ? "detached" : sample.startsWith("popup-") ? "popup" : "primary";
                if (role !== "primary" && !popup) {
                    const bounds = await page.locator("canvas").boundingBox(); assert.ok(bounds);
                    await page.mouse.move(bounds.x + 12, bounds.y + 12);
                    const opened = page.waitForEvent("popup");
                    await page.getByTitle("Open popup", { exact: true }).click();
                    popup = await opened;
                    popup.on("pageerror", error => endpointErrors.push(String(error)));
                    popup.on("console", consoleObserver);
                    await popup.waitForFunction(() => !!(window as any).__mirrorController);
                    await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
                    await popup.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
                    await popup.evaluate(observeMovingCaptureCanvas);
                    assert.equal(await popup.evaluate(() => (window as any).__mirrorController.trajectory.isFollower), true);
                }
                if (role === "detached" && !panel) {
                    await openMovingWorkFile(popup!);
                    const opened = popup!.waitForEvent("popup");
                    await popup!.getByTitle("Popout panel to external window", { exact: true }).click();
                    panel = await opened;
                    panel.on("pageerror", error => endpointErrors.push(String(error)));
                    await panel.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
                    await panel.locator('[data-molsysviewer-group-panel-tab="export"]').waitFor({ state: "attached" });
                    assert.equal(await panel.locator("canvas").isVisible(), false);
                }
                const canvas = role === "primary" ? page : popup!;
                const owner = role === "detached" ? panel! : canvas;
                const endpointId = await movingEndpointIdentity(canvas), ownerId = await movingEndpointIdentity(owner);
                await command("enable");
                if (!playing) {
                    await closePeers();
                    await command("empty_frame");
                    await page.waitForFunction(() => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame === 1)
                        .catch(async error => {
                            console.log("[E2E empty-frame] authority", JSON.stringify(await inspect()));
                            console.log("[E2E empty-frame] renderer", JSON.stringify(await page.evaluate(() => {
                                const w = window as any, c = w.__mirrorController;
                                return { trajectory: c.trajectory.getTrajectoryState(), pendingFrames: c.trajectory.pendingFrames.size,
                                    dynamicInFlight: c.dynamicRegionEvaluationInFlight, dynamicPending: c.dynamicRegionEvaluationPendingFrame,
                                    frames: w.__movingCapture.frames, commands: w.__movingCapture.commands, errors: w.__popupFixtureErrors };
                            })));
                            throw error;
                        });
                }
                const path = resolve(workspace, `${sample}.${kind === "state" ? "json" : "msv"}`);
                // UI preparation is outside the deliberate dependency stall.
                // Retaining scientific replies while opening/filling Studio
                // can expire unrelated queries before Save is even requested.
                const work = role === "primary" ? undefined : await openMovingWorkFile(owner);
                if (work) {
                    await work.getByLabel("Work file format", { exact: true }).selectOption(kind);
                    await work.getByLabel("Path in Python session", { exact: true }).fill(path);
                }
                const start = await page.evaluate(() => ({ inbound: (window as any).__movingCapture.inbound.length,
                    outbound: (window as any).__movingCapture.outbound.length, frames: (window as any).__movingCapture.frames.length }));
                await page.evaluate(({ playing, outbound, endpointId }) => {
                    const monitor = (window as any).__movingCapture;
                    monitor.heldSource = null;
                    monitor.activeCapture = { playing, outboundStart: outbound, requestSeen: false, frameChanges: 0, endpointId };
                }, { playing, outbound: start.outbound, endpointId });
                let result: any, completion: any;
                if (role === "primary") {
                    await command("hold");
                    await command("save", { path, kind });
                    console.log(`[E2E moving capture] ${sample}: source command acknowledged`);
                    result = await awaitJob(path);
                    completion = result.jobs[path];
                } else {
                    assert.ok(work);
                    const save = work.getByRole("button", { name: "Save file", exact: true });
                    // Arm the deliberate comm stall on the actual click. CDP
                    // actionability can take several draws on a busy canvas;
                    // that delay must not starve queries before Save happens.
                    await save.evaluate(button => {
                        button.addEventListener("click", () => {
                            const host = (window as any).__popupWidgetModel ? window : window.opener;
                            const monitor = host.__movingCapture;
                            monitor.activeCapture.holdArmedAt = host.performance.now();
                            void host.__popupWidgetModel.send({ moving_fixture: "hold" }).catch((error: any) => {
                                monitor.activeCapture.holdError = String(error);
                            });
                        }, { capture: true, once: true });
                    });
                    await save.click();
                    await page.waitForFunction(start => (window as any).__movingCapture.inbound.slice(start)
                        .some((message: any) => message.op === "studio_action_result" && message.action === "save_work_file"), start.inbound);
                    const verdict = await page.evaluate(start => (window as any).__movingCapture.inbound.slice(start)
                        .find((message: any) => message.op === "studio_action_result" && message.action === "save_work_file"), start.inbound);
                    result = await inspect();
                    completion = verdict;
                    assert.equal(result.pending_studio_saves, 0);
                    if (verdict.ok) {
                        assert.equal(verdict.target_endpoint_id, ownerId);
                        const intent = await page.evaluate(id => (window as any).__movingCapture.intents.find((message: any) => message.request_id === id), verdict.request_id);
                        assert.equal(intent._capture_endpoint_id, endpointId);
                        assert.equal(intent._work_file_owner_endpoint_id, ownerId);
                        assert.equal(intent._studio_owner_endpoint_id, ownerId);
                        assert.match(await work.locator('[data-molsysviewer-work-file-status]').innerText(), /Saved/);
                    }
                }
                const diagnostic = await page.evaluate(() => {
                    const m = (window as any).__movingCapture;
                    return { gates: m.gates, captureErrors: m.captureErrors, frames: m.frames, annotationOffsets: m.annotationOffsets,
                        drawCount: m.draws.length, inbound: m.inbound.slice(-12), outbound: m.outbound,
                        readiness: m.readiness, timing: m.timing, activeCapture: m.activeCapture,
                        endpoints: [...m.monitors.entries()].filter(([id, entry]: any) => id === entry.endpointId)
                            .map(([id, entry]: any) => ({ endpointId: id, frames: entry.frames, gates: entry.gates,
                                readiness: entry.readiness, drawCount: entry.draws.length, captureErrors: entry.captureErrors })) };
                });
                await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, `capture-${sample}-timing.json`),
                    JSON.stringify({ source: result.timeline, transport: bridge.getTransportObservation(), renderer: diagnostic }, null, 2));
                if (!completion.ok) {
                    console.log("[E2E moving capture] source error", JSON.stringify(completion));
                    console.log("[E2E moving capture] source timing", JSON.stringify(result.timeline));
                    console.log("[E2E moving capture] transport", JSON.stringify(bridge.getTransportObservation()));
                    console.log("[E2E moving capture] native diagnostic", JSON.stringify(diagnostic));
                }
                assert.equal(completion.ok, true, JSON.stringify(completion));
                assert.ok(diagnostic.activeCapture.requestSeen, "the real version-2 request must reach the receiver");
                assert.ok(diagnostic.activeCapture.released?.heldSource.count > 0, "Python must actually hold the dependent request");
                if (playing) assert.ok(diagnostic.activeCapture.released.frameChanges >= 2,
                    "two native frame changes must occur after the real capture request, while dependent geometry is held");
                assert.equal(diagnostic.activeCapture.released.repliesBeforeRelease, 0, "capture cannot precede dependent geometry");
                assert.equal(diagnostic.activeCapture.releaseError, undefined);
                assert.equal(diagnostic.activeCapture.holdError, undefined);
                const sourceRelease = result.timeline.findLast((entry: any) => entry.name === "release");
                assert.equal(sourceRelease.pending_saves, 1, "source save must still be pending when genuine replies are released");
                assert.equal(result.same_molsys, true);
                assert.equal(result.coordinates_unchanged, true);
                assert.equal(result.authority_state.view.playback.playing, playing);
                const artifact = await command("artifact", { path, kind });
                const saved = artifact.saved_state;
                if (process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR) {
                    // Preserve the original file even if a later native-scene
                    // assertion fails; the workspace still owns its cleanup.
                    await copyFile(path, resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR, basename(path)));
                }
                const observed = await page.evaluate(start => {
                    const monitor = (window as any).__movingCapture;
                    const reply = monitor.outbound.slice(start).find((event: any) => event.ok);
                    const capture = monitor.captures.find((capture: any) => capture.reply.request_id === reply?.request_id);
                    return { reply, draw: capture?.draw,
                        endpointId: monitor.monitors.get(capture?.endpointId)?.endpointId,
                        primaryRequests: monitor.inbound.filter((message: any) => message.op === "request_visual_state"),
                        frames: monitor.frames };
                }, start.outbound);
                assert.ok(observed.draw, "the actual completed-draw geometry must match the real capture reply");
                assert.equal(observed.endpointId, endpointId, "geometry must come from the actual owning canvas");
                assert.equal(observed.reply.request_id, diagnostic.activeCapture.requestId);
                const request = observed.primaryRequests.find((message: any) => message.request_id === observed.reply.request_id);
                assert.equal(request.capture_version, 2);
                if (role !== "primary") {
                    assert.equal(request.target_endpoint_id, endpointId);
                    assert.equal(observed.reply._capture_endpoint_id, endpointId);
                    assert.equal(await canvas.evaluate(() => (window as any).__mirrorController.trajectory.playbackTimer), undefined,
                        "a mirrored canvas must not create a second playback clock");
                }
                const frame = saved.view.structure_index, draw = observed.draw;
                assert.deepEqual(saved.view.camera, draw.snapshot);
                assert.deepEqual(saved.view.playback, draw.playback);
                assert.equal(saved.view.playback.playing, playing);
                if (!playing) assert.equal(frame, 1);
                assert.equal(saved.view.playback.mode, "ping-pong");
                assert.equal(saved.box_display.structure_index, frame);
                near(draw.center, [frame * 10, 0, 0], "trajectory sphere");
                near(draw.boxEnd, oracle.cells_angstrom[frame][0], "box basis");
                near(draw.annotation.anchor, oracle.coordinates_angstrom[frame][0], "annotation anchor");
                const text = draw.annotationPresentation.find((item: any) => item.kind === "text");
                near(text.textCenter, draw.annotation.position, "native transformed text center");
                near(text.cpuCenter, draw.annotation.position, "CPU loci center");
                const geometry = draw.measurement.geometry.find((item: any) => item.points?.length === 2);
                assert.ok(geometry, "the native distance representation must exist");
                geometry.points.forEach((point: number[], index: number) => near(point, oracle.coordinates_angstrom[frame][index], "distance endpoint"));
                assert.equal(draw.regionAtoms, frame === 1 ? 0 : 1);
                assert.deepEqual(artifact.restored_region_atoms, frame === 1 ? [] : [1]);
                assert.ok(draw.interactions.every((index: number) => index === frame));
                assert.equal(artifact.restored_state.view.structure_index, frame);
                if (kind === "state") assert.deepEqual(JSON.parse(await readFile(path, "utf8")), saved);
                assert.deepEqual(endpointErrors, []);
                console.log(`[E2E moving capture] ${sample}: native frame ${frame}, ${saved.view.playback.direction}, all scene dependencies coherent; playing=${playing}`);
            }
            await closePeers();
            if (phase === "all" || phase === "presentation") {
                await command("presentation");
                await checkAnnotationPresentation(page, workspace, command);
            }
        } catch (error) {
            console.error("[E2E moving capture failure]", error);
            try {
                const renderer = await page.evaluate(() => {
                    const m = (window as any).__movingCapture;
                    if (!m) return null;
                    return { active: m.activeCapture, inbound: m.inbound.slice(-16), outbound: m.outbound.slice(-8),
                        intents: m.intents.slice(-8), timing: m.timing, bootstraps: m.bootstraps,
                        endpoints: [...m.monitors.entries()].filter(([id, entry]: any) => id === entry.endpointId)
                            .map(([id, entry]: any) => ({ id, localDocument: entry.localDocument, frames: entry.frames,
                                gates: entry.gates, readiness: entry.readiness, errors: entry.captureErrors, draws: entry.draws.slice(-2) })) };
                });
                const source = await inspectSource?.();
                const popupBootstrap = await popup?.evaluate(() => ({ initial: (window as any).__movingBootstrap,
                    tail: (window as any).__movingBootstrapTail }));
                await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, "capture-failure.json"),
                    JSON.stringify({ error: String(error), renderer, source, popupBootstrap, endpointErrors, endpointWarnings,
                        transport: bridge.getTransportObservation() }, null, 2));
            } catch (diagnosticError) {
                console.error("[E2E moving diagnostic unavailable]", diagnosticError);
            }
            throw error;
        } finally {
            page.off("console", consoleObserver);
            await closePeers();
            await page.evaluate(releaseMovingCaptureObserver).catch(() => {});
            await release?.();
            await bridge.close();
        }
    });
}
