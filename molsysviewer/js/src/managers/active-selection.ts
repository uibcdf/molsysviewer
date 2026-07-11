import { Structure } from "molstar/lib/mol-model/structure";
import { StructureElement } from "molstar/lib/mol-model/structure";
import { Loci } from "molstar/lib/mol-model/loci";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Shape, ShapeGroup } from "molstar/lib/mol-model/shape";

export type ActiveSelectionItem = {
    source_kind: "element";
    element_level: "group";
    atom_indices: number[];
    group_indices: number[];
    component_indices?: number[];
    chain_indices: number[];
    molecule_indices?: number[];
    entity_indices: number[];
    group_name?: string;
    group_id?: number | string;
    component_name?: string;
    chain_name?: string;
    molecule_name?: string;
    entity_name?: string;
} | {
    source_kind: "annotation";
    annotation_kind: "label";
    atom_indices: number[];
    group_indices: number[];
    component_indices?: number[];
    chain_indices: number[];
    molecule_indices?: number[];
    entity_indices: number[];
    tag?: string;
    text?: string;
} | {
    source_kind: "shape";
    shape_kind: string;
    shape_name?: string;
    tag?: string;
    atom_indices: number[];
    group_indices: number[];
    component_indices?: number[];
    chain_indices: number[];
    molecule_indices?: number[];
    entity_indices: number[];
    entity_ref?: unknown;
};

/**
 * The `"element"` variant of {@link ActiveSelectionItem}. The group strip/panel
 * builders only ever produce element items, so the `*_name` fields are
 * legitimately accessible on their results.
 */
export type GroupSelectionItem = Extract<ActiveSelectionItem, { source_kind: "element" }>;

export type ActiveSelectionPayload = {
    event: "interaction_active_selection_changed";
    source_kind: "empty" | "element" | "annotation" | "shape" | "mixed";
    target_level: "none" | "annotation" | "shape" | "mixed";
    element_level: "none" | "group";
    items: ActiveSelectionItem[];
    atom_indices: number[];
    group_indices: number[];
    component_indices: number[];
    chain_indices: number[];
    molecule_indices: number[];
    entity_indices: number[];
    count_atoms: number;
    count_groups: number;
    count_shapes: number;
    count_annotations: number;
};

export type ActiveSelectionSetOperation = "replace" | "add" | "subtract" | "intersect";

export function buildGroupItemsFromStructure(structure: Structure): GroupSelectionItem[] {
    // Find the first atomic unit to access the shared model/hierarchy.
    const firstAtomicUnit = structure.units.find((unit) => unit.kind === 0);
    if (!firstAtomicUnit) return [];

    const model = firstAtomicUnit.model;
    const hierarchy = model.atomicHierarchy;
    let atomSite: any = undefined;

    if (model?.sourceData?.kind === "mmCIF") {
        atomSite = (model.sourceData.data as any).db?.atom_site;
    } else if (model?.sourceData?.kind === "mol-viewer:molsysmt") {
        atomSite = model.sourceData.data;
    }

    const residueOffsets = hierarchy.residueAtomSegments.offsets;
    const chainIndexByAtom = hierarchy.chainAtomSegments.index;
    const atoms = hierarchy.atoms;
    const residues = hierarchy.residues;
    const chains = hierarchy.chains;
    const modelIndex = hierarchy.index;
    const items: GroupSelectionItem[] = [];

    // Safe access to custom hierarchy columns
    const molIdCol = (atomSite as any)?.molsys_molecule_id || (atomSite as any)?.molecule_id;
    const molNameCol = (atomSite as any)?.molsys_molecule_name || (atomSite as any)?.molecule_name;
    const compIdCol = (atomSite as any)?.molsys_component_id || (atomSite as any)?.component_id;
    const compNameCol = (atomSite as any)?.molsys_component_name || (atomSite as any)?.component_name;

    // Collect the set of atom indices that actually appear in the structure
    // (spanning ALL atomic units, not just the first chain).
    const presentAtoms = new Set<number>();
    for (const unit of structure.units) {
        if (unit.kind !== 0) continue; // skip non-atomic units
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        for (let i = 0; i < count; i++) {
            presentAtoms.add(OrderedSet.getAt(elements, i));
        }
    }

    for (let groupIndex = 0; groupIndex < residueOffsets.length - 1; groupIndex++) {
        const start = residueOffsets[groupIndex];
        const end = residueOffsets[groupIndex + 1];
        if (end <= start) continue;

        // Skip groups whose atoms are not present in this structure (e.g., deleted residues).
        if (!presentAtoms.has(start)) continue;

        const atomIndices: number[] = [];
        for (let atomIndex = start; atomIndex < end; atomIndex++) {
            atomIndices.push(atomIndex);
        }
        const chainIndex = chainIndexByAtom[start];
        const entityIndex = modelIndex.getEntityFromChain(chainIndex);
        const compId = atoms.label_comp_id.value(start);
        const authSeqId = residues.auth_seq_id.value(groupIndex);
        const chainName = chains.label_asym_id.value(chainIndex);
        const entityName = chains.label_entity_id.value(chainIndex);

        const getValue = (col: any, idx: number) => {
            if (!col) return undefined;
            if (typeof col.value === "function") return col.value(idx);
            return col[idx];
        };

        const molId = getValue(molIdCol, start);
        const molName = getValue(molNameCol, start);
        const compIndex = getValue(compIdCol, start);
        const compName = getValue(compNameCol, start);

        const item: GroupSelectionItem = {
            source_kind: "element",
            element_level: "group",
            atom_indices: atomIndices,
            group_indices: [groupIndex],
            chain_indices: [chainIndex],
            entity_indices: [entityIndex],
            group_name: `${compId} ${authSeqId}`,
            group_id: authSeqId,
            chain_name: chainName,
            entity_name: entityName,
        };
        if (typeof compIndex === "number" && Number.isFinite(compIndex)) item.component_indices = [compIndex];
        if (typeof compName === "string" && compName.trim()) item.component_name = compName;
        if (typeof molId === "number" && Number.isFinite(molId)) item.molecule_indices = [molId];
        if (typeof molName === "string" && molName.trim()) item.molecule_name = molName;
        items.push(item);
    }

    return items;
}

function normalizeToElementLoci(rawLoci: any): any {
    if (StructureElement.Loci.is(rawLoci)) return rawLoci;
    try {
        return Loci.normalize(rawLoci, "element", true);
    } catch {
        return rawLoci;
    }
}

export function lociToGroupItems(rawLoci: any): GroupSelectionItem[] {
    const loci = normalizeToElementLoci(rawLoci);
    if (!StructureElement.Loci.is(loci)) return [];

    const items: GroupSelectionItem[] = [];
    const seen = new Set<string>();

    for (const lociElement of loci.elements) {
        const unit = lociElement.unit;
        const model = unit.model;
        const hierarchy = model?.atomicHierarchy;
        const modelIndex = hierarchy?.index;
        let atomSite: any = undefined;
        
        if (model?.sourceData?.kind === "mmCIF") {
            atomSite = (model.sourceData.data as any).db?.atom_site;
        } else if (model?.sourceData?.kind === "mol-viewer:molsysmt") {
            atomSite = model.sourceData.data;
        }


        if (!hierarchy || !modelIndex) continue;
        const residueIndexByAtom = hierarchy.residueAtomSegments.index;
        const residueOffsets = hierarchy.residueAtomSegments.offsets;
        const chainIndexByAtom = hierarchy.chainAtomSegments.index;
        const atoms = hierarchy.atoms;
        const residues = hierarchy.residues;
        const chains = hierarchy.chains;

        // Safe access to custom hierarchy columns
        const molIdCol = (atomSite as any)?.molsys_molecule_id || (atomSite as any)?.molecule_id;
        const molNameCol = (atomSite as any)?.molsys_molecule_name || (atomSite as any)?.molecule_name;
        const compIdCol = (atomSite as any)?.molsys_component_id || (atomSite as any)?.component_id;
        const compNameCol = (atomSite as any)?.molsys_component_name || (atomSite as any)?.component_name;

        const size = OrderedSet.size(lociElement.indices);
        for (let i = 0; i < size; i++) {
            const unitIndex = OrderedSet.getAt(lociElement.indices, i);
            const atomIndex = unit.elements[unitIndex];
            const groupIndex = residueIndexByAtom[atomIndex];
            const chainIndex = chainIndexByAtom[atomIndex];
            const entityIndex = modelIndex.getEntityFromChain(chainIndex);
            const key = `${model.id}:${chainIndex}:${groupIndex}`;
            if (seen.has(key)) continue;
            seen.add(key);

            const atomIndices: number[] = [];
            for (let j = residueOffsets[groupIndex], jl = residueOffsets[groupIndex + 1]; j < jl; j++) {
                atomIndices.push(j);
            }

            const firstAtom = residueOffsets[groupIndex];
            const compId = atoms.label_comp_id.value(firstAtom);
            const authSeqId = residues.auth_seq_id.value(groupIndex);
            const chainName = chains.label_asym_id.value(chainIndex);
            const entityName = chains.label_entity_id.value(chainIndex);
            const groupName = `${compId} ${authSeqId}`;

            const getValue = (col: any, idx: number) => {
                if (!col) return undefined;
                if (typeof col.value === "function") return col.value(idx);
                return col[idx];
            };

            const molId = getValue(molIdCol, atomIndex);
            const molName = getValue(molNameCol, atomIndex);
            const compIndex = getValue(compIdCol, atomIndex);
            const compName = getValue(compNameCol, atomIndex);

            const item: GroupSelectionItem = {
                source_kind: "element",
                element_level: "group",
                atom_indices: atomIndices,
                group_indices: [groupIndex],
                chain_indices: [chainIndex],
                entity_indices: [entityIndex],
                group_name: groupName,
                group_id: authSeqId,
                chain_name: chainName,
                entity_name: entityName,
            };
            if (typeof compIndex === "number" && Number.isFinite(compIndex)) item.component_indices = [compIndex];
            if (typeof compName === "string" && compName.trim()) item.component_name = compName;
            if (typeof molId === "number" && Number.isFinite(molId)) item.molecule_indices = [molId];
            if (typeof molName === "string" && molName.trim()) item.molecule_name = molName;
            items.push(item);
        }
    }

    return items;
}

function arrayOfNumbers(value: unknown): number[] {
    return Array.isArray(value)
        ? value.map((item) => (typeof item === "number" ? Math.trunc(item) : Number(item))).filter((item) => Number.isFinite(item))
        : [];
}

function lociToShapeItems(rawLoci: any): ActiveSelectionItem[] {
    const shape = ShapeGroup.isLoci(rawLoci) ? rawLoci.shape : Shape.isLoci(rawLoci) ? rawLoci.shape : null;
    if (!shape) return [];
    const data = (shape.sourceData ?? {}) as Record<string, unknown>;

    let shapeName = shape.name;
    // Default to the whole-shape atoms; narrow to the picked group's own atoms when
    // the shape exposes them (face -> its 3, edge -> 2, tetra -> 4) so clicking a
    // sub-element selects only that simplex, not the entire shape.
    let atomIndices = arrayOfNumbers(data.atom_indices);
    let entityRef: unknown = undefined;
    if (ShapeGroup.isLoci(rawLoci) && rawLoci.groups.length > 0) {
        try {
            const groupIdx = OrderedSet.getAt(rawLoci.groups[0].ids, 0);
            if (typeof shape.getLabel === "function") {
                shapeName = shape.getLabel(groupIdx, 0);
            }
            const perGroup = (data as any).__groupAtoms;
            if (Array.isArray(perGroup) && Array.isArray(perGroup[groupIdx])) {
                atomIndices = arrayOfNumbers(perGroup[groupIdx]);
            }
            const perGroupEntityRefs = (data as any).__groupEntityRefs;
            if (Array.isArray(perGroupEntityRefs) && perGroupEntityRefs[groupIdx] !== undefined) {
                entityRef = perGroupEntityRefs[groupIdx];
            } else if (Array.isArray((data as any).entity_refs) && (data as any).entity_refs[groupIdx] !== undefined) {
                entityRef = (data as any).entity_refs[groupIdx];
            }
        } catch (e) {
            console.warn("[MolSysViewer] Error getting shape group label:", e);
        }
    }

    const item: any = {
        source_kind: "shape",
        shape_kind: typeof data.kind === "string" ? data.kind : shape.name,
        shape_name: shapeName,
        tag: typeof data.tag === "string" ? data.tag : undefined,
        atom_indices: atomIndices,
        group_indices: arrayOfNumbers(data.group_indices),
        chain_indices: arrayOfNumbers(data.chain_indices),
        entity_indices: arrayOfNumbers(data.entity_indices),
        ...(entityRef !== undefined ? { entity_ref: entityRef } : {}),
    };
    // Keep the picked loci alongside the item for persistent shape-group
    // highlighting (consumed by syncVisualSelection). Non-enumerable so it does
    // not leak into the JSON payload sent to Python.
    if (rawLoci) {
        Object.defineProperty(item, "_loci", { value: rawLoci, enumerable: false, configurable: true });
    }
    return [item];
}

function emptyPayload(): ActiveSelectionPayload {
    return {
        event: "interaction_active_selection_changed",
        source_kind: "empty",
        element_level: "none",
        target_level: "none",
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
}

function signature(item: ActiveSelectionItem): string {
    if (item.source_kind === "annotation") {
        return `${item.source_kind}:${item.annotation_kind}:${item.tag ?? ""}:${item.group_indices.join(",")}:${item.chain_indices.join(",")}`;
    }
    if (item.source_kind === "shape") {
        return `${item.source_kind}:${item.tag ?? ""}:${item.shape_name ?? item.shape_kind}`;
    }
    return `${item.source_kind}:${item.element_level}:${item.group_indices.join(",")}:${item.chain_indices.join(",")}`;
}

function appendUnique(target: number[], seen: Set<number>, values: number[] | undefined) {
    if (!Array.isArray(values)) return;
    for (const value of values) {
        if (seen.has(value)) continue;
        seen.add(value);
        target.push(value);
    }
}

function buildPayload(items: ActiveSelectionItem[]): ActiveSelectionPayload {
    if (items.length === 0) return emptyPayload();

    const sourceKinds = new Set(items.map((item) => item.source_kind));
    const sourceKind = sourceKinds.size > 1 ? "mixed" : items[0].source_kind;

    const atomIndices: number[] = [];
    const groupIndices: number[] = [];
    const componentIndices: number[] = [];
    const chainIndices: number[] = [];
    const moleculeIndices: number[] = [];
    const entityIndices: number[] = [];
    const seenAtoms = new Set<number>();
    const seenGroups = new Set<number>();
    const seenComponents = new Set<number>();
    const seenChains = new Set<number>();
    const seenMolecules = new Set<number>();
    const seenEntities = new Set<number>();

    for (const item of items) {
        appendUnique(atomIndices, seenAtoms, item.atom_indices);
        appendUnique(groupIndices, seenGroups, item.group_indices);
        appendUnique(componentIndices, seenComponents, item.component_indices);
        appendUnique(chainIndices, seenChains, item.chain_indices);
        appendUnique(moleculeIndices, seenMolecules, item.molecule_indices);
        appendUnique(entityIndices, seenEntities, item.entity_indices);
    }

    return {
        event: "interaction_active_selection_changed",
        source_kind: sourceKind,
        element_level: sourceKind === "element" || sourceKind === "mixed" ? "group" : "none",
        target_level:
            sourceKind === "annotation"
                ? "annotation"
                : sourceKind === "shape"
                    ? "shape"
                    : sourceKind === "mixed"
                        ? "mixed"
                        : "none",
        items,
        atom_indices: atomIndices,
        group_indices: groupIndices,
        component_indices: componentIndices,
        chain_indices: chainIndices,
        molecule_indices: moleculeIndices,
        entity_indices: entityIndices,
        count_atoms: atomIndices.length,
        count_groups: groupIndices.length,
        count_shapes: items.filter((item) => item.source_kind === "shape").length,
        count_annotations: items.filter((item) => item.source_kind === "annotation").length,
    };
}

export class ActiveSelectionController {
    private items: ActiveSelectionItem[] = [];
    private allAvailableItems: GroupSelectionItem[] = [];
    private anchorItem: ActiveSelectionItem | null = null;

    // The original in-memory items (with their non-enumerable shape ``_loci`` refs)
    // for callers that need the live JS objects (e.g. ``syncVisualSelection`` to
    // mark shape-group selections persistently). The JSON payload sent to Python
    // strips ``_loci`` (non-enumerable), so consumers wanting it must read here.
    getCurrentItems(): ActiveSelectionItem[] {
        return this.items;
    }

    constructor(private readonly notify?: (msg: any) => void) {}

    setAllAvailableItems(items: GroupSelectionItem[]): void {
        this.allAvailableItems = items;
    }

    handlePrimaryClick(ev: any): void {
        const shift = !!ev?.modifiers?.shift;
        const alt = !!ev?.modifiers?.alt;
        const pickedItems: ActiveSelectionItem[] = [
            ...lociToGroupItems(ev?.current?.loci),
            ...lociToShapeItems(ev?.current?.loci),
        ];
        
        if (pickedItems.length === 0) {
            if (!shift) {
                this.clear();
                this.anchorItem = null;
            }
            return;
        }

        const current = pickedItems[0]; // Take first pick for simplicity in range logic

        if (shift && alt && this.anchorItem && this.anchorItem.source_kind === "element" && current.source_kind === "element") {
            // Range selection logic
            if (this.anchorItem.chain_name === current.chain_name) {
                const rangeItems = this.getRangeItems(this.anchorItem, current);
                if (rangeItems.length > 0) {
                    this.setItems(rangeItems, "add", true);
                    // Do not update anchor on range selection to allow expanding the range
                    return;
                }
            }
        }

        // Default behavior: single or add/toggle selection
        this.setItems(pickedItems, shift ? "add" : "replace");
        this.anchorItem = current;
    }

    handleItemClick(item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }): void {
        const { shift, alt } = modifiers;

        if (shift && alt && this.anchorItem && this.anchorItem.source_kind === "element" && item.source_kind === "element") {
            if (this.anchorItem.chain_name === item.chain_name) {
                const rangeItems = this.getRangeItems(this.anchorItem, item);
                if (rangeItems.length > 0) {
                    this.setItems(rangeItems, "add", true);
                    return;
                }
            }
        }

        this.setItems([item], shift ? "add" : "replace");
        this.anchorItem = item;
    }

    private getRangeItems(anchor: GroupSelectionItem, target: GroupSelectionItem): GroupSelectionItem[] {
        // Find indices in allAvailableItems based on group index and chain name
        const anchorIdx = this.allAvailableItems.findIndex(i => 
            i.chain_name === anchor.chain_name && i.group_indices[0] === anchor.group_indices[0]
        );
        const targetIdx = this.allAvailableItems.findIndex(i => 
            i.chain_name === target.chain_name && i.group_indices[0] === target.group_indices[0]
        );

        if (anchorIdx === -1 || targetIdx === -1) return [];

        const start = Math.min(anchorIdx, targetIdx);
        const end = Math.max(anchorIdx, targetIdx);
        
        return this.allAvailableItems.slice(start, end + 1);
    }

    setItems(items: ActiveSelectionItem[], op: ActiveSelectionSetOperation = "replace", isRange = false): void {
        if (items.length === 0) {
            if (op === "replace" || op === "intersect") this.clear();
            return;
        }
        if (op === "replace") {
            this.applyItems([...items]);
            return;
        }
        if (op === "subtract") {
            const removeKeys = new Set(items.map((item) => signature(item)));
            const next = this.items.filter((item) => !removeKeys.has(signature(item)));
            this.applyItems(next);
            return;
        }
        if (op === "intersect") {
            const keepKeys = new Set(items.map((item) => signature(item)));
            const next = this.items.filter((item) => keepKeys.has(signature(item)));
            this.applyItems(next);
            return;
        }
        const next = [...this.items];
        const indexByKey = new Map(next.map((item, index) => [signature(item), index] as const));
        for (const item of items) {
            const key = signature(item);
            const existingIndex = indexByKey.get(key);
            if (existingIndex !== undefined) {
                if (item.source_kind === "element" && !isRange) {
                    next.splice(existingIndex, 1);
                    indexByKey.clear();
                    next.forEach((candidate, index) => indexByKey.set(signature(candidate), index));
                }
                continue;
            }
            next.push(item);
            indexByKey.set(key, next.length - 1);
        }
        this.applyItems(next);
    }

    clear(): void {
        this.applyItems([]);
    }

    setFromAtomIndices(atomIndices: number[], structure: Structure | null | undefined): void {
        if (!structure || atomIndices.length === 0) {
            this.clear();
            return;
        }
        const target = new Set(atomIndices);
        // Build loci elements across ALL atomic units so that atoms on any chain
        // (e.g. monomer B of a dimer, or the second additively-loaded system) are found.
        const lociElements: { unit: any; indices: any }[] = [];
        for (const unit of structure.units) {
            if (unit.kind !== 0) continue; // skip non-atomic units
            const matched: number[] = [];
            const elements = unit.elements;
            const count = OrderedSet.size(elements);
            for (let i = 0; i < count; i++) {
                if (target.has(OrderedSet.getAt(elements, i))) matched.push(i);
            }
            if (matched.length > 0) {
                lociElements.push({ unit, indices: SortedArray.ofSortedArray(matched) });
            }
        }
        if (lociElements.length === 0) {
            this.clear();
            return;
        }
        const loci = StructureElement.Loci(structure, lociElements as any);
        const items = lociToGroupItems(loci);
        this.setItems(items, "replace");
    }

    private emit(): void {
        this.notify?.(buildPayload(this.items));
    }

    private applyItems(next: ActiveSelectionItem[]): void {
        if (sameItems(this.items, next)) {
            this.emit();
            return;
        }
        // Undo/redo is owned by the single scene history (Python view.history),
        // which checkpoints on the resulting interaction_active_selection_changed
        // event; this controller no longer keeps its own stack.
        this.items = [...next];
        this.emit();
    }
}

function sameItems(a: ActiveSelectionItem[], b: ActiveSelectionItem[]): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (signature(a[i]) !== signature(b[i])) return false;
    }
    return true;
}
