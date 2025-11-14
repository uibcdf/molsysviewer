// js/src/molstar_plugin.ts

// @ts-ignore  -> por si los types no encajan al 100%
import { Viewer } from "molstar/lib/apps/viewer/app";
import { Color } from 'molstar/lib/mol-util/color';
import { Vec3, Mat4 } from 'molstar/lib/mol-math/linear-algebra';
import { MeshBuilder } from 'molstar/lib/mol-geo/geometry/mesh/mesh-builder';
import { addSphere } from 'molstar/lib/mol-geo/geometry/mesh/builder/sphere';
import { Mesh } from 'molstar/lib/mol-geo/geometry/mesh/mesh';
import { Shape } from 'molstar/lib/mol-model/shape';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';

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

  // ------------------------------------------------------------------
  // Dibujar una esfera de prueba (test sphere)
  // ------------------------------------------------------------------
  async drawTestSphere(options: {
    center: number[],   // [x, y, z]
    radius: number,
    color: number[],    // [r, g, b] normalizado 0–1
    opacity: number     // 0–1
  }) {
    console.log("[MolSysViewer] drawTestSphere called:", options);

    const { center, radius, color, opacity } = options;

    // 1. Construimos un Mesh esférico con MeshBuilder + addSphere
    const meshState = MeshBuilder.createState(1, 1);
    // un solo grupo para toda la esfera
    meshState.currentGroup = 0;

    const centerVec = Vec3.create(center[0], center[1], center[2]);
    const detail = 2; // 0 = muy basto, 2–3 = más suave; ajustable

    addSphere(meshState, centerVec, radius, detail);

    const mesh: Mesh = MeshBuilder.getMesh(meshState);

    // 2. Creamos un Shape a partir de ese Mesh
    const c = Color.fromNormalizedRgb(color[0], color[1], color[2]);
    const transforms = [Mat4.identity()];

    const shape = Shape.create(
      'test-sphere',        // id/nombre
      {},                   // "source": puede ser cualquier objeto; aquí vacío
      mesh,                 // geometría
      () => c,              // getColor(groupId)
      () => 1.0,            // getSize(groupId)
      () => 'test-sphere',  // getLabel(groupId)
      transforms
    );

    // 3. Insertamos el Shape en el plugin vía ShapeRepresentation3D
    const plugin = this.plugin;
    const state = plugin.state.data;

    const update = state.build().toRoot()
      .apply(StateTransforms.Representation.ShapeRepresentation3D, {
        shape,
        alpha: opacity,
      });

    await update.commit();
  }

}

