import type { ActiveSelectionPayload } from "../managers/active-selection";

type BaseTarget =
    | { event: "interaction_context_menu"; kind: "empty" }
    | {
        event: "interaction_context_menu";
        kind: "structure";
        atom_indices: number[];
        group_name?: string;
        chain_name?: string;
    }
    | { event: "interaction_context_menu"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string }
    | { event: "interaction_context_menu"; kind: "measurement"; atom_indices: number[]; tag?: string; measurement_name?: string }
    | { event: "interaction_context_menu"; kind: "annotation"; atom_indices: number[]; tag?: string; text?: string };

export type ContextMenuTarget = BaseTarget;

export type ContextMenuAction =
    | "distance"
    | "angle"
    | "dihedral"
    | "focus_target"
    | "focus_region"
    | "toggle_region_visibility"
    | "delete_region"
    | "rename_region"
    | "hide_measurement"
    | "delete_annotation"
    | "delete_shape"
    | "delete_measurement"
    | "focus_selection"
    | "activate_selection"
    | "save_selection"
    | "remove_selection"
    | "clear_selection"
    | "create_region_from_selection"
    | "create_section_from_selection"
    | "add_label_from_selection"
    | "addon_context_action"
    | "reset_view"
    | "toggle_background"
    | "toggle_spin"
    | "toggle_swing";

export type ContextActionDetails = {
    endpoint_policy?: "atom" | "centroid" | "representative_atom";
    text?: string;
    tag?: string;
    new_tag?: string;
    camera_forward?: [number, number, number];
    label_style?: { color?: string; size_em?: number };
};

export type LastMeasurementSummary = {
    action: "distance" | "angle" | "dihedral";
    picked_count: number;
};

export type SavedSelectionSummary = {
    tag: string;
    atom_count: number;
};

export type RegionSummary = {
    tag: string;
    atom_indices: number[];
    atom_count: number;
    selection?: string;
    hidden: boolean;
};

export type AddonContextActionSummary = {
    addon: string;
    id: string;
    title: string;
    target_kinds: string[];
    group?: string;
};

function targetTitle(target: ContextMenuTarget): string {
    if (target.kind === "empty") return "Canvas";
    if (target.kind === "shape") return target.shape_name?.trim() || target.tag?.trim() || "Shape";
    if (target.kind === "measurement") return target.measurement_name?.trim() || target.tag?.trim() || "Measurement";
    if (target.kind === "annotation") return target.text?.trim() || target.tag?.trim() || "Annotation";
    if (target.group_name?.trim()) {
        return target.chain_name?.trim()
            ? `${target.group_name.trim()} · chain ${target.chain_name.trim()}`
            : target.group_name.trim();
    }
    const count = target.atom_indices.length;
    return count === 1 ? "Element (1 atom)" : `Element (${count} atoms)`;
}

function selectionTitle(selection: ActiveSelectionPayload): string {
    if (selection.source_kind === "mixed") {
        return `Active selection: mixed (${selection.items.length} items)`;
    }
    if (selection.source_kind === "annotation") {
        return `Active selection: annotation (${selection.count_annotations})`;
    }
    if (selection.source_kind === "element") {
        return `Active selection: ${selection.count_groups} group${selection.count_groups === 1 ? "" : "s"}`;
    }
    return "Active selection";
}

function selectionSummary(selection: ActiveSelectionPayload | null): string {
    if (!selection || selection.source_kind === "empty") return "Current selection";
    return `Stored as ${selection.count_atoms} atom${selection.count_atoms === 1 ? "" : "s"}`;
}

export class ViewerContextMenu {
    private readonly root: HTMLDivElement;
    private outsidePointerHandler?: (event: PointerEvent) => void;
    private scrollEl!: HTMLDivElement;
    private currentTarget: ContextMenuTarget | null = null;
    private currentSelection: ActiveSelectionPayload | null = null;
    private currentLastMeasurement: LastMeasurementSummary | null = null;
    private currentSavedSelections: SavedSelectionSummary[] = [];
    private currentRegions: RegionSummary[] = [];
    private currentAddonActions: AddonContextActionSummary[] = [];
    private currentPageX = 0;
    private currentPageY = 0;

    constructor(
        private readonly host: HTMLElement,
        private readonly notify?: (msg: any) => void,
        private readonly onAction?: (action: ContextMenuAction, target: ContextMenuTarget, details?: ContextActionDetails) => void,
        private readonly onClose?: () => void,
        private readonly getCameraDirection?: () => [number, number, number],
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-context-menu", "true");
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
    ): void {
        this.currentTarget = target;
        this.currentSelection = activeSelection ?? null;
        this.currentLastMeasurement = lastMeasurement ?? null;
        this.currentSavedSelections = Array.isArray(savedSelections) ? [...savedSelections] : [];
        this.currentRegions = Array.isArray(regions) ? [...regions] : [];
        this.currentAddonActions = Array.isArray(addonActions) ? [...addonActions] : [];
        this.currentPageX = pageX;
        this.currentPageY = pageY;
        this.scrollEl.replaceChildren();

        const header = document.createElement("div");
        header.setAttribute("data-molsysviewer-context-menu-title", "true");
        header.textContent = targetTitle(target);
        Object.assign(header.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.scrollEl.appendChild(header);

        if (target.kind === "structure") {
            this.scrollEl.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            this.scrollEl.appendChild(this.makeActionButton("Distance", "distance"));
            this.scrollEl.appendChild(this.makeActionButton("Distance (Representative Atom)", "distance", { endpoint_policy: "representative_atom" }));
            this.scrollEl.appendChild(this.makeActionButton("Angle", "angle"));
            this.scrollEl.appendChild(this.makeActionButton("Angle (Representative Atom)", "angle", { endpoint_policy: "representative_atom" }));
            this.scrollEl.appendChild(this.makeActionButton("Dihedral", "dihedral"));
            this.scrollEl.appendChild(this.makeActionButton("Dihedral (Representative Atom)", "dihedral", { endpoint_policy: "representative_atom" }));
        } else if (target.kind === "shape") {
            this.scrollEl.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            if (target.tag?.trim()) {
                this.scrollEl.appendChild(this.makeActionButton("Delete Shape", "delete_shape"));
            }
        } else if (target.kind === "measurement") {
            this.scrollEl.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            if (target.tag?.trim()) {
                this.scrollEl.appendChild(this.makeActionButton("Hide Measurement", "hide_measurement"));
                this.scrollEl.appendChild(this.makeActionButton("Delete Measurement", "delete_measurement"));
            }
        } else if (target.kind === "annotation") {
            this.scrollEl.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            if (target.tag?.trim()) {
                this.scrollEl.appendChild(this.makeActionButton("Delete Annotation", "delete_annotation"));
            }
        } else {
            // Empty canvas — scene-level actions
            this.scrollEl.appendChild(this.makeActionButton("Reset View", "reset_view"));
            this.scrollEl.appendChild(this.makeActionButton("Toggle Background", "toggle_background"));
            this.scrollEl.appendChild(this.makeActionButton("Toggle Spin", "toggle_spin"));
            this.scrollEl.appendChild(this.makeActionButton("Toggle Swing", "toggle_swing"));
        }

        if (this.currentSelection && this.currentSelection.source_kind !== "empty") {
            const section = document.createElement("div");
            Object.assign(section.style, {
                marginTop: "8px",
                paddingTop: "8px",
                borderTop: "1px solid rgba(255,255,255,0.10)",
            });

            const title = document.createElement("div");
            title.textContent = selectionTitle(this.currentSelection);
            Object.assign(title.style, {
                padding: "4px 8px 8px 8px",
                opacity: "0.82",
                fontSize: "12px",
            });
            section.appendChild(title);
            section.appendChild(this.makeActionButton("Focus Selection", "focus_selection"));
            section.appendChild(this.makeActionButton("Save Selection", "save_selection"));
            section.appendChild(this.makeActionButton("Create Region from Selection", "create_region_from_selection"));
            section.appendChild(this.makeActionButton("Create Section from Selection", "create_section_from_selection"));
            section.appendChild(this.makeActionButton("Add Label from Selection", "add_label_from_selection"));
            if (this.currentSelection.count_atoms > 0) {
                section.appendChild(this.makeActionButton("Remove Selected Atoms", "remove_selection"));
            }
            section.appendChild(this.makeActionButton("Clear Selection", "clear_selection"));
            this.scrollEl.appendChild(section);
        }

        if (this.currentSavedSelections.length > 0) {
            const section = document.createElement("div");
            Object.assign(section.style, {
                marginTop: "8px",
                paddingTop: "8px",
                borderTop: "1px solid rgba(255,255,255,0.10)",
            });

            const title = document.createElement("div");
            title.textContent = "Saved selections";
            Object.assign(title.style, {
                padding: "4px 8px 8px 8px",
                opacity: "0.82",
                fontSize: "12px",
            });
            section.appendChild(title);

            for (const selection of this.currentSavedSelections) {
                section.appendChild(this.makeSavedSelectionButton(selection));
            }
            this.scrollEl.appendChild(section);
        }

        if (this.currentRegions.length > 0) {
            const section = document.createElement("div");
            Object.assign(section.style, {
                marginTop: "8px",
                paddingTop: "8px",
                borderTop: "1px solid rgba(255,255,255,0.10)",
            });

            const title = document.createElement("div");
            title.textContent = "Regions";
            Object.assign(title.style, {
                padding: "4px 8px 8px 8px",
                opacity: "0.82",
                fontSize: "12px",
            });
            section.appendChild(title);

            for (const region of this.currentRegions) {
                section.appendChild(this.makeRegionButton(region));
            }
            this.scrollEl.appendChild(section);
        }

        const matchingAddonActions = this.currentAddonActions.filter((item) => item.target_kinds.includes(target.kind));
        if (matchingAddonActions.length > 0) {
            const section = document.createElement("div");
            Object.assign(section.style, {
                marginTop: "8px",
                paddingTop: "8px",
                borderTop: "1px solid rgba(255,255,255,0.10)",
            });

            const title = document.createElement("div");
            title.textContent = "Add-ons";
            Object.assign(title.style, {
                padding: "4px 8px 8px 8px",
                opacity: "0.82",
                fontSize: "12px",
            });
            section.appendChild(title);

            for (const addonAction of matchingAddonActions) {
                section.appendChild(this.makeAddonActionButton(addonAction));
            }
            this.scrollEl.appendChild(section);
        }

        const rect = this.host.getBoundingClientRect();
        this.scrollEl.style.maxHeight = "";
        this.root.style.display = "block";
        const menuWidth = this.root.offsetWidth || 180;
        const menuHeight = this.root.offsetHeight || 120;
        const left = Math.min(Math.max(0, pageX - rect.left), Math.max(0, rect.width - menuWidth));
        const rawTop = pageY - rect.top;
        const top = Math.min(Math.max(0, rawTop), Math.max(0, rect.height - menuHeight));
        const availableBelow = rect.height - top - 12;
        if (menuHeight > availableBelow) {
            this.scrollEl.style.maxHeight = `${Math.max(80, availableBelow)}px`;
            this.scrollEl.style.borderBottomLeftRadius = "9px";
            this.scrollEl.style.borderBottomRightRadius = "9px";
        } else {
            this.scrollEl.style.borderBottomLeftRadius = "";
            this.scrollEl.style.borderBottomRightRadius = "";
        }
        this.root.style.left = `${left}px`;
        this.root.style.top = `${top}px`;

        this.detachOutsidePointerHandler();
        this.outsidePointerHandler = (event: PointerEvent) => {
            const targetNode = event.target as Node | null;
            if (targetNode && this.root.contains(targetNode)) return;
            this.close();
        };
        window.addEventListener("pointerdown", this.outsidePointerHandler, true);
    }

    close(): void {
        const wasOpen = this.root.style.display !== "none";
        this.currentTarget = null;
        this.currentSelection = null;
        this.currentLastMeasurement = null;
        this.currentSavedSelections = [];
        this.currentRegions = [];
        this.currentAddonActions = [];
        this.root.style.display = "none";
        this.detachOutsidePointerHandler();
        if (wasOpen) this.onClose?.();
    }

    dispose(): void {
        this.close();
        this.root.remove();
    }

    private makeActionButton(label: string, action: ContextMenuAction, detailsOverride?: ContextActionDetails): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
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
            if (action === "add_label_from_selection") {
                this.renderLabelComposer();
                return;
            }
            if (action === "save_selection") {
                this.renderSelectionComposer();
                return;
            }
            if (action === "create_region_from_selection") {
                this.renderRegionComposer();
                return;
            }
            if (action === "activate_selection") {
                return;
            }
            const details = detailsOverride ?? this.resolveActionDetails(action);
            if (details === null) return;
            this.onAction?.(action, this.currentTarget, details ?? undefined);
            this.notify?.({
                event: "interaction_context_action",
                action,
                context: this.currentTarget,
                ...(details ?? {}),
            });
            this.close();
        });
        return button;
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

        const mkIconBtn = (svgPath: string, title: string, onClick: () => void): HTMLButtonElement => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.title = title;
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

        row.appendChild(label);
        row.appendChild(toggleBtn);
        row.appendChild(renameBtn);
        row.appendChild(deleteBtn);
        return row;
    }

    private renderRegionComposer(): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "New Region from Selection";
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
            const details = tag.length > 0 ? { tag } : {};
            this.onAction?.("create_region_from_selection", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "create_region_from_selection",
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
        input.focus?.();
    }

    private resolveActionDetails(action: ContextMenuAction): ContextActionDetails | null {
        if (action === "delete_annotation" || action === "delete_shape" || action === "delete_measurement" || action === "hide_measurement") {
            const tag =
                this.currentTarget?.kind === "annotation" || this.currentTarget?.kind === "shape" || this.currentTarget?.kind === "measurement"
                    ? this.currentTarget.tag
                    : undefined;
            if (!tag || tag.trim() === "") return null;
            return { tag };
        }
        if (action === "create_section_from_selection") {
            const camera_forward = this.getCameraDirection?.() ?? [0, 0, -1] as [number, number, number];
            return { camera_forward };
        }
        return {};
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

    private renderLabelComposer(): void {
        if (!this.currentTarget) return;
        this.scrollEl.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "Label from selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "8px",
        });
        this.scrollEl.appendChild(title);

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
            const details: ContextActionDetails = { text, label_style };
            this.onAction?.("add_label_from_selection", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "add_label_from_selection",
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
        input.focus?.();
    }

    private detachOutsidePointerHandler(): void {
        if (!this.outsidePointerHandler) return;
        window.removeEventListener("pointerdown", this.outsidePointerHandler, true);
        this.outsidePointerHandler = undefined;
    }
}
