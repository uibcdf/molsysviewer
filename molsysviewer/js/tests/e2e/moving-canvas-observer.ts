/** Read-only native observations; no geometry, capture verdict or playback is supplied. */
export function observeMovingPopupBootstrap(runtime: any) {
    const w = window as any;
    const observations: any[] = w.__movingBootstrap = [];
    const tail: any[] = w.__movingBootstrapTail = [];
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
        if (envelope?.action === "molsysviewer-initial-sync") record({ stage: "received-bootstrap",
            error: envelope.payload?.bootstrapError,
            messages: envelope.payload?.messages?.map((message: any) => ({ op: message.op, tag: message.tag ?? message.options?.tag })) });
    });
    for (const method of ["handleMessage", "loadArrayNativeMolSysPayload"]) {
        const original = runtime.MolSysViewerController.prototype[method];
        runtime.MolSysViewerController.prototype[method] = async function(...args: any[]) {
            const op = method === "handleMessage" ? args[0]?.op : method;
            const sample = (stage: string, error?: unknown) => record({ stage, op,
                tag: args[0]?.tag ?? args[0]?.options?.tag,
                frame: this.trajectory.getTrajectoryState().currentFrame,
                tags: [...this.state.tagIndex.keys()], error: error === undefined ? undefined : String(error) });
            sample("before");
            try {
                const result = await original.apply(this, args);
                sample("after");
                return result;
            } catch (error) { sample("failed", error); throw error; }
        };
    }
}

export function observeMovingCaptureCanvas() {
    const w = window as any, c = w.__mirrorController;
    const endpointId = w.molsysviewer_popup_channel?.popupEndpointId ?? "primary";
    const authority = endpointId === "primary" ? w.__movingCapture : window.opener?.__movingCapture;
    if (!authority) throw new Error("Moving capture observations require their real authority.");
    const monitor = w.__movingCapture ??= { inbound: [], commands: [], outbound: [], captures: [], draws: [], frames: [],
        gates: {}, captureErrors: [], annotationOffsets: [], readiness: [], timing: [], activeCapture: null, heldSource: null };
    monitor.endpointId = endpointId;
    monitor.localDocument = c.plugin.canvas3dContext.canvas.ownerDocument.defaultView === window;
    if (!monitor.localDocument) throw new Error("Capture observer must inspect its own native canvas.");
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
}

export function releaseMovingCaptureObserver() {
    const monitor = (window as any).__movingCapture;
    monitor?.subscription?.unsubscribe();
    monitor?.releaseFrames?.();
    monitor?.releaseMessages?.();
}
