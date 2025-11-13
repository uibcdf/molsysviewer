// js/src/molstar_plugin.ts

// @ts-ignore  -> por si los types no encajan al 100%
import { Viewer } from "molstar/lib/apps/viewer/app";

export type BasicRepresentationType =
  | "cartoon"
  | "sticks"
  | "surface"
  | string;

export interface MolstarControllerOptions {
  container: HTMLElement;
}

export class MolstarController {
  private container: HTMLElement;
  private viewer: any;
  private plugin: any;

  constructor(options: MolstarControllerOptions) {
    this.container = options.container;

    console.log("[MolSysViewer] Molstar Viewer import:", Viewer);

    const viewerOptions: any = {
      target: this.container,
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
    };

    this.viewer = new Viewer(viewerOptions);
    this.plugin = (this.viewer as any).plugin;

    console.log(
      "[MolSysViewer] Molstar Viewer instance created:",
      this.viewer,
    );
  }

  // ------------------------------------------------------------------
  // Cargar un PDB desde string
  // ------------------------------------------------------------------
  async loadPdbString(pdb: string): Promise<void> {
    if (!pdb || !pdb.trim()) {
      console.warn("[MolSysViewer] Empty PDB string; nothing to load.");
      return;
    }

    console.log("[MolSysViewer] loadPdbString, length =", pdb.length);
    const v: any = this.viewer;

    if (typeof v.loadStructureFromData === "function") {
      await v.loadStructureFromData(pdb, "pdb");
    } else {
      console.warn(
        "[MolSysViewer] viewer.loadStructureFromData is not available.",
        v,
      );
    }
  }

  setBasicRepresentation(type: BasicRepresentationType): void {
    console.log("[MolSysViewer] setBasicRepresentation:", type);
  }

  resetCamera(): void {
    console.log("[MolSysViewer] resetCamera");
    const v: any = this.viewer;
    if (typeof v.plugin?.canvas3d?.setProps === "function") {
      v.plugin.canvas3d.setProps({ camera: { resetTimeMs: 0 } });
    } else if (typeof v.resetCamera === "function") {
      v.resetCamera();
    } else {
      console.warn("[MolSysViewer] No camera reset API found on viewer.", v);
    }
  }

  setFrame(index: number): void {
    console.log("[MolSysViewer] setFrame:", index);
  }

  async drawTestSphere(options: {
    center: number[];
    radius: number;
    color: number[];
    opacity: number;
  }): Promise<void> {
    console.log("[MolSysViewer] drawTestSphere (stub) called with:", options);
  }
}

