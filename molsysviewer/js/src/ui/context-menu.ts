import type { ActiveSelectionPayload } from "../managers/active-selection";
import { MenuNavigation } from "./menu-navigation";

type BaseTarget =
    | { event: "interaction_context_menu"; kind: "empty" }
    | {
        event: "interaction_context_menu";
        kind: "structure";
        atom_indices: number[];
        group_name?: string;
        chain_name?: string;
        atom_index?: number;
        metadata?: { group_id?: string; group_name?: string; chain_id?: string; atom_name?: string };
        source_label?: string;
    }
    | { event: "interaction_context_menu"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string }
    | { event: "interaction_context_menu"; kind: "interaction"; atom_indices: number[]; tag?: string; shape_name?: string; entity_ref?: unknown }
    | { event: "interaction_context_menu"; kind: "measurement"; atom_indices: number[]; tag?: string; measurement_name?: string }
    | { event: "interaction_context_menu"; kind: "annotation"; atom_indices: number[]; tag?: string; text?: string };

export type ContextMenuTarget = BaseTarget & { focusable?: boolean };

export type ContextMenuAction =
    | "distance"
    | "angle"
    | "dihedral"
    | "focus_target"
    | "focus_all"
    | "show_help"
    | "edit_object_in_studio"
    | "edit_annotation_text"
    | "toggle_annotation_visibility"
    | "toggle_shape_visibility"
    | "inspect_target"
    | "select_context_target"
    | "create_region_from_target"
    | "create_annotation_from_target"
    | "open_shapes_for_target"
    | "open_interactions_for_target"
    | "focus_region"
    | "open_region_in_studio"
    | "toggle_region_visibility"
    | "toggle_region_enabled"
    | "delete_region"
    | "rename_region"
    | "hide_measurement"
    | "delete_annotation"
    | "delete_shape"
    | "delete_interaction"
    | "focus_interaction"
    | "inspect_picked_interaction"
    | "select_picked_interaction"
    | "focus_picked_interaction"
    | "toggle_interaction_visibility"
    | "edit_interaction_in_studio"
    | "delete_measurement"
    | "focus_selection"
    | "activate_selection"
    | "save_selection"
    | "remove_selection"
    | "clear_selection"
    | "expand_selection"
    | "create_region_from_selection"
    | "create_section_from_selection"
    | "add_label_from_selection"
    | "addon_context_action"
    | "reset_view"
    | "toggle_background"
    | "toggle_spin"
    | "toggle_swing"
    | "undo_scene"
    | "redo_scene"
    | "open_navigate"
    | "open_workbench"
    | "set_viewer_mode"
    | "toggle_canvas_visibility";

export type ContextActionDetails = {
    endpoint_policy?: "atom" | "centroid" | "representative_atom";
    text?: string;
    tag?: string;
    new_tag?: string;
    level?: "group" | "component" | "molecule" | "chain" | "entity" | "spatial";
    distance_angstroms?: number;
    camera_forward?: [number, number, number];
    label_style?: { color?: string; size_em?: number };
    studio_section?: "system" | "selection" | "regions" | "measures" | "interactions" | "annotations" | "shapes";
    enabled?: boolean;
    hidden?: boolean;
    mode?: "light" | "dark";
    scope?: "target" | "atom" | "group" | "chain";
    op?: "replace" | "add" | "subtract";
    workflow?: "inspect" | "calculate";
    structure_index?: number;
};

export type ContextMenuSceneState = {
    isSpinActive?: boolean;
    isSwingActive?: boolean;
    isDarkMode?: boolean;
    isNavigateExpanded?: boolean;
    isAddonsExpanded?: boolean;
    isCanvasVisible?: boolean;
    currentViewerMode?: string;
    canUndo?: boolean;
    canRedo?: boolean;
    canMeasure?: boolean;
    canFocusAll?: boolean;
    canHelp?: boolean;
};

export type LastMeasurementSummary = {
    action: "distance" | "angle" | "dihedral";
    picked_count: number;
};

export type SavedSelectionSummary = {
    tag: string;
    atom_count: number;
    element_level?: string;
};


export type RegionSummary = {
    tag: string;
    atom_indices: number[];
    atom_count: number;
    selection?: string;
    hidden: boolean;
    enabled?: boolean;
    representation?: string;
    preset?: string;
    overlap_tags?: string[];
    available_attributes?: string[];
};

export type AddonContextActionSummary = {
    addon: string;
    id: string;
    title: string;
    target_kinds: string[];
    group?: string;
};

export type AddonContextItemSummary = {
    addon: string;
    id: string;
    title: string;
    group?: string;
    order?: number;
    enabled?: boolean;
    target_kinds?: string[];
    payload?: any;
};

export type ContextMenuOptions = {
    /** Hide actions that the hosting surface cannot execute truthfully. */
    allowedActions?: ReadonlySet<ContextMenuAction>;
};

function targetTitle(target: ContextMenuTarget): string {
    if (target.kind === "empty") return "Canvas";
    if (target.kind === "shape") return target.shape_name?.trim() || target.tag?.trim() || "Shape";
    if (target.kind === "interaction") {
        const identity = target.entity_ref as { interaction_type?: string; frame?: number } | undefined;
        return [identity?.interaction_type || "Interaction", target.tag?.trim(),
            Number.isInteger(identity?.frame) ? `structure ${identity!.frame}` : ""].filter(Boolean).join(" · ");
    }
    if (target.kind === "measurement") return target.measurement_name?.trim() || target.tag?.trim() || "Measurement";
    if (target.kind === "annotation") return target.text?.trim() || target.tag?.trim() || "Annotation";
    if (target.group_name?.trim() || target.metadata?.group_name?.trim()) {
        let group = target.group_name?.trim() || target.metadata!.group_name!.trim();
        const id = target.metadata?.group_id;
        if (id && !group.endsWith(` ${id}`)) group += ` ${id}`;
        const chain = target.chain_name?.trim() || target.metadata?.chain_id?.trim();
        return [group, chain ? `chain ${chain}` : "", target.source_label?.trim()].filter(Boolean).join(" · ");
    }
    const count = target.atom_indices.length;
    return count === 1 ? "Element (1 atom)" : `Element (${count} atoms)`;
}

function selectionTitle(selection: ActiveSelectionPayload): string {
    const parts = [`${selection.count_atoms} atom${selection.count_atoms === 1 ? "" : "s"}`];
    if (selection.count_shapes) parts.push(`${selection.count_shapes} shape${selection.count_shapes === 1 ? "" : "s"}`);
    if (selection.count_annotations) parts.push(`${selection.count_annotations} annotation${selection.count_annotations === 1 ? "" : "s"}`);
    return `Active selection · ${parts.join(" · ")}`;
}

function selectionSummary(selection: ActiveSelectionPayload | null): string {
    if (!selection || selection.source_kind === "empty") return "Current selection";
    return `Stored as ${selection.count_atoms} atom${selection.count_atoms === 1 ? "" : "s"}`;
}

export class ViewerContextMenu {
    private readonly root: HTMLDivElement;
    private readonly navigation: MenuNavigation;
    private returnFocus?: HTMLElement;
    private outsidePointerHandler?: (event: PointerEvent) => void;
    private scrollEl!: HTMLDivElement;
    private currentTarget: ContextMenuTarget | null = null;
    private currentSelection: ActiveSelectionPayload | null = null;
    private currentLastMeasurement: LastMeasurementSummary | null = null;
    private currentSavedSelections: SavedSelectionSummary[] = [];
    private currentRegions: RegionSummary[] = [];
    private currentAddonActions: AddonContextActionSummary[] = [];
    private currentAddonItems: AddonContextItemSummary[] = [];
    private currentPageX = 0;
    private currentPageY = 0;
    private currentSceneState: ContextMenuSceneState | null = null;

    constructor(
        private readonly host: HTMLElement,
        private readonly notify?: (msg: any) => void,
        /** Return true for browser-owned actions that must not be dispatched again. */
        private readonly onAction?: (action: ContextMenuAction, target: ContextMenuTarget, details?: ContextActionDetails) => boolean | void,
        private readonly onClose?: () => void,
        private readonly getCameraDirection?: () => [number, number, number],
        private readonly options: ContextMenuOptions = {},
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-context-menu", "true");
        this.root.setAttribute("aria-hidden", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            display: "none",
            minWidth: "180px",
            maxWidth: "240px",
            borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(26, 26, 30, 0.96)",
            color: "#f4f4f5",
            boxShadow: "0 16px 40px rgba(0,0,0,0.35)",
            zIndex: "20",
            overflow: "hidden",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "13px",
        });
        this.root.addEventListener("pointerdown", (event) => {
            event.stopPropagation();
        });
        this.scrollEl = document.createElement("div");
        this.scrollEl.setAttribute("data-molsysviewer-context-scroll", "true");
        Object.assign(this.scrollEl.style, {
            overflowY: "auto",
            padding: "6px",
            boxSizing: "border-box",
            // Firefox scrollbar styling
            scrollbarWidth: "thin" as any,
            scrollbarColor: "rgba(255,255,255,0.25) transparent" as any,
        });
        this.root.appendChild(this.scrollEl);
        this.navigation = new MenuNavigation(this.scrollEl, () => this.close(), () => this.positionMenu());
        this.host.appendChild(this.root);

        // Inject webkit scrollbar styles once per document
        if (!document.getElementById("msv-context-menu-scrollbar-style")) {
            const style = document.createElement("style");
            style.id = "msv-context-menu-scrollbar-style";
            style.textContent = [
                "[data-molsysviewer-context-scroll]::-webkit-scrollbar { width: 5px; }",
                "[data-molsysviewer-context-scroll]::-webkit-scrollbar-track { background: transparent; }",
                "[data-molsysviewer-context-scroll]::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.25); border-radius: 3px; }",
                "[data-molsysviewer-context-scroll]::-webkit-scrollbar-corner { background: transparent; }",
                "[data-molsysviewer-context-menu] button:hover, [data-molsysviewer-context-menu] button:focus-visible { background: rgba(255,255,255,0.10) !important; outline: 2px solid #a5b4fc; outline-offset: -2px; }",
            ].join("\n");
            document.head.appendChild(style);
        }
    }

    open(
        target: ContextMenuTarget,
        pageX: number,
        pageY: number,
        activeSelection?: ActiveSelectionPayload | null,
        lastMeasurement?: LastMeasurementSummary | null,
        savedSelections?: SavedSelectionSummary[] | null,
        regions?: RegionSummary[] | null,
        addonActions?: AddonContextActionSummary[] | null,
        addonItems?: AddonContextItemSummary[] | null,
        sceneState?: ContextMenuSceneState | null,
    ): void {
        if (!this.isOpen()) {
            const active = document.activeElement as HTMLElement | null;
            this.returnFocus = active && this.host.contains(active)
                ? active : (this.host.querySelector?.("canvas") as HTMLElement | null) ?? this.host;
            if (this.returnFocus.tagName === "CANVAS" && this.returnFocus.tabIndex < 0) this.returnFocus.tabIndex = 0;
        }
        this.currentTarget = target;
        this.currentSelection = activeSelection ?? null;
        this.currentLastMeasurement = lastMeasurement ?? null;
        this.currentSavedSelections = Array.isArray(savedSelections) ? [...savedSelections] : [];
        this.currentRegions = Array.isArray(regions) ? [...regions] : [];
        this.currentAddonActions = Array.isArray(addonActions) ? [...addonActions] : [];
        this.currentAddonItems = Array.isArray(addonItems) ? [...addonItems] : [];
        this.currentPageX = pageX;
        this.currentPageY = pageY;
        this.currentSceneState = sceneState ?? null;
        this.renderMenu();
        this.root.style.display = "block";
        this.root.setAttribute("aria-hidden", "false");
        this.positionMenu();
        this.navigation.focusFirst();

        this.detachOutsidePointerHandler();
        this.outsidePointerHandler = (event: PointerEvent) => {
            const targetNode = event.target as Node | null;
            if (targetNode && this.root.contains(targetNode)) return;
            this.close();
        };
        window.addEventListener("pointerdown", this.outsidePointerHandler, true);
    }

    isOpen(): boolean { return this.root.style.display !== "none"; }

    updateHistoryState(state: { canUndo: boolean; canRedo: boolean }): void {
        this.currentSceneState = { ...this.currentSceneState, ...state };
        if (!this.isOpen()) return;
        for (const [action, enabled] of [["undo_scene", state.canUndo], ["redo_scene", state.canRedo]] as const) {
            const button = this.root.querySelector<HTMLButtonElement>(`[data-molsysviewer-context-action="${action}"]`);
            if (button) {
                button.disabled = !enabled;
                button.setAttribute("aria-disabled", enabled ? "false" : "true");
                button.style.opacity = enabled ? "1" : "0.45";
                button.title = enabled ? "" : "No scene history operation is available";
            }
        }
    }

    /** Dismiss one menu level before global Escape affects selection or Studio. */
    handleEscape(event: KeyboardEvent): boolean {
        if (!this.isOpen() || event.key !== "Escape") return false;
        if ((event.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return false;
        if (!this.navigation.containsCurrentPage()) this.reopen();
        else if (!this.navigation.back()) this.close();
        event.preventDefault();
        event.stopImmediatePropagation();
        return true;
    }

    private reopen(): void {
        if (!this.currentTarget) return;
        this.open(this.currentTarget, this.currentPageX, this.currentPageY,
            this.currentSelection, this.currentLastMeasurement, this.currentSavedSelections,
            this.currentRegions, this.currentAddonActions, this.currentAddonItems, this.currentSceneState);
    }

    private positionMenu(): void {
        if (!this.isOpen()) return;
        const rect = this.host.getBoundingClientRect();
        this.scrollEl.style.maxHeight = `${Math.max(0, rect.height - 12)}px`;
        this.root.style.minWidth = `${Math.min(180, Math.max(0, rect.width - 8))}px`;
        this.root.style.maxWidth = `${Math.min(280, Math.max(0, rect.width - 8))}px`;
        this.root.style.display = "block";
        const menuWidth = this.root.offsetWidth || 180;
        const menuHeight = this.root.offsetHeight || 120;
        const left = Math.min(Math.max(0, this.currentPageX - rect.left), Math.max(0, rect.width - menuWidth));
        const rawTop = this.currentPageY - rect.top;
        const top = Math.min(Math.max(0, rawTop), Math.max(0, rect.height - menuHeight));
        const availableBelow = rect.height - top - 12;
        if (menuHeight > availableBelow) {
            this.scrollEl.style.maxHeight = `${Math.max(0, availableBelow)}px`;
            this.scrollEl.style.borderBottomLeftRadius = "9px";
            this.scrollEl.style.borderBottomRightRadius = "9px";
        } else {
            this.scrollEl.style.borderBottomLeftRadius = "";
            this.scrollEl.style.borderBottomRightRadius = "";
        }
        this.root.style.left = `${left}px`;
        this.root.style.top = `${top}px`;

    }

    private renderMenu(): void {
        const target = this.currentTarget!;
        const main = this.navigation.reset(targetTitle(target));
        const header = document.createElement("div");
        header.setAttribute("data-molsysviewer-context-menu-title", "true");
        header.setAttribute("role", "presentation");
        header.textContent = targetTitle(target);
        Object.assign(header.style, { padding: "6px 8px 8px", fontWeight: "600", borderBottom: "1px solid rgba(255,255,255,0.10)", marginBottom: "6px" });
        main.appendChild(header);
        if (target.kind === "structure" && target.atom_index !== undefined && target.metadata?.atom_name) {
            const atom = document.createElement("div");
            atom.textContent = `Pointed atom: ${target.metadata.atom_name}`;
            Object.assign(atom.style, { padding: "0 8px 6px", opacity: "0.75", fontSize: "12px" });
            main.appendChild(atom);
        }

        if (target.kind === "structure") {
            main.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            main.appendChild(this.makeActionButton("Inspect Target…", "inspect_target"));
            this.navigation.addSubmenu(main, "Select", view => {
                for (const [scope, label] of [["atom", "Pointed atom"], ["group", "Residue"], ["chain", "Chain"]] as const) {
                    const heading = document.createElement("div");
                    heading.textContent = label;
                    Object.assign(heading.style, { padding: "6px 10px", fontWeight: "600" });
                    view.appendChild(heading);
                    for (const [op, name] of [["replace", "Replace selection"], ["add", "Add to selection"], ["subtract", "Remove from selection"]] as const) {
                        const button = this.makeActionButton(`${name} · ${label.toLowerCase()}`, "select_context_target", { scope, op });
                        if (scope === "atom" && target.atom_index === undefined) {
                            button.disabled = true;
                            button.setAttribute("aria-disabled", "true");
                            button.title = "This target does not identify one pointed atom";
                            button.style.opacity = "0.45";
                        }
                        view.appendChild(button);
                    }
                }
            });
            this.navigation.addSubmenu(main, "Create", view => {
                view.appendChild(this.makeActionButton("Region from Target…", "create_region_from_target"));
                view.appendChild(this.makeActionButton("Annotation from Target…", "create_annotation_from_target"));
                view.appendChild(this.makeActionButton("Shape from Target in Studio…", "open_shapes_for_target"));
            });
            this.navigation.addSubmenu(main, "Measure", view => {
                const policyLabel = document.createElement("label");
                policyLabel.textContent = "Endpoints";
                const policy = document.createElement("select");
                policy.setAttribute("data-molsysviewer-measure-endpoint-policy", "true");
                policy.setAttribute("aria-label", "Measurement endpoint policy");
                for (const [value, label] of [["centroid", "Centers of picked atom sets"], ["atom", "Individual atoms"], ["representative_atom", "Representative atoms (explicit)"]] as const) {
                    const option = document.createElement("option"); option.value = value; option.textContent = label;
                    option.disabled = value === "atom" && target.atom_index === undefined;
                    policy.appendChild(option);
                }
                policy.value = "centroid";
                Object.assign(policy.style, { display: "block", width: "100%", margin: "6px 0", color: "inherit", background: "#27272a" });
                policyLabel.appendChild(policy); view.appendChild(policyLabel);
                for (const [label, action] of [["Distance", "distance"], ["Angle", "angle"], ["Dihedral", "dihedral"]] as const) {
                    const details: ContextActionDetails = { endpoint_policy: "centroid" };
                    policy.addEventListener("change", () => { details.endpoint_policy = policy.value as ContextActionDetails["endpoint_policy"]; });
                    view.appendChild(this.makeActionButton(label, action, details));
                }
            });
            this.navigation.addSubmenu(main, "Interactions", view => {
                view.appendChild(this.makeActionButton("Inspect and Display Existing…", "open_interactions_for_target", { workflow: "inspect" }));
                view.appendChild(this.makeActionButton("Calculate for Target…", "open_interactions_for_target", { workflow: "calculate" }));
            });
        } else if (target.kind === "interaction") {
            main.appendChild(this.makeActionButton("Inspect This Interaction…", "inspect_picked_interaction"));
            main.appendChild(this.makeActionButton("Select Participants", "select_picked_interaction"));
            main.appendChild(this.makeActionButton("Focus Participants", "focus_picked_interaction"));
            if (target.tag?.trim()) this.navigation.addSubmenu(main, "Interaction set", view => {
                view.appendChild(this.makeActionButton("Focus Interaction Set", "focus_interaction"));
                view.appendChild(this.makeActionButton("Hide Interaction Representation", "toggle_interaction_visibility"));
                view.appendChild(this.makeActionButton("Edit Interaction Set in Studio…", "edit_interaction_in_studio"));
                view.appendChild(this.makeActionButton("Delete Interaction Representation", "delete_interaction"));
            });
        } else if (target.kind !== "empty") {
            main.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            main.appendChild(this.makeActionButton("Select Associated Atoms", "select_context_target", { scope: "target", op: "replace" }));
            if (target.tag?.trim()) {
                main.appendChild(this.makeActionButton(target.kind === "measurement" ? "Inspect and Edit Measurement…" : "Edit Appearance in Studio…", "edit_object_in_studio"));
                if (target.kind === "measurement") {
                    main.appendChild(this.makeActionButton("Hide Measurement", "hide_measurement"));
                    main.appendChild(this.makeActionButton("Delete Measurement", "delete_measurement"));
                } else if (target.kind === "annotation") {
                    main.appendChild(this.makeActionButton("Edit Annotation Text…", "edit_annotation_text"));
                    main.appendChild(this.makeActionButton("Hide Annotation", "toggle_annotation_visibility"));
                    main.appendChild(this.makeActionButton("Delete Annotation", "delete_annotation"));
                } else {
                    main.appendChild(this.makeActionButton("Hide Shape", "toggle_shape_visibility"));
                    main.appendChild(this.makeActionButton("Delete Shape", "delete_shape"));
                }
            }
        } else {
            main.appendChild(this.makeActionButton("Reset View", "reset_view"));
            main.appendChild(this.makeActionButton("Focus All", "focus_all"));
        }

        if (this.currentSelection && this.currentSelection.source_kind !== "empty") {
            this.navigation.addSubmenu(main, selectionTitle(this.currentSelection), view => {
                view.appendChild(this.makeActionButton("Focus Selection", "focus_selection"));
                view.appendChild(this.makeActionButton("Inspect Selection in Studio…", "open_navigate", { studio_section: "selection" }));
                view.appendChild(this.makeActionButton("Save Selection…", "save_selection"));
                view.appendChild(this.makeActionButton("Create Region from Selection…", "create_region_from_selection"));
                view.appendChild(this.makeActionButton("Create Section from Selection", "create_section_from_selection"));
                view.appendChild(this.makeActionButton("Add Label from Selection…", "add_label_from_selection"));
                this.appendSelectionExpanders(view);
                view.appendChild(this.makeActionButton("Clear Selection", "clear_selection"));
            });
        }
        if (this.currentRegions.length) {
            this.navigation.addSubmenu(main, "Related regions", view => {
                for (const region of this.currentRegions.slice(0, 8)) view.appendChild(this.makeRegionButton(region));
                view.appendChild(this.makeActionButton("Manage regions in Studio…", "open_navigate", { studio_section: "regions" }));
            });
        }
        // Collection size must not determine the size of the canvas menu.
        if (this.currentSavedSelections.length) main.appendChild(this.makeActionButton("Saved selections in Studio…", "open_navigate", { studio_section: "selection" }));

        const actions = this.isActionAllowed("addon_context_action")
            ? this.currentAddonActions.filter(item => item.target_kinds.includes(target.kind)) : [];
        const items = this.isActionAllowed("addon_context_action")
            ? this.currentAddonItems.filter(item => !item.target_kinds?.length || item.target_kinds.includes(target.kind)) : [];
        if (actions.length || items.length) {
            this.navigation.addSubmenu(main, "Add-ons", view => {
                for (const action of actions) view.appendChild(this.makeAddonActionButton(action));
                const byAddon = new Map<string, AddonContextItemSummary[]>();
                for (const item of items) {
                    if (!byAddon.has(item.addon)) byAddon.set(item.addon, []);
                    byAddon.get(item.addon)!.push(item);
                }
                for (const [addon, contributions] of byAddon) {
                    const heading = document.createElement("div");
                    heading.textContent = addon;
                    Object.assign(heading.style, { padding: "6px 10px", fontWeight: "600" });
                    view.appendChild(heading);
                    const groups = new Map<string, AddonContextItemSummary[]>();
                    for (const item of contributions) {
                        const group = item.group ?? "";
                        if (!groups.has(group)) groups.set(group, []);
                        groups.get(group)!.push(item);
                    }
                    for (const [group, entries] of groups) {
                        if (group) {
                            const label = document.createElement("div");
                            label.textContent = group;
                            Object.assign(label.style, { padding: "4px 10px", opacity: "0.75" });
                            view.appendChild(label);
                        }
                        for (const item of entries.sort((a, b) => (a.order ?? 0) - (b.order ?? 0))) view.appendChild(this.makeAddonItemButton(item));
                    }
                }
            });
        }
        this.navigation.addSubmenu(main, "View", view => {
            view.appendChild(this.makeActionButton("Reset View", "reset_view"));
            const scene = this.currentSceneState;
            view.appendChild(this.makeActionButton(scene?.isDarkMode ? "Use Light Background" : "Use Dark Background", "toggle_background", { mode: scene?.isDarkMode ? "light" : "dark" }));
            view.appendChild(this.makeActionButton(scene?.isSpinActive ? "Stop Automatic Rotation" : "Start Automatic Rotation", "toggle_spin", { enabled: !scene?.isSpinActive }));
            view.appendChild(this.makeActionButton(scene?.isSwingActive ? "Stop Swing" : "Start Swing", "toggle_swing", { enabled: !scene?.isSwingActive }));
            for (const mode of ["classic", "integrated", "cinema"]) {
                const label = mode[0].toUpperCase() + mode.slice(1);
                view.appendChild(this.makeActionButton(`${label}${scene?.currentViewerMode === mode ? " ✓" : ""}`, "set_viewer_mode", { text: mode }));
            }
        });
        main.appendChild(this.makeActionButton("Undo", "undo_scene"));
        main.appendChild(this.makeActionButton("Redo", "redo_scene"));
        const section = target.kind === "structure" ? "system" : target.kind === "interaction" ? "interactions"
            : target.kind === "measurement" ? "measures" : target.kind === "annotation" ? "annotations" : target.kind === "shape" ? "shapes" : undefined;
        main.appendChild(this.makeActionButton("Open Studio…", "open_navigate", section ? { studio_section: section } : undefined));
        main.appendChild(this.makeActionButton("Help", "show_help"));
        this.navigation.decorate();
    }

    close(): void {
        const wasOpen = this.root.style.display !== "none";
        this.currentTarget = null;
        this.currentSelection = null;
        this.currentLastMeasurement = null;
        this.currentSavedSelections = [];
        this.currentRegions = [];
        this.currentAddonActions = [];
        this.currentAddonItems = [];
        const active = document.activeElement;
        const restoreFocus = active && this.root.contains(active);
        this.root.style.display = "none";
        this.root.setAttribute("aria-hidden", "true");
        this.detachOutsidePointerHandler();
        if (restoreFocus) this.returnFocus?.focus?.();
        this.returnFocus = undefined;
        if (wasOpen) this.onClose?.();
    }

    invalidateInteractionContext(): void {
        if (this.currentTarget?.kind === "interaction") this.close();
    }

    dispose(): void {
        this.close();
        this.root.remove();
    }

    private makeActionButton(label: string, action: ContextMenuAction, detailsOverride?: ContextActionDetails): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute("data-molsysviewer-context-action", action);
        button.setAttribute("role", "menuitem");
        if (action === "undo_scene" || action === "redo_scene") {
            const enabled = action === "undo_scene" ? this.currentSceneState?.canUndo : this.currentSceneState?.canRedo;
            button.disabled = enabled !== true;
            button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
            if (button.disabled) {
                button.title = "No scene history operation is available";
                button.style.opacity = "0.45";
            }
        }
        const needsSelectionAtoms = ["focus_selection", "save_selection", "create_region_from_selection", "create_section_from_selection", "add_label_from_selection", "expand_selection"].includes(action);
        if (["inspect_picked_interaction", "select_picked_interaction", "focus_picked_interaction"].includes(action)) {
            const target = this.currentTarget;
            const identity = target?.kind === "interaction" ? target.entity_ref as Record<string, unknown> | undefined : undefined;
            const valid = !!identity && ["frame", "query_offset", "occurrence_index"].every(key => Number.isSafeInteger(identity[key]) && Number(identity[key]) >= 0)
                && ["analysis_name", "analysis_revision", "query_revision"].every(key => typeof identity[key] === "string" && !!identity[key]);
            if (!valid) {
                button.disabled = true; button.setAttribute("aria-disabled", "true");
                button.title = "This representation has no current query identity for occurrence actions";
                button.style.opacity = "0.45";
            }
        }
        if (["distance", "angle", "dihedral"].includes(action) && this.currentSceneState?.canMeasure === false) {
            button.disabled = true;
            button.setAttribute("aria-disabled", "true");
            button.title = "Measurement picking requires the canvas";
            button.style.opacity = "0.45";
        }
        if ((action === "focus_target" && this.currentTarget?.kind !== "empty" && !this.currentTarget?.atom_indices?.length && !this.currentTarget?.focusable)
            || (action === "select_context_target" && this.currentTarget?.kind !== "empty" && !this.currentTarget?.atom_indices?.length)
            || (action === "focus_all" && this.currentSceneState?.canFocusAll !== true)
            || (action === "show_help" && this.currentSceneState?.canHelp !== true)
            || (needsSelectionAtoms && !this.currentSelection?.atom_indices?.length)) {
            button.disabled = true;
            button.setAttribute("aria-disabled", "true");
            button.title = action === "focus_target" ? "This object has no available anchor or geometry bounds to focus"
                : action === "show_help" ? "Help is unavailable in this host" : action === "focus_all" ? "No molecular geometry is loaded in this canvas"
                : action === "select_context_target" ? "This object has no associated atoms" : "This action requires selected atoms";
            button.style.opacity = "0.45";
        }
        Object.assign(button.style, {
            display: this.isActionAllowed(action) ? "block" : "none",
            width: "100%",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: "inherit",
            textAlign: "left",
            cursor: "pointer",
        });
        button.addEventListener("pointerenter", () => {
            button.style.background = "rgba(255,255,255,0.10)";
        });
        button.addEventListener("pointerleave", () => {
            button.style.background = "transparent";
        });
        button.addEventListener("click", () => {
            if (!this.currentTarget || button.disabled || !this.isActionAllowed(action)) return;
            if (action === "add_label_from_selection" || action === "create_annotation_from_target") {
                this.renderLabelComposer(action === "create_annotation_from_target");
                return;
            }
            if (action === "save_selection") {
                this.renderSelectionComposer();
                return;
            }
            if (action === "create_region_from_selection" || action === "create_region_from_target") {
                this.renderRegionComposer(action === "create_region_from_target");
                return;
            }
            if (action === "activate_selection") {
                return;
            }
            const details = detailsOverride ?? this.resolveActionDetails(action);
            if (details === null) return;
            const handled = this.onAction?.(action, this.currentTarget, details ?? undefined) === true;
            if (!handled) this.notify?.({
                event: action === "undo_scene" ? "scene_history_undo" : action === "redo_scene" ? "scene_history_redo" : "interaction_context_action",
                action,
                context: this.currentTarget,
                ...(details ?? {}),
            });
            this.close();
        });
        return button;
    }

    private isActionAllowed(action: ContextMenuAction): boolean {
        return this.options.allowedActions?.has(action) !== false;
    }

    private appendSelectionExpanders(section: HTMLDivElement): void {
        const expandTitle = document.createElement("div");
        expandTitle.textContent = "Expand selection to...";
        Object.assign(expandTitle.style, {
            padding: "8px 8px 4px 8px",
            opacity: "0.6",
            fontSize: "11px",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            fontWeight: "600",
        });
        section.appendChild(expandTitle);

        for (const level of ["group", "component", "molecule", "chain", "entity"] as const) {
            section.appendChild(this.makeActionButton(
                level[0].toUpperCase() + level.slice(1),
                "expand_selection",
                { level },
            ));
        }

        const spatialTitle = document.createElement("div");
        spatialTitle.textContent = "Spatial expansion...";
        Object.assign(spatialTitle.style, {
            padding: "8px 8px 4px 8px",
            opacity: "0.6",
            fontSize: "11px",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            fontWeight: "600",
        });
        section.appendChild(spatialTitle);

        for (const distance of [3, 5, 8] as const) {
            section.appendChild(this.makeActionButton(
                `Within ${distance} Å`,
                "expand_selection",
                { level: "spatial", distance_angstroms: distance },
            ));
        }
    }

    private makeSavedSelectionButton(selection: SavedSelectionSummary): HTMLButtonElement {
        const label = `${selection.tag} · ${selection.atom_count} atom${selection.atom_count === 1 ? "" : "s"}`;
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute("data-molsysviewer-saved-selection", selection.tag);
        Object.assign(button.style, {
            display: "block",
            width: "100%",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: "inherit",
            textAlign: "left",
            cursor: "pointer",
        });
        button.addEventListener("pointerenter", () => {
            button.style.background = "rgba(255,255,255,0.10)";
        });
        button.addEventListener("pointerleave", () => {
            button.style.background = "transparent";
        });
        button.addEventListener("click", () => {
            if (!this.currentTarget) return;
            const details = { tag: selection.tag };
            this.onAction?.("activate_selection", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "activate_selection",
                context: this.currentTarget,
                ...details,
            });
            this.close();
        });
        return button;
    }

    private makeRegionButton(region: RegionSummary): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            alignItems: "center",
            gap: "4px",
            borderRadius: "8px",
        });

        const label = document.createElement("button");
        label.type = "button";
        const atomLabel = `${region.atom_count} atom${region.atom_count === 1 ? "" : "s"}`;
        const hiddenSuffix = region.hidden ? " · hidden" : "";
        label.textContent = `${region.tag} · ${atomLabel}${hiddenSuffix}`;
        label.setAttribute("data-molsysviewer-region", region.tag);
        Object.assign(label.style, {
            flex: "1 1 auto",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: region.hidden ? "rgba(244,244,245,0.55)" : "inherit",
            textDecoration: region.hidden ? "line-through" : "none",
            textAlign: "left",
            cursor: "pointer",
            fontSize: "inherit",
        });
        label.addEventListener("pointerenter", () => { label.style.background = "rgba(255,255,255,0.10)"; });
        label.addEventListener("pointerleave", () => { label.style.background = "transparent"; });
        label.addEventListener("click", () => {
            if (!this.currentTarget) return;
            const details = { tag: region.tag };
            this.onAction?.("focus_region", this.currentTarget, details);
            this.notify?.({ event: "interaction_context_action", action: "focus_region", context: this.currentTarget, ...details });
            this.close();
        });
        const open = this.makeActionButton("Open in Studio…", "open_region_in_studio", { tag: region.tag });
        open.textContent = "↗";
        open.title = `Open region ${region.tag} in Studio`;
        open.setAttribute("aria-label", `Open region ${region.tag} in Studio`);
        open.style.width = "auto";
        row.appendChild(open);

        const mkIconBtn = (svgPath: string, title: string, onClick: () => void): HTMLButtonElement => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.title = title;
            btn.setAttribute("aria-label", title);
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${svgPath}</svg>`;
            Object.assign(btn.style, {
                flexShrink: "0",
                padding: "5px",
                border: "0",
                borderRadius: "6px",
                background: "transparent",
                color: "rgba(244,244,245,0.55)",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
            });
            btn.addEventListener("pointerenter", () => { btn.style.background = "rgba(255,255,255,0.10)"; btn.style.color = "#f4f4f5"; });
            btn.addEventListener("pointerleave", () => { btn.style.background = "transparent"; btn.style.color = "rgba(244,244,245,0.55)"; });
            btn.addEventListener("click", (ev) => { ev.stopPropagation(); onClick(); });
            return btn;
        };

        const EYE_ON  = `<path d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5z"/><circle cx="8" cy="8" r="2.5"/>`;
        const EYE_OFF = `<path d="M1 8s2.5-5 7-5 5.5 3 5.5 3M14.5 11.5S12 13 8 13c-4.5 0-7-5-7-5"/><line x1="2" y1="2" x2="14" y2="14"/>`;
        const TRASH   = `<polyline points="3,6 13,6"/><path d="M5,6V4a1,1,0,0,1,1-1h4a1,1,0,0,1,1,1V6"/><rect x="4" y="6" width="8" height="8" rx="1"/>`;
        const PENCIL  = `<path d="M11 2l3 3-9 9H2v-3L11 2z"/>`;

        const toggleBtn = mkIconBtn(region.hidden ? EYE_OFF : EYE_ON, region.hidden ? "Show region" : "Hide region", () => {
            if (!this.currentTarget) return;
            const details = { tag: region.tag };
            this.onAction?.("toggle_region_visibility", this.currentTarget, details);
            this.notify?.({ event: "interaction_context_action", action: "toggle_region_visibility", context: this.currentTarget, ...details });
            this.close();
        });

        const renameBtn = mkIconBtn(PENCIL, "Rename region", () => {
            this.renderRenameRegionComposer(region.tag);
        });

        const deleteBtn = mkIconBtn(TRASH, "Delete region", () => {
            if (!this.currentTarget) return;
            const details = { tag: region.tag };
            this.onAction?.("delete_region", this.currentTarget, details);
            this.notify?.({ event: "interaction_context_action", action: "delete_region", context: this.currentTarget, ...details });
            this.close();
        });

        if (this.isActionAllowed("focus_region")) row.appendChild(label);
        if (this.isActionAllowed("toggle_region_visibility")) row.appendChild(toggleBtn);
        if (this.isActionAllowed("rename_region")) row.appendChild(renameBtn);
        if (this.isActionAllowed("delete_region")) row.appendChild(deleteBtn);
        return row;
    }

    private renderRegionComposer(fromTarget = false): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = fromTarget ? "New Region from Target" : "New Region from Selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.scrollEl.appendChild(title);

        const subtitle = document.createElement("div");
        subtitle.textContent = fromTarget ? targetTitle(this.currentTarget) : selectionSummary(this.currentSelection);
        Object.assign(subtitle.style, {
            padding: "0 8px 8px 8px",
            opacity: "0.82",
            fontSize: "12px",
        });
        this.scrollEl.appendChild(subtitle);
        const scope = fromTarget ? this.appendTargetScope() : null;

        const input = document.createElement("input");
        input.type = "text";
        input.value = "";
        input.placeholder = "Region tag (optional)";
        Object.assign(input.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            margin: "0 0 8px 0",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.06)",
            color: "#f4f4f5",
            outline: "none",
        });
        this.scrollEl.appendChild(input);

        const actions = document.createElement("div");
        Object.assign(actions.style, { display: "flex", gap: "8px" });

        const save = document.createElement("button");
        save.type = "button";
        save.textContent = "Create Region";
        Object.assign(save.style, {
            flex: "1 1 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(167, 243, 208, 0.18)",
            color: "#d1fae5",
            cursor: "pointer",
        });

        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "Back";
        Object.assign(cancel.style, {
            flex: "0 0 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(255,255,255,0.08)",
            color: "#f4f4f5",
            cursor: "pointer",
        });

        const submit = () => {
            if (!this.currentTarget) return;
            const tag = String(input.value ?? "").trim();
            const action = fromTarget ? "create_region_from_target" : "create_region_from_selection";
            const details: ContextActionDetails = { ...(tag.length > 0 ? { tag } : {}), ...(scope ? { scope: scope.value as ContextActionDetails["scope"] } : {}) };
            this.onAction?.(action, this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action,
                context: this.currentTarget,
                ...details,
            });
            this.close();
        };

        const goBack = () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
                this.currentSavedSelections,
                this.currentRegions,
                this.currentAddonActions,
                this.currentAddonItems,
                this.currentSceneState,
            );
        };

        save.addEventListener("click", submit);
        cancel.addEventListener("click", goBack);
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") { event.preventDefault?.(); submit(); }
            else if (event?.key === "Escape") { event.preventDefault?.(); goBack(); }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.scrollEl.appendChild(actions);
        this.positionMenu();
        input.focus?.();
    }

    private resolveActionDetails(action: ContextMenuAction): ContextActionDetails | null {
        if (["delete_interaction", "focus_interaction", "inspect_picked_interaction", "select_picked_interaction", "focus_picked_interaction", "toggle_interaction_visibility", "edit_interaction_in_studio"].includes(action)) {
            if (this.currentTarget?.kind !== "interaction" || !this.currentTarget.tag?.trim()) return null;
            return { tag: this.currentTarget.tag, ...(action === "toggle_interaction_visibility" ? { hidden: true } : {}) };
        }
        if (["delete_annotation", "delete_shape", "delete_measurement", "hide_measurement", "edit_object_in_studio", "edit_annotation_text", "toggle_annotation_visibility", "toggle_shape_visibility"].includes(action)) {
            const tag =
                this.currentTarget?.kind === "annotation" || this.currentTarget?.kind === "shape" || this.currentTarget?.kind === "measurement"
                    ? this.currentTarget.tag
                    : undefined;
            if (!tag || tag.trim() === "") return null;
            return { tag, ...(["toggle_annotation_visibility", "toggle_shape_visibility"].includes(action) ? { hidden: true } : {}) };
        }
        if (action === "create_section_from_selection") {
            const camera_forward = this.getCameraDirection?.() ?? [0, 0, -1] as [number, number, number];
            return { camera_forward };
        }
        return {};
    }

    private hasAddonContextItem(addon: string, id: string, target: ContextMenuTarget): boolean {
        return this.currentAddonItems.some((item) => (
            item.addon === addon
            && item.id === id
            && item.enabled !== false
            && (!item.target_kinds || item.target_kinds.length === 0 || item.target_kinds.includes(target.kind))
        ));
    }

    private makeAddonActionButton(addonAction: AddonContextActionSummary): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = `${addonAction.title} · ${addonAction.addon}`;
        button.setAttribute("data-molsysviewer-addon-action", `${addonAction.addon}:${addonAction.id}`);
        Object.assign(button.style, {
            display: "block",
            width: "100%",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: "inherit",
            textAlign: "left",
            cursor: "pointer",
        });
        button.addEventListener("pointerenter", () => {
            button.style.background = "rgba(255,255,255,0.10)";
        });
        button.addEventListener("pointerleave", () => {
            button.style.background = "transparent";
        });
        button.addEventListener("click", () => {
            if (!this.currentTarget) return;
            const details = { tag: addonAction.id };
            this.onAction?.("addon_context_action", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "addon_context_action",
                context: this.currentTarget,
                addon: addonAction.addon,
                addon_action_id: addonAction.id,
                addon_action_title: addonAction.title,
            });
            this.close();
        });
        return button;
    }

    private makeAddonItemButton(item: AddonContextItemSummary): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = item.title;
        button.setAttribute("data-molsysviewer-addon-item", `${item.addon}:${item.id}`);
        const disabled = item.enabled === false;
        button.disabled = disabled;
        if (disabled) button.setAttribute("aria-disabled", "true");
        Object.assign(button.style, {
            display: "block",
            width: "100%",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: "inherit",
            textAlign: "left",
            cursor: disabled ? "default" : "pointer",
            opacity: disabled ? "0.45" : "1",
        });
        if (!disabled) {
            button.addEventListener("pointerenter", () => {
                button.style.background = "rgba(255,255,255,0.10)";
            });
            button.addEventListener("pointerleave", () => {
                button.style.background = "transparent";
            });
            button.addEventListener("click", () => {
                if (!this.currentTarget) return;
                this.notify?.({
                    event: "interaction_context_action",
                    action: "addon_context_action",
                    context: this.currentTarget,
                    addon: item.addon,
                    addon_action_id: item.id,
                    addon_action_title: item.title,
                    addon_action_payload: item.payload ?? {},
                });
                this.close();
            });
        }
        return button;
    }

    private renderRenameRegionComposer(oldTag: string): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "Rename Region";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.scrollEl.appendChild(title);

        const subtitle = document.createElement("div");
        subtitle.textContent = `Current tag: ${oldTag}`;
        Object.assign(subtitle.style, {
            padding: "0 8px 8px 8px",
            opacity: "0.82",
            fontSize: "12px",
        });
        this.scrollEl.appendChild(subtitle);

        const input = document.createElement("input");
        input.type = "text";
        input.value = oldTag;
        input.placeholder = "New tag";
        Object.assign(input.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            margin: "0 0 8px 0",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.06)",
            color: "#f4f4f5",
            outline: "none",
        });
        this.scrollEl.appendChild(input);

        const actions = document.createElement("div");
        Object.assign(actions.style, { display: "flex", gap: "8px" });

        const save = document.createElement("button");
        save.type = "button";
        save.textContent = "Rename";
        Object.assign(save.style, {
            flex: "1 1 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(167, 243, 208, 0.18)",
            color: "#d1fae5",
            cursor: "pointer",
        });

        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "Back";
        Object.assign(cancel.style, {
            flex: "0 0 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(255,255,255,0.08)",
            color: "#f4f4f5",
            cursor: "pointer",
        });

        const submit = () => {
            const newTag = String(input.value ?? "").trim();
            if (newTag.length === 0 || newTag === oldTag || !this.currentTarget) return;
            const details: ContextActionDetails = { tag: oldTag, new_tag: newTag };
            this.onAction?.("rename_region", this.currentTarget, details);
            this.notify?.({ event: "interaction_context_action", action: "rename_region", context: this.currentTarget, ...details });
            this.close();
        };

        const goBack = () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
                this.currentSavedSelections,
                this.currentRegions,
                this.currentAddonActions,
                this.currentAddonItems,
                this.currentSceneState,
            );
        };

        save.addEventListener("click", submit);
        cancel.addEventListener("click", goBack);
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") { event.preventDefault?.(); submit(); }
            else if (event?.key === "Escape") { event.preventDefault?.(); goBack(); }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.scrollEl.appendChild(actions);
        input.select?.();
    }

    private appendTargetScope(): HTMLSelectElement {
        const label = document.createElement("label"); label.textContent = "Atom scope";
        const select = document.createElement("select");
        select.setAttribute("data-molsysviewer-context-target-scope", "true");
        select.setAttribute("aria-label", "Target atom scope");
        for (const [value, name] of [["target", "Target atoms"], ["atom", "Pointed atom"], ["group", "Residue"], ["chain", "Chain"]] as const) {
            const option = document.createElement("option"); option.value = value; option.textContent = name;
            option.disabled = value === "atom" && (this.currentTarget?.kind !== "structure" || this.currentTarget.atom_index === undefined);
            select.appendChild(option);
        }
        select.value = "target";
        Object.assign(select.style, { display: "block", width: "100%", margin: "6px 0 10px", color: "inherit", background: "#27272a" });
        label.appendChild(select); this.scrollEl.appendChild(label);
        return select;
    }

    private renderLabelComposer(fromTarget = false): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = fromTarget ? "Annotation from target" : "Label from selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "8px",
        });
        this.scrollEl.appendChild(title);
        const scope = fromTarget ? this.appendTargetScope() : null;

        const input = document.createElement("input");
        input.type = "text";
        input.value = "";
        input.placeholder = "Label text";
        Object.assign(input.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            margin: "0 0 8px 0",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.06)",
            color: "#f4f4f5",
            outline: "none",
        });
        this.scrollEl.appendChild(input);

        // Style row: color swatch + size slider
        const styleRow = document.createElement("div");
        Object.assign(styleRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "8px",
            margin: "0 0 8px 0",
        });

        const colorInput = document.createElement("input");
        colorInput.type = "color";
        colorInput.value = "#4080e0";
        colorInput.title = "Label color";
        Object.assign(colorInput.style, {
            width: "28px",
            height: "28px",
            padding: "0",
            border: "0",
            borderRadius: "6px",
            background: "transparent",
            cursor: "pointer",
            flexShrink: "0",
        });

        const sizeLabel = document.createElement("span");
        sizeLabel.textContent = "Size";
        Object.assign(sizeLabel.style, { fontSize: "12px", opacity: "0.75", flexShrink: "0" });

        const sizeInput = document.createElement("input");
        sizeInput.type = "range";
        sizeInput.min = "0.6";
        sizeInput.max = "2.0";
        sizeInput.step = "0.1";
        sizeInput.value = "1.0";
        sizeInput.title = "Label size (em)";
        Object.assign(sizeInput.style, { flex: "1 1 auto", cursor: "pointer" });

        styleRow.appendChild(colorInput);
        styleRow.appendChild(sizeLabel);
        styleRow.appendChild(sizeInput);
        this.scrollEl.appendChild(styleRow);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "8px",
        });

        const save = document.createElement("button");
        save.type = "button";
        save.textContent = "Create Label";
        Object.assign(save.style, {
            flex: "1 1 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(110, 231, 183, 0.18)",
            color: "#d1fae5",
            cursor: "pointer",
        });

        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "Back";
        Object.assign(cancel.style, {
            flex: "0 0 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(255,255,255,0.08)",
            color: "#f4f4f5",
            cursor: "pointer",
        });

        const submit = () => {
            const text = String(input.value ?? "").trim();
            if (text.length === 0 || !this.currentTarget) return;
            const label_style: ContextActionDetails["label_style"] = {
                color: colorInput.value,
                size_em: parseFloat(sizeInput.value),
            };
            const action = fromTarget ? "create_annotation_from_target" : "add_label_from_selection";
            const details: ContextActionDetails = { text, label_style, ...(scope ? { scope: scope.value as ContextActionDetails["scope"] } : {}) };
            this.onAction?.(action, this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action,
                context: this.currentTarget,
                ...details,
            });
            this.close();
        };

        const goBack = () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
                this.currentSavedSelections,
                this.currentRegions,
                this.currentAddonActions,
                this.currentAddonItems,
                this.currentSceneState,
            );
        };

        save.addEventListener("click", submit);
        cancel.addEventListener("click", goBack);
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") {
                event.preventDefault?.();
                submit();
            } else if (event?.key === "Escape") {
                event.preventDefault?.();
                goBack();
            }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.scrollEl.appendChild(actions);
        this.positionMenu();
        input.focus?.();
    }

    private renderSelectionComposer(): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "Save Selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.scrollEl.appendChild(title);

        const subtitle = document.createElement("div");
        subtitle.textContent = selectionSummary(this.currentSelection);
        Object.assign(subtitle.style, {
            padding: "0 8px 8px 8px",
            opacity: "0.82",
            fontSize: "12px",
        });
        this.scrollEl.appendChild(subtitle);

        const input = document.createElement("input");
        input.type = "text";
        input.value = "";
        input.placeholder = "Selection tag";
        Object.assign(input.style, {
            display: "block",
            width: "100%",
            boxSizing: "border-box",
            margin: "0 0 8px 0",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.06)",
            color: "#f4f4f5",
            outline: "none",
        });
        this.scrollEl.appendChild(input);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "8px",
        });

        const save = document.createElement("button");
        save.type = "button";
        save.textContent = "Save Selection";
        Object.assign(save.style, {
            flex: "1 1 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(147, 197, 253, 0.18)",
            color: "#dbeafe",
            cursor: "pointer",
        });

        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "Back";
        Object.assign(cancel.style, {
            flex: "0 0 auto",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "0",
            background: "rgba(255,255,255,0.08)",
            color: "#f4f4f5",
            cursor: "pointer",
        });

        const submit = () => {
            const tag = String(input.value ?? "").trim();
            if (tag.length === 0 || !this.currentTarget) return;
            const details = { tag };
            this.onAction?.("save_selection", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "save_selection",
                context: this.currentTarget,
                ...details,
            });
            this.close();
        };

        const goBack = () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
                this.currentSavedSelections,
                this.currentRegions,
                this.currentAddonActions,
                this.currentAddonItems,
                this.currentSceneState,
            );
        };

        save.addEventListener("click", submit);
        cancel.addEventListener("click", goBack);
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") {
                event.preventDefault?.();
                submit();
            } else if (event?.key === "Escape") {
                event.preventDefault?.();
                goBack();
            }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.scrollEl.appendChild(actions);
        this.positionMenu();
        input.focus?.();
    }

    private detachOutsidePointerHandler(): void {
        if (!this.outsidePointerHandler) return;
        window.removeEventListener("pointerdown", this.outsidePointerHandler, true);
        this.outsidePointerHandler = undefined;
    }
}
