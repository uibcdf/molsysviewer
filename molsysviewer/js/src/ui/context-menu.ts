import type { ActiveSelectionPayload } from "../managers/active-selection";

type BaseTarget =
    | { event: "interaction_context_menu"; kind: "empty" }
    | { event: "interaction_context_menu"; kind: "structure"; atom_indices: number[] }
    | { event: "interaction_context_menu"; kind: "annotation"; atom_indices: number[]; tag?: string; text?: string };

export type ContextMenuTarget = BaseTarget;

export type ContextMenuAction = "distance" | "angle" | "dihedral" | "focus_target" | "focus_selection" | "clear_selection";

function targetTitle(target: ContextMenuTarget): string {
    if (target.kind === "empty") return "Canvas";
    if (target.kind === "annotation") return target.text?.trim() || target.tag?.trim() || "Annotation";
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

export class ViewerContextMenu {
    private readonly root: HTMLDivElement;
    private outsidePointerHandler?: (event: PointerEvent) => void;
    private currentTarget: ContextMenuTarget | null = null;
    private currentSelection: ActiveSelectionPayload | null = null;

    constructor(
        private readonly host: HTMLElement,
        private readonly notify?: (msg: any) => void,
        private readonly onAction?: (action: ContextMenuAction, target: ContextMenuTarget) => void,
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

    open(target: ContextMenuTarget, pageX: number, pageY: number, activeSelection?: ActiveSelectionPayload | null): void {
        this.currentTarget = target;
        this.currentSelection = activeSelection ?? null;
        this.root.replaceChildren();

        const header = document.createElement("div");
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
        } else if (target.kind === "annotation") {
            this.root.appendChild(this.makeActionButton("Focus Target", "focus_target"));
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
            section.appendChild(this.makeActionButton("Clear Selection", "clear_selection"));
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
        this.currentTarget = null;
        this.currentSelection = null;
        this.root.style.display = "none";
        this.detachOutsidePointerHandler();
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
            this.onAction?.(action, this.currentTarget);
            this.notify?.({
                event: "interaction_context_action",
                action,
                context: this.currentTarget,
            });
            this.close();
        });
        return button;
    }

    private detachOutsidePointerHandler(): void {
        if (!this.outsidePointerHandler) return;
        window.removeEventListener("pointerdown", this.outsidePointerHandler, true);
        this.outsidePointerHandler = undefined;
    }
}
