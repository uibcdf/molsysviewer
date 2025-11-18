// src/structure.ts
import { PluginContext } from "molstar/lib/mol-plugin/context";

export async function loadStructureFromString(
    plugin: PluginContext,
    data: string,
    format: string = "pdb",
    label?: string
) {
    // Crea el data node bruto
    const raw = await plugin.builders.data.rawData({
        data,
        label: label ?? "Structure from string",
        // extension opcional; ayuda a algunos parsers
        ext: format,
    });

    // parseTrajectory necesita el nombre del formato: 'pdb', 'mmcif', etc.
    const trajectory = await plugin.builders.structure.parseTrajectory(raw, format as any);

    // Aplica el preset por defecto (representación bonita estándar)
    await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");
}

export async function loadStructureFromUrl(
    plugin: PluginContext,
    url: string,
    format?: string,
    label?: string
) {
    // Descarga la estructura (texto) desde la URL
    const data = await plugin.builders.data.download(
        { url, isBinary: false },
        { state: { isGhost: true } }
    );

    // Si no se especifica formato, intenta deducirlo de la extensión
    const guessedFormat =
        format ??
        (url.split(".").pop() ?? "pdb"); // "pdb", "cif", "mmcif", etc.

    const trajectory = await plugin.builders.structure.parseTrajectory(
        data,
        guessedFormat as any
    );

    await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");
}
