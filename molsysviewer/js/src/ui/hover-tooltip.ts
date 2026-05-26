/**
 * HoverTooltip – floating overlay that follows the mouse pointer and shows the
 * label of the hovered Mol* loci.  Works for all loci kinds: structure elements,
 * shapes (tetrahedra, spheres, etc.), annotations, and measurements.
 *
 * The tooltip subscribes to `plugin.behaviors.labels.highlight` which is
 * populated by the built-in `DefaultLociLabelProvider` behavior and the
 * `LociLabelManager`.  It therefore automatically picks up the label returned
 * by `shape.getLabel(groupId)` for custom Shape representations.
 */

export class HoverTooltip {
    private readonly el: HTMLDivElement;
    private readonly host: HTMLElement;
    private lastMouseX = 0;
    private lastMouseY = 0;
    private readonly onMouseMove: (e: MouseEvent) => void;

    constructor(host: HTMLElement, plugin: any) {
        this.host = host;

        this.el = document.createElement("div");
        this.el.setAttribute("data-molsysviewer-hover-tooltip", "true");
        Object.assign(this.el.style, {
            position: "absolute",
            display: "none",
            maxWidth: "380px",
            padding: "5px 10px",
            borderRadius: "8px",
            background: "rgba(14, 14, 18, 0.90)",
            color: "#eee",
            boxShadow: "0 4px 16px rgba(0,0,0,0.32)",
            zIndex: "30",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "11.5px",
            lineHeight: "1.35",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            transition: "opacity 80ms ease",
        });
        host.appendChild(this.el);

        // Track mouse position relative to host
        this.onMouseMove = (e: MouseEvent) => {
            const rect = this.host.getBoundingClientRect();
            this.lastMouseX = e.clientX - rect.left;
            this.lastMouseY = e.clientY - rect.top;
            this.reposition();
        };
        host.addEventListener("mousemove", this.onMouseMove, { passive: true });

        // Subscribe to Mol*'s label highlight observable
        const labelsObs = plugin?.behaviors?.labels?.highlight;
        if (typeof labelsObs?.subscribe === "function") {
            labelsObs.subscribe((ev: { labels: string[] }) => {
                this.setLabels(ev.labels);
            });
        }
    }

    private setLabels(labels: string[]) {
        const text = labels.filter(l => !!l).join(" · ");
        if (!text) {
            this.el.style.display = "none";
            return;
        }
        this.el.innerHTML = text;
        this.el.style.display = "block";
        this.reposition();
    }

    private reposition() {
        if (this.el.style.display === "none") return;

        const hostRect = this.host.getBoundingClientRect();
        const elWidth = this.el.offsetWidth;
        const elHeight = this.el.offsetHeight;

        const offsetX = 14;
        const offsetY = 18;

        let x = this.lastMouseX + offsetX;
        let y = this.lastMouseY + offsetY;

        // Keep within host bounds
        if (x + elWidth > hostRect.width - 4) {
            x = this.lastMouseX - elWidth - 8;
        }
        if (y + elHeight > hostRect.height - 4) {
            y = this.lastMouseY - elHeight - 8;
        }
        if (x < 4) x = 4;
        if (y < 4) y = 4;

        this.el.style.left = `${x}px`;
        this.el.style.top = `${y}px`;
    }

    dispose() {
        this.host.removeEventListener("mousemove", this.onMouseMove);
        this.el.remove();
    }
}
