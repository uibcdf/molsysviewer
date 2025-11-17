// src/widget.ts
// Frontend de MolSysViewer para anywidget (Mol* 5.x, shapes incluidos)

import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { DefaultPluginSpec } from 'molstar/lib/mol-plugin/spec';
import { PluginCommands } from 'molstar/lib/mol-plugin/commands';

import {
    addTransparentSphereFromPython,
    TransparentSphereSpec,
} from './shapes';

// ------------------------
// Tipos de mensajes Python
// ------------------------

type TransparentSphereMessage = {
    op: 'test_transparent_sphere';
    options?: TransparentSphereSpec;
};

type LoadStructureMessage = {
    op: 'load_pdb_string' | 'load_structure_from_string';
    options?: {
        pdb_string?: string;
        pdb?: string;
        pdb_text?: string;
        data?: string;
        text?: string;
        label?: string;
    };
};

type ViewerMessage =
    | TransparentSphereMessage
    | LoadStructureMessage
    | { op?: string; [k: string]: any };

// anywidget model (no lo tipamos fuerte para no pelear con versiones)
type MolSysViewerModel = {
    on: (event: string, cb: (arg?: any) => void) => void;
};

// ------------------------
// Helpers Mol*
// ------------------------

async function loadStructureFromString(
    plugin: PluginContext,
    data: string,
    label?: string
) {
    const raw = await plugin.builders.data.rawData({
        data,
        label: label ?? 'PDB string',
    });

    const trajectory = await plugin.builders.structure.parseTrajectory(raw, 'pdb');
    await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
}

async function createMolSysViewer(target: HTMLElement): Promise<PluginContext> {
    const plugin = new PluginContext(DefaultPluginSpec());

    await plugin.mountAsync(target as HTMLDivElement);
    await plugin.canvas3dInitialized;

    return plugin;
}

// ------------------------
// render() para anywidget
// ------------------------

function renderImpl({ model, el }: { model: MolSysViewerModel; el: HTMLElement }) {
    const container = el as HTMLDivElement;

    // Aseguramos que el contenedor tenga tamaño visible
    container.innerHTML = '';
    container.style.position = 'relative';
    container.style.width = '100%';
    container.style.display = 'block';
    container.style.height = '480px';   // ajusta este valor a tu gusto
    container.style.minHeight = '400px';

    // Creamos el plugin una sola vez para este elemento
    const pluginPromise = createMolSysViewer(container);

    // Escuchamos los mensajes que envía Python con `widget.send(...)`
    (model as any).on('msg:custom', async (msg: ViewerMessage) => {
        if (!msg || typeof msg !== 'object') return;
        const plugin = await pluginPromise;

        switch (msg.op) {
            case 'load_pdb_string':
            case 'load_structure_from_string': {
                const opts = msg.options ?? {};
                const pdb: string | undefined =
                    opts.pdb_string ??
                    opts.pdb ??
                    opts.pdb_text ??
                    opts.data ??
                    opts.text;

                if (!pdb || typeof pdb !== 'string') {
                    console.warn('[MolSysViewer] load_* sin cadena PDB válida', msg);
                    return;
                }

                try {
                    await loadStructureFromString(plugin, pdb, opts.label);
                } catch (e) {
                    console.error('[MolSysViewer] Error cargando estructura:', e);
                }
                break;
            }

            case 'test_transparent_sphere': {
                const opts = (msg as TransparentSphereMessage).options ?? {};
                const spec: TransparentSphereSpec = {
                    center: opts.center ?? [0, 0, 0],
                    radius: opts.radius ?? 10,
                    color: opts.color ?? 0x00ff00,
                    alpha: opts.alpha ?? 0.4,
                    id: opts.id ?? 'sphere-0',
                };
                try {
                    await addTransparentSphereFromPython(plugin, spec);
                } catch (e) {
                    console.error('[MolSysViewer] Error añadiendo esfera:', e);
                }
                break;
            }

            default: {
                if ((msg as any).op) {
                    console.warn('[MolSysViewer] op desconocida', (msg as any).op, msg);
                }
                break;
            }
        }
    });
}

// anywidget 0.9+ recomienda export default { render }
export default {
    render: renderImpl,
};

