import { bootPopup } from "../popup/popup-logic";

export class PopupHostManager {
    private popoutWin: Window | null = null;
    public isReady = false;

    constructor(private viewerJsSource: string) {}

    get isOpen() {
        return this.popoutWin && !this.popoutWin.closed;
    }

    async open() {
        if (this.isOpen) {
            this.close();
            return;
        }

        this.popoutWin = window.open("", "_blank", "width=960,height=720");
        if (!this.popoutWin) return;
        
        this.isReady = false;
        const doc = this.popoutWin.document;
        
        doc.open();
        doc.write(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>MolSysViewer Popout</title>
  <style>
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #111; }
    #molsysviewer-pop { position: relative; width: 100%; height: 100%; min-height: 400px; }
    /* ... (styles kept same as before for brevity, assuming user wants robust logic) ... */
    .molsysviewer-controls, .molsysviewer-controls * { user-select: none; -webkit-user-select: none; -moz-user-select: none; }
    .molsysviewer-traj-input::-webkit-inner-spin-button,
    .molsysviewer-traj-input::-webkit-outer-spin-button { -webkit-appearance: none !important; margin: 0 !important; }
    .molsysviewer-traj-input { -moz-appearance: textfield !important; appearance: none !important; color: rgba(255,255,255,0.9); background: rgba(40,40,40,0.6); }
    .molsysviewer-slider { background: transparent; height: 16px; border-radius: 999px; overflow: visible; }
    .molsysviewer-slider::-webkit-slider-runnable-track { background: rgba(200,200,200,0.35) !important; height: 16px; border-radius: 999px; }
    .molsysviewer-slider::-webkit-slider-thumb { -webkit-appearance: none !important; width: 16px; height: 16px; border-radius: 50% !important; background: rgba(0,0,0,0.5) !important; margin-top: 0px; }
  </style>
</head>
<body>
  <div id="molsysviewer-pop"></div>
</body>
</html>
        `);
        doc.close();

        // Robust Injection Strategy: Direct Blob from Payload
        try {
            if (!this.viewerJsSource) {
                throw new Error("No viewer source code provided to PopupHostManager");
            }
            
            // Create Blob in Popup context
            // NOTE: We create the Blob in the popup's window context to avoid cross-origin tainting for some browsers
            const popBlob = new this.popoutWin.Blob([this.viewerJsSource], { type: 'text/javascript' });
            const popBlobUrl = this.popoutWin.URL.createObjectURL(popBlob);
            
            console.log("[MolSysViewer Host] Injected viewer source to popup as:", popBlobUrl);

            // Inject bootstrapper
            const scriptEl = doc.createElement("script");
            scriptEl.type = "module";
            scriptEl.textContent = `
                (async () => {
                    try {
                        // Import the cloned blob
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
                        // Clean up the blob URL to free memory
                        URL.revokeObjectURL("${popBlobUrl}");
                    }
                })();
            `;
            doc.body.appendChild(scriptEl);

        } catch (err) {
            console.error("[MolSysViewer Host] Failed to inject viewer to popup:", err);
        }

        // Monitor closure
        const interval = window.setInterval(() => {
            if (!this.popoutWin || this.popoutWin.closed) {
                this.popoutWin = null;
                this.isReady = false;
                window.clearInterval(interval);
            }
        }, 2000);
    }

    close() {
        if (this.popoutWin) {
            this.popoutWin.close();
            this.popoutWin = null;
            this.isReady = false;
        }
    }

    send(type: string, data: any) {
        if (!this.isReady || !this.popoutWin || this.popoutWin.closed) return;
        try {
            this.popoutWin.postMessage({ type, data, from: "host" }, "*");
        } catch (e) {
            console.warn("[MolSysViewer Host] Popout message failed", e);
        }
    }
}
