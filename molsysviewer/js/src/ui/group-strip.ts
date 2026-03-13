import { StructureElement, Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;

function selectionKey(item: ActiveSelectionItem): string {
    if (item.source_kind === "annotation") {
        return `${item.chain_indices.join(",")}:${item.group_indices.join(",")}:annotation:${item.tag ?? ""}`;
    }
    return `${item.chain_indices.join(",")}:${item.group_indices.join(",")}`;
}

function makeLociForItem(structure: Structure, item: ActiveSelectionItem): StructureElement.Loci | null {
    const unit = structure.units.find((candidate) => candidate.kind === 0);
    if (!unit) return null;
    const indices: number[] = [];
    const unitElements = unit.elements;
    for (const atomIndex of item.atom_indices) {
        const unitIndex = unitElements.indexOf(atomIndex as any);
        if (unitIndex >= 0) indices.push(unitIndex);
    }
    if (indices.length === 0) return null;
    return StructureElement.Loci(structure, [{ unit, indices } as any]);
}

export class GroupStrip {
    private readonly root: HTMLDivElement;
    private readonly section: HTMLDivElement;
    private readonly title: HTMLDivElement;
    private readonly row: HTMLDivElement;
    private groupItems: ActiveSelectionItem[] = [];
    private selectedElementKeys = new Set<string>();
    private selectedAnnotationKeys = new Set<string>();
    private structure?: Structure;
    private readonly annotationRecords = new Map<string, Array<{ tag: string; text: string }>>();

    constructor(
        private readonly host: HTMLElement,
        private readonly chainLabel: string,
        private readonly onSelect: OnSelect,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-group-strip", "true");
        Object.assign(this.root.style, {
            minWidth: "0",
            display: "block",
        });

        this.section = document.createElement("div");
        this.section.style.marginBottom = "10px";

        this.title = document.createElement("div");
        Object.assign(this.title.style, {
            fontWeight: "700",
            marginBottom: "6px",
            opacity: "0.9",
        });
        this.title.textContent = `Chain ${this.chainLabel}`;

        this.row = document.createElement("div");
        Object.assign(this.row.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "6px",
        });

        this.section.appendChild(this.title);
        this.section.appendChild(this.row);
        this.root.appendChild(this.section);
        this.host.appendChild(this.root);
    }

    setData(structure: Structure | undefined, items: ActiveSelectionItem[]): void {
        this.structure = structure;
        this.groupItems = items;
        if (!structure) this.annotationRecords.clear();
        this.render();
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        const nextElements = new Set<string>();
        const nextAnnotations = new Set<string>();
        for (const item of selection.items ?? []) {
            if (item?.source_kind === "element" && item?.element_level === "group") {
                nextElements.add(selectionKey(item));
            } else if (item?.source_kind === "annotation" && item?.annotation_kind === "label") {
                nextAnnotations.add(selectionKey(item));
            }
        }
        this.selectedElementKeys = nextElements;
        this.selectedAnnotationKeys = nextAnnotations;
        this.render();
    }

    addLabelOverlay(msg: AddLabelMessage): void {
        const text = typeof msg.options?.text === "string" ? msg.options.text.trim() : "";
        const atomIndices = Array.isArray(msg.options?.atom_indices) ? msg.options.atom_indices : [];
        const tag = msg.tag ?? msg.options?.tag ?? "annotation";
        if (!text || atomIndices.length === 0 || this.groupItems.length === 0) return;

        const key = this.findSelectionKeyFromAtomIndices(atomIndices);
        if (!key) return;
        const records = this.annotationRecords.get(key) ?? [];
        records.push({ tag, text });
        this.annotationRecords.set(key, records);
        this.render();
    }

    clearAnnotationOverlays(): void {
        if (this.annotationRecords.size === 0) return;
        this.annotationRecords.clear();
        this.render();
    }

    clearAnnotationOverlaysByTag(tag?: string): void {
        if (!tag) {
            this.clearAnnotationOverlays();
            return;
        }
        let changed = false;
        for (const [key, records] of this.annotationRecords.entries()) {
            const next = records.filter((record) => record.tag !== tag);
            if (next.length === records.length) continue;
            changed = true;
            if (next.length === 0) {
                this.annotationRecords.delete(key);
            } else {
                this.annotationRecords.set(key, next);
            }
        }
        if (changed) this.render();
    }

    retagAnnotationOverlays(oldTag: string, newTag: string): void {
        let changed = false;
        for (const [key, records] of this.annotationRecords.entries()) {
            const next = records.map((record) => {
                if (record.tag !== oldTag) return record;
                changed = true;
                return { ...record, tag: newTag };
            });
            this.annotationRecords.set(key, next);
        }
        if (changed) this.render();
    }

    focusItem(item: ActiveSelectionItem): StructureElement.Loci | null {
        if (!this.structure) return null;
        return makeLociForItem(this.structure, item);
    }

    dispose(): void {
        this.root.remove();
    }

    private render(): void {
        this.row.replaceChildren();
        this.root.style.display = !this.structure || this.groupItems.length === 0 ? "none" : "block";
        if (!this.structure || this.groupItems.length === 0) return;

        for (const item of this.groupItems) {
            const key = selectionKey(item);
            const button = document.createElement("button");
            button.type = "button";
            button.setAttribute("data-molsysviewer-group-item", "true");
            button.setAttribute("data-chain-name", item.chain_name ?? "");
            button.setAttribute("data-group-name", item.group_name ?? "");
            const selected = this.selectedElementKeys.has(key);
            Object.assign(button.style, {
                padding: "6px 8px",
                borderRadius: "999px",
                border: selected ? "1px solid rgba(255,255,255,0.38)" : "1px solid rgba(255,255,255,0.12)",
                background: selected ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.06)",
                color: "inherit",
                cursor: "pointer",
                whiteSpace: "nowrap",
                font: "inherit",
            });
            const text = document.createElement("span");
            text.textContent = item.group_name ?? `${item.group_indices[0] ?? "?"}`;
            button.appendChild(text);

            const annotationRecords = this.annotationRecords.get(key) ?? [];
            if (annotationRecords.length > 0) {
                const badge = document.createElement("span");
                const primary = annotationRecords[0];
                const annotationSelected = this.selectedAnnotationKeys.has(`${key}:annotation:${primary.tag ?? ""}`);
                badge.textContent = annotationRecords.length > 1 ? ` ${annotationRecords.length}L` : " L";
                Object.assign(badge.style, {
                    marginLeft: "6px",
                    padding: "1px 6px",
                    borderRadius: "999px",
                    background: annotationSelected ? "rgba(250, 204, 21, 0.22)" : "rgba(110, 231, 183, 0.18)",
                    color: annotationSelected ? "#fde68a" : "#b7f7dd",
                    fontSize: "10px",
                    fontWeight: "700",
                });
                button.appendChild(badge);
                button.title = annotationRecords.map((record) => record.text).join("\n");
                badge.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    this.onSelect([{
                        source_kind: "annotation",
                        annotation_kind: "label",
                        atom_indices: item.atom_indices,
                        group_indices: item.group_indices,
                        chain_indices: item.chain_indices,
                        entity_indices: item.entity_indices,
                        tag: primary.tag,
                        text: primary.text,
                    }], !!(event as MouseEvent).shiftKey);
                });
                badge.addEventListener("contextmenu", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    this.onAnnotationContext(
                        {
                            event: "interaction_context_menu",
                            kind: "annotation",
                            atom_indices: item.atom_indices,
                            tag: primary.tag,
                            text: primary.text,
                        },
                        (event as MouseEvent).pageX,
                        (event as MouseEvent).pageY,
                    );
                });
            }
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.onSelect([item], !!(event as MouseEvent).shiftKey);
            });
            button.addEventListener("dblclick", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.onFocus(item);
            });
            button.addEventListener("mouseenter", () => {
                this.onHover(item);
            });
            button.addEventListener("mouseleave", () => {
                this.onHover(null);
            });
            button.addEventListener("contextmenu", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.onContext(item, (event as MouseEvent).pageX, (event as MouseEvent).pageY);
            });
            this.row.appendChild(button);
        }
    }

    private findSelectionKeyFromAtomIndices(atomIndices: number[]): string | null {
        const input = [...atomIndices].sort((a, b) => a - b);
        for (const item of this.groupItems) {
            if (item.atom_indices.length !== input.length) continue;
            const own = [...item.atom_indices].sort((a, b) => a - b);
            let same = true;
            for (let i = 0; i < own.length; i++) {
                if (own[i] !== input[i]) {
                    same = false;
                    break;
                }
            }
            if (same) return selectionKey(item);
        }
        return null;
    }
}
