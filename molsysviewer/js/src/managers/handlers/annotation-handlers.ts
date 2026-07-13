import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef, StateTransform } from "molstar/lib/mol-state";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { Color } from "molstar/lib/mol-util/color";

import { AddLabelMessage, LabelStyle, UpdateLabelMessage } from "../../messages/viewer-messages";

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
    private readonly refsByTag = new Map<string, Set<StateTransform.Ref>>();
    private readonly specsByTag = new Map<string, { text: string; atom_indices: number[]; tag: string; layer_tag?: string; style?: LabelStyle }>();
    /** Maps layer_tag → Set of annotation tags that belong to it. */
    private readonly layerTagIndex = new Map<string, Set<string>>();

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
        const layer_tag = msg.options?.layer_tag;
        const style = msg.options?.style;
        if (!text.trim() || atomIndices.length === 0) return;
        this.specsByTag.set(tag, { text: text.trim(), atom_indices: [...atomIndices], tag, layer_tag, style });
        if (layer_tag && layer_tag !== tag) {
            const group = this.layerTagIndex.get(layer_tag) ?? new Set<string>();
            group.add(tag);
            this.layerTagIndex.set(layer_tag, group);
        }

        // Notify UI overlay (strips)
        this.callbacks.addLabelOverlay?.(msg);

        const loci = this.buildLociFromAtomIndices(structure, atomIndices);
        if (!loci) return;

        const styleParams = styleToVisualParams(style) ?? {};
        // tooltip: tag enables Mol*'s pickability for this label repr
        const mergedVisualParams = { ...styleParams, tooltip: tag } as any;
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
                text: msg.options?.text,
                atom_indices: msg.options?.atom_indices,
                tag,
                layer_tag: msg.options?.layer_tag ?? prevSpec?.layer_tag,
                style: msg.options?.style ?? prevSpec?.style,
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
                layer_tag: spec.layer_tag === oldTag ? newTag : spec.layer_tag,
            });
        }
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
            await this.clearLabelByTag(tag);
            return;
        }
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
            },
        });
    }

    getSpec(tag: string): { text: string; atom_indices: number[] } | undefined {
        const spec = this.specsByTag.get(tag);
        return spec ? { text: spec.text, atom_indices: spec.atom_indices } : undefined;
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
