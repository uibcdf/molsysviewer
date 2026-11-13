import { overlayBounds, svgDocument, svgNode, MovieOverlayError, type MovieSvgOverlay } from "./movie-overlay-composition";

export interface LegendItem {
    label: string;
    color: number;
}

/**
 * A small colour-legend overlay pinned to a corner of the viewport. Generic: any
 * colour scheme (component families, clearance bands, affinity classes, …) can
 * feed it `{label, color}` entries via `scene.set_legend(...)`.
 */
export class LegendOverlay {
    private readonly root: HTMLElement;
    private items: LegendItem[] = [];
    private bottomInset = 0;

    constructor(private readonly host: HTMLElement) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-legend", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            top: "12px",
            right: "12px",
            display: "none",
            padding: "8px 10px",
            background: "rgba(20, 20, 20, 0.72)",
            color: "#f2f2f2",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "12px",
            lineHeight: "1.5",
            borderRadius: "6px",
            zIndex: "9",
            pointerEvents: "none",
            maxWidth: "240px",
        });
        this.host.appendChild(this.root);
    }

    set(items: LegendItem[] | undefined, position: string = "top-right") {
        this.items = items?.map(row => ({ ...row })) ?? [];
        if (!items || items.length === 0) {
            this.root.style.display = "none";
            this.root.replaceChildren();
            return;
        }

        Object.assign(this.root.style, {
            top: position.startsWith("top") ? "12px" : "",
            bottom: position.startsWith("bottom") ? `${12 + this.bottomInset}px` : "",
            left: position.endsWith("left") ? "12px" : "",
            right: position.endsWith("right") ? "12px" : "",
        });

        const rows = items.map((it) => {
            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex",
                alignItems: "center",
                gap: "6px",
            });
            const chip = document.createElement("span");
            const hex = "#" + ((it.color >>> 0) & 0xffffff).toString(16).padStart(6, "0");
            Object.assign(chip.style, {
                display: "inline-block",
                width: "12px",
                height: "12px",
                borderRadius: "2px",
                background: hex,
                flex: "0 0 auto",
            });
            const label = document.createElement("span");
            label.textContent = it.label;
            row.replaceChildren(chip, label);
            return row;
        });

        this.root.replaceChildren(...rows);
        this.root.style.display = "block";
    }

    setBottomInset(pixels: number): void {
        this.bottomInset = Number.isFinite(pixels) ? Math.max(0, pixels) : 0;
        if (this.root.style.bottom) this.root.style.bottom = `${12 + this.bottomInset}px`;
    }

    movieSnapshot(): MovieSvgOverlay | undefined {
        if (!this.items.length) return;
        if (this.items.length > 256 || this.items.reduce((size, row) => size + row.label.length, 0) > 16384) {
            throw new MovieOverlayError("MovieOverlayLimit", "Movie legend exceeds 256 entries or 16384 characters.");
        }
        const bounds = overlayBounds(this.root, this.host);
        const root = svgDocument(bounds.width, bounds.height);
        root.appendChild(svgNode("rect", { width: bounds.width, height: bounds.height, rx: 6, fill: "rgba(20,20,20,0.72)" }));
        // Use each rendered row's placement; labels are XML text, never markup.
        const children = Array.from(this.root.children);
        this.items.forEach((item, index) => {
            const row = children[index].getBoundingClientRect(), host = this.root.getBoundingClientRect();
            const y = row.top - host.top;
            root.appendChild(svgNode("rect", { x: 10, y: y + 3, width: 12, height: 12, rx: 2,
                fill: `#${(item.color & 0xffffff).toString(16).padStart(6, "0")}` }));
            const label = children[index].lastElementChild!;
            const range = document.createRange();
            // Preserve CSS word wrapping without accepting arbitrary HTML.
            const text = label.firstChild;
            if (text) {
                let line = "", lastY = -Infinity, x = 28;
                const flush = () => { if (line) root.appendChild(svgNode("text", { x, y: lastY - host.top + 12,
                    fill: "#f2f2f2", "font-size": 12, "font-family": "sans-serif" }, line)); line = ""; };
                for (let offset = 0; offset < (text.textContent?.length ?? 0); offset++) {
                    range.setStart(text, offset); range.setEnd(text, offset + 1);
                    const rect = range.getBoundingClientRect();
                    if (Math.abs(rect.top - lastY) > 1) { flush(); lastY = rect.top; x = rect.left - host.left; }
                    line += text.textContent![offset];
                }
                flush();
            }
        });
        return { kind: "colour_legend", tag: "colour-legend", bounds, svg: new XMLSerializer().serializeToString(root),
            rendering: { opacity: 1, view_box: { width: bounds.width, height: bounds.height } } };
    }

    dispose() {
        this.root.remove();
    }
}
