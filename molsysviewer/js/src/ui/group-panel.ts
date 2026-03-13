import { Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, buildGroupItemsFromStructure } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import { GroupStrip } from "./group-strip";

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;

export class GroupPanel {
    private readonly root: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly body: HTMLDivElement;
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

    constructor(
        private readonly host: HTMLElement,
        private readonly onSelect: OnSelect,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-group-panel", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            left: "0",
            top: "14px",
            bottom: "14px",
            display: "none",
            alignItems: "stretch",
            pointerEvents: "none",
            zIndex: "16",
        });

        this.toggleButton = document.createElement("button");
        this.toggleButton.type = "button";
        this.toggleButton.setAttribute("data-molsysviewer-group-panel-toggle", "true");
        Object.assign(this.toggleButton.style, {
            pointerEvents: "auto",
            alignSelf: "center",
            marginLeft: "0",
            width: "26px",
            height: "54px",
            border: "1px solid rgba(255,255,255,0.16)",
            borderLeft: "0",
            borderRadius: "0 10px 10px 0",
            background: "rgba(18, 18, 22, 0.94)",
            color: "#f4f4f5",
            boxShadow: "0 10px 24px rgba(0,0,0,0.24)",
            cursor: "pointer",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "16px",
            fontWeight: "700",
        });
        this.toggleButton.textContent = ">";
        this.toggleButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.expanded = !this.expanded;
            this.applyExpandedState();
        });

        this.body = document.createElement("div");
        this.body.setAttribute("data-molsysviewer-group-panel-body", "true");
        Object.assign(this.body.style, {
            pointerEvents: "auto",
            display: "flex",
            alignItems: "stretch",
            gap: "10px",
            flexDirection: "row",
            flexWrap: "nowrap",
            width: "240px",
            maxWidth: "240px",
            height: "100%",
            overflowX: "auto",
            overflowY: "hidden",
            padding: "10px",
            borderRadius: "0 14px 14px 0",
            border: "1px solid rgba(255,255,255,0.14)",
            borderLeft: "0",
            background: "rgba(18, 18, 22, 0.92)",
            color: "#f4f4f5",
            boxShadow: "0 12px 32px rgba(0,0,0,0.28)",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "12px",
            transform: "translateX(-100%)",
            transition: "transform 160ms ease",
        });

        this.root.appendChild(this.body);
        this.root.appendChild(this.toggleButton);
        this.host.appendChild(this.root);
    }

    setStructure(structure: Structure | undefined): void {
        this.structure = structure;
        if (!structure) this.annotationMessages.length = 0;
        this.render();
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        for (const strip of this.strips.values()) {
            strip.updateSelection(selection);
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
        const chainName = item.chain_name ?? "?";
        return this.strips.get(chainName)?.focusItem(item) ?? null;
    }

    dispose(): void {
        for (const strip of this.strips.values()) strip.dispose();
        this.strips.clear();
        this.root.remove();
    }

    private applyExpandedState(): void {
        this.toggleButton.textContent = this.expanded ? "<" : ">";
        this.body.style.transform = this.expanded ? "translateX(0)" : "translateX(-100%)";
    }

    private render(): void {
        const grouped = new Map<string, ActiveSelectionItem[]>();
        const items = this.structure ? buildGroupItemsFromStructure(this.structure) : [];
        for (const item of items) {
            const chain = item.chain_name ?? "?";
            if (!grouped.has(chain)) grouped.set(chain, []);
            grouped.get(chain)!.push(item);
        }

        const nextChains = new Set(grouped.keys());
        for (const [chain, strip] of this.strips.entries()) {
            if (nextChains.has(chain)) continue;
            strip.dispose();
            this.strips.delete(chain);
        }

        this.root.style.display = this.structure && grouped.size > 0 ? "flex" : "none";
        if (!this.structure || grouped.size === 0) return;

        for (const [chain, chainItems] of grouped.entries()) {
            let strip = this.strips.get(chain);
            if (!strip) {
                strip = new GroupStrip(this.body, chain, this.onSelect, this.onFocus, this.onHover, this.onContext, this.onAnnotationContext);
                this.strips.set(chain, strip);
            }
            strip.setData(this.structure, chainItems);
            strip.updateSelection(this.currentSelection);
            strip.clearAnnotationOverlays();
            for (const message of this.annotationMessages) {
                strip.addLabelOverlay(message);
            }
        }
        this.applyExpandedState();
    }
}
