import type { NavigateItem } from "../group-panel";
import { PanelContext, StudioPanel } from "./types";
import { makeRowElement, makeSectionHeader } from "./ui-helpers";

/**
 * Studio → Shapes subpanel.
 *
 * A pure inspector/manager: it lists the scene's 3D shapes (`view.shapes`).
 * Each item already carries its own activate/visibility/delete callbacks, so
 * the panel only renders and keeps its tab badge in sync. First panel migrated
 * to the panel-per-module architecture (proof of the pattern).
 */
export class ShapesPanel implements StudioPanel {
    readonly key = "shapes";
    private host: HTMLElement | null = null;
    private items: NavigateItem[] = [];

    constructor(private readonly ctx: PanelContext) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    /** Domain slice: the current list of shapes. */
    setItems(items: NavigateItem[]): void {
        this.items = [...items];
        this.ctx.setBadge(String(this.items.length));
        this.render();
    }

    private render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("3D Shapes"));

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.host.appendChild(list);

        if (this.items.length > 0) {
            for (const item of this.items) {
                list.appendChild(makeRowElement(
                    item.title,
                    item.subtitle || "Geometry",
                    item.onActivate,
                    item.onDelete,
                    { hidden: item.hidden, onToggleVisibility: item.onToggleVisibility },
                ));
            }
        } else {
            const empty = document.createElement("div");
            Object.assign(empty.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            empty.textContent = "No shapes yet.";
            list.appendChild(empty);
        }
    }
}
