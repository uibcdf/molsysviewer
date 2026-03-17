import { StructureElement, Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnInteraction = (item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;

function selectionKey(item: ActiveSelectionItem): string {
    const molPart = item.molecule_indices?.join(",") ?? "0";
    const compPart = item.component_indices?.join(",") ?? "0";
    const chainPart = item.chain_indices?.join(",") ?? "0";
    const groupPart = item.group_indices?.join(",") ?? "0";
    
    if (item.source_kind === "annotation") {
        return `${molPart}:${compPart}:${chainPart}:${groupPart}:annotation:${item.tag ?? ""}`;
    }
    return `${molPart}:${compPart}:${chainPart}:${groupPart}`;
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
        private readonly onInteraction: OnInteraction,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-group-strip", "true");
        Object.assign(this.root.style, {
            minWidth: "120px",
            maxWidth: "150px",
            height: "100%",
            overflowY: "hidden",
            overflowX: "hidden",
            display: "flex",
            flex: "0 0 auto",
            paddingRight: "4px",
        });

        this.section = document.createElement("div");
        Object.assign(this.section.style, {
            marginBottom: "10px",
            display: "flex",
            flexDirection: "column",
            minHeight: "0",
            height: "100%",
            width: "100%",
        });

        this.title = document.createElement("div");
        this.title.setAttribute("data-molsysviewer-group-strip-title", this.chainLabel);
        Object.assign(this.title.style, {
            fontWeight: "700",
            marginBottom: "6px",
            opacity: "0.9",
        });
        this.title.textContent = `Chain ${this.chainLabel}`;

        this.row = document.createElement("div");
        Object.assign(this.row.style, {
            display: "flex",
            flexDirection: "column",
            flexWrap: "nowrap",
            gap: "6px",
            overflowY: "auto",
            overflowX: "hidden",
            minHeight: "0",
            flex: "1 1 auto",
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

        // Group items hierarchically: Molecule -> Component -> Residues
        const hierarchy = new Map<number, Map<number, ActiveSelectionItem[]>>();
        const moleculeNames = new Map<number, string>();
        const componentNames = new Map<number, string>();

        for (const item of this.groupItems) {
            const molId = item.molecule_indices[0] ?? 0;
            const compId = item.component_indices[0] ?? 0;
            if (!hierarchy.has(molId)) hierarchy.set(molId, new Map());
            if (!hierarchy.get(molId)!.has(compId)) hierarchy.get(molId)!.set(compId, []);
            hierarchy.get(molId)!.get(compId)!.push(item);
            if (item.molecule_name) moleculeNames.set(molId, item.molecule_name);
            if (item.component_name) componentNames.set(compId, item.component_name);
        }

        const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

        for (const [molId, components] of hierarchy.entries()) {
            const molBox = document.createElement("div");
            const molColor = COLORS[molId % COLORS.length];
            Object.assign(molBox.style, {
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                paddingLeft: "8px",
                marginLeft: "2px",
                borderLeft: `3px solid ${molColor}44`, // Molecule border (semi-transparent)
                borderRadius: "4px 0 0 4px",
                marginBottom: "8px",
                position: "relative",
            });
            molBox.title = `Molecule: ${moleculeNames.get(molId) ?? molId}`;

            // Add invisible clickable area for molecule selection
            const molHandle = document.createElement("div");
            Object.assign(molHandle.style, {
                position: "absolute",
                left: "-10px",
                top: "0",
                bottom: "0",
                width: "14px",
                cursor: "pointer",
                zIndex: "2",
            });
            molHandle.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                const mouseEvent = event as MouseEvent;
                const allItems = Array.from(components.values()).flat();
                if (allItems.length > 0) {
                    this.onInteraction(allItems[0], { shift: mouseEvent.shiftKey, alt: mouseEvent.altKey });
                    if (allItems.length > 1) {
                        this.onSelect(allItems, true);
                    }
                }
            });
            molBox.appendChild(molHandle);

            for (const [compId, items] of components.entries()) {
                const compBox = document.createElement("div");
                const compColor = COLORS[compId % COLORS.length];
                Object.assign(compBox.style, {
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    paddingLeft: "8px",
                    marginLeft: "2px",
                    borderLeft: `2px solid ${compColor}aa`, // Component border (more opaque)
                    borderRadius: "2px 0 0 2px",
                    position: "relative",
                });
                compBox.title = `Component: ${componentNames.get(compId) ?? compId}`;

                // Add invisible clickable area for component selection
                const compHandle = document.createElement("div");
                Object.assign(compHandle.style, {
                    position: "absolute",
                    left: "-8px",
                    top: "0",
                    bottom: "0",
                    width: "10px",
                    cursor: "pointer",
                    zIndex: "3",
                });
                compHandle.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const mouseEvent = event as MouseEvent;
                    if (items.length > 0) {
                        this.onInteraction(items[0], { shift: mouseEvent.shiftKey, alt: mouseEvent.altKey });
                        if (items.length > 1) {
                            this.onSelect(items, true);
                        }
                    }
                });
                compBox.appendChild(compHandle);

                for (const item of items) {
                    const key = selectionKey(item);
                    const button = document.createElement("button");
                    button.type = "button";
                    button.setAttribute("data-molsysviewer-group-item", "true");
                    button.setAttribute("data-chain-name", item.chain_name ?? "");
                    button.setAttribute("data-group-name", item.group_name ?? "");
                    const selected = this.selectedElementKeys.has(key);
                    Object.assign(button.style, {
                        padding: "4px 8px",
                        borderRadius: "999px",
                        border: selected ? "1px solid rgba(255,255,255,0.38)" : "1px solid rgba(255,255,255,0.12)",
                        background: selected ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.06)",
                        color: "inherit",
                        cursor: "pointer",
                        whiteSpace: "nowrap",
                        font: "inherit",
                        width: "100%",
                        textAlign: "left",
                        fontSize: "11px",
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
                                component_indices: item.component_indices,
                                chain_indices: item.chain_indices,
                                molecule_indices: item.molecule_indices,
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
                        const mouseEvent = event as MouseEvent;
                        this.onInteraction(item, { shift: mouseEvent.shiftKey, alt: mouseEvent.altKey });
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
                    compBox.appendChild(button);
                }
                molBox.appendChild(compBox);
            }
            this.row.appendChild(molBox);
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
