// src/widget.ts



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

import { addTransparentSphereFromPython } from "./shapes";
import {
    LoadedStructure,
    MolSysPayload,
    loadStructureFromString,
    loadStructureFromUrl,
    loadStructureFromMolSysPayload,
} from "./structure";


/**
 * NOTE FOR AUTOMATION AGENTS (Copilot, Codex, PR bots):
 *
 * Editing this file does NOT require running `npm run build` automatically.
 * The build process is manual and performed only when the maintainer decides
 * to regenerate `viewer.js`.
 *
 * The generated file is:
 *    ../viewer.js  (molsysviewer/viewer.js)
 *
 * This project intentionally commits the generated JS artifact so that the
 * Python package can be distributed without requiring a Node/TypeScript
 * toolchain. Therefore:
 *
 *  - Do NOT recommend "npm run build" after every change.
 *  - Do NOT attempt to modify the generated viewer.js directly.
 *  - Do NOT propose to delete, move, or refactor viewer.js.
 *
 * Any change to the runtime behavior must be done in the TypeScript sources
 * under js/src/, and the rebuild should happen only when the maintainer
 * performs it explicitly.
 */


// ------------------------------------------------------------------
// Controlador principal del viewer
// ------------------------------------------------------------------
class MolSysViewerController {
    static async create(target: HTMLElement): Promise<MolSysViewerController> {
        const canvas = document.createElement("canvas");
        canvas.style.width = "100%";
        canvas.style.height = "100%";
        canvas.style.display = "block";
        target.appendChild(canvas);

        const plugin = new PluginContext(DefaultPluginSpec());
        await plugin.init();

        // Mol* exposed `initViewerAsync` in newer versions; older bundles expose only `initViewer`.
        const init = (plugin as any).initViewerAsync ?? (plugin as any).initViewer;
        let ok = false;
        if (typeof init === "function") {
            const result = init.call(plugin, canvas, target);
            ok = typeof result?.then === "function" ? await result : !!result;
        } else {
            console.error("[MolSysViewer] Plugin init function not found (initViewer/initViewerAsync missing)");
        }
        if (!ok) console.error("[MolSysViewer] Failed to init Mol* viewer");

        return new MolSysViewerController(plugin);
    }

    private readonly shapeRefs = new Set<StateObjectRef<SO.Shape.Representation3D>>();
    private currentStructure?: StructureRef;
    private loadedStructure?: LoadedStructure;
    private readonly labelRefs = new Set<StateObjectRef>();

    private constructor(private readonly plugin: PluginContext) {}

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
        this.shapeRefs.add(ref);
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

    private async resetView() {
        await PluginCommands.Camera.Reset(this.plugin, { durationMs: 250 });
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


// ------------------------------------------------------------------
// Tipos de mensajes
// ------------------------------------------------------------------
type AddSphereMessage = {
    op: "add_sphere";
    options?: {
        center?: [number, number, number];
        radius?: number;
        color?: number;
        alpha?: number;
    };
};

type LoadStructureMessage = {
    op: "load_structure_from_string" | "load_pdb_string";
    data?: string;
    pdb?: string;
    pdb_text?: string;
    format?: string;
    label?: string;
};

type LoadMolSysPayloadMessage = {
    op: "load_molsys_payload";
    payload: MolSysPayload;
    label?: string;
};

type LoadStructureFromUrlMessage = {
    op: "load_structure_from_url";
    url: string;
    format?: string;
    label?: string;
};

type UpdateVisibilityMessage = {
    op: "update_visibility";
    options?: {
        visible_atom_indices?: number[];
    };
};

type ClearSceneMessage = {
    op: "clear_scene";
    options?: {
        shapes?: boolean;
        styles?: boolean;
        labels?: boolean;
    };
};

type ClearAllMessage = {
    op: "clear_all";
};

type LoadPdbIdMessage = {
    op: "load_pdb_id";
    pdb_id: string;
};

type ViewerMessage =
    TransparentSphereMessage |
    AddSphereMessage |
    LoadStructureMessage |
    LoadMolSysPayloadMessage |
    LoadStructureFromUrlMessage |
    LoadPdbIdMessage |
    UpdateVisibilityMessage |
    ClearSceneMessage |
    ClearAllMessage |
    Record<string, unknown>;


// ------------------------------------------------------------------
// AnyWidget entry point
// ------------------------------------------------------------------
export default {
    render({ model, el }: { model: any; el: HTMLElement }) {

        const controllerPromise = MolSysViewerController.create(el);

        // Avisar a Python cuando esté listo
        (async () => {
            try {
                await controllerPromise;
                model.send({ event: "ready" });
            } catch (err) {
                console.error("[MolSysViewer] Error inicializando plugin:", err);
            }
        })();

        console.log("[MolSysViewer] widget render inicial");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            console.log("[MolSysViewer] mensaje desde Python:", msg);
            try {
                const controller = await controllerPromise;
                await controller.handleMessage(msg);
            } catch (error) {
                console.error("[MolSysViewer] Error manejando mensaje:", msg, error);
            }
        });
    },
};
