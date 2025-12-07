import { bootPopup } from "../popup/popup-logic";

export class PopupHostManager {
    private popoutWin: Window | null = null;
    public isReady = false;

    constructor(private viewerJsPath: string) {}

    get isOpen() {
        return this.popoutWin && !this.popoutWin.closed;
    }

    open() {
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
    .molsysviewer-controls, .molsysviewer-controls * { user-select: none; -webkit-user-select: none; -moz-user-select: none; }
    .molsysviewer-traj-input::-webkit-inner-spin-button,
    .molsysviewer-traj-input::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        appearance: none !important;
        -moz-appearance: none !important;
        margin: 0 !important;
    }
    .molsysviewer-traj-input {
        -moz-appearance: textfield !important;
        appearance: none !important;
        -webkit-appearance: none !important;
        color: rgba(255,255,255,0.9);
        background: rgba(40,40,40,0.6);
        caret-color: transparent;
    }
    .molsysviewer-slider {
        background: transparent;
        height: 16px;
        border-radius: 999px;
        overflow: visible;
    }
    .molsysviewer-slider::-webkit-slider-runnable-track {
        background: rgba(200,200,200,0.35) !important;
        height: 16px;
        border-radius: 999px;
    }
    .molsysviewer-slider::-moz-range-track {
        background: rgba(200,200,200,0.35) !important;
        height: 16px;
        border-radius: 999px;
    }
    .molsysviewer-slider::-ms-track {
        background: rgba(200,200,200,0.35) !important;
        height: 16px;
        border-radius: 999px;
        border: none;
        color: transparent;
    }
    .molsysviewer-slider::-webkit-slider-thumb {
        -webkit-appearance: none !important;
        appearance: none !important;
        width: 16px;
        height: 16px;
        border-radius: 50% !important;
        background: rgba(0,0,0,0.5) !important;
        border: none !important;
        box-shadow: none !important;
        margin-top: 0px;
    }
    .molsysviewer-slider::-webkit-slider-thumb:hover,
    .molsysviewer-slider::-webkit-slider-thumb:active,
    .molsysviewer-slider::-webkit-slider-thumb:focus {
        background: rgba(0,0,0,0.5) !important;
        border: none !important;
        box-shadow: none !important;
    }
    .molsysviewer-slider::-moz-range-thumb {
        width: 16px;
        height: 16px;
        border-radius: 50% !important;
        background: rgba(0,0,0,0.5) !important;
        border: none !important;
    }
    .molsysviewer-slider::-moz-range-thumb:hover,
    .molsysviewer-slider::-moz-range-thumb:active,
    .molsysviewer-slider::-moz-range-thumb:focus {
        background: rgba(0,0,0,0.5) !important;
        border: none !important;
    }
    .molsysviewer-slider::-ms-thumb {
        width: 16px;
        height: 16px;
        border-radius: 50% !important;
        background: rgba(0,0,0,0.5) !important;
        border: none !important;
    }
  </style>
</head>
<body>
  <div id="molsysviewer-pop"></div>
</body>
</html>
        `);
        doc.close();

        // Pass path via global
        Object.assign(this.popoutWin, { molsysviewer_path: this.viewerJsPath });

        // Inject script
        const scriptEl = doc.createElement("script");
        scriptEl.type = "module";
        scriptEl.textContent = `
            (async () => {
                try {
                    const path = window.molsysviewer_path;
                    const module = await import(path);
                    const boot = module.bootPopup || (module.default && module.default.bootPopup);
                    if (boot) {
                        boot(module);
                    } else {
                        console.error("MolSysViewer Popout: bootPopup not found in module", module);
                    }
                } catch (e) {
                    console.error("MolSysViewer Popout: Boot failed", e);
                }
            })();
        `;
        doc.body.appendChild(scriptEl);

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
