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
import { StateObjectRef } from "molstar/lib/mol-state";

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
    ResetCameraMessage,
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

/**
 * Controller that translates Python messages into Mol* actions and manages state refs.
 */
export class MolSysViewerController {
    static async create(target: HTMLElement): Promise<MolSysViewerController> {
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

        return new MolSysViewerController(plugin, target);
    }

    private readonly shapeRefs = new Set<StateObjectRef<SO.Shape.Representation3D>>();
    private readonly tagIndex = new Map<string, Set<StateObjectRef>>();
    private currentStructure?: StructureRef;
    private loadedStructure?: LoadedStructure;
    private readonly labelRefs = new Set<StateObjectRef>();
    private swingActive = false;
    private spinActive = false;

    private constructor(private readonly plugin: PluginContext, private readonly host: HTMLElement) {}

    private registerShapeRef(ref?: StateObjectRef, tag?: string) {
        if (!ref) return;
        this.shapeRefs.add(ref as any);
        if (!tag) return;
        if (!this.tagIndex.has(tag)) this.tagIndex.set(tag, new Set());
        this.tagIndex.get(tag)!.add(ref as any);
    }

    async handleMessage(msg: ViewerMessage) {
        if (!msg || typeof msg !== "object") return;
        if (!("op" in msg)) {
            console.warn("[MolSysViewer] mensaje sin 'op'", msg);
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

                default:
                    console.warn("[MolSysViewer] op desconocida:", (msg as any).op, msg);
                    break;
            }
        } catch (error) {
            console.error("[MolSysViewer] Error procesando mensaje:", msg, error);
        }
    }

    private async handleLoadFromString(msg: LoadStructureMessage) {
        const text = msg.data ?? msg.pdb ?? msg.pdb_text ?? "";
        if (!text || typeof text !== "string") {
            console.warn("[MolSysViewer] mensaje de carga sin data/pdb/pdb_text");
            return;
        }
        const format = msg.format ?? "pdb";
        const label = msg.label ?? "Structure";
        await this.loadFromString(text, format, label);
    }

    private async handleLoadMolSysPayload(msg: LoadMolSysPayloadMessage) {
        if (!msg.payload) {
            console.warn("[MolSysViewer] load_molsys_payload sin payload");
            return;
        }
        await this.loadFromMolSysPayload(msg.payload, msg.label);
    }

    private async handleLoadFromUrl(msg: LoadStructureFromUrlMessage) {
        if (!msg.url || typeof msg.url !== "string") {
            console.warn("[MolSysViewer] load_structure_from_url sin url");
            return;
        }
        await this.loadFromUrl(msg.url, msg.format, msg.label);
    }

    private async handleLoadPdbId(msg: LoadPdbIdMessage) {
        const pdbId = msg.pdb_id?.trim();
        if (!pdbId) {
            console.warn("[MolSysViewer] load_pdb_id sin pdb_id");
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
            console.warn("[MolSysViewer] add_alpha_sphere_set sin datos de alpha_spheres");
            return;
        }

        const centers = options.alpha_spheres.centers;
        const radii = options.alpha_spheres.radii;
        if (!Array.isArray(centers) || !Array.isArray(radii) || centers.length !== radii.length || centers.length === 0) {
            console.warn("[MolSysViewer] add_alpha_sphere_set datos inconsistentes");
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
            console.warn("[MolSysViewer] add_pocket_surface sin atom_indices");
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
            console.warn("[MolSysViewer] add_pocket_blob sin centers o radii");
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
            console.warn("[MolSysViewer] add_channel_tube requiere al menos dos centers y radii");
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
            console.warn("[MolSysViewer] add_anisotropy_ellipsoids requiere centers o atom_indices");
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
            console.warn("[MolSysViewer] add_pharmacophore_features requiere centers y kinds del mismo tamaño");
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
            console.warn("[MolSysViewer] add_displacement_vectors sin vectores");
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
            console.warn("[MolSysViewer] add_tetrahedra sin tetraCoords ni atom_quads");
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
            console.warn("[MolSysViewer] add_triangle_faces sin vertices ni atom_triplets");
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

    private async loadFromString(data: string, format: string, label?: string) {
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromString(this.plugin, data, format, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private async loadFromUrl(url: string, format?: string, label?: string) {
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromUrl(this.plugin, url, format, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private async loadFromMolSysPayload(payload: MolSysPayload, label?: string) {
        const previous = this.loadedStructure?.data ?? this.loadedStructure?.trajectory;
        this.loadedStructure = await loadStructureFromMolSysPayload(this.plugin, payload, label, {
            previous,
        });
        this.captureCurrentStructure();
    }

    private captureCurrentStructure() {
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        this.currentStructure = structures.length ? structures[structures.length - 1] : undefined;
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
            console.warn("[MolSysViewer] update_visibility sin estructura cargada");
            return;
        }
        const components = this.getComponents();
        if (components.length === 0) return;

        await clearStructureTransparency(this.plugin, components);

        if (!Array.isArray(visibleAtomIndices) || visibleAtomIndices.length === 0) return;

        const selectionBuilder = StructureSelection.LinearBuilder(structure);
        const visibleSet = new Set(visibleAtomIndices);
        let hasHidden = false;

        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elementCount = OrderedSet.size(unit.elements);
            if (elementCount === 0) continue;

            const hiddenElements: number[] = [];
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(unit.elements, ordinal);
                if (!visibleSet.has(elementIndex)) {
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
        const current = canvas3d.props?.renderer?.backgroundColor;
        const isDark = typeof current === "number" ? current === 0x101010 : false;
        const makeDark = mode ? mode === "dark" : !isDark;
        const bg = makeDark ? 0x101010 : 0xffffff;
        const fg = makeDark ? 0xffffff : 0x000000;
        canvas3d.setProps({
            renderer: {
                ...(canvas3d.props?.renderer || {}),
                backgroundColor: bg,
                lightColor: fg,
                ambientColor: fg,
            },
        });
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
