import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra/3d/vec3";

import {
    AddAngleMeasurementMessage,
    AddDihedralMeasurementMessage,
    AddDistanceMeasurementMessage,
} from "../../messages/viewer-messages";

type MeasurementMessage =
    | AddDistanceMeasurementMessage
    | AddAngleMeasurementMessage
    | AddDihedralMeasurementMessage;

type MeasurementEndpointPolicy = "atom" | "centroid" | "representative_atom";

type MeasurementOptionsSummary = {
    endpoint_policy: MeasurementEndpointPolicy;
    endpoint_kinds: string[];
    endpoint_labels: string[];
    endpoint_atom_indices: number[][];
};

const DEFAULT_REPRESENTATIVE_ATOMS = {
    protein: "CA",
    nucleic: "P",
    lipid: "P",
    other: "",
} as const;

export interface MeasurementCallbacks {
    getStructure: () => Structure | undefined;
    registerRef: (ref?: StateObjectRef, tag?: string) => void;
}

export class MeasurementHandlers {
    private readonly measurementRefs = new Set<StateObjectRef>();
    private readonly refsByTag = new Map<string, Set<StateObjectRef>>();
    private readonly specsByTag = new Map<string, MeasurementMessage>();
    private endpointPolicyDefault: MeasurementEndpointPolicy = "centroid";
    private representativeAtoms: Record<string, string> = { ...DEFAULT_REPRESENTATIVE_ATOMS };

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
        this.refsByTag.clear();
        await Promise.all(
            refs.map(ref => PluginCommands.State.RemoveObject(this.plugin, {
                state: this.plugin.state.data,
                ref,
                removeParentGhosts: true,
            }))
        );
    }

    async clearMeasurementByTag(tag: string) {
        const refs = Array.from(this.refsByTag.get(tag) ?? []);
        if (refs.length === 0) return;
        this.refsByTag.delete(tag);
        for (const ref of refs) {
            this.measurementRefs.delete(ref);
        }
        await Promise.all(
            refs.map(ref => PluginCommands.State.RemoveObject(this.plugin, {
                state: this.plugin.state.data,
                ref,
                removeParentGhosts: true,
            }))
        );
    }

    async setVisibility(tag: string, visible: boolean) {
        if (!visible) {
            await this.clearMeasurementByTag(tag);
            return;
        }
        if ((this.refsByTag.get(tag)?.size ?? 0) > 0) return;
        const spec = this.specsByTag.get(tag);
        if (!spec) return;
        if (spec.op === "add_distance_measurement") {
            await this.addDistance(spec);
        } else if (spec.op === "add_angle_measurement") {
            await this.addAngle(spec);
        } else {
            await this.addDihedral(spec);
        }
    }

    hasTag(tag: string): boolean {
        return this.specsByTag.has(tag) || this.refsByTag.has(tag);
    }

    renameTag(oldTag: string, newTag: string) {
        if (!oldTag || !newTag || oldTag === newTag) return;
        const refs = this.refsByTag.get(oldTag);
        if (refs) {
            this.refsByTag.delete(oldTag);
            this.refsByTag.set(newTag, refs);
        }
        const spec = this.specsByTag.get(oldTag);
        if (spec) {
            this.specsByTag.delete(oldTag);
            this.specsByTag.set(newTag, {
                ...spec,
                tag: newTag,
                options: {
                    ...(spec.options ?? {}),
                    tag: newTag,
                },
            } as MeasurementMessage);
        }
    }

    dropTag(tag: string) {
        const refs = Array.from(this.refsByTag.get(tag) ?? []);
        this.refsByTag.delete(tag);
        this.specsByTag.delete(tag);
        for (const ref of refs) {
            this.measurementRefs.delete(ref);
        }
    }

    setSettings(options?: { endpoint_policy_default?: string; representative_atoms?: Record<string, string> }) {
        const policy = options?.endpoint_policy_default;
        if (policy === "atom" || policy === "centroid" || policy === "representative_atom") {
            this.endpointPolicyDefault = policy;
        }
        if (options?.representative_atoms && typeof options.representative_atoms === "object") {
            this.representativeAtoms = {
                ...this.representativeAtoms,
                ...Object.fromEntries(
                    Object.entries(options.representative_atoms).map(([key, value]) => [key, String(value ?? "").trim()])
                ),
            };
        }
    }

    computeMeasurementValue(
        picks: number[][],
        options: MeasurementOptionsSummary,
        structureArg?: Structure,
    ): number | undefined {
        const structure = structureArg ?? this.callbacks.getStructure();
        const positions: Vec3[] = [];
        for (let i = 0; i < picks.length; i++) {
            const effectiveIndices = Array.isArray(options.endpoint_atom_indices[i]) && options.endpoint_atom_indices[i].length > 0
                ? options.endpoint_atom_indices[i]
                : picks[i] ?? [];
            const pos = this.centroidPosition(structure, effectiveIndices);
            if (pos === undefined) return undefined;
            positions.push(pos);
        }
        if (positions.length === 2) {
            return Vec3.distance(positions[0], positions[1]);
        }
        if (positions.length === 3) {
            // angle between three points: vectors from middle point to A and C
            const v1 = Vec3.sub(Vec3.zero(), positions[0], positions[1]);
            const v2 = Vec3.sub(Vec3.zero(), positions[2], positions[1]);
            return Vec3.angle(v1, v2) * (180 / Math.PI);
        }
        if (positions.length === 4) {
            return Vec3.dihedralAngle(positions[0], positions[1], positions[2], positions[3]) * (180 / Math.PI);
        }
        return undefined;
    }

    buildMeasurementOptions(
        picks: number[][],
        endpointPolicy?: string,
        structureArg?: Structure,
    ): MeasurementOptionsSummary {
        const structure = structureArg ?? this.callbacks.getStructure();
        const policy = this.normalizeEndpointPolicy(endpointPolicy);
        return this.resolveMeasurementOptions(structure, picks, policy);
    }

    private async addMeasurement(msg: MeasurementMessage, kind: "distance" | "angle" | "dihedral") {
        const structure = this.callbacks.getStructure();
        if (!structure) return;

        const picks = Array.isArray(msg.options?.picks_atom_indices) ? msg.options!.picks_atom_indices! : [];
        const tag = msg.tag ?? msg.options?.tag ?? "measurement";
        const measurementOptions = this.buildMeasurementOptions(
            picks,
            typeof msg.options?.endpoint_policy === "string" ? msg.options.endpoint_policy : undefined,
            structure,
        );
        this.specsByTag.set(tag, {
            op: msg.op,
            tag,
            options: {
                ...(msg.options ?? {}),
                tag,
                picks_atom_indices: picks.map(item => Array.isArray(item) ? [...item] : []),
                endpoint_policy: measurementOptions.endpoint_policy,
                endpoint_kinds: [...measurementOptions.endpoint_kinds],
                endpoint_labels: [...measurementOptions.endpoint_labels],
                endpoint_atom_indices: measurementOptions.endpoint_atom_indices.map((item) => [...item]),
            },
        } as MeasurementMessage);
        const actualAtomIndices = measurementOptions.endpoint_atom_indices.map((item, index) => {
            if (Array.isArray(item) && item.length > 0) return item;
            return picks[index] ?? [];
        });
        const locis = actualAtomIndices.map((pick) => this.buildLociFromAtomIndices(structure, pick)).filter(Boolean);
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
            const refs = this.refsByTag.get(tag) ?? new Set<StateObjectRef>();
            refs.add(added.selection.ref);
            this.refsByTag.set(tag, refs);
            this.callbacks.registerRef(added.selection.ref, tag);
        }
        if (added.representation?.ref) {
            this.measurementRefs.add(added.representation.ref);
            const refs = this.refsByTag.get(tag) ?? new Set<StateObjectRef>();
            refs.add(added.representation.ref);
            this.refsByTag.set(tag, refs);
            this.callbacks.registerRef(added.representation.ref, tag);
        }
    }

    private atomPositionForIndex(structure: Structure | undefined, atomIndex: number): Vec3 | undefined {
        if (!structure) return undefined;
        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elements = unit.elements;
            if (OrderedSet.indexOf(elements, atomIndex as any) < 0) continue;
            const conformation = unit.model.atomicConformation;
            return Vec3.create(conformation.x[atomIndex], conformation.y[atomIndex], conformation.z[atomIndex]);
        }
        return undefined;
    }

    private centroidPosition(structure: Structure | undefined, atomIndices: number[]): Vec3 | undefined {
        if (!atomIndices || atomIndices.length === 0) return undefined;
        const sum = Vec3.zero();
        let count = 0;
        for (const idx of atomIndices) {
            const pos = this.atomPositionForIndex(structure, idx);
            if (pos === undefined) return undefined;
            Vec3.add(sum, sum, pos);
            count++;
        }
        if (count === 0) return undefined;
        return Vec3.scale(sum, sum, 1 / count);
    }

    private normalizeEndpointPolicy(endpointPolicy?: string): MeasurementEndpointPolicy {
        if (endpointPolicy === "atom" || endpointPolicy === "centroid" || endpointPolicy === "representative_atom") {
            return endpointPolicy;
        }
        return this.endpointPolicyDefault;
    }

    private resolveMeasurementOptions(
        structure: Structure | undefined,
        picks: number[][],
        endpointPolicy: MeasurementEndpointPolicy,
    ): MeasurementOptionsSummary {
        const endpoint_kinds: string[] = [];
        const endpoint_labels: string[] = [];
        const endpoint_atom_indices: number[][] = [];
        for (const rawPick of picks) {
            const pick = Array.isArray(rawPick) ? rawPick.map((item) => Number(item)).filter((item) => Number.isFinite(item)) : [];
            if (pick.length === 0) {
                endpoint_kinds.push("atom");
                endpoint_labels.push("atom");
                endpoint_atom_indices.push([]);
                continue;
            }
            if (pick.length === 1) {
                endpoint_kinds.push("atom");
                endpoint_labels.push(this.atomNameForIndex(structure, pick[0]) ?? "atom");
                endpoint_atom_indices.push([pick[0]]);
                continue;
            }
            if (endpointPolicy === "centroid") {
                endpoint_kinds.push("centroid");
                endpoint_labels.push("centroid");
                endpoint_atom_indices.push([]);
                continue;
            }
            const representativeIndex = this.resolveRepresentativeAtomIndex(structure, pick);
            endpoint_kinds.push("representative_atom");
            endpoint_labels.push(this.atomNameForIndex(structure, representativeIndex) ?? "representative_atom");
            endpoint_atom_indices.push([representativeIndex]);
        }
        return {
            endpoint_policy: endpointPolicy,
            endpoint_kinds,
            endpoint_labels,
            endpoint_atom_indices,
        };
    }

    private resolveRepresentativeAtomIndex(structure: Structure | undefined, pick: number[]): number {
        const atomNames = pick.map((item) => this.atomNameForIndex(structure, item) ?? "");
        const groupType = this.groupTypeForIndex(structure, pick[0]) ?? "";
        const category = this.representativeCategory(atomNames, groupType);
        const preferred = String(this.representativeAtoms[category] ?? this.representativeAtoms.other ?? "").trim();
        if (preferred) {
            for (let i = 0; i < pick.length; i++) {
                if ((atomNames[i] ?? "").toUpperCase() === preferred.toUpperCase()) {
                    return pick[i];
                }
            }
        }
        return pick[0];
    }

    private representativeCategory(atomNames: string[], groupType: string): "protein" | "nucleic" | "lipid" | "other" {
        const normalizedGroupType = String(groupType ?? "").trim().toLowerCase();
        if (normalizedGroupType === "amino acid") return "protein";
        if (normalizedGroupType === "nucleotide") return "nucleic";
        if (normalizedGroupType === "lipid") return "lipid";
        const atomNameSet = new Set(atomNames.map((item) => String(item ?? "").trim().toUpperCase()));
        if (atomNameSet.has("CA")) return "protein";
        if (atomNameSet.has("P")) return "nucleic";
        return "other";
    }

    private atomNameForIndex(structure: Structure | undefined, atomIndex: number): string | undefined {
        const model = this.modelForAtomIndex(structure, atomIndex);
        const value = model?.atomicHierarchy?.atoms?.label_atom_id?.value?.(atomIndex);
        if (typeof value === "string" && value.trim()) return value.trim();
        return undefined;
    }

    private groupTypeForIndex(structure: Structure | undefined, atomIndex: number): string | undefined {
        const model = this.modelForAtomIndex(structure, atomIndex);
        const atoms: any = model?.atomicHierarchy?.atoms;
        const value = atoms?.molsys_group_type?.value?.(atomIndex);
        if (typeof value === "string" && value.trim()) return value.trim();
        return undefined;
    }

    private modelForAtomIndex(structure: Structure | undefined, atomIndex: number): any {
        if (!structure) return undefined;
        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            if ((unit.elements as any).indexOf?.(atomIndex) >= 0) {
                return unit.model;
            }
        }
        return undefined;
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
