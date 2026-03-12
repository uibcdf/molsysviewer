import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";

import {
    AddAngleMeasurementMessage,
    AddDihedralMeasurementMessage,
    AddDistanceMeasurementMessage,
} from "../../messages/viewer-messages";

type MeasurementMessage =
    | AddDistanceMeasurementMessage
    | AddAngleMeasurementMessage
    | AddDihedralMeasurementMessage;

export interface MeasurementCallbacks {
    getStructure: () => Structure | undefined;
    registerRef: (ref?: StateObjectRef, tag?: string) => void;
}

export class MeasurementHandlers {
    private readonly measurementRefs = new Set<StateObjectRef>();

    constructor(
        private readonly plugin: PluginContext,
        private readonly callbacks: MeasurementCallbacks,
    ) {}

    async addDistance(msg: AddDistanceMeasurementMessage) {
        await this.addMeasurement(msg, "distance");
    }

    async addAngle(msg: AddAngleMeasurementMessage) {
        await this.addMeasurement(msg, "angle");
    }

    async addDihedral(msg: AddDihedralMeasurementMessage) {
        await this.addMeasurement(msg, "dihedral");
    }

    async clearMeasurements() {
        if (this.measurementRefs.size === 0) return;
        const refs = Array.from(this.measurementRefs);
        this.measurementRefs.clear();
        await Promise.all(
            refs.map(ref => PluginCommands.State.RemoveObject(this.plugin, {
                state: this.plugin.state.data,
                ref,
                removeParentGhosts: true,
            }))
        );
    }

    private async addMeasurement(msg: MeasurementMessage, kind: "distance" | "angle" | "dihedral") {
        const structure = this.callbacks.getStructure();
        if (!structure) return;

        const picks = Array.isArray(msg.options?.picks_atom_indices) ? msg.options!.picks_atom_indices! : [];
        const tag = msg.tag ?? msg.options?.tag ?? "measurement";
        const locis = picks.map((pick) => this.buildLociFromAtomIndices(structure, pick)).filter(Boolean);
        const expected = kind === "distance" ? 2 : kind === "angle" ? 3 : 4;
        if (locis.length !== expected) return;

        const measurement = this.plugin.managers.structure.measurement;
        let added:
            | { selection?: { ref?: StateObjectRef }; representation?: { ref?: StateObjectRef } }
            | undefined;

        if (kind === "distance") {
            added = await measurement.addDistance(locis[0]!, locis[1]!, {
                selectionTags: [tag],
                reprTags: [tag],
            });
        } else if (kind === "angle") {
            added = await measurement.addAngle(locis[0]!, locis[1]!, locis[2]!, {
                selectionTags: [tag],
                reprTags: [tag],
            });
        } else {
            added = await measurement.addDihedral(locis[0]!, locis[1]!, locis[2]!, locis[3]!, {
                selectionTags: [tag],
                reprTags: [tag],
            });
        }

        if (!added) return;
        if (added.selection?.ref) {
            this.measurementRefs.add(added.selection.ref);
            this.callbacks.registerRef(added.selection.ref, tag);
        }
        if (added.representation?.ref) {
            this.measurementRefs.add(added.representation.ref);
            this.callbacks.registerRef(added.representation.ref, tag);
        }
    }

    private buildLociFromAtomIndices(structure: Structure, atomIndices: number[]) {
        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        const set = new Set(
            (Array.isArray(atomIndices) ? atomIndices : [])
                .map(i => (typeof i === "number" ? Math.trunc(i) : Number(i)))
                .filter(i => Number.isFinite(i))
        );
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
