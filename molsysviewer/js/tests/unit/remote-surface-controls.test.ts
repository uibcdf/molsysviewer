import assert from "node:assert/strict";
import test from "node:test";

import { RemoteSurfaceControls } from "../../src/ui/remote-surface-controls";

type Listener = (event: any) => void;

class FakeElement {
    readonly style: Record<string, string> = {};
    readonly children: FakeElement[] = [];
    readonly attributes = new Map<string, string>();
    readonly listeners = new Map<string, Listener[]>();
    textContent = "";
    title = "";
    type = "";
    className = "";
    id = "";
    innerHTML = "";
    removed = false;

    appendChild(child: FakeElement) { this.children.push(child); return child; }
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }
    addEventListener(name: string, handler: Listener) {
        const listeners = this.listeners.get(name) ?? [];
        listeners.push(handler);
        this.listeners.set(name, listeners);
    }
    removeEventListener(name: string, handler: Listener) {
        this.listeners.set(name, (this.listeners.get(name) ?? []).filter(item => item !== handler));
    }
    dispatch(name: string, event: any = {}) {
        for (const listener of this.listeners.get(name) ?? []) listener(event);
    }
    contains(target: FakeElement): boolean {
        return target === this || this.children.some(child => child.contains(target));
    }
    closest() { return null; }
    remove() { this.removed = true; }
}

const find = (root: FakeElement, name: string, value: string): FakeElement | undefined => {
    if (root.getAttribute(name) === value) return root;
    for (const child of root.children) {
        const result = find(child, name, value);
        if (result) return result;
    }
    return undefined;
};

test("RemoteSurfaceControls exposes truthful local chrome and semantic reset", async () => {
    const previousDocument = (globalThis as any).document;
    const previousWindow = (globalThis as any).window;
    const documentTarget = new FakeElement();
    const windowTarget = new FakeElement();
    const head = new FakeElement();
    const fakeDocument: any = {
        ...documentTarget,
        head,
        fullscreenElement: null,
        createElement: () => new FakeElement(),
        getElementById: () => null,
        addEventListener: documentTarget.addEventListener.bind(documentTarget),
        removeEventListener: documentTarget.removeEventListener.bind(documentTarget),
        exitFullscreen: async () => { fakeDocument.fullscreenElement = null; },
    };
    (globalThis as any).document = fakeDocument;
    (globalThis as any).window = {
        addEventListener: windowTarget.addEventListener.bind(windowTarget),
        removeEventListener: windowTarget.removeEventListener.bind(windowTarget),
    };

    try {
        const host = new FakeElement() as FakeElement & { requestFullscreen: () => Promise<void> };
        host.requestFullscreen = async () => { fakeDocument.fullscreenElement = host; };
        let resets = 0;
        let panelToggles = 0;
        const controls = new RemoteSurfaceControls(host as unknown as HTMLElement, {
            resetView: () => { resets += 1; },
            togglePanel: () => { panelToggles += 1; },
        });

        find(host, "data-molsysviewer-remote-control", "reset")?.dispatch("click");
        find(host, "data-molsysviewer-remote-control", "panel")?.dispatch("click");
        find(host, "data-molsysviewer-remote-control", "full")?.dispatch("click");
        await Promise.resolve();

        assert.equal(resets, 1);
        assert.equal(panelToggles, 1);
        assert.equal(fakeDocument.fullscreenElement, host);
        assert.ok(find(host, "data-molsysviewer-remote-control", "help"));
        assert.equal(find(host, "data-molsysviewer-remote-control", "background"), undefined);

        controls.dispose();
        assert.equal(controls.root.removed, true);
    } finally {
        (globalThis as any).document = previousDocument;
        (globalThis as any).window = previousWindow;
    }
});
