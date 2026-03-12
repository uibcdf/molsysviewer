import { StructureElement } from "molstar/lib/mol-model/structure";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";

export type ActiveSelectionItem = {
    source_kind: "element";
    element_level: "atom";
    atom_indices: number[];
};

export type ActiveSelectionPayload = {
    event: "interaction_active_selection_changed";
    source_kind: "empty" | "element";
    element_level: "none" | "atom";
    target_level: "none";
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
};

function lociToAtomIndices(loci: any): number[] {
    if (!StructureElement.Loci.is(loci)) return [];
    const atomIndices: number[] = [];
    const seen = new Set<number>();
    for (const element of loci.elements) {
        const size = OrderedSet.size(element.indices);
        for (let i = 0; i < size; i++) {
            const unitIndex = OrderedSet.getAt(element.indices, i);
            const atomIndex = element.unit.elements[unitIndex];
            if (!seen.has(atomIndex)) {
                seen.add(atomIndex);
                atomIndices.push(atomIndex);
            }
        }
    }
    return atomIndices;
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
    };
}

function signature(item: ActiveSelectionItem): string {
    return `${item.source_kind}:${item.element_level}:${item.atom_indices.join(",")}`;
}

function buildPayload(items: ActiveSelectionItem[]): ActiveSelectionPayload {
    if (items.length === 0) return emptyPayload();
    const atomIndices: number[] = [];
    const seen = new Set<number>();
    for (const item of items) {
        for (const atomIndex of item.atom_indices) {
            if (seen.has(atomIndex)) continue;
            seen.add(atomIndex);
            atomIndices.push(atomIndex);
        }
    }
    return {
        event: "interaction_active_selection_changed",
        source_kind: "element",
        element_level: "atom",
        target_level: "none",
        items,
        atom_indices: atomIndices,
        group_indices: [],
        component_indices: [],
        chain_indices: [],
        molecule_indices: [],
        entity_indices: [],
        count_atoms: atomIndices.length,
        count_groups: 0,
        count_shapes: 0,
    };
}

export class ActiveSelectionController {
    private items: ActiveSelectionItem[] = [];

    constructor(private readonly notify?: (msg: any) => void) {}

    handlePrimaryClick(ev: any): void {
        const shift = !!ev?.modifiers?.shift;
        const atomIndices = lociToAtomIndices(ev?.current?.loci);
        if (atomIndices.length === 0) {
            if (!shift) this.clear();
            return;
        }
        const item: ActiveSelectionItem = {
            source_kind: "element",
            element_level: "atom",
            atom_indices: atomIndices,
        };
        if (!shift) {
            this.items = [item];
            this.emit();
            return;
        }
        const next = [...this.items];
        const known = new Set(next.map(signature));
        const key = signature(item);
        if (!known.has(key)) {
            next.push(item);
            this.items = next;
        }
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
