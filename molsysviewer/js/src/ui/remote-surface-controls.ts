import { HelpOverlay, type HelpOverlaySections } from "./help-overlay";
import {
    makeViewportIconButton,
    setViewportIcon,
    VIEWPORT_ICON_EXIT_FULLSCREEN,
    VIEWPORT_ICON_FULLSCREEN,
    VIEWPORT_ICON_HELP,
    VIEWPORT_ICON_PANEL,
    VIEWPORT_ICON_RESET,
} from "./viewport-icon-button";

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

        this.addButton("reset", VIEWPORT_ICON_RESET, "Reset remote camera", () => this.options.resetView());
        this.addButton("panel", VIEWPORT_ICON_PANEL, "Open or close Studio (N / W)", () => {
            this.options.togglePanel();
        });
        this.fullscreenButton = this.addButton("full", VIEWPORT_ICON_FULLSCREEN, "Fullscreen", () => {
            void this.toggleFullscreen();
        });
        this.help = new HelpOverlay(host, REMOTE_HELP);
        this.addButton("help", VIEWPORT_ICON_HELP, "Help (H)", () => this.help.toggle());
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

    private addButton(name: string, icon: string, title: string, callback: () => void): HTMLButtonElement {
        const button = makeViewportIconButton(icon, title, callback);
        button.setAttribute("data-molsysviewer-remote-control", name);
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
        setViewportIcon(
            this.fullscreenButton,
            document.fullscreenElement ? VIEWPORT_ICON_EXIT_FULLSCREEN : VIEWPORT_ICON_FULLSCREEN,
        );
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
