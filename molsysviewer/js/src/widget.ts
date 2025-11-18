// src/widget.ts

import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";

import { addTransparentSphereFromPython } from "./shapes";
import { loadStructureFromString } from "./structure";

export async function createMolSysViewer(target: HTMLElement): Promise<PluginContext> {
    const plugin = new PluginContext(DefaultPluginSpec());

    // monta el plugin dentro del elemento target
    await plugin.mountAsync(target);
    await plugin.canvas3dInitialized;

    return plugin;
}

// Tipos de mensajes
type TransparentSphereMessage = {
    op: "test_transparent_sphere";
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

type ViewerMessage = TransparentSphereMessage | LoadStructureMessage | Record<string, unknown>;

export default {
    render({ model, el }: { model: any; el: HTMLElement }) {
        // Crear el plugin una sola vez por elemento
        const pluginPromise = createMolSysViewer(el);

        // Avisar al backend cuando el plugin esté inicializado para
        // que pueda enviar los mensajes pendientes.
        (async () => {
            try {
                await pluginPromise;
                model.send({ event: "ready" });
            } catch (error) {
                console.error("[MolSysViewer] Error inicializando el plugin:", error);
            }
        })();

        // Logs de depuración por si acaso
        console.log("[MolSysViewer] widget render inicial");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            console.log("[MolSysViewer] mensaje desde Python:", msg);

            const plugin = await pluginPromise;

            switch (msg.op) {
                case "load_structure_from_string":
                case "load_pdb_string": {
                    const text =
                        (msg as any).data ??
                        (msg as any).pdb ??
                        (msg as any).pdb_text ??
                        "";
                    if (!text || typeof text !== "string") {
                        console.warn("[MolSysViewer] mensaje de carga sin data/pdb/pdb_text");
                        return;
                    }
                    const format = (msg as LoadStructureMessage).format ?? "pdb";
                    const label = (msg as LoadStructureMessage).label ?? "Structure";

                    try {
                        await loadStructureFromString(plugin, text, format, label);
                    } catch (e) {
                        console.error("[MolSysViewer] Error al cargar estructura:", e);
                    }
                    break;
                }

                case "test_transparent_sphere": {
                    const options = (msg as TransparentSphereMessage).options ?? {};
                    await addTransparentSphereFromPython(plugin, {
                        center: options.center ?? [0, 0, 0],
                        radius: options.radius ?? 10,
                        color: options.color ?? 0x00ff00,
                        alpha: options.alpha ?? 0.4,
                    });
                    break;
                }

                default:
                    console.warn("[MolSysViewer] op desconocida:", (msg as any).op, msg);
                    break;
            }
        });
    },
};

