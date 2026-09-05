type HelpRow = [string, string];

export interface HelpOverlaySections {
    mouse: HelpRow[];
    keyboard: HelpRow[];
}

const DEFAULT_SECTIONS: HelpOverlaySections = {
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
        ["N", "Open / close Studio"],
        ["W", "Open / close Workbench"],
        ["V", "Toggle canvas visibility"],
        ["H", "Toggle this help"],
        ["Esc", "Close panel / cancel"],
    ],
};

function injectHelpStyles(): void {
    const styleId = "molsysviewer-help-styles";
    if (document.getElementById(styleId)) return;

    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
        .molsysviewer-help-card {
            width: min(640px, 88%);
            height: min(480px, calc(100% - 40px));
            overflow-y: auto;
            background: rgba(18, 18, 22, 0.92);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 24px 64px rgba(0,0,0,0.45);
            color: #f4f4f5;
            font-family: "IBM Plex Sans", system-ui, sans-serif;
            font-size: 13px;
            padding: 20px 24px 24px;
            box-sizing: border-box;
            transition: all 150ms cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        
        /* Custom elegant scrollbar for the help card */
        .molsysviewer-help-card::-webkit-scrollbar {
            width: 4px;
        }
        .molsysviewer-help-card::-webkit-scrollbar-track {
            background: transparent;
        }
        .molsysviewer-help-card::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 99px;
        }
        .molsysviewer-help-card::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .molsysviewer-help-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .molsysviewer-help-title {
            font-weight: 600;
            font-size: 14px;
        }
        .molsysviewer-help-close {
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.45);
            cursor: default;
            padding: 4px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 5px;
            transition: color 120ms ease;
        }
        .molsysviewer-help-close:hover {
            color: rgba(255, 255, 255, 0.9);
        }
        .molsysviewer-help-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
        }
        .molsysviewer-help-section-title {
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            opacity: 0.45;
            margin-bottom: 10px;
        }
        .molsysviewer-help-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .molsysviewer-help-key {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            padding: 2px 7px;
            font-size: 11px;
            font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
            white-space: nowrap;
            flex-shrink: 0;
            line-height: 1.6;
        }
        .molsysviewer-help-desc {
            opacity: 0.75;
            text-align: right;
            font-size: 12px;
        }
    `;
    document.head.appendChild(style);
}

function makeSection(heading: string, rows: HelpRow[]): HTMLDivElement {
    const section = document.createElement("div");

    const h = document.createElement("div");
    h.className = "molsysviewer-help-section-title";
    h.textContent = heading;
    section.appendChild(h);

    for (const [key, desc] of rows) {
        const row = document.createElement("div");
        row.className = "molsysviewer-help-row";

        const keyEl = document.createElement("span");
        keyEl.className = "molsysviewer-help-key";
        keyEl.textContent = key;

        const descEl = document.createElement("span");
        descEl.className = "molsysviewer-help-desc";
        descEl.textContent = desc;

        row.appendChild(keyEl);
        row.appendChild(descEl);
        section.appendChild(row);
    }

    return section;
}

export class HelpOverlay {
    private readonly root: HTMLDivElement;
    private visible = false;
    private releaseKeyHandler?: () => void;

    constructor(
        private readonly host: HTMLElement,
        sections: HelpOverlaySections = DEFAULT_SECTIONS,
    ) {
        injectHelpStyles();

        this.root = document.createElement("div");
        Object.assign(this.root.style, {
            position: "absolute",
            inset: "0",
            display: "none",
            alignItems: "center",
            justifyContent: "center",
            zIndex: "40",
            pointerEvents: "auto",
        });

        const card = document.createElement("div");
        card.className = "molsysviewer-help-card";

        // Header
        const header = document.createElement("div");
        header.className = "molsysviewer-help-header";

        const title = document.createElement("span");
        title.className = "molsysviewer-help-title";
        title.textContent = "Canvas Quick Reference";

        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.title = "Close (H or Esc)";
        closeBtn.className = "molsysviewer-help-close";
        closeBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>`;
        closeBtn.addEventListener("click", () => this.hide());

        header.appendChild(title);
        header.appendChild(closeBtn);
        card.appendChild(header);

        // Two-column grid
        const grid = document.createElement("div");
        grid.className = "molsysviewer-help-grid";

        grid.appendChild(makeSection("Mouse", sections.mouse));
        grid.appendChild(makeSection("Keyboard", sections.keyboard));

        card.appendChild(grid);

        // Close on backdrop click
        this.root.addEventListener("pointerdown", (ev) => {
            if (ev.target === this.root) this.hide();
        });

        this.root.appendChild(card);
        this.host.appendChild(this.root);
    }

    public onVisibilityChange?: (visible: boolean) => void;

    toggle(): void {
        this.visible ? this.hide() : this.show();
    }

    show(): void {
        this.visible = true;
        this.root.style.display = "flex";
        this.onVisibilityChange?.(true);

        const onKey = (ev: KeyboardEvent) => {
            if ((ev.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return;
            if (!this.host.contains(ev.target as Node)) return;
            if (ev.key === "Escape" || ev.key.toLowerCase() === "h") {
                ev.stopPropagation();
                this.hide();
            }
        };
        window.addEventListener("keydown", onKey, true);
        this.releaseKeyHandler = () => window.removeEventListener("keydown", onKey, true);
    }

    hide(): void {
        this.visible = false;
        this.root.style.display = "none";
        this.onVisibilityChange?.(false);
        this.releaseKeyHandler?.();
        this.releaseKeyHandler = undefined;
    }

    isVisible(): boolean { return this.visible; }

    dispose(): void {
        this.hide();
        this.root.remove();
    }
}
