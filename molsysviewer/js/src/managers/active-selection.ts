import { Structure } from "molstar/lib/mol-model/structure";
import { StructureElement } from "molstar/lib/mol-model/structure";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { Shape, ShapeGroup } from "molstar/lib/mol-model/shape";

export type ActiveSelectionItem = {
    source_kind: "element";
    element_level: "group";
    atom_indices: number[];
    group_indices: number[];
    chain_indices: number[];
    entity_indices: number[];
    group_name?: string;
    group_id?: number | string;
    chain_name?: string;
    entity_name?: string;
} | {
    source_kind: "annotation";
    annotation_kind: "label";
    atom_indices: number[];
    group_indices: number[];
    chain_indices: number[];
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
    chain_indices: number[];
    entity_indices: number[];
};

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

export function buildGroupItemsFromStructure(structure: Structure): ActiveSelectionItem[] {
    const atomicUnit = structure.units.find((unit) => unit.kind === 0);
    if (!atomicUnit) return [];

    const model = atomicUnit.model;
    const hierarchy = model.atomicHierarchy;
    const residueOffsets = hierarchy.residueAtomSegments.offsets;
    const chainIndexByAtom = hierarchy.chainAtomSegments.index;
    const atoms = hierarchy.atoms;
    const residues = hierarchy.residues;
    const chains = hierarchy.chains;
    const modelIndex = hierarchy.index;
    const items: ActiveSelectionItem[] = [];

    for (let groupIndex = 0; groupIndex < residueOffsets.length - 1; groupIndex++) {
        const start = residueOffsets[groupIndex];
        const end = residueOffsets[groupIndex + 1];
        if (end <= start) continue;
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
        items.push({
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
        });
    }

    return items;
}

function lociToGroupItems(rawLoci: any): ActiveSelectionItem[] {
    if (!StructureElement.Loci.is(rawLoci)) return [];

    const items: ActiveSelectionItem[] = [];
    const seen = new Set<string>();

    for (const lociElement of rawLoci.elements) {
        const unit = lociElement.unit;
        const model = unit.model;
        const hierarchy = model.atomicHierarchy;
        const residueIndexByAtom = hierarchy.residueAtomSegments.index;
        const residueOffsets = hierarchy.residueAtomSegments.offsets;
        const chainIndexByAtom = hierarchy.chainAtomSegments.index;
        const atoms = hierarchy.atoms;
        const residues = hierarchy.residues;
        const chains = hierarchy.chains;
        const modelIndex = hierarchy.index;

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

            items.push({
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
            });
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
    return [{
        source_kind: "shape",
        shape_kind: typeof data.kind === "string" ? data.kind : shape.name,
        shape_name: shape.name,
        tag: typeof data.tag === "string" ? data.tag : undefined,
        atom_indices: arrayOfNumbers(data.atom_indices),
        group_indices: arrayOfNumbers(data.group_indices),
        chain_indices: arrayOfNumbers(data.chain_indices),
        entity_indices: arrayOfNumbers(data.entity_indices),
    }];
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

function appendUnique(target: number[], seen: Set<number>, values: number[]) {
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
    const chainIndices: number[] = [];
    const entityIndices: number[] = [];
    const seenAtoms = new Set<number>();
    const seenGroups = new Set<number>();
    const seenChains = new Set<number>();
    const seenEntities = new Set<number>();

    for (const item of items) {
        appendUnique(atomIndices, seenAtoms, item.atom_indices);
        appendUnique(groupIndices, seenGroups, item.group_indices);
        appendUnique(chainIndices, seenChains, item.chain_indices);
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
        component_indices: [],
        chain_indices: chainIndices,
        molecule_indices: [],
        entity_indices: entityIndices,
        count_atoms: atomIndices.length,
        count_groups: groupIndices.length,
        count_shapes: items.filter((item) => item.source_kind === "shape").length,
        count_annotations: items.filter((item) => item.source_kind === "annotation").length,
    };
}

export class ActiveSelectionController {
    private items: ActiveSelectionItem[] = [];

    constructor(private readonly notify?: (msg: any) => void) {}

    handlePrimaryClick(ev: any): void {
        const shift = !!ev?.modifiers?.shift;
        const items = lociToGroupItems(ev?.current?.loci).concat(lociToShapeItems(ev?.current?.loci));
        if (items.length === 0) {
            if (!shift) this.clear();
            return;
        }
        this.setItems(items, shift);
    }

    setItems(items: ActiveSelectionItem[], additive = false): void {
        if (items.length === 0) {
            if (!additive) this.clear();
            return;
        }
        if (!additive) {
            this.items = [...items];
            this.emit();
            return;
        }
        const next = [...this.items];
        const known = new Set(next.map(signature));
        for (const item of items) {
            const key = signature(item);
            if (known.has(key)) continue;
            known.add(key);
            next.push(item);
        }
        this.items = next;
        this.emit();
    }

    clear(): void {
        this.items = [];
        this.emit();
    }

    private emit(): void {
        this.notify?.(buildPayload(this.items));
    }
}
