import type { NavigateItem } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelContext } from "./types";
import { makeRowElement, makeSectionHeader } from "./ui-helpers";

export interface InspectorListConfig {
    /** Section header text. */
    header: string;
    /** Fallback subtitle when an item has none. */
    subtitleFallback: string;
    /** Text shown when the list is empty. */
    emptyText: string;
}

/**
 * Generic Studio inspector/manager subpanel: a flat list of scene objects
 * (`NavigateItem`), each carrying its own activate/visibility/delete callbacks.
 *
 * Shared by the Shapes, Measures, and Annotations subpanels — three views that
 * differ only in their labels. Owns its own item slice and keeps its tab badge
 * (the item count) in sync.
 */
export class InspectorListPanel extends BasePanel {
    private items: NavigateItem[] = [];

    constructor(
        readonly key: string,
        private readonly ctx: PanelContext,
        private readonly config: InspectorListConfig,
    ) {
        super();
    }

    /** Domain slice: the current list of items. */
    setItems(items: NavigateItem[]): void {
        this.items = [...items];
        this.ctx.setBadge(String(this.items.length));
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader(this.config.header));

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.host.appendChild(list);

        if (this.items.length > 0) {
            for (const item of this.items) {
                const row = makeRowElement(
                    item.title,
                    item.subtitle || this.config.subtitleFallback,
                    item.onActivate,
                    item.onDelete,
                    { hidden: item.hidden, onToggleVisibility: item.onToggleVisibility },
                );
                row.setAttribute("data-molsysviewer-scene-object-kind", this.key);
                row.setAttribute("data-molsysviewer-scene-object-tag", item.key ?? item.title);
                list.appendChild(row);
            }
        } else {
            const empty = document.createElement("div");
            Object.assign(empty.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            empty.textContent = this.config.emptyText;
            list.appendChild(empty);
        }
    }
}
