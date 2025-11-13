// js/src/index.ts

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from "@jupyterlab/application";

import {
  IJupyterWidgetRegistry,
} from "@jupyter-widgets/base";

import {
  MolSysViewerModel,
  MolSysViewerView,
} from "./widget";

// Plugin de JupyterLab que registra nuestro widget
const EXTENSION_ID = "molsysviewer:plugin";

const extension: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  autoStart: true,
  requires: [IJupyterWidgetRegistry],
  activate: (app: JupyterFrontEnd, registry: IJupyterWidgetRegistry) => {
    console.log("[MolSysViewer] registering widget with IJupyterWidgetRegistry");

    registry.registerWidget({
      name: "molsysviewer",
      version: "0.0.0",
      exports: {
        MolSysViewerModel,
        MolSysViewerView,
      },
    });
  },
};

export default extension;
export { MolSysViewerModel, MolSysViewerView };

