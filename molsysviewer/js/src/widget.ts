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
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { StateObjectRef } from "molstar/lib/mol-state";

import { addTransparentSphereFromPython } from "./shapes";
import { loadStructureFromString, loadStructureFromUrl } from "./structure";


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

        const ok = await plugin.initViewerAsync(canvas, target);
        if (!ok) console.error("[MolSysViewer] Failed to init Mol* viewer");

        return new MolSysViewerController(plugin);
    }

    private readonly shapeRefs = new Set<StateObjectRef<SO.Shape.Representation3D>>();
    private currentStructure?: StructureRef;

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
                case "load_pdb_string": {
                    const text =
                        (msg as any).data ?? (msg as any).pdb ?? (msg as any).pdb_text ?? "";
                    if (!text || typeof text !== "string") {
                        console.warn(
                            "[MolSysViewer] mensaje de carga sin data/pdb/pdb_text"
                        );
                        return;
                    }
                    const format = (msg as LoadStructureMessage).format ?? "pdb";
                    const label = (msg as LoadStructureMessage).label ?? "Structure";
                    await this.loadFromString(text, format, label);
                    break;
                }

                case "load_structure_from_url": {
                    const { url, format, label } = msg as LoadStructureFromUrlMessage;
                    if (!url || typeof url !== "string") {
                        console.warn("[MolSysViewer] load_structure_from_url sin url");
                        return;
                    }
                    await this.loadFromUrl(url, format, label);
                    break;
                }

                case "test_transparent_sphere":
                case "add_sphere": {
                    const options = (msg as AddSphereMessage).options ?? {};
                    await this.addSphere({
                        center: options.center ?? [0, 0, 0],
                        radius: options.radius ?? 10,
                        color: options.color ?? 0x00ff00,
                        alpha: options.alpha ?? 0.4,
                    });
                    break;
                }

                case "update_visibility": {
                    const options = (msg as UpdateVisibilityMessage).options;
                    await this.updateVisibility(options?.visible_atom_indices);
                    break;
                }

                case "reset_view":
                    await this.resetView();
                    break;

                case "clear_scene":
                    await this.clearScene((msg as ClearSceneMessage).options);
                    break;

                case "clear_all":
                    await this.clearAll();
                    break;

                case "test_pdb_id":
                    console.warn("[MolSysViewer] test_pdb_id aún no implementado");
                    break;

                default:
                    console.warn("[MolSysViewer] op desconocida:", (msg as any).op, msg);
                    break;
            }
        } catch (error) {
            console.error("[MolSysViewer] Error procesando mensaje:", msg, error);
        }
    }

    private async loadFromString(data: string, format: string, label?: string) {
        await loadStructureFromString(this.plugin, data, format, label);
        this.captureCurrentStructure();
    }

    private async loadFromUrl(url: string, format?: string, label?: string) {
        await loadStructureFromUrl(this.plugin, url, format, label);
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

        if (!Array.isArray(visibleAtomIndices)) return;

        const visibleSet = new Set(visibleAtomIndices);
        const lociElements: { unit: Unit; indices: OrderedSet<number> }[] = [];
        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elementCount = OrderedSet.size(unit.elements);
            if (visibleSet.size === 0) {
                if (elementCount === 0) continue;
                lociElements.push({
                    unit,
                    indices: OrderedSet.ofBounds(0, elementCount),
                });
                continue;
            }

            const hiddenOrdinals: number[] = [];
            for (let ordinal = 0; ordinal < elementCount; ordinal++) {
                const elementIndex = OrderedSet.getAt(unit.elements, ordinal);
                if (!visibleSet.has(elementIndex)) hiddenOrdinals.push(ordinal);
            }
            if (hiddenOrdinals.length === 0) continue;
            const indices =
                hiddenOrdinals.length === elementCount
                    ? OrderedSet.ofBounds(0, elementCount)
                    : OrderedSet.ofSortedArray(hiddenOrdinals);
            lociElements.push({ unit, indices });
        }

        if (lociElements.length === 0) return;

        const loci = StructureElement.Loci(structure, lociElements as any);
        await setStructureTransparency(this.plugin, components, 1, async () => loci);
    }

    private async resetView() {
        await PluginCommands.Camera.Reset(this.plugin, { durationMs: 250 });
    }

    private async clearScene(options?: ClearSceneMessage["options"]) {
        const shapes = options?.shapes ?? true;
        const styles = options?.styles ?? true;

        if (shapes) await this.clearShapes();
        if (styles) await this.resetStructureDecorations();
    }

    private async clearShapes() {
        if (this.shapeRefs.size === 0) return;
        const builder = this.plugin.state.data.build();
        for (const ref of this.shapeRefs) builder.delete(ref);
        await PluginCommands.State.Update(this.plugin, {
            state: this.plugin.state.data,
            tree: builder,
            options: { doNotLogTiming: true },
        });
        this.shapeRefs.clear();
    }

    private async resetStructureDecorations() {
        const components = this.getComponents();
        if (components.length === 0) return;
        await clearStructureTransparency(this.plugin, components);
    }

    private async clearAll() {
        await this.clearScene({ shapes: true, styles: true, labels: true });
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        if (structures.length) {
            await this.plugin.managers.structure.hierarchy.remove(structures);
        }
        this.currentStructure = undefined;
    }
}


// ------------------------------------------------------------------
// Tipos de mensajes
// ------------------------------------------------------------------
type TransparentSphereMessage = {
    op: "test_transparent_sphere";
    options?: {
        center?: [number, number, number];
        radius?: number;
        color?: number;
        alpha?: number;
    };
};

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

type ViewerMessage =
    TransparentSphereMessage |
    AddSphereMessage |
    LoadStructureMessage |
    LoadStructureFromUrlMessage |
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

