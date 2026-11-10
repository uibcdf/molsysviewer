import type { Model } from "molstar/lib/mol-model/structure/model";

// Mol* sorts atomic rows into its own group/chain hierarchy. Python and the
// MolSys wire protocol retain the original source axis. The hierarchy is shared
// by trajectory models, so a lazy inverse belongs here, not once per frame.
const inverses = new WeakMap<object, Int32Array>();
const native = (model: Model | undefined): boolean => model?.sourceData?.kind === "mol-viewer:molsysmt";

export function sourceAtomIndex(model: Model, elementIndex: number): number {
    const source = native(model) ? model.atomicHierarchy?.atomSourceIndex : undefined;
    return source ? source.value(elementIndex) : elementIndex;
}

export function modelAtomIndex(model: Model, sourceIndex: number): number | undefined {
    const hierarchy = native(model) ? model.atomicHierarchy : undefined;
    const source = hierarchy?.atomSourceIndex;
    if (!hierarchy || !source) return sourceIndex;
    if (!Number.isInteger(sourceIndex) || sourceIndex < 0 || sourceIndex >= source.rowCount) return undefined;
    if (source.value(sourceIndex) === sourceIndex) return sourceIndex;
    let inverse = inverses.get(hierarchy);
    if (!inverse) {
        inverse = new Int32Array(source.rowCount);
        inverse.fill(-1);
        for (let i = 0; i < source.rowCount; i++) inverse[source.value(i)] = i;
        inverses.set(hierarchy, inverse);
    }
    const index = inverse[sourceIndex];
    return index < 0 ? undefined : index;
}

/** Native label_* columns carry explicit positional axes, not author IDs. */
export function sourceGroupIndex(model: Model, groupIndex: number): number {
    return native(model) && (model.sourceData.data as any)?.has_source_group_indices
        ? model.atomicHierarchy.residues.label_seq_id.value(groupIndex) : groupIndex;
}

export function sourceChainIndex(model: Model, chainIndex: number): number {
    return native(model) && (model.sourceData.data as any)?.has_source_chain_indices
        ? Number(model.atomicHierarchy.chains.label_asym_id.value(chainIndex)) : chainIndex;
}
