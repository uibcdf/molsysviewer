import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public parentElement: FakeElement | null = null;
    public readonly attributes: Record<string, string> = {};

    setAttribute(name: string, value: string) {
        this.attributes[name] = value;
    }

    appendChild(child: FakeElement) {
        child.parentElement = this;
        this.children.push(child);
        return child;
    }

    remove() {
        if (!this.parentElement) return;
        const index = this.parentElement.children.indexOf(this);
        if (index >= 0) this.parentElement.children.splice(index, 1);
        this.parentElement = null;
    }
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    const previousBlob = (globalThis as any).Blob;
    const previousCreateObjectURL = URL.createObjectURL;
    const previousRevokeObjectURL = URL.revokeObjectURL;
    let source = "";

    (globalThis as any).document = {
        createElement: () => new FakeElement(),
    };
    (globalThis as any).Blob = class FakeBlob {
        constructor(parts: any[]) {
            source = parts.join("");
        }
    };
    URL.createObjectURL = (() => `data:text/javascript,${encodeURIComponent(source)}`) as any;
    URL.revokeObjectURL = (() => {}) as any;

    return () => {
        (globalThis as any).document = previousDocument;
        (globalThis as any).Blob = previousBlob;
        URL.createObjectURL = previousCreateObjectURL;
        URL.revokeObjectURL = previousRevokeObjectURL;
    };
}

test("addon panel render cleanup runs before widget host unmount", async () => {
    const restore = installFakeDom();
    try {
        const events: string[] = [];
        const controller: any = Object.create(MolSysViewerController.prototype);
        controller.model = undefined;
        controller.activePanelMsgListeners = [];
        controller.activePanelCleanup = null;
        controller.activePanelWidgetKey = null;
        controller.addonListeners = new Map();
        controller.notify = undefined;
        controller.applyWorkbenchMessage = () => {};
        controller.refreshNavigatePanel = () => {};
        controller.refreshAddonsPanel = () => {};
        controller.syncStripOverlaysForMessage = () => {};
        controller.addonsPanel = {
            mountAddonWidget(_el: HTMLElement) {
                events.push("mount");
            },
            unmountAddonWidget() {
                events.push("unmount");
            },
            unmountAddonWidgetOnly() {
                events.push("unmount_only");
            },
        };

        await controller.handleMessage({
            op: "mount_addon_panel",
            addon: "topomt",
            panel: "main",
            esm: `export function render({ el }) { el.textContent = "mounted"; return () => { globalThis.__msvAddonCleanupEvents.push("cleanup"); }; }`,
        });

        assert.strictEqual(events.at(-1), "mount");
        events.length = 0;
        (globalThis as any).__msvAddonCleanupEvents = events;
        controller.cleanupActivePanelWidget();
        assert.deepStrictEqual(events, ["cleanup", "unmount"]);
    } finally {
        delete (globalThis as any).__msvAddonCleanupEvents;
        restore();
    }
});


test("backend error ack shows a frontend toast", async () => {
    const restore = installFakeDom();
    try {
        const controller: any = Object.create(MolSysViewerController.prototype);
        const host = new FakeElement();
        controller.host = host;
        controller.applyWorkbenchMessage = () => {};
        controller.refreshNavigatePanel = () => {};
        controller.refreshAddonsPanel = () => {};
        controller.syncStripOverlaysForMessage = () => {};

        await controller.handleMessage({
            op: "backend_error_occurred",
            error_type: "ValueError",
            error_message: "No region found with tag 'missing'.",
        });

        assert.strictEqual(host.children.length, 1);
        assert.strictEqual(host.children[0].attributes["data-molsysviewer-toast"], "true");
        assert.strictEqual(host.children[0].textContent, "ValueError: No region found with tag 'missing'.");
    } finally {
        restore();
    }
});
