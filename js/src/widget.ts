
// js/src/widget.ts

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from "@jupyter-widgets/base";

import { MolstarController } from "./molstar_plugin";

// These constants must match the strings used in the Python widget
const MODULE_NAME = "molsysviewer";
const MODULE_VERSION = "^0.0.0"; // Adjust when you publish versions


// ---------------------------------------------------------------------------
// Model
// ---------------------------------------------------------------------------

export class MolSysViewerModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: "MolSysViewerModel",
      _view_name: "MolSysViewerView",
      _model_module: MODULE_NAME,
      _view_module: MODULE_NAME,
      _model_module_version: MODULE_VERSION,
      _view_module_version: MODULE_VERSION,

      // Custom sync attributes (mirroring Python traitlets)
      state: {},
      frame: 0,
    };
  }

  static model_name = "MolSysViewerModel";
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;

  static view_name = "MolSysViewerView";
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any custom serializers here if needed later
  };
}


// ---------------------------------------------------------------------------
// View
// ---------------------------------------------------------------------------

export class MolSysViewerView extends DOMWidgetView {
  private container: HTMLDivElement | null = null;
  private controller: MolstarController | null = null;

  render(): void {
    // Create a container div for Mol*
    this.container = document.createElement("div");
    this.container.classList.add("molsysviewer-container");
    this.el.appendChild(this.container);

    // Initialize Mol* controller (placeholder for now)
    this.controller = new MolstarController({
      container: this.container,
    });

    // Listen to custom messages from the Python side
    this.model.on("msg:custom", this.onCustomMessage, this);

    // Optionally, react to frame changes via synced attribute
    this.model.on("change:frame", this.onFrameChanged, this);
  }

  // -----------------------------------------------------------------------
  // Handling custom messages from Python
  // -----------------------------------------------------------------------
  private onCustomMessage(msg: any): void {
    const op = msg?.op;
    const payload = msg?.payload ?? {};

    if (!this.controller) {
      console.warn("[MolSysViewer] Controller not initialized yet.");
      return;
    }

    switch (op) {
      case "LOAD_PDB_STRING":
        this.controller.loadPdbString(payload.pdb ?? "");
        break;

      case "SET_REPRESENTATION_BASIC":
        this.controller.setBasicRepresentation(payload.type ?? "cartoon");
        break;

      case "RESET_CAMERA":
        this.controller.resetCamera();
        break;

      case "SET_FRAME":
        // We both update controller and sync to model frame attr
        if (typeof payload.index === "number") {
          this.controller.setFrame(payload.index);
          this.model.set("frame", payload.index);
          this.touch();
        }
        break;

      default:
        console.warn("[MolSysViewer] Unknown op:", op, "payload:", payload);
        break;
    }
  }

  // -----------------------------------------------------------------------
  // React to traitlet changes (e.g., frame changed from Python)
  // -----------------------------------------------------------------------
  private onFrameChanged(): void {
    if (!this.controller) return;
    const frame = this.model.get("frame");
    if (typeof frame === "number") {
      this.controller.setFrame(frame);
    }
  }
}
