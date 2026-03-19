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
    | { event: "interaction_context_menu"; kind: "annotation"; atom_indices: number[]; tag?: string; text?: string };

export type ContextMenuTarget = BaseTarget;

export type ContextMenuAction =
    | "distance"
    | "angle"
    | "dihedral"
    | "focus_target"
    | "focus_region"
    | "delete_annotation"
    | "delete_shape"
    | "focus_selection"
    | "activate_selection"
    | "save_selection"
    | "clear_selection"
    | "create_region_from_selection"
    | "add_label_from_selection"
    | "persist_last_measurement";

export type ContextActionDetails = {
    text?: string;
    tag?: string;
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

function targetTitle(target: ContextMenuTarget): string {
    if (target.kind === "empty") return "Canvas";
    if (target.kind === "shape") return target.shape_name?.trim() || target.tag?.trim() || "Shape";
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
    private currentTarget: ContextMenuTarget | null = null;
    private currentSelection: ActiveSelectionPayload | null = null;
    private currentLastMeasurement: LastMeasurementSummary | null = null;
    private currentSavedSelections: SavedSelectionSummary[] = [];
    private currentRegions: RegionSummary[] = [];
    private currentPageX = 0;
    private currentPageY = 0;

    constructor(
        private readonly host: HTMLElement,
        private readonly notify?: (msg: any) => void,
        private readonly onAction?: (action: ContextMenuAction, target: ContextMenuTarget, details?: ContextActionDetails) => void,
        private readonly onClose?: () => void,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-context-menu", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            display: "none",
            minWidth: "180px",
            maxWidth: "240px",
            padding: "6px",
            borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(26, 26, 30, 0.96)",
            color: "#f4f4f5",
            boxShadow: "0 16px 40px rgba(0,0,0,0.35)",
            zIndex: "20",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "13px",
        });
        this.root.addEventListener("pointerdown", (event) => {
            event.stopPropagation();
        });
        this.host.appendChild(this.root);
    }

    open(
        target: ContextMenuTarget,
        pageX: number,
        pageY: number,
        activeSelection?: ActiveSelectionPayload | null,
        lastMeasurement?: LastMeasurementSummary | null,
        savedSelections?: SavedSelectionSummary[] | null,
        regions?: RegionSummary[] | null,
    ): void {
        this.currentTarget = target;
        this.currentSelection = activeSelection ?? null;
        this.currentLastMeasurement = lastMeasurement ?? null;
        this.currentSavedSelections = Array.isArray(savedSelections) ? [...savedSelections] : [];
        this.currentRegions = Array.isArray(regions) ? [...regions] : [];
        this.currentPageX = pageX;
        this.currentPageY = pageY;
        this.root.replaceChildren();

        const header = document.createElement("div");
        header.setAttribute("data-molsysviewer-context-menu-title", "true");
        header.textContent = targetTitle(target);
        Object.assign(header.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.root.appendChild(header);

        if (target.kind === "structure") {
            this.root.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            this.root.appendChild(this.makeActionButton("Distance", "distance"));
            this.root.appendChild(this.makeActionButton("Angle", "angle"));
            this.root.appendChild(this.makeActionButton("Dihedral", "dihedral"));
        } else if (target.kind === "shape") {
            this.root.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            if (target.tag?.trim()) {
                this.root.appendChild(this.makeActionButton("Delete Shape", "delete_shape"));
            }
        } else if (target.kind === "annotation") {
            this.root.appendChild(this.makeActionButton("Focus Target", "focus_target"));
            if (target.tag?.trim()) {
                this.root.appendChild(this.makeActionButton("Delete Annotation", "delete_annotation"));
            }
        } else {
            const note = document.createElement("div");
            note.textContent = "No target under cursor";
            Object.assign(note.style, {
                padding: "8px",
                opacity: "0.8",
            });
            this.root.appendChild(note);
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
            if (this.currentSelection.count_groups === 1) {
                section.appendChild(this.makeActionButton("Add Label from Selection", "add_label_from_selection"));
            }
            section.appendChild(this.makeActionButton("Clear Selection", "clear_selection"));
            this.root.appendChild(section);
        }

        if (this.currentLastMeasurement) {
            const section = document.createElement("div");
            Object.assign(section.style, {
                marginTop: "8px",
                paddingTop: "8px",
                borderTop: "1px solid rgba(255,255,255,0.10)",
            });

            const title = document.createElement("div");
            title.textContent = `Last measurement: ${this.currentLastMeasurement.action} (${this.currentLastMeasurement.picked_count})`;
            Object.assign(title.style, {
                padding: "4px 8px 8px 8px",
                opacity: "0.82",
                fontSize: "12px",
            });
            section.appendChild(title);
            section.appendChild(this.makeActionButton("Persist Last Measurement", "persist_last_measurement"));
            this.root.appendChild(section);
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
            this.root.appendChild(section);
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
            this.root.appendChild(section);
        }

        const rect = this.host.getBoundingClientRect();
        this.root.style.display = "block";
        const menuWidth = this.root.offsetWidth || 180;
        const menuHeight = this.root.offsetHeight || 120;
        const left = Math.min(Math.max(0, pageX - rect.left), Math.max(0, rect.width - menuWidth));
        const top = Math.min(Math.max(0, pageY - rect.top), Math.max(0, rect.height - menuHeight));
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
        this.root.style.display = "none";
        this.detachOutsidePointerHandler();
        if (wasOpen) this.onClose?.();
    }

    dispose(): void {
        this.close();
        this.root.remove();
    }

    private makeActionButton(label: string, action: ContextMenuAction): HTMLButtonElement {
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
            if (action === "activate_selection") {
                return;
            }
            const details = this.resolveActionDetails(action);
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

    private makeRegionButton(region: RegionSummary): HTMLButtonElement {
        const suffix = region.hidden ? " · hidden" : "";
        const label = `${region.tag} · ${region.atom_count} atom${region.atom_count === 1 ? "" : "s"}${suffix}`;
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute("data-molsysviewer-region", region.tag);
        Object.assign(button.style, {
            display: "block",
            width: "100%",
            padding: "8px 10px",
            margin: "0",
            border: "0",
            borderRadius: "8px",
            background: "transparent",
            color: region.hidden ? "rgba(244,244,245,0.72)" : "inherit",
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
            const details = { tag: region.tag };
            this.onAction?.("focus_region", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "focus_region",
                context: this.currentTarget,
                ...details,
            });
            this.close();
        });
        return button;
    }

    private resolveActionDetails(action: ContextMenuAction): ContextActionDetails | null {
        if (action === "delete_annotation" || action === "delete_shape") {
            const tag =
                this.currentTarget?.kind === "annotation" || this.currentTarget?.kind === "shape"
                    ? this.currentTarget.tag
                    : undefined;
            if (!tag || tag.trim() === "") return null;
            return { tag };
        }
        return {};
    }

    private renderLabelComposer(): void {
        if (!this.currentTarget) return;
        this.root.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "Label from selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "8px",
        });
        this.root.appendChild(title);

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
        this.root.appendChild(input);

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
            const details = { text };
            this.onAction?.("add_label_from_selection", this.currentTarget, details);
            this.notify?.({
                event: "interaction_context_action",
                action: "add_label_from_selection",
                context: this.currentTarget,
                ...details,
            });
            this.close();
        };

        save.addEventListener("click", submit);
        cancel.addEventListener("click", () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
            );
        });
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") {
                event.preventDefault?.();
                submit();
            } else if (event?.key === "Escape") {
                event.preventDefault?.();
                if (!this.currentTarget) return;
                this.open(
                    this.currentTarget,
                    this.currentPageX,
                    this.currentPageY,
                    this.currentSelection,
                    this.currentLastMeasurement,
                );
            }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.root.appendChild(actions);
        input.focus?.();
    }

    private renderSelectionComposer(): void {
        if (!this.currentTarget) return;
        this.root.replaceChildren();

        const title = document.createElement("div");
        title.textContent = "Save Selection";
        Object.assign(title.style, {
            padding: "6px 8px 8px 8px",
            fontWeight: "600",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            marginBottom: "6px",
        });
        this.root.appendChild(title);

        const subtitle = document.createElement("div");
        subtitle.textContent = selectionSummary(this.currentSelection);
        Object.assign(subtitle.style, {
            padding: "0 8px 8px 8px",
            opacity: "0.82",
            fontSize: "12px",
        });
        this.root.appendChild(subtitle);

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
        this.root.appendChild(input);

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

        save.addEventListener("click", submit);
        cancel.addEventListener("click", () => {
            if (!this.currentTarget) return;
            this.open(
                this.currentTarget,
                this.currentPageX,
                this.currentPageY,
                this.currentSelection,
                this.currentLastMeasurement,
            );
        });
        input.addEventListener("keydown", (event: any) => {
            if (event?.key === "Enter") {
                event.preventDefault?.();
                submit();
            } else if (event?.key === "Escape") {
                event.preventDefault?.();
                if (!this.currentTarget) return;
                this.open(
                    this.currentTarget,
                    this.currentPageX,
                    this.currentPageY,
                    this.currentSelection,
                    this.currentLastMeasurement,
                );
            }
        });

        actions.appendChild(save);
        actions.appendChild(cancel);
        this.root.appendChild(actions);
        input.focus?.();
    }

    private detachOutsidePointerHandler(): void {
        if (!this.outsidePointerHandler) return;
        window.removeEventListener("pointerdown", this.outsidePointerHandler, true);
        this.outsidePointerHandler = undefined;
    }
}
