import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef, StateTransform } from "molstar/lib/mol-state";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { Color } from "molstar/lib/mol-util/color";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra";

import { AddLabelMessage, LabelStyle, UpdateLabelMessage } from "../../messages/viewer-messages";
import { AnnotationGeometry, cameraOffsetPosition, renderAnnotation } from "../../shapes/annotation-callout";

function styleToVisualParams(style?: LabelStyle): Record<string, unknown> | undefined {
    if (!style) return undefined;
    const params: Record<string, unknown> = {};
    if (style.color !== undefined) {
        const hex = style.color.trim();
        if (hex.startsWith("#") && (hex.length === 7 || hex.length === 4)) {
            const full = hex.length === 4
                ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`
                : hex;
            params.textColor = Color(parseInt(full.slice(1), 16));
        }
    }
    if (style.size_em !== undefined) params.textSize = style.size_em;
    if (style.background !== undefined) params.background = style.background;
    if (style.background_opacity !== undefined) params.backgroundOpacity = style.background_opacity;
    return Object.keys(params).length > 0 ? params : undefined;
}

export interface AnnotationCallbacks {
    getStructure: () => Structure | undefined;
    registerRef: (ref?: StateObjectRef, tag?: string) => void;
    addLabelOverlay?: (msg: AddLabelMessage) => void;
}

export class AnnotationHandlers {
    private readonly labelRefs = new Set<StateTransform.Ref>();
    private readonly hiddenTags = new Set<string>();
    private readonly callouts = new Map<string, { ref: string; signature: string }>();
    private refreshQueue = Promise.resolve();
    private cameraSignature = "";
    private disposed = false;
    private readonly refsByTag = new Map<string, Set<StateTransform.Ref>>();
    private readonly specsByTag = new Map<string, {
        text: string;
        atom_indices: number[];
        tag: string;
        layer_tag?: string;
        style?: LabelStyle;
        position?: number[];
        offset_mode?: "camera" | "world";
        offset?: number[];
        leader_line?: boolean;
        leader_line_style?: "solid" | "dashed" | "dotted";
    }>();
    /** Maps layer_tag → Set of annotation tags that belong to it. */
    private readonly layerTagIndex = new Map<string, Set<string>>();

    constructor(
        private readonly plugin: PluginContext,
        private readonly callbacks: AnnotationCallbacks,
    ) {}

    async addLabel(msg: AddLabelMessage) {
        const structure = this.callbacks.getStructure();

        const text = typeof msg.options?.text === "string" ? msg.options.text : "";
        const atomIndices = Array.isArray(msg.options?.atom_indices)
            ? msg.options!.atom_indices!.map(i => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter(i => Number.isFinite(i))
            : [];
        const tag = msg.tag ?? msg.options?.tag ?? "annotation";
        const layer_tag = msg.options?.layer_tag;
        const style = msg.options?.style;
        const position = Array.isArray(msg.options?.position)
            ? msg.options.position.map(Number)
            : undefined;
        const offsetMode = msg.options?.offset_mode ?? "camera";
        const offset = Array.isArray(msg.options?.offset)
            ? msg.options.offset.map(Number)
            : [0.0, 0.0, 0.0];
        const leaderLine = !!msg.options?.leader_line;
        const leaderLineStyle = msg.options?.leader_line_style ?? "dashed";
        if (position && msg.options?.position_unit !== undefined && msg.options.position_unit !== "angstrom") {
            throw new Error("Annotation position must use angstrom units.");
        }
        const expectedOffsetUnit = offsetMode === "world" ? "angstrom" : "dimensionless";
        if (msg.options?.offset_unit !== undefined && msg.options.offset_unit !== expectedOffsetUnit) {
            throw new Error("Annotation offset has incompatible units.");
        }
        if ((position && (position.length !== 3 || position.some(v => !Number.isFinite(v)))) ||
            offset.length !== 3 || offset.some(v => !Number.isFinite(v))) {
            throw new Error("Annotation coordinates and offsets require finite triples.");
        }

        if (!text.trim() && !position && atomIndices.length === 0) return;

        this.specsByTag.set(tag, {
            text: text.trim(),
            atom_indices: [...atomIndices],
            tag,
            layer_tag,
            style,
            position,
            offset_mode: offsetMode,
            offset,
            leader_line: leaderLine,
            leader_line_style: leaderLineStyle,
        });

        if (layer_tag && layer_tag !== tag) {
            const group = this.layerTagIndex.get(layer_tag) ?? new Set<string>();
            group.add(tag);
            this.layerTagIndex.set(layer_tag, group);
        }

        // Notify UI overlay (strips)
        this.callbacks.addLabelOverlay?.(msg);
        if (this.hiddenTags.has(tag)) return;

        if (position || offsetMode === "world" || leaderLine) {
            const geometry = this.geometryFor(tag);
            if (!geometry) return;
            const ref = await renderAnnotation(this.plugin, geometry);
            this.callouts.set(tag, { ref, signature: JSON.stringify(geometry) });
            this.labelRefs.add(ref);
            this.refsByTag.set(tag, new Set([ref]));
            this.callbacks.registerRef(ref, tag);
            return;
        }

        let loci: any;
        const finalOffset = [...offset];

        if (!structure) return;
        loci = this.buildLociFromAtomIndices(structure, atomIndices);

        if (!loci) return;

        const styleParams = styleToVisualParams(style) ?? {};
        // tooltip: tag enables Mol*'s pickability for this label repr
        const mergedVisualParams = {
            ...styleParams,
            tooltip: tag,
            offsetX: finalOffset[0],
            offsetY: finalOffset[1],
            offsetZ: finalOffset[2],
            tether: leaderLine,
            tetherLength: 1,
        } as any;

        const added = await this.plugin.managers.structure.measurement.addLabel(loci, {
            selectionTags: [tag],
            reprTags: [tag],
            labelParams: { customText: text },
            visualParams: mergedVisualParams,
        });
        if (!added) return;

        if (added.selection?.ref) {
            const selectionRef = StateObjectRef.resolveRef(added.selection.ref);
            if (selectionRef) {
                this.labelRefs.add(selectionRef);
                const refs = this.refsByTag.get(tag) ?? new Set<StateTransform.Ref>();
                refs.add(selectionRef);
                this.refsByTag.set(tag, refs);
            }
            this.callbacks.registerRef(added.selection.ref, tag);
        }
        if (added.representation?.ref) {
            const representationRef = StateObjectRef.resolveRef(added.representation.ref);
            if (representationRef) {
                this.labelRefs.add(representationRef);
                const refs = this.refsByTag.get(tag) ?? new Set<StateTransform.Ref>();
                refs.add(representationRef);
                this.refsByTag.set(tag, refs);
            }
            this.callbacks.registerRef(added.representation.ref, tag);
        }
    }

    async updateLabel(msg: UpdateLabelMessage) {
        const tag = msg.tag ?? msg.options?.tag ?? "annotation";
        await this.clearLabelByTag(tag);
        const prevSpec = this.specsByTag.get(tag);
        await this.addLabel({
            op: "add_label",
            tag,
            options: {
                text: msg.options?.text ?? prevSpec?.text,
                atom_indices: msg.options?.atom_indices ?? prevSpec?.atom_indices,
                tag,
                layer_tag: msg.options?.layer_tag ?? prevSpec?.layer_tag,
                style: msg.options?.style ?? prevSpec?.style,
                position: msg.options && Object.prototype.hasOwnProperty.call(msg.options, "position")
                    ? msg.options.position ?? undefined : prevSpec?.position,
                offset_mode: msg.options?.offset_mode ?? prevSpec?.offset_mode,
                offset: msg.options?.offset ?? prevSpec?.offset,
                leader_line: msg.options?.leader_line ?? prevSpec?.leader_line,
                leader_line_style: msg.options?.leader_line_style ?? prevSpec?.leader_line_style,
            },
        });
    }

    /** Structure rebuilds may already have removed a label and its ghost parent. */
    private async removeLabelRefs(refs: Iterable<string>): Promise<void> {
        for (const ref of refs) {
            const state = this.plugin.state.data;
            if (!state.tree.transforms.has(ref)) continue;
            await PluginCommands.State.RemoveObject(this.plugin, { state, ref, removeParentGhosts: true });
        }
    }

    async clearLabels() {
        this.specsByTag.clear();
        this.hiddenTags.clear();
        this.layerTagIndex.clear();
        this.callouts.clear();
        await this.refreshQueue;
        const refs = Array.from(this.labelRefs);
        this.labelRefs.clear();
        this.refsByTag.clear();
        await this.removeLabelRefs(refs);
    }

    async clearLabelByTag(tag: string) {
        this.callouts.delete(tag);
        await this.refreshQueue;
        const refs = Array.from(this.refsByTag.get(tag) ?? []);
        if (refs.length === 0) return;
        this.refsByTag.delete(tag);
        for (const ref of refs) {
            this.labelRefs.delete(ref);
        }
        await this.removeLabelRefs(refs);
    }

    hasTag(tag: string): boolean {
        return this.specsByTag.has(tag) || this.refsByTag.has(tag);
    }

    renameTag(oldTag: string, newTag: string) {
        if (!oldTag || !newTag || oldTag === newTag) return;
        if (this.hiddenTags.delete(oldTag)) this.hiddenTags.add(newTag);
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
                layer_tag: spec.layer_tag === oldTag ? newTag : spec.layer_tag,
            });
        }
        const callout = this.callouts.get(oldTag);
        if (callout) { this.callouts.delete(oldTag); this.callouts.set(newTag, callout); }
        for (const tags of this.layerTagIndex.values()) {
            if (tags.delete(oldTag)) tags.add(newTag);
        }
        const ownLayer = this.layerTagIndex.get(oldTag);
        if (ownLayer) {
            this.layerTagIndex.delete(oldTag);
            this.layerTagIndex.set(newTag, ownLayer);
        }
    }

    dropTag(tag: string) {
        this.hiddenTags.delete(tag);
        this.callouts.delete(tag);
        const refs = Array.from(this.refsByTag.get(tag) ?? []);
        this.refsByTag.delete(tag);
        this.specsByTag.delete(tag);
        for (const ref of refs) this.labelRefs.delete(ref);
        for (const tags of this.layerTagIndex.values()) tags.delete(tag);
        this.layerTagIndex.delete(tag);
    }

    async setVisibility(tag: string, visible: boolean) {
        // If the tag matches a layer_tag group, delegate to each member annotation.
        const layerGroup = this.layerTagIndex.get(tag);
        if (layerGroup && layerGroup.size > 0) {
            await Promise.all(Array.from(layerGroup).map(t => this.setVisibility(t, visible)));
            return;
        }
        if (!visible) {
            this.hiddenTags.add(tag);
            await this.clearLabelByTag(tag);
            return;
        }
        this.hiddenTags.delete(tag);
        if ((this.refsByTag.get(tag)?.size ?? 0) > 0) return;
        const spec = this.specsByTag.get(tag);
        if (!spec) return;
        await this.addLabel({
            op: "add_label",
            tag,
            options: {
                text: spec.text,
                atom_indices: [...spec.atom_indices],
                tag,
                layer_tag: spec.layer_tag,
                style: spec.style,
                position: spec.position,
                offset_mode: spec.offset_mode,
                offset: spec.offset,
                leader_line: spec.leader_line,
                leader_line_style: spec.leader_line_style,
            },
        });
    }

    getSpec(tag: string): { text: string; atom_indices: number[] } | undefined {
        const spec = this.specsByTag.get(tag);
        return spec ? { text: spec.text, atom_indices: spec.atom_indices } : undefined;
    }

    private geometryFor(tag: string): AnnotationGeometry | undefined {
        const spec = this.specsByTag.get(tag);
        if (!spec) return;
        let anchor = spec.position ? [...spec.position] : undefined;
        if (!anchor) {
            const structure = this.callbacks.getStructure();
            if (!structure) return;
            const wanted = new Set(spec.atom_indices);
            const center = Vec3();
            const point = Vec3();
            let count = 0;
            for (const unit of structure.units) {
                if (!Unit.isAtomic(unit)) continue;
                for (let ordinal = 0; ordinal < OrderedSet.size(unit.elements); ordinal++) {
                    const atom = OrderedSet.getAt(unit.elements, ordinal);
                    if (!wanted.has(atom)) continue;
                    unit.conformation.position(atom, point);
                    Vec3.add(center, center, point);
                    count++;
                }
            }
            if (!count) return;
            anchor = Array.from(Vec3.scale(center, center, 1 / count));
        }
        const offset = spec.offset ?? [0, 0, 0];
        const camera = this.plugin.canvas3d?.camera.state;
        const position = spec.offset_mode === "world" || !camera
            ? anchor.map((value, i) => value + offset[i]) : cameraOffsetPosition(anchor, offset, camera);
        const style = styleToVisualParams(spec.style) ?? {};
        return { tag, text: spec.text, anchor, position,
            color: Number(style.textColor ?? 0), size: Number(style.textSize ?? 0.5),
            background: Boolean(style.background ?? false), backgroundOpacity: Number(style.backgroundOpacity ?? 0.5),
            leader: !!spec.leader_line, pattern: spec.leader_line_style ?? "dashed" };
    }

    refresh(): Promise<void> {
        const update = this.refreshQueue.then(async () => {
            if (this.disposed) return;
            for (const [tag, callout] of this.callouts) {
                const geometry = this.geometryFor(tag);
                if (!geometry) continue;
                const signature = JSON.stringify(geometry);
                if (signature === callout.signature) continue;
                await renderAnnotation(this.plugin, geometry, callout.ref);
                if (this.callouts.get(tag) === callout) callout.signature = signature;
            }
        });
        this.refreshQueue = update.catch(() => {});
        return update;
    }

    onCamera(snapshot: unknown): void {
        if (!this.callouts.size) return;
        const signature = JSON.stringify(snapshot);
        if (signature === this.cameraSignature) return;
        this.cameraSignature = signature;
        void this.refresh().catch(error => console.warn("[MolSysViewer] Annotation refresh failed", error));
    }

    dispose(): void { this.disposed = true; this.callouts.clear(); }

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

    private findClosestAtom(structure: Structure, target: number[]): { elementIndex: number; unit: Unit; distance: number; coords: [number, number, number] } | undefined {
        let closest: { elementIndex: number; unit: Unit; distance: number; coords: [number, number, number] } | undefined = undefined;
        let minDistSq = Infinity;

        const tx = target[0];
        const ty = target[1];
        const tz = target[2];

        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elements = unit.elements;
            const elementCount = OrderedSet.size(elements);
            const p = Vec3.zero();

            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(elements, ordinal);
                unit.conformation.position(elementIndex, p);
                const dx = p[0] - tx;
                const dy = p[1] - ty;
                const dz = p[2] - tz;
                const distSq = dx * dx + dy * dy + dz * dz;
                if (distSq < minDistSq) {
                    minDistSq = distSq;
                    closest = {
                        elementIndex,
                        unit,
                        distance: Math.sqrt(distSq),
                        coords: [p[0], p[1], p[2]]
                    };
                }
            }
        }
        return closest;
    }

    private buildLociForSingleAtom(structure: Structure, unit: Unit, elementIndex: number) {
        const subset = SortedArray.ofSortedArray([elementIndex]) as StructureElement.Set;
        const childUnit = unit.getChild(subset);
        const subStructure = Structure.create([childUnit], { parent: structure });
        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        selectionBuilder.add(subStructure);
        const sel = selectionBuilder.getSelection();
        return StructureSelection.toLociWithSourceUnits(sel);
    }
}
