// Native message callback hold used only by actual-renderer camera receiving.
export function installCameraPacketHold() {
    const w = window as any;
    const add = window.addEventListener.bind(window), remove = window.removeEventListener.bind(window);
    const listeners = new Map<any, Map<boolean, any>>(), all = new Set<any>(), held: any[] = [];
    const captureOf = (options: any) => typeof options === "boolean" ? options : !!options?.capture;
    const forget = (record: any) => {
        const captures = listeners.get(record.listener);
        if (captures?.get(record.capture) === record) {
            captures.delete(record.capture);
            if (!captures.size) listeners.delete(record.listener);
        }
    };
    const deactivate = (record: any) => {
        record.active = false;
        forget(record);
        record.signal?.removeEventListener("abort", record.abort);
        all.delete(record);
    };
    const invoke = (record: any, event: MessageEvent, target: any) => {
        if (!record.active) return false;
        if (record.once) deactivate(record);
        if (typeof record.listener === "function") record.listener.call(target, event);
        else record.listener.handleEvent.call(record.listener, event);
        return true;
    };
    const retain = (event: MessageEvent) => {
        const preflight = w.__staleTransportPreflight;
        let p: any;
        if (preflight?.armed && event.source === window && event.data?.privateTransportPreflight === preflight.id) p = preflight;
        else {
            p = w.__staleCameraProbe;
            const wire = event.data, envelope = wire?.envelope;
            if (!p?.armed || event.source !== window.opener || envelope?.action !== "molsysviewer-sync-camera"
                || wire.channel?.popupEndpointId !== w.molsysviewer_popup_channel.popupEndpointId) return false;
            if (p.held && p.held !== event) return false;
            const same = ["position", "target", "up"].every(key => (envelope.payload.snapshot ?? envelope.payload)?.[key]?.every((value: number, index: number) => Math.abs(value - p.saved[key][index]) < 1e-5));
            if (!p.held && same) return false;
        }
        if (!p.held) {
            p.held = event;
            if (w.__staleCameraProbe === p) {
                p.heldEnvelopeJson = JSON.stringify(event.data.envelope);
                const c = w.__mirrorController;
                p.observations.push({ at: performance.timeOrigin + performance.now(), phase: "held-real-sync-event",
                    data: { envelope: structuredClone(event.data.envelope) }, camera: c.getCameraSnapshot(),
                    trajectory: c.trajectory.getTrajectoryState(), transition: c.plugin.canvas3d.camera.transition.inTransition });
            }
        }
        p.heldCallbackCount = (p.heldCallbackCount ?? 0) + 1;
        return true;
    };
    window.addEventListener = ((type: any, listener: any, options?: any) => {
        if (type !== "message" || !listener) return add(type, listener, options);
        const capture = captureOf(options), existing = listeners.get(listener)?.get(capture);
        if (existing) return add(type, existing.wrapper, options);
        if (options?.signal?.aborted) return add(type, listener, options);
        const record: any = { listener, capture, once: !!options?.once, signal: options?.signal, active: true,
            options: { capture, once: !!options?.once, passive: !!options?.passive, signal: options?.signal } };
        record.wrapper = function(this: any, event: MessageEvent) {
            // The browser itself consumes `once` at native delivery. Remove
            // its identity now so re-registration retains native behavior.
            if (record.once) { record.nativeOnceConsumed = true; forget(record); }
            if (retain(event)) held.push({ record, event, target: this });
            else invoke(record, event, this);
        };
        record.abort = () => deactivate(record);
        let captures = listeners.get(listener);
        if (!captures) { captures = new Map(); listeners.set(listener, captures); }
        captures.set(capture, record);
        all.add(record);
        try { add(type, record.wrapper, options); record.signal?.addEventListener("abort", record.abort, { once: true }); }
        catch (error) { deactivate(record); throw error; }
    }) as typeof window.addEventListener;
    window.removeEventListener = ((type: any, listener: any, options?: any) => {
        const record = type === "message" ? listeners.get(listener)?.get(captureOf(options)) : undefined;
        if (record) { deactivate(record); return remove(type, record.wrapper, options); }
        return remove(type, listener, options);
    }) as typeof window.removeEventListener;
    w.__staleFlushOriginalCallbacks = () => {
        let delivered = 0;
        const pending = held.splice(0);
        for (const entry of pending) if (invoke(entry.record, entry.event, entry.target)) delivered++;
        return { deferred: pending.length, delivered };
    };
    w.__staleReleaseMessageHooks = () => {
        // Instrumentation owns wrappers, not the application's registrations.
        // Restore active callbacks in their original order and with the native
        // options; otherwise the next real Studio action loses its transport.
        for (const record of [...all]) {
            remove("message", record.wrapper, record.capture);
            const restore = record.active && !record.nativeOnceConsumed && !record.signal?.aborted;
            deactivate(record);
            if (restore) add("message", record.listener, record.options);
        }
        held.length = 0;
        window.addEventListener = add;
        window.removeEventListener = remove;
    };
}
