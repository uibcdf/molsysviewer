import { PanelShell } from "./panel-shell";
import { FloatingPanelShell } from "./floating-panel-shell";

export type AddonDiagnosticSummary = {
    kind?: string;
    source: string;
    reason: string;
    traceback?: string;
};

export type WorkspaceOption = {
    id: string;
    title: string;
    subtitle?: string;
    panelCount?: number;
    workbenchSectionCount?: number;
    workbenchSectionTitles?: string[];
    contextActionCount?: number;
    exportHelperCount?: number;
    description?: string; // Add-on description
};

export type WorkspacePanelOption = {
    id: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
    active?: boolean;
};

export type ActiveWorkspacePanelSummary = {
    workspaceTitle: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
    contextActionTitles?: string[];
    exportHelperTitles?: string[];
    sections?: Array<{
        key: string;
        title: string;
        itemTitle: string;
        itemSubtitle?: string;
    }>;
};

export class AddonsPanel {
    private readonly shell: PanelShell | FloatingPanelShell;
    private readonly root: HTMLDivElement;
    private readonly body: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;

    // Two-column layout columns
    private readonly leftColumn: HTMLDivElement;
    private readonly rightColumn: HTMLDivElement;

    // Content Hosts
    private readonly workspaceOverviewHost: HTMLDivElement;
    private readonly addonsWidgetHost: HTMLDivElement;

    // State
    private workspaceItems: WorkspaceOption[] = [];
    private workspacePanelItems: WorkspacePanelOption[] = [];
    private currentWorkspaceId = "core";
    private activeWorkspacePanelSummary: ActiveWorkspacePanelSummary | null = null;
    private addonDiagnostics: AddonDiagnosticSummary[] = [];

    private onSelectWorkspace?: (workspaceId: string) => void;
    private onSelectWorkspacePanel?: (panelId: string) => void;
    private expanded = false;
    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToNavigate?: () => void;
    private readonly floating: boolean;
    private readonly sharedShell: boolean;
    private visible = false;

    constructor(private readonly host: HTMLElement, options?: { floating?: boolean; sharedShell?: FloatingPanelShell }) {
        const floating = options?.floating || !!options?.sharedShell;
        this.floating = floating;
        this.sharedShell = !!options?.sharedShell;
        this.shell = options?.sharedShell
            ? options.sharedShell
            : (floating
                ? new FloatingPanelShell(host, { title: "Add-ons", navButtonLabel: "Navigate" })
                : new PanelShell(host, { title: "Add-ons", width: 560, toggleWidth: 26, navButtonLabel: "Navigate" }));
        this.root = this.shell.root;
        this.toggleButton = this.shell.toggleButton;

        if (options?.sharedShell) {
            this.body = document.createElement("div");
            Object.assign(this.body.style, {
                display: "none",
                flexDirection: "row",
                overflow: "hidden",
                gap: "0",
                width: "100%",
                height: "100%",
            });
            this.shell.content.appendChild(this.body);
        } else {
            this.body = this.shell.content;
            Object.assign(this.body.style, {
                flexDirection: "row",
                overflow: "hidden",
                gap: "0",
            });
        }

        this.root.setAttribute("data-molsysviewer-addons-panel", "true");
        this.shell.titleElement.setAttribute("data-molsysviewer-addons-panel-title", "true");
        this.body.setAttribute("data-molsysviewer-addons-panel-body", "true");

        if (!floating) {
            Object.assign(this.root.style, {
                left: "unset",
                right: "0",
                transform: `translateX(${(this.shell as PanelShell).width}px)`,
            });
            Object.assign((this.shell as PanelShell).panel.style, {
                borderLeft: "1px solid rgba(255,255,255,0.14)",
                borderRight: "0",
                borderRadius: "14px 0 0 14px",
            });
            Object.assign(this.toggleButton.style, {
                order: "-1",
                borderLeft: "1px solid rgba(255,255,255,0.14)",
                borderRight: "0",
                borderRadius: "10px 0 0 10px",
            });
        }

        if (!this.sharedShell) {
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
        }

        // ── Left column: Navigation Tabs (Addon Sections) ───────────
        this.leftColumn = document.createElement("div");
        this.leftColumn.setAttribute("data-molsysviewer-addons-panel-left", "true");
        Object.assign(this.leftColumn.style, {
            display: "none",
            flexDirection: "column",
            gap: "8px",
            width: "180px",
            minWidth: "180px",
            overflowY: "auto",
            overflowX: "hidden",
            paddingRight: "8px",
            borderRight: "1px solid rgba(255,255,255,0.06)",
        });
        this.body.appendChild(this.leftColumn);

        // ── Right column: Content Viewport ──────────────────────────
        this.rightColumn = document.createElement("div");
        this.rightColumn.setAttribute("data-molsysviewer-addons-panel-right", "true");
        Object.assign(this.rightColumn.style, {
            display: "flex",
            flexDirection: "column",
            flex: "1 1 0",
            minWidth: "0",
            overflow: "hidden",
        });
        this.body.appendChild(this.rightColumn);

        // Catalog grid container
        this.workspaceOverviewHost = document.createElement("div");
        this.workspaceOverviewHost.setAttribute("data-molsysviewer-addons-workspace-overview", "true");
        Object.assign(this.workspaceOverviewHost.style, {
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            flex: "1 1 0",
            overflowY: "auto",
            paddingRight: "4px",
        });
        this.rightColumn.appendChild(this.workspaceOverviewHost);

        // Widget host
        this.addonsWidgetHost = document.createElement("div");
        this.addonsWidgetHost.setAttribute("data-molsysviewer-addon-widget-host", "true");
        Object.assign(this.addonsWidgetHost.style, {
            display: "none",
            flexDirection: "column",
            flex: "1 1 0",
            overflowY: "auto",
        });
        this.rightColumn.appendChild(this.addonsWidgetHost);

        this.applyExpandedState();
        this.setVisible(!floating);
    }

    setVisible(visible: boolean): void {
        this.visible = visible;
        this.updateBodyDisplay();
        if (!this.sharedShell && !visible && this.expanded) {
            this.expanded = false;
            this.applyExpandedState();
        }
    }

    get panelContentWidth(): number {
        return this.shell.width;
    }

    isVisible(): boolean {
        return this.visible;
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
        if (!this.sharedShell) {
            this.shell.setNavButtonLabel(callback ? label : undefined);
        }
    }

    setWorkspaces(items: WorkspaceOption[], currentId: string, onSelect: ((workspaceId: string) => void) | undefined): void {
        this.workspaceItems = Array.isArray(items) ? items : [];
        this.currentWorkspaceId = currentId;
        this.onSelectWorkspace = onSelect;
        this.shell.setOnSelectWorkspace(onSelect);
        this.shell.setWorkspaceOptions(items, currentId);
        this.render();
    }

    setWorkspacePanels(items: WorkspacePanelOption[], onSelect: ((panelId: string) => void) | undefined): void {
        this.workspacePanelItems = Array.isArray(items) ? items : [];
        this.onSelectWorkspacePanel = onSelect;
        if (!this.sharedShell) {
            this.shell.setOnSelectPanel(onSelect);
            this.shell.setPanelOptions(items.map((item) => ({
                id: item.id,
                title: item.title,
                active: item.active,
            })));
        }
        this.render();
    }

    setActiveWorkspacePanel(summary: ActiveWorkspacePanelSummary | null): void {
        this.activeWorkspacePanelSummary = summary;
        this.render();
    }

    setAddonDiagnostics(items: AddonDiagnosticSummary[]): void {
        this.addonDiagnostics = Array.isArray(items) ? items : [];
        this.render();
    }

    // Stubs to keep full API compatibility with viewer-controller.ts
    setAnnotations(_items: any[]): void {}
    setMeasurements(_items: any[]): void {}
    setShapes(_items: any[]): void {}
    setScene(_summary: any): void {}
    setAddons(_items: any[]): void {}
    setAddonWorkbenchSections(_items: any[]): void {}

    mountAddonWidget(el: HTMLElement): void {
        this.addonsWidgetHost.replaceChildren(el);
        this.addonsWidgetHost.style.display = "flex";
        this.workspaceOverviewHost.style.display = "none";
    }

    unmountAddonWidget(): void {
        this.addonsWidgetHost.replaceChildren();
        this.addonsWidgetHost.style.display = "none";
        this.workspaceOverviewHost.style.display = "flex";
    }

    dispose(): void {
        if (!this.sharedShell) {
            this.shell.dispose();
        }
    }

    private updateBodyDisplay(): void {
        if (this.sharedShell) {
            this.body.style.display = (this.visible && this.expanded) ? "flex" : "none";
        } else {
            this.shell.setVisible(this.visible);
        }
    }

    private applyExpandedState(): void {
        if (this.floating) {
            if (this.sharedShell) {
                this.updateBodyDisplay();
            } else {
                this.shell.setExpanded(this.expanded);
            }
        } else {
            this.toggleButton.textContent = this.expanded ? ">" : "<";
            this.root.style.transform = this.expanded ? "translateX(0)" : `translateX(${this.shell.width}px)`;
        }
        this.onExpandedChange?.(this.expanded);
    }

    private render(): void {
        const isCore = this.currentWorkspaceId === "core";

        if (isCore) {
            this.leftColumn.style.display = "none";
            this.rightColumn.style.paddingLeft = "0";
            this.workspaceOverviewHost.style.display = "flex";
            this.renderCatalogView();
        } else {
            this.leftColumn.style.display = "flex";
            this.rightColumn.style.paddingLeft = "12px";
            this.workspaceOverviewHost.style.display = "none";
            this.renderAddonWorkspaceView();
        }
    }

    // ── Catalog Screen Rendering ──────────────────────────────────
    private renderCatalogView(): void {
        this.workspaceOverviewHost.replaceChildren();

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "13px",
            fontWeight: "700",
            color: "#f4f4f5",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            paddingBottom: "6px",
            marginBottom: "4px",
        });
        title.textContent = "Available Add-ons";
        this.workspaceOverviewHost.appendChild(title);

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "12px",
            width: "100%",
        });
        this.workspaceOverviewHost.appendChild(grid);

        // Filter out "core" from catalog display
        const addonItems = this.workspaceItems.filter((item) => item.id !== "core");

        if (addonItems.length === 0 && this.addonDiagnostics.length === 0) {
            const empty = document.createElement("div");
            Object.assign(empty.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                textAlign: "center",
                padding: "20px 0",
            });
            empty.textContent = "No analytical add-ons registered.";
            this.workspaceOverviewHost.appendChild(empty);
            return;
        }

        // Render successfully discovered add-ons
        for (const item of addonItems) {
            // Find if there is a loading/discovery diagnostic failure for this addon
            const failure = this.addonDiagnostics.find(
                (d) => d.source.toLowerCase().includes(item.id.toLowerCase())
            );

            const card = document.createElement("button");
            card.type = "button";
            card.setAttribute("data-molsysviewer-addon-card", item.id);
            
            Object.assign(card.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "stretch",
                gap: "8px",
                padding: "12px",
                borderRadius: "10px",
                textAlign: "left",
                cursor: "pointer",
                transition: "all 0.15s ease-in-out",
            });

            if (failure) {
                // Failure card: styling red
                card.setAttribute("data-molsysviewer-addons-addon-discovery-failure", item.id);
                Object.assign(card.style, {
                    background: "rgba(239,68,68,0.03)",
                    border: "1px solid rgba(239,68,68,0.25)",
                    color: "#fca5a5",
                });
                card.title = failure.traceback || "Diagnostic traceback unavailable";

                // Error badge
                const header = document.createElement("div");
                Object.assign(header.style, {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                });
                const name = document.createElement("span");
                Object.assign(name.style, { fontWeight: "700", fontSize: "13px" });
                name.textContent = item.title;
                const badge = document.createElement("span");
                Object.assign(badge.style, {
                    fontSize: "9px",
                    background: "rgba(239,68,68,0.2)",
                    border: "1px solid rgba(239,68,68,0.4)",
                    color: "#ef4444",
                    borderRadius: "4px",
                    padding: "1px 5px",
                    fontWeight: "700",
                    textTransform: "uppercase",
                });
                badge.textContent = failure.kind === "lifecycle" ? "Lifecycle Error" : "Discovery Error";
                header.appendChild(name);
                header.appendChild(badge);
                card.appendChild(header);

                // Short reason
                const desc = document.createElement("div");
                Object.assign(desc.style, { fontSize: "11px", color: "rgba(252,165,165,0.72)", lineHeight: "1.3" });
                desc.textContent = failure.reason || "Error loading addon.";
                card.appendChild(desc);

                // Collapsible traceback viewer on click
                const traceBox = document.createElement("pre");
                Object.assign(traceBox.style, {
                    display: "none",
                    margin: "6px 0 0 0",
                    padding: "8px",
                    borderRadius: "6px",
                    background: "rgba(0,0,0,0.3)",
                    border: "1px solid rgba(239,68,68,0.15)",
                    fontSize: "9px",
                    color: "rgba(252,165,165,0.9)",
                    overflowX: "auto",
                    whiteSpace: "pre-wrap",
                });
                traceBox.textContent = failure.traceback || "No traceback detail.";
                card.appendChild(traceBox);

                card.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const isVisible = traceBox.style.display === "block";
                    traceBox.style.display = isVisible ? "none" : "block";
                });
            } else {
                // Success card: styling standard dark-indigo
                Object.assign(card.style, {
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "#f4f4f5",
                });
                card.addEventListener("mouseenter", () => {
                    card.style.background = "rgba(255,255,255,0.06)";
                    card.style.border = "1px solid rgba(255,255,255,0.14)";
                    card.style.transform = "translateY(-1px)";
                });
                card.addEventListener("mouseleave", () => {
                    card.style.background = "rgba(255,255,255,0.03)";
                    card.style.border = "1px solid rgba(255,255,255,0.08)";
                    card.style.transform = "translateY(0)";
                });

                const name = document.createElement("div");
                Object.assign(name.style, { fontWeight: "700", fontSize: "13px" });
                name.textContent = item.title;
                card.appendChild(name);

                if (item.subtitle || item.description) {
                    const desc = document.createElement("div");
                    Object.assign(desc.style, {
                        fontSize: "11px",
                        color: "rgba(244,244,245,0.58)",
                        lineHeight: "1.35",
                    });
                    desc.textContent = item.description || item.subtitle || "";
                    card.appendChild(desc);
                }

                // Capabilities chips
                const chipRow = document.createElement("div");
                Object.assign(chipRow.style, { display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "4px" });
                card.appendChild(chipRow);

                const createChip = (text: string) => {
                    const chip = document.createElement("span");
                    Object.assign(chip.style, {
                        fontSize: "9px",
                        fontWeight: "700",
                        padding: "2px 6px",
                        borderRadius: "99px",
                        background: "rgba(255,255,255,0.05)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        color: "rgba(244,244,245,0.64)",
                    });
                    chip.textContent = text;
                    chipRow.appendChild(chip);
                };

                if ((item.panelCount ?? 0) > 0) createChip(`${item.panelCount} Panel${item.panelCount === 1 ? "" : "s"}`);
                if ((item.workbenchSectionCount ?? 0) > 0) createChip(`${item.workbenchSectionCount} Section${item.workbenchSectionCount === 1 ? "" : "s"}`);
                if ((item.contextActionCount ?? 0) > 0) createChip(`${item.contextActionCount} Context`);

                card.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.onSelectWorkspace?.(item.id);
                });
            }

            grid.appendChild(card);
        }

        // Render standalone diagnostics failures that don't match listed workspaces
        for (const failure of this.addonDiagnostics) {
            const isMatched = addonItems.some((item) => failure.source.toLowerCase().includes(item.id.toLowerCase()));
            if (isMatched) continue;

            const card = document.createElement("button");
            card.type = "button";
            card.setAttribute("data-molsysviewer-addons-addon-discovery-failure", failure.source);
            Object.assign(card.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "stretch",
                gap: "8px",
                padding: "12px",
                borderRadius: "10px",
                background: "rgba(239,68,68,0.03)",
                border: "1px solid rgba(239,68,68,0.25)",
                color: "#fca5a5",
                textAlign: "left",
                cursor: "pointer",
            });

            const header = document.createElement("div");
            Object.assign(header.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
            const name = document.createElement("span");
            Object.assign(name.style, { fontWeight: "700", fontSize: "13px" });
            name.textContent = failure.source;
            const badge = document.createElement("span");
            Object.assign(badge.style, {
                fontSize: "9px",
                background: "rgba(239,68,68,0.2)",
                border: "1px solid rgba(239,68,68,0.4)",
                color: "#ef4444",
                borderRadius: "4px",
                padding: "1px 5px",
                fontWeight: "700",
                textTransform: "uppercase",
            });
            badge.textContent = failure.kind === "lifecycle" ? "Lifecycle Error" : "Discovery Error";
            header.appendChild(name);
            header.appendChild(badge);
            card.appendChild(header);

            const desc = document.createElement("div");
            Object.assign(desc.style, { fontSize: "11px", color: "rgba(252,165,165,0.72)", lineHeight: "1.3" });
            desc.textContent = failure.reason || "Error loading entry point.";
            card.appendChild(desc);

            const traceBox = document.createElement("pre");
            Object.assign(traceBox.style, {
                display: "none",
                margin: "6px 0 0 0",
                padding: "8px",
                borderRadius: "6px",
                background: "rgba(0,0,0,0.3)",
                border: "1px solid rgba(239,68,68,0.15)",
                fontSize: "9px",
                color: "rgba(252,165,165,0.9)",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
            });
            traceBox.textContent = failure.traceback || "No traceback detail.";
            card.appendChild(traceBox);

            card.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                const isVisible = traceBox.style.display === "block";
                traceBox.style.display = isVisible ? "none" : "block";
            });

            grid.appendChild(card);
        }
    }

    // ── Active Addon Workspace view (Sidebar + Widget area) ────────
    private renderAddonWorkspaceView(): void {
        this.leftColumn.replaceChildren();

        // 1. Back button
        const backBtn = document.createElement("button");
        backBtn.type = "button";
        backBtn.setAttribute("data-molsysviewer-addon-back-button", "true");
        Object.assign(backBtn.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            width: "100%",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.1)",
            background: "rgba(255,255,255,0.04)",
            color: "#f4f4f5",
            fontSize: "11px",
            fontWeight: "700",
            cursor: "pointer",
            marginBottom: "12px",
            transition: "all 0.15s ease",
        });
        backBtn.textContent = "← Back to Add-ons";

        backBtn.addEventListener("mouseenter", () => {
            backBtn.style.background = "rgba(255,255,255,0.08)";
            backBtn.style.border = "1px solid rgba(255,255,255,0.16)";
        });
        backBtn.addEventListener("mouseleave", () => {
            backBtn.style.background = "rgba(255,255,255,0.04)";
            backBtn.style.border = "1px solid rgba(255,255,255,0.1)";
        });
        backBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.onSelectWorkspace?.("core");
        });

        this.leftColumn.appendChild(backBtn);

        // 2. Sections header title
        const sectionsHeader = document.createElement("div");
        Object.assign(sectionsHeader.style, {
            fontSize: "10px",
            fontWeight: "700",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "rgba(244,244,245,0.48)",
            paddingLeft: "4px",
            marginBottom: "6px",
        });
        sectionsHeader.textContent = "Add-on Sections";
        this.leftColumn.appendChild(sectionsHeader);

        // 3. Sections vertical menu
        const menuContainer = document.createElement("div");
        Object.assign(menuContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
        });
        this.leftColumn.appendChild(menuContainer);

        // Render sections (filtering out navigate and addons tabs which belong to main shell)
        const relevantSections = this.workspacePanelItems.filter(
            (item) => item.id !== "navigate" && item.id !== "addons"
        );

        for (const panel of relevantSections) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("data-molsysviewer-addon-section-tab", panel.id);
            Object.assign(btn.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                gap: "2px",
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                border: "0",
                background: "transparent",
                color: "rgba(244,244,245,0.68)",
                textAlign: "left",
                cursor: "pointer",
                transition: "all 0.15s ease-in-out",
            });

            if (panel.active) {
                Object.assign(btn.style, {
                    background: "rgba(255,255,255,0.08)",
                    color: "#f4f4f5",
                    borderLeft: "3px solid #6366f1",
                    paddingLeft: "9px",
                });
            } else {
                btn.addEventListener("mouseenter", () => {
                    btn.style.background = "rgba(255,255,255,0.04)";
                    btn.style.color = "rgba(244,244,245,0.9)";
                });
                btn.addEventListener("mouseleave", () => {
                    btn.style.background = "transparent";
                    btn.style.color = "rgba(244,244,245,0.68)";
                });
            }

            const title = document.createElement("div");
            Object.assign(title.style, { fontSize: "12px", fontWeight: "600" });
            title.textContent = panel.title;
            btn.appendChild(title);

            if (panel.description) {
                const sub = document.createElement("div");
                Object.assign(sub.style, {
                    fontSize: "10px",
                    color: panel.active ? "rgba(244,244,245,0.6)" : "rgba(244,244,245,0.44)",
                });
                sub.textContent = panel.description;
                btn.appendChild(sub);
            }

            btn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.onSelectWorkspacePanel?.(panel.id);
            });

            menuContainer.appendChild(btn);
        }
    }
}
