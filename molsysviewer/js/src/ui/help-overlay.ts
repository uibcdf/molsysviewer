type HelpRow = [string, string];

function makeSection(heading: string, rows: HelpRow[]): HTMLDivElement {
    const section = document.createElement("div");

    const h = document.createElement("div");
    h.textContent = heading;
    Object.assign(h.style, {
        fontWeight: "600",
        fontSize: "11px",
        textTransform: "uppercase",
        letterSpacing: "0.07em",
        opacity: "0.45",
        marginBottom: "10px",
    });
    section.appendChild(h);

    for (const [key, desc] of rows) {
        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            padding: "5px 0",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
        });

        const keyEl = document.createElement("span");
        keyEl.textContent = key;
        Object.assign(keyEl.style, {
            background: "rgba(255,255,255,0.1)",
            borderRadius: "5px",
            padding: "2px 7px",
            fontSize: "11px",
            fontFamily: "\"IBM Plex Mono\", \"SFMono-Regular\", monospace",
            whiteSpace: "nowrap",
            flexShrink: "0",
            lineHeight: "1.6",
        });

        const descEl = document.createElement("span");
        descEl.textContent = desc;
        Object.assign(descEl.style, {
            opacity: "0.75",
            textAlign: "right",
            fontSize: "12px",
        });

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

    constructor(private readonly host: HTMLElement) {
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
        Object.assign(card.style, {
            width: "min(640px, 88%)",
            background: "rgba(18,18,22,0.95)",
            borderRadius: "16px",
            border: "1px solid rgba(255,255,255,0.14)",
            boxShadow: "0 24px 64px rgba(0,0,0,0.45)",
            color: "#f4f4f5",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "13px",
            padding: "20px 24px 24px",
            boxSizing: "border-box",
        });

        // Header
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "18px",
            paddingBottom: "12px",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
        });

        const title = document.createElement("span");
        title.textContent = "Canvas Quick Reference";
        Object.assign(title.style, { fontWeight: "600", fontSize: "14px" });

        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.title = "Close (H or Esc)";
        closeBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>`;
        Object.assign(closeBtn.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
        });
        closeBtn.addEventListener("mouseenter", () => { closeBtn.style.color = "rgba(255,255,255,0.9)"; });
        closeBtn.addEventListener("mouseleave", () => { closeBtn.style.color = "rgba(255,255,255,0.45)"; });
        closeBtn.addEventListener("click", () => this.hide());

        header.appendChild(title);
        header.appendChild(closeBtn);
        card.appendChild(header);

        // Two-column grid
        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "28px",
        });

        grid.appendChild(makeSection("Mouse", [
            ["Left drag", "Rotate"],
            ["Right drag", "Pan"],
            ["Scroll", "Zoom"],
            ["Left click", "Select element"],
            ["Shift + Click", "Add to selection"],
            ["Shift + Alt + Click", "Range selection (same chain)"],
            ["Double click", "Focus on element"],
            ["Right click", "Context menu"],
        ]));

        grid.appendChild(makeSection("Keyboard", [
            ["N", "Open / close Navigate"],
            ["W", "Open / close Workbench"],
            ["V", "Toggle canvas visibility"],
            ["H", "Toggle this help"],
            ["Esc", "Close panel / cancel"],
        ]));

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
