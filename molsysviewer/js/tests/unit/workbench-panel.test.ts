import assert from "node:assert";
import test from "node:test";

import { WorkbenchPanel } from "../../src/ui/workbench-panel";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
    public parent: FakeElement | null = null;
    private attributes = new Map<string, string>();
    private listeners = new Map<string, Array<(event?: any) => void>>();

    appendChild(child: FakeElement) {
        child.parent = this;
        this.children.push(child);
        return child;
    }

    replaceChildren(...children: FakeElement[]) {
        this.children.length = 0;
        for (const child of children) child.parent = this;
        this.children.push(...children);
    }

    remove() {}
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }

    addEventListener(name: string, handler: (event?: any) => void) {
        const handlers = this.listeners.get(name) ?? [];
        handlers.push(handler);
        this.listeners.set(name, handlers);
    }

    dispatch(name: string, event?: any) {
        for (const handler of this.listeners.get(name) ?? []) {
            handler(event);
        }
    }
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    (globalThis as any).document = {
        createElement: () => new FakeElement(),
    };
    return () => {
        (globalThis as any).document = previousDocument;
    };
}

function findFirstByAttribute(root: FakeElement, attributeName: string, value?: string): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        const attr = node.getAttribute(attributeName);
        if (attr !== undefined && (value === undefined || attr === value)) {
            out = node;
            return;
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function findFirstText(node: FakeElement): string {
    if (node.textContent) return node.textContent;
    for (const child of node.children) {
        const text = findFirstText(child);
        if (text) return text;
    }
    return "";
}

test("WorkbenchPanel renders titled shell and empty sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);

        const root = host.children[0];
        const title = findFirstByAttribute(root, "data-molsysviewer-workbench-panel-title");
        const navGroup = findFirstByAttribute(root, "data-molsysviewer-panel-nav-group", "true");
        const navCurrent = findFirstByAttribute(root, "data-molsysviewer-panel-nav-current", "workbench");
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "navigate");
        const annotationsEmpty = findFirstByAttribute(root, "data-molsysviewer-workbench-empty", "annotations");
        const sceneEmpty = findFirstByAttribute(root, "data-molsysviewer-workbench-empty", "scene");

        assert.ok(root);
        assert.ok(title);
        assert.ok(navGroup);
        assert.ok(navCurrent);
        assert.ok(navButton);
        assert.strictEqual(navButton?.textContent, "Navigate");
        assert.strictEqual(title?.textContent, "Workbench");
        assert.strictEqual(root.style.display, "flex");
        assert.strictEqual(root.style.transform, "translateX(240px)");
        assert.strictEqual(annotationsEmpty?.textContent, "No annotations yet.");
        assert.strictEqual(sceneEmpty?.textContent, "No scene style selected.");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel populates sections and scene summary", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);
        panel.setAnnotations([{ key: "notes", title: "Picked label", subtitle: "group 12", active: true, context: true }]);
        panel.setMeasurements([{ title: "Distance", subtitle: "3.2 A" }]);
        panel.setShapes([{ title: "Pocket", subtitle: "surface", hidden: true }]);
        panel.setScene({ styleTag: "polymer-and-ligand", preset: "atomic-detail" });
        panel.setAddons([{
            name: "topomt",
            workspaceTitles: ["TopoMT"],
            panelTitles: ["Topo"],
            workbenchTitles: ["Pockets"],
            contextActionTitles: ["Focus Pocket"],
            exportHelperTitles: ["Topography Figure Export"],
        }]);

        const root = host.children[0];
        const items = [];
        const collect = (node: FakeElement) => {
            if (node.getAttribute("data-molsysviewer-workbench-item") === "true") items.push(node);
            for (const child of node.children) collect(child);
        };
        collect(root);

        assert.strictEqual(items.length, 6);
        assert.strictEqual(findFirstText(items[0]), "Picked label");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-workbench-item-active"), "true");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-workbench-item-context"), "true");
        assert.strictEqual(findFirstText(items[1]), "Distance");
        assert.strictEqual(findFirstText(items[2]), "Pocket");
        assert.strictEqual(findFirstText(items[3]), "Style: polymer-and-ligand");
        assert.strictEqual(findFirstText(items[4]), "Preset: atomic-detail");
        assert.strictEqual(findFirstText(items[5]), "topomt");
        assert.ok(items[5].children[1]);
        assert.strictEqual(
            items[5].children[1]?.textContent,
            "Workspaces: TopoMT · Panels: Topo · Workbench: Pockets · Context: Focus Pocket · Export: Topography Figure Export",
        );

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel renders dynamic addon workbench sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);
        panel.setAddonWorkbenchSections([
            {
                key: "topomt:pockets",
                title: "Pockets",
                itemTitle: "Add-on: topomt",
                itemSubtitle: "top_pockets",
            },
        ]);

        const root = host.children[0];
        const section = findFirstByAttribute(root, "data-molsysviewer-workbench-section", "addon:topomt:pockets");
        const row = findFirstByAttribute(root, "data-molsysviewer-workbench-item-key", "topomt:pockets");

        assert.ok(section);
        assert.ok(row);
        assert.strictEqual(findFirstText(row!), "Add-on: topomt");
        assert.strictEqual(row?.children[1]?.textContent, "top_pockets");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel renders workspace panel selector and active host", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);
        let selected = "";

        panel.setVisible(true);
        panel.setWorkspacePanels(
            [
                { id: "topo", title: "Topo", active: true, description: "Pocket analysis", entry: "topomt.panel.topo", addon: "topomt" },
                { id: "channels", title: "Channels" },
            ],
            (panelId) => { selected = panelId; },
        );
        panel.setActiveWorkspacePanel({
            workspaceTitle: "TopoMT",
            title: "Topo",
            description: "Pocket analysis",
            entry: "topomt.panel.topo",
            addon: "topomt",
            contextActionTitles: ["Inspect Pocket", "Focus Pocket"],
            exportHelperTitles: ["Pocket Figure"],
            sections: [
                {
                    key: "topomt:pockets",
                    title: "Pockets",
                    itemTitle: "Add-on: topomt",
                    itemSubtitle: "top_pockets",
                },
            ],
        });

        const root = host.children[0];
        const stack = findFirstByAttribute(root, "data-molsysviewer-panel-stack", "true");
        const active = findFirstByAttribute(root, "data-molsysviewer-panel-stack-current", "topo");
        const button = findFirstByAttribute(root, "data-molsysviewer-panel-stack-option", "channels");
        const hostCard = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-host", "true");
        const title = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-title", "true");
        const entry = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-entry", "true");
        const context = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-context-actions", "true");
        const exports = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-export-helpers", "true");
        const section = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-section", "topomt:pockets");
        const sectionTitle = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-section-title", "topomt:pockets");
        const sectionItem = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-section-item", "topomt:pockets");
        const sectionSubtitle = findFirstByAttribute(root, "data-molsysviewer-workbench-workspace-panel-section-subtitle", "topomt:pockets");

        assert.ok(stack);
        assert.ok(active);
        assert.ok(button);
        assert.ok(hostCard);
        assert.ok(title);
        assert.ok(entry);
        assert.ok(context);
        assert.ok(exports);
        assert.ok(section);
        assert.ok(sectionTitle);
        assert.ok(sectionItem);
        assert.ok(sectionSubtitle);
        assert.strictEqual(title?.textContent, "TopoMT · Topo");
        assert.strictEqual(entry?.textContent, "Entry: topomt.panel.topo");
        assert.strictEqual(context?.textContent, "Context: Inspect Pocket, Focus Pocket");
        assert.strictEqual(exports?.textContent, "Export: Pocket Figure");
        assert.strictEqual(sectionTitle?.textContent, "Pockets");
        assert.strictEqual(sectionItem?.textContent, "Add-on: topomt");
        assert.strictEqual(sectionSubtitle?.textContent, "top_pockets");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selected, "channels");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel rows trigger activation when provided", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);
        let activated = 0;

        panel.setVisible(true);
        panel.setAnnotations([{ title: "Picked label", subtitle: "group 12", onActivate: () => { activated += 1; } }]);

        const root = host.children[0];
        const row = findFirstByAttribute(root, "data-molsysviewer-workbench-item");
        assert.ok(row);
        row?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(activated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel rows expose visibility toggle when provided", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);
        let toggled = 0;

        panel.setVisible(true);
        panel.setAnnotations([{
            title: "Picked label",
            subtitle: "group 12",
            hidden: true,
            onToggleVisibility: () => { toggled += 1; },
        }]);

        const root = host.children[0];
        const button = findFirstByAttribute(root, "data-molsysviewer-workbench-item-visibility", "hidden");
        assert.ok(button);
        assert.strictEqual(button?.textContent, "Show");
        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(toggled, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel sections can collapse and expand", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);
        panel.setAnnotations([{ title: "Picked label", subtitle: "group 12" }]);

        const root = host.children[0];
        const toggle = findFirstByAttribute(root, "data-molsysviewer-workbench-section-toggle", "annotations");
        const marker = findFirstByAttribute(root, "data-molsysviewer-workbench-section-marker", "annotations");
        const section = findFirstByAttribute(root, "data-molsysviewer-workbench-section", "annotations");
        const row = findFirstByAttribute(root, "data-molsysviewer-workbench-item");
        assert.ok(toggle);
        assert.ok(marker);
        assert.ok(section);
        assert.ok(row);
        const list = section?.children[1];
        assert.ok(list);
        assert.strictEqual(list?.style.display, "flex");
        assert.strictEqual(marker?.textContent, "−");

        toggle?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(list?.style.display, "none");
        assert.strictEqual(marker?.textContent, "+");

        toggle?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(list?.style.display, "flex");
        assert.strictEqual(marker?.textContent, "−");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel exposes shared expanded state API and collapses when hidden", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let lastExpanded: boolean | null = null;
        const panel = new WorkbenchPanel(host);
        panel.setOnExpandedChange((expanded) => { lastExpanded = expanded; });

        panel.setVisible(true);
        panel.setExpanded(true);

        const root = host.children[0];
        assert.strictEqual(panel.isExpanded(), true);
        assert.strictEqual(lastExpanded, true);
        assert.strictEqual(root.style.transform, "translateX(0)");

        panel.setVisible(false);
        assert.strictEqual(panel.isExpanded(), false);
        assert.strictEqual(lastExpanded, false);
        assert.strictEqual(root.style.transform, "translateX(240px)");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel header nav button triggers navigate-to-navigate callback", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let navigated = 0;
        const panel = new WorkbenchPanel(host);
        panel.setOnNavigateToNavigate(() => { navigated += 1; });

        panel.setVisible(true);

        const root = host.children[0];
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "navigate");
        assert.ok(navButton);

        navButton?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(navigated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel exposes workspace launcher when multiple workspaces exist", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let selectedWorkspace: string | null = null;
        const panel = new WorkbenchPanel(host);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core", subtitle: "Navigate + Workbench" },
                { id: "topomt", title: "TopoMT", subtitle: "2 panels · 1 section" },
            ],
            "core",
            (workspaceId) => { selectedWorkspace = workspaceId; },
        );

        panel.setVisible(true);

        const root = host.children[0];
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current", "core");
        const launcher = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-launcher", "true");
        assert.ok(current);
        assert.ok(launcher);
        assert.strictEqual(current?.textContent, "Core");

        current?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const button = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option", "topomt");
        const subtitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-subtitle", "topomt");
        assert.ok(button);
        assert.strictEqual(subtitle?.textContent, "2 panels · 1 section");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel supports custom navigation labels", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        let navigated = 0;
        panel.setOnNavigateToNavigate(() => {
            navigated += 1;
        }, "Core");

        const root = host.children[0];
        const button = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "core");
        assert.ok(button);
        assert.strictEqual(button?.textContent, "Core");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(navigated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});
