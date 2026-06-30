/**
 * Non-blocking overlay shown when the WebGL context is lost (GPU crash, sleep/
 * wake, driver reset). Mol* restores the GL resources from the retained scene
 * on `webglcontextrestored`; this overlay only informs the user that recovery
 * is in progress and clears once the context is back.
 */
export class WebGLStatusOverlay {
    private readonly root: HTMLDivElement;

    constructor(private readonly host: HTMLElement) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-webgl-status", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            left: "50%",
            top: "18px",
            transform: "translateX(-50%)",
            display: "none",
            maxWidth: "min(90%, 420px)",
            padding: "10px 14px",
            borderRadius: "12px",
            border: "1px solid rgba(251, 191, 36, 0.45)",
            background: "rgba(28, 22, 10, 0.94)",
            color: "#fde68a",
            boxShadow: "0 12px 28px rgba(0,0,0,0.32)",
            zIndex: "40",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "12px",
            lineHeight: "1.4",
            textAlign: "center",
            pointerEvents: "none",
        });
        this.host.appendChild(this.root);
    }

    show(message: string): void {
        this.root.textContent = message;
        this.root.style.display = "block";
    }

    hide(): void {
        this.root.style.display = "none";
        this.root.textContent = "";
    }

    dispose(): void {
        this.root.remove();
    }
}
