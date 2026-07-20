import { Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, ActiveSelectionSetOperation } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import {
    makeButton,
    makeCheckboxRow,
    makeRowElement,
    makeSectionHeader,
    makeSettingsCard,
    makeStyledSelect,
} from "./panels/ui-helpers";
import { PanelContext, StudioPanel } from "./panels/types";
import { ViewportPanel } from "./panels/viewport-panel";
import { ExportPanel } from "./panels/export-panel";
import { LayersPanel, LayerObjectSummary, LayerSummary } from "./panels/layers-panel";
import { RegionsPanel } from "./panels/regions-panel";
import { SelectionPanel } from "./panels/selection-panel";
import { SystemPanel } from "./panels/system-panel";
import { WholePanel } from "./panels/whole-panel";
import { MeasuresPanel, MeasurementSeries, MeasurementSettings, MeasurementSummary } from "./panels/measures-panel";
import { AnnotationsPanel, AnnotationSettings, AnnotationSummary } from "./panels/annotations-panel";
import { ShapesPanel, ShapeRenderStatus, ShapeSummary } from "./panels/shapes-panel";
import { PanelShell } from "./panel-shell";
import { FloatingPanelShell } from "./floating-panel-shell";

const TAB_ORDER_STORAGE_KEY = "molsysviewer-studio-tab-order";

// localStorage must be reached inside a try/catch, not merely guarded for existence:
// in a document with an opaque origin (the e2e harness, file://, a sandboxed iframe)
// *reading the property itself* throws SecurityError. Guarding `window.localStorage`
// and then touching it is exactly the bug that took three e2e suites down.
function readTabOrderStorage(): string | null {
    try {
        return typeof window === "undefined" ? null : window.localStorage.getItem(TAB_ORDER_STORAGE_KEY);
    } catch {
        return null;   // tab order is a convenience; never let it break the viewer
    }
}

function writeTabOrderStorage(order: TabKey[]): void {
    try {
        if (typeof window !== "undefined") {
            window.localStorage.setItem(TAB_ORDER_STORAGE_KEY, JSON.stringify(order));
        }
    } catch {
        // ignore: the order simply will not persist
    }
}

export type NavigateItem = {
    key?: string;
    title: string;
    subtitle?: string;
    active?: boolean;
    hidden?: boolean;
    broken?: boolean;
    brokenReason?: string;
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

export type SectionSummary = {
    tag: string;
    owner?: string;
    point: [number, number, number];
    unit: string;
    normal: [number, number, number];
    invert: boolean;
    hidden: boolean;
};

export type SectionSettings = {
    activeSelectionCount: number;
    systemLoaded: boolean;
};

export type OnSelect = (items: ActiveSelectionItem[], op: ActiveSelectionSetOperation) => void;
export type OnInteraction = (item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }) => void;
export type OnFocus = (item: ActiveSelectionItem) => void;
export type OnHover = (item: ActiveSelectionItem | null) => void;
export type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
export type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;
export type SavedSelectionSummary = { tag: string; atom_count: number; element_level?: string };
export type RegionSummary = {
    tag: string;
    owner?: string;
    atom_count: number;
    hidden: boolean;
    layer?: string | null;
    mode?: "static" | "dynamic";
    frame_dependent?: boolean;
    representation?: string;
    preset?: string;
    representation_params?: Record<string, unknown>;
    overlap_tags?: string[];
    available_attributes?: string[];
};
export type RegionDetails = {
    request_id?: number;
    tag: string;
    atom_count: number;
    group_count: number;
    chain_count: number;
    center_nm: number[];
    structure_index: number;
    provenance?: Record<string, unknown>;
    order?: number;
    mode?: "static" | "dynamic";
    broken?: boolean;
};
export type WholeSummary = {
    representation?: string | null;
    preset?: string | null;
    params: Record<string, unknown>;
    visible: boolean;
    color_scheme?: string | null;
    scene_style_name?: string | null;
    available_attributes: string[];
    color_schemes: string[];
    inheriting_region_count: number;
    none_state_region_count: number;
    covering_layer_count: number;
    composition?: Record<string, number>;
    contains?: Record<string, boolean>;
};
export type WholeDetails = {
    request_id?: number;
    atom_count: number;
    composition?: Record<string, number>;
    contains?: Record<string, boolean>;
    is_composed_of?: Record<string, boolean>;
    center_nm: number[];
    structure_index: number;
};
type WorkspaceOption = { id: string; title: string; subtitle?: string };
type PanelOption = { id: string; title: string; active?: boolean };
export type SelectionQuerySyntax = "MolSysMT" | "Indices";
export type SelectionQueryPreview = {
    request_id?: number;
    ok?: boolean;
    count?: number;
    error_message?: string;
    status?: "pending";
};

type TabKey = "system" | "whole" | "selection" | "regions" | "measures" | "annotations" | "shapes" | "layers" | "viewport" | "export" | "settings";

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

    // Migrated subpanels (panel-per-module architecture)
    private readonly shapesPanel: ShapesPanel;
    private readonly measuresPanel: MeasuresPanel;
    private readonly annotationsPanel: AnnotationsPanel;
    private readonly wholePanel: WholePanel;
    private readonly layersPanel: LayersPanel;
    private readonly viewportPanel: ViewportPanel;
    private readonly exportPanel: ExportPanel;
    private readonly regionsPanel: RegionsPanel;
    private readonly selectionPanel: SelectionPanel;
    private readonly systemPanel: SystemPanel;
    private readonly panels = new Map<TabKey, { section: HTMLDivElement; panel: StudioPanel }>();

    // Right column: Content Sections
    private readonly rightColumn: HTMLDivElement;
    private readonly systemSection: HTMLDivElement;
    private readonly wholeSection: HTMLDivElement;
    private readonly selectionSection: HTMLDivElement;
    private readonly regionsSection: HTMLDivElement;
    private readonly measuresSection: HTMLDivElement;
    private readonly annotationsSection: HTMLDivElement;
    private readonly shapesSection: HTMLDivElement;
    private readonly layersSection: HTMLDivElement;
    private readonly viewportSection: HTMLDivElement;
    private readonly exportSection: HTMLDivElement;
    private readonly settingsSection: HTMLDivElement;
    private readonly model?: any;

    private expanded = false;

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
        settingsBtn.title = "Configure viewer behavior, cache settings, and options.";
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
        this.wholeSection = this.createSection("whole");
        this.wholePanel = new WholePanel(this.makePanelContext("whole"));
        this.selectionSection = this.createSection("selection");
        this.regionsSection = this.createSection("regions");
        this.regionsPanel = new RegionsPanel(this.makePanelContext("regions"), this.onFocusRegion);
        this.selectionPanel = new SelectionPanel(this.makePanelContext("selection"), this.onSelect, this.onActivateSavedSelection, (tag) => this.regionsPanel.hasRegion(tag));
        this.measuresSection = this.createSection("measures");
        this.measuresPanel = new MeasuresPanel(this.makePanelContext("measures"));
        this.annotationsSection = this.createSection("annotations");
        this.annotationsPanel = new AnnotationsPanel(
            this.makePanelContext("annotations"),
            atomIndices => this.onFocus({
                source_kind: "annotation",
                annotation_kind: "label",
                atom_indices: atomIndices,
                group_indices: [],
                chain_indices: [],
                entity_indices: [],
            }),
        );
        this.shapesSection = this.createSection("shapes");
        this.shapesPanel = new ShapesPanel(this.makePanelContext("shapes"));
        this.layersSection = this.createSection("layers");
        this.layersPanel = new LayersPanel(this.makePanelContext("layers"));
        this.viewportSection = this.createSection("viewport");
        this.viewportPanel = new ViewportPanel(this.makePanelContext("viewport"));
        this.exportSection = this.createSection("export");
        this.exportPanel = new ExportPanel(this.makePanelContext("export"));
        this.settingsSection = this.createSection("settings");

        this.systemPanel = new SystemPanel(this.makePanelContext("system"), {
            onSelect: this.onSelect,
            onInteraction: this.onInteraction,
            onFocus: this.onFocus,
            onHover: this.onHover,
            onContext: this.onContext,
            onAnnotationContext: this.onAnnotationContext,
            onRebuilt: (naturalVisible: boolean) => {
                this.visible = this.runtimeVisibleOverride === false ? false : naturalVisible;
                this.updateBodyDisplay();
                if (!this.sharedShell && !this.visible && this.expanded) this.expanded = false;
                if (naturalVisible) this.applyExpandedState();
            },
        });
        // Register the subpanels and build their tabs, mounting each into its
        // section. Adding a subpanel is a single registry entry.
        const registryMap = new Map<TabKey, [string, string, HTMLDivElement, StudioPanel]>([
            ["system", ["System", "Molecular Hierarchy & Sequence", this.systemSection, this.systemPanel]],
            ["whole", ["Whole", "Overall Representation & Presets", this.wholeSection, this.wholePanel]],
            ["selection", ["Selections", "None", this.selectionSection, this.selectionPanel]],
            ["regions", ["Regions", "0", this.regionsSection, this.regionsPanel]],
            ["measures", ["Measures", "0", this.measuresSection, this.measuresPanel]],
            ["annotations", ["Annotations", "0", this.annotationsSection, this.annotationsPanel]],
            ["shapes", ["Shapes", "0", this.shapesSection, this.shapesPanel]],
            ["layers", ["Layers", "0", this.layersSection, this.layersPanel]],
            ["viewport", ["Viewport", "Dark", this.viewportSection, this.viewportPanel]],
            ["export", ["Export", "None", this.exportSection, this.exportPanel]],
        ]);

        const defaultOrder: TabKey[] = [
            "system",
            "whole",
            "selection",
            "regions",
            "measures",
            "annotations",
            "shapes",
            "layers",
            "viewport",
            "export",
        ];
        let tabOrder = [...defaultOrder];
        const savedOrder = readTabOrderStorage();
        if (savedOrder) {
            try {
                const parsed = JSON.parse(savedOrder);
                if (Array.isArray(parsed) && parsed.length === defaultOrder.length && parsed.every(k => defaultOrder.includes(k as TabKey))) {
                    tabOrder = parsed as TabKey[];
                }
            } catch (e) {
                // Ignore parsing errors
            }
        }

        for (const key of tabOrder) {
            const entry = registryMap.get(key);
            if (entry) {
                const [title, badge, section, panel] = entry;
                this.addTab(key, title, badge);
                panel.mount(section);
                this.panels.set(key, { section, panel });
            }
        }

        // Show the default tab.
        this.switchTab("system");
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
        const tooltips: Record<string, string> = {
            system: "Molecular hierarchy, chain sequence, and residue-level selections.",
            whole: "Global representation styling, visual presets, and overall system view.",
            selection: "Create, view, and modify active and saved selection queries.",
            regions: "Define and style spatial regions, boolean composition, and overlap inspection.",
            measures: "Measure distances, angles, and dihedrals between atoms.",
            annotations: "View and customize textual labels, 3D annotations, and overlays.",
            shapes: "Manage custom 3D geometric shapes and objects in the scene.",
            layers: "Configure drawing layers, rendering order, and depth settings.",
            viewport: "Adjust background color, lighting, camera, and display parameters.",
            export: "Export high-resolution images, coordinates, and system state files.",
        };
        const tooltip = tooltips[key];
        if (tooltip) {
            button.title = tooltip;
        }
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

        // Enable Drag & Drop
        button.draggable = true;

        button.addEventListener("dragstart", (e) => {
            if (e.dataTransfer) {
                e.dataTransfer.setData("text/plain", key);
                e.dataTransfer.effectAllowed = "move";
            }
            button.style.opacity = "0.4";
        });

        button.addEventListener("dragend", () => {
            button.style.opacity = "1";
            for (const tab of this.tabs.values()) {
                tab.button.style.borderTop = "0";
                tab.button.style.borderBottom = "0";
            }
        });

        button.addEventListener("dragover", (e) => {
            e.preventDefault();
            if (e.dataTransfer) {
                e.dataTransfer.dropEffect = "move";
            }
            const rect = button.getBoundingClientRect();
            const midpoint = rect.top + rect.height / 2;
            if (e.clientY < midpoint) {
                button.style.borderTop = "2px solid #6366f1";
                button.style.borderBottom = "0";
            } else {
                button.style.borderBottom = "2px solid #6366f1";
                button.style.borderTop = "0";
            }
        });

        button.addEventListener("dragleave", () => {
            button.style.borderTop = "0";
            button.style.borderBottom = "0";
        });

        button.addEventListener("drop", (e) => {
            e.preventDefault();
            button.style.borderTop = "0";
            button.style.borderBottom = "0";
            
            const draggedKey = e.dataTransfer ? e.dataTransfer.getData("text/plain") : "";
            if (!draggedKey || draggedKey === key) return;
            
            const order = this.getTabOrder();
            const draggedIdx = order.indexOf(draggedKey as TabKey);
            let targetIdx = order.indexOf(key);
            if (draggedIdx === -1 || targetIdx === -1) return;
            
            order.splice(draggedIdx, 1);
            
            const rect = button.getBoundingClientRect();
            const midpoint = rect.top + rect.height / 2;
            if (e.clientY >= midpoint) {
                targetIdx = order.indexOf(key);
                order.splice(targetIdx + 1, 0, draggedKey as TabKey);
            } else {
                targetIdx = order.indexOf(key);
                order.splice(targetIdx, 0, draggedKey as TabKey);
            }
            
            writeTabOrderStorage(order);

            this.reorderTabsDOM(order);
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

        // Toggle section visibility via the registry, driving render-on-show.
        for (const [tabKey, entry] of this.panels.entries()) {
            const isActive = tabKey === key;
            entry.section.style.display = isActive ? "flex" : "none";
            entry.panel.setVisible(isActive);
        }
        this.settingsSection.style.display = key === "settings" ? "flex" : "none";

        if (key === "settings") {
            this.renderSettingsSection();
        }
    }

    setStructure(structure: Structure | undefined): void {
        this.switchTab("system");
        this.systemPanel.setStructure(structure);
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
        if (this.runtimeVisibleOverride === visible) return;
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
        this.systemPanel.updateSelection(selection);
        this.selectionPanel.updateSelection(selection);
        this.regionsPanel.setCurrentSelection(selection);
        this.measuresPanel.setCurrentSelection(selection);
        this.annotationsPanel.setCurrentSelection(selection);
    }

    updateSelectionHistoryState(state: { canUndo: boolean; canRedo: boolean }): void {
        this.selectionPanel.updateHistory(state);
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.selectionPanel.setSavedSelections(items);
        this.regionsPanel.setSavedSelections(items);
    }

    updateSelectionQueryPreview(preview: SelectionQueryPreview): void {
        if (this.regionsPanel.updatePreview(preview)) return;
        this.selectionPanel.updatePreview(preview);
    }



    setRegions(items: RegionSummary[]): void {
        this.regionsPanel.setRegions(items);
        this.layersPanel.setRegions(items);
    }

    setRegionStyleOptions(options: { representations: string[]; presets: string[]; wholeHidden?: boolean }): void {
        this.regionsPanel.setStyleOptions(options);
    }

    setWholeSummary(summary: WholeSummary | null): void {
        this.wholePanel.setSummary(summary);
        this.systemPanel.setColorScheme(summary?.color_scheme === "physicochemical" ? "physicochemical" : "neutral");
    }

    updateWholeDetails(details: WholeDetails): void {
        this.wholePanel.updateDetails(details);
    }

    updateRegionDetails(details: RegionDetails): void {
        this.regionsPanel.updateDetails(details);
    }

    setShapes(items: ShapeSummary[], renderStatuses?: ReadonlyMap<string, ShapeRenderStatus>): void {
        this.shapesPanel.setShapes(items, renderStatuses);
    }

    updateShapeRenderStatus(status: ShapeRenderStatus): void {
        this.shapesPanel.updateRenderStatus(status);
    }

    setLayerObjects(items: LayerObjectSummary[]): void {
        this.layersPanel.setObjects(items);
    }

    setLayers(items: LayerSummary[]): void {
        this.layersPanel.setLayers(items);
    }

    /** Build the narrow context injected into a migrated subpanel. */
    private makePanelContext(key: TabKey): PanelContext {
        return {
            onAction: (action, details) => this.onAction?.(action, details),
            setBadge: (text) => {
                const badge = this.tabs.get(key)?.badge;
                if (badge) badge.textContent = text;
            },
        };
    }

    setAnnotations(items: AnnotationSummary[], settings: AnnotationSettings): void {
        this.annotationsPanel.setAnnotations(items, settings);
    }

    setMeasurements(items: MeasurementSummary[], settings: MeasurementSettings): void {
        this.measuresPanel.setMeasurements(items, settings);
    }

    updateMeasurementSeries(payload: MeasurementSeries): void {
        this.measuresPanel.updateSeries(payload);
    }

    setScene(state: SceneState): void {
        this.viewportPanel.setScene(state);
        this.exportPanel.setScene(state);
    }

    setSections(items: SectionSummary[], settings: SectionSettings): void {
        this.viewportPanel.setSections(items, settings);
    }

    updateContextTarget(target: ContextMenuTarget | null): void {
        this.systemPanel.updateContextTarget(target);
    }

    addLabelOverlay(msg: AddLabelMessage): void {
        this.systemPanel.addLabelOverlay(msg);
    }

    clearAnnotationOverlays(): void {
        this.systemPanel.clearAnnotationOverlays();
    }

    clearAnnotationOverlaysByTag(tag?: string): void {
        this.systemPanel.clearAnnotationOverlaysByTag(tag);
    }

    retagAnnotationOverlays(oldTag: string, newTag: string): void {
        this.systemPanel.retagAnnotationOverlays(oldTag, newTag);
    }

    focusItem(item: ActiveSelectionItem) {
        return this.systemPanel.focusItem(item);
    }

    dispose(): void {
        this.systemPanel.dispose();
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

    render(): void {
        this.systemPanel.rebuild();
    }


    private makeSectionHeader(title: string): HTMLDivElement {
        return makeSectionHeader(title);
    }

    // Compact header for the System tab, hosting the residue color-scheme (🎨) toggle.
    // The palette button used to live in a section titled "Structure"; the navigate-panel
    // redesign renamed that section to the "System" tab, so it is re-anchored here.




    // ── 1. Selection Section Rendering ───────────────────────



    // ── 2. Regions Section Rendering ─────────────────────────

    // ── 5. Viewport Section Rendering ────────────────────────

    // ── Helper UI Constructors ──────────────────────────────
    private makeButton(text: string, onClick: () => void): HTMLButtonElement {
        return makeButton(text, onClick);
    }

    private makeRowElement(
        titleText: string,
        subtitleText: string,
        onActivate?: () => void,
        onDelete?: () => void,
        visibility?: { hidden?: boolean; onToggleVisibility?: (hidden: boolean) => void },
        onStyle?: () => void
    ): HTMLDivElement {
        return makeRowElement(titleText, subtitleText, onActivate, onDelete, visibility, onStyle);
    }

    private makeSettingsCard(titleText: string): HTMLDivElement {
        return makeSettingsCard(titleText);
    }

    private makeCheckboxRow(labelText: string, checked: boolean, onChange: (checked: boolean) => void): HTMLDivElement {
        return makeCheckboxRow(labelText, checked, onChange);
    }

    private makeStyledSelect(
        options: Array<string | { value: string; label: string }>,
        selectedValue: string,
        onChange: (value: string) => void,
    ): HTMLSelectElement {
        return makeStyledSelect(options, selectedValue, onChange);
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

    private getTabOrder(): TabKey[] {
        const order: TabKey[] = [];
        for (let i = 0; i < this.tabsContainer.children.length; i++) {
            const child = this.tabsContainer.children[i];
            const key = child.getAttribute("data-molsysviewer-group-panel-tab");
            if (key) {
                order.push(key as TabKey);
            }
        }
        return order;
    }

    private reorderTabsDOM(order: TabKey[]): void {
        for (const key of order) {
            const tab = this.tabs.get(key);
            if (tab) {
                this.tabsContainer.appendChild(tab.button);
            }
        }
    }
}
