import assert from "node:assert";
import test from "node:test";

import { AddonsPanel } from "../../src/ui/addons-panel";

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

function collectByAttribute(root: FakeElement, attributeName: string, value?: string): FakeElement[] {
    const out: FakeElement[] = [];
    const walk = (node: FakeElement) => {
        const attr = node.getAttribute(attributeName);
        if (attr !== undefined && (value === undefined || attr === value)) {
            out.push(node);
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

test("AddonsPanel renders in catalog mode when currentWorkspaceId is core", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);
        let selectedWorkspace = "";

        panel.setVisible(true);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core", subtitle: "Navigate" },
                { id: "topomt", title: "TopoMT", description: "cavity detection and channel analysis", panelCount: 2, workbenchSectionCount: 1, contextActionCount: 1 },
                { id: "pharmacophoremt", title: "PharmacophoreMT", description: "pharmacophore modeling", panelCount: 3, workbenchSectionCount: 2, contextActionCount: 2 },
            ],
            "core",
            (workspaceId) => { selectedWorkspace = workspaceId; }
        );

        const root = host.children[0];
        const leftColumn = findFirstByAttribute(root, "data-molsysviewer-addons-panel-left");
        const rightColumn = findFirstByAttribute(root, "data-molsysviewer-addons-panel-right");
        const overview = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview");

        assert.ok(root);
        assert.ok(leftColumn);
        assert.ok(rightColumn);
        assert.ok(overview);

        // Sidebar is hidden in core/catalog mode
        assert.strictEqual(leftColumn.style.display, "none");
        assert.strictEqual(rightColumn.style.paddingLeft, "0");

        // Verify addon cards render
        const cards = collectByAttribute(root, "data-molsysviewer-addon-card");
        assert.strictEqual(cards.length, 2);
        assert.strictEqual(findFirstText(cards[0]), "TopoMT");
        assert.strictEqual(findFirstText(cards[1]), "PharmacophoreMT");

        // Check description text
        assert.ok(cards[0].children[1]?.textContent.includes("cavity detection"));

        // Card select callback works
        cards[0].dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel renders diagnostics for discovery/load failures", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core" },
                { id: "topomt", title: "TopoMT" },
            ],
            "core",
            () => {}
        );
        panel.setAddonDiagnostics([
            {
                kind: "discovery",
                source: "topomt",
                reason: "failed to import module",
                traceback: "Traceback: ImportError in topomt",
            }
        ]);

        const root = host.children[0];
        const failureCard = findFirstByAttribute(root, "data-molsysviewer-addons-addon-discovery-failure", "topomt");
        assert.ok(failureCard);

        const errorBadge = failureCard.children[0]?.children[1];
        assert.ok(errorBadge);
        assert.strictEqual(errorBadge.textContent, "Discovery Error");
        assert.strictEqual(failureCard.children[1]?.textContent, "failed to import module");

        // Collapsible traceback is initially hidden
        const traceBox = failureCard.children[2];
        assert.ok(traceBox);
        assert.strictEqual(traceBox.style.display, "none");

        // Toggles display on click
        failureCard.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(traceBox.style.display, "block");
        assert.strictEqual(traceBox.textContent, "Traceback: ImportError in topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel renders active workspace panels as vertical sidebar tabs", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);
        let selectedWorkspace = "";
        let selectedPanel = "";

        panel.setVisible(true);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core" },
                { id: "topomt", title: "TopoMT" },
            ],
            "topomt",
            (workspaceId) => { selectedWorkspace = workspaceId; }
        );
        panel.setWorkspacePanels(
            [
                { id: "navigate", title: "Navigate" },
                { id: "addons", title: "Add-ons" },
                { id: "topo", title: "Topo", active: true, description: "cavities" },
                { id: "channels", title: "Channels", description: "pathways" },
            ],
            (panelId) => { selectedPanel = panelId; }
        );

        const root = host.children[0];
        const leftColumn = findFirstByAttribute(root, "data-molsysviewer-addons-panel-left");
        const rightColumn = findFirstByAttribute(root, "data-molsysviewer-addons-panel-right");

        assert.ok(leftColumn);
        assert.ok(rightColumn);

        // Sidebar is visible in active workspace mode
        assert.strictEqual(leftColumn.style.display, "flex");
        assert.strictEqual(rightColumn.style.paddingLeft, "12px");

        // Back button is rendered
        const backBtn = findFirstByAttribute(root, "data-molsysviewer-addon-back-button", "true");
        assert.ok(backBtn);
        assert.strictEqual(backBtn.textContent, "← Back to Add-ons");

        // Back button triggers select core
        backBtn.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "core");

        // Workspace panel tabs are rendered (excluding shell control tabs navigate & addons)
        const tabs = collectByAttribute(root, "data-molsysviewer-addon-section-tab");
        assert.strictEqual(tabs.length, 2);
        assert.strictEqual(tabs[0].getAttribute("data-molsysviewer-addon-section-tab"), "topo");
        assert.strictEqual(tabs[1].getAttribute("data-molsysviewer-addon-section-tab"), "channels");

        // Highlight active tab
        assert.ok(tabs[0].style.borderLeft);
        assert.ok(!tabs[1].style.borderLeft);

        // Tab click triggers callback
        tabs[1].dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedPanel, "channels");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel mountAddonWidget/unmountAddonWidget displays widget correctly", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);
        const widgetEl = new FakeElement() as any;
        panel.mountAddonWidget(widgetEl);

        const root = host.children[0];
        const widgetHost = findFirstByAttribute(root, "data-molsysviewer-addon-widget-host", "true");
        const overview = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview", "true");

        assert.ok(widgetHost);
        assert.ok(overview);
        assert.strictEqual(widgetHost.style.display, "flex");
        assert.strictEqual(overview.style.display, "none");
        assert.strictEqual(widgetHost.children[0], widgetEl);

        panel.unmountAddonWidget();
        assert.strictEqual(widgetHost.style.display, "none");
        assert.strictEqual(overview.style.display, "flex");
        assert.strictEqual(widgetHost.children.length, 0);

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel exposes shared expanded state API", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let lastExpanded: boolean | null = null;
        const panel = new AddonsPanel(host);
        panel.setOnExpandedChange((expanded) => { lastExpanded = expanded; });

        panel.setVisible(true);
        panel.setExpanded(true);

        const root = host.children[0];
        assert.strictEqual(panel.isExpanded(), true);
        assert.strictEqual(lastExpanded, true);
        assert.strictEqual(root.style.transform, "translateX(0)");

        panel.dispose();
    } finally {
        restore();
    }
});
