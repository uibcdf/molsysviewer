
// js/src/widget.ts

import type { AnyModel } from 'anywidget';
import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { DefaultPluginSpec } from 'molstar/lib/mol-plugin/spec';
import { addTransparentSphereToPlugin } from './shapes';

interface MolSysViewerModel extends AnyModel {
  on(event: string, cb: (msg: any) => void): void;
  send(msg: any): void;
}

// Crea un PluginContext de Mol* con un canvas propio dentro de `container`
async function createMolSysPlugin(container: HTMLElement): Promise<PluginContext> {
  const canvas = document.createElement('canvas');
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  container.appendChild(canvas);

  const spec = DefaultPluginSpec();
  const plugin = new PluginContext(spec);
  await plugin.init();

  // Mol* 5.x: método asíncrono para inicializar el viewer
  const ok = await plugin.initViewerAsync(canvas, container);
  if (!ok) {
    console.error('MolSysViewer: Failed to init Mol* viewer');
  }

  return plugin;
}

async function loadStructureFromString(
  plugin: PluginContext,
  params: { format: 'pdb' | 'mmcif'; data: string; label?: string },
) {
  const { format, data, label } = params;

  const dataBuilder = plugin.builders.data;
  const structureBuilder = plugin.builders.structure;

  // 1. Nodo de datos crudos
  const dataState = await dataBuilder.rawData({
    data,
    label: label ?? `string-${format}`,
  });

  // 2. Parsear a trayectoria (OJO: parseTrajectory cuelga del structureBuilder)
  const trajectory = await structureBuilder.parseTrajectory(dataState, format);

  // 3. Aplicar preset por defecto para ver algo
  await structureBuilder.hierarchy.applyPreset(trajectory, 'default');

  plugin.canvas3d?.requestCameraReset();
}

async function loadStructureFromUrl(
  plugin: PluginContext,
  params: { url: string; format: 'pdb' | 'mmcif' | 'auto'; label?: string },
) {
  let { url, format, label } = params;

  if (!url || typeof url !== 'string') {
    console.warn('MolSysViewer: url vacío o no-string en load_structure_from_url');
    return;
  }

  if (format === 'auto' || !format) {
    const lower = url.toLowerCase();
    if (lower.endsWith('.cif') || lower.endsWith('.mmcif')) format = 'mmcif';
    else format = 'pdb';
  }

  const response = await fetch(url);
  if (!response.ok) {
    console.error(`MolSysViewer: error HTTP ${response.status} al descargar ${url}`);
    return;
  }
  const text = await response.text();

  await loadStructureFromString(plugin, {
    format: (format === 'mmcif' ? 'mmcif' : 'pdb'),
    data: text,
    label: label ?? `From URL: ${url}`,
  });
}

export async function render({ model, el }: { model: MolSysViewerModel; el: HTMLElement }) {
  // limpiar contenedor
  el.innerHTML = '';

  const container = document.createElement('div');
  container.style.position = 'relative';
  container.style.width = '100%';
  container.style.height = '500px';
  container.style.border = '1px solid #ccc';
  el.appendChild(container);

  const plugin = await createMolSysPlugin(container);

  // Mensajes desde Python
  model.on('msg:custom', async (msg: any) => {
    if (!msg || typeof msg.op !== 'string') return;

    console.log('MolSysViewer: mensaje recibido', msg);

    // --- cargar estructura desde string (PDB o mmCIF) ---
    if (msg.op === 'load_structure_from_string') {
      const format = (msg.format || 'pdb') as 'pdb' | 'mmcif';
      const data = msg.data as string;
      const label = msg.label || 'MolSysViewer structure';

      if (!data || typeof data !== 'string') {
        console.warn('MolSysViewer: data vacío o no-string en load_structure_from_string');
        return;
      }

      try {
        await loadStructureFromString(plugin, { format, data, label });
      } catch (e) {
        console.error('MolSysViewer: error cargando estructura desde string', e);
      }
      return;
    }

    // --- cargar estructura desde URL ---
    if (msg.op === 'load_structure_from_url') {
      try {
        await loadStructureFromUrl(plugin, {
          url: msg.url as string,
          format: (msg.format || 'auto') as 'pdb' | 'mmcif' | 'auto',
          label: msg.label as string | undefined,
        });
      } catch (e) {
        console.error('MolSysViewer: error cargando estructura desde URL', e);
      }
      return;
    }

    // --- esfera transparente de test ---
    if (msg.op === 'test_transparent_sphere') {
      try {
        const options = msg.options || {};
        await addTransparentSphereToPlugin(
          plugin,
          options.center as [number, number, number],
          options.radius as number,
          options.color as number,
          options.alpha as number,
        );
      } catch (e) {
        console.error('MolSysViewer: error en test_transparent_sphere', e);
      }
      return;
    }

    // --- limpiar escena ---
    if (msg.op === 'clear') {
      try {
        await plugin.clear();
      } catch (e) {
        console.warn('MolSysViewer: error al limpiar la escena', e);
      }
      return;
    }
  });

  // Notificar back-end: listo para recibir mensajes
  model.send({ event: 'ready' });
}
