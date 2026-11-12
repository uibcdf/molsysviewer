/** Read-only native observations; no geometry, capture verdict or playback is supplied. */
export function observeMovingPopupBootstrap(runtime: any) {
    const w = window as any;
    const observations: any[] = w.__movingBootstrap = [];
    const tail: any[] = w.__movingBootstrapTail = [];
    const delivery: any[] = w.__movingFrameDelivery = [];
    const frameOps = new Set(["set_trajectory_frame", "set_dynamic_region_atoms", "set_interaction_frame", "interaction_frame_complete"]);
    const observeDelivery = (stage: string, message: any, currentFrame?: number) => {
        if (!frameOps.has(message?.op)) return;
        delivery.push({ ms: window.opener.performance.now(), stage, op: message.op,
            frame: message.index ?? message.frame, request_id: message.request_id, currentFrame });
        if (delivery.length > 1024) delivery.shift();
    };
    const record = (item: any) => {
        const entry = { ms: performance.now(), ...item };
        // Preserve the bootstrap itself; rolling trajectory summaries must not
        // evict the ordering evidence this observer was installed to receive.
        if (observations.length < 128) observations.push(entry);
        tail.push(entry);
        if (tail.length > 24) tail.shift();
    };
    window.addEventListener("message", event => {
        if (event.source !== window.opener) return;
        const envelope = event.data?.envelope;
        if (envelope?.action === "molsysviewer-sync-op") observeDelivery("received", envelope.payload);
        if (envelope?.action === "molsysviewer-initial-sync") record({ stage: "received-bootstrap",
            error: envelope.payload?.bootstrapError,
            messages: envelope.payload?.messages?.map((message: any) => ({ op: message.op, tag: message.tag ?? message.options?.tag })) });
    });
    for (const method of ["handleMessage", "loadArrayNativeMolSysPayload"]) {
        const original = runtime.MolSysViewerController.prototype[method];
        runtime.MolSysViewerController.prototype[method] = async function(...args: any[]) {
            const op = method === "handleMessage" ? args[0]?.op : method;
            if (method === "handleMessage") observeDelivery("before", args[0], this.trajectory.getTrajectoryState().currentFrame);
            const sample = (stage: string, error?: unknown) => record({ stage, op,
                tag: args[0]?.tag ?? args[0]?.options?.tag,
                frame: this.trajectory.getTrajectoryState().currentFrame,
                tags: [...this.state.tagIndex.keys()], error: error === undefined ? undefined : String(error) });
            sample("before");
            try {
                const result = await original.apply(this, args);
                if (method === "handleMessage") observeDelivery("after", args[0], this.trajectory.getTrajectoryState().currentFrame);
                sample("after");
                return result;
            } catch (error) { sample("failed", error); throw error; }
        };
    }
    const prepare = runtime.MolSysViewerController.prototype.prepareMovingVisualCapture;
    runtime.MolSysViewerController.prototype.prepareMovingVisualCapture = function(...args: any[]) {
        const active = window.opener?.__movingCapture?.activeCapture;
        if (active?.endpointId === w.molsysviewer_popup_channel?.popupEndpointId) {
            active.startedAt = window.opener.performance.now();
            active.startFrame = this.trajectory.getTrajectoryState().currentFrame;
        }
        return prepare.apply(this, args);
    };
}

export function observeMovingCaptureCanvas() {
    const w = window as any, c = w.__mirrorController;
    const endpointId = w.molsysviewer_popup_channel?.popupEndpointId ?? "primary";
    const authority = endpointId === "primary" ? w.__movingCapture : window.opener?.__movingCapture;
    if (!authority) throw new Error("Moving capture observations require their real authority.");
    const monitor = w.__movingCapture ??= { inbound: [], commands: [], outbound: [], captures: [], draws: [], frames: [],
        gates: {}, captureErrors: [], annotationOffsets: [], readiness: [], timing: [], activeCapture: null, heldSource: null };
    monitor.endpointId = endpointId;
    monitor.frameDelivery = w.__movingFrameDelivery;
    monitor.localDocument = c.plugin.canvas3dContext.canvas.ownerDocument.defaultView === window;
    if (!monitor.localDocument) throw new Error("Capture observer must inspect its own native canvas.");
    const stages: any[] = monitor.stages = [];
    const clock = () => endpointId === "primary" || !window.opener || window.opener.closed
        ? performance.now() : window.opener.performance.now();
    const recordStage = (item: any) => {
        stages.push(item);
        if (stages.length > 1024) stages.shift();
    };
    const restore: (() => void)[] = [];
    let sequence = 0;
    const observe = (owner: any, key: string, name: string) => {
        const original = owner[key];
        const wrapped = function(this: any, ...args: any[]) {
            const id = ++sequence, started = clock();
            const detail = name === "task" ? args[0]?.name : name === "message"
                ? { op: args[0]?.op, frame: args[0]?.frame ?? args[0]?.index, request_id: args[0]?.request_id }
                : args[0]?.frame ?? args[0]?.index;
            recordStage({ id, name, detail, stage: "start", ms: started });
            const finish = (error = false) => { const ended = clock();
                let settled: any;
                if (["model", "dynamic", "interactions", "message"].includes(name)) {
                    try {
                        const frame = c.trajectory.getTrajectoryState().currentFrame;
                        settled = { frame, coherent: !!c.readMovingVisualState(),
                            dynamic: { applied: c.dynamicRegionEvaluationAppliedFrame,
                                inFlight: c.dynamicRegionEvaluationInFlight, pending: c.dynamicRegionEvaluationPendingFrame },
                            interactions: { frame: c.interactions.frame, pending: c.interactions.pending, work: c.interactions.pendingWork },
                            updating: c.plugin.state.data.behaviors.isUpdating.value };
                    } catch (failure: any) { settled = { error: failure?.name ?? "UnknownError" }; }
                }
                recordStage({ id, name, detail, stage: "end", ms: ended, duration: ended - started, error,
                    ...(settled ? { settled } : {}) }); };
            try {
                const result = original.apply(this, args);
                if (result?.then) result.then(() => finish(), () => finish(true));
                else finish();
                return result;
            } catch (error) { finish(true); throw error; }
        };
        owner[key] = wrapped;
        restore.push(() => { if (owner[key] === wrapped) owner[key] = original; });
    };
    observe(c.plugin, "runTask", "task");
    observe(c, "handleMessage", "message");
    observe(c.trajectory, "applyTrajectoryFrame", "model");
    observe(c.annotations, "refresh", "annotations");
    observe(c.state, "setDynamicRegionAtoms", "dynamic");
    observe(c.interactions, "apply", "interactions");
    const offset = clock() - performance.now();
    const longTasks = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) recordStage({ name: "longtask", ms: entry.startTime + offset,
            duration: entry.duration });
    });
    longTasks.observe({ entryTypes: ["longtask"] });
    monitor.releaseInstrumentation = () => { longTasks.disconnect(); for (const release of restore) release(); };
    authority.monitors ??= new Map();
    authority.monitors.set(endpointId, monitor);
    const hostAlias = endpointId === "primary" ? `widget-host:${w.__popupWidgetModel.get("runtime_session_id")}` : undefined;
    if (hostAlias) authority.monitors.set(hostAlias, monitor);
    const incoming = (event: MessageEvent) => {
        if (event.source !== window.opener || event.data?.envelope?.action !== "molsysviewer-sync-op") return;
        const message = event.data.envelope.payload;
        if (message?.op !== "request_visual_state" || message.capture_version !== 2
            || message.target_endpoint_id !== endpointId) return;
        const active = authority.activeCapture;
        if (!active || active.endpointId !== endpointId) return;
        active.requestSeen = true; active.requestId = message.request_id;
        active.receivedAt = window.opener.performance.now();
        active.lastFrame = c.trajectory.getTrajectoryState().currentFrame;
        authority.releaseHeldWhenObserved?.();
    };
    if (endpointId !== "primary") window.addEventListener("message", incoming);
    monitor.releaseMessages = () => {
        window.removeEventListener("message", incoming);
        authority.monitors.delete(endpointId);
        if (hostAlias) authority.monitors.delete(hostAlias);
    };
    monitor.releaseFrames = c.onTrajectoryState((state: any) => {
        if (monitor.frames.at(-1) !== state.currentFrame) monitor.frames.push(state.currentFrame);
        if (monitor.frames.length > 256) monitor.frames.shift();
        const active = authority.activeCapture;
        if (active?.requestSeen && active.endpointId === monitor.endpointId && active.lastFrame !== state.currentFrame) {
            active.lastFrame = state.currentFrame; active.frameChanges++;
            active.changes ??= [];
            active.changes.push({ ms: endpointId === "primary" ? performance.now() : window.opener.performance.now(), frame: state.currentFrame });
            authority.releaseHeldWhenObserved?.();
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
        const now = endpointId === "primary" ? performance.now() : window.opener.performance.now();
        const active = authority.activeCapture;
        if (ready && active?.endpointId === endpointId && active.startedAt !== undefined) active.firstCoherentDrawAt ??= now;
        monitor.readiness.push({ ms: now, frame, gates,
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
        monitor.draws.push(w.Harness.inspectMovingCaptureDraw(c));
        if (monitor.draws.length > 512) monitor.draws.shift();
    });
    replay = false;
}

export function releaseMovingCaptureObserver() {
    const monitor = (window as any).__movingCapture;
    monitor?.subscription?.unsubscribe();
    monitor?.releaseFrames?.();
    monitor?.releaseMessages?.();
    monitor?.releaseInstrumentation?.();
}
