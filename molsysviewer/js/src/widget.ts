// widget.ts — MolSysViewer stable version
// --------------------------------------
// This file restores a stable Mol* viewer setup that:
//   ✔ shows axes
//   ✔ loads and displays a PDB structure
//   ✔ logs sphere parameters (placeholder)
// without attempting to use Mol* APIs that are not yet verified
// in this specific molstar@5.x build.
//
// A future branch will implement real shapes safely.

import type { AnyModel } from "anywidget";
import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";

import {
    describeTransparentSphere,
    TransparentSphereOptions,
} from "./shapes";

interface MolSysViewerModel extends AnyModel {
    on(event: string, cb: (msg: any) => void): void;
    send(msg: any): void;
}

// ---------------------------------------------------------
// CREATE MOL* PLUGIN (viewer only, stable, minimal)
// ---------------------------------------------------------
async function createMolSysPlugin(container: HTMLElement): Promise<PluginContext> {
    const canvas = document.createElement("canvas");
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    container.appendChild(canvas);

    // Use DefaultPluginSpec() WITHOUT modifications.
    // This matches the working setup where structures were visible.
    const plugin = new PluginContext(DefaultPluginSpec());

    // Initialize core plugin
    await plugin.init();

    // Initialize viewer (axes, interaction, etc.)
    await plugin.initViewerAsync(canvas, container);

    console.log("MolSysViewer: Plugin initialized.");

    return plugin;
}

// ---------------------------------------------------------
// LOAD STRUCTURE (this already worked correctly before)
// ---------------------------------------------------------
async function loadStructureFromString(plugin: PluginContext, msg: any) {
    const raw = await plugin.builders.data.rawData({
        data: msg.data,
        label: msg.label,
    });

    const traj = await plugin.builders.structure.parseTrajectory(
        raw,
        msg.format
    );

    await plugin.builders.structure.hierarchy.applyPreset(traj, "default");

    plugin.canvas3d?.requestCameraReset();
    console.log("MolSysViewer: structure loaded.");
}

// ---------------------------------------------------------
// PLACEHOLDER FOR CUSTOM SHAPES
// ---------------------------------------------------------
async function placeholderTransparentSphere(plugin: PluginContext, options: any) {
    const opts: TransparentSphereOptions = {
        center: options?.center ?? [0, 0, 0],
        radius: options?.radius ?? 1,
        color: options?.color ?? 0x00ff00,
        alpha: options?.alpha ?? 0.4,
    };

    console.log(
        "MolSysViewer: test_transparent_sphere (placeholder)\n" +
            describeTransparentSphere(opts)
    );

    // IMPORTANT:
    // We do NOT touch plugin.representation, transforms, or any
    // Mol* internal shape APIs here. This is just a logging hook.
}

// ---------------------------------------------------------
// RENDER ENTRY POINT
// ---------------------------------------------------------
function render({
    model,
    el,
}: {
    model: MolSysViewerModel;
    el: HTMLElement;
}) {
    el.innerHTML = "";

    const container = document.createElement("div");
    container.style.width = "100%";
    container.style.height = "500px";
    el.appendChild(container);

    createMolSysPlugin(container).then((plugin) => {
        model.on("msg:custom", async (msg: any) => {
            if (!msg || typeof msg.op !== "string") return;

            if (msg.op === "load_structure_from_string") {
                await loadStructureFromString(plugin, msg);
                return;
            }

            if (msg.op === "test_transparent_sphere") {
                await placeholderTransparentSphere(plugin, msg.options);
                return;
            }
        });

        model.send({ event: "ready" });
    });
}

export default { render };

