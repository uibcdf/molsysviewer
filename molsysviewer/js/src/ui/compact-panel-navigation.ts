import { makeStyledSelect } from "./panels/ui-helpers";

/** Owns the narrow-card alternative to a panel's sidebar. Domain selection stays with the caller. */
export class CompactPanelNavigation {
    readonly select: HTMLSelectElement;
    private observer?: ResizeObserver;
    constructor(private body: HTMLElement, private sidebar: HTMLElement, private content: HTMLElement,
        label: string, onSelect: (value: string) => void) {
        this.select = makeStyledSelect([], "", onSelect);
        this.select.setAttribute("aria-label", label);
        this.select.setAttribute("data-molsysviewer-compact-navigation", "true");
        Object.assign(this.select.style, { display: "none", width: "100%", flexShrink: "0", marginBottom: "8px", boxSizing: "border-box" });
        body.prepend(this.select);
        if (typeof ResizeObserver !== "undefined") {
            this.observer = new ResizeObserver(() => this.refresh());
            this.observer.observe(body);
        }
    }
    update(items: Array<{ value: string; label: string }>, current: string): void {
        this.select.replaceChildren();
        for (const item of items) {
            const option = document.createElement("option"); option.value = item.value; option.textContent = item.label;
            this.select.appendChild(option);
        }
        this.select.value = current;
        this.refresh();
    }
    refresh(): void {
        const width = this.body.clientWidth;
        if (!width) return; // Hidden workspaces retain their last layout until shown.
        const compact = width < 480;
        this.body.style.flexDirection = compact ? "column" : "row";
        this.sidebar.style.display = compact ? "none" : "flex";
        this.content.style.paddingLeft = compact ? "0" : "12px";
        this.select.style.display = compact ? "block" : "none";
        if (compact && this.sidebar.contains(this.body.ownerDocument.activeElement)) this.select.focus();
    }
    dispose(): void { this.observer?.disconnect(); this.select.remove(); }
}
