import { StructureElement, Structure, Unit } from "molstar/lib/mol-model/structure";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";

import { ActiveSelectionItem, ActiveSelectionPayload, GroupSelectionItem } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import { ResidueToClass, PhysicochemicalColorsHex } from "../themes/physicochemical-color";
import { getPerAtomColor } from "../themes/per-atom-color";

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
    const target = new Set(item.atom_indices);
    const lociElements: { unit: Unit.Atomic; indices: any }[] = [];
    for (const unit of structure.units) {
        if (!Unit.isAtomic(unit)) continue;
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        const matched: number[] = [];
        for (let i = 0; i < count; i++) {
            if (target.has(OrderedSet.getAt(elements, i))) matched.push(i);
        }
        if (matched.length > 0) {
            lociElements.push({ unit, indices: SortedArray.ofSortedArray(matched) });
        }
    }
    if (lociElements.length === 0) return null;
    return StructureElement.Loci(structure, lociElements as any);
}

function buildHierarchyCaption(kind: "molecule" | "component", index: number, name?: string): string {
    const prefix = kind === "molecule" ? "M" : "C";
    const cleanName = typeof name === "string" ? name.trim() : "";
    if (cleanName.length === 0) return `${prefix}${index}`;
    return `${prefix} ${cleanName}`;
}

export class GroupStrip {
    private readonly root: HTMLDivElement;
    private readonly section: HTMLDivElement;
    private readonly title: HTMLDivElement;
    private readonly row: HTMLDivElement;
    private groupItems: GroupSelectionItem[] = [];
    private selectedElementKeys = new Set<string>();
    private selectedAnnotationKeys = new Set<string>();
    private structure?: Structure;
    private readonly annotationRecords = new Map<string, Array<{ tag: string; text: string }>>();
    private readonly collapsedMolecules = new Set<number>();
    private readonly collapsedComponents = new Set<string>();
    private currentContextTarget: ContextMenuTarget | null = null;
    private activeColorScheme: "neutral" | "physicochemical" = "neutral";

    setColorScheme(scheme: "neutral" | "physicochemical"): void {
        if (this.activeColorScheme !== scheme) {
            this.activeColorScheme = scheme;
            this.render();
        }
    }

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
            minHeight: "0",
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
        this.row.setAttribute("data-molsysviewer-group-strip-row", "true");
        Object.assign(this.row.style, {
            display: "flex",
            flexDirection: "column",
            flexWrap: "nowrap",
            gap: "6px",
            overflowY: "auto",
            overflowX: "hidden",
            minHeight: "0",
            flex: "1 1 auto",
            scrollbarWidth: "thin",
            scrollbarColor: "rgba(255, 255, 255, 0.15) transparent",
        });

        this.section.appendChild(this.title);
        this.section.appendChild(this.row);
        this.root.appendChild(this.section);
        this.host.appendChild(this.root);
    }

    setData(structure: Structure | undefined, items: GroupSelectionItem[]): void {
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
        const selectionChanged = nextElements.size !== this.selectedElementKeys.size
            || [...nextElements].some((k) => !this.selectedElementKeys.has(k));
        this.selectedElementKeys = nextElements;
        this.selectedAnnotationKeys = nextAnnotations;
        this.render();
        if (selectionChanged && nextElements.size > 0) {
            const btn = this.row.querySelector?.("[data-group-item-selected]") as HTMLElement | null;
            btn?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
        }
    }

    updateContextTarget(target: ContextMenuTarget | null): void {
        this.currentContextTarget = target;
        this.render();
    }

    getCollapseState(): { molecules: number[]; components: string[] } {
        return {
            molecules: Array.from(this.collapsedMolecules.values()).sort((a, b) => a - b),
            components: Array.from(this.collapsedComponents.values()).sort(),
        };
    }

    setCollapseState(state?: { molecules?: number[]; components?: string[] } | null): void {
        this.collapsedMolecules.clear();
        this.collapsedComponents.clear();
        for (const molecule of state?.molecules ?? []) {
            if (typeof molecule === "number") this.collapsedMolecules.add(molecule);
        }
        for (const component of state?.components ?? []) {
            if (typeof component === "string") this.collapsedComponents.add(component);
        }
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
        const hierarchy = new Map<number, Map<number, GroupSelectionItem[]>>();
        const moleculeNames = new Map<number, string>();
        const componentNames = new Map<number, string>();

        for (const item of this.groupItems) {
            const moleculeIndices = Array.isArray(item.molecule_indices) ? item.molecule_indices : [];
            const componentIndices = Array.isArray(item.component_indices) ? item.component_indices : [];
            const molId = moleculeIndices[0] ?? 0;
            const compId = componentIndices[0] ?? 0;
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
            const moleculeCollapsed = this.collapsedMolecules.has(molId);
            Object.assign(molBox.style, {
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                paddingLeft: "8px",
                marginLeft: "2px",
                borderLeft: `3px solid ${molColor}88`,
                borderRadius: "4px 0 0 4px",
                marginBottom: "8px",
                position: "relative",
            });
            molBox.title = `Molecule: ${moleculeNames.get(molId) ?? molId}`;

            const molCaption = document.createElement("div");
            molCaption.setAttribute("data-molsysviewer-group-strip-molecule-caption", String(molId));
            molCaption.textContent = `${moleculeCollapsed ? "▶" : "▼"} ${buildHierarchyCaption("molecule", molId, moleculeNames.get(molId))}`;
            Object.assign(molCaption.style, {
                alignSelf: "flex-start",
                marginLeft: "2px",
                marginBottom: "2px",
                padding: "2px 7px",
                borderRadius: "999px",
                background: `${molColor}28`,
                color: molColor,
                fontSize: "10px",
                fontWeight: "700",
                letterSpacing: "0.03em",
                textTransform: "uppercase",
                maxWidth: "100%",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                cursor: "pointer",
            });
            molCaption.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                if (this.collapsedMolecules.has(molId)) {
                    this.collapsedMolecules.delete(molId);
                } else {
                    this.collapsedMolecules.add(molId);
                }
                this.render();
            });
            molBox.appendChild(molCaption);

            // Add invisible clickable area for molecule selection
            const molHandle = document.createElement("div");
            molHandle.setAttribute("data-molsysviewer-group-strip-molecule-handle", String(molId));
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

            if (moleculeCollapsed) {
                this.row.appendChild(molBox);
                continue;
            }

            for (const [compId, items] of components.entries()) {
                const compBox = document.createElement("div");
                const componentKey = `${molId}:${compId}`;
                const componentCollapsed = this.collapsedComponents.has(componentKey);
                Object.assign(compBox.style, {
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    paddingLeft: "8px",
                    marginLeft: "2px",
                    borderLeft: "1.5px solid rgba(255,255,255,0.22)",
                    borderRadius: "2px 0 0 2px",
                    position: "relative",
                });
                compBox.title = `Component: ${componentNames.get(compId) ?? compId}`;

                const compCaption = document.createElement("div");
                compCaption.setAttribute("data-molsysviewer-group-strip-component-caption", String(compId));
                compCaption.textContent = `${componentCollapsed ? "▶" : "▼"} ${buildHierarchyCaption("component", compId, componentNames.get(compId))}`;
                Object.assign(compCaption.style, {
                    alignSelf: "flex-start",
                    marginLeft: "2px",
                    marginBottom: "2px",
                    padding: "1px 5px",
                    borderRadius: "999px",
                    background: "rgba(255,255,255,0.08)",
                    color: "rgba(244,244,245,0.72)",
                    fontSize: "9px",
                    fontWeight: "600",
                    letterSpacing: "0.03em",
                    textTransform: "uppercase",
                    maxWidth: "100%",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    cursor: "pointer",
                });
                compCaption.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    if (this.collapsedComponents.has(componentKey)) {
                        this.collapsedComponents.delete(componentKey);
                    } else {
                        this.collapsedComponents.add(componentKey);
                    }
                    this.render();
                });
                compBox.appendChild(compCaption);

                // Add invisible clickable area for component selection
                const compHandle = document.createElement("div");
                compHandle.setAttribute("data-molsysviewer-group-strip-component-handle", String(compId));
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

                if (componentCollapsed) {
                    molBox.appendChild(compBox);
                    continue;
                }

                for (const item of items) {
                    const key = selectionKey(item);
                    const button = document.createElement("button");
                    button.type = "button";
                    button.setAttribute("data-molsysviewer-group-item", "true");
                    button.setAttribute("data-chain-name", item.chain_name ?? "");
                    button.setAttribute("data-group-name", item.group_name ?? "");
                    const selected = this.selectedElementKeys.has(key);
                    const contextSelected =
                        this.currentContextTarget?.kind === "structure"
                        && Array.isArray(this.currentContextTarget.atom_indices)
                        && this.findSelectionKeyFromAtomIndices(this.currentContextTarget.atom_indices) === key;
                    const firstAtomIndex = item.atom_indices[0];
                    const customColorInt = firstAtomIndex !== undefined ? getPerAtomColor(firstAtomIndex) : undefined;
                    let colorHex: string | null = null;
                    if (customColorInt !== undefined) {
                        colorHex = "#" + customColorInt.toString(16).padStart(6, "0");
                    } else if (this.activeColorScheme === "physicochemical") {
                        const groupNameUpper = (item.group_name ?? "").toUpperCase();
                        const residueClass = ResidueToClass[groupNameUpper];
                        if (residueClass) {
                            colorHex = PhysicochemicalColorsHex[residueClass];
                        }
                    }

                    Object.assign(button.style, {
                        padding: "4px 8px",
                        borderRadius: "999px",
                        border: selected
                            ? (colorHex ? `1px solid ${colorHex}` : "1px solid rgba(255,255,255,0.38)")
                            : contextSelected
                                ? "1px solid rgba(251, 191, 36, 0.48)"
                                : (colorHex ? `1px solid ${colorHex}50` : "1px solid rgba(255,255,255,0.12)"),
                        background: selected
                            ? (colorHex ? `${colorHex}55` : "rgba(255,255,255,0.18)")
                            : contextSelected
                                ? "rgba(251, 191, 36, 0.12)"
                                : (colorHex ? `${colorHex}22` : "rgba(255,255,255,0.06)"),
                        boxShadow: contextSelected ? "inset 0 0 0 1px rgba(251, 191, 36, 0.18)" : "none",
                        color: "inherit",
                        cursor: "pointer",
                        whiteSpace: "nowrap",
                        font: "inherit",
                        width: "100%",
                        textAlign: "left",
                        fontSize: "11px",
                    });
                    if (selected) button.setAttribute("data-group-item-selected", "true");
                    const text = document.createElement("span");
                    text.textContent = item.group_name ?? `${item.group_indices[0] ?? "?"}`;
                    button.appendChild(text);

                    const annotationRecords = this.annotationRecords.get(key) ?? [];
                    if (annotationRecords.length > 0) {
                        const badge = document.createElement("span");
                        const primary = annotationRecords[0];
                        const annotationSelected = this.selectedAnnotationKeys.has(`${key}:annotation:${primary.tag ?? ""}`);
                        const annotationContextSelected =
                            this.currentContextTarget?.kind === "annotation"
                            && this.currentContextTarget.tag === primary.tag;
                        badge.textContent = annotationRecords.length > 1 ? ` ${annotationRecords.length}L` : " L";
                        Object.assign(badge.style, {
                            marginLeft: "6px",
                            padding: "1px 6px",
                            borderRadius: "999px",
                            background: annotationSelected
                                ? "rgba(250, 204, 21, 0.22)"
                                : annotationContextSelected
                                    ? "rgba(251, 191, 36, 0.16)"
                                    : "rgba(110, 231, 183, 0.18)",
                            color: annotationSelected
                                ? "#fde68a"
                                : annotationContextSelected
                                    ? "#fcd34d"
                                    : "#b7f7dd",
                            fontSize: "10px",
                            fontWeight: "700",
                            boxShadow: annotationContextSelected ? "inset 0 0 0 1px rgba(251, 191, 36, 0.28)" : "none",
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
