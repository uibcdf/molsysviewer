import { Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, GroupSelectionItem, buildGroupItemsFromStructure } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import { GroupStrip } from "./group-strip";
import { PanelShell } from "./panel-shell";
import { FloatingPanelShell } from "./floating-panel-shell";

export type NavigateItem = {
    key?: string;
    title: string;
    subtitle?: string;
    active?: boolean;
    hidden?: boolean;
    onActivate?: () => void;
    onToggleVisibility?: (hidden: boolean) => void;
    onDelete?: () => void;
};

export type SceneState = {
    styleTag?: string;
    preset?: string;
    figurePreset?: string;
    figureScale?: number;
    figureVariants?: string[];
    isDarkMode?: boolean;
    isSpinActive?: boolean;
    isSwingActive?: boolean;
    cameraMode?: "perspective" | "orthographic";
    fogEnabled?: boolean;
    fogIntensity?: number;
};

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnInteraction = (item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;
type SavedSelectionSummary = { tag: string; atom_count: number };
type RegionSummary = { tag: string; atom_count: number; hidden: boolean };
type WorkspaceOption = { id: string; title: string; subtitle?: string };
type PanelOption = { id: string; title: string; active?: boolean };

type TabKey = "system" | "selection" | "regions" | "overlays" | "viewport" | "settings";

export class GroupPanel {
    private readonly root: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly body: HTMLDivElement;
    private readonly shell: PanelShell | FloatingPanelShell;
    
    // Left column: Tabs
    private readonly leftColumn: HTMLDivElement;
    private readonly tabsContainer: HTMLDivElement;
    private activeTab: TabKey = "system";
    private readonly tabs: Map<TabKey, { button: HTMLButtonElement; badge: HTMLSpanElement }> = new Map();

    // Right column: Content Sections
    private readonly rightColumn: HTMLDivElement;
    private readonly systemSection: HTMLDivElement;
    private readonly selectionSection: HTMLDivElement;
    private readonly regionsSection: HTMLDivElement;
    private readonly overlaysSection: HTMLDivElement;
    private readonly viewportSection: HTMLDivElement;
    private readonly settingsSection: HTMLDivElement;
    private readonly model?: any;
    private activeStyleRegionTag: string | null = null;

    private readonly strips = new Map<string, GroupStrip>();
    private structure?: Structure;
    private expanded = false;
    private currentSelection: ActiveSelectionPayload = {
        event: "interaction_active_selection_changed",
        source_kind: "empty",
        target_level: "none",
        element_level: "none",
        items: [],
        atom_indices: [],
        group_indices: [],
        component_indices: [],
        chain_indices: [],
        molecule_indices: [],
        entity_indices: [],
        count_atoms: 0,
        count_groups: 0,
        count_shapes: 0,
        count_annotations: 0,
    };
    private readonly annotationMessages: AddLabelMessage[] = [];
    private currentContextTarget: ContextMenuTarget | null = null;
    private readonly collapseStateByChain = new Map<string, { molecules: number[]; components: string[] }>();
    private savedSelections: SavedSelectionSummary[] = [];
    private regions: RegionSummary[] = [];
    private shapes: NavigateItem[] = [];
    private annotations: NavigateItem[] = [];
    private measurements: NavigateItem[] = [];
    private sceneState: SceneState = {};

    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToWorkbench?: () => void;
    private onNavigateToSettings?: () => void;
    private runtimeVisibleOverride: boolean | null = null;
    private readonly sharedShell: boolean;
    private visible = false;

    constructor(
        private readonly host: HTMLElement,
        private readonly onSelect: OnSelect,
        private readonly onInteraction: OnInteraction,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
        private readonly onActivateSavedSelection: (tag: string) => void,
        private readonly onFocusRegion: (tag: string) => void,
        private readonly onAction: ((action: string, details?: any) => void) | undefined,
        options?: { floating?: boolean; sharedShell?: FloatingPanelShell; model?: any },
    ) {
        this.model = options?.model;
        const floating = options?.floating || !!options?.sharedShell;
        this.sharedShell = !!options?.sharedShell;
        this.shell = options?.sharedShell
            ? options.sharedShell
            : (floating
                ? new FloatingPanelShell(this.host, { title: "Studio", navButtonLabel: "Add-ons" })
                : new PanelShell(this.host, { title: "Studio", width: 560, toggleWidth: 26, navButtonLabel: "Add-ons" }));
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

        this.root.setAttribute("data-molsysviewer-group-panel", "true");
        this.toggleButton.setAttribute("data-molsysviewer-group-panel-toggle", "true");
        this.shell.titleElement.setAttribute("data-molsysviewer-group-panel-title", "true");
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
                this.onNavigateToWorkbench?.();
            });
        }

        this.body.setAttribute("data-molsysviewer-group-panel-body", "true");
        Object.assign(this.body.style, {
            flexDirection: "row",
            overflow: "hidden",
            gap: "0",
        });

        // ── Left column: Navigation Tabs ───────────────────────────
        this.leftColumn = document.createElement("div");
        this.leftColumn.setAttribute("data-molsysviewer-group-panel-left", "true");
        Object.assign(this.leftColumn.style, {
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            width: "180px",
            minWidth: "180px",
            height: "100%",
            paddingRight: "8px",
            borderRight: "1px solid rgba(255,255,255,0.06)",
            boxSizing: "border-box",
        });
        this.body.appendChild(this.leftColumn);

        // Container for top navigation tabs
        this.tabsContainer = document.createElement("div");
        Object.assign(this.tabsContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            width: "100%",
            overflowY: "auto",
            overflowX: "hidden",
            flex: "1 1 0",
        });
        this.leftColumn.appendChild(this.tabsContainer);

        // Container for bottom settings tab
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

        // ⚙ Settings Button at the bottom
        const settingsBtn = document.createElement("button");
        settingsBtn.type = "button";
        settingsBtn.setAttribute("data-molsysviewer-group-settings-btn", "true");
        Object.assign(settingsBtn.style, {
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
        settingsBtn.addEventListener("mouseenter", () => {
            if (this.activeTab !== "settings") {
                settingsBtn.style.background = "rgba(255,255,255,0.04)";
                settingsBtn.style.color = "rgba(244,244,245,0.9)";
            }
        });
        settingsBtn.addEventListener("mouseleave", () => {
            if (this.activeTab !== "settings") {
                settingsBtn.style.background = "transparent";
                settingsBtn.style.color = "rgba(244,244,245,0.68)";
            }
        });
        settingsBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.switchTab("settings");
        });

        const settingsTitle = document.createElement("div");
        Object.assign(settingsTitle.style, { fontSize: "12px", fontWeight: "600" });
        settingsTitle.textContent = "⚙ Settings";
        settingsBtn.appendChild(settingsTitle);

        const settingsBadge = document.createElement("span");
        Object.assign(settingsBadge.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.48)",
        });
        settingsBadge.textContent = "Viewer config";
        settingsBtn.appendChild(settingsBadge);

        bottomContainer.appendChild(settingsBtn);
        this.tabs.set("settings", { button: settingsBtn, badge: settingsBadge });

        // ── Right column: Content Viewport ──────────────────────────
        this.rightColumn = document.createElement("div");
        this.rightColumn.setAttribute("data-molsysviewer-group-panel-right", "true");
        Object.assign(this.rightColumn.style, {
            display: "flex",
            flexDirection: "column",
            flex: "1 1 0",
            minWidth: "0",
            overflow: "hidden",
            paddingLeft: "12px",
        });
        this.body.appendChild(this.rightColumn);

        // Create Sections
        this.systemSection = this.createSection("system");
        this.selectionSection = this.createSection("selection");
        this.regionsSection = this.createSection("regions");
        this.overlaysSection = this.createSection("overlays");
        this.viewportSection = this.createSection("viewport");
        this.settingsSection = this.createSection("settings");

        // Set system panel layout specificity
        Object.assign(this.systemSection.style, {
            flexDirection: "row",
            overflowX: "auto",
            overflowY: "hidden",
            paddingBottom: "8px",
        });

        // Add tabs
        this.addTab("system", "System", "None");
        this.addTab("selection", "Selection", "None");
        this.addTab("regions", "Regions", "0");
        this.addTab("overlays", "Overlays", "0");
        this.addTab("viewport", "Viewport", "Dark");

        // Switch to system tab by default
        this.switchTab("system");

        // Render empty sections initially
        this.renderSelectionSection();
        this.renderRegionsSection();
        this.renderOverlaysSection();
        this.renderViewportSection();
    }

    private createSection(key: TabKey): HTMLDivElement {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-group-panel-section", key);
        Object.assign(section.style, {
            display: "none",
            flexDirection: "column",
            flex: "1 1 0",
            minHeight: "0",
            gap: "12px",
            overflowY: "auto",
        });
        this.rightColumn.appendChild(section);
        return section;
    }

    private addTab(key: TabKey, title: string, initialBadge: string): void {
        const button = document.createElement("button");
        button.setAttribute("data-molsysviewer-group-panel-tab", key);
        Object.assign(button.style, {
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

        button.addEventListener("mouseenter", () => {
            if (this.activeTab !== key) {
                button.style.background = "rgba(255,255,255,0.04)";
                button.style.color = "rgba(244,244,245,0.9)";
            }
        });
        button.addEventListener("mouseleave", () => {
            if (this.activeTab !== key) {
                button.style.background = "transparent";
                button.style.color = "rgba(244,244,245,0.68)";
            }
        });
        button.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.switchTab(key);
        });

        const titleDiv = document.createElement("div");
        Object.assign(titleDiv.style, {
            fontSize: "12px",
            fontWeight: "600",
        });
        titleDiv.textContent = title;

        const badge = document.createElement("span");
        Object.assign(badge.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.48)",
        });
        badge.textContent = initialBadge;

        button.appendChild(titleDiv);
        button.appendChild(badge);
        this.tabsContainer.appendChild(button);

        this.tabs.set(key, { button, badge });
    }

    private switchTab(key: TabKey): void {
        this.activeTab = key;

        // Reset all tabs styles
        for (const [tabKey, { button, badge }] of this.tabs.entries()) {
            if (tabKey === key) {
                Object.assign(button.style, {
                    background: "rgba(255,255,255,0.08)",
                    color: "#f4f4f5",
                    borderLeft: "3px solid #6366f1",
                    paddingLeft: "9px",
                });
                badge.style.color = "rgba(244,244,245,0.8)";
            } else {
                Object.assign(button.style, {
                    background: "transparent",
                    color: "rgba(244,244,245,0.68)",
                    borderLeft: "0",
                    paddingLeft: "12px",
                });
                badge.style.color = "rgba(244,244,245,0.48)";
            }
        }

        // Toggle sections visibility
        this.systemSection.style.display = key === "system" ? "flex" : "none";
        this.selectionSection.style.display = key === "selection" ? "flex" : "none";
        this.regionsSection.style.display = key === "regions" ? "flex" : "none";
        this.overlaysSection.style.display = key === "overlays" ? "flex" : "none";
        this.viewportSection.style.display = key === "viewport" ? "flex" : "none";
        this.settingsSection.style.display = key === "settings" ? "flex" : "none";

        if (key === "settings") {
            this.renderSettingsSection();
        }
    }

    setStructure(structure: Structure | undefined): void {
        this.structure = structure;
        if (!structure) this.annotationMessages.length = 0;
        
        // Reset to system tab on reload
        this.switchTab("system");
        this.render();
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

    setOnNavigateToWorkbench(callback: (() => void) | undefined, label = "Add-ons"): void {
        this.onNavigateToWorkbench = callback;
        if (!this.sharedShell) {
            this.shell.setNavButtonLabel(callback ? label : undefined);
        }
    }

    setOnNavigateToSettings(callback: (() => void) | undefined): void {
        this.onNavigateToSettings = callback;
    }

    setRuntimeVisible(visible: boolean | null): void {
        this.runtimeVisibleOverride = visible;
        this.render();
    }

    setWorkspaces(items: WorkspaceOption[], currentId: string, onSelect: ((workspaceId: string) => void) | undefined): void {
        this.shell.setOnSelectWorkspace(onSelect);
        this.shell.setWorkspaceOptions(items, currentId);
    }

    setPanelStack(items: PanelOption[], onSelect: ((panelId: string) => void) | undefined): void {
        if (!this.sharedShell) {
            this.shell.setOnSelectPanel(onSelect);
            this.shell.setPanelOptions(items);
        }
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        for (const strip of this.strips.values()) {
            strip.updateSelection(selection);
        }
        
        // Update sidebar Selection badge
        const badge = this.tabs.get("selection")?.badge;
        if (badge) {
            badge.textContent = selection.count_atoms > 0 ? `${selection.count_atoms} atoms` : "None";
        }

        this.renderSelectionSection();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.renderSelectionSection();
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        
        // Update sidebar Regions badge
        const badge = this.tabs.get("regions")?.badge;
        if (badge) {
            badge.textContent = String(items.length);
        }

        this.renderRegionsSection();
    }

    setShapes(items: NavigateItem[]): void {
        this.shapes = [...items];
        this.updateOverlaysBadge();
        this.renderOverlaysSection();
    }

    setAnnotations(items: NavigateItem[]): void {
        this.annotations = [...items];
        this.updateOverlaysBadge();
        this.renderOverlaysSection();
    }

    setMeasurements(items: NavigateItem[]): void {
        this.measurements = [...items];
        this.updateOverlaysBadge();
        this.renderOverlaysSection();
    }

    private updateOverlaysBadge(): void {
        const count = this.shapes.length + this.annotations.length + this.measurements.length;
        const badge = this.tabs.get("overlays")?.badge;
        if (badge) {
            badge.textContent = String(count);
        }
    }

    setScene(state: SceneState): void {
        this.sceneState = { ...state };
        
        // Update sidebar Viewport badge
        const badge = this.tabs.get("viewport")?.badge;
        if (badge) {
            badge.textContent = state.isDarkMode ? "Dark" : "Light";
            if (state.isSpinActive) badge.textContent += " · Spin";
        }

        this.renderViewportSection();
    }

    updateContextTarget(target: ContextMenuTarget | null): void {
        this.currentContextTarget = target;
        for (const strip of this.strips.values()) {
            strip.updateContextTarget(target);
        }
    }

    addLabelOverlay(msg: AddLabelMessage): void {
        this.annotationMessages.push(msg);
        for (const strip of this.strips.values()) {
            strip.addLabelOverlay(msg);
        }
    }

    clearAnnotationOverlays(): void {
        this.annotationMessages.length = 0;
        for (const strip of this.strips.values()) {
            strip.clearAnnotationOverlays();
        }
    }

    clearAnnotationOverlaysByTag(tag?: string): void {
        if (!tag) {
            this.clearAnnotationOverlays();
            return;
        }
        for (let index = this.annotationMessages.length - 1; index >= 0; index--) {
            if (this.annotationMessages[index].tag === tag || this.annotationMessages[index].options?.tag === tag) {
                this.annotationMessages.splice(index, 1);
            }
        }
        for (const strip of this.strips.values()) {
            strip.clearAnnotationOverlaysByTag(tag);
        }
    }

    retagAnnotationOverlays(oldTag: string, newTag: string): void {
        for (const message of this.annotationMessages) {
            if (message.tag === oldTag) message.tag = newTag;
            if (message.options?.tag === oldTag) message.options.tag = newTag;
        }
        for (const strip of this.strips.values()) {
            strip.retagAnnotationOverlays(oldTag, newTag);
        }
    }

    focusItem(item: ActiveSelectionItem) {
        const chainName = item.source_kind === "element" ? (item.chain_name ?? "?") : "?";
        return this.strips.get(chainName)?.focusItem(item) ?? null;
    }

    dispose(): void {
        this.captureCollapseState();
        for (const strip of this.strips.values()) strip.dispose();
        this.strips.clear();
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
        if (this.sharedShell) {
            this.updateBodyDisplay();
        } else {
            this.shell.setExpanded(this.expanded);
        }
        this.onExpandedChange?.(this.expanded);
    }

    private render(): void {
        this.captureCollapseState();
        const grouped = new Map<string, GroupSelectionItem[]>();
        const items = this.structure ? buildGroupItemsFromStructure(this.structure) : [];
        for (const item of items) {
            const chain = item.chain_name ?? "?";
            if (!grouped.has(chain)) grouped.set(chain, []);
            grouped.get(chain)!.push(item);
        }

        const nextChains = new Set(grouped.keys());
        for (const [chain, strip] of this.strips.entries()) {
            if (nextChains.has(chain)) continue;
            this.collapseStateByChain.set(chain, strip.getCollapseState());
            strip.dispose();
            this.strips.delete(chain);
        }

        const naturalVisible = Boolean(this.structure) && grouped.size > 0;
        this.visible = this.runtimeVisibleOverride === false ? false : naturalVisible;
        this.updateBodyDisplay();
        if (!this.sharedShell && !this.visible && this.expanded) {
            this.expanded = false;
        }

        // Update sidebar System badge
        const badge = this.tabs.get("system")?.badge;
        if (badge) {
            badge.textContent = naturalVisible ? `${grouped.size} chain${grouped.size === 1 ? "" : "s"}, ${items.length} res` : "None";
        }

        if (!this.structure || grouped.size === 0) return;

        for (const [chain, chainItems] of grouped.entries()) {
            let strip = this.strips.get(chain);
            if (!strip) {
                strip = new GroupStrip(this.systemSection, chain, this.onSelect, this.onInteraction, this.onFocus, this.onHover, this.onContext, this.onAnnotationContext);
                this.strips.set(chain, strip);
            }
            strip.setData(this.structure, chainItems);
            strip.setCollapseState(this.collapseStateByChain.get(chain));
            strip.updateSelection(this.currentSelection);
            strip.updateContextTarget(this.currentContextTarget);
            strip.clearAnnotationOverlays();
            for (const message of this.annotationMessages) {
                strip.addLabelOverlay(message);
            }
        }
        this.applyExpandedState();
    }

    private captureCollapseState(): void {
        for (const [chain, strip] of this.strips.entries()) {
            this.collapseStateByChain.set(chain, strip.getCollapseState());
        }
    }

    private makeSectionHeader(title: string): HTMLDivElement {
        const header = document.createElement("div");
        Object.assign(header.style, {
            fontSize: "13px",
            fontWeight: "700",
            color: "#f4f4f5",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            paddingBottom: "6px",
            marginBottom: "6px",
        });
        header.textContent = title;
        return header;
    }

    // ── 1. Selection Section Rendering ───────────────────────
    private renderSelectionSection(): void {
        this.selectionSection.replaceChildren();

        // A. Active Selection Area
        this.selectionSection.appendChild(this.makeSectionHeader("Active Selection"));
        const activeContainer = document.createElement("div");
        Object.assign(activeContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.05)",
        });
        this.selectionSection.appendChild(activeContainer);

        if (this.currentSelection.count_atoms > 0) {
            const countLabel = document.createElement("div");
            countLabel.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
            Object.assign(countLabel.style, {
                fontSize: "12px",
                color: "#e4e4e7",
                fontWeight: "500",
            });
            countLabel.textContent = `${this.currentSelection.count_atoms} atoms selected (${this.currentSelection.source_kind} level)`;
            activeContainer.appendChild(countLabel);

            // Action Buttons
            const btnRow = document.createElement("div");
            Object.assign(btnRow.style, {
                display: "flex",
                gap: "8px",
            });
            activeContainer.appendChild(btnRow);

            // Inline input container (will be shown on save / create region)
            const inlineForm = document.createElement("div");
            Object.assign(inlineForm.style, {
                display: "none",
                flexDirection: "row",
                gap: "6px",
                marginTop: "6px",
            });
            const inlineInput = document.createElement("input");
            inlineInput.type = "text";
            Object.assign(inlineInput.style, {
                flex: "1 1 0",
                background: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "6px",
                padding: "6px 8px",
                color: "#fff",
                fontSize: "11px",
                outline: "none",
            });
            const inlineConfirm = document.createElement("button");
            Object.assign(inlineConfirm.style, {
                background: "#6366f1",
                border: "0",
                borderRadius: "6px",
                padding: "6px 10px",
                color: "#fff",
                fontSize: "11px",
                fontWeight: "600",
                cursor: "pointer",
            });
            const inlineCancel = document.createElement("button");
            inlineCancel.textContent = "Cancel";
            Object.assign(inlineCancel.style, {
                background: "rgba(255,255,255,0.08)",
                border: "0",
                borderRadius: "6px",
                padding: "6px 10px",
                color: "#e4e4e7",
                fontSize: "11px",
                cursor: "pointer",
            });

            inlineForm.appendChild(inlineInput);
            inlineForm.appendChild(inlineConfirm);
            inlineForm.appendChild(inlineCancel);
            activeContainer.appendChild(inlineForm);

            const showForm = (mode: "save" | "region") => {
                inlineForm.style.display = "flex";
                inlineInput.value = "";
                inlineInput.placeholder = mode === "save" ? "Selection name..." : "Region name...";
                inlineConfirm.textContent = mode === "save" ? "Save" : "Create";
                
                // Remove previous listeners
                const newConfirm = inlineConfirm.cloneNode(true) as HTMLButtonElement;
                const newCancel = inlineCancel.cloneNode(true) as HTMLButtonElement;
                inlineConfirm.replaceWith(newConfirm);
                inlineCancel.replaceWith(newCancel);

                newConfirm.addEventListener("click", () => {
                    const tag = inlineInput.value.trim();
                    if (!tag) return;
                    if (mode === "save") {
                        this.onAction?.("save_selection", { tag });
                    } else {
                        this.onAction?.("create_region_from_selection", { tag });
                    }
                    inlineForm.style.display = "none";
                });
                newCancel.addEventListener("click", () => {
                    inlineForm.style.display = "none";
                });
                inlineInput.focus();
            };

            const clearBtn = this.makeButton("Clear", () => this.onSelect([], false));
            const saveBtn = this.makeButton("Save", () => showForm("save"));
            const regionBtn = this.makeButton("Create Region", () => showForm("region"));

            btnRow.appendChild(clearBtn);
            btnRow.appendChild(saveBtn);
            btnRow.appendChild(regionBtn);
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                textAlign: "center",
                padding: "6px 0",
            });
            emptyLabel.textContent = "No active selection.";
            activeContainer.appendChild(emptyLabel);
        }

        // B. Saved Selections Area
        this.selectionSection.appendChild(this.makeSectionHeader("Saved Selections"));
        const savedList = document.createElement("div");
        Object.assign(savedList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.selectionSection.appendChild(savedList);

        if (this.savedSelections.length > 0) {
            const sorted = [...this.savedSelections].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                const row = this.makeRowElement(
                    item.tag,
                    `${item.atom_count} atoms`,
                    () => this.onActivateSavedSelection(item.tag),
                    () => this.onAction?.("delete_selection", { tag: item.tag })
                );
                savedList.appendChild(row);
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No saved selections yet.";
            savedList.appendChild(emptyLabel);
        }
    }

    // ── 2. Regions Section Rendering ─────────────────────────
    private renderRegionsSection(): void {
        this.regionsSection.replaceChildren();
        this.regionsSection.appendChild(this.makeSectionHeader("Regions"));

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.regionsSection.appendChild(list);

        if (this.regions.length > 0) {
            const sorted = [...this.regions].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                const itemContainer = document.createElement("div");
                Object.assign(itemContainer.style, {
                    display: "flex",
                    flexDirection: "column",
                });
                list.appendChild(itemContainer);

                const row = this.makeRowElement(
                    item.tag,
                    item.hidden ? `${item.atom_count} atoms · hidden` : `${item.atom_count} atoms`,
                    () => this.onFocusRegion(item.tag),
                    () => this.onAction?.("delete_region", { tag: item.tag }),
                    {
                        hidden: item.hidden,
                        onToggleVisibility: () => this.onAction?.("toggle_region_visibility", { tag: item.tag })
                    },
                    () => {
                        this.activeStyleRegionTag = this.activeStyleRegionTag === item.tag ? null : item.tag;
                        this.renderRegionsSection();
                    }
                );
                itemContainer.appendChild(row);

                if (this.activeStyleRegionTag === item.tag) {
                    itemContainer.appendChild(this.renderStyleComposer(item.tag));
                }
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No regions yet.";
            list.appendChild(emptyLabel);
        }
    }

    // ── 3. Overlays Section Rendering ────────────────────────
    private renderOverlaysSection(): void {
        this.overlaysSection.replaceChildren();
        this.overlaysSection.appendChild(this.makeSectionHeader("Scene Overlays"));

        // A. 3D Shapes
        this.overlaysSection.appendChild(this.makeSectionHeader("3D Shapes"));
        const shapesList = document.createElement("div");
        Object.assign(shapesList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginBottom: "12px",
        });
        this.overlaysSection.appendChild(shapesList);

        if (this.shapes.length > 0) {
            for (const item of this.shapes) {
                const row = this.makeRowElement(
                    item.title,
                    item.subtitle || "Geometry",
                    item.onActivate,
                    item.onDelete,
                    {
                        hidden: item.hidden,
                        onToggleVisibility: item.onToggleVisibility
                    }
                );
                shapesList.appendChild(row);
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No shapes yet.";
            shapesList.appendChild(emptyLabel);
        }

        // B. Annotations (Labels)
        this.overlaysSection.appendChild(this.makeSectionHeader("Annotations (Labels)"));
        const annotationsList = document.createElement("div");
        Object.assign(annotationsList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginBottom: "12px",
        });
        this.overlaysSection.appendChild(annotationsList);

        if (this.annotations.length > 0) {
            for (const item of this.annotations) {
                const row = this.makeRowElement(
                    item.title,
                    item.subtitle || "Annotation",
                    item.onActivate,
                    item.onDelete,
                    {
                        hidden: item.hidden,
                        onToggleVisibility: item.onToggleVisibility
                    }
                );
                annotationsList.appendChild(row);
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No annotations yet.";
            annotationsList.appendChild(emptyLabel);
        }

        // C. Measurements (Distances)
        this.overlaysSection.appendChild(this.makeSectionHeader("Measurements (Distances)"));
        const measurementsList = document.createElement("div");
        Object.assign(measurementsList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.overlaysSection.appendChild(measurementsList);

        if (this.measurements.length > 0) {
            for (const item of this.measurements) {
                const row = this.makeRowElement(
                    item.title,
                    item.subtitle || "Distance line",
                    item.onActivate,
                    item.onDelete,
                    {
                        hidden: item.hidden,
                        onToggleVisibility: item.onToggleVisibility
                    }
                );
                measurementsList.appendChild(row);
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No measurements yet.";
            measurementsList.appendChild(emptyLabel);
        }
    }

    private renderStyleComposer(tag: string): HTMLDivElement {
        const container = document.createElement("div");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "8px 10px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.03)",
            border: "1px dashed rgba(255,255,255,0.08)",
            marginTop: "4px",
            marginBottom: "4px",
        });

        // 1. Style / Representation select
        const styleRow = document.createElement("div");
        Object.assign(styleRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const styleLabel = document.createElement("span");
        styleLabel.textContent = "Representation Style";
        Object.assign(styleLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.7)" });

        const styleSelect = this.makeStyledSelect(
            ["Cartoon", "Sticks", "CPK", "Trace", "Putty"],
            "Cartoon",
            () => {}
        );
        styleRow.appendChild(styleLabel);
        styleRow.appendChild(styleSelect);
        container.appendChild(styleRow);

        // 2. Color scheme select
        const colorRow = document.createElement("div");
        Object.assign(colorRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const colorLabel = document.createElement("span");
        colorLabel.textContent = "Color Scheme";
        Object.assign(colorLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.7)" });

        const customColorInput = document.createElement("input");
        customColorInput.type = "color";
        customColorInput.value = "#3b82f6"; // default blue
        Object.assign(customColorInput.style, {
            width: "20px",
            height: "20px",
            border: "1px solid rgba(255,255,255,0.25)",
            borderRadius: "50%",
            padding: "0",
            background: "transparent",
            cursor: "pointer",
            display: "none",
            boxSizing: "border-box",
            overflow: "hidden",
            outline: "none",
        });

        const colorSelect = this.makeStyledSelect(
            ["Element (CPK)", "Chain ID", "Secondary Structure", "Hydrophobicity", "Custom Color"],
            "Element (CPK)",
            (val) => {
                customColorInput.style.display = val === "Custom Color" ? "inline-block" : "none";
            }
        );

        const colorRight = document.createElement("div");
        Object.assign(colorRight.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        colorRight.appendChild(customColorInput);
        colorRight.appendChild(colorSelect);

        colorRow.appendChild(colorLabel);
        colorRow.appendChild(colorRight);
        container.appendChild(colorRow);

        // 3. Actions Row (Apply & Cancel)
        const actionsRow = document.createElement("div");
        Object.assign(actionsRow.style, {
            display: "flex",
            justifyContent: "flex-end",
            gap: "6px",
            width: "100%",
            marginTop: "4px",
        });

        const cancelBtn = this.makeButton("Cancel", () => {
            this.activeStyleRegionTag = null;
            this.renderRegionsSection();
        });
        Object.assign(cancelBtn.style, {
            flex: "0 0 auto",
            fontSize: "10px",
            padding: "3px 8px",
        });

        const applyBtn = this.makeButton("Apply Style", () => {
            const chosenStyleMap: Record<string, string> = {
                "Cartoon": "cartoon",
                "Sticks": "licorice",
                "CPK": "spacefill",
                "Trace": "backbone",
                "Putty": "putty"
            };
            const repr = chosenStyleMap[styleSelect.value] || "cartoon";

            const chosenColor = colorSelect.value;
            let scheme: string | undefined = undefined;
            if (chosenColor === "Element (CPK)") scheme = "element";
            else if (chosenColor === "Chain ID") scheme = "chain-id";
            else if (chosenColor === "Secondary Structure") scheme = "secondary-structure";
            else if (chosenColor === "Hydrophobicity") scheme = "hydrophobicity";
            else if (chosenColor === "Custom Color") scheme = customColorInput.value;

            this.onAction?.("set_region_representation", {
                tag,
                representation: repr,
                params: scheme ? { color_scheme: scheme } : {},
            });

            this.activeStyleRegionTag = null;
            this.renderRegionsSection();
        });
        Object.assign(applyBtn.style, {
            flex: "0 0 auto",
            fontSize: "10px",
            padding: "3px 8px",
            background: "rgba(16,185,129,0.15)",
            border: "1px solid rgba(16,185,129,0.3)",
        });
        applyBtn.addEventListener("mouseenter", () => {
            applyBtn.style.background = "rgba(16,185,129,0.25)";
            applyBtn.style.border = "1px solid rgba(16,185,129,0.5)";
        });
        applyBtn.addEventListener("mouseleave", () => {
            applyBtn.style.background = "rgba(16,185,129,0.15)";
            applyBtn.style.border = "1px solid rgba(16,185,129,0.3)";
        });

        actionsRow.appendChild(cancelBtn);
        actionsRow.appendChild(applyBtn);
        container.appendChild(actionsRow);

        return container;
    }

    // ── 5. Viewport Section Rendering ────────────────────────
    private renderViewportSection(): void {
        this.viewportSection.replaceChildren();
        this.viewportSection.appendChild(this.makeSectionHeader("Viewport & Export Settings"));

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            paddingBottom: "10px",
        });
        this.viewportSection.appendChild(grid);

        // A. Viewport Card
        const viewportCard = this.makeSettingsCard("Viewport Settings");
        grid.appendChild(viewportCard);

        // A1. Background toggle
        const bgRow = document.createElement("div");
        Object.assign(bgRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const bgLabel = document.createElement("span");
        bgLabel.textContent = "Background";
        Object.assign(bgLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const bgSelect = this.makeStyledSelect(["Dark", "Light"], this.sceneState.isDarkMode ? "Dark" : "Light", (val) => {
            this.onAction?.("toggle_background", { mode: val.toLowerCase() });
        });
        bgRow.appendChild(bgLabel);
        bgRow.appendChild(bgSelect);
        viewportCard.appendChild(bgRow);

        // A2. Spin toggle
        viewportCard.appendChild(this.makeCheckboxRow("Auto-Rotate (Spin)", !!this.sceneState.isSpinActive, () => {
            this.onAction?.("toggle_spin");
        }));

        // A3. Swing toggle
        viewportCard.appendChild(this.makeCheckboxRow("Oscillate (Swing)", !!this.sceneState.isSwingActive, () => {
            this.onAction?.("toggle_swing");
        }));

        // B. Camera Card
        const cameraCard = this.makeSettingsCard("Camera Projection");
        grid.appendChild(cameraCard);

        // B1. Projection Mode
        const projRow = document.createElement("div");
        Object.assign(projRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const projLabel = document.createElement("span");
        projLabel.textContent = "Projection";
        Object.assign(projLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const projSelect = this.makeStyledSelect(["Perspective", "Orthographic"], 
            this.sceneState.cameraMode === "orthographic" ? "Orthographic" : "Perspective", (val) => {
                this.onAction?.("set_camera_mode", { mode: val.toLowerCase() });
            }
        );
        projRow.appendChild(projLabel);
        projRow.appendChild(projSelect);
        cameraCard.appendChild(projRow);

        // B2. Fog enabled
        const fogEnabled = !!this.sceneState.fogEnabled;
        const fogIntensity = typeof this.sceneState.fogIntensity === "number" ? this.sceneState.fogIntensity : 0.5;

        cameraCard.appendChild(this.makeCheckboxRow("Fog Enabled", fogEnabled, (checked) => {
            this.onAction?.("set_fog", { enable: checked, intensity: fogIntensity });
        }));

        // B3. Fog intensity slider
        const fogSliderRow = document.createElement("div");
        Object.assign(fogSliderRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            marginTop: "2px",
        });
        const fogSliderLabel = document.createElement("div");
        Object.assign(fogSliderLabel.style, {
            display: "flex",
            justifyContent: "space-between",
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
        });
        fogSliderLabel.innerHTML = `<span>Fog Intensity</span><span>${Math.round(fogIntensity * 100)}%</span>`;

        const fogSlider = document.createElement("input");
        fogSlider.type = "range";
        fogSlider.min = "0.0";
        fogSlider.max = "1.0";
        fogSlider.step = "0.05";
        fogSlider.value = String(fogIntensity);
        fogSlider.disabled = !fogEnabled;
        Object.assign(fogSlider.style, {
            width: "100%",
            height: "4px",
            borderRadius: "2px",
            background: "rgba(255,255,255,0.12)",
            outline: "none",
            cursor: fogEnabled ? "pointer" : "not-allowed",
            opacity: fogEnabled ? "1" : "0.5",
        });
        fogSlider.addEventListener("change", () => {
            const intensity = parseFloat(fogSlider.value);
            this.onAction?.("set_fog", { enable: fogEnabled, intensity });
        });

        fogSliderRow.appendChild(fogSliderLabel);
        fogSliderRow.appendChild(fogSlider);
        cameraCard.appendChild(fogSliderRow);

        // C. Figure Export Card
        const exportCard = this.makeSettingsCard("Figure Export");
        grid.appendChild(exportCard);

        const currentPreset = this.sceneState.figurePreset || "publication-light";
        const currentScale = typeof this.sceneState.figureScale === "number" ? this.sceneState.figureScale : 2.0;
        const currentVariants = this.sceneState.figureVariants || ["dark", "transparent"];
        const isTransparent = currentVariants.includes("transparent");

        const updateFigureSpec = (preset: string, scale: number, trans: boolean) => {
            const variants = ["dark"];
            if (trans) variants.push("transparent");
            this.onAction?.("set_figure_spec", {
                figure_preset: preset,
                figure_scale: scale,
                figure_variants: variants,
            });
        };

        // C1. Preset selector
        const presetRow = document.createElement("div");
        Object.assign(presetRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const presetLabel = document.createElement("span");
        presetLabel.textContent = "Preset";
        Object.assign(presetLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const presetSelect = this.makeStyledSelect(["Light", "Dark"], 
            currentPreset.includes("dark") ? "Dark" : "Light", (val) => {
                const presetVal = val === "Dark" ? "publication-dark" : "publication-light";
                updateFigureSpec(presetVal, currentScale, isTransparent);
            }
        );
        presetRow.appendChild(presetLabel);
        presetRow.appendChild(presetSelect);
        exportCard.appendChild(presetRow);

        // C2. Resolution Scale dropdown
        const scaleRow = document.createElement("div");
        Object.assign(scaleRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const scaleLabel = document.createElement("span");
        scaleLabel.textContent = "Resolution Scale";
        Object.assign(scaleLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const scaleSelect = this.makeStyledSelect(["1.0x", "2.0x", "3.0x", "4.0x"], `${currentScale.toFixed(1)}x`, (val) => {
            const scaleVal = parseFloat(val.replace("x", ""));
            updateFigureSpec(currentPreset, scaleVal, isTransparent);
        });
        scaleRow.appendChild(scaleLabel);
        scaleRow.appendChild(scaleSelect);
        exportCard.appendChild(scaleRow);

        // C3. Transparency checkbox
        exportCard.appendChild(this.makeCheckboxRow("Transparent Background", isTransparent, (checked) => {
            updateFigureSpec(currentPreset, currentScale, checked);
        }));

        // C4. Download button
        const downloadRow = document.createElement("div");
        Object.assign(downloadRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            marginTop: "6px",
        });
        const downloadButton = this.makeButton("Download Image File", () => {
            this.onAction?.("download_image");
        });
        downloadRow.appendChild(downloadButton);
        exportCard.appendChild(downloadRow);

        // D. Data & State Card
        const dataCard = this.makeSettingsCard("Data & State");
        grid.appendChild(dataCard);

        const htmlRow = document.createElement("div");
        Object.assign(htmlRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            width: "100%",
        });
        const htmlLabel = document.createElement("span");
        htmlLabel.textContent = "Save standalone view as HTML page";
        Object.assign(htmlLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)" });
        const htmlButton = this.makeButton("Download HTML View", () => {
            this.onAction?.("export_html");
        });
        htmlRow.appendChild(htmlLabel);
        htmlRow.appendChild(htmlButton);
        dataCard.appendChild(htmlRow);
    }

    // ── Helper UI Constructors ──────────────────────────────
    private makeButton(text: string, onClick: () => void): HTMLButtonElement {
        const btn = document.createElement("button");
        btn.textContent = text;
        Object.assign(btn.style, {
            flex: "1 1 0",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "6px",
            padding: "5px 8px",
            color: "#f4f4f5",
            fontSize: "11px",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.15s ease",
            textAlign: "center",
        });
        btn.addEventListener("mouseenter", () => {
            btn.style.background = "rgba(255,255,255,0.12)";
            btn.style.border = "1px solid rgba(255,255,255,0.16)";
        });
        btn.addEventListener("mouseleave", () => {
            btn.style.background = "rgba(255,255,255,0.06)";
            btn.style.border = "1px solid rgba(255,255,255,0.1)";
        });
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onClick();
        });
        return btn;
    }

    private makeRowElement(
        titleText: string,
        subtitleText: string,
        onActivate?: () => void,
        onDelete?: () => void,
        visibility?: { hidden?: boolean; onToggleVisibility?: (hidden: boolean) => void },
        onStyle?: () => void
    ): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-group-panel-row", "true");
        row.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
        Object.assign(row.style, {
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "6px 10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.06)",
            gap: "8px",
            transition: "background 0.1s ease",
        });

        // Hover effect
        row.addEventListener("mouseenter", () => {
            row.style.background = "rgba(255,255,255,0.09)";
        });
        row.addEventListener("mouseleave", () => {
            row.style.background = "rgba(255,255,255,0.05)";
        });

        // Clickable main area
        const main = document.createElement("div");
        Object.assign(main.style, {
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            flex: "1 1 0",
            minWidth: "0",
            cursor: onActivate ? "pointer" : "default",
        });
        if (onActivate) {
            row.style.cursor = "pointer";
            row.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                onActivate();
            });
        }

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "600",
            color: "#f4f4f5",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
        });
        title.textContent = titleText;

        const subtitle = document.createElement("div");
        Object.assign(subtitle.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
        });
        subtitle.textContent = subtitleText;

        main.appendChild(title);
        main.appendChild(subtitle);
        row.appendChild(main);

        // Actions toolbar (Right side)
        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            flex: "0 0 auto",
        });
        row.appendChild(actions);

        // Style / Paint Button
        if (onStyle) {
            const styleBtn = document.createElement("button");
            styleBtn.type = "button";
            styleBtn.textContent = "🎨";
            styleBtn.title = "Style & Color";
            Object.assign(styleBtn.style, {
                background: "transparent",
                border: "0",
                color: "rgba(244,244,245,0.55)",
                fontSize: "11px",
                cursor: "pointer",
                padding: "2px 6px",
                borderRadius: "4px",
            });
            styleBtn.addEventListener("mouseenter", () => {
                styleBtn.style.color = "#10b981";
            });
            styleBtn.addEventListener("mouseleave", () => {
                styleBtn.style.color = "rgba(244,244,245,0.55)";
            });
            styleBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                onStyle();
            });
            actions.appendChild(styleBtn);
        }

        // Visibility Toggle (Eye icon)
        if (visibility?.onToggleVisibility) {
            const eyeBtn = document.createElement("button");
            eyeBtn.type = "button";
            eyeBtn.textContent = visibility.hidden ? "⦻" : "👁";
            eyeBtn.title = visibility.hidden ? "Show" : "Hide";
            Object.assign(eyeBtn.style, {
                background: "transparent",
                border: "0",
                color: visibility.hidden ? "rgba(244,244,245,0.36)" : "#6366f1",
                fontSize: "12px",
                cursor: "pointer",
                padding: "2px 6px",
                borderRadius: "4px",
            });
            eyeBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                visibility.onToggleVisibility?.(!visibility.hidden);
            });
            actions.appendChild(eyeBtn);
        }

        // Delete Button (Trash/X icon)
        if (onDelete) {
            const delBtn = document.createElement("button");
            delBtn.type = "button";
            delBtn.textContent = "✕";
            delBtn.title = "Delete";
            Object.assign(delBtn.style, {
                background: "transparent",
                border: "0",
                color: "rgba(244,244,245,0.48)",
                fontSize: "12px",
                cursor: "pointer",
                padding: "2px 6px",
                borderRadius: "4px",
                transition: "color 0.1s ease",
            });
            delBtn.addEventListener("mouseenter", () => {
                delBtn.style.color = "#ef4444";
            });
            delBtn.addEventListener("mouseleave", () => {
                delBtn.style.color = "rgba(244,244,245,0.48)";
            });
            delBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete();
            });
            actions.appendChild(delBtn);
        }
        return row;
    }

    private makeSettingsCard(titleText: string): HTMLDivElement {
        const card = document.createElement("div");
        Object.assign(card.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.05)",
        });

        const header = document.createElement("div");
        Object.assign(header.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.48)",
            textTransform: "uppercase",
            borderBottom: "1px solid rgba(255,255,255,0.04)",
            paddingBottom: "4px",
            marginBottom: "2px",
        });
        header.textContent = titleText;
        card.appendChild(header);

        return card;
    }

    private makeCheckboxRow(labelText: string, checked: boolean, onChange: (checked: boolean) => void): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            cursor: "pointer",
        });

        const label = document.createElement("span");
        label.textContent = labelText;
        Object.assign(label.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        row.appendChild(label);

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = checked;
        Object.assign(cb.style, {
            cursor: "pointer",
            outline: "none",
        });

        const toggle = () => {
            cb.checked = !cb.checked;
            onChange(cb.checked);
        };

        row.addEventListener("click", (e) => {
            if (e.target !== cb) {
                e.preventDefault();
                toggle();
            }
        });
        cb.addEventListener("change", () => {
            onChange(cb.checked);
        });

        row.appendChild(cb);
        return row;
    }

    private makeStyledSelect(options: string[], selectedValue: string, onChange: (value: string) => void): HTMLSelectElement {
        const select = document.createElement("select");
        Object.assign(select.style, {
            background: "rgba(0,0,0,0.28)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "3px 6px",
            color: "#f4f4f5",
            fontSize: "11px",
            fontWeight: "500",
            outline: "none",
            cursor: "pointer",
        });

        for (const opt of options) {
            const el = document.createElement("option");
            el.value = opt;
            el.textContent = opt;
            el.selected = opt === selectedValue;
            select.appendChild(el);
        }

        select.addEventListener("change", () => {
            onChange(select.value);
        });

        return select;
    }

    private renderSettingsSection(): void {
        this.settingsSection.replaceChildren();
        this.settingsSection.appendChild(this.makeSectionHeader("Viewer Settings"));

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            paddingBottom: "10px",
        });
        this.settingsSection.appendChild(grid);

        // Viewport Controls preferences card
        const configCard = this.makeSettingsCard("Viewport Controls");
        grid.appendChild(configCard);

        const autohideRow = document.createElement("div");
        Object.assign(autohideRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            marginTop: "4px",
        });
        configCard.appendChild(autohideRow);

        const autohideLabel = document.createElement("span");
        autohideLabel.textContent = "Autohide Controls";
        Object.assign(autohideLabel.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.8)",
            lineHeight: "1.3",
        });
        autohideRow.appendChild(autohideLabel);

        const autohideEnabled = this.model ? !!this.model.get("autohide_controls") : true;

        // Custom iOS toggle switch for Autohide Controls
        const autohideToggleTrack = document.createElement("div");
        Object.assign(autohideToggleTrack.style, {
            width: "30px",
            height: "16px",
            borderRadius: "8px",
            background: autohideEnabled ? "#6366f1" : "rgba(255,255,255,0.12)",
            position: "relative",
            cursor: "pointer",
            transition: "background 0.2s ease",
            flexShrink: "0",
        });
        const autohideToggleThumb = document.createElement("div");
        Object.assign(autohideToggleThumb.style, {
            width: "12px",
            height: "12px",
            borderRadius: "50%",
            background: "#ffffff",
            position: "absolute",
            top: "2px",
            left: autohideEnabled ? "16px" : "2px",
            transition: "left 0.2s ease",
        });
        autohideToggleTrack.appendChild(autohideToggleThumb);
        autohideRow.appendChild(autohideToggleTrack);

        autohideToggleTrack.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (this.model) {
                const newVal = !this.model.get("autohide_controls");
                this.model.set("autohide_controls", newVal);
                this.model.save_changes();
                this.renderSettingsSection();
            }
        });
    }
}
