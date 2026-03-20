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
    panelTitles: string[];
    workbenchTitles: string[];
    contextActionTitles: string[];
    exportHelperTitles: string[];
};

type WorkbenchSectionKey = "annotations" | "measurements" | "shapes" | "scene" | "addons";

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
    private readonly sections: Record<WorkbenchSectionKey, SectionView>;
    private readonly sectionExpanded: Record<WorkbenchSectionKey, boolean>;
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

        this.sections = {
            annotations: this.createSection("Annotations", "No annotations yet."),
            measurements: this.createSection("Measurements", "No measurements yet."),
            shapes: this.createSection("Shapes", "No shapes yet."),
            scene: this.createSection("Scene", "No scene style selected."),
            addons: this.createSection("Add-ons", "No add-ons active."),
        };
        this.sectionExpanded = {
            annotations: true,
            measurements: true,
            shapes: true,
            scene: true,
            addons: true,
        };

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

    setOnNavigateToNavigate(callback: (() => void) | undefined): void {
        this.onNavigateToNavigate = callback;
        this.shell.setNavButtonLabel(callback ? "Navigate" : undefined);
    }

    setAnnotations(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.annotations, items);
        this.applySectionExpandedState("annotations");
    }

    setMeasurements(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.measurements, items);
        this.applySectionExpandedState("measurements");
    }

    setShapes(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.shapes, items);
        this.applySectionExpandedState("shapes");
    }

    setScene(summary: SceneSummary | null): void {
        const items: WorkbenchItem[] = [];
        if (summary?.styleTag) items.push({ title: `Style: ${summary.styleTag}` });
        if (summary?.preset) items.push({ title: `Preset: ${summary.preset}` });
        this.renderItems(this.sections.scene, items);
        this.applySectionExpandedState("scene");
    }

    setAddons(items: AddonSummary[]): void {
        this.renderItems(
            this.sections.addons,
            items.map((item) => ({
                key: item.name,
                title: item.name,
                subtitle: [
                    item.panelTitles.length > 0 ? `Panels: ${item.panelTitles.join(", ")}` : null,
                    item.workbenchTitles.length > 0 ? `Workbench: ${item.workbenchTitles.join(", ")}` : null,
                    item.contextActionTitles.length > 0 ? `Context: ${item.contextActionTitles.join(", ")}` : null,
                    item.exportHelperTitles.length > 0 ? `Export: ${item.exportHelperTitles.join(", ")}` : null,
                ].filter(Boolean).join(" · "),
            })),
        );
        this.applySectionExpandedState("addons");
    }

    dispose(): void {
        this.shell.dispose();
    }

    private applyExpandedState(): void {
        this.toggleButton.textContent = this.expanded ? ">" : "<";
        this.root.style.transform = this.expanded ? "translateX(0)" : "translateX(240px)";
        this.onExpandedChange?.(this.expanded);
    }

    private createSection(title: string, emptyText: string): SectionView {
        const key = title.toLowerCase() as WorkbenchSectionKey;
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
            this.sectionExpanded[key] = !this.sectionExpanded[key];
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

        return { root: section, list, empty, marker: headerMarker };
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
        const section = this.sections[key];
        const expanded = this.sectionExpanded[key];
        section.marker.textContent = expanded ? "−" : "+";
        section.list.style.display = expanded ? "flex" : "none";
        const hasItems = section.list.children.length > 0;
        section.empty.style.display = expanded && !hasItems ? "block" : "none";
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
