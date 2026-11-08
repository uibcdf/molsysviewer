import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";
import { checkAnnotationPresentation } from "./annotation-presentation-scenarios";

/** Exercise the unadvertised v2 receiver against a genuinely moving authority. */
export async function checkMovingCapture(page: Page, dir: string,
    phase: "all" | "empty" | "presentation" | "state" = "all") {
    await withFixtureWorkspace("moving-capture", async workspace => {
        const bridge = new PythonFixtureBridge(resolve(dir, "moving-capture-bridge.py"), resolve(dir, "../../../.."),
            90000, { env: fixtureEnvironment(workspace), observeTransport: true });
        let release: (() => Promise<void>) | undefined;
        try {
            release = await mountCanvasPopupFixture(page, bridge);
            await captureCanvasPopupControllers(page);
            await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
            console.log("[E2E moving capture] real widget and annotation inspector ready");
            await page.evaluate(() => {
                const w = window as any, c = w.__mirrorController, model = w.__popupWidgetModel;
                const monitor = w.__movingCapture = { inbound: [], commands: [], outbound: [], captures: [], draws: [], frames: [], gates: {},
                    captureErrors: [], annotationOffsets: [], readiness: [], timing: [], activeCapture: null as any, heldSource: null as any };
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
                const send = model.send.bind(model);
                model.send = (message: any) => {
                    const payload = message.payload ?? message;
                    if (payload.moving_fixture || ["request_dynamic_region_evaluation", "visual_state_snapshot"].includes(payload.event)) {
                        monitor.timing.push({ ms: performance.now(), stage: "send", name: payload.moving_fixture ?? payload.event, frame: payload.frame });
                        if (monitor.timing.length > 128) monitor.timing.shift();
                    }
                    if (payload.event === "visual_state_snapshot") {
                        monitor.outbound.push(structuredClone(payload));
                        if (payload.ok) monitor.captures.push({ reply: structuredClone(payload),
                            draw: monitor.draws.findLast((draw: any) => draw.structure_index === payload.structure_index
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
                    monitor.commands.push({ ms: performance.now(), op: payload.op, index: payload.index, frame: payload.frame, action: payload.action });
                    if (monitor.commands.length > 128) monitor.commands.shift();
                    if (["request_visual_state", "set_dynamic_region_atoms", "cancel_visual_state"].includes(payload.op)) {
                        monitor.inbound.push(structuredClone(payload));
                    }
                    if (payload.op === "request_visual_state" && payload.capture_version === 2 && monitor.activeCapture) {
                        const active = monitor.activeCapture;
                        active.requestSeen = true; active.requestId = payload.request_id;
                        active.lastFrame = c.trajectory.getTrajectoryState().currentFrame;
                        releaseHeldWhenObserved();
                    }
                });
                monitor.releaseFrames = c.onTrajectoryState((state: any) => {
                    if (monitor.frames.at(-1) !== state.currentFrame) monitor.frames.push(state.currentFrame);
                    if (monitor.frames.length > 256) monitor.frames.shift();
                    const active = monitor.activeCapture;
                    if (active?.requestSeen && active.lastFrame !== state.currentFrame) {
                        active.lastFrame = state.currentFrame; active.frameChanges++;
                        releaseHeldWhenObserved();
                    }
                });
                let replay = true;
                monitor.subscription = c.plugin.canvas3d.didDraw.subscribe(() => {
                    if (replay) return;
                    let ready;
                    try { ready = c.readMovingVisualState(); } catch (error: any) {
                        if (monitor.captureErrors.length < 5) monitor.captureErrors.push(error.name); return;
                    }
                    const frame = c.trajectory.getTrajectoryState().currentFrame;
                    const gates = { stateUpdating: !c.plugin.state.data.behaviors.isUpdating.value,
                        trajectory: c.trajectory.isCaptureFrameReady(frame), box: c.boxDisplay.isFrameReady(frame),
                        shapes: c.shapes.isFrameReady(frame), interactions: c.interactions.isFrameReady(frame),
                        annotations: c.annotations.isGeometryCurrent(), movie: c.movie.isCaptureSafe,
                        dynamic: !c.state.hasFrameDependentDynamicRegions() || (c.dynamicRegionEvaluationInFlight === null
                            && c.dynamicRegionEvaluationPendingFrame === null && c.dynamicRegionEvaluationAppliedFrame === frame) };
                    for (const [name, passed] of Object.entries(gates)) if (!passed) monitor.gates[name] = (monitor.gates[name] ?? 0) + 1;
                    monitor.readiness.push({ ms: performance.now(), frame, gates,
                        dynamic: { applied: c.dynamicRegionEvaluationAppliedFrame, inFlight: c.dynamicRegionEvaluationInFlight,
                            pending: c.dynamicRegionEvaluationPendingFrame },
                        interactions: { frame: c.interactions.frame, pending: c.interactions.pending, work: c.interactions.pendingWork,
                            summaries: c.interactions.summaries.map((item: any) => ({ tag: item.tag, frame: item.frame, status: item.status })) } });
                    if (monitor.readiness.length > 64) monitor.readiness.shift();
                    if (!gates.annotations) {
                        const refs = c.state.tagIndex.get("annotation\u0000moving-note") ?? new Set();
                        const repr = [...refs].map((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr).find(Boolean);
                        const data = repr?.getAllLoci().find((loci: any) => loci.shape)?.shape.sourceData;
                        if (data?.anchor && data?.position) {
                            const camera = c.getCameraSnapshot();
                            const norm = (v: number[]) => { const n = Math.hypot(...v); return v.map(x => x / n); };
                            const cross = (a: number[], b: number[]) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
                            const toward = norm(camera.position.map((v: number, i: number) => v - camera.target[i]));
                            const right = norm(cross(camera.up, toward)), up = norm(cross(toward, right));
                            const expected = data.anchor.map((v: number, i: number) => v + 6*right[i] + 8*up[i] + 5*toward[i]);
                            monitor.annotationOffsets.push({ frame, actual: [...data.position], expected,
                                maxError: Math.max(...expected.map((v: number, i: number) => Math.abs(v-data.position[i]))) });
                            if (monitor.annotationOffsets.length > 4) monitor.annotationOffsets.shift();
                        }
                    }
                    if (!ready) return;
                    const shapes = (kind: string, tag: string) => {
                        const refs = c.state.tagIndex.get(`${kind}\u0000${tag}`) ?? new Set();
                        return [...refs].flatMap((ref: any) => c.plugin.state.data.cells.get(ref)?.obj?.data?.repr?.getAllLoci?.()
                            .filter((loci: any) => loci.shape).map((loci: any) => loci.shape) ?? []);
                    };
                    const sphere = shapes("shape", "moving-marker").find((shape: any) => shape.geometry.kind === "mesh");
                    let center;
                    if (sphere) {
                        const geometry = sphere.geometry, low = [Infinity, Infinity, Infinity], high = [-Infinity, -Infinity, -Infinity];
                        for (let vertex = 0; vertex < geometry.vertexCount; vertex++) for (let axis = 0; axis < 3; axis++) {
                            const value = geometry.vertexBuffer.ref.value[3 * vertex + axis];
                            low[axis] = Math.min(low[axis], value); high[axis] = Math.max(high[axis], value);
                        }
                        center = low.map((value, axis) => (value + high[axis]) / 2);
                    }
                    const box = shapes("shape", "__msv_box").find((shape: any) => shape.geometry.kind === "mesh");
                    const annotation = shapes("annotation", "moving-note")[0];
                    const interactions = shapes("interaction", "moving-hbonds").map((shape: any) => shape.sourceData.interaction?.frame);
                    const region = c.state.regionIndex.get("moving-near");
                    const componentRef = typeof region?.component === "string" ? region.component : region?.component?.ref;
                    const regionAtoms = componentRef ? c.plugin.state.data.cells.get(componentRef)?.obj?.data?.elementCount ?? 0 : 0;
                    monitor.draws.push({ ...ready, center, boxEnd: box?.sourceData.links[0].end,
                        annotation: annotation ? { anchor: [...annotation.sourceData.anchor], position: [...annotation.sourceData.position] } : null,
                        annotationPresentation: w.Harness.inspectAnnotationPresentation(c, "moving-note"),
                        measurement: w.Harness.inspectMeasurementGeometry(c, "moving-distance"), regionAtoms, interactions });
                    if (monitor.draws.length > 512) monitor.draws.shift();
                });
                replay = false;
            });
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
            const awaitJob = async (path: string) => {
                for (let count = 0; count < 160; count++) {
                    const result = await inspect();
                    if (result.jobs[path]?.done) return result;
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error("Moving save did not complete its bounded source request");
            };
            await command("enable");
            await command("play");
            await page.waitForFunction(() => (window as any).__movingCapture.frames.length >= 3);
            console.log("[E2E moving capture] uninterrupted camera and trajectory observed");
            const oracle = await inspect();
            const near = (point: number[], expected: number[], label: string) => {
                assert.equal(point?.length, expected.length, label);
                point.forEach((value, index) => assert.ok(Math.abs(value - expected[index]) < 2e-4,
                    `${label}: ${JSON.stringify(point)} != ${JSON.stringify(expected)}`));
            };
            const samples = phase === "presentation" ? [] : phase === "empty" ? ["empty-state"]
                : phase === "state" ? ["state"] : ["state", "session", "empty-state"];
            for (const sample of samples) {
                const kind = sample === "session" ? "session" : "state", playing = sample !== "empty-state";
                if (!playing) {
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
                const start = await page.evaluate(() => ({ inbound: (window as any).__movingCapture.inbound.length,
                    outbound: (window as any).__movingCapture.outbound.length, frames: (window as any).__movingCapture.frames.length }));
                await page.evaluate(({ playing, outbound }) => {
                    const monitor = (window as any).__movingCapture;
                    monitor.heldSource = null;
                    monitor.activeCapture = { playing, outboundStart: outbound, requestSeen: false, frameChanges: 0 };
                }, { playing, outbound: start.outbound });
                await command("hold");
                console.log(`[E2E moving capture] ${sample}: hold acknowledged; submitting public async save`);
                await command("save", { path, kind });
                console.log(`[E2E moving capture] ${sample}: source command acknowledged`);
                const result = await awaitJob(path);
                const diagnostic = await page.evaluate(() => {
                    const m = (window as any).__movingCapture;
                    return { gates: m.gates, captureErrors: m.captureErrors, frames: m.frames, annotationOffsets: m.annotationOffsets,
                        drawCount: m.draws.length, inbound: m.inbound.slice(-12), outbound: m.outbound,
                        readiness: m.readiness, timing: m.timing, activeCapture: m.activeCapture };
                });
                await writeFile(resolve(process.env.E2E_MOVING_CAPTURE_ARTIFACT_DIR ?? workspace, `capture-${sample}-timing.json`),
                    JSON.stringify({ source: result.timeline, transport: bridge.getTransportObservation(), renderer: diagnostic }, null, 2));
                if (!result.jobs[path].ok) {
                    console.log("[E2E moving capture] source error", JSON.stringify(result.jobs[path]));
                    console.log("[E2E moving capture] source timing", JSON.stringify(result.timeline));
                    console.log("[E2E moving capture] transport", JSON.stringify(bridge.getTransportObservation()));
                    console.log("[E2E moving capture] native diagnostic", JSON.stringify(diagnostic));
                }
                assert.equal(result.jobs[path].ok, true, JSON.stringify(result.jobs[path]));
                assert.ok(diagnostic.activeCapture.requestSeen, "the real version-2 request must reach the receiver");
                assert.ok(diagnostic.activeCapture.released?.heldSource.count > 0, "Python must actually hold the dependent request");
                if (playing) assert.ok(diagnostic.activeCapture.released.frameChanges >= 2,
                    "two native frame changes must occur after the real capture request, while dependent geometry is held");
                assert.equal(diagnostic.activeCapture.released.repliesBeforeRelease, 0, "capture cannot precede dependent geometry");
                assert.equal(diagnostic.activeCapture.releaseError, undefined);
                const sourceRelease = result.timeline.findLast((entry: any) => entry.name === "release");
                assert.equal(sourceRelease.pending_saves, 1, "source save must still be pending when genuine replies are released");
                assert.equal(result.same_molsys, true);
                assert.equal(result.coordinates_unchanged, true);
                assert.equal(result.authority_state.view.playback.playing, playing);
                const artifact = await command("artifact", { path, kind });
                const saved = artifact.saved_state;
                const observed = await page.evaluate(start => {
                    const monitor = (window as any).__movingCapture;
                    const reply = monitor.outbound.slice(start).find((event: any) => event.ok);
                    return { reply, draw: monitor.captures.find((capture: any) => capture.reply.request_id === reply?.request_id)?.draw,
                        frames: monitor.frames };
                }, start.outbound);
                assert.ok(observed.draw, "the actual completed-draw geometry must match the real capture reply");
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
                console.log(`[E2E moving capture] ${sample}: native frame ${frame}, ${saved.view.playback.direction}, all scene dependencies coherent; playing=${playing}`);
            }
            if (phase !== "empty" && phase !== "state") {
                await command("presentation");
                await checkAnnotationPresentation(page, workspace, command);
            }
        } finally {
            await page.evaluate(() => {
                const monitor = (window as any).__movingCapture;
                monitor?.subscription?.unsubscribe(); monitor?.releaseFrames?.();
            }).catch(() => {});
            await release?.();
            await bridge.close();
        }
    });
}
