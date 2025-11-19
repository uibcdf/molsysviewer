// src/widget.ts

import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";

import { addTransparentSphereFromPython } from "./shapes";
import { loadStructureFromString, loadStructureFromUrl } from "./structure";


// ------------------------------------------------------------------
// Crear e inicializar el plugin Mol*
// ------------------------------------------------------------------
export async function createMolSysViewer(target: HTMLElement): Promise<PluginContext> {

    const canvas = document.createElement("canvas");
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.display = "block";
    target.appendChild(canvas);

    const plugin = new PluginContext(DefaultPluginSpec());

    await plugin.init();

    const ok = await plugin.initViewerAsync(canvas, target);
    if (!ok) console.error("[MolSysViewer] Failed to init Mol* viewer");

    return plugin;
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

type ViewerMessage =
    TransparentSphereMessage |
    AddSphereMessage |
    LoadStructureMessage |
    LoadStructureFromUrlMessage |
    Record<string, unknown>;


// ------------------------------------------------------------------
// AnyWidget entry point
// ------------------------------------------------------------------
export default {
    render({ model, el }: { model: any; el: HTMLElement }) {

        const pluginPromise = createMolSysViewer(el);

        // Avisar a Python cuando esté listo
        (async () => {
            try {
                await pluginPromise;
                model.send({ event: "ready" });
            } catch (err) {
                console.error("[MolSysViewer] Error inicializando plugin:", err);
            }
        })();

        console.log("[MolSysViewer] widget render inicial");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            console.log("[MolSysViewer] mensaje desde Python:", msg);

            const plugin = await pluginPromise;

            switch (msg.op) {

                // ------------------------------------------------------------
                // CARGA DESDE STRING
                // ------------------------------------------------------------
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

                // ------------------------------------------------------------
                // CARGA DESDE URL
                // ------------------------------------------------------------
                case "load_structure_from_url": {
                    const { url, format, label } = msg as LoadStructureFromUrlMessage;
                    if (!url || typeof url !== "string") {
                        console.warn("[MolSysViewer] load_structure_from_url sin url");
                        return;
                    }

                    try {
                        await loadStructureFromUrl(plugin, url, format, label);
                    } catch (e) {
                        console.error("[MolSysViewer] Error al cargar estructura desde URL:", e);
                    }
                    break;
                }

                // ------------------------------------------------------------
                // ESFERAS (actual)
                // ------------------------------------------------------------
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

                case "add_sphere": {
                    const options = (msg as AddSphereMessage).options ?? {};
                    await addTransparentSphereFromPython(plugin, {
                        center: options.center ?? [0, 0, 0],
                        radius: options.radius ?? 10,
                        color: options.color ?? 0x00ff00,
                        alpha: options.alpha ?? 0.4,
                    });
                    break;
                }

                // ------------------------------------------------------------
                // NOPs (todavía no implementados)
                // ------------------------------------------------------------
                case "update_visibility":
                    console.warn("[MolSysViewer] update_visibility aún no implementado");
                    break;

                case "reset_view":
                    console.warn("[MolSysViewer] reset_view aún no implementado");
                    break;

                case "clear_scene":
                    console.warn("[MolSysViewer] clear_scene aún no implementado");
                    break;

                case "clear_all":
                    console.warn("[MolSysViewer] clear_all aún no implementado");
                    break;

                case "test_pdb_id":
                    console.warn("[MolSysViewer] test_pdb_id aún no implementado");
                    break;

                // ------------------------------------------------------------
                default:
                    console.warn("[MolSysViewer] op desconocida:", (msg as any).op, msg);
                    break;
            }
        });
    },
};

