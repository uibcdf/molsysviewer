export class PopupHostManager {
    private popoutWin: Window | null = null;
    private panelWin: Window | null = null;
    public isReady = false;
    public isPanelReady = false;

    private readonly viewerJsSource: string;
    private readonly viewerModuleUrl?: string;

    constructor(viewer: string | { source?: string; moduleUrl?: string }) {
        if (typeof viewer === "string") {
            this.viewerJsSource = viewer;
            return;
        }
        this.viewerJsSource = viewer.source ?? "";
        this.viewerModuleUrl = viewer.moduleUrl;
    }

    private controller?: any;

    setController(controller: any) {
        this.controller = controller;
    }

    get isCanvasOpen() {
        return this.popoutWin && !this.popoutWin.closed;
    }

    get isPanelOpen() {
        return this.panelWin && !this.panelWin.closed;
    }

    async open(mode: "canvas" | "panel" = "canvas") {
        const isOpen = mode === "canvas" ? this.isCanvasOpen : this.isPanelOpen;
        if (isOpen) {
            this.close(mode);
            return;
        }

        let resolvedModuleUrl: string | null = null;
        if (this.viewerModuleUrl) {
            try {
                resolvedModuleUrl = new URL(this.viewerModuleUrl, window.location.href).href;
                fetch(resolvedModuleUrl, { cache: "force-cache" }).catch(() => {});
            } catch (e) {
                resolvedModuleUrl = null;
            }
        }

        const win = window.open("", "_blank", mode === "canvas" ? "width=960,height=720" : "width=450,height=800");
        if (!win) return;

        if (mode === "canvas") {
            this.popoutWin = win;
            this.isReady = false;
        } else {
            this.panelWin = win;
            this.isPanelReady = false;
        }

        if (this.controller) {
            (win as any).molsysviewer_init_options = {
                viewerMode: this.controller.getViewerMode(),
                controlsMode: this.controller.getControlsMode(),
                panelModeStyle: mode === "panel" ? "split" : this.controller.getPanelModeStyle(),
                isAmbient: this.controller.sharedShell?.isAmbient,
                isSplit: this.controller.sharedShell?.isSplit,
                isPanelOnly: mode === "panel",
                activePanel: this.controller.getActivePanel() || "navigate",
            };
        }
        
        const doc = win.document;
        
        doc.open();
        doc.write(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${mode === "canvas" ? "MolSysViewer Popout" : "MolSysViewer Panel"}</title>
  <style>
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #121216; }
    #molsysviewer-pop { position: relative; width: 100%; height: 100%; min-height: 400px; }
    #molsysviewer-loading { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: #fff; font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; font-size: 14px; letter-spacing: 0.2px; background: #121216; z-index: 1000; transition: opacity 240ms ease; }
    #molsysviewer-loading .spinner { width: 28px; height: 28px; border-radius: 999px; border: 3px solid rgba(255,255,255,0.12); border-top-color: rgba(255,255,255,0.45); animation: molsysviewer-spin 0.9s linear infinite; }
    @keyframes molsysviewer-spin { to { transform: rotate(360deg); } }
    .molsysviewer-controls { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "DejaVu Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; }
    .molsysviewer-controls button,
    .molsysviewer-controls input,
    .molsysviewer-controls select,
    .molsysviewer-controls textarea,
    .molsysviewer-controls span { font-family: inherit; }
    .molsysviewer-controls, .molsysviewer-controls * { user-select: none; -webkit-user-select: none; -moz-user-select: none; }
    .molsysviewer-traj-input::-webkit-inner-spin-button,
    .molsysviewer-traj-input::-webkit-outer-spin-button { -webkit-appearance: none !important; margin: 0 !important; }
    .molsysviewer-traj-input { -moz-appearance: textfield !important; appearance: none !important; color: rgba(255,255,255,0.9); background: rgba(40,40,40,0.6); }
    .molsysviewer-slider { background: transparent; height: 16px; border-radius: 999px; overflow: visible; }
    .molsysviewer-slider::-webkit-slider-runnable-track { background: rgba(200,200,200,0.35) !important; height: 16px; border-radius: 999px; }
    .molsysviewer-slider::-webkit-slider-thumb { -webkit-appearance: none !important; width: 16px; height: 16px; border-radius: 50% !important; background: rgba(0,0,0,0.5) !important; margin-top: 0px; }
  </style>
  ${resolvedModuleUrl ? `<link rel="modulepreload" href="${resolvedModuleUrl}">` : ""}
</head>
<body>
  <div id="molsysviewer-loading"><div class="spinner"></div><div>Loading...</div></div>
  <div id="molsysviewer-pop"></div>
</body>
</html>
        `);
        doc.close();

        try {
            const scriptEl = doc.createElement("script");
            scriptEl.type = "module";
            if (this.viewerModuleUrl) {
                scriptEl.textContent = `
                    (async () => {
                        try {
                            const module = await import("${resolvedModuleUrl ?? ""}");
                            const boot = module.bootPopup || (module.default && module.default.bootPopup);
                            if (boot) {
                                boot(module);
                            } else {
                                console.error("MolSysViewer Popout: bootPopup not found in module");
                            }
                        } catch (e) {
                            console.error("MolSysViewer Popout: Boot failed", e);
                        }
                    })();
                `;
            } else {
                if (!this.viewerJsSource) {
                    throw new Error("No viewer source code provided to PopupHostManager");
                }
                const popBlob = new win.Blob([this.viewerJsSource], { type: "text/javascript" });
                const popBlobUrl = win.URL.createObjectURL(popBlob);

                console.log("[MolSysViewer Host] Injected viewer source to popup as:", popBlobUrl);

                scriptEl.textContent = `
                    (async () => {
                        try {
                            const module = await import("${popBlobUrl}");
                            const boot = module.bootPopup || (module.default && module.default.bootPopup);
                            if (boot) {
                                boot(module);
                            } else {
                                console.error("MolSysViewer Popout: bootPopup not found in module");
                            }
                        } catch (e) {
                            console.error("MolSysViewer Popout: Boot failed", e);
                        } finally {
                            URL.revokeObjectURL("${popBlobUrl}");
                        }
                    })();
                `;
            }
            doc.body.appendChild(scriptEl);

        } catch (err) {
            console.error("[MolSysViewer Host] Failed to inject viewer to popup:", err);
        }

        // Monitor closure
        const interval = window.setInterval(() => {
            if (mode === "canvas") {
                if (!this.popoutWin || this.popoutWin.closed) {
                    this.popoutWin = null;
                    this.isReady = false;
                    window.clearInterval(interval);
                }
            } else {
                if (!this.panelWin || this.panelWin.closed) {
                    this.panelWin = null;
                    this.isPanelReady = false;
                    window.clearInterval(interval);
                    // Automatically restore host card when panel window is closed
                    if (this.controller?.sharedShell) {
                        this.controller.sharedShell.setVisible(true);
                    }
                }
            }
        }, 1000);
    }

    close(mode: "canvas" | "panel" = "canvas") {
        if (mode === "canvas") {
            if (this.popoutWin) {
                this.popoutWin.close();
                this.popoutWin = null;
                this.isReady = false;
            }
        } else {
            if (this.panelWin) {
                this.panelWin.close();
                this.panelWin = null;
                this.isPanelReady = false;
            }
        }
    }

    send(type: string, data: any) {
        if (this.isReady && this.popoutWin && !this.popoutWin.closed) {
            try {
                this.popoutWin.postMessage({ type, data, from: "host" }, "*");
            } catch (e) {
                console.warn("[MolSysViewer Host] Popout message failed", e);
            }
        }
        if (this.isPanelReady && this.panelWin && !this.panelWin.closed) {
            try {
                this.panelWin.postMessage({ type, data, from: "host" }, "*");
            } catch (e) {
                console.warn("[MolSysViewer Host] Panel message failed", e);
            }
        }
    }
}
