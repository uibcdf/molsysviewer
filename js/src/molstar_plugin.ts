// js/src/molstar_plugin.ts

// In the future we'll import Mol* here, e.g.:
// import { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
// import { DefaultPluginSpec } from "molstar/lib/mol-plugin-ui/spec";
// etc.

 // @ts-ignore
import { Viewer } from "molstar/build/viewer/molstar";

export type BasicRepresentationType = "cartoon" | "sticks" | "surface" | string;

export interface MolstarControllerOptions {
  container: HTMLElement;
}

export class MolstarController {
  private container: HTMLElement;
  private viewer: Viewer;
  private plugin: any;

  constructor(options: MolstarControllerOptions) {
    this.container = options.container;

    // Crear un viewer de Mol*
    this.viewer = new Viewer(this.container, {
      layoutIsExpanded: false,
      layoutShowControls: false,
      layoutShowSequence: false,
      layoutShowLog: false,
      layoutShowLeftPanel: false,
      viewportShowExpand: false,
      viewportShowSelectionMode: false,
      viewportShowAnimation: false,
      pdbProvider: "rcsb",
      emdbProvider: "rcsb",
    });

    // Acceso bruto al plugin interno (por ahora lo dejamos como any)
    // para usarlo más adelante con formas, cavidades, etc.
    this.plugin = (this.viewer as any).plugin;
  }

  // ------------------------------------------------------------------
  // Cargar un PDB (más adelante lo usaremos con MolSysMT)
  // ------------------------------------------------------------------
  async loadPdbString(pdb: string): Promise<void> {
    if (!pdb || !pdb.trim()) {
      console.warn("[MolSysViewer] Empty PDB string; nothing to load.");
      return;
    }

    console.log("[MolSysViewer] loadPdbString, length =", pdb.length);
    await this.viewer.loadStructureFromData(pdb, "pdb");
  }

  setBasicRepresentation(type: BasicRepresentationType): void {
    console.log("[MolSysViewer] setBasicRepresentation:", type);
    // Más adelante mapearemos aquí 'cartoon', 'sticks', etc. a presets de Mol*
  }

  resetCamera(): void {
    console.log("[MolSysViewer] resetCamera");
    this.viewer.resetCamera();
  }

  setFrame(index: number): void {
    console.log("[MolSysViewer] setFrame:", index);
    // Cuando tengamos trayectoria, hablaremos con el timeline de Mol*
  }

  // ------------------------------------------------------------------
  // Esfera de prueba (stub por ahora)
  // ------------------------------------------------------------------
  async drawTestSphere(options: {
    center: number[];
    radius: number;
    color: number[];
    opacity: number;
  }): Promise<void> {
    console.log("[MolSysViewer] drawTestSphere (stub) called with:", options);

    // Próximo paso: aquí crearemos un Shape con una esfera y lo añadiremos
    // al estado de Mol* usando this.plugin. De momento solo confirmamos que
    // el mensaje llega correctamente desde Python.
  }
}

