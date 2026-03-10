import assert from "node:assert";
import test from "node:test";

import { bootPopup } from "../../src/popup/popup-logic";

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

test("bootPopup replays initial sync and enables autohide listeners", async () => {
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
        fn();
        return 1;
    };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup({ MolSysViewerController: { create: async () => ctrl } });
        await flushAsync();

        assert.deepStrictEqual(env.postedToHost[0], {
            type: "molsysviewer-pop-ready",
            data: null,
            from: "popup",
        });
        assert.ok(drawSubscriber);

        env.windowObj.dispatch("message", {
            data: {
                type: "molsysviewer-initial-sync",
                data: {
                    messages: [{ op: "load_molsys_payload" }, { op: "hide_global", target: "global" }],
                    cameraSnapshot: { target: [0, 0, 0] },
                    isSpinActive: true,
                    isSwingActive: true,
                    isDarkMode: true,
                    autohide: true,
                },
            },
        });
        await flushAsync();

        assert.deepStrictEqual(calls.handled, [
            { op: "load_molsys_payload" },
            { op: "hide_global", target: "global" },
        ]);
        assert.deepStrictEqual(calls.camera, [
            { snapshot: { target: [0, 0, 0] }, duration: 0 },
        ]);
        assert.deepStrictEqual(calls.spin, [true]);
        assert.deepStrictEqual(calls.swing, [true]);
        assert.deepStrictEqual(calls.bg, ["dark"]);
        assert.ok(env.container.listenerCount("pointerenter") > 0);
        assert.ok(env.container.listenerCount("pointerleave") > 0);
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});

test("bootPopup gates camera sync by interaction in both directions", async () => {
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
        },
        async toggleSpin(_enable?: boolean) {},
        async toggleSwing(_enable?: boolean) {},
        async toggleBackground(_mode?: string) {},
        getCameraSnapshot() {
            return { eye: [9, 8, 7] };
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
        fn();
        return 1;
    };
    (globalThis as any).clearTimeout = (_id: number) => {};

    try {
        await bootPopup({ MolSysViewerController: { create: async () => ctrl } });
        await flushAsync();
        assert.ok(drawSubscriber);

        drawSubscriber?.();
        assert.strictEqual(
            env.postedToHost.some(msg => msg.type === "molsysviewer-sync-camera"),
            false,
        );

        env.container.dispatch("pointerdown");
        drawSubscriber?.();
        assert.deepStrictEqual(env.postedToHost.at(-1), {
            type: "molsysviewer-sync-camera",
            data: { eye: [9, 8, 7] },
            from: "popup",
        });

        env.windowObj.dispatch("message", {
            data: {
                type: "molsysviewer-sync-camera",
                data: { target: [1, 1, 1] },
            },
        });
        await flushAsync();
        assert.deepStrictEqual(cameraApplied, []);

        env.windowObj.dispatch("pointerup");
        env.windowObj.dispatch("message", {
            data: {
                type: "molsysviewer-sync-camera",
                data: { target: [2, 2, 2] },
            },
        });
        await flushAsync();
        assert.deepStrictEqual(cameraApplied, [
            { snapshot: { target: [2, 2, 2] }, duration: 0 },
        ]);
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).document = previousDocument;
        (globalThis as any).setTimeout = previousSetTimeout;
        (globalThis as any).clearTimeout = previousClearTimeout;
    }
});
