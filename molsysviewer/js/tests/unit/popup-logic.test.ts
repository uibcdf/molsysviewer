import assert from "node:assert";
import test from "node:test";

import { bootPopup } from "../../src/popup/popup-logic";
import type { PopupChannelIdentity } from "../../src/messages/popup-channel";

const TEST_CHANNEL: PopupChannelIdentity = {
    protocolVersion: 1,
    viewerId: "view-a",
    sessionId: "session-a",
    authorityEndpointId: "python:view-a",
    hostEndpointId: "host-a",
    popupEndpointId: "canvas-popup-a",
    token: "unguessable-test-token",
    mode: "canvas",
};

let hostMessageCounter = 0;

function hostWire(action: string, payload: unknown) {
    return {
        channel: TEST_CHANNEL,
        envelope: {
            protocolVersion: 1,
            viewerId: TEST_CHANNEL.viewerId,
            sessionId: TEST_CHANNEL.sessionId,
            endpointId: TEST_CHANNEL.authorityEndpointId,
            targetEndpointId: TEST_CHANNEL.popupEndpointId,
            messageId: `host-test:${++hostMessageCounter}`,
            // Mirror the host: camera sync is an ephemeral event, everything
            // else a projection (see PopupHostManager.postToPopup).
            direction: action === "molsysviewer-sync-camera" ? "event" : "projection",
            action,
            payload,
        },
    };
}

type Listener = (event?: any) => any;

function makeElement(id?: string) {
    const listeners = new Map<string, Listener[]>();
    const element: any = {
        id,
        style: {
            setProperty(_name: string, _value: string) {},
        },
        children: [] as any[],
        textContent: "",
        className: "",
        type: "",
        value: "0",
        min: "0",
        max: "0",
        disabled: false,
        title: "",
        appendChild(child: any) {
            this.children.push(child);
        },
        addEventListener(type: string, listener: Listener) {
            const current = listeners.get(type) ?? [];
            current.push(listener);
            listeners.set(type, current);
        },
        removeEventListener(type: string, listener: Listener) {
            const current = listeners.get(type) ?? [];
            listeners.set(type, current.filter(item => item !== listener));
        },
        dispatch(type: string, event: any = {}) {
            for (const listener of listeners.get(type) ?? []) {
                listener(event);
            }
        },
        listenerCount(type: string) {
            return (listeners.get(type) ?? []).length;
        },
        remove() {},
    };
    return element;
}

function makePopupTestEnv() {
    const container = makeElement("molsysviewer-pop");
    const loading = makeElement("molsysviewer-loading");
    const head = makeElement("head");
    const body = makeElement("body");
    const documentListeners = new Map<string, Listener[]>();
    const windowListeners = new Map<string, Listener[]>();
    const postedToHost: any[] = [];

    const document: any = {
        head,
        body,
        createElement(_tag: string) {
            return makeElement();
        },
        getElementById(id: string) {
            if (id === "molsysviewer-pop") return container;
            if (id === "molsysviewer-loading") return loading;
            if (id === "molsysviewer-pop-slider-style") return null;
            return null;
        },
        addEventListener(type: string, listener: Listener) {
            const current = documentListeners.get(type) ?? [];
            current.push(listener);
            documentListeners.set(type, current);
        },
    };

    const opener = {
        closed: false,
        postMessage(message: any, _target: string) {
            postedToHost.push(message);
        },
    };

    const windowObj: any = {
        opener,
        location: { origin: "https://notebook.example.dev" },
        molsysviewer_popup_channel: TEST_CHANNEL,
        listeners: windowListeners,
        addEventListener(type: string, listener: Listener) {
            const current = windowListeners.get(type) ?? [];
            current.push(listener);
            windowListeners.set(type, current);
        },
        removeEventListener(type: string, listener: Listener) {
            const current = windowListeners.get(type) ?? [];
            windowListeners.set(type, current.filter(item => item !== listener));
        },
        dispatch(type: string, event: any = {}) {
            for (const listener of windowListeners.get(type) ?? []) {
                listener(event);
            }
        },
        setTimeout(fn: () => void, _ms?: number) {
            fn();
            return 1;
        },
        clearTimeout(_id: number) {},
        close() {},
    };

    return { container, loading, head, body, document, windowObj, postedToHost };
}

function flushAsync() {
    return new Promise(resolve => setImmediate(resolve));
}

// Rendering is exercised by the real exported-page/popup browser guard.
// These tests isolate the authenticated protocol and shared UI model projection.
function popupModule(ctrl: any) {
    return {
        MolSysViewerController: { create: async () => ctrl },
        mountControls(_controller: any, model: any, sendSync: any) {
            ctrl.controlsModel = model;
            ctrl.sendControlsSync = sendSync;
        },
    };
}

test("bootPopup replays initial sync and projects controls preferences", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const previousSetTimeout = (globalThis as any).setTimeout;
    const previousClearTimeout = (globalThis as any).clearTimeout;
    const env = makePopupTestEnv();
    const calls = {
        handled: [] as any[],
        camera: [] as any[],
        spin: [] as any[],
        swing: [] as any[],
        bg: [] as any[],
        reset: [] as any[],
    };
    let drawSubscriber: (() => void) | undefined;

    const ctrl: any = {
        plugin: {
            canvas3d: {
                didDraw: {
                    subscribe(fn: () => void) {
                        drawSubscriber = fn;
                    },
                },
            },
        },
        trajectory: {
            getTrajectoryState() {
                return { hasTrajectory: false, frameCount: 0, currentFrame: 0, isPlaying: false };
            },
        },
        async handleMessage(msg: any) {
            calls.handled.push(msg);
        },
        setCameraSnapshot(snapshot: any, duration: number) {
            calls.camera.push({ snapshot, duration });
        },
        async toggleSpin(enable?: boolean) {
            calls.spin.push(enable);
        },
        async toggleSwing(enable?: boolean) {
            calls.swing.push(enable);
        },
        async toggleBackground(mode?: string) {
            calls.bg.push(mode);
        },
        getCameraSnapshot() {
            return { position: [1, 2, 3] };
        },
        onTrajectoryState(_cb: any, _opts: any) {},
        async resetView() { calls.reset.push(true); },
        toggleFullscreen() {},
        stepTrajectory(_by: number) {},
        stopTrajectoryPlayback() {},
        playTrajectory(_opts: any) {},
        setTrajectoryFrame(_index: number) {},
        isSpinActive: false,
        isSwingActive: false,
        isDarkMode: false,
    };

    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    (globalThis as any).setTimeout = (fn: () => void, _ms?: number) => {
        fn();
        return 1;
    };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup(popupModule(ctrl));
        await flushAsync();

        assert.deepStrictEqual(env.postedToHost[0].channel, TEST_CHANNEL);
        assert.deepStrictEqual(env.postedToHost[0].envelope, {
            protocolVersion: 1,
            viewerId: TEST_CHANNEL.viewerId,
            sessionId: TEST_CHANNEL.sessionId,
            endpointId: TEST_CHANNEL.popupEndpointId,
            targetEndpointId: TEST_CHANNEL.hostEndpointId,
            messageId: `${TEST_CHANNEL.popupEndpointId}:1`,
            direction: "event",
            action: "molsysviewer-pop-ready",
            payload: null,
        });
        assert.ok(drawSubscriber);

        env.windowObj.dispatch("message", {
            source: {},
            data: hostWire(
                "molsysviewer-sync-op",
                { op: "hide_whole", target: "whole" },
            ),
        });
        const forgedToken = hostWire(
            "molsysviewer-sync-op",
            { op: "hide_whole", target: "whole" },
        );
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: {
                ...forgedToken,
                channel: { ...TEST_CHANNEL, token: "forged" },
            },
        });
        const impersonatedPopup = hostWire(
            "molsysviewer-sync-op",
            { op: "hide_whole", target: "whole" },
        );
        impersonatedPopup.envelope.endpointId = TEST_CHANNEL.popupEndpointId;
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: impersonatedPopup,
        });
        await flushAsync();
        assert.deepStrictEqual(calls.handled, []);

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-not-declared", { ignored: true }),
        });
        await flushAsync();
        assert.deepStrictEqual(
            env.postedToHost.at(-1)?.envelope,
            {
                protocolVersion: 1,
                viewerId: TEST_CHANNEL.viewerId,
                sessionId: TEST_CHANNEL.sessionId,
                endpointId: TEST_CHANNEL.popupEndpointId,
                targetEndpointId: TEST_CHANNEL.hostEndpointId,
                messageId: `${TEST_CHANNEL.popupEndpointId}:2`,
                direction: "event",
                action: "molsysviewer-runtime-contract-rejected",
                payload: {
                    seam: "popup-inbound",
                    reason: "undeclared-popup-action",
                    detail: "molsysviewer-not-declared:projection",
                },
            },
        );

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire(
                "molsysviewer-initial-sync",
                {
                    messages: [{ op: "load_molsys_payload" }, { op: "hide_whole", target: "whole" }],
                    cameraSnapshot: { target: [0, 0, 0] },
                    isSpinActive: true,
                    isSwingActive: true,
                    isDarkMode: true,
                    autohide: true,
                    autohideScope: "canvas",
                },
            ),
        });
        await flushAsync();

        assert.deepStrictEqual(calls.handled, [
            { op: "load_molsys_payload" },
            { op: "hide_whole", target: "whole" },
        ]);
        assert.deepStrictEqual(calls.camera, [
            { snapshot: { target: [0, 0, 0] }, duration: 0 },
        ]);
        assert.deepStrictEqual(calls.spin, [true]);
        assert.deepStrictEqual(calls.swing, [true]);
        assert.deepStrictEqual(calls.bg, ["dark"]);
        assert.equal(ctrl.controlsModel.get("autohide_controls"), true);
        assert.equal(ctrl.controlsModel.get("autohide_scope"), "canvas");

        ctrl.sendControlsSync({ op: "reset_view" });
        await flushAsync();
        assert.deepStrictEqual(calls.reset, []);
        assert.deepStrictEqual(calls.handled, [
            { op: "load_molsys_payload" },
            { op: "hide_whole", target: "whole" },
        ]);
        assert.deepStrictEqual(env.postedToHost.at(-1)?.envelope.action, "molsysviewer-sync-op");
        assert.deepStrictEqual(
            env.postedToHost.at(-1)?.envelope.payload,
            { op: "reset_view" },
        );
        assert.deepStrictEqual(env.postedToHost.at(-1)?.envelope.direction, "command");

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-op", { op: "reset_view" }),
        });
        await flushAsync();
        assert.deepStrictEqual(calls.handled.at(-1), { op: "reset_view" });

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-structure-data", {
                message: { op: "load_molsys_payload", payload: { structures: [] } },
                buffers: [],
            }),
        });
        await flushAsync();
        assert.deepStrictEqual(
            calls.handled.at(-1),
            { op: "load_molsys_payload", payload: { structures: [] } },
        );
        assert.equal(
            env.postedToHost.at(-1)?.envelope.action,
            "molsysviewer-structure-data-ack",
        );
        assert.deepStrictEqual(
            env.postedToHost.at(-1)?.envelope.payload,
            { event: "structure_data_json_complete" },
        );
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});

test("bootPopup relays changed programmatic cameras and consumes projections without echo", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const previousSetTimeout = (globalThis as any).setTimeout;
    const previousClearTimeout = (globalThis as any).clearTimeout;
    const env = makePopupTestEnv();
    const cameraApplied: any[] = [];
    let drawSubscriber: (() => void) | undefined;

    const ctrl: any = {
        plugin: {
            canvas3d: {
                didDraw: {
                    subscribe(fn: () => void) {
                        drawSubscriber = fn;
                    },
                },
            },
        },
        trajectory: {
            getTrajectoryState() {
                return { hasTrajectory: false, frameCount: 0, currentFrame: 0, isPlaying: false };
            },
        },
        async handleMessage(_msg: any) {},
        setCameraSnapshot(snapshot: any, duration: number) {
            cameraApplied.push({ snapshot, duration });
            ctrl.currentSnapshot = snapshot;
        },
        async toggleSpin(_enable?: boolean) {},
        async toggleSwing(_enable?: boolean) {},
        async toggleBackground(_mode?: string) {},
        getCameraSnapshot() {
            return ctrl.currentSnapshot ?? { eye: [9, 8, 7] };
        },
        onTrajectoryState(_cb: any, _opts: any) {},
        async resetView() {},
        toggleFullscreen() {},
        stepTrajectory(_by: number) {},
        stopTrajectoryPlayback() {},
        playTrajectory(_opts: any) {},
        setTrajectoryFrame(_index: number) {},
        isSpinActive: false,
        isSwingActive: false,
        isDarkMode: false,
    };

    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    (globalThis as any).setTimeout = (fn: () => void, _ms?: number) => {
        queueMicrotask(fn);
        return 1;
    };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup(popupModule(ctrl));
        await flushAsync();
        assert.ok(drawSubscriber);

        drawSubscriber?.();
        assert.strictEqual(
            env.postedToHost.some(msg => msg.type === "molsysviewer-sync-camera"),
            false,
        );

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-initial-sync", { messages: [] }),
        });
        await flushAsync();
        // Focus changes do not require a pressed pointer.
        drawSubscriber?.();
        await flushAsync();
        assert.deepStrictEqual(
            env.postedToHost.at(-1)?.envelope.action,
            "molsysviewer-sync-camera",
        );
        assert.deepStrictEqual(
            env.postedToHost.at(-1)?.envelope.payload,
            { eye: [9, 8, 7] },
        );
        assert.deepStrictEqual(env.postedToHost.at(-1)?.envelope.direction, "event");

        env.container.dispatch("pointerdown");
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-camera", { target: [1, 1, 1] }),
        });
        await flushAsync();
        assert.deepStrictEqual(cameraApplied, []);

        env.windowObj.dispatch("pointerup");
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-camera", { target: [2, 2, 2] }),
        });
        await flushAsync();
        assert.deepStrictEqual(cameraApplied, [
            { snapshot: { target: [2, 2, 2] }, duration: 0 },
        ]);
        const count = env.postedToHost.length;
        drawSubscriber?.(); await flushAsync();
        drawSubscriber?.(); await flushAsync();
        assert.equal(env.postedToHost.length, count, "received projections and unchanged draws never echo");
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-camera", { target: [4, 4, 4] }),
        });
        await flushAsync();
        // New input before that projection's first draw must still travel.
        ctrl.currentSnapshot = { eye: [3, 4, 5] };
        drawSubscriber?.(); await flushAsync();
        assert.deepStrictEqual(env.postedToHost.at(-1)?.envelope.payload, { eye: [3, 4, 5] });
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});

test("bootPopup dispatches molsysviewer-sync-op to controller (live mirror)", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const previousSetTimeout = (globalThis as any).setTimeout;
    const previousClearTimeout = (globalThis as any).clearTimeout;
    const env = makePopupTestEnv();
    const handled: any[] = [];

    const ctrl: any = {
        plugin: { canvas3d: { didDraw: { subscribe(_fn: any) {} } } },
        trajectory: { getTrajectoryState() { return { hasTrajectory: false, frameCount: 0, currentFrame: 0, isPlaying: false }; } },
        async handleMessage(msg: any) { handled.push(msg); },
        setCameraSnapshot(_s: any, _d: number) {},
        async toggleSpin(_e?: boolean) {},
        async toggleSwing(_e?: boolean) {},
        async toggleBackground(_m?: string) {},
        getCameraSnapshot() { return {}; },
        onTrajectoryState(_cb: any, _opts: any) {},
        async resetView() {},
        toggleFullscreen() {},
        stepTrajectory(_by: number) {},
        stopTrajectoryPlayback() {},
        playTrajectory(_opts: any) {},
        setTrajectoryFrame(_i: number) {},
        isSpinActive: false,
        isSwingActive: false,
        isDarkMode: false,
    };

    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    (globalThis as any).setTimeout = (fn: () => void, _ms?: number) => { fn(); return 1; };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup(popupModule(ctrl));
        await flushAsync();

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-op", { op: "hide_region", tag: "r1" }),
        });
        await flushAsync();

        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-op", { op: "show_whole", target: "whole" }),
        });
        await flushAsync();

        assert.deepStrictEqual(handled, [
            { op: "hide_region", tag: "r1" },
            { op: "show_whole", target: "whole" },
        ]);
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});

test("bootPopup molsysviewer-sync-autohide updates shared controls policy", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const previousSetTimeout = (globalThis as any).setTimeout;
    const previousClearTimeout = (globalThis as any).clearTimeout;
    const env = makePopupTestEnv();

    const ctrl: any = {
        plugin: { canvas3d: { didDraw: { subscribe(_fn: any) {} } } },
        trajectory: { getTrajectoryState() { return { hasTrajectory: false, frameCount: 0, currentFrame: 0, isPlaying: false }; } },
        async handleMessage(_msg: any) {},
        setCameraSnapshot(_s: any, _d: number) {},
        async toggleSpin(_e?: boolean) {},
        async toggleSwing(_e?: boolean) {},
        async toggleBackground(_m?: string) {},
        getCameraSnapshot() { return {}; },
        onTrajectoryState(_cb: any, _opts: any) {},
        async resetView() {},
        toggleFullscreen() {},
        stepTrajectory(_by: number) {},
        stopTrajectoryPlayback() {},
        playTrajectory(_opts: any) {},
        setTrajectoryFrame(_i: number) {},
        isSpinActive: false,
        isSwingActive: false,
        isDarkMode: false,
    };

    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    (globalThis as any).setTimeout = (fn: () => void, _ms?: number) => { fn(); return 1; };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup(popupModule(ctrl));
        await flushAsync();

        assert.equal(ctrl.controlsModel.get("autohide_controls"), true);

        // Enable autohide
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-autohide", { enabled: true, scope: "canvas" }),
        });
        await flushAsync();
        assert.equal(ctrl.controlsModel.get("autohide_controls"), true);
        assert.equal(ctrl.controlsModel.get("autohide_scope"), "canvas");

        // Disable autohide without reconstructing the controls.
        env.windowObj.dispatch("message", {
            source: env.windowObj.opener,
            data: hostWire("molsysviewer-sync-autohide", { enabled: false }),
        });
        await flushAsync();
        assert.equal(ctrl.controlsModel.get("autohide_controls"), false);
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});

test("bootPopup captures its own canvas after queued scene work and a fresh draw", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const env = makePopupTestEnv();
    const subscribers = new Set<() => void>();
    let completeScene!: () => void;
    const sceneBarrier = new Promise<void>(resolve => { completeScene = resolve; });
    let camera = { position: [1, 2, 3], target: [0, 0, 0], up: [0, 1, 0] };
    const appliedCamera = { position: [8, 5, 2], target: [1, 1, 1], up: [0, 1, 0] };
    let drawCount = 0;
    const handled: any[] = [];
    const ctrl: any = {
        plugin: { canvas3d: {
            didDraw: { subscribe(fn: () => void) { subscribers.add(fn); return { unsubscribe() { subscribers.delete(fn); } }; } },
            requestDraw() { drawCount++; setImmediate(() => { for (const fn of [...subscribers]) fn(); }); },
        } },
        async handleMessage(message: any) {
            handled.push(message);
            await sceneBarrier;
            camera = appliedCamera;
        },
        getCameraSnapshot() { return camera; },
        onTrajectoryState(callback: any, options: any) {
            if (options?.immediate) callback({ currentFrame: 2 });
            return () => {};
        },
    };
    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    try {
        await bootPopup(popupModule(ctrl));
        const dispatch = (payload: any) => env.windowObj.dispatch("message", {
            source: env.windowObj.opener, data: hostWire("molsysviewer-sync-op", payload),
        });
        dispatch({ op: "set_camera_snapshot", snapshot: appliedCamera });
        dispatch({ op: "request_visual_state", request_id: "capture-popup", capture_revision: "revision-a", capture_timeout_ms: 500 });
        await flushAsync();
        assert.equal(drawCount, 0, "capture must wait for earlier scene work");
        assert.equal(env.postedToHost.some(message => message.envelope.payload?.event === "visual_state_snapshot"), false);
        completeScene();
        for (let i = 0; i < 5; i++) await flushAsync();
        const reply = env.postedToHost.find(message => message.envelope.payload?.event === "visual_state_snapshot");
        assert.ok(reply);
        assert.equal(drawCount, 1);
        assert.equal(handled.length, 1, "frontend requests belong to the request handler, not the scene dispatcher");
        assert.equal(reply.envelope.endpointId, TEST_CHANNEL.popupEndpointId);
        assert.deepEqual(reply.envelope.payload, {
            event: "visual_state_snapshot", request_id: "capture-popup", capture_revision: "revision-a",
            ok: true, snapshot: appliedCamera, structure_index: 2,
        });
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
    }
});

test("bootPopup authenticates lifecycle controls before bypassing a pending draw or scene barrier", async () => {
    const previousWindow = (globalThis as any).window;
    const previousDocument = (globalThis as any).document;
    const env = makePopupTestEnv();
    const subscribers = new Set<() => void>();
    const handled: any[] = [];
    let drawCount = 0, disposals = 0;
    let releaseScene!: () => void;
    const scene = new Promise<void>(resolve => { releaseScene = resolve; });
    const ctrl: any = {
        plugin: { canvas3d: {
            didDraw: { subscribe(fn: () => void) { subscribers.add(fn); return { unsubscribe() { subscribers.delete(fn); } }; } },
            requestDraw() { drawCount++; },
        } },
        async handleMessage(message: any) { handled.push(message); if (message.op === "hold_scene") await scene; },
        dispose() { disposals++; },
    };
    (globalThis as any).window = env.windowObj;
    (globalThis as any).document = env.document;
    try {
        await bootPopup(popupModule(ctrl));
        await flushAsync();
        const existingSubscriptions = subscribers.size; // CameraSync owns its independent draw listener.
        const dispatch = (payload: any, valid = true) => {
            const wire = hostWire("molsysviewer-sync-op", payload);
            env.windowObj.dispatch("message", { source: env.windowObj.opener,
                data: valid ? wire : { ...wire, channel: { ...wire.channel, token: "wrong-channel" } } });
        };
        const capture = { op: "request_visual_state", request_id: "broker-request", capture_revision: "revision" };
        dispatch(capture);
        await flushAsync();
        assert.equal(drawCount, 1);
        assert.equal(subscribers.size, existingSubscriptions + 1);
        dispatch({ op: "studio_action_result", action: "restore_work_file", request_id: "restore-domain", ok: true });
        const verdict = { op: "studio_action_result", action: "cancel_work_file", request_id: "studio-domain", ok: true };
        dispatch({ ...capture, op: "cancel_visual_state" }, false);
        dispatch(verdict, false);
        await flushAsync();
        assert.equal(subscribers.size, existingSubscriptions + 1, "an unauthenticated abort cannot release the canvas wait");
        assert.equal(handled.length, 0, "unauthenticated verdicts and ordered restore must not bypass capture");
        dispatch(verdict);
        await flushAsync();
        assert.deepEqual(handled, [verdict], "the original Studio id releases its controls without pretending to be the broker id");
        assert.equal(subscribers.size, existingSubscriptions + 1);
        dispatch({ ...capture, op: "cancel_visual_state", capture_revision: "wrong" });
        await flushAsync();
        assert.equal(subscribers.size, existingSubscriptions + 1);
        dispatch({ ...capture, op: "cancel_visual_state" });
        for (let index = 0; index < 4; index++) await flushAsync();
        assert.equal(subscribers.size, existingSubscriptions);
        assert.equal(handled[1].action, "restore_work_file");
        assert.equal(env.postedToHost.some(message => message.envelope.payload?.event === "visual_state_snapshot"), false);

        dispatch({ op: "hold_scene" });
        dispatch({ ...capture, request_id: "queued-broker" });
        dispatch({ ...capture, op: "cancel_visual_state", request_id: "queued-broker" });
        await flushAsync();
        releaseScene();
        for (let index = 0; index < 4; index++) await flushAsync();
        assert.equal(drawCount, 1, "a queued capture canceled before starting must never request a draw");
        env.windowObj.dispatch("pagehide");
        dispatch({ ...capture, request_id: "after-disposal" });
        await flushAsync();
        assert.equal(drawCount, 1);
        assert.equal(disposals, 1);
    } finally {
        releaseScene();
        env.windowObj.dispatch("pagehide");
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
    }
});
