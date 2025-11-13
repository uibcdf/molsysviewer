
// js/src/molstar_plugin.ts

// In the future we'll import Mol* here, e.g.:
// import { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
// import { DefaultPluginSpec } from "molstar/lib/mol-plugin-ui/spec";
// etc.

// For now, we just define a minimal controller with stubs.

export type BasicRepresentationType = "cartoon" | "sticks" | "surface" | string;

export interface MolstarControllerOptions {
  container: HTMLElement;
}

export class MolstarController {
  private container: HTMLElement;
  private pdbString: string | null = null;
  private currentRep: BasicRepresentationType = "cartoon";
  private currentFrame = 0;

  // In the future, we will hold a Mol* plugin instance here:
  // private plugin: PluginUIContext | null = null;

  constructor(options: MolstarControllerOptions) {
    this.container = options.container;

    // For now, just set a placeholder background and text
    this.container.style.position = "relative";
    this.container.style.width = "100%";
    this.container.style.height = "400px";
    this.container.style.background = "#111";
    this.container.style.color = "#eee";
    this.container.style.display = "flex";
    this.container.style.alignItems = "center";
    this.container.style.justifyContent = "center";
    this.container.style.fontFamily = "sans-serif";
    this.container.innerText = "MolSysViewer (Mol* placeholder)";

    // TODO: initialize Mol* plugin here in the future.
    // this.initMolstar();
  }

  // ------------------------------------------------------------------
  // Future: real Mol* initialization
  // ------------------------------------------------------------------
  // private async initMolstar() {
  //   this.plugin = await createPlugin(this.container, ...);
  // }

  // ------------------------------------------------------------------
  // Commands called from the widget
  // ------------------------------------------------------------------
  loadPdbString(pdb: string): void {
    this.pdbString = pdb;
    console.log("[MolSysViewer] loadPdbString called, length =", pdb.length);

    // TODO: when Mol* is integrated:
    // - create a data source from pdb string
    // - load into the plugin
    // - set default representation
  }

  setBasicRepresentation(type: BasicRepresentationType): void {
    this.currentRep = type;
    console.log("[MolSysViewer] setBasicRepresentation:", type);

    // TODO: change Mol* representation accordingly, e.g.
    // plugin.managers.structure.component.updateRepresentations...
  }

  resetCamera(): void {
    console.log("[MolSysViewer] resetCamera");
    // TODO: plugin.camera.reset();
  }

  setFrame(index: number): void {
    this.currentFrame = index;
    console.log("[MolSysViewer] setFrame:", index);

    // TODO: when trajectory is wired:
    // plugin.managers.structure.component.setFrame(index) or similar
  }
}
