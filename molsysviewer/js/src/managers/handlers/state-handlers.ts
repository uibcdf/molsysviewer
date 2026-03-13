import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef, StateObjectSelector } from "molstar/lib/mol-state";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { setSubtreeVisibility } from "molstar/lib/mol-plugin/behavior/static/state";
import { PresetStructureRepresentations } from "molstar/lib/mol-plugin-state/builder/structure/representation-preset";
import {
    clearStructureTransparency,
    setStructureTransparency,
} from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";

import {
    CreateLayerMessage,
    CreateRegionMessage,
    DeleteLayerMessage,
    DeleteRegionMessage,
    HideGlobalMessage,
    HideLayerMessage,
    HideRegionMessage,
    SetGlobalRepresentationMessage,
    SetLayerTagMessage,
    SetRegionRepresentationMessage,
    ShowGlobalMessage,
    ShowLayerMessage,
    ShowRegionMessage,
    UpdateVisibilityMessage,
    ZoomMessage,
} from "../../messages/viewer-messages";
import { LoadedStructure } from "../../plugin/structure";

interface RegionEntry {
    component?: StateObjectRef;
    representations: StateObjectRef[];
    atomIndices: number[];
    selection?: string;
    hidden?: boolean;
}

export interface StateCallbacks {
    getStructure: () => Structure | undefined;
    getLoadedStructure: () => LoadedStructure | undefined;
    getCurrentStructureRef: () => StateObjectRef | undefined;
    getComponents: () => StructureComponentRef[];
    notify: (msg: any) => void;
    setManagedLayerVisibility?: (tag: string, kind: string, visible: boolean) => Promise<boolean>;
}

export class StateHandlers {
    private readonly regionIndex = new Map<string, RegionEntry>();
    private readonly layerMeta = new Map<string, { kind?: string; meta?: Record<string, unknown> }>();
    private readonly tagIndex = new Map<string, Set<StateObjectRef>>();
    private readonly globalReprs = new Set<StateObjectRef>();
    private readonly pendingGlobalOps: Array<{ hide: boolean; target: "global" | "all" }> = [];
    private readonly pendingLayerVisibility = new Map<string, boolean>();
    private readonly pendingRegions: CreateRegionMessage[] = [];
    private pendingVisibility?: number[];
    private requestedGlobalHidden: boolean | null = null;
    private pendingZoom?: ZoomMessage;

    constructor(private plugin: PluginContext, private callbacks: StateCallbacks) {}

    registerTaggedRef(ref?: StateObjectRef, tag?: string, kind: string = "shape") {
        if (!ref) return;
        if (!tag) return;
        if (!this.tagIndex.has(tag)) this.tagIndex.set(tag, new Set());
        this.tagIndex.get(tag)!.add(ref);
        
        if (!this.layerMeta.has(tag)) {
            this.layerMeta.set(tag, { kind, meta: {} });
            this.callbacks.notify({ event: "layer_ack", tag, kind, meta: {} });
        }
        
        if (this.pendingLayerVisibility.has(tag)) {
            const hide = this.pendingLayerVisibility.get(tag)!;
            this.pendingLayerVisibility.delete(tag);
            setSubtreeVisibility(this.plugin.state.data, ref, hide);
        }
    }

    registerShapeRef(ref?: StateObjectRef, tag?: string) {
        this.registerTaggedRef(ref, tag, "shape");
    }

    async updateVisibility(msg: UpdateVisibilityMessage | number[] | undefined) {
        const indices = Array.isArray(msg) || msg === undefined ? msg : msg.options?.visible_atom_indices;
        
        const structure = this.callbacks.getStructure();
        if (!structure) {
            if (Array.isArray(indices)) {
                this.pendingVisibility = indices;
            }
            return;
        }
        const components = this.callbacks.getComponents();
        if (components.length === 0) return;

        await clearStructureTransparency(this.plugin, components);

        if (!Array.isArray(indices)) return;

        const hideAll = indices.length === 0;
        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        const visibleSet = hideAll ? void 0 : new Set(indices);
        let hasHidden = hideAll;

        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elementCount = OrderedSet.size(unit.elements);
            if (elementCount === 0) continue;

            if (hideAll) {
                const childUnit = unit.getChild(unit.elements);
                const hiddenStructure = Structure.create([childUnit], { parent: structure });
                selectionBuilder.add(hiddenStructure);
                continue;
            }

            const hiddenElements: number[] = [];
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(unit.elements, ordinal);
                if (!visibleSet?.has(elementIndex)) {
                    hiddenElements.push(elementIndex);
                }
            }

            if (hiddenElements.length === 0) continue;
            hasHidden = true;

            const elementSubset =
                hiddenElements.length === elementCount
                    ? unit.elements
                    : (SortedArray.ofSortedArray(hiddenElements) as StructureElement.Set);
            const childUnit = unit.getChild(elementSubset);
            const hiddenStructure = Structure.create([childUnit], { parent: structure });
            selectionBuilder.add(hiddenStructure);
        }

        if (!hasHidden) return;

        const selection = selectionBuilder.getSelection();
        if (StructureSelection.isEmpty(selection)) return;

        const loci = StructureSelection.toLociWithSourceUnits(selection);
        await setStructureTransparency(this.plugin, components, 1, async () => loci);
    }

    async createRegion(msg: CreateRegionMessage) {
        const structure = this.callbacks.getStructure();
        if (!structure) {
            this.pendingRegions.push(msg);
            return;
        }
        const tag = msg.tag ?? "region";
        const atomIndices = Array.isArray(msg.atom_indices)
            ? msg.atom_indices.map(i => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter(i => Number.isFinite(i))
            : [];
        const selection = this.buildSelectionFromAtomIndices(structure, atomIndices);
        if (!selection) {
            console.warn("[MolSysViewer] create_region missing valid atom indices");
            return;
        }

        try {
            const structureRef = this.callbacks.getLoadedStructure()?.structure;
            if (!structureRef) return;

            const bundle = StructureElement.Bundle.fromSelection(selection);
            const root = this.plugin.state.data.build().to(structureRef);
            const component = root.apply(StateTransforms.Model.StructureComponent, {
                type: { name: "bundle", params: bundle },
                nullIfEmpty: true,
                label: tag,
            });
            await component.commit({ revertOnError: false });
            const componentRef = component.selector.ref;
            
            if (!component.selector.isOk || !componentRef) {
                console.warn("[MolSysViewer] create_region: empty component for", tag);
                return;
            }
            
            const reprType = msg.representation ?? "cartoon";
            const repr = await this.plugin.builders.structure.representation.addRepresentation(
                componentRef as any,
                { type: reprType as any, typeParams: (msg.params ?? {}) as any },
                { tag }
            );
            const reprRef = repr?.ref;
            
            this.regionIndex.set(tag, {
                component: componentRef,
                representations: reprRef ? [reprRef] : [],
                atomIndices,
                selection: msg.selection,
                hidden: false,
            });
            
            this.callbacks.notify({ event: "region_ack", tag, atom_indices: atomIndices, selection: msg.selection });
        } catch (err) {
            console.error("[MolSysViewer] Error creating region", err);
        }
    }

    async setRegionRepresentation(msg: SetRegionRepresentationMessage) {
        const tag = msg.tag ?? "region";
        const entry = this.regionIndex.get(tag);
        if (!entry || !entry.component) return;

        if (entry.representations.length) {
            await Promise.all(entry.representations.map(ref => this.removeStateObject(ref)));
            entry.representations = [];
        }
        if (msg.user_preset) {
            const { base, rules } = msg.user_preset || {};
            if (base) {
                const applied = await this.plugin.builders.structure.representation.applyPreset(
                    { ref: entry.component } as any,
                    base as any,
                    (msg.params ?? {}) as any
                );
                const refs = this.collectRefsFromPreset(applied as any);
                entry.representations.push(...refs);
            }
            if (Array.isArray(rules)) {
                const update = this.plugin.state.data.build();
                for (const rule of rules) {
                    const type = rule?.representation ?? "cartoon";
                    const params = (rule?.params ?? msg.params ?? {}) as any;
                    const repr = this.plugin.builders.structure.representation.buildRepresentation(
                        update,
                        { ref: entry.component } as any,
                        { type: type as any, typeParams: params },
                        { tag }
                    );
                    if (repr?.ref) entry.representations.push(repr.ref);
                }
                await update.commit({ revertOnError: false });
            }
        } else if (msg.preset) {
            const applied = await this.plugin.builders.structure.representation.applyPreset(
                { ref: entry.component } as any,
                msg.preset as any,
                (msg.params ?? {}) as any
            );
            const refs = this.collectRefsFromPreset(applied as any);
            entry.representations.push(...refs);
        } else {
            const update = this.plugin.state.data.build();
            const reprType = msg.representation ?? "cartoon";
            const repr = this.plugin.builders.structure.representation.buildRepresentation(
                update,
                { ref: entry.component } as any,
                { type: reprType as any, typeParams: (msg.params ?? {}) as any },
                { tag }
            );
            await update.commit({ revertOnError: false });
            const reprRef = repr?.ref;
            if (reprRef) entry.representations.push(reprRef);
        }
    }

    async showRegion(msg: ShowRegionMessage) {
        await this.toggleRegionVisibility(msg.tag, false);
    }

    async hideRegion(msg: HideRegionMessage) {
        await this.toggleRegionVisibility(msg.tag, true);
    }

    async deleteRegion(msg: DeleteRegionMessage) {
        const tag = msg.tag ?? "region";
        const entry = this.regionIndex.get(tag);
        if (!entry) return;
        const refs: Array<StateObjectRef | undefined> = [
            ...entry.representations,
            entry.component,
        ];
        await Promise.all(refs.map(ref => this.removeStateObject(ref)));
        this.regionIndex.delete(tag);
        this.callbacks.notify({ event: "region_deleted", tag });
    }

    async createLayer(msg: CreateLayerMessage) {
        const tag = msg.tag ?? "layer";
        this.layerMeta.set(tag, { kind: msg.kind, meta: msg.meta });
        this.callbacks.notify({ event: "layer_ack", tag, kind: msg.kind, meta: msg.meta });
    }

    async showLayer(msg: ShowLayerMessage) {
        await this.toggleLayerVisibility(msg.tag, false);
    }

    async hideLayer(msg: HideLayerMessage) {
        await this.toggleLayerVisibility(msg.tag, true);
    }

    async deleteLayer(msg: DeleteLayerMessage) {
        const tag = msg.tag ?? "layer";
        const refs = this.tagIndex.get(tag);
        if (refs && refs.size) {
            await Promise.all(Array.from(refs).map(ref => this.removeStateObject(ref)));
            this.tagIndex.delete(tag);
        }
        this.layerMeta.delete(tag);
        this.callbacks.notify({ event: "layer_deleted", tag });
    }

    async setLayerTag(msg: SetLayerTagMessage) {
        const oldTag = msg.tag ?? "layer";
        const newTag = msg.new_tag;
        if (!newTag || oldTag === newTag) return;
        const refs = this.tagIndex.get(oldTag);
        if (refs) {
            this.tagIndex.delete(oldTag);
            this.tagIndex.set(newTag, refs);
        }
        const meta = this.layerMeta.get(oldTag);
        if (meta) {
            this.layerMeta.delete(oldTag);
            this.layerMeta.set(newTag, meta);
        }
    }

    async setGlobalRepresentation(msg: SetGlobalRepresentationMessage) {
        const structureRef = this.callbacks.getLoadedStructure()?.structure;
        if (!structureRef) return;

        if (this.globalReprs.size) {
            await Promise.all(Array.from(this.globalReprs).map(ref => this.removeStateObject(ref)));
            this.globalReprs.clear();
        }
        if (msg.user_preset) {
            const userPreset = msg.user_preset || {};
            const base = userPreset.base as string | undefined;
            const rules = Array.isArray(userPreset.rules) ? userPreset.rules : [];
            if (base) {
                const applied = await this.plugin.builders.structure.representation.applyPreset(
                    { ref: structureRef } as any,
                    base as any,
                    (msg.params ?? {}) as any
                );
                const refs = this.collectRefsFromPreset(applied as any);
                refs.forEach(ref => this.globalReprs.add(ref));
            }
            for (const rule of rules) {
                const atomIndices = Array.isArray(rule?.atom_indices)
                    ? rule.atom_indices.map(i => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter(i => Number.isFinite(i))
                    : [];
                if (atomIndices.length === 0) continue;
                
                const structureData = this.callbacks.getStructure();
                if (!structureData) continue;
                
                const selection = this.buildSelectionFromAtomIndices(structureData, atomIndices);
                if (!selection) continue;
                
                const bundle = StructureElement.Bundle.fromSelection(selection);
                const root = this.plugin.state.data.build().to(structureRef);
                const component = root.apply(StateTransforms.Model.StructureComponent, {
                    type: { name: "bundle", params: bundle },
                    nullIfEmpty: true,
                    label: msg.user_preset?.name ?? "global-rule",
                });
                await component.commit({ revertOnError: false });
                const componentRef = component.selector?.ref;
                if (!component.selector?.isOk || !componentRef) continue;
                
                const update = this.plugin.state.data.build();
                const reprType = rule?.representation ?? "cartoon";
                const repr = this.plugin.builders.structure.representation.buildRepresentation(
                    update,
                    { ref: componentRef } as any,
                    { type: reprType as any, typeParams: (rule?.params ?? {}) as any },
                    { tag: "global" }
                );
                await update.commit({ revertOnError: false });
                if (repr?.ref) this.globalReprs.add(repr.ref);
            }
        } else if (msg.preset) {
            const presetId = (msg.preset as any) in PresetStructureRepresentations ? msg.preset : msg.preset;
            const applied = await this.plugin.builders.structure.representation.applyPreset(
                { ref: structureRef } as any,
                presetId as any,
                (msg.params ?? {}) as any
            );
            const refs = this.collectRefsFromPreset(applied as any);
            refs.forEach(ref => this.globalReprs.add(ref));
        } else {
            const update = this.plugin.state.data.build();
            const reprType = msg.representation ?? "cartoon";
            const repr = this.plugin.builders.structure.representation.buildRepresentation(
                update,
                { ref: structureRef } as any,
                { type: reprType as any, typeParams: (msg.params ?? {}) as any },
                { tag: "global" }
            );
            await update.commit({ revertOnError: false });
            if (repr?.ref) this.globalReprs.add(repr.ref);
        }
        await this.handleShowHideGlobal(false);
    }

    async showGlobal(msg: ShowGlobalMessage) {
        await this.handleShowHideGlobal(false, msg.target ?? "global");
    }

    async hideGlobal(msg: HideGlobalMessage) {
        await this.handleShowHideGlobal(true, msg.target ?? "global");
    }

    async zoom(msg: ZoomMessage) {
        const structure = this.callbacks.getStructure();
        if (!structure) {
            this.pendingZoom = msg;
            return;
        }

        const atomIndices = Array.isArray(msg.atom_indices)
            ? msg.atom_indices.map(i => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter(i => Number.isFinite(i))
            : [];
        if (atomIndices.length === 0) {
            console.warn("[MolSysViewer] zoom called with empty atom_indices");
            return;
        }

        const selection = this.buildSelectionFromAtomIndices(structure, atomIndices);
        if (!selection) return;

        const loci = StructureSelection.toLociWithSourceUnits(selection);
        this.plugin.managers.camera.focusLoci(loci, {
            durationMs: msg.options?.duration_ms,
            extraRadius: msg.options?.extra_radius,
            minRadius: msg.options?.min_radius,
        });
    }

    // Public method to be called by Loader/Controller when structure is ready
    async onStructureLoaded() {
        if (this.pendingVisibility) {
            const pending = this.pendingVisibility;
            this.pendingVisibility = void 0;
            await this.updateVisibility(pending);
        }
        if (this.pendingZoom) {
            const pending = this.pendingZoom;
            this.pendingZoom = void 0;
            await this.zoom(pending);
        }
        if (this.pendingGlobalOps.length) {
            const ops = [...this.pendingGlobalOps];
            this.pendingGlobalOps.length = 0;
            ops.forEach(op => void this.handleShowHideGlobal(op.hide, op.target));
        }
        if (this.pendingRegions.length) {
            const queued = [...this.pendingRegions];
            this.pendingRegions.length = 0;
            for (const msg of queued) {
                await this.createRegion(msg);
            }
        }
        if (this.globalReprs.size === 0) {
            await this.ensureDefaultGlobalRepresentation();
        }
        if (this.requestedGlobalHidden !== null) {
            await this.handleShowHideGlobal(this.requestedGlobalHidden, "global");
        }
    }

    async clearState() {
        if (this.tagIndex.size > 0) {
            await Promise.all(Array.from(this.tagIndex.values()).flatMap(set => Array.from(set)).map(ref => this.removeStateObject(ref)));
            this.tagIndex.clear();
        }
        this.regionIndex.clear();
        this.layerMeta.clear();
        if (this.globalReprs.size > 0) {
            await Promise.all(Array.from(this.globalReprs).map(ref => this.removeStateObject(ref)));
            this.globalReprs.clear();
        }
    }

    async clearShapesByTag(tag?: string) {
        if (!tag) {
            if (this.tagIndex.size > 0) {
                const allRefs = Array.from(this.tagIndex.values()).flatMap(set => Array.from(set));
                await Promise.all(allRefs.map(ref => this.removeStateObject(ref)));
                this.tagIndex.clear();
            }
            return;
        }
        const refs = this.tagIndex.get(tag);
        if (!refs || refs.size === 0) return;
        await Promise.all(Array.from(refs).map(ref => this.removeStateObject(ref)));
        this.tagIndex.delete(tag);
    }

    private async handleShowHideGlobal(hide: boolean, target: "global" | "all" = "global") {
        if (target === "global") {
            this.requestedGlobalHidden = hide;
        }
        if (!this.callbacks.getStructure()) {
            this.pendingGlobalOps.push({ hide, target });
            return;
        }
        const refs: StateObjectRef[] = [];
        const baselineRefs: StateObjectRef[] = [];
        const hierarchy = this.plugin.managers.structure.hierarchy.current;
        const structures = hierarchy?.structures ?? [];

        const regionReprRefs = new Set<string>();
        const hiddenRegionReprRefs = new Set<string>();
        this.regionIndex.forEach(entry => entry.representations.forEach(ref => {
            regionReprRefs.add(ref as any);
            if (entry.hidden) hiddenRegionReprRefs.add(ref as any);
        }));

        if (target === "global") {
            this.globalReprs.forEach(ref => {
                refs.push(ref);
                baselineRefs.push(ref);
            });
            structures.forEach(s => {
                (s.representations ?? []).forEach(r => {
                    if (!regionReprRefs.has(r.cell.transform.ref)) {
                        refs.push(r.cell.transform.ref);
                        baselineRefs.push(r.cell.transform.ref);
                    }
                });
                (s.components ?? []).forEach(c =>
                    (c.representations ?? []).forEach(r => {
                        if (!regionReprRefs.has(r.cell.transform.ref)) {
                            refs.push(r.cell.transform.ref);
                            baselineRefs.push(r.cell.transform.ref);
                        }
                    })
                );
            });
            if (refs.length === 0) {
                await this.ensureDefaultGlobalRepresentation();
                this.globalReprs.forEach(ref => {
                    refs.push(ref);
                    baselineRefs.push(ref);
                });
            }
        } else {
            structures.forEach(s => {
                (s.representations ?? []).forEach(r => {
                    if (hiddenRegionReprRefs.has(r.cell.transform.ref)) return;
                    refs.push(r.cell.transform.ref);
                });
                (s.components ?? []).forEach(c => (c.representations ?? []).forEach(r => {
                    if (hiddenRegionReprRefs.has(r.cell.transform.ref)) return;
                    refs.push(r.cell.transform.ref);
                }));
            });
            this.globalReprs.forEach(ref => refs.push(ref));
            this.tagIndex.forEach(set => set.forEach(ref => refs.push(ref)));
            
            this.globalReprs.forEach(ref => baselineRefs.push(ref));
            structures.forEach(s => {
                (s.representations ?? []).forEach(r => {
                    if (!regionReprRefs.has(r.cell.transform.ref)) baselineRefs.push(r.cell.transform.ref);
                });
                (s.components ?? []).forEach(c =>
                    (c.representations ?? []).forEach(r => {
                        if (!regionReprRefs.has(r.cell.transform.ref)) baselineRefs.push(r.cell.transform.ref);
                    })
                );
            });
        }

        if (refs.length === 0) return;
        refs.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, hide));

        if (target === "all" && !hide && this.requestedGlobalHidden) {
            if (baselineRefs.length === 0) {
                await this.ensureDefaultGlobalRepresentation();
                this.globalReprs.forEach(ref => baselineRefs.push(ref));
            }
            if (baselineRefs.length) {
                baselineRefs.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, true));
            } else {
                this.pendingGlobalOps.push({ hide: true, target: "global" });
            }
        }
    }

    private async toggleRegionVisibility(tag: string | undefined, hide: boolean) {
        const regionTag = tag ?? "region";
        const entry = this.regionIndex.get(regionTag);
        if (!entry || entry.representations.length === 0) return;
        entry.hidden = hide;
        entry.representations.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, hide));
    }

    private async toggleLayerVisibility(tag: string | undefined, hide: boolean) {
        const layerTag = tag ?? "layer";
        const kind = this.layerMeta.get(layerTag)?.kind;
        if ((kind === "annotation" || kind === "measurement") && this.callbacks.setManagedLayerVisibility) {
            const handled = await this.callbacks.setManagedLayerVisibility(layerTag, kind, !hide);
            if (handled) {
                this.pendingLayerVisibility.delete(layerTag);
                return;
            }
        }
        const refs = this.tagIndex.get(layerTag);
        if (!refs || refs.size === 0) {
            this.pendingLayerVisibility.set(layerTag, hide);
            return;
        }
        this.pendingLayerVisibility.delete(layerTag);
        refs.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, hide));
    }

    private async ensureDefaultGlobalRepresentation() {
        const structureRef = this.callbacks.getLoadedStructure()?.structure;
        if (!structureRef || this.globalReprs.size > 0) return;
        try {
            const applied = await this.plugin.builders.structure.representation.applyPreset(
                { ref: structureRef } as any,
                "auto" as any,
                {}
            );
            const refs = this.collectRefsFromPreset(applied as any);
            refs.forEach(ref => this.globalReprs.add(ref));

            if (this.globalReprs.size === 0) {
                const repr = await this.plugin.builders.structure.representation.addRepresentation(
                    structureRef as any,
                    { type: "cartoon" as any },
                    { tag: "global" }
                );
                if (repr?.ref) this.globalReprs.add(repr.ref);
            }
            if (this.requestedGlobalHidden) {
                this.globalReprs.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, true));
            }
        } catch (err) {
            console.warn("[MolSysViewer] default global representation failed", err);
        }
    }

    private buildSelectionFromAtomIndices(structure: Structure, atomIndices: number[]) {
        if (!Array.isArray(atomIndices) || atomIndices.length === 0) return void 0;
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

        return added ? selectionBuilder.getSelection() : void 0;
    }

    private collectRefsFromPreset(result?: { representations?: { [name: string]: StateObjectSelector | undefined } }) {
        const refs: StateObjectRef[] = [];
        if (!result?.representations) return refs;
        Object.values(result.representations).forEach(sel => {
            if (sel?.ref) refs.push(sel.ref);
        });
        return refs;
    }

    private async removeStateObject(ref?: StateObjectRef) {
        if (!ref) return;
        await PluginCommands.State.RemoveObject(this.plugin, {
            state: this.plugin.state.data,
            ref,
            removeParentGhosts: true,
        });
    }
}
