import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef, StateObjectSelector, StateSelection, StateTransform } from "molstar/lib/mol-state";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { Loci, isEmptyLoci } from "molstar/lib/mol-model/loci";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { setSubtreeVisibility } from "molstar/lib/mol-plugin/behavior/static/state";
import { PresetStructureRepresentations } from "molstar/lib/mol-plugin-state/builder/structure/representation-preset";
import { createStructureRepresentationParams } from "molstar/lib/mol-plugin-state/helpers/structure-representation-params";
import { Transparency } from "molstar/lib/mol-theme/transparency";
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
    HideWholeMessage,
    HideLayerMessage,
    HideRegionMessage,
    SetAtomColorsMessage,
    SetWholeRepresentationMessage,
    SetFocusFadeMessage,
    SetLayerTagMessage,
    SetRegionRepresentationMessage,
    SetRegionOrderMessage,
    SetRegionsVisibilityMessage,
    SetRegionSummariesMessage,
    SetDynamicRegionAtomsMessage,
    BatchRegionOperationsMessage,
    ShowWholeMessage,
    ShowLayerMessage,
    ShowRegionMessage,
    UpdateVisibilityMessage,
    UpdateVisibilityDeltaMessage,
    ZoomMessage,
} from "../../messages/viewer-messages";
import { LoadedStructure } from "../../plugin/structure";
import {
    clearPerAtomColorsFor,
    clearPerAtomColors,
    hasPerAtomColors,
    MsvPerAtomColorThemeName,
    setPerAtomColors,
} from "../../themes/per-atom-color";

const DEFAULT_GLOBAL_REPRESENTATION = "cartoon";
const TRANSPARENCY_MANAGER_TAG = "transparency-controls";
type RegionRepresentationState = "none" | "inherit" | "own";

interface RegionEntry {
    component?: StateObjectRef;
    representations: StateTransform.Ref[];
    atomIndices: number[];
    selection?: string;
    hidden?: boolean;
    representationState: RegionRepresentationState;
    representation?: string;
    preset?: string;
    userPreset?: any;
    params: Record<string, unknown>;
    order: number;
}

export interface RegionSummary {
    tag: string;
    atom_indices: number[];
    atom_count: number;
    selection?: string;
    hidden: boolean;
    /** Tag of the layer this region belongs to, or null (Phase 9). */
    layer?: string | null;
    representation?: string;
    preset?: string;
    representation_params: Record<string, unknown>;
    overlap_tags: string[];
    available_attributes: string[];
    mode?: "static" | "dynamic";
    frame_dependent?: boolean;
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
    private readonly pendingGlobalOps: Array<{ hide: boolean; target: "whole" | "all" }> = [];
    private readonly pendingLayerVisibility = new Map<string, boolean>();
    private readonly pendingRegions: CreateRegionMessage[] = [];
    private regionStyleOptions = { representations: [] as string[], presets: [] as string[] };
    private pendingVisibility?: number[];
    private focusFadeIndices?: number[];
    private focusFadeValue = 0;
    private showOnlyRegionTag?: string;
    private transparencyInitialized = false;
    private previousUserHiddenKey = "";
    private previousFadedKey = "";
    private previousFocusFadeValue = 0;
    private previousShowOnlyWholeMask = false;
    private previousRegionOwnershipKey = "";
    private previousOwnedOpaqueIndices = new Set<number>();
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

    private componentRefId(component: StructureComponentRef): string | undefined {
        return (
            (component as any)?.cell?.transform?.ref
            ?? (component as any)?.transform?.ref
            ?? (component as any)?.ref
        );
    }

    private getRegionComponentRefs(): Set<string> {
        const refs = new Set<string>();
        this.regionIndex.forEach(entry => {
            const ref = StateObjectRef.resolveRef(entry.component);
            if (ref) refs.add(ref);
        });
        return refs;
    }

    private splitComponentsByRegionOwnership(): {
        all: StructureComponentRef[];
        whole: StructureComponentRef[];
        regions: StructureComponentRef[];
    } {
        const all = this.callbacks.getComponents();
        const regionRefs = this.getRegionComponentRefs();
        const whole: StructureComponentRef[] = [];
        const regions: StructureComponentRef[] = [];
        for (const component of all) {
            const ref = this.componentRefId(component);
            if (ref && regionRefs.has(ref)) {
                regions.push(component);
            } else {
                whole.push(component);
            }
        }
        return { all, whole, regions };
    }

    private componentForRegionEntry(entry: RegionEntry, components: StructureComponentRef[]): StructureComponentRef[] {
        const entryRef = StateObjectRef.resolveRef(entry.component);
        if (!entryRef) return [];
        return components.filter(component => this.componentRefId(component) === entryRef);
    }

    private allAtomIndices(structure: Structure): number[] {
        const indices: number[] = [];
        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elementCount = OrderedSet.size(unit.elements);
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                indices.push(OrderedSet.getAt(unit.elements, ordinal));
            }
        }
        return indices;
    }

    private hiddenAtomIndicesFromUserMask(structure: Structure): number[] | undefined {
        const indices = this.currentVisibleIndices;
        if (!Array.isArray(indices)) return undefined;
        if (indices.length === 0) return this.allAtomIndices(structure);
        const visibleSet = new Set(indices);
        return this.allAtomIndices(structure).filter(index => !visibleSet.has(index));
    }

    private unionAtomIndices(...sets: Array<number[] | undefined>): number[] {
        const union = new Set<number>();
        for (const values of sets) {
            for (const value of values ?? []) union.add(value);
        }
        return Array.from(union).sort((a, b) => a - b);
    }

    private atomIndexKey(indices: number[] | undefined): string {
        return Array.isArray(indices) && indices.length > 0 ? indices.join(",") : "";
    }

    private complementAtomIndices(structure: Structure, indices: number[] | undefined): number[] | undefined {
        if (!Array.isArray(indices) || indices.length === 0) return undefined;
        const keep = new Set(indices);
        return this.allAtomIndices(structure).filter(index => !keep.has(index));
    }

    private isFullyOpaque(params: Record<string, unknown> | undefined): boolean {
        const alpha = params?.alpha;
        return alpha === undefined || alpha === null || Number(alpha) === 1;
    }

    private ownedOpaqueAtomIndices(): number[] {
        const owned = new Set<number>();
        for (const entry of this.ownedOpaqueRegionEntries()) {
            for (const index of entry.atomIndices) owned.add(index);
        }
        return Array.from(owned).sort((a, b) => a - b);
    }

    private ownedOpaqueRegionEntries(): RegionEntry[] {
        return Array.from(this.regionIndex.values())
            .filter(entry =>
                !entry.hidden
                && entry.representationState !== "none"
                && this.isFullyOpaque(entry.params)
            )
            .sort((left, right) => left.order - right.order);
    }

    private regionOwnedByHigherOrderAtomIndices(entry: RegionEntry): number[] {
        const masked = new Set<number>();
        for (const owner of this.ownedOpaqueRegionEntries()) {
            if (owner === entry) continue;
            if (owner.order <= entry.order) continue;
            for (const index of owner.atomIndices) masked.add(index);
        }
        if (masked.size === 0) return [];
        const atomSet = new Set(entry.atomIndices);
        return Array.from(masked)
            .filter(index => atomSet.has(index))
            .sort((a, b) => a - b);
    }

    private regionOwnershipKey(): string {
        return Array.from(this.regionIndex.entries())
            .map(([tag, entry]) => `${tag}:${entry.order}:${this.regionOwnedByHigherOrderAtomIndices(entry).join(",")}`)
            .join("|");
    }

    private async applyTransparencyLayer(
        components: StructureComponentRef[],
        atomIndices: number[] | undefined,
        value: number,
    ) {
        const structure = this.callbacks.getStructure();
        if (!structure || components.length === 0 || !Array.isArray(atomIndices) || atomIndices.length === 0) return;
        const selection = this.buildSelectionFromAtomIndices(structure, atomIndices);
        if (!selection || StructureSelection.isEmpty(selection)) return;
        const loci = StructureSelection.toLociWithSourceUnits(selection);
        await setStructureTransparency(this.plugin, components, value, async () => loci);
    }

    private currentGlobalRepresentationRefs(): StateTransform.Ref[] {
        const refs: StateTransform.Ref[] = [];
        this.globalReprs.forEach(ref => {
            const resolved = StateObjectRef.resolveRef(ref);
            if (resolved && this.plugin.state.data.cells.has(resolved)) refs.push(resolved);
        });
        return refs;
    }

    private filteredTransparencyBundle(layers: Array<{ bundle: StructureElement.Bundle; value: number }>, structure: Structure) {
        const transparency = Transparency.ofBundle(layers, structure.root) as Transparency<StructureElement.Loci>;
        const merged = Transparency.merge(transparency) as Transparency<StructureElement.Loci>;
        const filtered = Transparency.filter(merged, structure) as Transparency<StructureElement.Loci>;
        return Transparency.toBundle(filtered);
    }

    private async applyTransparencyToRepresentationRefs(
        refs: StateTransform.Ref[],
        atomIndices: number[] | undefined,
        value: number,
    ) {
        const rootStructure = this.callbacks.getStructure();
        if (!rootStructure || refs.length === 0 || !Array.isArray(atomIndices) || atomIndices.length === 0) return;
        const selection = this.buildSelectionFromAtomIndices(rootStructure, atomIndices);
        if (!selection || StructureSelection.isEmpty(selection)) return;
        const loci = StructureSelection.toLociWithSourceUnits(selection);
        if (Loci.isEmpty(loci) || isEmptyLoci(loci)) return;
        const layer = {
            bundle: StructureElement.Bundle.fromLoci(loci),
            value,
        };
        const state = this.plugin.state.data;
        const update = state.build();
        for (const ref of refs) {
            const reprCell = state.cells.get(ref);
            const reprStructure = (reprCell?.obj?.data?.sourceData as Structure | undefined) ?? rootStructure;
            const transparencyCell = state.select(
                StateSelection.Generators
                    .ofTransformer(StateTransforms.Representation.TransparencyStructureRepresentation3DFromBundle, ref)
                    .withTag(TRANSPARENCY_MANAGER_TAG),
            )[0];
            if (transparencyCell) {
                const existingLayers = transparencyCell.params?.values.layers ?? [];
                const layers = [...existingLayers, layer];
                update.to(transparencyCell).update(this.filteredTransparencyBundle(layers, reprStructure));
            } else {
                update.to(ref).apply(
                    StateTransforms.Representation.TransparencyStructureRepresentation3DFromBundle,
                    this.filteredTransparencyBundle([layer], reprStructure),
                    { tags: TRANSPARENCY_MANAGER_TAG },
                );
            }
        }
        await update.commit({ doNotUpdateCurrent: true });
    }

    private async clearTransparencyFromRepresentationRefs(refs: StateTransform.Ref[]) {
        if (refs.length === 0) return;
        const state = this.plugin.state.data;
        const update = state.build();
        for (const ref of refs) {
            const transparencyCell = state.select(
                StateSelection.Generators
                    .ofTransformer(StateTransforms.Representation.TransparencyStructureRepresentation3DFromBundle, ref)
                    .withTag(TRANSPARENCY_MANAGER_TAG),
            )[0];
            if (transparencyCell) update.delete(transparencyCell.transform.ref);
        }
        await update.commit({ doNotUpdateCurrent: true });
    }

    private async applyWholeTransparencyLayer(
        wholeComponents: StructureComponentRef[],
        atomIndices: number[] | undefined,
        value: number,
    ) {
        const globalRefs = this.currentGlobalRepresentationRefs();
        if (globalRefs.length > 0) {
            await this.applyTransparencyToRepresentationRefs(globalRefs, atomIndices, value);
        } else {
            await this.applyTransparencyLayer(wholeComponents, atomIndices, value);
        }
    }

    private async applyComposedTransparency() {
        const structure = this.callbacks.getStructure();
        if (!structure) return;
        const { all, whole, regions } = this.splitComponentsByRegionOwnership();
        if (all.length === 0) return;

        const userHidden = this.hiddenAtomIndicesFromUserMask(structure);
        const faded = this.focusFadeValue > 0
            ? this.complementAtomIndices(structure, this.focusFadeIndices)
            : undefined;
        const ownedOpaque = this.ownedOpaqueAtomIndices();
        const regionOwnershipKey = this.regionOwnershipKey();
        const showOnlyWholeMaskActive = !!this.showOnlyRegionTag;
        const showOnlyWholeMask = showOnlyWholeMaskActive ? this.allAtomIndices(structure) : undefined;
        const wholeHidden = this.unionAtomIndices(userHidden, this.ownedOpaqueAtomIndices(), showOnlyWholeMask);

        const userHiddenKey = this.atomIndexKey(userHidden);
        const fadedKey = this.atomIndexKey(faded);
        const requiresFullRebuild =
            !this.transparencyInitialized
            || userHiddenKey !== this.previousUserHiddenKey
            || fadedKey !== this.previousFadedKey
            || this.focusFadeValue !== this.previousFocusFadeValue
            || showOnlyWholeMaskActive !== this.previousShowOnlyWholeMask
            || regionOwnershipKey !== this.previousRegionOwnershipKey;

        if (requiresFullRebuild) {
            await clearStructureTransparency(this.plugin, all);
            await this.clearTransparencyFromRepresentationRefs(this.currentGlobalRepresentationRefs());

            for (const entry of this.regionIndex.values()) {
                const components = this.componentForRegionEntry(entry, regions);
                if (components.length === 0) continue;
                const regionHidden = this.unionAtomIndices(userHidden, this.regionOwnedByHigherOrderAtomIndices(entry));
                if (regionHidden.length > 0) {
                    await this.applyTransparencyLayer(components, regionHidden, 1);
                }
            }
            if (Array.isArray(faded) && faded.length > 0) {
                await this.applyWholeTransparencyLayer(whole, faded, Math.min(1, this.focusFadeValue));
            }
            if (wholeHidden.length > 0) {
                await this.applyWholeTransparencyLayer(whole, wholeHidden, 1);
            }
        } else {
            const previousOwned = this.previousOwnedOpaqueIndices;
            const nextOwned = new Set(ownedOpaque);
            const userHiddenSet = new Set(userHidden ?? []);
            const fadedSet = new Set(faded ?? []);
            const added = ownedOpaque.filter(index => !previousOwned.has(index));
            const removed = Array.from(previousOwned).filter(index => !nextOwned.has(index));

            if (added.length > 0) {
                await this.applyWholeTransparencyLayer(whole, added, 1);
            }

            if (!showOnlyWholeMaskActive && removed.length > 0) {
                const fadedReleased: number[] = [];
                const clearReleased: number[] = [];
                for (const index of removed) {
                    if (userHiddenSet.has(index)) continue;
                    if (fadedSet.has(index)) {
                        fadedReleased.push(index);
                    } else {
                        clearReleased.push(index);
                    }
                }
                if (fadedReleased.length > 0) {
                    await this.applyWholeTransparencyLayer(whole, fadedReleased, Math.min(1, this.focusFadeValue));
                }
                if (clearReleased.length > 0) {
                    await this.applyWholeTransparencyLayer(whole, clearReleased, 0);
                }
            }
        }

        this.transparencyInitialized = true;
        this.previousUserHiddenKey = userHiddenKey;
        this.previousFadedKey = fadedKey;
        this.previousFocusFadeValue = this.focusFadeValue;
        this.previousShowOnlyWholeMask = showOnlyWholeMaskActive;
        this.previousRegionOwnershipKey = regionOwnershipKey;
        this.previousOwnedOpaqueIndices = new Set(ownedOpaque);
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
        await this.applyComposedTransparency();
    }

    async setFocusFade(msg: SetFocusFadeMessage) {
        // Soft spotlight: fade everything *outside* focus_atom_indices to a
        // partial transparency (the buried-feature focus, e.g. for voids).
        const structure = this.callbacks.getStructure();
        if (!structure) return;

        const indices = msg.options?.focus_atom_indices;
        const fade = msg.options?.fade ?? 0;
        this.focusFadeIndices = Array.isArray(indices) && indices.length > 0 ? indices : undefined;
        this.focusFadeValue = fade > 0 ? fade : 0;
        await this.applyComposedTransparency();
    }

    private regionStateFromMessage(
        msg: CreateRegionMessage | SetRegionRepresentationMessage,
    ): RegionRepresentationState {
        if (msg.user_preset || msg.preset) return "own";
        if (msg.representation === "inherit") return "inherit";
        if (typeof msg.representation === "string" && msg.representation.trim() !== "") return "own";
        return "none";
    }

    private async addTypedRegionRepresentation(
        componentRef: StateObjectRef,
        tag: string,
        reprType: string,
        params: Record<string, unknown> | undefined,
    ): Promise<StateTransform.Ref[]> {
        const structuralColor = this.getStructuralColorThemeFromParams(reprType, params);
        const cleanParams = this.omitStructuralColorKeys(params);
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
        return repr?.ref ? [repr.ref] : [];
    }

    private async addOwnRegionRepresentations(
        componentRef: StateObjectRef,
        tag: string,
        msg: SetRegionRepresentationMessage | CreateRegionMessage,
    ): Promise<StateTransform.Ref[]> {
        const params = msg.params ?? {};
        const structuralColor = this.getStructuralColorThemeFromParams(
            msg.representation ?? undefined,
            params,
        );
        const cleanParams = this.omitStructuralColorKeys(params);
        const refs: StateTransform.Ref[] = [];

        if ((msg as SetRegionRepresentationMessage).user_preset) {
            const userPreset = (msg as SetRegionRepresentationMessage).user_preset || {};
            const { base, rules } = userPreset;
            if (base) {
                const applied = await this.plugin.builders.structure.representation.applyPreset(
                    { ref: componentRef } as any,
                    base as any,
                    {
                        ...cleanParams,
                        ...(structuralColor.theme ? { theme: structuralColor.theme } : {}),
                    } as any
                );
                refs.push(...this.collectRefsFromPreset(applied as any));
            }
            if (Array.isArray(rules)) {
                for (const rule of rules) {
                    const type = rule?.representation ?? DEFAULT_GLOBAL_REPRESENTATION;
                    refs.push(...await this.addTypedRegionRepresentation(
                        componentRef,
                        tag,
                        type,
                        (rule?.params ?? cleanParams) as Record<string, unknown>,
                    ));
                }
            }
            return refs;
        }

        if ((msg as SetRegionRepresentationMessage).preset) {
            const applied = await this.plugin.builders.structure.representation.applyPreset(
                { ref: componentRef } as any,
                (msg as SetRegionRepresentationMessage).preset as any,
                {
                    ...cleanParams,
                    ...(structuralColor.theme ? { theme: structuralColor.theme } : {}),
                } as any
            );
            refs.push(...this.collectRefsFromPreset(applied as any));
            return refs;
        }

        if (typeof msg.representation === "string" && msg.representation !== "inherit") {
            refs.push(...await this.addTypedRegionRepresentation(componentRef, tag, msg.representation, params));
        }
        return refs;
    }

    /**
     * The concrete representation types the whole is actually drawing, deduped by
     * name, each with the whole's own typeParams. Read from `globalReprs` — the
     * representation refs this handler created for the global view — so an inherit
     * region mirrors what the user sees regardless of whether the whole is on a
     * type, a built-in preset or a user preset. (The whole's reps are not tracked as
     * `StructureComponentRef.representations`, so that path reads empty; `globalReprs`
     * is the authoritative source.)
     */
    private wholeRepresentationTypes(): Array<{ name: string; typeParams: Record<string, unknown> }> {
        const seen = new Set<string>();
        const types: Array<{ name: string; typeParams: Record<string, unknown> }> = [];
        for (const ref of this.globalReprs) {
            const type = (this.plugin.state.data.cells.get(ref)?.transform?.params as any)?.type;
            const name = type?.name;
            if (typeof name !== "string" || name === "" || seen.has(name)) continue;
            seen.add(name);
            types.push({ name, typeParams: (type?.params ?? {}) as Record<string, unknown> });
        }
        return types;
    }

    private async addInheritedRegionRepresentations(
        componentRef: StateObjectRef,
        tag: string,
        params: Record<string, unknown> | undefined,
    ): Promise<StateTransform.Ref[]> {
        // Inherit mirrors the whole's *rendered* representation types via
        // component-level addRepresentation. A structure-level preset (built-in or
        // user) cannot be applied to a region component — Mol* rejects it with
        // "Applying structure repr. provider to bad cell", leaving the region with no
        // representation while ownership still masks the whole, i.e. an invisible hole.
        const inheritedTypes = this.wholeRepresentationTypes();
        const resolved = inheritedTypes.length > 0
            ? inheritedTypes
            : [{ name: DEFAULT_GLOBAL_REPRESENTATION, typeParams: {} }];
        const refs: StateTransform.Ref[] = [];
        for (const { name, typeParams } of resolved) {
            refs.push(...await this.addTypedRegionRepresentation(
                componentRef,
                tag,
                name,
                { ...typeParams, ...(params ?? {}) },
            ));
        }
        return refs;
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
            
            const representationState = this.regionStateFromMessage(msg);
            const representations: StateTransform.Ref[] = [];
            if (representationState === "inherit") {
                representations.push(...await this.addInheritedRegionRepresentations(componentRef, tag, msg.params));
            } else if (representationState === "own") {
                representations.push(...await this.addOwnRegionRepresentations(componentRef, tag, msg));
            }
            
            this.regionIndex.set(tag, {
                component: componentRef,
                representations,
                atomIndices,
                selection: msg.selection,
                hidden: false,
                representationState,
                representation: msg.representation,
                preset: msg.preset,
                userPreset: msg.user_preset,
                params: { ...(msg.params ?? {}) },
                order: typeof msg.order === "number" ? msg.order : 0,
            });
            await this.applyComposedTransparency();
            
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

        let componentRef = StateObjectRef.resolveRef(entry.component);
        if (!componentRef || entry.representations.length > 0) {
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
            componentRef = component.selector?.ref;
            if (!component.selector?.isOk || !componentRef) {
                console.warn("[MolSysViewer] setRegionRepresentation: empty component for", tag);
                return;
            }
            entry.component = componentRef;
        } else {
            entry.representations = [];
        }

        entry.representationState = this.regionStateFromMessage(msg);
        entry.representation = msg.representation;
        entry.preset = msg.preset;
        entry.userPreset = msg.user_preset;
        entry.params = { ...(msg.params ?? {}) };
        if (typeof msg.order === "number") entry.order = msg.order;

        if (entry.representationState === "inherit") {
            entry.representations.push(...await this.addInheritedRegionRepresentations(componentRef, tag, msg.params));
        } else if (entry.representationState === "own") {
            entry.representations.push(...await this.addOwnRegionRepresentations(componentRef, tag, msg));
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
        await this.applyComposedTransparency();
    }

    private async addRepresentationsForRegionEntry(entry: RegionEntry, tag: string, componentRef: StateObjectRef) {
        entry.representations = [];
        if (entry.representationState === "inherit") {
            entry.representations.push(...await this.addInheritedRegionRepresentations(componentRef, tag, entry.params));
        } else if (entry.representationState === "own") {
            entry.representations.push(...await this.addOwnRegionRepresentations(componentRef, tag, {
                op: "set_region_representation",
                tag,
                representation: entry.representation,
                preset: entry.preset,
                user_preset: entry.userPreset,
                params: entry.params,
            }));
        }
    }

    private async updateRegionComponentAtomIndices(tag: string, entry: RegionEntry, atomIndices: number[]) {
        const structure = this.callbacks.getStructure();
        const structureRef = this.callbacks.getLoadedStructure()?.structure;
        if (!structure || !structureRef) return;

        entry.atomIndices = [...atomIndices];
        const selection = this.buildSelectionFromAtomIndices(structure, entry.atomIndices);

        if (!selection) {
            if (entry.component) await this.removeStateObject(entry.component);
            entry.component = undefined;
            entry.representations = [];
            await this.applyComposedTransparency();
            return;
        }

        const bundle = StructureElement.Bundle.fromSelection(selection);
        if (entry.component) {
            const update = this.plugin.state.data.build();
            update.to(entry.component).update({
                type: { name: "bundle", params: bundle },
                nullIfEmpty: true,
                label: tag,
            });
            await update.commit({ doNotUpdateCurrent: true });
        } else {
            const component = this.plugin.state.data.build().to(structureRef).apply(
                StateTransforms.Model.StructureComponent,
                {
                    type: { name: "bundle", params: bundle },
                    nullIfEmpty: true,
                    label: tag,
                },
            );
            await component.commit({ revertOnError: false });
            const componentRef = component.selector.ref;
            if (!component.selector.isOk || !componentRef) return;
            entry.component = componentRef;
            await this.addRepresentationsForRegionEntry(entry, tag, componentRef);
            if (entry.hidden) {
                entry.representations.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, true));
            }
        }
        await this.applyComposedTransparency();
    }

    async setDynamicRegionAtoms(msg: SetDynamicRegionAtomsMessage) {
        const regions = Array.isArray(msg.regions) ? msg.regions : [];
        for (const item of regions) {
            if (typeof item?.tag !== "string") continue;
            const entry = this.regionIndex.get(item.tag);
            if (!entry) continue;
            const atomIndices = Array.isArray(item.atom_indices)
                ? item.atom_indices.map(value => Math.trunc(Number(value))).filter(Number.isFinite)
                : [];
            await this.updateRegionComponentAtomIndices(item.tag, entry, atomIndices);
        }
    }

    async setRegionOrder(msg: SetRegionOrderMessage) {
        const tag = msg.tag ?? "region";
        const entry = this.regionIndex.get(tag);
        if (!entry || typeof msg.order !== "number") return;
        entry.order = msg.order;
        await this.applyComposedTransparency();
    }

    async showRegion(msg: ShowRegionMessage) {
        await this.toggleRegionVisibility(msg.tag, false);
    }

    async showOnlyRegion(msg: ShowRegionMessage) {
        const regionTag = msg.tag ?? "region";
        const entry = this.regionIndex.get(regionTag);
        if (!entry) return;
        this.showOnlyRegionTag = regionTag;
        this.regionIndex.forEach((candidate, tag) => {
            candidate.hidden = tag !== regionTag;
            candidate.representations.forEach(ref =>
                setSubtreeVisibility(this.plugin.state.data, ref, tag !== regionTag)
            );
        });
        await this.applyComposedTransparency();
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
                // Layer membership (Phase 9) must survive the summary mapping,
                // or the Layers subpanel can never group a region under its layer.
                layer: typeof item.layer === "string" ? item.layer : null,
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
                mode: item.mode === "dynamic" ? "dynamic" as const : "static" as const,
                frame_dependent: !!item.frame_dependent,
            }))
            .sort((left, right) => left.tag.localeCompare(right.tag));
    }

    hasFrameDependentDynamicRegions(): boolean {
        return Array.from(this.backendRegionSummaries ?? []).some(region =>
            region.mode === "dynamic" && region.frame_dependent === true
        );
    }

    getRegionStyleOptions(): { representations: string[]; presets: string[] } {
        return {
            representations: [...this.regionStyleOptions.representations],
            presets: [...this.regionStyleOptions.presets],
        };
    }

    hasRegion(tag: string): boolean {
        return this.regionIndex.has(tag);
    }

    isRegionHidden(tag: string): boolean | undefined {
        return this.regionIndex.get(tag)?.hidden;
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
                case "set_region_order":
                    await this.setRegionOrder(operation as unknown as SetRegionOrderMessage);
                    break;
                case "show_region":
                    await this.showRegion(operation as unknown as ShowRegionMessage);
                    break;
                case "show_only_region":
                    await this.showOnlyRegion(operation as unknown as ShowRegionMessage);
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
        if (this.showOnlyRegionTag === tag) this.showOnlyRegionTag = undefined;
        await this.applyComposedTransparency();
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

    async setWholeRepresentation(msg: SetWholeRepresentationMessage) {
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
                const reprType = rule?.representation ?? DEFAULT_GLOBAL_REPRESENTATION;
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
            const reprType = msg.representation ?? DEFAULT_GLOBAL_REPRESENTATION;
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
        await this.repaintInheritedRegions();
        this.transparencyInitialized = false;
        await this.applyComposedTransparency();
    }

    async showWhole(msg: ShowWholeMessage) {
        await this.handleShowHideGlobal(false, msg.target ?? "whole");
    }

    async hideWhole(msg: HideWholeMessage) {
        await this.handleShowHideGlobal(true, msg.target ?? "whole");
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
            await this.handleShowHideGlobal(this.requestedGlobalHidden, "whole");
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
        this.focusFadeIndices = undefined;
        this.focusFadeValue = 0;
        this.showOnlyRegionTag = undefined;
        this.transparencyInitialized = false;
        this.previousUserHiddenKey = "";
        this.previousFadedKey = "";
        this.previousFocusFadeValue = 0;
        this.previousShowOnlyWholeMask = false;
        this.previousRegionOwnershipKey = "";
        this.previousOwnedOpaqueIndices.clear();
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

    private async handleShowHideGlobal(hide: boolean, target: "whole" | "all" = "whole") {
        if (target === "whole") {
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

        if (target === "whole") {
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
                this.pendingGlobalOps.push({ hide: true, target: "whole" });
            }
        }
    }

    private async toggleRegionVisibility(tag: string | undefined, hide: boolean) {
        const regionTag = tag ?? "region";
        const entry = this.regionIndex.get(regionTag);
        if (!entry) return;
        if (this.showOnlyRegionTag && (!hide || regionTag === this.showOnlyRegionTag)) {
            this.showOnlyRegionTag = undefined;
        }
        entry.hidden = hide;
        entry.representations.forEach(ref => setSubtreeVisibility(this.plugin.state.data, ref, hide));
        await this.applyComposedTransparency();
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

    private async repaintInheritedRegions() {
        const inherited = Array.from(this.regionIndex.entries())
            .filter(([, entry]) => entry.representationState === "inherit");
        for (const [tag, entry] of inherited) {
            await this.setRegionRepresentation({
                op: "set_region_representation",
                tag,
                representation: "inherit",
                params: entry.params,
            });
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

    async clearAtomColors(msg: ClearAtomColorsMessage) {
        const atomIndices = Array.isArray(msg.atom_indices) ? msg.atom_indices : undefined;
        if (atomIndices) clearPerAtomColorsFor(atomIndices);
        else clearPerAtomColors();
        await this._applyPerAtomColorTheme();
    }

    private perAtomThemeParamsFromCurrent(colorTheme: any) {
        const current = colorTheme?.name && colorTheme.name !== MsvPerAtomColorThemeName
            ? { name: colorTheme.name, params: colorTheme.params ?? {} }
            : colorTheme?.params?.base;
        return {
            name: MsvPerAtomColorThemeName,
            params: {
                base: current ?? { name: "element-symbol", params: {} },
            },
        };
    }

    private restoreBaseThemeParamsFromCurrent(colorTheme: any) {
        if (colorTheme?.name === MsvPerAtomColorThemeName) {
            return colorTheme.params?.base ?? { name: "element-symbol", params: {} };
        }
        return colorTheme ?? { name: "element-symbol", params: {} };
    }

    private async updateGlobalRepresentationColorThemes(hasColors: boolean) {
        const refs = this.currentGlobalRepresentationRefs();
        if (refs.length === 0) return;
        const update = this.plugin.state.data.build();
        for (const ref of refs) {
            update.to(ref).update(
                StateTransforms.Representation.StructureRepresentation3D,
                (params: any) => {
                    params.colorTheme = hasColors
                        ? this.perAtomThemeParamsFromCurrent(params.colorTheme)
                        : this.restoreBaseThemeParamsFromCurrent(params.colorTheme);
                },
            );
        }
        await update.commit({ doNotUpdateCurrent: true });
    }

    private async _applyPerAtomColorTheme() {
        const components = this.callbacks.getComponents();
        const hasColors = hasPerAtomColors();
        await this.updateGlobalRepresentationColorThemes(hasColors);
        if (components.length === 0) return;
        if (!hasColors) {
            await this.plugin.managers.structure.component.updateRepresentationsTheme(
                components,
                { color: "default" as any },
            );
            return;
        }
        await this.plugin.managers.structure.component.updateRepresentationsTheme(
            components,
            (_component: any, representation: any) => {
                const oldTheme = representation?.cell?.transform?.params?.colorTheme;
                return {
                    color: MsvPerAtomColorThemeName as any,
                    colorParams: this.perAtomThemeParamsFromCurrent(oldTheme).params,
                };
            },
        );
    }
}
