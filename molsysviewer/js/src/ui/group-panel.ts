import { Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, ActiveSelectionSetOperation, GroupSelectionItem, buildGroupItemsFromStructure } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import { GroupStrip } from "./group-strip";
import { ManualQueryComposer } from "./query-composer";
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

type OnSelect = (items: ActiveSelectionItem[], op: ActiveSelectionSetOperation) => void;
type OnInteraction = (item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;
type SavedSelectionSummary = { tag: string; atom_count: number; element_level?: string };
type RegionSummary = {
    tag: string;
    atom_count: number;
    hidden: boolean;
    representation?: string;
    preset?: string;
    representation_params?: Record<string, unknown>;
    overlap_tags?: string[];
    available_attributes?: string[];
};
type RegionDetails = {
    request_id?: number;
    tag: string;
    atom_count: number;
    group_count: number;
    chain_count: number;
    center_nm: number[];
    structure_index: number;
};
type WorkspaceOption = { id: string; title: string; subtitle?: string };
type PanelOption = { id: string; title: string; active?: boolean };
type SelectionQuerySyntax = "MolSysMT" | "Indices";
type SelectionQueryPreview = {
    request_id?: number;
    ok?: boolean;
    count?: number;
    error_message?: string;
    status?: "pending";
};

type TabKey = "system" | "whole" | "selection" | "regions" | "measures" | "annotations" | "shapes" | "layers" | "viewport" | "export" | "settings";

export class GroupPanel {
    private static readonly SELECTION_STYLE_ID = "molsysviewer-selection-panel-design-system";

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
    private readonly systemStripsRow: HTMLDivElement;
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
    private selectionQueryExpression = "";
    private selectionQuerySyntax: SelectionQuerySyntax = "MolSysMT";
    private selectionQueryPreviewRequest = 0;
    private selectionQueryPreviewTimer: ReturnType<typeof setTimeout> | null = null;
    private selectionQueryPreview: SelectionQueryPreview | null = null;
    private selectionCheatSheetOpen = false;
    private selectionSpatialDistance = "4.0";
    private selectionCanUndo = false;
    private selectionCanRedo = false;
    private regionQueryComposer: ManualQueryComposer | null = null;
    private regionCreateOrigin: "active" | "query" | "split" = "active";
    private regionCreateTag = "";
    private regionCreateRepresentation = "";
    private regionSplitLevel: "chain" | "molecule" | "entity" = "chain";
    private regionRenameTag: string | null = null;
    private regionCreateCollision: {
        action: string;
        details: Record<string, unknown>;
        tag: string;
    } | null = null;
    private regionRenameCollisionTag: string | null = null;
    private regionStyleRepresentations: string[] = [];
    private regionStylePresets: string[] = [];
    private regionBooleanA = "";
    private regionBooleanB = "";
    private regionBooleanOperation: "union" | "intersection" | "difference" = "union";
    private regionBooleanOutput = "";
    private regionComposeCollision: {
        tag: string;
        details: Record<string, unknown>;
    } | null = null;
    private readonly regionInspectOpen = new Set<string>();
    private readonly regionDetails = new Map<string, RegionDetails>();
    private readonly regionDetailsRequests = new Map<string, number>();
    private nextRegionDetailsRequest = 1;
    private regionBooleanAttention = false;
    private regionBooleanComposerElement: HTMLDivElement | null = null;

    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToWorkbench?: () => void;
    private onNavigateToSettings?: () => void;
    private runtimeVisibleOverride: boolean | null = null;
    private readonly sharedShell: boolean;
    private visible = false;
    private activeColorScheme: "neutral" | "physicochemical" = "neutral";

    private static ensureSelectionDesignSystemStyles(): void {
        if (typeof document === "undefined") return;
        if (document.getElementById?.(GroupPanel.SELECTION_STYLE_ID)) return;
        if (!document.head) return;

        const style = document.createElement("style");
        style.id = GroupPanel.SELECTION_STYLE_ID;
        style.textContent = `
[data-molsysviewer-group-panel] {
    --bg-sidebar: #12131a;
    --bg-card: rgba(255, 255, 255, 0.03);
    --bg-card-hover: rgba(255, 255, 255, 0.06);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --accent-indigo: #6366f1;
    --accent-indigo-soft: rgba(99, 102, 241, 0.16);
    --accent-indigo-border: rgba(129, 140, 248, 0.34);
    --accent-indigo-glow: 0 0 12px rgba(99, 102, 241, 0.25);
    --text-primary: #f4f4f5;
    --text-secondary: rgba(244, 244, 245, 0.68);
    --text-muted: rgba(244, 244, 245, 0.48);
}

[data-molsysviewer-group-panel-section="selection"] {
    background: var(--bg-sidebar);
}

[data-molsysviewer-selection-active-card],
[data-molsysviewer-selection-query-composer="true"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.055), rgba(255,255,255,0.012)) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.055);
    backdrop-filter: blur(12px);
}

[data-molsysviewer-selection-query-composer="true"]:focus-within {
    border-color: rgba(99, 102, 241, 0.36) !important;
    box-shadow: var(--accent-indigo-glow), inset 0 1px 0 rgba(255,255,255,0.06);
}

[data-molsysviewer-selection-query-input="true"]:focus,
[data-molsysviewer-selection-query-syntax="true"]:focus,
[data-molsysviewer-selection-spatial-distance="true"]:focus {
    border-color: rgba(99, 102, 241, 0.46) !important;
    box-shadow: var(--accent-indigo-glow);
    outline: none;
}

[data-molsysviewer-selection-query-preset] {
    background: var(--accent-indigo-soft) !important;
    border-color: var(--accent-indigo-border) !important;
    transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}

[data-molsysviewer-selection-query-preset]:hover {
    background: rgba(99, 102, 241, 0.24) !important;
    border-color: rgba(165, 180, 252, 0.48) !important;
    transform: translateY(-1px);
}

[data-molsysviewer-saved-selection-list] {
    background: transparent;
}

[data-molsysviewer-saved-selection-card] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        transform 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[data-molsysviewer-saved-selection-card]:hover,
[data-molsysviewer-saved-selection-card][data-molsysviewer-selection-row-hover="true"] {
    background: var(--bg-card-hover) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
    transform: translateY(-1px);
}

[data-molsysviewer-saved-selection-card][data-molsysviewer-selection-row-active="true"] {
    border-left: 3px solid var(--accent-indigo) !important;
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, rgba(255,255,255,0.03) 100%) !important;
}

[data-molsysviewer-selection-query-preview-status="ok"] {
    text-shadow: 0 0 10px rgba(134, 239, 172, 0.18);
}

[data-molsysviewer-selection-query-preview-status="error"] {
    text-shadow: 0 0 10px rgba(252, 165, 165, 0.16);
}

[data-molsysviewer-group-panel-section="regions"] {
    background: var(--bg-sidebar);
}

[data-molsysviewer-region-create],
[data-molsysviewer-region-boolean-composer],
[data-molsysviewer-region-card] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
}

[data-molsysviewer-region-card] {
    transition: background 0.16s ease, border-color 0.16s ease, opacity 0.16s ease,
        transform 0.16s ease;
}

[data-molsysviewer-region-card]:hover {
    background: var(--bg-card-hover) !important;
    border-color: rgba(255, 255, 255, 0.14) !important;
    transform: translateY(-1px);
}

[data-molsysviewer-region-overlap] {
    color: #facc15 !important;
    border-color: rgba(250, 204, 21, 0.34) !important;
    background: rgba(250, 204, 21, 0.08) !important;
}

[data-molsysviewer-region-boolean-composer][data-molsysviewer-region-boolean-attention="true"] {
    border-color: var(--accent-indigo) !important;
    box-shadow: var(--accent-indigo-glow);
    animation: molsysviewer-region-attention 0.9s ease;
}

@keyframes molsysviewer-region-attention {
    0%, 100% { box-shadow: none; }
    45% { box-shadow: var(--accent-indigo-glow); }
}

[data-molsysviewer-region-style-composer] {
    border-color: var(--accent-indigo-border) !important;
    background: rgba(99, 102, 241, 0.055) !important;
}

[data-molsysviewer-region-style-opacity] {
    accent-color: var(--accent-indigo);
}

[data-molsysviewer-region-inspect-panel] {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 5px 10px;
    padding: 8px;
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.14);
    color: var(--text-secondary);
    font-size: 10px;
}

[data-molsysviewer-region-inspect-center] {
    grid-column: 1 / -1;
    font-variant-numeric: tabular-nums;
}
`;
        document.head.appendChild(style);
    }

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
        private readonly onChangeColorScheme?: (scheme: "neutral" | "physicochemical") => void,
        options?: { floating?: boolean; sharedShell?: FloatingPanelShell; model?: any },
    ) {
        GroupPanel.ensureSelectionDesignSystemStyles();
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
        this.wholeSection = this.createSection("whole");
        this.selectionSection = this.createSection("selection");
        this.selectionSection.tabIndex = 0;
        this.selectionSection.setAttribute("data-molsysviewer-selection-panel", "true");
        this.selectionSection.addEventListener("keydown", (event) => this.handleSelectionPanelKeydown(event));
        this.regionsSection = this.createSection("regions");
        this.measuresSection = this.createSection("measures");
        this.annotationsSection = this.createSection("annotations");
        this.shapesSection = this.createSection("shapes");
        this.layersSection = this.createSection("layers");
        this.viewportSection = this.createSection("viewport");
        this.exportSection = this.createSection("export");
        this.settingsSection = this.createSection("settings");

        // System tab: a compact palette header on top, horizontal sequence strips below.
        Object.assign(this.systemSection.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "hidden",
            gap: "6px",
        });
        this.systemSection.appendChild(this.makeSystemHeader());
        this.systemStripsRow = document.createElement("div");
        Object.assign(this.systemStripsRow.style, {
            display: "flex",
            flexDirection: "row",
            flex: "1 1 0",
            minHeight: "0",
            overflowX: "auto",
            overflowY: "hidden",
            paddingBottom: "8px",
        });
        this.systemSection.appendChild(this.systemStripsRow);

        // Add tabs
        this.addTab("system", "System", "None");
        this.addTab("whole", "Whole", "None");
        this.addTab("selection", "Selection", "None");
        this.addTab("regions", "Regions", "0");
        this.addTab("measures", "Measures", "0");
        this.addTab("annotations", "Annotations", "0");
        this.addTab("shapes", "Shapes", "0");
        this.addTab("layers", "Layers", "0");
        this.addTab("viewport", "Viewport", "Dark");
        this.addTab("export", "Export", "None");

        // Switch to system tab by default
        this.switchTab("system");

        // Render empty sections initially
        this.renderSelectionSection();
        this.renderRegionsSection();
        this.renderWholeSection();
        this.renderMeasuresSection();
        this.renderAnnotationsSection();
        this.renderShapesSection();
        this.renderLayersSection();
        this.renderViewportSection();
        this.renderExportSection();
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
        this.wholeSection.style.display = key === "whole" ? "flex" : "none";
        this.selectionSection.style.display = key === "selection" ? "flex" : "none";
        this.regionsSection.style.display = key === "regions" ? "flex" : "none";
        this.measuresSection.style.display = key === "measures" ? "flex" : "none";
        this.annotationsSection.style.display = key === "annotations" ? "flex" : "none";
        this.shapesSection.style.display = key === "shapes" ? "flex" : "none";
        this.layersSection.style.display = key === "layers" ? "flex" : "none";
        this.viewportSection.style.display = key === "viewport" ? "flex" : "none";
        this.exportSection.style.display = key === "export" ? "flex" : "none";
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
        if (this.regionCreateOrigin === "active") {
            this.renderRegionsSection();
        }
    }

    updateSelectionHistoryState(state: { canUndo: boolean; canRedo: boolean }): void {
        this.selectionCanUndo = state.canUndo;
        this.selectionCanRedo = state.canRedo;
        this.renderSelectionSection();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.renderSelectionSection();
    }

    updateSelectionQueryPreview(preview: SelectionQueryPreview): void {
        if (this.regionQueryComposer?.updatePreview(preview)) {
            this.renderRegionsSection();
            return;
        }
        const requestId = typeof preview.request_id === "number" ? preview.request_id : undefined;
        if (requestId !== undefined && requestId !== this.selectionQueryPreviewRequest) return;
        this.selectionQueryPreview = preview;
        this.renderSelectionSection();
    }

    private handleSelectionPanelKeydown(event: KeyboardEvent): void {
        if (!(event.ctrlKey || event.metaKey)) return;
        if (this.isEditableTarget(event.target)) return;
        const key = event.key.toLowerCase();
        if (key === "z" && !event.shiftKey) {
            if (!this.selectionCanUndo) return;
            event.preventDefault();
            event.stopPropagation();
            this.onAction?.("undo_active_selection");
        } else if (key === "y" || (key === "z" && event.shiftKey)) {
            if (!this.selectionCanRedo) return;
            event.preventDefault();
            event.stopPropagation();
            this.onAction?.("redo_active_selection");
        }
    }

    private isEditableTarget(target: EventTarget | null): boolean {
        const node = target as HTMLElement | null;
        if (!node) return false;
        const tagName = node.tagName?.toLowerCase();
        return tagName === "input" || tagName === "textarea" || tagName === "select" || node.isContentEditable === true;
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        const tags = this.regions.map(item => item.tag);
        if (!tags.includes(this.regionBooleanA)) {
            this.regionBooleanA = tags[0] ?? "";
        }
        if (!tags.includes(this.regionBooleanB) || this.regionBooleanB === this.regionBooleanA) {
            this.regionBooleanB = tags.find(tag => tag !== this.regionBooleanA) ?? "";
        }
        for (const tag of [...this.regionInspectOpen]) {
            if (!tags.includes(tag)) {
                this.regionInspectOpen.delete(tag);
                this.regionDetails.delete(tag);
                this.regionDetailsRequests.delete(tag);
            }
        }

        // Update sidebar Regions badge
        const badge = this.tabs.get("regions")?.badge;
        if (badge) {
            badge.textContent = String(items.length);
        }

        this.renderRegionsSection();
    }

    setRegionStyleOptions(options: { representations: string[]; presets: string[] }): void {
        this.regionStyleRepresentations = [...options.representations];
        this.regionStylePresets = [...options.presets];
    }

    updateRegionDetails(details: RegionDetails): void {
        const expectedRequest = this.regionDetailsRequests.get(details.tag);
        if (
            expectedRequest === undefined
            || details.request_id !== expectedRequest
            || !this.regionInspectOpen.has(details.tag)
        ) {
            return;
        }
        this.regionDetails.set(details.tag, details);
        this.renderRegionsSection();
    }

    setShapes(items: NavigateItem[]): void {
        this.shapes = [...items];
        this.updateBadges();
        this.renderShapesSection();
    }

    setAnnotations(items: NavigateItem[]): void {
        this.annotations = [...items];
        this.updateBadges();
        this.renderAnnotationsSection();
    }

    setMeasurements(items: NavigateItem[]): void {
        this.measurements = [...items];
        this.updateBadges();
        this.renderMeasuresSection();
    }

    private updateBadges(): void {
        const measuresBadge = this.tabs.get("measures")?.badge;
        if (measuresBadge) {
            measuresBadge.textContent = String(this.measurements.length);
        }
        const annotationsBadge = this.tabs.get("annotations")?.badge;
        if (annotationsBadge) {
            annotationsBadge.textContent = String(this.annotations.length);
        }
        const shapesBadge = this.tabs.get("shapes")?.badge;
        if (shapesBadge) {
            shapesBadge.textContent = String(this.shapes.length);
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
        this.renderExportSection();
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

    render(): void {
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
                strip = new GroupStrip(this.systemStripsRow, chain, this.onSelect, this.onInteraction, this.onFocus, this.onHover, this.onContext, this.onAnnotationContext);
                this.strips.set(chain, strip);
            }
            strip.setColorScheme(this.activeColorScheme);
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
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            position: "relative",
            width: "100%",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            paddingBottom: "6px",
            marginBottom: "6px",
        });

        const text = document.createElement("span");
        text.textContent = title;
        header.appendChild(text);

        return header;
    }

    // Compact header for the System tab, hosting the residue color-scheme (🎨) toggle.
    // The palette button used to live in a section titled "Structure"; the navigate-panel
    // redesign renamed that section to the "System" tab, so it is re-anchored here.
    private makeSystemHeader(): HTMLDivElement {
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            position: "relative",
            width: "100%",
            flex: "0 0 auto",
            gap: "8px",
        });
        header.appendChild(this.makeModifierLegend());
        header.appendChild(this.makeColorSchemeButton());
        return header;
    }

    private makeModifierLegend(): HTMLDivElement {
        const legend = document.createElement("div");
        legend.setAttribute("data-molsysviewer-selection-modifier-legend", "true");
        Object.assign(legend.style, {
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "6px",
            minWidth: "0",
            color: "rgba(244,244,245,0.56)",
            fontSize: "10px",
            lineHeight: "1.2",
        });

        const entries: Array<[string, string]> = [
            ["Click", "Replace"],
            ["Shift", "Add/toggle"],
            ["Shift+Alt", "Range"],
        ];
        for (const [key, label] of entries) {
            const item = document.createElement("span");
            item.setAttribute("data-molsysviewer-selection-modifier-legend-item", key);
            Object.assign(item.style, {
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                whiteSpace: "nowrap",
            });

            const keyEl = document.createElement("span");
            Object.assign(keyEl.style, {
                padding: "1px 4px",
                borderRadius: "4px",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "rgba(244,244,245,0.82)",
                fontWeight: "700",
            });
            keyEl.textContent = key;

            const labelEl = document.createElement("span");
            labelEl.textContent = label;

            item.appendChild(keyEl);
            item.appendChild(labelEl);
            legend.appendChild(item);
        }
        return legend;
    }

    private makeColorSchemeButton(): HTMLButtonElement {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.innerHTML = "🎨";
        btn.title = "Residue color scheme";
        btn.setAttribute("data-molsysviewer-color-scheme-toggle", "true");
        Object.assign(btn.style, {
            background: "transparent",
            border: "none",
            color: "rgba(244,244,245,0.6)",
            cursor: "pointer",
            padding: "2px 4px",
            fontSize: "12px",
            outline: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
        });
        btn.addEventListener("mouseenter", () => {
            btn.style.color = "rgba(244,244,245,0.95)";
        });
        btn.addEventListener("mouseleave", () => {
            btn.style.color = "rgba(244,244,245,0.6)";
        });
        btn.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.toggleColorSchemeMenu(btn);
        });
        return btn;
    }

    private toggleColorSchemeMenu(button: HTMLElement): void {
        const existing = this.root.querySelector("[data-molsysviewer-color-scheme-menu]");
        if (existing) {
            existing.remove();
            return;
        }

        const dropdown = document.createElement("div");
        dropdown.setAttribute("data-molsysviewer-color-scheme-menu", "true");
        Object.assign(dropdown.style, {
            position: "absolute",
            top: "20px",
            right: "0",
            background: "#18181b",
            border: "1px solid #3f3f46",
            borderRadius: "4px",
            zIndex: "100",
            padding: "4px 0",
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.5)",
            display: "flex",
            flexDirection: "column",
            minWidth: "140px",
        });

        const makeOption = (label: string, value: "neutral" | "physicochemical") => {
            const opt = document.createElement("button");
            opt.type = "button";
            opt.setAttribute("data-molsysviewer-color-scheme-option", value);
            opt.textContent = label;
            const active = this.activeColorScheme === value;
            Object.assign(opt.style, {
                background: active ? "rgba(255,255,255,0.08)" : "transparent",
                border: "none",
                color: active ? "#ffffff" : "rgba(244,244,245,0.72)",
                padding: "6px 12px",
                fontSize: "11px",
                textAlign: "left",
                cursor: "pointer",
                fontWeight: active ? "700" : "400",
            });
            opt.addEventListener("mouseenter", () => {
                opt.style.background = "rgba(255,255,255,0.12)";
                opt.style.color = "#ffffff";
            });
            opt.addEventListener("mouseleave", () => {
                opt.style.background = active ? "rgba(255,255,255,0.08)" : "transparent";
                opt.style.color = active ? "#ffffff" : "rgba(244,244,245,0.72)";
            });
            opt.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropdown.remove();
                if (this.activeColorScheme !== value) {
                    this.activeColorScheme = value;
                    this.render();
                    this.onChangeColorScheme?.(value);
                }
            });
            return opt;
        };

        dropdown.appendChild(makeOption("Neutral", "neutral"));
        dropdown.appendChild(makeOption("Physicochemical Class", "physicochemical"));

        button.parentElement?.appendChild(dropdown);

        const onOutsideClick = (e: MouseEvent) => {
            if (!dropdown.contains(e.target as Node) && e.target !== button) {
                dropdown.remove();
                window.removeEventListener("click", onOutsideClick);
            }
        };
        setTimeout(() => window.addEventListener("click", onOutsideClick), 0);
    }

    // ── 1. Selection Section Rendering ───────────────────────
    private renderSelectionSection(): void {
        this.selectionSection.replaceChildren();

        // A. Active Selection Area
        this.selectionSection.appendChild(this.makeSectionHeader("Active Selection"));
        const activeContainer = document.createElement("div");
        activeContainer.setAttribute("data-molsysviewer-selection-active-card", "true");
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

        const historyRow = document.createElement("div");
        Object.assign(historyRow.style, {
            display: "flex",
            gap: "6px",
            alignItems: "center",
        });
        const undoBtn = this.makeButton("↶ Undo", () => this.onAction?.("undo_active_selection"));
        undoBtn.setAttribute("data-molsysviewer-selection-undo", "true");
        undoBtn.disabled = !this.selectionCanUndo;
        const redoBtn = this.makeButton("↷ Redo", () => this.onAction?.("redo_active_selection"));
        redoBtn.setAttribute("data-molsysviewer-selection-redo", "true");
        redoBtn.disabled = !this.selectionCanRedo;
        for (const btn of [undoBtn, redoBtn]) {
            btn.style.flex = "0 0 auto";
            if (btn.disabled) {
                btn.style.opacity = "0.42";
                btn.style.cursor = "not-allowed";
            }
            historyRow.appendChild(btn);
        }
        activeContainer.appendChild(historyRow);

        const quickRow = document.createElement("div");
        Object.assign(quickRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "6px",
        });
        const allBtn = this.makeButton("All", () =>
            this.onAction?.("set_active_selection_operation", { operation: "all" })
        );
        allBtn.setAttribute("data-molsysviewer-selection-all", "true");
        const noneBtn = this.makeButton("None", () =>
            this.onAction?.("set_active_selection_operation", { operation: "none" })
        );
        noneBtn.setAttribute("data-molsysviewer-selection-none", "true");
        const invertBtn = this.makeButton("Invert", () =>
            this.onAction?.("set_active_selection_operation", { operation: "invert" })
        );
        invertBtn.setAttribute("data-molsysviewer-selection-invert", "true");
        quickRow.appendChild(allBtn);
        quickRow.appendChild(noneBtn);
        quickRow.appendChild(invertBtn);
        activeContainer.appendChild(quickRow);

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

            const showForm = (mode: "save" | "region" | "label") => {
                inlineForm.style.display = "flex";
                inlineInput.value = "";
                inlineInput.placeholder = mode === "save"
                    ? "Selection name..."
                    : mode === "region"
                        ? "Region name..."
                        : "Label text...";
                inlineConfirm.textContent = mode === "save"
                    ? "Save"
                    : mode === "region"
                        ? "Create"
                        : "Add Label";

                // Remove previous listeners
                const newConfirm = inlineConfirm.cloneNode(true) as HTMLButtonElement;
                const newCancel = inlineCancel.cloneNode(true) as HTMLButtonElement;
                inlineConfirm.replaceWith(newConfirm);
                inlineCancel.replaceWith(newCancel);

                newConfirm.addEventListener("click", () => {
                    const tag = inlineInput.value.trim();
                    if (!tag) return;
                    if (mode === "save") {
                        const exists = this.savedSelections.some(s => s.tag === tag);
                        if (exists) {
                            const doOverwrite = typeof confirm === "function" ? confirm(`A saved selection named "${tag}" already exists. Overwrite?`) : true;
                            if (doOverwrite) {
                                this.onAction?.("delete_selection", { tag });
                                this.onAction?.("save_selection", { tag });
                            } else {
                                return;
                            }
                        } else {
                            this.onAction?.("save_selection", { tag });
                        }
                    } else if (mode === "region") {
                        const exists = this.regions.some(r => r.tag === tag);
                        if (exists) {
                            const doOverwrite = typeof confirm === "function" ? confirm(`A region named "${tag}" already exists. Overwrite?`) : true;
                            if (doOverwrite) {
                                this.onAction?.("delete_region", { tag });
                                this.onAction?.("create_region_from_selection", { tag });
                            } else {
                                return;
                            }
                        } else {
                            this.onAction?.("create_region_from_selection", { tag });
                        }
                    } else {
                        this.onAction?.("add_label_from_selection", { text: tag });
                    }
                    inlineForm.style.display = "none";
                });
                newCancel.addEventListener("click", () => {
                    inlineForm.style.display = "none";
                });
                inlineInput.focus?.();
            };

            const clearBtn = this.makeButton("Clear", () => this.onSelect([], "replace"));
            const saveBtn = this.makeButton("Save", () => showForm("save"));
            const regionBtn = this.makeButton("Create Region", () => showForm("region"));
            const labelBtn = this.makeButton("Add Label", () => showForm("label"));
            clearBtn.setAttribute("data-molsysviewer-selection-clear", "true");
            saveBtn.setAttribute("data-molsysviewer-selection-save", "true");
            regionBtn.setAttribute("data-molsysviewer-selection-to-region", "true");
            labelBtn.setAttribute("data-molsysviewer-selection-to-label", "true");
            inlineForm.setAttribute("data-molsysviewer-selection-inline-form", "true");
            inlineInput.setAttribute("data-molsysviewer-selection-inline-input", "true");

            btnRow.appendChild(clearBtn);
            btnRow.appendChild(saveBtn);
            btnRow.appendChild(regionBtn);
            btnRow.appendChild(labelBtn);
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

        // B. Query Composer
        this.selectionSection.appendChild(this.renderSelectionQueryComposer());

        // C. Saved Selections Area
        this.selectionSection.appendChild(this.makeSectionHeader("Saved Selections"));
        const savedList = document.createElement("div");
        savedList.setAttribute("data-molsysviewer-saved-selection-list", "true");
        Object.assign(savedList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.selectionSection.appendChild(savedList);

        if (this.savedSelections.length > 0) {
            const sorted = [...this.savedSelections].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                const card = document.createElement("div");
                card.setAttribute("data-molsysviewer-group-panel-row", "true");
                card.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
                card.setAttribute("data-molsysviewer-saved-selection-card", item.tag);
                Object.assign(card.style, {
                    display: "flex",
                    flexDirection: "column",
                    padding: "8px 10px",
                    borderRadius: "8px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.06)",
                    gap: "6px",
                    transition: "background 0.1s ease",
                    cursor: "pointer",
                });
                card.addEventListener("mouseenter", () => {
                    card.setAttribute("data-molsysviewer-selection-row-hover", "true");
                    card.style.background = "rgba(255,255,255,0.09)";
                });
                card.addEventListener("mouseleave", () => {
                    card.setAttribute("data-molsysviewer-selection-row-hover", "false");
                    card.style.background = "rgba(255,255,255,0.05)";
                });
                card.addEventListener("click", (e) => {
                    if (e && e.target && e.target !== card) {
                        return;
                    }
                    e?.preventDefault();
                    e?.stopPropagation();
                    this.onActivateSavedSelection(item.tag);
                });

                // Top row (Title & Meta)
                const topRow = document.createElement("div");
                Object.assign(topRow.style, {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                });
                const title = document.createElement("div");
                Object.assign(title.style, {
                    fontSize: "12px",
                    fontWeight: "600",
                    color: "#f4f4f5",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                });
                title.textContent = item.tag;

                const subtitle = document.createElement("span");
                Object.assign(subtitle.style, {
                    fontSize: "10px",
                    color: "rgba(244,244,245,0.56)",
                    marginLeft: "6px",
                    fontWeight: "normal",
                });
                const levelText = item.element_level ? ` · ${item.element_level} level` : " · group level";
                subtitle.textContent = `(${item.atom_count} atoms${levelText})`;
                title.appendChild(subtitle);
                topRow.appendChild(title);
                card.appendChild(topRow);

                // Buttons container row
                const btnRow = document.createElement("div");
                btnRow.setAttribute("data-molsysviewer-saved-selection-buttons-row", item.tag);
                Object.assign(btnRow.style, {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px",
                });

                // Inline form container (Rename / Region / Label)
                const inlineForm = document.createElement("div");
                Object.assign(inlineForm.style, {
                    display: "none",
                    flexDirection: "row",
                    gap: "6px",
                    marginTop: "2px",
                });
                const inlineInput = document.createElement("input");
                inlineInput.type = "text";
                Object.assign(inlineInput.style, {
                    flex: "1 1 0",
                    background: "rgba(0,0,0,0.2)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "6px",
                    padding: "4px 6px",
                    color: "#fff",
                    fontSize: "11px",
                    outline: "none",
                });
                card.appendChild(inlineForm);

                const showForm = (mode: "rename" | "region" | "label") => {
                    btnRow.style.display = "none";

                    // Clear and reconstruct to avoid cloneNode / replaceWith
                    inlineForm.replaceChildren();
                    inlineInput.value = "";
                    inlineInput.placeholder = mode === "rename" ? "New name..." : mode === "region" ? "Region name..." : "Label text...";

                    const inlineConfirm = document.createElement("button");
                    inlineConfirm.type = "button";
                    inlineConfirm.textContent = mode === "rename" ? "Rename" : mode === "region" ? "Create" : "Add Label";
                    Object.assign(inlineConfirm.style, {
                        background: "#6366f1",
                        border: "0",
                        borderRadius: "6px",
                        padding: "4px 8px",
                        color: "#fff",
                        fontSize: "11px",
                        fontWeight: "600",
                        cursor: "pointer",
                    });

                    const inlineCancel = document.createElement("button");
                    inlineCancel.type = "button";
                    inlineCancel.textContent = "Cancel";
                    Object.assign(inlineCancel.style, {
                        background: "rgba(255,255,255,0.08)",
                        border: "0",
                        borderRadius: "6px",
                        padding: "4px 8px",
                        color: "#e4e4e7",
                        fontSize: "11px",
                        cursor: "pointer",
                    });

                    inlineConfirm.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const val = inlineInput.value.trim();
                        if (!val) return;
                        if (mode === "rename") {
                            const exists = this.savedSelections.some(s => s.tag === val);
                            if (exists) {
                                if (val === item.tag) {
                                    inlineForm.style.display = "none";
                                    btnRow.style.display = "flex";
                                    return;
                                }
                                const doOverwrite = typeof confirm === "function" ? confirm(`A saved selection named "${val}" already exists. Overwrite?`) : true;
                                if (doOverwrite) {
                                    this.onAction?.("delete_selection", { tag: val });
                                    this.onAction?.("rename_selection", { tag: item.tag, new_tag: val });
                                } else {
                                    return;
                                }
                            } else {
                                this.onAction?.("rename_selection", { tag: item.tag, new_tag: val });
                            }
                        } else if (mode === "region") {
                            const exists = this.regions.some(r => r.tag === val);
                            if (exists) {
                                const doOverwrite = typeof confirm === "function" ? confirm(`A region named "${val}" already exists. Overwrite?`) : true;
                                if (doOverwrite) {
                                    this.onAction?.("delete_region", { tag: val });
                                    this.onAction?.("create_region_from_saved_selection", { selection_tag: item.tag, tag: val });
                                } else {
                                    return;
                                }
                            } else {
                                this.onAction?.("create_region_from_saved_selection", { selection_tag: item.tag, tag: val });
                            }
                        } else if (mode === "label") {
                            this.onAction?.("create_label_from_saved_selection", { selection_tag: item.tag, text: val });
                        }
                        inlineForm.style.display = "none";
                        btnRow.style.display = "flex";
                    });

                    inlineCancel.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        inlineForm.style.display = "none";
                        btnRow.style.display = "flex";
                    });

                    inlineForm.appendChild(inlineInput);
                    inlineForm.appendChild(inlineConfirm);
                    inlineForm.appendChild(inlineCancel);

                    inlineForm.style.display = "flex";
                    inlineInput.focus?.();
                };

                const activateBtn = this.makeButton("Activate", () => this.onActivateSavedSelection(item.tag));
                activateBtn.setAttribute("data-molsysviewer-saved-selection-activate", item.tag);
                const unionBtn = this.makeButton("+Union", () => this.onAction?.("compose_saved_selection", { tag: item.tag, op: "add" }));
                unionBtn.setAttribute("data-molsysviewer-saved-selection-compose-add", item.tag);
                const subBtn = this.makeButton("-Sub", () => this.onAction?.("compose_saved_selection", { tag: item.tag, op: "subtract" }));
                subBtn.setAttribute("data-molsysviewer-saved-selection-compose-subtract", item.tag);
                const intBtn = this.makeButton("∩Int", () => this.onAction?.("compose_saved_selection", { tag: item.tag, op: "intersect" }));
                intBtn.setAttribute("data-molsysviewer-saved-selection-compose-intersect", item.tag);

                const renameBtn = this.makeButton("Rename", () => showForm("rename"));
                renameBtn.setAttribute("data-molsysviewer-saved-selection-rename", item.tag);
                const regionBtn = this.makeButton("→Region", () => showForm("region"));
                regionBtn.setAttribute("data-molsysviewer-saved-selection-to-region", item.tag);
                const labelBtn = this.makeButton("→Label", () => showForm("label"));
                labelBtn.setAttribute("data-molsysviewer-saved-selection-to-label", item.tag);

                const deleteBtn = this.makeButton("🗑", () => this.onAction?.("delete_selection", { tag: item.tag }));
                deleteBtn.setAttribute("data-molsysviewer-saved-selection-delete", item.tag);

                for (const btn of [activateBtn, unionBtn, subBtn, intBtn, renameBtn, regionBtn, labelBtn, deleteBtn]) {
                    btn.style.flex = "0 1 auto";
                    btn.style.padding = "3px 6px";
                    btn.style.fontSize = "10px";
                    btnRow.appendChild(btn);
                }

                card.appendChild(btnRow);
                savedList.appendChild(card);
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

    private renderSelectionQueryComposer(): HTMLDivElement {
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-selection-query-composer", "true");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.05)",
        });

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "700",
            color: "#f4f4f5",
        });
        title.textContent = "Select by Query";
        container.appendChild(title);

        const inputRow = document.createElement("div");
        Object.assign(inputRow.style, {
            display: "flex",
            gap: "6px",
            alignItems: "center",
        });

        const input = document.createElement("input");
        input.type = "text";
        input.value = this.selectionQueryExpression;
        input.placeholder = this.selectionQuerySyntax === "Indices" ? "0, 1, 2" : "molecule_type==\"protein\"";
        input.setAttribute("data-molsysviewer-selection-query-input", "true");
        Object.assign(input.style, {
            flex: "1 1 0",
            minWidth: "0",
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 8px",
            color: "#fff",
            fontSize: "11px",
            outline: "none",
        });
        input.addEventListener("input", () => {
            this.selectionQueryExpression = input.value;
            this.scheduleSelectionQueryPreview();
        });

        const syntax = document.createElement("select");
        syntax.setAttribute("data-molsysviewer-selection-query-syntax", "true");
        for (const item of ["MolSysMT", "Indices"] as const) {
            const option = document.createElement("option");
            option.value = item;
            option.textContent = item;
            option.selected = item === this.selectionQuerySyntax;
            syntax.appendChild(option);
        }
        Object.assign(syntax.style, {
            flex: "0 0 auto",
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 8px",
            color: "#f4f4f5",
            fontSize: "11px",
            outline: "none",
        });
        syntax.addEventListener("change", () => {
            this.selectionQuerySyntax = syntax.value === "Indices" ? "Indices" : "MolSysMT";
            this.scheduleSelectionQueryPreview();
            this.renderSelectionSection();
        });

        inputRow.appendChild(input);
        inputRow.appendChild(syntax);

        const helpBtn = this.makeButton("?", () => {
            this.selectionCheatSheetOpen = !this.selectionCheatSheetOpen;
            this.renderSelectionSection();
        });
        helpBtn.title = this.selectionCheatSheetOpen ? "Hide selection query examples" : "Show selection query examples";
        helpBtn.setAttribute("data-molsysviewer-selection-cheatsheet-toggle", "true");
        Object.assign(helpBtn.style, {
            flex: "0 0 30px",
            width: "30px",
            padding: "6px 0",
            fontWeight: "700",
        });
        inputRow.appendChild(helpBtn);
        container.appendChild(inputRow);

        const presetRow = document.createElement("div");
        presetRow.setAttribute("data-molsysviewer-selection-query-presets", "true");
        Object.assign(presetRow.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "5px",
            alignItems: "center",
        });
        const presetLabel = document.createElement("span");
        Object.assign(presetLabel.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.52)",
            marginRight: "2px",
        });
        presetLabel.textContent = "Presets";
        presetRow.appendChild(presetLabel);
        const presets = [
            { label: "protein", expression: 'molecule_type=="protein"' },
            { label: "water", expression: 'molecule_type=="water"' },
            { label: "backbone", expression: 'atom_name in ["N", "CA", "C", "O"]' },
            { label: "sidechain", expression: 'atom_name not in ["N", "CA", "C", "O"]' },
            { label: "ligand", expression: 'molecule_type=="small molecule"' },
        ] as const;
        for (const preset of presets) {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.textContent = preset.label;
            chip.title = preset.expression;
            chip.setAttribute("data-molsysviewer-selection-query-preset", preset.label);
            Object.assign(chip.style, {
                background: "rgba(99,102,241,0.12)",
                border: "1px solid rgba(129,140,248,0.24)",
                borderRadius: "999px",
                padding: "3px 8px",
                color: "#c7d2fe",
                fontSize: "10px",
                lineHeight: "14px",
                cursor: "pointer",
            });
            chip.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.selectionQuerySyntax = "MolSysMT";
                this.selectionQueryExpression = preset.expression;
                this.scheduleSelectionQueryPreview();
            });
            presetRow.appendChild(chip);
        }
        container.appendChild(presetRow);

        if (this.selectionCheatSheetOpen) {
            const cheatSheet = document.createElement("div");
            cheatSheet.setAttribute("data-molsysviewer-selection-cheatsheet", "true");
            Object.assign(cheatSheet.style, {
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: "4px",
                padding: "8px",
                borderRadius: "6px",
                background: "rgba(0,0,0,0.18)",
                border: "1px solid rgba(255,255,255,0.08)",
            });
            const examples = [
                ["Atom name", 'atom_name=="CA"'],
                ["Group index", "group_index in [10, 15]"],
                ["Chain", 'chain_id=="A"'],
                ["Protein", 'molecule_type=="protein"'],
                ["Nearby", "all within 5 angstroms of atom_index in [0]"],
                ["Bonded", "bonded to atom_index in [0]"],
            ] as const;
            for (const [label, expression] of examples) {
                const row = document.createElement("button");
                row.type = "button";
                row.setAttribute("data-molsysviewer-selection-cheatsheet-example", label);
                Object.assign(row.style, {
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "8px",
                    width: "100%",
                    background: "transparent",
                    border: "0",
                    padding: "3px 2px",
                    color: "#e4e4e7",
                    fontSize: "10px",
                    textAlign: "left",
                    cursor: "pointer",
                });
                const name = document.createElement("span");
                name.textContent = label;
                name.style.color = "rgba(244,244,245,0.62)";
                const code = document.createElement("code");
                code.textContent = expression;
                Object.assign(code.style, {
                    color: "#c7d2fe",
                    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                });
                row.appendChild(name);
                row.appendChild(code);
                row.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    this.selectionQuerySyntax = "MolSysMT";
                    this.selectionQueryExpression = expression;
                    this.scheduleSelectionQueryPreview();
                });
                cheatSheet.appendChild(row);
            }
            container.appendChild(cheatSheet);
        }

        const buttonRow = document.createElement("div");
        Object.assign(buttonRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: "6px",
        });
        const hasExpression = this.selectionQueryExpression.trim().length > 0;
        const apply = (op: "replace" | "add" | "subtract" | "intersect") => {
            const expression = this.selectionQueryExpression.trim();
            if (!expression) return;
            this.onAction?.("apply_selection_query", {
                expression,
                syntax: this.selectionQuerySyntax,
                op,
            });
        };
        const selectBtn = this.makeButton("Select", () => apply("replace"));
        selectBtn.setAttribute("data-molsysviewer-selection-query-apply", "replace");
        const unionBtn = this.makeButton("+Union", () => apply("add"));
        unionBtn.setAttribute("data-molsysviewer-selection-query-apply", "add");
        const subtractBtn = this.makeButton("-Subtract", () => apply("subtract"));
        subtractBtn.setAttribute("data-molsysviewer-selection-query-apply", "subtract");
        const intersectBtn = this.makeButton("Intersect", () => apply("intersect"));
        intersectBtn.setAttribute("data-molsysviewer-selection-query-apply", "intersect");
        for (const btn of [selectBtn, unionBtn, subtractBtn, intersectBtn]) {
            btn.disabled = !hasExpression;
            if (!hasExpression) {
                btn.style.opacity = "0.42";
                btn.style.cursor = "not-allowed";
            }
            buttonRow.appendChild(btn);
        }
        container.appendChild(buttonRow);

        const preview = document.createElement("div");
        preview.setAttribute("data-molsysviewer-selection-query-preview", "true");
        Object.assign(preview.style, {
            minHeight: "14px",
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
        });
        if (!this.selectionQueryExpression.trim()) {
            preview.textContent = "Enter a query to preview atom matches.";
            preview.setAttribute("data-molsysviewer-selection-query-preview-status", "idle");
        } else if (this.selectionQueryPreview?.status === "pending") {
            preview.textContent = "Checking query...";
            preview.style.color = "rgba(244,244,245,0.72)";
            preview.setAttribute("data-molsysviewer-selection-query-preview-status", "pending");
        } else if (this.selectionQueryPreview?.ok === true) {
            const count = Number(this.selectionQueryPreview.count ?? 0);
            preview.textContent = count === 1 ? "✓ 1 atom" : `✓ ${count} atoms`;
            preview.style.color = count > 0 ? "#86efac" : "#facc15";
            preview.setAttribute("data-molsysviewer-selection-query-preview-status", count > 0 ? "ok" : "empty");
        } else if (this.selectionQueryPreview?.ok === false) {
            preview.textContent = `✗ ${this.selectionQueryPreview.error_message ?? "invalid syntax"}`;
            preview.style.color = "#fca5a5";
            preview.setAttribute("data-molsysviewer-selection-query-preview-status", "error");
        } else {
            preview.textContent = "Checking query...";
            preview.setAttribute("data-molsysviewer-selection-query-preview-status", "pending");
        }
        container.appendChild(preview);

        const expandPanel = document.createElement("div");
        expandPanel.setAttribute("data-molsysviewer-selection-expander-panel", "true");
        Object.assign(expandPanel.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            paddingTop: "2px",
        });

        const levelRow = document.createElement("div");
        Object.assign(levelRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
            gap: "6px",
        });
        for (const level of ["group", "component", "molecule", "chain", "entity"] as const) {
            const btn = this.makeButton(level, () => this.onAction?.("expand_selection", { level }));
            btn.setAttribute("data-molsysviewer-selection-expand-level", level);
            btn.disabled = this.currentSelection.count_atoms <= 0;
            if (btn.disabled) {
                btn.style.opacity = "0.42";
                btn.style.cursor = "not-allowed";
            }
            levelRow.appendChild(btn);
        }
        expandPanel.appendChild(levelRow);

        const spatialRow = document.createElement("div");
        Object.assign(spatialRow.style, {
            display: "flex",
            gap: "6px",
            alignItems: "center",
        });

        const spatialInput = document.createElement("input");
        spatialInput.type = "number";
        spatialInput.value = this.selectionSpatialDistance;
        spatialInput.setAttribute("data-molsysviewer-selection-spatial-distance", "true");
        Object.assign(spatialInput.style, {
            flex: "0 0 72px",
            minWidth: "0",
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 8px",
            color: "#fff",
            fontSize: "11px",
            outline: "none",
        });
        spatialInput.addEventListener("input", () => {
            this.selectionSpatialDistance = spatialInput.value;
        });

        const spatialBtn = this.makeButton("Within Å", () => {
            const distance = Number.parseFloat(this.selectionSpatialDistance);
            if (!Number.isFinite(distance) || distance <= 0) return;
            this.onAction?.("expand_selection", {
                level: "spatial",
                distance_angstroms: distance,
            });
        });
        spatialBtn.setAttribute("data-molsysviewer-selection-expand-spatial", "true");
        spatialBtn.disabled = this.currentSelection.count_atoms <= 0;
        if (spatialBtn.disabled) {
            spatialBtn.style.opacity = "0.42";
            spatialBtn.style.cursor = "not-allowed";
        }

        spatialRow.appendChild(spatialInput);
        spatialRow.appendChild(spatialBtn);
        expandPanel.appendChild(spatialRow);
        container.appendChild(expandPanel);

        return container;
    }

    private scheduleSelectionQueryPreview(): void {
        if (this.selectionQueryPreviewTimer !== null) {
            clearTimeout(this.selectionQueryPreviewTimer);
            this.selectionQueryPreviewTimer = null;
        }
        this.selectionQueryPreview = null;
        const expression = this.selectionQueryExpression.trim();
        if (!expression) {
            this.renderSelectionSection();
            return;
        }
        const requestId = this.selectionQueryPreviewRequest + 1;
        this.selectionQueryPreviewRequest = requestId;
        this.selectionQueryPreview = { request_id: requestId, status: "pending" };
        this.renderSelectionSection();
        this.selectionQueryPreviewTimer = setTimeout(() => {
            this.selectionQueryPreviewTimer = null;
            this.onAction?.("selection_query_preview_request", {
                request_id: requestId,
                expression,
                syntax: this.selectionQuerySyntax,
            });
        }, 250);
    }

    // ── 2. Regions Section Rendering ─────────────────────────
    private renderRegionsSection(): void {
        this.regionsSection.replaceChildren();
        this.regionsSection.appendChild(this.makeSectionHeader("Create & Global Actions"));
        this.regionsSection.appendChild(this.renderRegionCreateSection());
        this.regionsSection.appendChild(this.makeSectionHeader("Boolean Composition"));
        this.regionsSection.appendChild(this.renderRegionBooleanComposer());
        this.regionsSection.appendChild(this.makeSectionHeader("Regions"));

        const list = document.createElement("div");
        list.setAttribute("data-molsysviewer-region-list", "true");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.regionsSection.appendChild(list);

        if (this.regions.length > 0) {
            const sorted = [...this.regions].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                list.appendChild(this.renderRegionCard(item));
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

    private getRegionQueryComposer(): ManualQueryComposer {
        if (this.regionQueryComposer === null) {
            this.regionQueryComposer = new ManualQueryComposer("region", (details) => {
                this.onAction?.("selection_query_preview_request", details);
            });
        }
        return this.regionQueryComposer;
    }

    private renderRegionCreateSection(): HTMLDivElement {
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-region-create", "true");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
        });

        const originRow = document.createElement("div");
        Object.assign(originRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "6px",
        });
        for (const [origin, label] of [
            ["active", "Active"],
            ["query", "Query"],
            ["split", "Split"],
        ] as const) {
            const button = this.makeButton(label, () => {
                this.regionCreateOrigin = origin;
                this.renderRegionsSection();
            });
            button.setAttribute("data-molsysviewer-region-create-origin", origin);
            if (this.regionCreateOrigin === origin) {
                button.style.borderColor = "rgba(99,102,241,0.7)";
                button.style.background = "rgba(99,102,241,0.18)";
            }
            originRow.appendChild(button);
        }
        container.appendChild(originRow);

        const optionsRow = document.createElement("div");
        Object.assign(optionsRow.style, {
            display: "grid",
            gridTemplateColumns: this.regionCreateOrigin === "split"
                ? "minmax(110px, 1fr)"
                : "minmax(0, 1fr) minmax(110px, 0.7fr)",
            gap: "6px",
        });
        const tagInput = document.createElement("input");
        tagInput.type = "text";
        tagInput.value = this.regionCreateTag;
        tagInput.placeholder = "Name (optional)";
        tagInput.setAttribute("data-molsysviewer-region-create-tag", "true");
        tagInput.addEventListener("input", () => {
            this.regionCreateTag = tagInput.value;
        });
        const representation = this.makeStyledSelect(
            [
                { value: "", label: "Base" },
                "cartoon",
                "backbone",
                "ball-and-stick",
                "line",
                "spacefill",
                "putty",
            ],
            this.regionCreateRepresentation,
            (value) => { this.regionCreateRepresentation = value; },
        );
        representation.setAttribute("data-molsysviewer-region-create-representation", "true");
        if (this.regionCreateOrigin !== "split") {
            optionsRow.appendChild(tagInput);
        }
        optionsRow.appendChild(representation);
        container.appendChild(optionsRow);

        const createWithCollision = (action: string, details: Record<string, unknown>) => {
            const tag = this.regionCreateTag.trim();
            const emit = () => {
                this.onAction?.(action, {
                    ...details,
                    ...(tag ? { tag } : {}),
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            };
            if (tag && this.regions.some(region => region.tag === tag)) {
                this.regionCreateCollision = { action, details, tag };
                this.renderRegionsSection();
                return;
            }
            emit();
        };

        if (this.regionCreateOrigin === "active") {
            const create = this.makeButton("Create from active selection", () => {
                createWithCollision("create_region_from_selection", {});
            });
            create.setAttribute("data-molsysviewer-region-create-active", "true");
            create.disabled = this.currentSelection.count_atoms <= 0;
            if (create.disabled) {
                create.style.opacity = "0.42";
                create.style.cursor = "not-allowed";
                create.title = "Select atoms before creating a region.";
            }
            container.appendChild(create);
        } else if (this.regionCreateOrigin === "query") {
            const composer = this.getRegionQueryComposer();
            container.appendChild(composer.element());
            const create = this.makeButton("Create from query", () => {
                const query = composer.value();
                if (!query.expression || !composer.isVerifiedNonEmpty()) return;
                createWithCollision("create_region_from_query", query);
            });
            create.setAttribute("data-molsysviewer-region-create-query", "true");
            create.disabled = !composer.isVerifiedNonEmpty();
            if (create.disabled) {
                create.style.opacity = "0.42";
                create.style.cursor = "not-allowed";
            }
            container.appendChild(create);
        } else {
            const splitRow = document.createElement("div");
            Object.assign(splitRow.style, {
                display: "flex",
                gap: "6px",
            });
            const level = this.makeStyledSelect(
                ["chain", "molecule", "entity"],
                this.regionSplitLevel,
                (value) => {
                    this.regionSplitLevel = value === "molecule"
                        ? "molecule"
                        : value === "entity" ? "entity" : "chain";
                },
            );
            level.setAttribute("data-molsysviewer-region-split-level", "true");
            const split = this.makeButton("Split", () => {
                this.onAction?.("make_regions_by", {
                    element: this.regionSplitLevel,
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
            });
            split.setAttribute("data-molsysviewer-region-split", "true");
            splitRow.appendChild(level);
            splitRow.appendChild(split);
            container.appendChild(splitRow);
        }

        if (this.regionCreateCollision !== null) {
            const collision = document.createElement("div");
            collision.setAttribute("data-molsysviewer-region-create-collision", this.regionCreateCollision.tag);
            collision.textContent = `"${this.regionCreateCollision.tag}" already exists.`;
            const rename = this.makeButton("Rename", () => {
                this.regionCreateCollision = null;
                this.renderRegionsSection();
            });
            rename.setAttribute("data-molsysviewer-region-collision-rename", "create");
            const overwrite = this.makeButton("Overwrite", () => {
                const pending = this.regionCreateCollision;
                if (pending === null) return;
                this.onAction?.("delete_region", { tag: pending.tag });
                this.onAction?.(pending.action, {
                    ...pending.details,
                    tag: pending.tag,
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            });
            overwrite.setAttribute("data-molsysviewer-region-collision-overwrite", "create");
            const cancel = this.makeButton("Cancel", () => {
                this.regionCreateCollision = null;
                this.renderRegionsSection();
            });
            cancel.setAttribute("data-molsysviewer-region-collision-cancel", "create");
            collision.appendChild(rename);
            collision.appendChild(overwrite);
            collision.appendChild(cancel);
            container.appendChild(collision);
        }

        const globalRow = document.createElement("div");
        Object.assign(globalRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "6px",
            paddingTop: "2px",
        });
        const showAll = this.makeButton("Show all", () => this.onAction?.("show_all_regions"));
        showAll.setAttribute("data-molsysviewer-region-show-all", "true");
        const hideAll = this.makeButton("Hide all", () => this.onAction?.("hide_all_regions"));
        hideAll.setAttribute("data-molsysviewer-region-hide-all", "true");
        globalRow.appendChild(showAll);
        globalRow.appendChild(hideAll);
        container.appendChild(globalRow);
        return container;
    }

    private renderRegionCard(item: RegionSummary): HTMLDivElement {
        const card = document.createElement("div");
        card.setAttribute("data-molsysviewer-region-card", item.tag);
        card.setAttribute("data-molsysviewer-region-hidden", String(item.hidden));
        Object.assign(card.style, {
            display: "flex",
            flexDirection: "column",
            gap: "7px",
            padding: "9px 10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.035)",
            opacity: item.hidden ? "0.58" : "1",
        });

        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const focus = this.makeButton(item.tag, () => this.onFocusRegion(item.tag));
        focus.setAttribute("data-molsysviewer-region-focus", item.tag);
        focus.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
        focus.style.flex = "1 1 auto";
        focus.style.textAlign = "left";
        const hint = document.createElement("span");
        hint.textContent = `${item.atom_count} atoms · ${item.preset ?? item.representation ?? "base"}`;
        Object.assign(hint.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.58)",
        });
        focus.appendChild(hint);
        header.appendChild(focus);

        if ((item.overlap_tags?.length ?? 0) > 0 && !item.hidden) {
            const overlap = this.makeButton("⚠", () => {
                this.regionBooleanA = item.tag;
                this.regionBooleanB = item.overlap_tags![0];
                this.regionBooleanOperation = "difference";
                this.regionComposeCollision = null;
                this.regionBooleanAttention = true;
                this.renderRegionsSection();
                this.regionBooleanComposerElement?.scrollIntoView?.({
                    behavior: "smooth",
                    block: "nearest",
                });
            });
            overlap.setAttribute("data-molsysviewer-region-overlap", item.tag);
            overlap.title = `Overlaps: ${item.overlap_tags!.join(", ")}`;
            overlap.setAttribute("aria-label", overlap.title);
            header.appendChild(overlap);
        }
        const visibility = this.makeButton(item.hidden ? "Show" : "Hide", () =>
            this.onAction?.("toggle_region_visibility", { tag: item.tag })
        );
        visibility.setAttribute("data-molsysviewer-region-visibility", item.tag);
        const remove = this.makeButton("Delete", () =>
            this.onAction?.("delete_region", { tag: item.tag })
        );
        remove.setAttribute("data-molsysviewer-region-delete", item.tag);
        header.appendChild(visibility);
        header.appendChild(remove);
        card.appendChild(header);

        const actions = document.createElement("div");
        actions.setAttribute("data-molsysviewer-region-actions", item.tag);
        Object.assign(actions.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
        });
        const isolate = this.makeButton("Isolate", () =>
            this.onAction?.("show_only_region", { tag: item.tag })
        );
        isolate.setAttribute("data-molsysviewer-region-isolate", item.tag);
        const complement = this.makeButton("Complement", () =>
            this.onAction?.("create_complementary_region", { tag: item.tag })
        );
        complement.setAttribute("data-molsysviewer-region-complement", item.tag);
        const duplicate = this.makeButton("Duplicate", () =>
            this.onAction?.("duplicate_region", { tag: item.tag })
        );
        duplicate.setAttribute("data-molsysviewer-region-duplicate", item.tag);
        const reset = this.makeButton("Reset repr", () =>
            this.onAction?.("reset_region_representation", { tag: item.tag })
        );
        reset.setAttribute("data-molsysviewer-region-reset", item.tag);
        const rename = this.makeButton("Rename", () => {
            this.regionRenameTag = item.tag;
            this.renderRegionsSection();
        });
        rename.setAttribute("data-molsysviewer-region-rename", item.tag);
        const style = this.makeButton("Style", () => {
            this.activeStyleRegionTag = this.activeStyleRegionTag === item.tag ? null : item.tag;
            this.renderRegionsSection();
        });
        style.setAttribute("data-molsysviewer-region-style", item.tag);
        const inspect = this.makeButton("Inspect", () => {
            if (this.regionInspectOpen.has(item.tag)) {
                this.regionInspectOpen.delete(item.tag);
                this.regionDetailsRequests.delete(item.tag);
                this.renderRegionsSection();
                return;
            }
            this.regionInspectOpen.add(item.tag);
            this.requestRegionDetails(item.tag);
            this.renderRegionsSection();
        });
        inspect.setAttribute("data-molsysviewer-region-inspect", item.tag);
        for (const button of [isolate, complement, rename, duplicate, reset, style, inspect]) {
            button.style.fontSize = "10px";
            button.style.padding = "3px 6px";
            actions.appendChild(button);
        }
        card.appendChild(actions);

        if (this.regionRenameTag === item.tag) {
            const form = document.createElement("div");
            form.setAttribute("data-molsysviewer-region-rename-form", item.tag);
            Object.assign(form.style, {
                display: "flex",
                gap: "6px",
            });
            const input = document.createElement("input");
            input.type = "text";
            input.value = item.tag;
            input.setAttribute("data-molsysviewer-region-rename-input", item.tag);
            input.style.flex = "1 1 0";
            const confirmRename = () => {
                const newTag = input.value.trim();
                if (!newTag || newTag === item.tag) {
                    this.regionRenameTag = null;
                    this.renderRegionsSection();
                    return;
                }
                const collision = this.regions.some(region => region.tag === newTag);
                if (collision) {
                    this.regionRenameCollisionTag = newTag;
                    this.renderRegionsSection();
                    return;
                }
                this.onAction?.("rename_region", { tag: item.tag, new_tag: newTag });
                this.regionRenameTag = null;
                this.regionRenameCollisionTag = null;
            };
            input.addEventListener("keydown", (event) => {
                if (event.key !== "Enter") return;
                event.preventDefault();
                confirmRename();
            });
            const submit = this.makeButton("Rename", confirmRename);
            submit.setAttribute("data-molsysviewer-region-rename-confirm", item.tag);
            const cancel = this.makeButton("Cancel", () => {
                this.regionRenameTag = null;
                this.renderRegionsSection();
            });
            form.appendChild(input);
            form.appendChild(submit);
            form.appendChild(cancel);
            card.appendChild(form);

            if (this.regionRenameCollisionTag !== null) {
                const collisionTag = this.regionRenameCollisionTag;
                const collision = document.createElement("div");
                collision.setAttribute("data-molsysviewer-region-rename-collision", collisionTag);
                collision.textContent = `"${collisionTag}" already exists.`;
                const chooseRename = this.makeButton("Rename", () => {
                    this.regionRenameCollisionTag = null;
                    this.renderRegionsSection();
                });
                chooseRename.setAttribute("data-molsysviewer-region-collision-rename", "rename");
                const overwrite = this.makeButton("Overwrite", () => {
                    this.onAction?.("delete_region", { tag: collisionTag });
                    this.onAction?.("rename_region", { tag: item.tag, new_tag: collisionTag });
                    this.regionRenameTag = null;
                    this.regionRenameCollisionTag = null;
                });
                overwrite.setAttribute("data-molsysviewer-region-collision-overwrite", "rename");
                const cancelCollision = this.makeButton("Cancel", () => {
                    this.regionRenameTag = null;
                    this.regionRenameCollisionTag = null;
                    this.renderRegionsSection();
                });
                cancelCollision.setAttribute("data-molsysviewer-region-collision-cancel", "rename");
                collision.appendChild(chooseRename);
                collision.appendChild(overwrite);
                collision.appendChild(cancelCollision);
                card.appendChild(collision);
            }
        }

        if (this.activeStyleRegionTag === item.tag) {
            card.appendChild(this.renderStyleComposer(item));
        }
        if (this.regionInspectOpen.has(item.tag)) {
            card.appendChild(this.renderRegionInspect(item.tag));
        }
        return card;
    }

    private renderRegionBooleanComposer(): HTMLDivElement {
        const container = document.createElement("div");
        this.regionBooleanComposerElement = container;
        container.setAttribute("data-molsysviewer-region-boolean-composer", "true");
        container.setAttribute(
            "data-molsysviewer-region-boolean-attention",
            String(this.regionBooleanAttention),
        );
        container.setAttribute("data-molsysviewer-region-boolean-current-a", this.regionBooleanA);
        container.setAttribute("data-molsysviewer-region-boolean-current-b", this.regionBooleanB);
        container.setAttribute(
            "data-molsysviewer-region-boolean-current-operation",
            this.regionBooleanOperation,
        );
        Object.assign(container.style, {
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) minmax(120px, 0.8fr) minmax(0, 1fr)",
            gap: "6px",
            padding: "10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
        });
        const tags = this.regions.map(item => item.tag);
        const left = this.makeStyledSelect(tags, this.regionBooleanA, value => {
            this.regionBooleanA = value;
            if (this.regionBooleanB === value) {
                this.regionBooleanB = tags.find(tag => tag !== value) ?? "";
                this.renderRegionsSection();
            }
        });
        left.setAttribute("data-molsysviewer-region-boolean-a", "true");
        const operation = this.makeStyledSelect(
            [
                { value: "union", label: "Union (A ∪ B)" },
                { value: "intersection", label: "Intersection (A ∩ B)" },
                { value: "difference", label: "Difference (A − B)" },
            ],
            this.regionBooleanOperation,
            value => {
                this.regionBooleanOperation = value === "intersection"
                    ? "intersection"
                    : value === "difference" ? "difference" : "union";
            },
        );
        operation.setAttribute("data-molsysviewer-region-boolean-operation", "true");
        const right = this.makeStyledSelect(tags, this.regionBooleanB, value => {
            this.regionBooleanB = value;
        });
        right.setAttribute("data-molsysviewer-region-boolean-b", "true");
        container.appendChild(left);
        container.appendChild(operation);
        container.appendChild(right);

        const output = document.createElement("input");
        output.type = "text";
        output.placeholder = "Output name (optional)";
        output.value = this.regionBooleanOutput;
        output.setAttribute("data-molsysviewer-region-boolean-output", "true");
        output.addEventListener("input", () => {
            this.regionBooleanOutput = output.value;
        });
        const create = this.makeButton("Create", () => {
            if (!this.regionBooleanA || !this.regionBooleanB || this.regionBooleanA === this.regionBooleanB) {
                return;
            }
            const tag = this.regionBooleanOutput.trim();
            const details = {
                tag_a: this.regionBooleanA,
                tag_b: this.regionBooleanB,
                op: this.regionBooleanOperation,
                ...(tag ? { new_tag: tag } : {}),
            };
            if (tag && tags.includes(tag)) {
                this.regionComposeCollision = { tag, details };
                this.renderRegionsSection();
                return;
            }
            this.onAction?.("compose_regions", details);
            this.regionBooleanOutput = "";
        });
        create.disabled = tags.length < 2 || !this.regionBooleanA || !this.regionBooleanB;
        create.setAttribute("data-molsysviewer-region-boolean-create", "true");
        container.appendChild(output);
        container.appendChild(create);

        if (this.regionComposeCollision !== null) {
            const collision = document.createElement("div");
            collision.setAttribute(
                "data-molsysviewer-region-boolean-collision",
                this.regionComposeCollision.tag,
            );
            collision.textContent = `"${this.regionComposeCollision.tag}" already exists.`;
            const rename = this.makeButton("Rename", () => {
                this.regionComposeCollision = null;
                this.renderRegionsSection();
            });
            const overwrite = this.makeButton("Overwrite", () => {
                const pending = this.regionComposeCollision;
                if (pending === null) return;
                this.onAction?.("compose_regions", {
                    ...pending.details,
                    overwrite: true,
                });
                this.regionBooleanOutput = "";
                this.regionComposeCollision = null;
            });
            overwrite.setAttribute("data-molsysviewer-region-boolean-overwrite", "true");
            const cancel = this.makeButton("Cancel", () => {
                this.regionComposeCollision = null;
                this.renderRegionsSection();
            });
            collision.appendChild(rename);
            collision.appendChild(overwrite);
            collision.appendChild(cancel);
            container.appendChild(collision);
        }
        return container;
    }

    private requestRegionDetails(tag: string): void {
        this.regionDetails.delete(tag);
        const requestId = this.nextRegionDetailsRequest++;
        this.regionDetailsRequests.set(tag, requestId);
        this.onAction?.("get_region_details", {
            tag,
            request_id: requestId,
        });
    }

    private renderRegionInspect(tag: string): HTMLDivElement {
        const panel = document.createElement("div");
        panel.setAttribute("data-molsysviewer-region-inspect-panel", tag);
        const details = this.regionDetails.get(tag);
        if (!details) {
            panel.textContent = "Loading...";
            return panel;
        }
        const center = details.center_nm.map(value => Number(value).toFixed(3)).join(", ");
        panel.setAttribute("data-molsysviewer-region-inspect-frame", String(details.structure_index));
        for (const [key, value] of [
            ["atoms", String(details.atom_count)],
            ["groups", String(details.group_count)],
            ["chains", String(details.chain_count)],
            ["frame", String(details.structure_index)],
        ]) {
            const metric = document.createElement("div");
            metric.setAttribute("data-molsysviewer-region-inspect-metric", key);
            metric.textContent = `${key}: ${value}`;
            panel.appendChild(metric);
        }
        const centerRow = document.createElement("div");
        centerRow.setAttribute("data-molsysviewer-region-inspect-center", "true");
        centerRow.textContent = `center [nm]: ${center}`;
        panel.appendChild(centerRow);
        const refresh = this.makeButton("Refresh", () => {
            this.requestRegionDetails(tag);
            this.renderRegionsSection();
        });
        refresh.setAttribute("data-molsysviewer-region-inspect-refresh", tag);
        refresh.title = "Refresh details for the current trajectory frame.";
        panel.appendChild(refresh);
        return panel;
    }

    // ── 3. Overlays Section Rendering ────────────────────────
    private renderWholeSection(): void {
        this.wholeSection.replaceChildren();
        this.wholeSection.appendChild(this.makeSectionHeader("Whole Structure"));

        const card = this.makeSettingsCard("Feature Roadmap");
        
        const desc = document.createElement("div");
        Object.assign(desc.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.5",
            marginBottom: "8px",
        });
        desc.textContent = "This subpanel will house visual configuration controls for the baseline molecular structure (view.whole). Planned features include:";
        card.appendChild(desc);

        const list = document.createElement("ul");
        Object.assign(list.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.6",
            paddingLeft: "16px",
            margin: "0",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const items = [
            "Presets & Representation Styles: Choose from 12 styles (cartoon, ribbon, spacefill, licorice, ball & stick, etc.)",
            "Structure Opacity: Fine-tune baseline alpha transparency across the global scene",
            "Render Quality: Adjust geometric details for high-performance viewing or production exports",
            "Base Coloring: Select standard or custom uniform color palettes for the whole system"
        ];

        for (const itemText of items) {
            const li = document.createElement("li");
            li.textContent = itemText;
            list.appendChild(li);
        }

        card.appendChild(list);
        this.wholeSection.appendChild(card);
    }

    private renderMeasuresSection(): void {
        this.measuresSection.replaceChildren();
        this.measuresSection.appendChild(this.makeSectionHeader("Measurements (Distances)"));

        const measurementsList = document.createElement("div");
        Object.assign(measurementsList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.measuresSection.appendChild(measurementsList);

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

    private renderAnnotationsSection(): void {
        this.annotationsSection.replaceChildren();
        this.annotationsSection.appendChild(this.makeSectionHeader("Annotations (Labels)"));

        const annotationsList = document.createElement("div");
        Object.assign(annotationsList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.annotationsSection.appendChild(annotationsList);

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
    }

    private renderShapesSection(): void {
        this.shapesSection.replaceChildren();
        this.shapesSection.appendChild(this.makeSectionHeader("3D Shapes"));

        const shapesList = document.createElement("div");
        Object.assign(shapesList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.shapesSection.appendChild(shapesList);

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
    }

    private renderLayersSection(): void {
        this.layersSection.replaceChildren();
        this.layersSection.appendChild(this.makeSectionHeader("Logical Layers"));

        const card = this.makeSettingsCard("Feature Roadmap");

        const desc = document.createElement("div");
        Object.assign(desc.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.5",
            marginBottom: "8px",
        });
        desc.textContent = "This subpanel will act as a logical group tag organizer (view.layers). Planned features include:";
        card.appendChild(desc);

        const list = document.createElement("ul");
        Object.assign(list.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.6",
            paddingLeft: "16px",
            margin: "0",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const items = [
            "Group Tag Registry: View and list all active grouping tags across layers",
            "Bulk Actions: Toggle visibility or delete whole categories of annotations/measures in one click",
            "Layer Assignments: Map structural representations and custom shapes to target layers dynamically"
        ];

        for (const itemText of items) {
            const li = document.createElement("li");
            li.textContent = itemText;
            list.appendChild(li);
        }

        card.appendChild(list);
        this.layersSection.appendChild(card);
    }

    private renderStyleComposer(item: RegionSummary): HTMLDivElement {
        const tag = item.tag;
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-region-style-composer", tag);
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

        const makeControlRow = (label: string, control: HTMLElement): HTMLDivElement => {
            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "8px",
                width: "100%",
            });
            const text = document.createElement("span");
            text.textContent = label;
            Object.assign(text.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.7)",
            });
            row.appendChild(text);
            row.appendChild(control);
            return row;
        };

        const fallbackRepresentations = [
            "backbone",
            "ball-and-stick",
            "carbohydrate",
            "cartoon",
            "ellipsoid",
            "gaussian-surface",
            "gaussian-volume",
            "line",
            "molecular-surface",
            "point",
            "putty",
            "spacefill",
        ];
        const fallbackPresets = [
            "atomic-detail",
            "auto",
            "coarse-surface",
            "empty",
            "polymer-and-ligand",
            "polymer-cartoon",
        ];
        const representations = this.regionStyleRepresentations.length > 0
            ? this.regionStyleRepresentations
            : fallbackRepresentations;
        const presets = this.regionStylePresets.length > 0
            ? this.regionStylePresets
            : fallbackPresets;
        const params = item.representation_params ?? {};
        const draftHeading = document.createElement("div");
        draftHeading.textContent = "Style draft";
        draftHeading.setAttribute("data-molsysviewer-region-style-draft-heading", tag);
        Object.assign(draftHeading.style, {
            fontSize: "10px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.55)",
        });
        container.appendChild(draftHeading);

        let representationSelect: HTMLSelectElement;
        let presetSelect: HTMLSelectElement;
        representationSelect = this.makeStyledSelect(
            [{ value: "", label: "Base" }, ...representations],
            item.preset ? "" : (item.representation ?? ""),
            (value) => {
                if (value) presetSelect.value = "";
            },
        );
        representationSelect.setAttribute("data-molsysviewer-region-style-representation", tag);
        presetSelect = this.makeStyledSelect(
            [{ value: "", label: "No preset" }, ...presets],
            item.preset ?? "",
            (value) => {
                if (value) representationSelect.value = "";
            },
        );
        presetSelect.setAttribute("data-molsysviewer-region-style-preset", tag);
        container.appendChild(makeControlRow("Representation", representationSelect));
        container.appendChild(makeControlRow("Preset", presetSelect));

        const immediateHeading = document.createElement("div");
        immediateHeading.textContent = "Immediate adjustments";
        immediateHeading.setAttribute("data-molsysviewer-region-style-immediate-heading", tag);
        Object.assign(immediateHeading.style, {
            fontSize: "10px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.55)",
            paddingTop: "2px",
        });
        const opacityWrap = document.createElement("div");
        Object.assign(opacityWrap.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const opacity = document.createElement("input");
        opacity.type = "range";
        opacity.min = "0";
        opacity.max = "1";
        opacity.step = "0.05";
        opacity.value = String(typeof params.alpha === "number" ? params.alpha : 1);
        opacity.setAttribute("data-molsysviewer-region-style-opacity", tag);
        const opacityValue = document.createElement("span");
        opacityValue.textContent = Number(opacity.value).toFixed(2);
        opacityValue.setAttribute("data-molsysviewer-region-style-opacity-value", tag);
        opacity.addEventListener("input", () => {
            opacityValue.textContent = Number(opacity.value).toFixed(2);
        });
        opacityWrap.appendChild(opacity);
        opacityWrap.appendChild(opacityValue);
        const opacityRow = makeControlRow("Opacity", opacityWrap);

        const qualityValues = ["auto", "lowest", "lower", "low", "medium", "high", "higher", "highest", "custom"];
        const quality = this.makeStyledSelect(
            qualityValues,
            typeof params.quality === "string" ? params.quality : "auto",
            () => {},
        );
        quality.setAttribute("data-molsysviewer-region-style-quality", tag);
        container.appendChild(makeControlRow("Quality", quality));

        const customColorInput = document.createElement("input");
        customColorInput.type = "color";
        customColorInput.value = "#3b82f6";
        customColorInput.setAttribute("data-molsysviewer-region-style-uniform-color", tag);
        Object.assign(customColorInput.style, {
            width: "24px",
            height: "24px",
            border: "1px solid rgba(255,255,255,0.25)",
            borderRadius: "4px",
            padding: "0",
            background: "transparent",
            cursor: "pointer",
            boxSizing: "border-box",
            overflow: "hidden",
            outline: "none",
        });

        const colorScheme = this.makeStyledSelect(
            [
                { value: "", label: "Keep current" },
                { value: "element_cpk", label: "Element (CPK)" },
                { value: "chain_default", label: "Chain" },
                { value: "secondary_structure_default", label: "Secondary structure" },
                { value: "physicochemical", label: "Physicochemical" },
                { value: "residue_name", label: "Residue name" },
                { value: "molecule_type", label: "Molecule type" },
                { value: "entity_default", label: "Entity" },
                { value: "illustrative_default", label: "Illustrative" },
                { value: "uniform", label: "Uniform color" },
            ],
            typeof params.color_scheme === "string" ? params.color_scheme : "",
            (val) => {
                customColorInput.style.display = val === "uniform" ? "inline-block" : "none";
            },
        );
        colorScheme.setAttribute("data-molsysviewer-region-style-color-scheme", tag);
        customColorInput.style.display = colorScheme.value === "uniform" ? "inline-block" : "none";

        const colorRight = document.createElement("div");
        Object.assign(colorRight.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        colorRight.appendChild(customColorInput);
        colorRight.appendChild(colorScheme);
        container.appendChild(makeControlRow("Color", colorRight));
        container.appendChild(immediateHeading);
        container.appendChild(opacityRow);

        const attributeRow = document.createElement("div");
        Object.assign(attributeRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const attribute = this.makeStyledSelect(
            [
                { value: "", label: "None" },
                ...(item.available_attributes ?? []),
            ],
            "",
            (value) => {
                if (!value) return;
                this.onAction?.("color_region_by_attribute", {
                    tag,
                    attribute: value,
                });
            },
        );
        attribute.setAttribute("data-molsysviewer-region-style-color-attribute", tag);
        const resetColors = this.makeButton("Reset colors", () =>
            this.onAction?.("reset_region_colors", { tag })
        );
        resetColors.setAttribute("data-molsysviewer-region-style-reset-colors", tag);
        attributeRow.appendChild(attribute);
        attributeRow.appendChild(resetColors);
        container.appendChild(makeControlRow("Color by", attributeRow));

        const buildStyleAction = () => {
            const selectedPreset = presetSelect.value;
            const selectedRepresentation = representationSelect.value;
            if (!selectedPreset && !selectedRepresentation) {
                return { action: "reset_region_representation", details: { tag } };
            }
            const nextParams: Record<string, unknown> = {
                ...params,
                alpha: Number(opacity.value),
                quality: quality.value,
            };
            if (colorScheme.value === "uniform") {
                delete nextParams.color_scheme;
                delete nextParams.molstar_color_theme;
                nextParams.color = customColorInput.value;
            } else if (colorScheme.value) {
                delete nextParams.color;
                delete nextParams.molstar_color_theme;
                nextParams.color_scheme = colorScheme.value;
            }
            return {
                action: "set_region_representation",
                details: {
                    tag,
                    ...(selectedPreset
                        ? { preset: selectedPreset }
                        : { representation: selectedRepresentation }),
                    params: nextParams,
                },
            };
        };
        opacity.addEventListener("change", () => {
            if (!item.representation && !item.preset) return;
            this.onAction?.("set_region_representation", {
                tag,
                ...(item.preset
                    ? { preset: item.preset }
                    : { representation: item.representation }),
                params: {
                    ...params,
                    alpha: Number(opacity.value),
                },
            });
        });

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
        cancelBtn.setAttribute("data-molsysviewer-region-style-cancel", tag);
        Object.assign(cancelBtn.style, {
            flex: "0 0 auto",
            fontSize: "10px",
            padding: "3px 8px",
        });

        const applyBtn = this.makeButton("Apply Style", () => {
            const next = buildStyleAction();
            this.onAction?.(next.action, next.details);
            this.activeStyleRegionTag = null;
            this.renderRegionsSection();
        });
        applyBtn.setAttribute("data-molsysviewer-region-style-apply", tag);
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
        this.viewportSection.appendChild(this.makeSectionHeader("Viewport Settings"));

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
    }

    private renderExportSection(): void {
        this.exportSection.replaceChildren();
        this.exportSection.appendChild(this.makeSectionHeader("Export Settings"));

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            paddingBottom: "10px",
        });
        this.exportSection.appendChild(grid);

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

    private makeStyledSelect(
        options: Array<string | { value: string; label: string }>,
        selectedValue: string,
        onChange: (value: string) => void,
    ): HTMLSelectElement {
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
            const value = typeof opt === "string" ? opt : opt.value;
            const label = typeof opt === "string" ? opt : opt.label;
            const el = document.createElement("option");
            el.value = value;
            el.textContent = label;
            el.selected = value === selectedValue;
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
