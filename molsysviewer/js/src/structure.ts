// src/structure.ts
import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateObjectRef } from "molstar/lib/mol-state";

export interface LoadStructureOptions {
    /** Referencia al nodo anterior que se debe eliminar antes de cargar. */
    previous?: StateObjectRef;
}

export interface LoadedStructure {
    /** Referencia al nodo raíz de los datos brutos. */
    data: StateObjectRef<SO.Data.String | SO.Data.Binary | SO.Data.Blob>;
    /** Referencia al nodo de la trayectoria (parseado). */
    trajectory: StateObjectRef<SO.Molecule.Trajectory>;
    /** Referencia opcional a la estructura creada por el preset. */
    structure?: StateObjectRef<SO.Molecule.Structure>;
}

async function recyclePreviousNode(plugin: PluginContext, previous?: StateObjectRef) {
    if (!previous) return;
    const builder = plugin.build();
    builder.delete(previous);
    await builder.commit();
}

export async function loadStructureFromString(
    plugin: PluginContext,
    data: string,
    format: string = "pdb",
    label?: string,
    options?: LoadStructureOptions
): Promise<LoadedStructure> {
    await recyclePreviousNode(plugin, options?.previous);

    const raw = await plugin.builders.data.rawData({
        data,
        label: label ?? "Structure from string",
        // extension opcional; ayuda a algunos parsers
        ext: format,
    });

    // parseTrajectory necesita el nombre del formato: 'pdb', 'mmcif', etc.
    const trajectory = await plugin.builders.structure.parseTrajectory(raw, format as any);

    // Aplica el preset por defecto (representación bonita estándar)
    const preset = await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");

    return {
        data: raw.ref,
        trajectory: trajectory.ref,
        structure: preset?.structure?.ref,
    };
}

export async function loadStructureFromUrl(
    plugin: PluginContext,
    url: string,
    format?: string,
    label?: string,
    options?: LoadStructureOptions
): Promise<LoadedStructure> {
    await recyclePreviousNode(plugin, options?.previous);

    // Descarga la estructura (texto) desde la URL
    const dataNode = await plugin.builders.data.download(
        { url, isBinary: false, label },
        { state: { isGhost: true } }
    );

    // Si no se especifica formato, intenta deducirlo de la extensión
    const guessedFormat =
        format ??
        (url.split(".").pop() ?? "pdb"); // "pdb", "cif", "mmcif", etc.

    const trajectory = await plugin.builders.structure.parseTrajectory(
        dataNode,
        guessedFormat as any
    );

    const preset = await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");

    return {
        data: dataNode.ref,
        trajectory: trajectory.ref,
        structure: preset?.structure?.ref,
    };
}
