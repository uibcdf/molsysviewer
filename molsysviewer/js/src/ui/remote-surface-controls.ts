import { HelpOverlay, type HelpOverlaySections } from "./help-overlay";

export interface RemoteSurfaceControlsOptions {
    resetView: () => void;
    togglePanel: () => void;
}

const REMOTE_HELP: HelpOverlaySections = {
    mouse: [
        ["Left drag", "Rotate"],
        ["Right drag", "Pan"],
        ["Scroll", "Zoom"],
        ["Left click", "Select element"],
        ["Shift + Click", "Add to selection"],
        ["Shift + Alt + Click", "Range selection (same chain)"],
        ["Double click", "Focus on element"],
        ["Right click", "Context menu"],
    ],
    keyboard: [
        ["N / W", "Open / close Studio"],
        ["H", "Toggle this help"],
        ["Esc", "Close panel / help"],
    ],
};

/** Local chrome for a video-backed remote viewport. */
export class RemoteSurfaceControls {
    readonly root: HTMLDivElement;
    private readonly help: HelpOverlay;
    private readonly fullscreenButton: HTMLButtonElement;

    constructor(
        private readonly host: HTMLElement,
        private readonly options: RemoteSurfaceControlsOptions,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-remote-controls", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            top: "12px",
            right: "12px",
            zIndex: "4",
            display: "flex",
            gap: "4px",
            pointerEvents: "auto",
        });

        this.addButton("Reset", "Reset remote camera", () => this.options.resetView());
        this.fullscreenButton = this.addButton("Full", "Fullscreen", () => {
            void this.toggleFullscreen();
        });
        this.help = new HelpOverlay(host, REMOTE_HELP);
        this.addButton("Help", "Help (H)", () => this.help.toggle());
        this.addButton("Panel", "Open or close Studio (N / W)", () => {
            this.options.togglePanel();
        });
        host.appendChild(this.root);
        window.addEventListener("keydown", this.onKeyDown, true);
        document.addEventListener("fullscreenchange", this.updateFullscreenLabel);
    }

    dispose(): void {
        window.removeEventListener("keydown", this.onKeyDown, true);
        document.removeEventListener("fullscreenchange", this.updateFullscreenLabel);
        this.help.dispose();
        this.root.remove();
    }

    private addButton(label: string, title: string, callback: () => void): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.title = title;
        button.setAttribute("data-molsysviewer-remote-control", label.toLowerCase());
        Object.assign(button.style, {
            height: "22px",
            padding: "2px 6px",
            border: "1px solid rgba(255,255,255,.5)",
            borderRadius: "4px",
            background: "rgba(0,0,0,.5)",
            color: "#fff",
            font: "11px/16px system-ui,sans-serif",
            cursor: "default",
        });
        button.addEventListener("click", callback);
        this.root.appendChild(button);
        return button;
    }

    private readonly onKeyDown = (event: KeyboardEvent): void => {
        if ((event.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return;
        if (!this.host.contains(event.target as Node)) return;
        const key = event.key.toLowerCase();
        if (key === "h" && !this.help.isVisible()) {
            event.preventDefault();
            event.stopPropagation();
            this.help.show();
        } else if (key === "n" || key === "w") {
            event.preventDefault();
            event.stopPropagation();
            this.options.togglePanel();
        }
    };

    private readonly updateFullscreenLabel = (): void => {
        this.fullscreenButton.textContent = document.fullscreenElement ? "Exit" : "Full";
        this.fullscreenButton.title = document.fullscreenElement ? "Exit fullscreen" : "Fullscreen";
    };

    private async toggleFullscreen(): Promise<void> {
        try {
            if (document.fullscreenElement) await document.exitFullscreen();
            else await this.host.requestFullscreen();
        } catch (error) {
            console.error("[MolSysViewer remote client] fullscreen failed", error);
        }
    }
}
