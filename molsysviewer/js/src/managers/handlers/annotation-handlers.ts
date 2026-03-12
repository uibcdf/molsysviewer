import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";

import { AddLabelMessage, UpdateLabelMessage } from "../../messages/viewer-messages";

export interface AnnotationCallbacks {
    getStructure: () => Structure | undefined;
    registerRef: (ref?: StateObjectRef, tag?: string) => void;
}

export class AnnotationHandlers {
    private readonly labelRefs = new Set<StateObjectRef>();
    private readonly refsByTag = new Map<string, Set<StateObjectRef>>();

    constructor(
        private readonly plugin: PluginContext,
        private readonly callbacks: AnnotationCallbacks,
    ) {}

    async addLabel(msg: AddLabelMessage) {
        const structure = this.callbacks.getStructure();
        if (!structure) return;

        const text = typeof msg.options?.text === "string" ? msg.options.text : "";
        const atomIndices = Array.isArray(msg.options?.atom_indices)
            ? msg.options!.atom_indices!.map(i => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter(i => Number.isFinite(i))
            : [];
        const tag = msg.tag ?? msg.options?.tag ?? "annotation";
        if (!text.trim() || atomIndices.length === 0) return;

        const loci = this.buildLociFromAtomIndices(structure, atomIndices);
        if (!loci) return;

        const added = await this.plugin.managers.structure.measurement.addLabel(loci, {
            selectionTags: [tag],
            reprTags: [tag],
            labelParams: { customText: text },
        });
        if (!added) return;

        if (added.selection?.ref) {
            this.labelRefs.add(added.selection.ref);
            const refs = this.refsByTag.get(tag) ?? new Set<StateObjectRef>();
            refs.add(added.selection.ref);
            this.refsByTag.set(tag, refs);
            this.callbacks.registerRef(added.selection.ref, tag);
        }
        if (added.representation?.ref) {
            this.labelRefs.add(added.representation.ref);
            const refs = this.refsByTag.get(tag) ?? new Set<StateObjectRef>();
            refs.add(added.representation.ref);
            this.refsByTag.set(tag, refs);
            this.callbacks.registerRef(added.representation.ref, tag);
        }
    }

    async updateLabel(msg: UpdateLabelMessage) {
        const tag = msg.tag ?? msg.options?.tag ?? "annotation";
        await this.clearLabelByTag(tag);
        await this.addLabel({
            op: "add_label",
            tag,
            options: {
                text: msg.options?.text,
                atom_indices: msg.options?.atom_indices,
                tag,
            },
        });
    }

    async clearLabels() {
        if (this.labelRefs.size === 0) return;
        const refs = Array.from(this.labelRefs);
        this.labelRefs.clear();
        this.refsByTag.clear();
        await Promise.all(
            refs.map(ref => PluginCommands.State.RemoveObject(this.plugin, {
                state: this.plugin.state.data,
                ref,
                removeParentGhosts: true,
            }))
        );
    }

    async clearLabelByTag(tag: string) {
        const refs = Array.from(this.refsByTag.get(tag) ?? []);
        if (refs.length === 0) return;
        this.refsByTag.delete(tag);
        for (const ref of refs) {
            this.labelRefs.delete(ref);
        }
        await Promise.all(
            refs.map(ref => PluginCommands.State.RemoveObject(this.plugin, {
                state: this.plugin.state.data,
                ref,
                removeParentGhosts: true,
            }))
        );
    }

    private buildLociFromAtomIndices(structure: Structure, atomIndices: number[]) {
        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        const set = new Set(atomIndices);
        let added = false;

        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elements = unit.elements;
            const elementCount = OrderedSet.size(elements);
            if (elementCount === 0) continue;

            const matched: number[] = [];
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(elements, ordinal);
                if (set.has(elementIndex)) matched.push(elementIndex);
            }
            if (matched.length === 0) continue;
            added = true;
            matched.sort((a, b) => a - b);

            const subset =
                matched.length === elementCount
                    ? elements
                    : (SortedArray.ofSortedArray(matched) as StructureElement.Set);
            const childUnit = unit.getChild(subset);
            const subStructure = Structure.create([childUnit], { parent: structure });
            selectionBuilder.add(subStructure);
        }

        if (!added) return undefined;
        return StructureSelection.toLociWithSourceUnits(selectionBuilder.getSelection());
    }
}
