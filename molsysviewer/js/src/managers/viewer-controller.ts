// src/managers/viewer-controller.ts

import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import {
    StructureComponentRef,
    StructureRef,
} from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import {
    clearStructureTransparency,
    setStructureTransparency,
} from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { StateObjectRef, StateObjectSelector } from "molstar/lib/mol-state";
import { PresetStructureRepresentations } from "molstar/lib/mol-plugin-state/builder/structure/representation-preset";

import {
    addAnisotropyEllipsoidsFromPython,
    addChannelTubeFromPython,
    addDisplacementVectorsFromPython,
    addNetworkLinksFromPython,
    addPharmacophoreFromPython,
    addPocketBlobFromPython,
    addTetrahedraFromPython,
    addTransparentSphereFromPython,
    addTransparentSpheresFromPython,
    addTriangleFacesFromPython,
    AnisotropyEllipsoidOptions,
    ChannelTubeOptions,
    DisplacementVectorOptions,
    NetworkLinkOptions,
    PharmacophoreOptions,
    PocketBlobOptions,
    TetrahedraOptions,
    TransparentSphereSpec,
    TriangleFacesOptions,
} from "../shapes";
import { addPocketSurfaceFromPython, PocketSurfaceOptions } from "../shapes/pocket-surface";
import {
    AddAlphaSphereSetMessage,
    AddAnisotropyEllipsoidsMessage,
    AddChannelTubeMessage,
    AddDisplacementVectorsMessage,
    AddNetworkLinksMessage,
    AddPharmacophoreMessage,
    AddPocketBlobMessage,
    AddPocketSurfaceMessage,
    AddSphereMessage,
    AddTetrahedraMessage,
    AddTriangleFacesMessage,
    ClearAllMessage,
    ClearByTagMessage,
    ClearSceneMessage,
    LoadMolSysPayloadMessage,
    LoadPdbIdMessage,
    LoadStructureFromUrlMessage,
    LoadStructureMessage,
    CreateRegionMessage,
    SetRegionRepresentationMessage,
    ShowRegionMessage,
    HideRegionMessage,
    DeleteRegionMessage,
    CreateLayerMessage,
    ShowLayerMessage,
    HideLayerMessage,
    DeleteLayerMessage,
    SetLayerTagMessage,
    SetGlobalRepresentationMessage,
    ShowGlobalMessage,
    HideGlobalMessage,
    ResetCameraMessage,
    SetTrajectoryFrameMessage,
    SetTrajectoryPlaybackMessage,
    StepTrajectoryMessage,
    ToggleBackgroundMessage,
    ToggleFullscreenMessage,
    ToggleSpinMessage,
    ToggleSwingMessage,
    UpdateVisibilityMessage,
    ViewerMessage,
} from "../messages/viewer-messages";
import {
    LoadedStructure,
    MolSysPayload,
    loadStructureFromMolSysPayload,
    loadStructureFromString,
    loadStructureFromUrl,
} from "../plugin/structure";
import { UpdateTrajectory } from "molstar/lib/mol-plugin-state/actions/structure";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { AnimateModelIndex } from "molstar/lib/mol-plugin-state/animation/built-in/model-index";

interface RegionEntry {
    component?: StateObjectRef;
    representations: StateObjectRef[];
    atomIndices: number[];
    selection?: string;
}

/**
 * Controller that translates Python messages into Mol* actions and manages state refs.
 */
export class MolSysViewerController {
    static async create(target: HTMLElement, notify?: (msg: any) => void): Promise<MolSysViewerController> {
        const canvas = document.createElement("canvas");
        canvas.style.width = "100%";
        canvas.style.height = "100%";
        canvas.style.display = "block";
        target.appendChild(canvas);

        const plugin = new PluginContext(DefaultPluginSpec());
        await plugin.init();

        const init = (plugin as any).initViewerAsync ?? (plugin as any).initViewer;
        let ok = false;
        if (typeof init === "function") {
            const result = init.call(plugin, canvas, target);
            ok = typeof result?.then === "function" ? await result : !!result;
        } else {
            console.error("[MolSysViewer] Plugin init function not found (initViewer/initViewerAsync missing)");
        }
        if (!ok) console.error("[MolSysViewer] Failed to init Mol* viewer");

        return new MolSysViewerController(plugin, target, notify);
    }

    private readonly shapeRefs = new Set<StateObjectRef<SO.Shape.Representation3D>>();
    private readonly tagIndex = new Map<string, Set<StateObjectRef>>();
    private readonly regionIndex = new Map<string, RegionEntry>();
    private readonly layerMeta = new Map<string, { kind?: string; meta?: Record<string, unknown> }>();
    private readonly globalReprs = new Set<StateObjectRef>();
    private readonly pendingRegions: CreateRegionMessage[] = [];
    private currentStructure?: StructureRef;
    private loadedStructure?: LoadedStructure;
    private readonly labelRefs = new Set<StateObjectRef>();
    private swingActive = false;
    private spinActive = false;
    private pendingVisibility?: number[];
    private trajectoryListeners = new Set<(state: TrajectoryState) => void>();
    private trajectoryPoll?: ReturnType<typeof setInterval>;
    private playbackTimer?: ReturnType<typeof setInterval>;
    private savedLightRenderer?: any;
    private savedDarkRenderer?: any;
    private savedLightCamera?: any;
    private savedDarkCamera?: any;
    private darkMode = false;

    private constructor(private readonly plugin: PluginContext, private readonly host: HTMLElement, private readonly notify?: (msg: any) => void) {}

    private registerShapeRef(ref?: StateObjectRef, tag?: string) {
        if (!ref) return;
        this.shapeRefs.add(ref as any);
        if (!tag) return;
        if (!this.tagIndex.has(tag)) this.tagIndex.set(tag, new Set());
        this.tagIndex.get(tag)!.add(ref as any);
        if (!this.layerMeta.has(tag)) {
            this.layerMeta.set(tag, { kind: "shape", meta: {} });
            this.notify?.({ event: "layer_ack", tag, kind: "shape", meta: {} });
        }
    }

    async handleMessage(msg: ViewerMessage) {
        if (!msg || typeof msg !== "object") return;
        if (!("op" in msg)) {
            console.warn("[MolSysViewer] message missing 'op'", msg);
            return;
        }

        try {
            switch (msg.op) {
                case "load_structure_from_string":
                case "load_pdb_string":
                    await this.handleLoadFromString(msg as LoadStructureMessage);
                    break;

                case "load_molsys_payload":
                    await this.handleLoadMolSysPayload(msg as LoadMolSysPayloadMessage);
                    break;

                case "load_structure_from_url":
                    await this.handleLoadFromUrl(msg as LoadStructureFromUrlMessage);
                    break;

                case "load_pdb_id":
                    await this.handleLoadPdbId(msg as LoadPdbIdMessage);
                    break;

                case "add_sphere":
                    await this.handleAddSphere(msg as AddSphereMessage);
                    break;

                case "add_alpha_sphere_set":
                    await this.handleAddAlphaSphereSet(msg as AddAlphaSphereSetMessage);
                    break;

                case "add_pocket_surface":
                    await this.handleAddPocketSurface(msg as AddPocketSurfaceMessage);
                    break;
                case "add_pocket_blob":
                    await this.handleAddPocketBlob(msg as AddPocketBlobMessage);
                    break;
                case "add_channel_tube":
                    await this.handleAddChannelTube(msg as AddChannelTubeMessage);
                    break;
                case "add_anisotropy_ellipsoids":
                    await this.handleAddAnisotropyEllipsoids(msg as AddAnisotropyEllipsoidsMessage);
                    break;
                case "add_pharmacophore_features":
                    await this.handleAddPharmacophore(msg as AddPharmacophoreMessage);
                    break;
                case "add_network_links":
                    await this.handleAddNetworkLinks(msg as AddNetworkLinksMessage);
                    break;
                case "add_displacement_vectors":
                    await this.handleAddDisplacementVectors(msg as AddDisplacementVectorsMessage);
                    break;
                case "add_tetrahedra":
                    await this.handleAddTetrahedra(msg as AddTetrahedraMessage);
                    break;
                case "add_triangle_faces":
                    await this.handleAddTriangleFaces(msg as AddTriangleFacesMessage);
                    break;

                case "update_visibility":
                    await this.handleUpdateVisibility(msg as UpdateVisibilityMessage);
                    break;

                case "reset_view":
                    await this.resetView();
                    break;

                case "clear_scene":
                    await this.clearScene((msg as ClearSceneMessage).options);
                    break;

                case "clear_all":
                    await this.clearAll();
                    break;
                case "clear_shapes_by_tag":
                    await this.clearShapesByTag((msg as ClearByTagMessage).tag);
                    break;
                case "reset_camera":
                    await this.resetView();
                    break;
                case "toggle_fullscreen":
                    await this.toggleFullscreen((msg as ToggleFullscreenMessage).enable);
                    break;
                case "toggle_background":
                    await this.toggleBackground((msg as ToggleBackgroundMessage).mode);
                    break;
                case "toggle_swing":
                    await this.toggleSwing((msg as ToggleSwingMessage).enable);
                    break;
                case "toggle_spin":
                    await this.toggleSpin((msg as ToggleSpinMessage).enable);
                    break;
                case "step_trajectory":
                    await this.handleStepTrajectory(msg as StepTrajectoryMessage);
                    break;
                case "set_trajectory_frame":
                    await this.handleSetTrajectoryFrame(msg as SetTrajectoryFrameMessage);
                    break;
                case "set_trajectory_playback":
                    await this.handleSetTrajectoryPlayback(msg as SetTrajectoryPlaybackMessage);
                    break;
                case "create_region":
                    await this.handleCreateRegion(msg as CreateRegionMessage);
                    break;
                case "set_region_representation":
                    await this.handleSetRegionRepresentation(msg as SetRegionRepresentationMessage);
                    break;
                case "show_region":
                    await this.handleShowHideRegion(msg as ShowRegionMessage, false);
                    break;
                case "hide_region":
                    await this.handleShowHideRegion(msg as HideRegionMessage, true);
                    break;
                case "delete_region":
                    await this.handleDeleteRegion(msg as DeleteRegionMessage);
                    break;
                case "create_layer":
                    await this.handleCreateLayer(msg as CreateLayerMessage);
                    break;
                case "show_layer":
                    await this.handleShowHideLayer(msg as ShowLayerMessage, false);
                    break;
                case "hide_layer":
                    await this.handleShowHideLayer(msg as HideLayerMessage, true);
                    break;
                case "delete_layer":
                    await this.handleDeleteLayer(msg as DeleteLayerMessage);
                    break;
                case "set_layer_tag":
                    await this.handleSetLayerTag(msg as SetLayerTagMessage);
                    break;
                case "set_global_representation":
                    await this.handleSetGlobalRepresentation(msg as SetGlobalRepresentationMessage);
                    break;
                case "show_global":
                    await this.handleShowHideGlobal(false, (msg as ShowGlobalMessage).target ?? "global");
                    break;
                case "hide_global":
                    await this.handleShowHideGlobal(true, (msg as HideGlobalMessage).target ?? "global");
                    break;

                default:
                    console.warn("[MolSysViewer] unknown op:", (msg as any).op, msg);
                    break;
            }
        } catch (error) {
            console.error("[MolSysViewer] Error handling message:", msg, error);
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

    private async handleLoadFromString(msg: LoadStructureMessage) {
        const text = msg.data ?? msg.pdb ?? msg.pdb_text ?? "";
        if (!text || typeof text !== "string") {
            console.warn("[MolSysViewer] load message without data/pdb/pdb_text");
            return;
        }
        const format = msg.format ?? "pdb";
        const label = msg.label ?? "Structure";
        await this.loadFromString(text, format, label);
    }

    private async handleLoadMolSysPayload(msg: LoadMolSysPayloadMessage) {
        if (!msg.payload) {
            console.warn("[MolSysViewer] load_molsys_payload without payload");
            return;
        }
        await this.loadFromMolSysPayload(msg.payload, msg.label);
    }

    private async handleLoadFromUrl(msg: LoadStructureFromUrlMessage) {
        if (!msg.url || typeof msg.url !== "string") {
            console.warn("[MolSysViewer] load_structure_from_url without url");
            return;
        }
        await this.loadFromUrl(msg.url, msg.format, msg.label);
    }

    private async handleLoadPdbId(msg: LoadPdbIdMessage) {
        const pdbId = msg.pdb_id?.trim();
        if (!pdbId) {
            console.warn("[MolSysViewer] load_pdb_id without pdb_id");
            return;
        }
        await this.loadPdbId(pdbId);
    }

    private async handleAddSphere(msg: AddSphereMessage) {
        const options = msg.options ?? {};
        await this.addSphere({
            center: options.center ?? [0, 0, 0],
            radius: options.radius ?? 10,
            color: options.color ?? 0x00ff00,
            alpha: options.alpha ?? 0.4,
        });
    }

    private async handleAddAlphaSphereSet(msg: AddAlphaSphereSetMessage) {
        const options = msg.options;
        if (!options?.alpha_spheres?.centers || !options.alpha_spheres.radii) {
            console.warn("[MolSysViewer] add_alpha_sphere_set missing alpha_spheres");
            return;
        }

        const centers = options.alpha_spheres.centers;
        const radii = options.alpha_spheres.radii;
        if (!Array.isArray(centers) || !Array.isArray(radii) || centers.length !== radii.length || centers.length === 0) {
            console.warn("[MolSysViewer] add_alpha_sphere_set inconsistent data");
            return;
        }

        const alphaColor = options.alpha_spheres.color ?? 0x00ff00;
        const alphaAlpha = options.alpha_spheres.alpha ?? 0.3;
        const alphaSpecs: TransparentSphereSpec[] = centers.map((c, i) => ({
            center: [c[0], c[1], c[2]],
            radius: radii[i],
            color: alphaColor,
            alpha: alphaAlpha,
        }));

        const tag = options.tag ?? "molsysviewer:alpha-spheres";
        const alphaRef = await addTransparentSpheresFromPython(this.plugin, alphaSpecs, alphaAlpha, tag);
        this.registerShapeRef(alphaRef, tag);

        if (options.atom_spheres?.centers && options.atom_spheres.centers.length > 0) {
            const atomRadius = options.atom_spheres.radius ?? 1.0;
            const atomColor = options.atom_spheres.color ?? 0x0000ff;
            const atomAlpha = options.atom_spheres.alpha ?? 0.5;
            const atomSpecs: TransparentSphereSpec[] = options.atom_spheres.centers.map(c => ({
                center: [c[0], c[1], c[2]],
                radius: atomRadius,
                color: atomColor,
                alpha: atomAlpha,
            }));
            const atomRef = await addTransparentSpheresFromPython(this.plugin, atomSpecs, atomAlpha, tag);
            this.registerShapeRef(atomRef, tag);
        }
    }

    private async handleAddPocketSurface(msg: AddPocketSurfaceMessage) {
        const options = msg.options ?? ({} as PocketSurfaceOptions);
        if (!Array.isArray(options.atom_indices) || options.atom_indices.length === 0) {
            console.warn("[MolSysViewer] add_pocket_surface without atom_indices");
            return;
        }
        try {
            const ref = await addPocketSurfaceFromPython(this.plugin, options);
            if (Array.isArray(ref)) {
                ref.forEach(r => this.registerShapeRef(r, options.tag));
            } else {
                this.registerShapeRef(ref, options.tag);
            }
        } catch (err) {
            console.error("[MolSysViewer] Error creando pocket surface", err);
        }
    }

    private async handleAddPocketBlob(msg: AddPocketBlobMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.radii || options.centers.length === 0 || options.radii.length === 0) {
            console.warn("[MolSysViewer] add_pocket_blob without centers or radii");
            return;
        }
        try {
            const ref = await addPocketBlobFromPython(this.plugin, options);
            if (Array.isArray(ref)) {
                ref.forEach(r => this.registerShapeRef(r, options.tag));
            } else {
                this.registerShapeRef(ref, options.tag);
            }
        } catch (err) {
            console.error("[MolSysViewer] Error creando pocket blob", err);
        }
    }

    private async handleAddChannelTube(msg: AddChannelTubeMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.radii || options.centers.length < 2 || options.radii.length < 2) {
            console.warn("[MolSysViewer] add_channel_tube requires at least two centers and radii");
            return;
        }
        try {
            const ref = await addChannelTubeFromPython(this.plugin, options);
            this.registerShapeRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando channel tube", err);
        }
    }

    private async handleAddAnisotropyEllipsoids(msg: AddAnisotropyEllipsoidsMessage) {
        const options = msg.options ?? {};
        if (!options.centers && !options.atom_indices) {
            console.warn("[MolSysViewer] add_anisotropy_ellipsoids requires centers or atom_indices");
            return;
        }
        try {
            const ref = await addAnisotropyEllipsoidsFromPython(this.plugin, options);
            this.registerShapeRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando anisotropy ellipsoids", err);
        }
    }

    private async handleAddPharmacophore(msg: AddPharmacophoreMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.kinds || options.centers.length === 0 || options.kinds.length !== options.centers.length) {
            console.warn("[MolSysViewer] add_pharmacophore_features requires centers and kinds of same length");
            return;
        }
        try {
            const ref = await addPharmacophoreFromPython(this.plugin, options);
            this.registerShapeRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando pharmacophore features", err);
        }
    }

    private async handleAddNetworkLinks(msg: AddNetworkLinksMessage) {
        const options = msg.options ?? {};
        try {
            const ref = await addNetworkLinksFromPython(this.plugin, options);
            this.registerShapeRef(ref as any, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando network links", err);
        }
    }

    private async handleAddDisplacementVectors(msg: AddDisplacementVectorsMessage) {
        const options = msg.options ?? {};
        if (!options.vectors || options.vectors.length === 0) {
            console.warn("[MolSysViewer] add_displacement_vectors without vectors");
            return;
        }
        try {
            const ref = await addDisplacementVectorsFromPython(this.plugin, options);
            this.registerShapeRef(ref as any, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando displacement vectors", err);
        }
    }

    private async handleAddTetrahedra(msg: AddTetrahedraMessage) {
        const options = msg.options ?? {};
        if (!options.tetraCoords && !options.tetra_coords && !options.atomQuads && !options.atom_quads) {
            console.warn("[MolSysViewer] add_tetrahedra without tetraCoords or atom_quads");
            return;
        }
        try {
            const ref = await addTetrahedraFromPython(this.plugin, options);
            this.registerShapeRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando tetrahedra", err);
        }
    }

    private async handleAddTriangleFaces(msg: AddTriangleFacesMessage) {
        const options = msg.options ?? {};
        if (!options.vertices && !options.atom_triplets && !options.atomTriplets) {
            console.warn("[MolSysViewer] add_triangle_faces without vertices or atom_triplets");
            return;
        }
        try {
            const ref = await addTriangleFacesFromPython(this.plugin, options);
            this.registerShapeRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando triangle faces", err);
        }
    }

    private async handleUpdateVisibility(msg: UpdateVisibilityMessage) {
        const indices = msg.options?.visible_atom_indices;
        await this.updateVisibility(indices);
    }

    private async handleCreateRegion(msg: CreateRegionMessage) {
        const structure = this.getStructure();
        if (!structure || !this.currentStructure) {
            // Defer until structure is captured
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
            const structureRef = this.loadedStructure?.structure;
            if (!structureRef) {
                console.warn("[MolSysViewer] create_region: no structure ref");
                return;
            }
            console.log("[MolSysViewer] create_region: building component", tag, "atoms", atomIndices.length);
            const bundle = StructureElement.Bundle.fromSelection(selection);
            const root = this.plugin.state.data.build().to(structureRef);
            const component = root.apply(StateTransforms.Model.StructureComponent, {
                type: { name: "bundle", params: bundle },
                nullIfEmpty: true,
                label: tag,
            });
            const commitRes = await component.commit({ revertOnError: false });
            const selector = component.selector;
            const componentRef = selector?.ref;
            const compCount = selector?.cell?.obj?.data?.elementCount ?? 0;
            if (!selector?.isOk || !componentRef || compCount === 0) {
                console.warn("[MolSysViewer] create_region: empty component for", tag, "commit", commitRes, "count", compCount);
                return;
            }
            const reprType = msg.representation ?? "cartoon";
            const repr = await this.plugin.builders.structure.representation.addRepresentation(
                componentRef as any,
                { type: reprType as any, typeParams: (msg.params ?? {}) as any },
                { tag }
            );
            const reprRef = repr?.ref;
            if (!reprRef) console.warn("[MolSysViewer] create_region: representation missing ref", tag, "repr", repr);
            this.regionIndex.set(tag, {
                component: componentRef,
                representations: reprRef ? [reprRef] : [],
                atomIndices,
                selection: msg.selection,
            });
            console.log("[MolSysViewer] create_region: done", tag, "compCount", compCount, "repr", reprRef);
            this.notify?.({ event: "region_ack", tag, atom_indices: atomIndices, selection: msg.selection });
        } catch (err) {
            console.error("[MolSysViewer] Error creating region", err);
        }
    }

    private async handleSetRegionRepresentation(msg: SetRegionRepresentationMessage) {
        const tag = msg.tag ?? "region";
        const entry = this.regionIndex.get(tag);
        if (!entry || !entry.component || !this.loadedStructure?.structure) {
            console.warn("[MolSysViewer] set_region_representation: unknown tag", tag);
            return;
        }
        // Remove existing representations
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
            // Add new representation
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

    private async handleShowHideRegion(msg: ShowRegionMessage | HideRegionMessage, hide: boolean) {
        const tag = (msg.tag ?? "region") as string;
        const entry = this.regionIndex.get(tag);
        if (!entry || entry.representations.length === 0) return;
        const update = this.plugin.state.data.build();
        entry.representations.forEach(ref =>
            update.to(ref).update((old: any) => ({
                ...old,
                state: { ...(old?.state ?? {}), isHidden: hide },
            }))
        );
        await update.commit({ revertOnError: false });
    }

    private async handleDeleteRegion(msg: DeleteRegionMessage) {
        const tag = msg.tag ?? "region";
        const entry = this.regionIndex.get(tag);
        if (!entry) return;
        const refs: Array<StateObjectRef | undefined> = [
            ...entry.representations,
            entry.component,
        ];
        await Promise.all(refs.map(ref => this.removeStateObject(ref)));
        this.regionIndex.delete(tag);
        this.notify?.({ event: "region_deleted", tag });
    }

    private async handleCreateLayer(msg: CreateLayerMessage) {
        const tag = msg.tag ?? "layer";
        this.layerMeta.set(tag, { kind: msg.kind, meta: msg.meta });
        this.notify?.({ event: "layer_ack", tag, kind: msg.kind, meta: msg.meta });
    }

    private async handleShowHideLayer(msg: ShowLayerMessage | HideLayerMessage, hide: boolean) {
        const tag = msg.tag ?? "layer";
        const refs = this.tagIndex.get(tag);
        if (!refs || refs.size === 0) return;
        const update = this.plugin.state.data.build();
        refs.forEach(ref =>
            update.to(ref).update((old: any) => ({
                ...old,
                state: { ...(old?.state ?? {}), isHidden: hide },
            }))
        );
        await update.commit({ revertOnError: false });
    }

    private async handleDeleteLayer(msg: DeleteLayerMessage) {
        const tag = msg.tag ?? "layer";
        const refs = this.tagIndex.get(tag);
        if (refs && refs.size) {
            await Promise.all(Array.from(refs).map(ref => this.removeStateObject(ref)));
            this.tagIndex.delete(tag);
        }
        this.layerMeta.delete(tag);
        this.notify?.({ event: "layer_deleted", tag });
    }

    private async handleSetLayerTag(msg: SetLayerTagMessage) {
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

    private collectRefsFromPreset(result?: { representations?: { [name: string]: StateObjectSelector | undefined } }) {
        const refs: StateObjectRef[] = [];
        if (!result?.representations) return refs;
        Object.values(result.representations).forEach(sel => {
            if (sel?.ref) refs.push(sel.ref);
        });
        return refs;
    }

    private async handleSetGlobalRepresentation(msg: SetGlobalRepresentationMessage) {
        const structureRef = this.loadedStructure?.structure;
        if (!structureRef) {
            console.warn("[MolSysViewer] set_global_representation: no structure loaded");
            return;
        }
        // Ensure we are using the latest structure data object
        const structureData = this.getStructure();
        // Remove existing global reps
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

    private async handleShowHideGlobal(hide: boolean, target: "global" | "all" = "global") {
        const refs: StateObjectRef[] = [];
        // Always include tracked global reps if available
        this.globalReprs.forEach(ref => refs.push(ref));
        if (target === "all") {
            // Include every structure representation in the state tree
            const allReprs = this.plugin.state.data.select(SO.Molecule.Structure.Representation3D);
            for (const r of allReprs) {
                refs.push(r.transform.ref);
            }
        }
        if (refs.length === 0) return;
        const update = this.plugin.state.data.build();
        refs.forEach(ref => update.to(ref).setState({ isHidden: hide }));
        await this.plugin.runTask(this.plugin.state.data.updateTree(update));
    }

    private async handleStepTrajectory(msg: StepTrajectoryMessage) {
        const by = msg.by ?? 1;
        await this.stepTrajectory(by);
    }

    private async handleSetTrajectoryFrame(msg: SetTrajectoryFrameMessage) {
        const index = msg.index ?? 0;
        await this.setTrajectoryFrame(index);
    }

    private async handleSetTrajectoryPlayback(msg: SetTrajectoryPlaybackMessage) {
        const action = msg.action ?? "stop";
        const fps = msg.fps ?? 30;
        const step = msg.step ?? 1;
        const mode = msg.mode ?? "loop";
        const direction = msg.direction ?? "forward";
        if (action === "play") {
            await this.playTrajectory({ fps, mode, direction, step });
        } else {
            await this.stopTrajectoryPlayback();
        }
    }

    private async clearGlobalRepresentations() {
        if (this.globalReprs.size === 0) return;
        await Promise.all(Array.from(this.globalReprs).map(ref => this.removeStateObject(ref)));
        this.globalReprs.clear();
    }

    private async loadFromString(data: string, format: string, label?: string) {
        await this.clearGlobalRepresentations();
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromString(this.plugin, data, format, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private async loadFromUrl(url: string, format?: string, label?: string) {
        await this.clearGlobalRepresentations();
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromUrl(this.plugin, url, format, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private async loadFromMolSysPayload(payload: MolSysPayload, label?: string) {
        await this.clearGlobalRepresentations();
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromMolSysPayload(this.plugin, payload, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private captureCurrentStructure() {
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        this.currentStructure = structures.length ? structures[structures.length - 1] : undefined;

        // Apply pending visibility once structure exists
        if (this.pendingVisibility) {
            const pending = this.pendingVisibility;
            this.pendingVisibility = void 0;
            void this.updateVisibility(pending);
        }
        // Process any pending regions queued before structure was ready
        if (this.pendingRegions.length && this.currentStructure) {
            const queued = [...this.pendingRegions];
            this.pendingRegions.length = 0;
            for (const msg of queued) {
                void this.handleCreateRegion(msg);
            }
        }
        // Ensure a default global representation exists after load
        if (this.currentStructure && this.globalReprs.size === 0) {
            void this.ensureDefaultGlobalRepresentation();
        }
        this.updateTrajectoryState();
    }

    private async ensureDefaultGlobalRepresentation() {
        const structureRef = this.loadedStructure?.structure;
        if (!structureRef || this.globalReprs.size > 0) return;
        const update = this.plugin.state.data.build();
        try {
            const repr = this.plugin.builders.structure.representation.buildRepresentation(
                update,
                { ref: structureRef } as any,
                { type: "cartoon" as any },
                { tag: "global" }
            );
            await update.commit({ revertOnError: false });
            if (repr?.ref) this.globalReprs.add(repr.ref);
        } catch (err) {
            console.warn("[MolSysViewer] default global representation failed", err);
        }
    }

    private getStructure(): Structure | undefined {
        return this.currentStructure?.cell.obj?.data as Structure | undefined;
    }

    private getComponents(): StructureComponentRef[] {
        return this.currentStructure?.components ?? [];
    }

    private async addSphere(options: AddSphereMessage["options"]) {
        const ref = await addTransparentSphereFromPython(this.plugin, {
            center: options?.center ?? [0, 0, 0],
            radius: options?.radius ?? 10,
            color: options?.color ?? 0x00ff00,
            alpha: options?.alpha ?? 0.4,
        });
        this.registerShapeRef(ref);
    }

    private async updateVisibility(visibleAtomIndices?: number[]) {
        const structure = this.getStructure();
        if (!structure) {
            if (Array.isArray(visibleAtomIndices)) {
                this.pendingVisibility = visibleAtomIndices;
            }
            // Structure not ready yet; visibility will be applied later.
            return;
        }
        const components = this.getComponents();
        if (components.length === 0) return;

        await clearStructureTransparency(this.plugin, components);

        if (!Array.isArray(visibleAtomIndices)) return;

        const hideAll = visibleAtomIndices.length === 0;

        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        const visibleSet = hideAll ? void 0 : new Set(visibleAtomIndices);
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

    async resetView() {
        await PluginCommands.Camera.Reset(this.plugin, { durationMs: 250 });
    }

    async toggleFullscreen(enable?: boolean) {
        const root = this.plugin.canvas3d?.props.parent;
        const canvas = this.plugin.canvas3d?.props.canvas ?? this.plugin.canvas3d?.getCanvas?.();
        const target =
            this.host ??
            root?.parentElement ??
            root ??
            canvas?.parentElement ??
            canvas ??
            document.documentElement;
        if (!target || !(target as any).requestFullscreen) return;
        const shouldEnable = enable ?? !document.fullscreenElement;
        try {
            if (shouldEnable) {
                if (!document.fullscreenElement) await target.requestFullscreen();
            } else if (document.fullscreenElement) {
                await document.exitFullscreen();
            }
        } catch (err) {
            console.warn("[MolSysViewer] fullscreen toggle failed", err);
        }
    }

    async toggleBackground(mode?: "light" | "dark") {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const renderer = canvas3d.props?.renderer ?? {};
        const camera = canvas3d.props?.camera ?? {};

        // Snapshot the initial light mode once.
        if (!this.savedLightRenderer) this.savedLightRenderer = { ...renderer };
        if (!this.savedLightCamera) this.savedLightCamera = { ...camera };

        const makeDark = mode ? mode === "dark" : !this.darkMode;

        if (makeDark) {
            if (!this.savedDarkRenderer) {
                this.savedDarkRenderer = {
                    ...renderer,
                    backgroundColor: 0x101010,
                    lightColor: 0xffffff,
                    ambientColor: 0xffffff,
                    exposure: renderer.exposure ?? 1,
                    lightIntensity: renderer.lightIntensity ?? 1,
                    ambientIntensity: renderer.ambientIntensity ?? 1,
                };
            }
            if (!this.savedDarkCamera) {
                this.savedDarkCamera = { ...camera };
            }
            canvas3d.setProps({
                renderer: { ...this.savedDarkRenderer },
                camera: { ...this.savedDarkCamera },
            });
            this.darkMode = true;
        } else {
            const lightRenderer = this.savedLightRenderer ?? renderer;
            const lightCamera = this.savedLightCamera ?? camera;
            canvas3d.setProps({
                renderer: { ...lightRenderer },
                camera: { ...lightCamera },
            });
            this.darkMode = false;
        }
    }

    async toggleSwing(enable?: boolean) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.swingActive;
        this.swingActive = shouldEnable;
        this.spinActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable
                    ? { name: "rock", params: { speed: 0.25, angle: 20 } }
                    : { name: "off", params: {} },
            },
        });
    }

    async toggleSpin(enable?: boolean) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.spinActive;
        this.spinActive = shouldEnable;
        this.swingActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable ? { name: "spin", params: { speed: 0.1 } } : { name: "off", params: {} },
            },
        });
    }

    /**
     * Trajectory helpers
     */
    getTrajectoryState(): TrajectoryState {
        const frameCount = this.getFrameCount();
        const currentFrame = this.getCurrentFrameIndex();
        const isPlaying = this.plugin.managers.animation.isAnimating;
        return { frameCount, currentFrame, isPlaying };
    }

    onTrajectoryState(cb: (state: TrajectoryState) => void): () => void {
        this.trajectoryListeners.add(cb);
        cb(this.getTrajectoryState());
        return () => this.trajectoryListeners.delete(cb);
    }

    private notifyTrajectoryState() {
        const state = this.getTrajectoryState();
        for (const cb of this.trajectoryListeners) cb(state);
    }

    private getTrajectoryRef(): StateObjectRef | undefined {
        return this.loadedStructure?.trajectory;
    }

    private getTrajectoryModels(trajRef: StateObjectRef) {
        const all = this.plugin.state.data.selectQ(q => q.ofTransformer(StateTransforms.Model.ModelFromTrajectory));
        return all.filter(cell => cell.transform.parent === trajRef);
    }

    private getFrameCount(): number {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return 0;
        const cell = this.plugin.state.data.cells.get(trajRef);
        const traj = cell?.obj?.data as any;
        return traj?.frameCount ?? 0;
    }

    private getCurrentFrameIndex(): number {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return 0;
        const models = this.getTrajectoryModels(trajRef);
        const first = models[0];
        const params = first?.transform.params as any;
        const idx = params?.modelIndex ?? 0;
        return typeof idx === "number" ? idx : 0;
    }

    async setTrajectoryFrame(index: number) {
        const frameCount = this.getFrameCount();
        if (frameCount < 1) return;
        const clamped = Math.max(0, Math.min(frameCount - 1, Math.floor(index)));
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return;
        const models = this.getTrajectoryModels(trajRef);
        if (!models.length) return;
        const update = this.plugin.state.data.build();
        for (const m of models) {
            update.to(m).update({ modelIndex: clamped });
        }
        await this.plugin.runTask(this.plugin.state.data.updateTree(update));
        this.updateTrajectoryState();
    }

    async stepTrajectory(by: number) {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return;
        await PluginCommands.State.ApplyAction(this.plugin, {
            state: this.plugin.state.data,
            action: UpdateTrajectory.create({ action: "advance", by }),
        });
        this.updateTrajectoryState();
    }

    async playTrajectory(options: { fps?: number; mode?: "loop" | "palindrome" | "once"; direction?: "forward" | "backward"; step?: number } = {}) {
        const frameCount = this.getFrameCount();
        if (frameCount < 2) {
            console.warn("[MolSysViewer] playTrajectory ignored: trajectory has less than 2 frames");
            return;
        }

        const fps = options.fps ?? 30;
        const step = Math.max(1, Math.floor(options.step ?? 1));
        const direction = options.direction ?? "forward";

        // Stop any existing animation/timer first
        await this.stopTrajectoryPlayback();

        const intervalMs = Math.max(1, Math.floor(1000 / Math.max(fps, 1)));
        const delta = direction === "backward" ? -step : step;

        this.playbackTimer = setInterval(() => {
            void this.stepTrajectory(delta);
        }, intervalMs);

        if (this.trajectoryPoll) clearInterval(this.trajectoryPoll);
        this.trajectoryPoll = setInterval(() => this.notifyTrajectoryState(), 200);
        this.updateTrajectoryState();
    }

    async stopTrajectoryPlayback() {
        this.plugin.managers.animation.stop();
        if (this.playbackTimer) {
            clearInterval(this.playbackTimer);
            this.playbackTimer = void 0;
        }
        if (this.trajectoryPoll) {
            clearInterval(this.trajectoryPoll);
            this.trajectoryPoll = void 0;
        }
        this.updateTrajectoryState();
    }

    private updateTrajectoryState() {
        this.notifyTrajectoryState();
    }

    private async clearScene(options?: ClearSceneMessage["options"]) {
        const shapes = options?.shapes ?? true;
        const styles = options?.styles ?? true;
        const labels = options?.labels ?? false;

        if (shapes) await this.clearShapes();
        if (styles) await this.resetStructureDecorations();
        if (labels) await this.clearLabels();
    }

    private async clearShapes() {
        if (this.shapeRefs.size === 0) return;
        await Promise.all(Array.from(this.shapeRefs).map(ref => this.removeStateObject(ref)));
        this.shapeRefs.clear();
        this.tagIndex.clear();
    }

    private async clearLabels() {
        if (this.labelRefs.size === 0) return;
        await Promise.all(Array.from(this.labelRefs).map(ref => this.removeStateObject(ref)));
        this.labelRefs.clear();
    }

    private async resetStructureDecorations() {
        const components = this.getComponents();
        if (components.length === 0) return;
        await clearStructureTransparency(this.plugin, components);
    }

    private async clearAll() {
        await this.clearScene({ shapes: true, styles: true, labels: true });
        await this.removeLoadedStructure();
        this.currentStructure = undefined;
        this.regionIndex.clear();
        this.layerMeta.clear();
        this.globalReprs.clear();
        this.notify?.({ event: "registry_cleared" });
    }

    private async clearShapesByTag(tag?: string) {
        if (!tag) {
            await this.clearShapes();
            return;
        }
        const refs = this.tagIndex.get(tag);
        if (!refs || refs.size === 0) return;
        await Promise.all(Array.from(refs).map(ref => this.removeStateObject(ref)));
        refs.forEach(ref => this.shapeRefs.delete(ref as any));
        this.tagIndex.delete(tag);
    }

    private async removeLoadedStructure() {
        if (!this.loadedStructure) return;
        const refs: Array<StateObjectRef | undefined> = [
            this.loadedStructure.structure,
            this.loadedStructure.trajectory,
            this.loadedStructure.data,
        ];
        for (const ref of refs) await this.removeStateObject(ref);
        this.loadedStructure = undefined;
    }

    private async loadPdbId(pdbId: string) {
        const normalized = pdbId.trim().toUpperCase();
        const url = `https://files.rcsb.org/download/${normalized}.pdb`;
        await this.loadFromUrl(url, "pdb", `PDB ${normalized}`);
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

export interface TrajectoryState {
    frameCount: number;
    currentFrame: number;
    isPlaying: boolean;
}
