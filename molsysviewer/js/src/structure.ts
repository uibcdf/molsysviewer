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
