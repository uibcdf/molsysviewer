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
        if (!items || items.length === 0) {
            this.root.style.display = "none";
            this.root.replaceChildren();
            return;
        }

        Object.assign(this.root.style, {
            top: position.startsWith("top") ? "12px" : "",
            bottom: position.startsWith("bottom") ? "12px" : "",
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

    dispose() {
        this.root.remove();
    }
}
