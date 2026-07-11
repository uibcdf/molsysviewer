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
    addon?: string; // The add-on this workspace belongs to
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

// The stack of panels handed to the shell (structurally matches the shells'
// own PanelOption). Declared here so setPanelStack is typed rather than `any`.
export type PanelOption = {
    id: string;
    title: string;
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
    private readonly addonHeaderHost: HTMLDivElement;
    private readonly addonsWidgetHost: HTMLDivElement;

    // State
    private workspaceItems: WorkspaceOption[] = [];
    private workspacePanelItems: WorkspacePanelOption[] = [];
    private addonsList: any[] = [];
    private currentWorkspaceId = "core";
    private activeWorkspacePanelSummary: ActiveWorkspacePanelSummary | null = null;
    private addonDiagnostics: AddonDiagnosticSummary[] = [];
    private activeSectionKey: string | null = null;
    private widgetObserver: MutationObserver | null = null;

    private onSelectWorkspace?: (workspaceId: string) => void;
    private onSelectWorkspacePanel?: (panelId: string) => void;
    private expanded = false;
    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToNavigate?: () => void;
    private readonly floating: boolean;
    private readonly sharedShell: boolean;
    private readonly onAction?: (action: string, payload: any) => void;
    private readonly model?: any;
    private visible = false;

    constructor(private readonly host: HTMLElement, options?: { floating?: boolean; sharedShell?: FloatingPanelShell; onAction?: (action: string, payload: any) => void; model?: any }) {
        const floating = options?.floating || !!options?.sharedShell;
        this.floating = floating;
        this.sharedShell = !!options?.sharedShell;
        this.onAction = options?.onAction;
        this.model = options?.model;
        this.shell = options?.sharedShell
            ? options.sharedShell
            : (floating
                ? new FloatingPanelShell(host, { title: "Add-ons", navButtonLabel: "Studio" })
                : new PanelShell(host, { title: "Add-ons", width: 560, toggleWidth: 26, navButtonLabel: "Studio" }));
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
            display: "flex",
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
            paddingLeft: "12px",
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

        // Header host
        this.addonHeaderHost = document.createElement("div");
        this.addonHeaderHost.setAttribute("data-molsysviewer-addon-header-host", "true");
        Object.assign(this.addonHeaderHost.style, {
            display: "none",
            flexDirection: "column",
            gap: "6px",
            paddingBottom: "8px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            marginBottom: "8px",
            flex: "0 0 auto",
        });
        this.rightColumn.appendChild(this.addonHeaderHost);

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

        // Initialize MutationObserver for dynamic section updates in widget
        if (typeof MutationObserver !== "undefined") {
            this.widgetObserver = new MutationObserver(() => {
                this.applySectionVisibilityFilter();
            });
            this.widgetObserver.observe(this.addonsWidgetHost, { childList: true, subtree: true });
        }

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

    setOnNavigateToNavigate(callback: (() => void) | undefined, label = "Studio"): void {
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
        this.render();
    }

    setPanelStack(items: PanelOption[], onSelect: ((panelId: string) => void) | undefined): void {
        if (!this.sharedShell) {
            this.shell.setOnSelectPanel(onSelect);
            this.shell.setPanelOptions(items);
        }
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
    setAddons(items: any[]): void {
        this.addonsList = Array.isArray(items) ? items : [];
        this.render();
    }
    setAddonWorkbenchSections(_items: any[]): void {}

    mountAddonWidget(el: HTMLElement): void {
        this.addonsWidgetHost.replaceChildren(el);
        this.addonsWidgetHost.style.display = "flex";
        this.workspaceOverviewHost.style.display = "none";
        this.applySectionVisibilityFilter();
    }

    unmountAddonWidget(): void {
        this.addonsWidgetHost.replaceChildren();
        this.addonsWidgetHost.style.display = "none";
        this.workspaceOverviewHost.style.display = "flex";
        this.activeSectionKey = null;
    }

    unmountAddonWidgetOnly(): void {
        this.addonsWidgetHost.replaceChildren();
    }

    dispose(): void {
        if (this.widgetObserver) {
            this.widgetObserver.disconnect();
            this.widgetObserver = null;
        }
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
        this.renderLeftNavigation();

        const isCore = this.currentWorkspaceId === "core";
        if (isCore) {
            this.addonHeaderHost.style.display = "none";
            this.addonsWidgetHost.style.display = "none";
            this.workspaceOverviewHost.style.display = "flex";
            this.renderCatalogView();
        } else {
            this.workspaceOverviewHost.style.display = "none";
            this.addonHeaderHost.style.display = "flex";
            this.addonsWidgetHost.style.display = "flex";

            const activeWorkspace = this.workspaceItems.find((item) => item.id === this.currentWorkspaceId);
            if (activeWorkspace) {
                this.renderAddonHeader(activeWorkspace);
            }
            this.applySectionVisibilityFilter();
        }
    }

    // ── Catalog Screen Rendering ──────────────────────────────────
    private renderCatalogView(): void {
        this.workspaceOverviewHost.replaceChildren();

        // 1. Header with title & subtext
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            paddingBottom: "8px",
            marginBottom: "12px",
            flex: "0 0 auto",
        });
        this.workspaceOverviewHost.appendChild(header);

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "13px",
            fontWeight: "700",
            color: "#f4f4f5",
        });
        title.textContent = "Settings & Extensions";
        header.appendChild(title);

        const subtitle = document.createElement("div");
        Object.assign(subtitle.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.48)",
        });
        subtitle.textContent = "Configure global viewer options, manage analytical extensions, and register custom modules.";
        header.appendChild(subtitle);

        // 2. Global Actions Row
        const actionsRow = document.createElement("div");
        Object.assign(actionsRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "12px",
        });
        this.workspaceOverviewHost.appendChild(actionsRow);

        const rescanBtn = document.createElement("button");
        rescanBtn.type = "button";
        Object.assign(rescanBtn.style, {
            padding: "4px 8px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "4px",
            color: "rgba(244,244,245,0.78)",
            fontSize: "10px",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.15s ease",
        });
        rescanBtn.textContent = "⟳ Autodetect";
        rescanBtn.addEventListener("mouseenter", () => {
            rescanBtn.style.background = "rgba(255,255,255,0.08)";
            rescanBtn.style.color = "#ffffff";
        });
        rescanBtn.addEventListener("mouseleave", () => {
            rescanBtn.style.background = "rgba(255,255,255,0.05)";
            rescanBtn.style.color = "rgba(244,244,245,0.78)";
        });
        rescanBtn.addEventListener("click", (e) => {
            e.preventDefault();
            this.onAction?.("addon_rescan", {});
        });
        actionsRow.appendChild(rescanBtn);

        const registerBtn = document.createElement("button");
        registerBtn.type = "button";
        Object.assign(registerBtn.style, {
            padding: "4px 8px",
            background: "rgba(99,102,241,0.15)",
            border: "1px solid rgba(99,102,241,0.3)",
            borderRadius: "4px",
            color: "#a5b4fc",
            fontSize: "10px",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.15s ease",
        });
        registerBtn.textContent = "＋ Register Module";
        registerBtn.addEventListener("mouseenter", () => {
            registerBtn.style.background = "rgba(99,102,241,0.25)";
            registerBtn.style.color = "#c7d2fe";
        });
        registerBtn.addEventListener("mouseleave", () => {
            registerBtn.style.background = "rgba(99,102,241,0.15)";
            registerBtn.style.color = "#a5b4fc";
        });
        actionsRow.appendChild(registerBtn);

        // 3. Register Module Form
        const registerForm = document.createElement("form");
        Object.assign(registerForm.style, {
            display: "none",
            flexDirection: "row",
            alignItems: "center",
            gap: "8px",
            padding: "8px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            marginBottom: "12px",
            width: "100%",
        });
        this.workspaceOverviewHost.appendChild(registerForm);

        const registerInput = document.createElement("input");
        registerInput.type = "text";
        registerInput.placeholder = "Module or package name (e.g. molsysmt)";
        Object.assign(registerInput.style, {
            flex: "1",
            padding: "4px 8px",
            borderRadius: "4px",
            border: "1px solid rgba(255,255,255,0.1)",
            background: "rgba(0,0,0,0.2)",
            color: "#ffffff",
            fontSize: "11px",
        });
        registerForm.appendChild(registerInput);

        const submitBtn = document.createElement("button");
        submitBtn.type = "submit";
        Object.assign(submitBtn.style, {
            padding: "4px 10px",
            background: "#6366f1",
            borderRadius: "4px",
            border: "0",
            color: "#ffffff",
            fontSize: "10px",
            fontWeight: "700",
            cursor: "pointer",
        });
        submitBtn.textContent = "Register";
        registerForm.appendChild(submitBtn);

        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        Object.assign(cancelBtn.style, {
            padding: "4px 8px",
            background: "transparent",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "4px",
            color: "rgba(244,244,245,0.48)",
            fontSize: "10px",
            cursor: "pointer",
        });
        cancelBtn.textContent = "Cancel";
        registerForm.appendChild(cancelBtn);

        registerBtn.addEventListener("click", (e) => {
            e.preventDefault();
            registerForm.style.display = "flex";
            registerInput.focus();
        });
        cancelBtn.addEventListener("click", () => {
            registerForm.style.display = "none";
            registerInput.value = "";
        });
        registerForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const val = registerInput.value.trim();
            if (val) {
                this.onAction?.("addon_register_module", { name: val });
                registerForm.style.display = "none";
                registerInput.value = "";
            }
        });

        // 4. Fallback if addonsList is not populated yet
        let effectiveAddons = this.addonsList;
        if (effectiveAddons.length === 0) {
            effectiveAddons = this.workspaceItems
                .filter((w) => w.id !== "core")
                .map((w) => ({
                    name: w.id,
                    title: w.title,
                    description: w.description || w.subtitle || "",
                    enabled: true,
                    workspaceTitles: [w.title],
                    panelTitles: w.panelCount ? Array(w.panelCount).fill("Panel") : [],
                    workbenchTitles: w.workbenchSectionCount ? Array(w.workbenchSectionCount).fill("Section") : [],
                    contextActionTitles: w.contextActionCount ? Array(w.contextActionCount).fill("Context") : [],
                    exportHelperTitles: w.exportHelperCount ? Array(w.exportHelperCount).fill("Export") : [],
                }));
        }

        if (effectiveAddons.length === 0 && this.addonDiagnostics.length === 0) {
            const empty = document.createElement("div");
            Object.assign(empty.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                textAlign: "center",
                padding: "24px 0",
            });
            empty.textContent = "No analytical add-ons registered.";
            this.workspaceOverviewHost.appendChild(empty);
            return;
        }

        // 4.8. Header for extensions
        const extensionsHeader = document.createElement("div");
        Object.assign(extensionsHeader.style, {
            fontSize: "10px",
            fontWeight: "700",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "rgba(244,244,245,0.44)",
            marginBottom: "8px",
        });
        extensionsHeader.textContent = "Registered Add-ons";
        this.workspaceOverviewHost.appendChild(extensionsHeader);

        // 5. Render Registered Add-ons List
        const listContainer = document.createElement("div");
        Object.assign(listContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            width: "100%",
        });
        this.workspaceOverviewHost.appendChild(listContainer);

        for (const addon of effectiveAddons) {
            // Find if there is a loading/discovery diagnostic failure for this addon
            const failure = this.addonDiagnostics.find(
                (d) => d.source.toLowerCase().includes(addon.name.toLowerCase())
            );

            // Card row container
            const row = document.createElement("div");
            row.setAttribute("data-molsysviewer-addon-card", addon.name);
            Object.assign(row.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "stretch",
                gap: "4px",
                padding: "10px 12px",
                borderRadius: "8px",
                border: "1px solid rgba(255,255,255,0.06)",
                background: "rgba(255,255,255,0.02)",
                transition: "all 0.15s ease",
                position: "relative",
                paddingRight: "100px",
                textAlign: "left",
                cursor: "pointer",
            });

            if (failure) {
                // Renders diagnostic failure card style
                row.setAttribute("data-molsysviewer-addons-addon-discovery-failure", addon.name);
                Object.assign(row.style, {
                    background: "rgba(239,68,68,0.03)",
                    border: "1px solid rgba(239,68,68,0.25)",
                    paddingRight: "12px",
                });

                const header = document.createElement("div");
                Object.assign(header.style, {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                });
                const name = document.createElement("span");
                Object.assign(name.style, { fontWeight: "700", fontSize: "12px", color: "#fca5a5" });
                name.textContent = addon.title || addon.name;
                const badge = document.createElement("span");
                Object.assign(badge.style, {
                    fontSize: "8px",
                    background: "rgba(239,68,68,0.2)",
                    border: "1px solid rgba(239,68,68,0.4)",
                    color: "#ef4444",
                    borderRadius: "4px",
                    padding: "1px 5px",
                    fontWeight: "700",
                });
                badge.textContent = failure.kind === "lifecycle" ? "Lifecycle Error" : "Discovery Error";
                header.appendChild(name);
                header.appendChild(badge);
                row.appendChild(header);

                const desc = document.createElement("div");
                Object.assign(desc.style, { fontSize: "10px", color: "rgba(252,165,165,0.72)" });
                desc.textContent = failure.reason || "Error loading addon.";
                row.appendChild(desc);

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
                row.appendChild(traceBox);

                row.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const isVisible = traceBox.style.display === "block";
                    traceBox.style.display = isVisible ? "none" : "block";
                });
            } else {
                // Success card: styling standard dark-indigo
                row.addEventListener("mouseenter", () => {
                    if (addon.enabled) {
                        row.style.background = "rgba(255,255,255,0.04)";
                        row.style.border = "1px solid rgba(255,255,255,0.1)";
                    }
                });
                row.addEventListener("mouseleave", () => {
                    row.style.background = "rgba(255,255,255,0.02)";
                    row.style.border = "1px solid rgba(255,255,255,0.06)";
                });

                // Row click selects workspace if enabled
                const matchedWorkspace = this.workspaceItems.find(
                    (w) => w.addon === addon.name || w.id === addon.name
                );
                row.addEventListener("click", (e) => {
                    e.preventDefault();
                    if (addon.enabled && matchedWorkspace) {
                        this.onSelectWorkspace?.(matchedWorkspace.id);
                    }
                });

                // Direct Children:
                // 1. Name Row (children[0])
                const nameRow = document.createElement("div");
                Object.assign(nameRow.style, {
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                });
                row.appendChild(nameRow);

                const name = document.createElement("div");
                Object.assign(name.style, {
                    fontWeight: "700",
                    fontSize: "12px",
                    color: addon.enabled ? "#f4f4f5" : "rgba(244,244,245,0.34)",
                });
                name.textContent = addon.title || addon.name;
                nameRow.appendChild(name);

                if (!addon.enabled) {
                    const disabledBadge = document.createElement("span");
                    Object.assign(disabledBadge.style, {
                        fontSize: "8px",
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        color: "rgba(244,244,245,0.3)",
                        padding: "1px 4px",
                        borderRadius: "3px",
                    });
                    disabledBadge.textContent = "Disabled";
                    nameRow.appendChild(disabledBadge);
                }

                // 2. Description (children[1]) - ALWAYS appended to preserve exact index 1 in tests
                const desc = document.createElement("div");
                Object.assign(desc.style, {
                    fontSize: "10px",
                    color: addon.enabled ? "rgba(244,244,245,0.48)" : "rgba(244,244,245,0.22)",
                    lineHeight: "1.35",
                });
                desc.textContent = addon.description || "";
                row.appendChild(desc);

                // 3. Capability Chips (children[2])
                const chipRow = document.createElement("div");
                Object.assign(chipRow.style, {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px",
                    marginTop: "2px",
                    opacity: addon.enabled ? "1" : "0.3",
                });
                row.appendChild(chipRow);

                const createChip = (text: string) => {
                    const chip = document.createElement("span");
                    Object.assign(chip.style, {
                        fontSize: "8px",
                        fontWeight: "700",
                        padding: "1px 5px",
                        borderRadius: "99px",
                        background: "rgba(255,255,255,0.03)",
                        border: "1px solid rgba(255,255,255,0.06)",
                        color: "rgba(244,244,245,0.5)",
                    });
                    chip.textContent = text;
                    chipRow.appendChild(chip);
                };

                const panels = addon.panelTitles?.length || 0;
                const sections = addon.workbenchTitles?.length || 0;
                const actions = addon.contextActionTitles?.length || 0;

                if (panels > 0) createChip(`${panels} Panel${panels === 1 ? "" : "s"}`);
                if (sections > 0) createChip(`${sections} Section${sections === 1 ? "" : "s"}`);
                if (actions > 0) createChip(`${actions} Context`);

                // 4. Actions Container (Right side, absolute positioned - children[3])
                const actionsContainer = document.createElement("div");
                Object.assign(actionsContainer.style, {
                    position: "absolute",
                    right: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                });
                row.appendChild(actionsContainer);

                // iOS Style Toggle Switch
                const toggleTrack = document.createElement("div");
                Object.assign(toggleTrack.style, {
                    width: "30px",
                    height: "16px",
                    borderRadius: "8px",
                    background: addon.enabled ? "#6366f1" : "rgba(255,255,255,0.12)",
                    position: "relative",
                    cursor: "pointer",
                    transition: "background 0.2s ease",
                });
                const toggleThumb = document.createElement("div");
                Object.assign(toggleThumb.style, {
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    background: "#ffffff",
                    position: "absolute",
                    top: "2px",
                    left: addon.enabled ? "16px" : "2px",
                    transition: "left 0.2s ease",
                });
                toggleTrack.appendChild(toggleThumb);
                actionsContainer.appendChild(toggleTrack);

                toggleTrack.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.onAction?.(addon.enabled ? "addon_disable" : "addon_enable", { name: addon.name });
                });

                if (matchedWorkspace) {
                    const openBtn = document.createElement("button");
                    openBtn.type = "button";
                    Object.assign(openBtn.style, {
                        padding: "3px 8px",
                        borderRadius: "4px",
                        border: "1px solid rgba(255,255,255,0.1)",
                        background: "rgba(255,255,255,0.03)",
                        color: addon.enabled ? "rgba(244,244,245,0.78)" : "rgba(244,244,245,0.2)",
                        fontSize: "10px",
                        fontWeight: "600",
                        cursor: addon.enabled ? "pointer" : "not-allowed",
                        transition: "all 0.15s ease",
                    });
                    openBtn.textContent = "Open ➔";

                    if (addon.enabled) {
                        openBtn.addEventListener("mouseenter", () => {
                            openBtn.style.background = "rgba(255,255,255,0.08)";
                            openBtn.style.color = "#ffffff";
                        });
                        openBtn.addEventListener("mouseleave", () => {
                            openBtn.style.background = "rgba(255,255,255,0.03)";
                            openBtn.style.color = "rgba(244,244,245,0.78)";
                        });
                        openBtn.addEventListener("click", (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            this.onSelectWorkspace?.(matchedWorkspace.id);
                        });
                    }
                    actionsContainer.appendChild(openBtn);
                }
            }

            listContainer.appendChild(row);
        }

        // 6. Standalone diagnostics failures (errors from modules that couldn't even register as workspaces)
        let diagnosticsRendered = false;
        for (const failure of this.addonDiagnostics) {
            const isMatched = effectiveAddons.some((addon) => failure.source.toLowerCase().includes(addon.name.toLowerCase()));
            if (isMatched) continue;

            if (!diagnosticsRendered) {
                const diagHeader = document.createElement("div");
                Object.assign(diagHeader.style, {
                    fontSize: "11px",
                    fontWeight: "700",
                    color: "#fca5a5",
                    marginTop: "16px",
                    marginBottom: "8px",
                });
                diagHeader.textContent = "Diagnostics & Failures";
                this.workspaceOverviewHost.appendChild(diagHeader);
                diagnosticsRendered = true;
            }

            const card = document.createElement("div");
            card.setAttribute("data-molsysviewer-addons-addon-discovery-failure", failure.source);
            Object.assign(card.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "stretch",
                gap: "6px",
                padding: "10px 12px",
                borderRadius: "8px",
                background: "rgba(239,68,68,0.03)",
                border: "1px solid rgba(239,68,68,0.25)",
                color: "#fca5a5",
                marginBottom: "8px",
                cursor: "pointer",
            });

            const header = document.createElement("div");
            Object.assign(header.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
            const name = document.createElement("span");
            Object.assign(name.style, { fontWeight: "700", fontSize: "12px" });
            name.textContent = failure.source;
            const badge = document.createElement("span");
            Object.assign(badge.style, {
                fontSize: "8px",
                background: "rgba(239,68,68,0.2)",
                border: "1px solid rgba(239,68,68,0.4)",
                color: "#ef4444",
                borderRadius: "4px",
                padding: "1px 5px",
                fontWeight: "700",
            });
            badge.textContent = failure.kind === "lifecycle" ? "Lifecycle Error" : "Discovery Error";
            header.appendChild(name);
            header.appendChild(badge);
            card.appendChild(header);

            const desc = document.createElement("div");
            Object.assign(desc.style, { fontSize: "10px", color: "rgba(252,165,165,0.72)" });
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
                const isVisible = traceBox.style.display === "block";
                traceBox.style.display = isVisible ? "none" : "block";
            });

            this.workspaceOverviewHost.appendChild(card);
        }
    }

    // ── Left Column: Workspace Navigation (Mimicking Studio layout) ──
    private renderLeftNavigation(): void {
        this.leftColumn.replaceChildren();

        // Style leftColumn as flex container to push Settings to the bottom
        Object.assign(this.leftColumn.style, {
            display: "flex",
            flexDirection: "column",
            height: "100%",
            justifyContent: "space-between",
            paddingRight: "8px",
            boxSizing: "border-box",
        });

        // Top container for add-on workspaces
        const topContainer = document.createElement("div");
        Object.assign(topContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            overflowY: "auto",
            flex: "1 1 0",
        });
        this.leftColumn.appendChild(topContainer);

        // Bottom container for Settings/Catalog button
        const bottomContainer = document.createElement("div");
        Object.assign(bottomContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            borderTop: "1px solid rgba(255,255,255,0.06)",
            paddingTop: "8px",
            marginTop: "8px",
            flex: "0 0 auto",
        });
        this.leftColumn.appendChild(bottomContainer);

        const createWorkspaceButton = (workspace: WorkspaceOption) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("data-molsysviewer-addon-workspace-tab", workspace.id);
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

            const isActive = workspace.id === this.currentWorkspaceId;

            if (isActive) {
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
            Object.assign(title.style, { 
                fontSize: "12px", 
                fontWeight: "600",
                display: "flex",
                alignItems: "center",
                gap: "6px"
            });
            
            if (workspace.id === "core") {
                title.textContent = "⚙ Settings";
            } else {
                title.textContent = workspace.title;
            }
            btn.appendChild(title);

            const descText = workspace.id === "core" ? "Add-ons manager" : (workspace.description || workspace.subtitle || "");
            if (descText) {
                const sub = document.createElement("div");
                Object.assign(sub.style, {
                    fontSize: "10px",
                    color: isActive ? "rgba(244,244,245,0.6)" : "rgba(244,244,245,0.44)",
                });
                sub.textContent = descText;
                btn.appendChild(sub);
            }

            btn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.onSelectWorkspace?.(workspace.id);
            });

            return btn;
        };

        // Render add-ons at the top
        for (const workspace of this.workspaceItems) {
            if (workspace.id === "core") continue;
            topContainer.appendChild(createWorkspaceButton(workspace));
        }

        // Render Settings/Catalog at the bottom
        const coreWorkspace = this.workspaceItems.find((w) => w.id === "core") || {
            id: "core",
            title: "Settings",
        };
        bottomContainer.appendChild(createWorkspaceButton(coreWorkspace));
    }

    // ── Right Column: Fixed Header with Subpanels & Sections ───────
    private renderAddonHeader(activeWorkspace: WorkspaceOption): void {
        this.addonHeaderHost.replaceChildren();

        // 1. Addon Title
        const headerTitle = document.createElement("div");
        Object.assign(headerTitle.style, {
            fontSize: "13px",
            fontWeight: "700",
            color: "#f4f4f5",
            marginBottom: "8px",
        });
        headerTitle.textContent = activeWorkspace.title;
        this.addonHeaderHost.appendChild(headerTitle);

        // 2. Horizontal Row 1 (Panels / Subpanels - Nivel 2)
        const row1 = document.createElement("div");
        Object.assign(row1.style, {
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
            width: "100%",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            paddingBottom: "4px",
            marginBottom: "8px",
        });
        this.addonHeaderHost.appendChild(row1);

        const relevantPanels = this.workspacePanelItems.filter(
            (item) => item.id !== "navigate" && item.id !== "addons"
        );

        for (const panel of relevantPanels) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.setAttribute("data-molsysviewer-addon-panel-tab", panel.id);
            Object.assign(btn.style, {
                background: "transparent",
                border: "0",
                padding: "4px 0 8px 0",
                fontSize: "11px",
                fontWeight: "600",
                color: panel.active ? "#6366f1" : "rgba(244,244,245,0.48)",
                cursor: "pointer",
                position: "relative",
                transition: "color 0.15s ease",
            });

            if (panel.active) {
                const underline = document.createElement("div");
                Object.assign(underline.style, {
                    position: "absolute",
                    bottom: "0",
                    left: "0",
                    right: "0",
                    height: "2px",
                    background: "#6366f1",
                });
                btn.appendChild(underline);
            } else {
                btn.addEventListener("mouseenter", () => {
                    btn.style.color = "rgba(244,244,245,0.85)";
                });
                btn.addEventListener("mouseleave", () => {
                    btn.style.color = "rgba(244,244,245,0.48)";
                });
            }

            btn.textContent = panel.title;

            btn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                // Reset selected Nivel 3 operation on subpanel switch
                this.activeSectionKey = null;
                this.onSelectWorkspacePanel?.(panel.id);
            });

            row1.appendChild(btn);
        }

        // 3. Horizontal Row 2 (Operations / Sections - Nivel 3)
        const summary = this.activeWorkspacePanelSummary;
        if (summary && Array.isArray(summary.sections) && summary.sections.length > 0) {
            const row2 = document.createElement("div");
            Object.assign(row2.style, {
                display: "flex",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "6px",
                width: "100%",
                marginBottom: "4px",
            });
            this.addonHeaderHost.appendChild(row2);

            const sections = summary.sections;
            if (!this.activeSectionKey || !sections.some(s => s.key === this.activeSectionKey)) {
                this.activeSectionKey = sections[0].key;
            }

            for (const section of sections) {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.setAttribute("data-molsysviewer-addon-section-tab", section.key);

                const isActive = section.key === this.activeSectionKey;
                Object.assign(btn.style, {
                    background: isActive ? "rgba(99,102,241,0.15)" : "transparent",
                    border: isActive ? "1px solid rgba(99,102,241,0.3)" : "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "4px",
                    padding: "3px 8px",
                    fontSize: "10px",
                    fontWeight: "500",
                    color: isActive ? "#a5b4fc" : "rgba(244,244,245,0.58)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                });

                if (!isActive) {
                    btn.addEventListener("mouseenter", () => {
                        btn.style.background = "rgba(255,255,255,0.04)";
                        btn.style.color = "rgba(244,244,245,0.85)";
                    });
                    btn.addEventListener("mouseleave", () => {
                        btn.style.background = "transparent";
                        btn.style.color = "rgba(244,244,245,0.58)";
                    });
                }

                btn.textContent = section.title;

                btn.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.activeSectionKey = section.key;
                    this.render();
                });

                row2.appendChild(btn);
            }
        }
    }

    // ── Operation / Section Visibility Filter (Nivel 3) ──────────────
    private applySectionVisibilityFilter(): void {
        const key = this.activeSectionKey;
        if (!key) return;

        const sections = this.addonsWidgetHost.querySelectorAll("[data-molsysviewer-addon-section]");
        if (sections.length === 0) return;

        for (let i = 0; i < sections.length; i++) {
            const el = sections[i] as HTMLElement;
            const secKey = el.getAttribute("data-molsysviewer-addon-section");
            if (secKey === key) {
                el.style.display = "";
            } else {
                el.style.display = "none";
            }
        }
    }
}
