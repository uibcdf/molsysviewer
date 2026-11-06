import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public parentElement: FakeElement | null = null;
    public readonly attributes: Record<string, string> = {};
    private content = "";

    get innerHTML() { return this.content; }
    set innerHTML(value: string) {
        this.content = value;
        for (const child of this.children) child.parentElement = null;
        this.children.length = 0;
    }

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

test("managed synchronization emits immutable bounded addon metadata", async () => {
    const controller: any = Object.create(MolSysViewerController.prototype);
    const events: any[] = [];
    const playback: any[] = [];
    controller.addonListeners = new Map();
    controller.systemSyncOverlay = { setState() {} };
    controller.trajectory = { async setTrajectoryPlayback(value: any) { playback.push(value); } };
    controller.applyWorkbenchMessage = () => {};
    controller.refreshNavigatePanel = () => {};
    controller.refreshAddonsPanel = () => {};
    controller.syncStripOverlaysForMessage = () => {};
    controller.registerAddonListener("consumer", "system-sync-changed", (value: any) => events.push(value));
    await controller.handleMessage({
        op: "set_system_sync_state", state: "pending", target_revision: 2,
        integration_revision: 1, pending_operations: 1, coordinates: [99],
    } as any);
    assert.deepStrictEqual(events, [{
        state: "pending", operation_id: null, target_revision: 2,
        integration_revision: 1, pending_operations: 1, reason: null,
    }]);
    assert.ok(Object.isFrozen(events[0]));
    assert.strictEqual(playback.length, 1);
    await controller.handleMessage({ op: "set_system_sync_state", state: "synchronized", target_revision: 2 } as any);
    assert.strictEqual(events.at(-1).state, "synchronized");
    assert.strictEqual(playback.length, 1);
});

test("addon CSS survives render content replacement", async () => {
    const restore = installFakeDom();
    const controller: any = Object.create(MolSysViewerController.prototype);
    let mounted: FakeElement | undefined;
    try {
        controller.model = undefined;
        controller.activePanelMsgListeners = [];
        controller.activePanelCleanup = null;
        controller.activePanelWidgetKey = null;
        controller.addonListeners = new Map();
        controller.applyWorkbenchMessage = () => {};
        controller.refreshNavigatePanel = () => {};
        controller.refreshAddonsPanel = () => {};
        controller.syncStripOverlaysForMessage = () => {};
        controller.addonsPanel = {
            mountAddonWidget(el: FakeElement) { mounted = el; },
            unmountAddonWidget() {}, unmountAddonWidgetOnly() {},
        };
        const css = ".probe { display: flex; }";
        await controller.handleMessage({
            op: "mount_addon_panel", addon: "css-probe", panel: "main", css,
            esm: `export function render({ el }) { el.innerHTML = "<section>initial</section>"; globalThis.__cssRenderElement = el; }`,
        });
        assert.ok(mounted?.children.some(child => child.textContent === css));
        (globalThis as any).__cssRenderElement.innerHTML = "<section>next state</section>";
        assert.ok(mounted?.children.some(child => child.textContent === css));
    } finally {
        controller.cleanupActivePanelWidget();
        delete (globalThis as any).__cssRenderElement;
        restore();
    }
});

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

// These normalization/selection methods need no DOM or molecular substitute.
// The browser receiver separately exercises the registered provider and clicks.
test("addon navigation honors declared order and entry without resetting a valid choice", () => {
    const controller: any = Object.create(MolSysViewerController.prototype);
    const workspace_specs = [
        { addon: "z", id: "z", title: "First", order: -1, entry_panel: "system" },
        { addon: "a", id: "a", title: "Second", order: 10 },
    ];
    controller.addonWorkspaces = controller.buildAddonWorkspaceSummary({ workspace_specs });
    assert.deepStrictEqual(controller.addonWorkspaces.map((w: any) => w.id), ["z", "a"]);
    controller.addonPanels = controller.buildAddonPanelSummary({workspace_specs, panel_specs: [
        {addon: "z", id: "geometry", title: "Geometry", order: 0},
        {addon: "z", id: "system", title: "System", order: 10},
        {addon: "z", id: "last", title: "Last", order: 20},
    ]});
    assert.deepStrictEqual(controller.getWorkspacePanels("z").map((p: any) => p.id), ["geometry", "system", "last"]);
    controller.currentWorkspacePanelByWorkspace = new Map();
    assert.strictEqual(controller.ensureWorkspacePanelSelection("z"), "system");
    controller.currentWorkspacePanelByWorkspace.set("z", "geometry");
    assert.strictEqual(controller.ensureWorkspacePanelSelection("z"), "geometry");
    controller.currentWorkspacePanelByWorkspace.set("z", "retired");
    controller.addonWorkspaces[0].entryPanel = "missing";
    assert.strictEqual(controller.ensureWorkspacePanelSelection("z"), "geometry");
    assert.strictEqual(controller.ensureWorkspacePanelSelection("unknown"), null);
    const fallback = controller.buildAddonPanelSummary({workspace_specs, panel_specs: [
        {addon:"z",id:"z",title:"Z",order:NaN},
        {addon:"z",id:"a",title:"A"},
    ]});
    assert.deepStrictEqual(fallback.map((p: any) => p.id), ["a","z"]);
});
