import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef, StateObjectSelector, StateTransform } from "molstar/lib/mol-state";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { setSubtreeVisibility } from "molstar/lib/mol-plugin/behavior/static/state";
import { PresetStructureRepresentations } from "molstar/lib/mol-plugin-state/builder/structure/representation-preset";
import { createStructureRepresentationParams } from "molstar/lib/mol-plugin-state/helpers/structure-representation-params";
import {
    clearStructureTransparency,
    setStructureTransparency,
} from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";

import {
    ClearAtomColorsMessage,
    CreateLayerMessage,
    CreateRegionMessage,
    DeleteLayerMessage,
    DeleteRegionMessage,
    RenameRegionMessage,
    HideGlobalMessage,
    HideLayerMessage,
    HideRegionMessage,
    SetAtomColorsMessage,
    SetGlobalRepresentationMessage,
    SetFocusFadeMessage,
    SetLayerTagMessage,
    SetRegionRepresentationMessage,
    SetRegionsVisibilityMessage,
    SetRegionSummariesMessage,
    BatchRegionOperationsMessage,
    ShowGlobalMessage,
    ShowLayerMessage,
    ShowRegionMessage,
    UpdateVisibilityMessage,
    UpdateVisibilityDeltaMessage,
    ZoomMessage,
} from "../../messages/viewer-messages";
import { LoadedStructure } from "../../plugin/structure";
import {
    clearPerAtomColors,
    MsvPerAtomColorThemeName,
    setPerAtomColors,
} from "../../themes/per-atom-color";

interface RegionEntry {
    component?: StateObjectRef;
    representations: StateTransform.Ref[];
    atomIndices: number[];
    selection?: string;
    hidden?: boolean;
}

export interface RegionSummary {
    tag: string;
    atom_indices: number[];
    atom_count: number;
    selection?: string;
    hidden: boolean;
    representation?: string;
    preset?: string;
    representation_params: Record<string, unknown>;
    overlap_tags: string[];
    available_attributes: string[];
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
    private backendRegionSummaries: RegionSummary[] | null = null;
    private readonly layerMeta = new Map<string, { kind?: string; meta?: Record<string, unknown> }>();
    private readonly tagIndex = new Map<string, Set<StateTransform.Ref>>();
    private readonly globalReprs = new Set<StateTransform.Ref>();
    private readonly pendingGlobalOps: Array<{ hide: boolean; target: "global" | "all" }> = [];
    private readonly pendingLayerVisibility = new Map<string, boolean>();
    private readonly pendingRegions: CreateRegionMessage[] = [];
    private regionStyleOptions = { representations: [] as string[], presets: [] as string[] };
    private pendingVisibility?: number[];
    // Versioned visibility state for the delta protocol: the last applied visible
    // atom indices and the version they were stamped with. A delta only applies
    // when its base_version matches; otherwise we ask the kernel for a full resync.
    private currentVisibleIndices: number[] | null = null;
    private visibilityVersion = 0;
    private requestedGlobalHidden: boolean | null = null;
    private pendingZoom?: ZoomMessage;

    constructor(private plugin: PluginContext, private callbacks: StateCallbacks) {}

    private parseMolstarThemeSpec(
        value: unknown,
    ): { name: string; params: Record<string, unknown> } | undefined {
        if (typeof value === "string" && value.trim() !== "") {
            return { name: value, params: {} };
        }
        if (value && typeof value === "object") {
            const candidate = value as Record<string, unknown>;
            if (typeof candidate.name === "string" && candidate.name.trim() !== "") {
                const params =
                    candidate.params && typeof candidate.params === "object"
                        ? { ...(candidate.params as Record<string, unknown>) }
                        : {};
                return { name: candidate.name, params };
            }
        }
        return undefined;
    }

    private getStructuralColorThemeFromParams(
        reprType: string | undefined,
        params: Record<string, unknown> | undefined,
    ): { color?: string; colorParams?: Record<string, unknown>; theme?: Record<string, unknown> } {
        const scheme = typeof params?.color_scheme === "string" ? params.color_scheme : undefined;
        if (scheme) {
            const mapped = ({
                element_cpk: "element-symbol",
                secondary_structure_default: "secondary-structure",
                chain_default: "chain-id",
                residue_name: "residue-name",
                molecule_type: "molecule-type",
                entity_default: "entity-id",
                illustrative_default: "illustrative",
                physicochemical: "msv-physicochemical",
            } as Record<string, string>)[scheme];
            if (mapped) {
                return {
                    color: mapped,
                    colorParams: {},
                    theme: { globalName: mapped },
                };
            }
        }
        const advanced = this.parseMolstarThemeSpec(params?.molstar_color_theme);
        if (advanced) {
            return {
                color: advanced.name,
                colorParams: advanced.params,
                theme: { globalName: advanced.name, globalColorParams: advanced.params },
            };
        }
        return {};
    }

    private getStructuralSizeThemeFromParams(
        reprType: string | undefined,
        params: Record<string, unknown> | undefined,
    ): { size?: string; sizeParams?: Record<string, unknown> } {
        const scheme = typeof params?.size_scheme === "string" ? params.size_scheme : undefined;
        if (scheme) {
            const mapped = ({
                uniform: "uniform",
                physical: "physical",
                uncertainty: "uncertainty",
            } as Record<string, string>)[scheme];
            if (mapped) {
                return {
                    size: mapped,
                    sizeParams: {},
                };
            }
        }
        const advanced = this.parseMolstarThemeSpec(params?.molstar_size_theme);
        if (advanced) {
            return {
                size: advanced.name,
                sizeParams: advanced.params,
            };
        }
        return {};
    }

    private omitStructuralColorKeys(params: Record<string, unknown> | undefined): Record<string, unknown> {
        if (!params) return {};
        const next = { ...params };
        delete next.color_scheme;
        delete next.size_scheme;
        delete next.molstar_color_theme;
        delete next.molstar_size_theme;
        return next;
    }

    registerTaggedRef(ref?: StateObjectRef, tag?: string, kind: string = "shape") {
        const resolvedRef = StateObjectRef.resolveRef(ref);
        if (!resolvedRef) return;
        if (!tag) return;
        if (!this.tagIndex.has(tag)) this.tagIndex.set(tag, new Set());
        this.tagIndex.get(tag)!.add(resolvedRef);

        if (!this.layerMeta.has(tag)) {
            this.layerMeta.set(tag, { kind, meta: {} });
            this.callbacks.notify({ event: "layer_ack", tag, kind, meta: {} });
        }

        if (this.pendingLayerVisibility.has(tag)) {
            const hide = this.pendingLayerVisibility.get(tag)!;
            this.pendingLayerVisibility.delete(tag);
            setSubtreeVisibility(this.plugin.state.data, resolvedRef, hide);
        }
    }

    registerShapeRef(ref?: StateObjectRef, tag?: string) {
        this.registerTaggedRef(ref, tag, "shape");
    }

    getRegionSummaries(): RegionSummary[] {
        if (this.backendRegionSummaries !== null) {
            return this.backendRegionSummaries.map(item => ({
                ...item,
                atom_indices: [...item.atom_indices],
                overlap_tags: [...item.overlap_tags],
                available_attributes: [...item.available_attributes],
                representation_params: { ...item.representation_params },
            }));
        }
        return Array.from(this.regionIndex.entries())
            .map(([tag, entry]) => ({
                tag,
                atom_indices: [...entry.atomIndices],
                atom_count: entry.atomIndices.length,
                selection: entry.selection,
                hidden: !!entry.hidden,
                representation_params: {},
                overlap_tags: [],
                available_attributes: [],
            }))
            .sort((a, b) => a.tag.localeCompare(b.tag));
    }

    async updateVisibility(msg: UpdateVisibilityMessage | number[] | undefined) {
        const indices = Array.isArray(msg) || msg === undefined ? msg : msg.options?.visible_atom_indices;
        const version = (Array.isArray(msg) || msg === undefined) ? undefined : msg.options?.version;
        if (Array.isArray(indices)) {
            this.currentVisibleIndices = indices;
            if (typeof version === "number") this.visibilityVersion = version;
        }
        await this.applyVisibility(indices);
    }

    async updateVisibilityDelta(msg: UpdateVisibilityDeltaMessage) {
        const opts = msg.options;
        if (!opts) return;
        // Apply only on top of the exact version we currently hold; otherwise the
        // stream drifted (missed/out-of-order message or a bug) and we ask the
        // kernel for the authoritative full state instead of applying blindly.
        if (this.currentVisibleIndices === null || opts.base_version !== this.visibilityVersion) {
            this.callbacks.notify({ event: "request_visibility_resync" });
            return;
        }
        const set = new Set(this.currentVisibleIndices);
        for (const i of opts.shown ?? []) set.add(i);
        for (const i of opts.hidden ?? []) set.delete(i);
        const nextIndices = Array.from(set);
        this.currentVisibleIndices = nextIndices;
        this.visibilityVersion = opts.version;
        await this.applyVisibility(nextIndices);
    }

    private async applyVisibility(indices: number[] | undefined) {
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

    async setFocusFade(msg: SetFocusFadeMessage) {
        // Soft spotlight: fade everything *outside* focus_atom_indices to a
        // partial transparency (the buried-feature focus, e.g. for voids).
        // Same loci construction as updateVisibility, but a partial transparency
        // on the complement instead of fully hiding it.
        const structure = this.callbacks.getStructure();
        if (!structure) return;
        const components = this.callbacks.getComponents();
        if (components.length === 0) return;

        await clearStructureTransparency(this.plugin, components);

        const indices = msg.options?.focus_atom_indices;
        const fade = msg.options?.fade ?? 0;
        if (!Array.isArray(indices) || indices.length === 0 || fade <= 0) return;

        const focusSet = new Set(indices);
        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        let hasFaded = false;

        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elementCount = OrderedSet.size(unit.elements);
            if (elementCount === 0) continue;

            const fadedElements: number[] = [];
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(unit.elements, ordinal);
                if (!focusSet.has(elementIndex)) fadedElements.push(elementIndex);
            }
            if (fadedElements.length === 0) continue;
            hasFaded = true;

            const elementSubset =
                fadedElements.length === elementCount
                    ? unit.elements
                    : (SortedArray.ofSortedArray(fadedElements) as StructureElement.Set);
            const childUnit = unit.getChild(elementSubset);
            const fadedStructure = Structure.create([childUnit], { parent: structure });
            selectionBuilder.add(fadedStructure);
        }

        if (!hasFaded) return;

        const selection = selectionBuilder.getSelection();
        if (StructureSelection.isEmpty(selection)) return;

        const loci = StructureSelection.toLociWithSourceUnits(selection);
        await setStructureTransparency(this.plugin, components, Math.min(1, fade), async () => loci);
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

        const structure = this.callbacks.getStructure();
        const structureRef = this.callbacks.getLoadedStructure()?.structure;
        if (!structure || !structureRef) return;

        // Delete the entire component (cascades to all representation children).
        // Removing only the representation refs with removeParentGhosts:true can
        // silently delete the parent component when it becomes empty, leaving
        // entry.component pointing at a dangling ref that subsequent addRepresentation
        // calls fail against with revertOnError:false — the region then vanishes.
        await this.removeStateObject(entry.component);
        entry.component = undefined as any;
        entry.representations = [];

        // Rebuild the component from the stored atom indices.
        const selection = this.buildSelectionFromAtomIndices(structure, entry.atomIndices);
        if (!selection) return;

        const bundle = StructureElement.Bundle.fromSelection(selection);
        const root = this.plugin.state.data.build().to(structureRef);
        const component = root.apply(StateTransforms.Model.StructureComponent, {
            type: { name: "bundle", params: bundle },
            nullIfEmpty: true,
            label: tag,
        });
        await component.commit({ revertOnError: false });
        const componentRef = component.selector?.ref;
        if (!component.selector?.isOk || !componentRef) {
            console.warn("[MolSysViewer] setRegionRepresentation: empty component for", tag);
            return;
        }
        entry.component = componentRef;

        const structuralColor = this.getStructuralColorThemeFromParams(
            msg.representation ?? undefined,
            msg.params,
        );
        const cleanParams = this.omitStructuralColorKeys(msg.params);

        if (msg.user_preset) {
            const { base, rules } = msg.user_preset || {};
            if (base) {
                const applied = await this.plugin.builders.structure.representation.applyPreset(
                    { ref: componentRef } as any,
                    base as any,
                    {
                        ...cleanParams,
                        ...(structuralColor.theme ? { theme: structuralColor.theme } : {}),
                    } as any
                );
                const refs = this.collectRefsFromPreset(applied as any);
                entry.representations.push(...refs);
            }
            if (Array.isArray(rules)) {
                for (const rule of rules) {
                    const type = rule?.representation ?? "cartoon";
                    const repr = await this.plugin.builders.structure.representation.addRepresentation(
                        componentRef as any,
                        {
                            type: type as any,
                            typeParams: (rule?.params ?? cleanParams) as any,
                            ...(structuralColor.color ? { color: structuralColor.color as any } : {}),
                            ...(structuralColor.colorParams ? { colorParams: structuralColor.colorParams as any } : {}),
                        },
                        { tag }
                    );
                    if (repr?.ref) entry.representations.push(repr.ref);
                }
            }
        } else if (msg.preset) {
            const applied = await this.plugin.builders.structure.representation.applyPreset(
                { ref: componentRef } as any,
                msg.preset as any,
                {
                    ...cleanParams,
                    ...(structuralColor.theme ? { theme: structuralColor.theme } : {}),
                } as any
            );
            const refs = this.collectRefsFromPreset(applied as any);
            entry.representations.push(...refs);
        } else {
            const reprType = msg.representation ?? "cartoon";
            const repr = await this.plugin.builders.structure.representation.addRepresentation(
                componentRef as any,
                {
                    type: reprType as any,
                    typeParams: cleanParams as any,
                    ...(structuralColor.color ? { color: structuralColor.color as any } : {}),
                    ...(structuralColor.colorParams ? { colorParams: structuralColor.colorParams as any } : {}),
                },
                { tag }
            );
            if (repr?.ref) entry.representations.push(repr.ref);
        }

        const alpha = msg.params?.alpha;
        if ((msg.preset || msg.user_preset) && typeof alpha === "number") {
            await this.applyAlphaToRepresentations(entry.representations, alpha);
        }

        // Restore visibility state.
        if (entry.hidden) {
            entry.representations.forEach(ref =>
                setSubtreeVisibility(this.plugin.state.data, ref, true)
            );
        }
    }

    async showRegion(msg: ShowRegionMessage) {
        await this.toggleRegionVisibility(msg.tag, false);
    }

    async hideRegion(msg: HideRegionMessage) {
        await this.toggleRegionVisibility(msg.tag, true);
    }

    async setRegionsVisibility(msg: SetRegionsVisibilityMessage) {
        const tags = Array.isArray(msg.tags) ? msg.tags : Array.from(this.regionIndex.keys());
        await Promise.all(tags.map(tag => this.toggleRegionVisibility(tag, !!msg.hidden)));
    }

    setRegionSummaries(msg: SetRegionSummariesMessage) {
        const regions = Array.isArray(msg.regions) ? msg.regions : [];
        this.regionStyleOptions = {
            representations: Array.isArray(msg.representations)
                ? msg.representations.filter((value): value is string => typeof value === "string")
                : [],
            presets: Array.isArray(msg.presets)
                ? msg.presets.filter((value): value is string => typeof value === "string")
                : [],
        };
        this.backendRegionSummaries = regions
            .filter(item => typeof item?.tag === "string")
            .map(item => ({
                tag: item.tag,
                atom_indices: Array.isArray(item.atom_indices)
                    ? item.atom_indices.filter((value): value is number => typeof value === "number")
                    : [],
                atom_count: typeof item.atom_count === "number"
                    ? item.atom_count
                    : Array.isArray(item.atom_indices) ? item.atom_indices.length : 0,
                selection: typeof item.selection === "string" ? item.selection : undefined,
                hidden: !!item.hidden,
                representation: typeof item.representation === "string" ? item.representation : undefined,
                preset: typeof item.preset === "string" ? item.preset : undefined,
                representation_params: item.representation_params && typeof item.representation_params === "object"
                    ? { ...item.representation_params }
                    : {},
                overlap_tags: Array.isArray(item.overlap_tags)
                    ? item.overlap_tags.filter((value): value is string => typeof value === "string")
                    : [],
                available_attributes: Array.isArray(item.available_attributes)
                    ? item.available_attributes.filter((value): value is string => typeof value === "string")
                    : [],
            }))
            .sort((left, right) => left.tag.localeCompare(right.tag));
    }

    getRegionStyleOptions(): { representations: string[]; presets: string[] } {
        return {
            representations: [...this.regionStyleOptions.representations],
            presets: [...this.regionStyleOptions.presets],
        };
    }

    async applyRegionOperations(msg: BatchRegionOperationsMessage) {
        const operations = Array.isArray(msg.operations) ? msg.operations : [];
        for (const operation of operations) {
            switch (operation.op) {
                case "create_region":
                    await this.createRegion(operation as unknown as CreateRegionMessage);
                    break;
                case "set_region_representation":
                    await this.setRegionRepresentation(operation as unknown as SetRegionRepresentationMessage);
                    break;
                case "show_region":
                    await this.showRegion(operation as unknown as ShowRegionMessage);
                    break;
                case "hide_region":
                    await this.hideRegion(operation as unknown as HideRegionMessage);
                    break;
                default:
                    console.warn("[MolSysViewer] unsupported batched region op:", operation.op);
                    break;
            }
        }
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

    async renameRegion(msg: RenameRegionMessage) {
        const oldTag = msg.tag ?? "region";
        const newTag = msg.new_tag;
        if (!newTag || oldTag === newTag) return;
        const entry = this.regionIndex.get(oldTag);
        if (!entry) return;
        this.regionIndex.delete(oldTag);
        this.regionIndex.set(newTag, entry);
        this.callbacks.notify({ event: "region_renamed", tag: oldTag, new_tag: newTag });
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

        // Preserve camera state: removing then re-adding representations can trigger
        // Mol*-internal camera adjustments that leave the orbit minRadius too small,
        // preventing the user from zooming back out.
        const cameraSnap = this.plugin.canvas3d?.camera.getSnapshot?.();

        const structure = this.callbacks.getStructure();
        const structuralColor = this.getStructuralColorThemeFromParams(
            msg.representation ?? undefined,
            msg.params,
        );
        const structuralSize = this.getStructuralSizeThemeFromParams(
            msg.representation ?? undefined,
            msg.params,
        );
        const cleanParams = this.omitStructuralColorKeys(msg.params);

        const refsToClear = this.collectBaselineGlobalRepresentationRefs();
        if (refsToClear.length > 0) {
            await Promise.all(refsToClear.map(ref => this.removeStateObject(ref)));
        }
        this.globalReprs.clear();
        if (msg.user_preset) {
            const userPreset = msg.user_preset || {};
            const base = userPreset.base as string | undefined;
            const rules = Array.isArray(userPreset.rules) ? userPreset.rules : [];
            if (base) {
                const applied = await this.plugin.builders.structure.representation.applyPreset(
                    { ref: structureRef } as any,
                    base as any,
                    { ...cleanParams, ...(structuralColor.theme ? { theme: structuralColor.theme } : {}) } as any
                );
                const refs = this.collectRefsFromPreset(applied as any);
                refs.forEach(ref => this.globalReprs.add(ref));
            }
            for (const rule of rules) {
                const atomIndices = Array.isArray(rule?.atom_indices)
                    ? rule.atom_indices.map((i: number | string) => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter((i: number) => Number.isFinite(i))
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
                        {
                            type: reprType as any,
                            typeParams: (rule?.params ?? {}) as any,
                            ...(structuralColor.color ? { color: structuralColor.color as any } : {}),
                            ...(structuralColor.colorParams ? { colorParams: structuralColor.colorParams as any } : {}),
                            ...(structuralSize.size ? { size: structuralSize.size as any } : {}),
                            ...(structuralSize.sizeParams ? { sizeParams: structuralSize.sizeParams as any } : {}),
                        },
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
                { ...cleanParams, ...(structuralColor.theme ? { theme: structuralColor.theme } : {}) } as any
            );
            const refs = this.collectRefsFromPreset(applied as any);
            refs.forEach(ref => this.globalReprs.add(ref));
        } else {
            const update = this.plugin.state.data.build();
            const reprType = msg.representation ?? "cartoon";
            const reprParams = createStructureRepresentationParams(
                this.plugin,
                structure,
                {
                    type: reprType as any,
                    typeParams: cleanParams as any,
                    ...(structuralColor.color ? { color: structuralColor.color } : {}),
                    ...(structuralColor.colorParams ? { colorParams: structuralColor.colorParams } : {}),
                    ...(structuralSize.size ? { size: structuralSize.size } : {}),
                    ...(structuralSize.sizeParams ? { sizeParams: structuralSize.sizeParams } : {}),
                } as any,
            );
            if (structuralColor.color) {
                (reprParams as any).colorTheme = {
                    name: structuralColor.color,
                    params: structuralColor.colorParams ?? {},
                };
            }
            if (structuralSize.size) {
                (reprParams as any).sizeTheme = {
                    name: structuralSize.size,
                    params: structuralSize.sizeParams ?? {},
                };
            }
            const repr = update.to(structureRef).apply(
                StateTransforms.Representation.StructureRepresentation3D,
                reprParams,
                { tags: "global" }
            );
            await update.commit({ revertOnError: false });
            const reprRef = (repr as any)?.ref ?? (repr as any)?.selector?.ref;
            if (reprRef) this.globalReprs.add(reprRef);
        }
        await this.handleShowHideGlobal(false);

        // Restore camera position after the representation swap.
        if (cameraSnap) {
            try {
                await PluginCommands.Camera.SetSnapshot(this.plugin, {
                    snapshot: cameraSnap,
                    durationMs: 0,
                });
            } catch {
                // Non-fatal: if the snapshot restore fails the user just loses their view.
            }
        }
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
        this.captureInitialGlobalRepresentations();
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
        this.backendRegionSummaries = null;
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
        const refs: StateTransform.Ref[] = [];
        const baselineRefs: StateTransform.Ref[] = [];
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
                (s.components ?? []).forEach(c => (c.representations ?? []).forEach(r => {
                    if (hiddenRegionReprRefs.has(r.cell.transform.ref)) return;
                    refs.push(r.cell.transform.ref);
                }));
            });
            this.globalReprs.forEach(ref => refs.push(ref));
            this.tagIndex.forEach(set => set.forEach(ref => refs.push(ref)));
            
            this.globalReprs.forEach(ref => baselineRefs.push(ref));
            structures.forEach(s => {
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

    private collectBaselineGlobalRepresentationRefs(): StateTransform.Ref[] {
        const refs = new Set<StateTransform.Ref>();
        const hierarchy = this.plugin.managers.structure.hierarchy.current;
        const structures = hierarchy?.structures ?? [];

        const regionReprRefs = new Set<string>();
        this.regionIndex.forEach(entry => entry.representations.forEach(ref => {
            regionReprRefs.add(ref as any);
        }));

        this.globalReprs.forEach(ref => refs.add(ref));
        structures.forEach(s => {
            (s.components ?? []).forEach(c =>
                (c.representations ?? []).forEach(r => {
                    const ref = r.cell.transform.ref;
                    if (!regionReprRefs.has(ref)) refs.add(ref);
                })
            );
        });

        return Array.from(refs);
    }

    private captureInitialGlobalRepresentations() {
        if (this.globalReprs.size > 0) return;
        const refs = this.collectBaselineGlobalRepresentationRefs();
        refs.forEach(ref => this.globalReprs.add(ref));
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
        const refs: StateTransform.Ref[] = [];
        if (!result?.representations) return refs;
        Object.values(result.representations).forEach(sel => {
            if (sel?.ref) refs.push(sel.ref);
        });
        return refs;
    }

    private async applyAlphaToRepresentations(refs: StateTransform.Ref[], alpha: number) {
        if (refs.length === 0) return;
        const update = this.plugin.state.data.build();
        for (const ref of refs) {
            update.to(ref).update(
                StateTransforms.Representation.StructureRepresentation3D,
                (params: any) => {
                    params.type.params.alpha = alpha;
                },
            );
        }
        await update.commit({ doNotUpdateCurrent: true });
    }

    private async removeStateObject(ref?: StateObjectRef) {
        const resolvedRef = StateObjectRef.resolveRef(ref);
        if (!resolvedRef) return;
        if (!this.plugin.state.data.cells.has(resolvedRef)) return;
        await PluginCommands.State.RemoveObject(this.plugin, {
            state: this.plugin.state.data,
            ref: resolvedRef,
            removeParentGhosts: true,
        });
    }

    // ── Per-atom color mapping ─────────────────────────────────────────────

    async setAtomColors(msg: SetAtomColorsMessage) {
        const atomIndices = Array.isArray(msg.atom_indices) ? msg.atom_indices : [];
        const colorInts = Array.isArray(msg.colors) ? msg.colors : [];
        const replace = msg.replace !== false;
        setPerAtomColors(atomIndices, colorInts, replace);
        await this._applyPerAtomColorTheme();
    }

    async clearAtomColors(_msg: ClearAtomColorsMessage) {
        clearPerAtomColors();
        await this._applyPerAtomColorTheme();
    }

    private async _applyPerAtomColorTheme() {
        const components = this.callbacks.getComponents();
        if (components.length === 0) return;
        await this.plugin.managers.structure.component.updateRepresentationsTheme(
            components,
            { color: MsvPerAtomColorThemeName as any },
        );
    }
}
