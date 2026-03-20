import { PanelShell } from "./panel-shell";

type WorkbenchItem = {
    key?: string;
    title: string;
    subtitle?: string;
    hidden?: boolean;
    active?: boolean;
    context?: boolean;
    onActivate?: () => void;
    onToggleVisibility?: () => void;
};

type SceneSummary = {
    styleTag?: string;
    preset?: string;
};

type AddonSummary = {
    name: string;
    workspaceTitles: string[];
    panelTitles: string[];
    workbenchTitles: string[];
    contextActionTitles: string[];
    exportHelperTitles: string[];
    active?: boolean;
};

type AddonWorkbenchSectionSummary = {
    key: string;
    workspaceId: string;
    title: string;
    itemTitle: string;
    itemSubtitle?: string;
};

type WorkspaceOption = { id: string; title: string; subtitle?: string };
type WorkspacePanelOption = {
    id: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
    active?: boolean;
};
type ActiveWorkspacePanelSummary = {
    workspaceTitle: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
};

type BuiltInWorkbenchSectionKey = "annotations" | "measurements" | "shapes" | "scene" | "addons";
type WorkbenchSectionKey = BuiltInWorkbenchSectionKey | `addon:${string}`;

type SectionView = {
    root: HTMLDivElement;
    list: HTMLDivElement;
    empty: HTMLDivElement;
    marker: HTMLSpanElement;
};

export class WorkbenchPanel {
    private readonly shell: PanelShell;
    private readonly root: HTMLDivElement;
    private readonly body: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly workspacePanelHost: HTMLDivElement;
    private readonly workspacePanelHostTitle: HTMLDivElement;
    private readonly workspacePanelHostBody: HTMLDivElement;
    private readonly sections = new Map<WorkbenchSectionKey, SectionView>();
    private readonly sectionExpanded = new Map<WorkbenchSectionKey, boolean>();
    private readonly builtInSectionKeys: BuiltInWorkbenchSectionKey[] = ["annotations", "measurements", "shapes", "scene", "addons"];
    private addonSectionKeys: WorkbenchSectionKey[] = [];
    private expanded = false;
    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToNavigate?: () => void;

    constructor(private readonly host: HTMLElement) {
        this.shell = new PanelShell(host, { title: "Workbench", width: 240, toggleWidth: 26, navButtonLabel: "Navigate" });
        this.root = this.shell.root;
        this.body = this.shell.content;
        this.toggleButton = this.shell.toggleButton;

        this.root.setAttribute("data-molsysviewer-workbench-panel", "true");
        this.shell.titleElement.setAttribute("data-molsysviewer-workbench-panel-title", "true");
        this.body.setAttribute("data-molsysviewer-workbench-panel-body", "true");

        Object.assign(this.root.style, {
            left: "unset",
            right: "0",
            transform: "translateX(240px)",
        });
        Object.assign(this.shell.panel.style, {
            borderLeft: "1px solid rgba(255,255,255,0.14)",
            borderRight: "0",
            borderRadius: "14px 0 0 14px",
        });
        Object.assign(this.toggleButton.style, {
            order: "-1",
            borderLeft: "1px solid rgba(255,255,255,0.16)",
            borderRight: "0",
            borderRadius: "10px 0 0 10px",
            boxShadow: "0 10px 24px rgba(0,0,0,0.18)",
        });

        this.toggleButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.expanded = !this.expanded;
            this.applyExpandedState();
        });
        this.shell.navButton?.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.onNavigateToNavigate?.();
        });

        Object.assign(this.body.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "auto",
            gap: "8px",
        });

        this.workspacePanelHost = document.createElement("div");
        this.workspacePanelHost.setAttribute("data-molsysviewer-workbench-workspace-panel-host", "true");
        Object.assign(this.workspacePanelHost.style, {
            display: "none",
            flexDirection: "column",
            gap: "6px",
            padding: "10px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
        });

        this.workspacePanelHostTitle = document.createElement("div");
        this.workspacePanelHostTitle.setAttribute("data-molsysviewer-workbench-workspace-panel-title", "true");
        Object.assign(this.workspacePanelHostTitle.style, {
            fontSize: "12px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.96)",
        });

        this.workspacePanelHostBody = document.createElement("div");
        this.workspacePanelHostBody.setAttribute("data-molsysviewer-workbench-workspace-panel-body", "true");
        Object.assign(this.workspacePanelHostBody.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            fontSize: "12px",
            color: "rgba(244,244,245,0.78)",
        });

        this.workspacePanelHost.appendChild(this.workspacePanelHostTitle);
        this.workspacePanelHost.appendChild(this.workspacePanelHostBody);
        this.body.appendChild(this.workspacePanelHost);

        this.createSection("annotations", "Annotations", "No annotations yet.");
        this.createSection("measurements", "Measurements", "No measurements yet.");
        this.createSection("shapes", "Shapes", "No shapes yet.");
        this.createSection("scene", "Scene", "No scene style selected.");
        this.createSection("addons", "Add-ons", "No add-ons active.");

        this.applyExpandedState();
        this.setVisible(false);
    }

    setVisible(visible: boolean): void {
        this.shell.setVisible(visible);
        if (!visible && this.expanded) {
            this.expanded = false;
            this.applyExpandedState();
        }
    }

    isVisible(): boolean {
        return this.shell.isVisible();
    }

    setExpanded(expanded: boolean): void {
        this.expanded = expanded;
        this.applyExpandedState();
    }

    isExpanded(): boolean {
        return this.expanded;
    }

    setOnExpandedChange(callback: ((expanded: boolean) => void) | undefined): void {
        this.onExpandedChange = callback;
    }

    setOnNavigateToNavigate(callback: (() => void) | undefined, label = "Navigate"): void {
        this.onNavigateToNavigate = callback;
        this.shell.setNavButtonLabel(callback ? label : undefined);
    }

    setWorkspaces(items: WorkspaceOption[], currentId: string, onSelect: ((workspaceId: string) => void) | undefined): void {
        this.shell.setOnSelectWorkspace(onSelect);
        this.shell.setWorkspaceOptions(items, currentId);
    }

    setWorkspacePanels(
        items: WorkspacePanelOption[],
        onSelect: ((panelId: string) => void) | undefined,
    ): void {
        this.shell.setOnSelectPanel(onSelect);
        this.shell.setPanelOptions(items.map((item) => ({
            id: item.id,
            title: item.title,
            active: item.active,
        })));
    }

    setActiveWorkspacePanel(summary: ActiveWorkspacePanelSummary | null): void {
        this.workspacePanelHostBody.replaceChildren();
        if (!summary) {
            this.workspacePanelHost.style.display = "none";
            return;
        }

        this.workspacePanelHost.style.display = "flex";
        this.workspacePanelHostTitle.textContent = `${summary.workspaceTitle} · ${summary.title}`;

        if (summary.description) {
            const description = document.createElement("div");
            description.setAttribute("data-molsysviewer-workbench-workspace-panel-description", "true");
            description.textContent = summary.description;
            this.workspacePanelHostBody.appendChild(description);
        }
        if (summary.entry) {
            const entry = document.createElement("div");
            entry.setAttribute("data-molsysviewer-workbench-workspace-panel-entry", "true");
            entry.textContent = `Entry: ${summary.entry}`;
            this.workspacePanelHostBody.appendChild(entry);
        }
        if (summary.addon) {
            const addon = document.createElement("div");
            addon.setAttribute("data-molsysviewer-workbench-workspace-panel-addon", "true");
            addon.textContent = `Add-on: ${summary.addon}`;
            this.workspacePanelHostBody.appendChild(addon);
        }
    }

    setAnnotations(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("annotations")!, items);
        this.applySectionExpandedState("annotations");
    }

    setMeasurements(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("measurements")!, items);
        this.applySectionExpandedState("measurements");
    }

    setShapes(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("shapes")!, items);
        this.applySectionExpandedState("shapes");
    }

    setScene(summary: SceneSummary | null): void {
        const items: WorkbenchItem[] = [];
        if (summary?.styleTag) items.push({ title: `Style: ${summary.styleTag}` });
        if (summary?.preset) items.push({ title: `Preset: ${summary.preset}` });
        this.renderItems(this.sections.get("scene")!, items);
        this.applySectionExpandedState("scene");
    }

    setAddons(items: AddonSummary[]): void {
        this.renderItems(
            this.sections.get("addons")!,
            items.map((item) => ({
                key: item.name,
                title: item.name,
                active: item.active,
                subtitle: [
                    item.workspaceTitles.length > 0 ? `Workspaces: ${item.workspaceTitles.join(", ")}` : null,
                    item.panelTitles.length > 0 ? `Panels: ${item.panelTitles.join(", ")}` : null,
                    item.workbenchTitles.length > 0 ? `Workbench: ${item.workbenchTitles.join(", ")}` : null,
                    item.contextActionTitles.length > 0 ? `Context: ${item.contextActionTitles.join(", ")}` : null,
                    item.exportHelperTitles.length > 0 ? `Export: ${item.exportHelperTitles.join(", ")}` : null,
                ].filter(Boolean).join(" · "),
            })),
        );
        this.applySectionExpandedState("addons");
    }

    setAddonWorkbenchSections(items: AddonWorkbenchSectionSummary[]): void {
        const nextKeys = new Set<WorkbenchSectionKey>();
        for (const item of items) {
            const key = (`addon:${item.key}`) as WorkbenchSectionKey;
            nextKeys.add(key);
            if (!this.sections.has(key)) {
                this.createSection(key, item.title, "Add-on section registered.");
            }
            const section = this.sections.get(key)!;
            this.renderItems(section, [{ key: item.key, title: item.itemTitle, subtitle: item.itemSubtitle }]);
            this.applySectionExpandedState(key);
        }

        for (const key of this.addonSectionKeys) {
            if (nextKeys.has(key)) continue;
            const section = this.sections.get(key);
            section?.root.remove();
            this.sections.delete(key);
            this.sectionExpanded.delete(key);
        }

        this.addonSectionKeys = Array.from(nextKeys);
        this.reorderSections();
    }

    dispose(): void {
        this.shell.dispose();
    }

    private applyExpandedState(): void {
        this.toggleButton.textContent = this.expanded ? ">" : "<";
        this.root.style.transform = this.expanded ? "translateX(0)" : "translateX(240px)";
        this.onExpandedChange?.(this.expanded);
    }

    private createSection(key: WorkbenchSectionKey, title: string, emptyText: string): SectionView {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-workbench-section", key);
        Object.assign(section.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "8px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
        });

        const header = document.createElement("button");
        header.type = "button";
        header.setAttribute("data-molsysviewer-workbench-section-toggle", key);
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.88)",
            background: "transparent",
            border: "0",
            padding: "0",
            cursor: "pointer",
            textAlign: "left",
        });
        const headerTitle = document.createElement("span");
        headerTitle.textContent = title;
        const headerMarker = document.createElement("span");
        headerMarker.setAttribute("data-molsysviewer-workbench-section-marker", key);
        headerMarker.textContent = "−";
        Object.assign(headerMarker.style, {
            color: "rgba(244,244,245,0.52)",
            fontSize: "12px",
            lineHeight: "1",
        });
        header.appendChild(headerTitle);
        header.appendChild(headerMarker);
        header.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.sectionExpanded.set(key, !(this.sectionExpanded.get(key) ?? true));
            this.applySectionExpandedState(key);
        });

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const empty = document.createElement("div");
        empty.setAttribute("data-molsysviewer-workbench-empty", title.toLowerCase());
        Object.assign(empty.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.56)",
        });
        empty.textContent = emptyText;

        section.appendChild(header);
        section.appendChild(list);
        section.appendChild(empty);
        this.body.appendChild(section);

        const view = { root: section, list, empty, marker: headerMarker };
        this.sections.set(key, view);
        this.sectionExpanded.set(key, true);
        return view;
    }

    private renderItems(section: SectionView, items: WorkbenchItem[]): void {
        section.list.replaceChildren();
        if (items.length === 0) {
            section.empty.style.display = "block";
            return;
        }
        section.empty.style.display = "none";
        for (const item of items) {
            section.list.appendChild(this.makeRow(item));
        }
    }

    private applySectionExpandedState(key: WorkbenchSectionKey): void {
        const section = this.sections.get(key);
        if (!section) return;
        const expanded = this.sectionExpanded.get(key) ?? true;
        section.marker.textContent = expanded ? "−" : "+";
        section.list.style.display = expanded ? "flex" : "none";
        const hasItems = section.list.children.length > 0;
        section.empty.style.display = expanded && !hasItems ? "block" : "none";
    }

    private reorderSections(): void {
        const orderedKeys: WorkbenchSectionKey[] = [
            ...this.builtInSectionKeys,
            ...this.addonSectionKeys.sort((left, right) => left.localeCompare(right)),
        ];
        for (const key of orderedKeys) {
            const section = this.sections.get(key);
            if (section) this.body.appendChild(section.root);
        }
    }

    private makeRow(item: WorkbenchItem): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-workbench-item", "true");
        if (item.key) row.setAttribute("data-molsysviewer-workbench-item-key", item.key);
        if (item.active) row.setAttribute("data-molsysviewer-workbench-item-active", "true");
        if (item.context) row.setAttribute("data-molsysviewer-workbench-item-context", "true");
        Object.assign(row.style, {
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            padding: "6px 8px",
            borderRadius: "8px",
            background: item.active
                ? "rgba(255,255,255,0.12)"
                : item.context
                    ? "rgba(255,255,255,0.08)"
                : item.hidden
                    ? "rgba(255,255,255,0.03)"
                    : "rgba(255,255,255,0.06)",
            color: item.hidden ? "rgba(244,244,245,0.58)" : "#f4f4f5",
            cursor: item.onActivate ? "pointer" : "default",
            outline: item.active
                ? "1px solid rgba(255,255,255,0.16)"
                : item.context
                    ? "1px solid rgba(255,255,255,0.10)"
                    : "none",
        });
        if (item.onActivate) {
            row.addEventListener("click", (event) => {
                event.preventDefault?.();
                event.stopPropagation?.();
                item.onActivate?.();
            });
        }

        const top = document.createElement("div");
        Object.assign(top.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
        });

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "600",
            flex: "1 1 auto",
        });
        title.textContent = item.title;
        top.appendChild(title);

        if (item.onToggleVisibility) {
            const visibilityButton = document.createElement("button");
            visibilityButton.type = "button";
            visibilityButton.setAttribute("data-molsysviewer-workbench-item-visibility", item.hidden ? "hidden" : "visible");
            visibilityButton.textContent = item.hidden ? "Show" : "Hide";
            Object.assign(visibilityButton.style, {
                fontSize: "10px",
                color: "rgba(244,244,245,0.72)",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)",
                borderRadius: "999px",
                padding: "1px 6px",
                cursor: "pointer",
            });
            visibilityButton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                item.onToggleVisibility?.();
            });
            top.appendChild(visibilityButton);
        }

        row.appendChild(top);

        if (item.subtitle) {
            const subtitle = document.createElement("div");
            Object.assign(subtitle.style, {
                fontSize: "11px",
                color: item.hidden ? "rgba(244,244,245,0.45)" : "rgba(244,244,245,0.68)",
            });
            subtitle.textContent = item.subtitle;
            row.appendChild(subtitle);
        }

        return row;
    }
}
