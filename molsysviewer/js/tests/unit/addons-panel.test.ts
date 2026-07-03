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

function findFirstText(node: FakeElement): string {
    if (node.textContent) return node.textContent;
    for (const child of node.children) {
        const text = findFirstText(child);
        if (text) return text;
    }
    return "";
}

test("AddonsPanel renders titled shell and empty sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);

        const root = host.children[0];
        const title = findFirstByAttribute(root, "data-molsysviewer-addons-panel-title");
        const navGroup = findFirstByAttribute(root, "data-molsysviewer-panel-nav-group", "true");
        const navCurrent = findFirstByAttribute(root, "data-molsysviewer-panel-nav-current", "add-ons");
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "navigate");
        const annotationsEmpty = findFirstByAttribute(root, "data-molsysviewer-addons-empty", "annotations");
        const sceneEmpty = findFirstByAttribute(root, "data-molsysviewer-addons-empty", "scene");

        assert.ok(root);
        assert.ok(title);
        assert.ok(navGroup);
        assert.ok(navCurrent);
        assert.ok(navButton);
        assert.strictEqual(navButton?.textContent, "Navigate");
        assert.strictEqual(title?.textContent, "Add-ons");
        assert.strictEqual(root.style.display, "flex");
        assert.strictEqual(root.style.transform, "translateX(240px)");
        assert.strictEqual(annotationsEmpty?.textContent, "No annotations yet.");
        assert.strictEqual(sceneEmpty?.textContent, "No scene style selected.");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel populates sections and scene summary", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);
        panel.setAnnotations([{ key: "notes", title: "Picked label", subtitle: "group 12", active: true, context: true }]);
        panel.setMeasurements([{ title: "Distance", subtitle: "3.2 A" }]);
        panel.setShapes([{ title: "Pocket", subtitle: "surface", hidden: true }]);
        panel.setScene({
            styleTag: "polymer-and-ligand",
            preset: "atomic-detail",
            figurePreset: "publication-light",
            figureScale: 2.0,
            figureVariants: ["dark", "transparent"],
        });
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
            if (node.getAttribute("data-molsysviewer-addons-item") === "true") items.push(node);
            for (const child of node.children) collect(child);
        };
        collect(root);

        assert.strictEqual(items.length, 8);
        assert.strictEqual(findFirstText(items[0]), "Picked label");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-addons-item-active"), "true");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-addons-item-context"), "true");
        assert.strictEqual(findFirstText(items[1]), "Distance");
        assert.strictEqual(findFirstText(items[2]), "Pocket");
        assert.strictEqual(findFirstText(items[3]), "Style: polymer-and-ligand");
        assert.strictEqual(findFirstText(items[4]), "Preset: atomic-detail");
        assert.strictEqual(findFirstText(items[5]), "Figure: publication-light @ 2.0x");
        assert.strictEqual(findFirstText(items[6]), "Variants: dark, transparent");
        assert.strictEqual(findFirstText(items[7]), "topomt");
        assert.ok(items[7].children[1]);
        assert.strictEqual(
            items[7].children[1]?.textContent,
            "Workspaces: TopoMT · Panels: Topo · Workbench: Pockets · Context: Focus Pocket · Export: Topography Figure Export",
        );

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel renders addon discovery failures", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);
        panel.setAddons([]);
        panel.setAddonDiagnostics([
            {
                kind: "discovery",
                source: "entry-point:broken-addon",
                reason: "broken entry point",
                traceback: "Traceback details",
            },
            {
                kind: "lifecycle",
                source: "lifecycle:broken-addon.on_enable",
                reason: "enable exploded",
                traceback: "Lifecycle traceback",
            },
        ]);

        const root = host.children[0];
        const failure = findFirstByAttribute(
            root,
            "data-molsysviewer-addons-addon-discovery-failure",
            "entry-point:broken-addon",
        );

        assert.ok(failure);
        assert.strictEqual(findFirstText(failure), "Discovery failed: entry-point:broken-addon");
        assert.strictEqual(failure.children[1]?.textContent, "broken entry point");
        assert.strictEqual(failure.title, "Traceback details");

        const lifecycleFailure = findFirstByAttribute(
            root,
            "data-molsysviewer-addons-addon-discovery-failure",
            "lifecycle:broken-addon.on_enable",
        );
        assert.ok(lifecycleFailure);
        assert.strictEqual(findFirstText(lifecycleFailure), "Lifecycle failed: lifecycle:broken-addon.on_enable");
        assert.strictEqual(lifecycleFailure.children[1]?.textContent, "enable exploded");
        assert.strictEqual(lifecycleFailure.title, "Lifecycle traceback");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel renders dynamic addon workbench sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

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
        const section = findFirstByAttribute(root, "data-molsysviewer-addons-section", "addon:topomt:pockets");
        const row = findFirstByAttribute(root, "data-molsysviewer-addons-item-key", "topomt:pockets");

        assert.ok(section);
        assert.ok(row);
        assert.strictEqual(findFirstText(row!), "Add-on: topomt");
        assert.strictEqual(row?.children[1]?.textContent, "top_pockets");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel renders workspace panel selector and active host", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);
        let selected = "";
        let selectedWorkspace = "";

        panel.setVisible(true);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core", subtitle: "Navigate + Workbench", panelCount: 2 },
                { id: "topomt", title: "TopoMT", subtitle: "2 panels · 1 section", panelCount: 2, workbenchSectionCount: 1, workbenchSectionTitles: ["Pockets"], contextActionCount: 1, exportHelperCount: 1 },
                { id: "pharmacophoremt", title: "PharmacophoreMT", subtitle: "3 panels · 2 sections", panelCount: 3, workbenchSectionCount: 2, contextActionCount: 2 },
            ],
            "topomt",
            (workspaceId) => { selectedWorkspace = workspaceId; },
        );
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
        const runtimeDeck = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-runtime-deck", "true");
        const currentSection = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-section", "current");
        const overviewCard = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card", "topomt");
        const overviewSubtitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-subtitle", "topomt");
        const overviewEntry = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-entry", "topomt");
        const overviewPreview = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview", "topomt");
        const overviewPreviewDescription = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-description", "topomt");
        const overviewPreviewCapabilities = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-capabilities", "topomt");
        const overviewPreviewSection = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-section", "topomt:pockets");
        const overviewPreviewSectionTitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-section-title", "topomt:pockets");
        const overviewPreviewSectionItem = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-section-item", "topomt:pockets");
        const overviewPreviewSectionSubtitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-preview-section-subtitle", "topomt:pockets");
        const overviewCapabilities = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-capabilities", "topomt");
        const overviewPanels = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panels", "topomt");
        const overviewCurrentPanel = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel-current", "topo");
        const overviewPanelButton = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel", "channels");
        const overviewCurrentPanelTitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel-title", "topo");
        const overviewCurrentPanelDescription = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel-description", "topo");
        const overviewCurrentPanelEntry = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel-entry", "topo");
        const overviewPanelButtonTitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-panel-title", "channels");
        const overviewMarker = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-marker", "topomt");
        const stack = findFirstByAttribute(root, "data-molsysviewer-panel-stack", "true");
        const active = findFirstByAttribute(root, "data-molsysviewer-panel-stack-current", "topo");
        const button = findFirstByAttribute(root, "data-molsysviewer-panel-stack-option", "channels");
        const hostCard = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-host", "true");
        const title = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-title", "true");
        const entry = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-entry", "true");
        const context = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-context-actions", "true");
        const exports = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-export-helpers", "true");
        const section = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-section", "topomt:pockets");
        const sectionTitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-section-title", "topomt:pockets");
        const sectionItem = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-section-item", "topomt:pockets");
        const sectionSubtitle = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-panel-section-subtitle", "topomt:pockets");

        assert.ok(runtimeDeck);
        assert.ok(currentSection);
        assert.ok(overviewCard);
        assert.ok(overviewSubtitle);
        assert.ok(overviewEntry);
        assert.ok(overviewPreview);
        assert.ok(overviewPreviewDescription);
        assert.ok(overviewPreviewCapabilities);
        assert.ok(overviewPreviewSection);
        assert.ok(overviewPreviewSectionTitle);
        assert.ok(overviewPreviewSectionItem);
        assert.ok(overviewPreviewSectionSubtitle);
        assert.ok(overviewCapabilities);
        assert.ok(overviewPanels);
        assert.ok(overviewCurrentPanel);
        assert.ok(overviewPanelButton);
        assert.ok(overviewCurrentPanelTitle);
        assert.ok(overviewCurrentPanelDescription);
        assert.ok(overviewCurrentPanelEntry);
        assert.ok(overviewPanelButtonTitle);
        assert.ok(overviewMarker);
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
        assert.strictEqual(currentSection?.textContent, "Current");
        assert.strictEqual(overviewSubtitle?.textContent, "Panel: Topo");
        assert.strictEqual(overviewEntry?.textContent, "Entry: topomt.panel.topo");
        assert.strictEqual(overviewPreviewDescription?.textContent, "Pocket analysis");
        assert.strictEqual(overviewCapabilities?.children.length, 4);
        assert.strictEqual(overviewPreviewCapabilities?.children.length, 3);
        assert.strictEqual(overviewPreviewSectionTitle?.textContent, "Pockets");
        assert.strictEqual(overviewPreviewSectionItem?.textContent, "Add-on: topomt");
        assert.strictEqual(overviewPreviewSectionSubtitle?.textContent, "top_pockets");
        assert.strictEqual(overviewMarker?.textContent, "Current workspace");
        assert.strictEqual(overviewCurrentPanelTitle?.textContent, "Topo");
        assert.strictEqual(overviewCurrentPanelDescription?.textContent, "Pocket analysis");
        assert.strictEqual(overviewCurrentPanelEntry?.textContent, "Entry: topomt.panel.topo");
        assert.strictEqual(overviewPanelButtonTitle?.textContent, "Channels");
        assert.strictEqual(title?.textContent, "TopoMT · Topo");
        assert.strictEqual(entry?.textContent, "Entry: topomt.panel.topo");
        assert.strictEqual(context?.textContent, "Context: Inspect Pocket, Focus Pocket");
        assert.strictEqual(exports?.textContent, "Export: Pocket Figure");
        assert.strictEqual(sectionTitle?.textContent, "Pockets");
        assert.strictEqual(sectionItem?.textContent, "Add-on: topomt");
        assert.strictEqual(sectionSubtitle?.textContent, "top_pockets");

        overviewCard?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");
        overviewPanelButton?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selected, "channels");
        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selected, "channels");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel rows trigger activation when provided", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);
        let activated = 0;

        panel.setVisible(true);
        panel.setAnnotations([{ title: "Picked label", subtitle: "group 12", onActivate: () => { activated += 1; } }]);

        const root = host.children[0];
        const row = findFirstByAttribute(root, "data-molsysviewer-addons-item");
        assert.ok(row);
        row?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(activated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel rows expose visibility toggle when provided", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);
        let toggled = 0;

        panel.setVisible(true);
        panel.setAnnotations([{
            title: "Picked label",
            subtitle: "group 12",
            hidden: true,
            onToggleVisibility: () => { toggled += 1; },
        }]);

        const root = host.children[0];
        const button = findFirstByAttribute(root, "data-molsysviewer-addons-item-visibility", "hidden");
        assert.ok(button);
        assert.strictEqual(button?.textContent, "Show");
        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(toggled, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel sections can collapse and expand", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

        panel.setVisible(true);
        panel.setAnnotations([{ title: "Picked label", subtitle: "group 12" }]);

        const root = host.children[0];
        const toggle = findFirstByAttribute(root, "data-molsysviewer-addons-section-toggle", "annotations");
        const marker = findFirstByAttribute(root, "data-molsysviewer-addons-section-marker", "annotations");
        const section = findFirstByAttribute(root, "data-molsysviewer-addons-section", "annotations");
        const row = findFirstByAttribute(root, "data-molsysviewer-addons-item");
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

test("AddonsPanel exposes shared expanded state API and collapses when hidden", () => {
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

        panel.setVisible(false);
        assert.strictEqual(panel.isExpanded(), false);
        assert.strictEqual(lastExpanded, false);
        assert.strictEqual(root.style.transform, "translateX(240px)");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel header nav button triggers navigate-to-navigate callback", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let navigated = 0;
        const panel = new AddonsPanel(host);
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

test("AddonsPanel exposes workspace launcher when multiple workspaces exist", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let selectedWorkspace: string | null = null;
        const panel = new AddonsPanel(host);
        panel.setWorkspaces(
            [
                { id: "core", title: "Core", subtitle: "Navigate + Workbench", panelCount: 2 },
                { id: "topomt", title: "TopoMT", subtitle: "2 panels · 1 section", panelCount: 2, workbenchSectionCount: 1, workbenchSectionTitles: ["Pockets"], contextActionCount: 1, exportHelperCount: 1 },
                { id: "pharmacophoremt", title: "PharmacophoreMT", subtitle: "3 panels · 2 sections", panelCount: 3, workbenchSectionCount: 2, contextActionCount: 2 },
            ],
            "core",
            (workspaceId) => { selectedWorkspace = workspaceId; },
        );

        panel.setVisible(true);

        const root = host.children[0];
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current", "core");
        const currentMarker = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-marker", "true");
        const currentTitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-title", "true");
        const currentSubtitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-subtitle", "true");
        const launcher = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-launcher", "true");
        const overview = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview", "true");
        const overviewCurrentSection = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-section", "current");
        const overviewAddonSection = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-section", "addons");
        const overviewCard = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card", "topomt");
        const overviewCurrent = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-current", "core");
        const overviewMarker = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-marker", "topomt");
        const overviewCapabilities = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-capabilities", "topomt");
        const overviewSections = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-sections", "topomt");
        const overviewSection = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-section", "topomt:Pockets");
        const overviewCurrentMarker = findFirstByAttribute(root, "data-molsysviewer-addons-workspace-overview-card-marker", "core");
        assert.ok(current);
        assert.ok(currentMarker);
        assert.ok(currentTitle);
        assert.ok(currentSubtitle);
        assert.ok(launcher);
        assert.ok(overview);
        assert.ok(overviewCurrentSection);
        assert.ok(overviewAddonSection);
        assert.ok(overviewCard);
        assert.ok(overviewCurrent);
        assert.ok(overviewMarker);
        assert.ok(overviewCapabilities);
        assert.ok(overviewSections);
        assert.ok(overviewSection);
        assert.ok(overviewCurrentMarker);
        assert.strictEqual(currentMarker?.textContent, "Core workspace");
        assert.strictEqual(currentTitle?.textContent, "Core");
        assert.strictEqual(currentSubtitle?.textContent, "Navigate + Workbench");
        assert.strictEqual(launcher?.getAttribute("data-molsysviewer-panel-workspace-launcher-mode"), "mosaic");
        assert.strictEqual(overviewCurrentSection?.textContent, "Current");
        assert.strictEqual(overviewAddonSection?.textContent, "Add-ons");
        assert.strictEqual(overviewMarker?.textContent, "Open workspace");
        assert.strictEqual(overviewCapabilities?.children.length, 4);
        assert.strictEqual(overviewSection?.textContent, "Pockets");
        assert.strictEqual(overviewCurrentMarker?.textContent, "Current workspace");

        overviewCard?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");
        selectedWorkspace = null;

        current?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const button = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option", "topomt");
        const title = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-title", "topomt");
        const subtitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-subtitle", "topomt");
        const marker = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-marker", "core");
        const other = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option", "pharmacophoremt");
        const coreSection = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-section", "core");
        const addonSection = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-section", "addons");
        assert.ok(button);
        assert.ok(other);
        assert.ok(coreSection);
        assert.ok(addonSection);
        assert.strictEqual(title?.textContent, "TopoMT");
        assert.strictEqual(subtitle?.textContent, "2 panels · 1 section");
        assert.strictEqual(marker?.textContent, "Current");
        assert.strictEqual(coreSection?.textContent, "Core");
        assert.strictEqual(addonSection?.textContent, "Add-ons");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("AddonsPanel supports custom navigation labels", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new AddonsPanel(host);

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
