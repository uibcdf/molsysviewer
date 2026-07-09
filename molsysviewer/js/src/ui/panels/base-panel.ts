import { StudioPanel } from "./types";

/**
 * Base class for content subpanels with render-on-show semantics.
 *
 * A panel paints once on mount so its DOM exists immediately. After that it
 * only repaints when it is the visible tab: domain-state setters call
 * `scheduleRender()`, which paints immediately if visible or marks the panel
 * dirty otherwise; the deferred paint runs when the tab is next shown. This
 * avoids rebuilding hidden panels on frequent updates (selection clicks,
 * trajectory frames) with 10 subpanels. The host orchestrator drives visibility
 * through `setVisible()`.
 */
export abstract class BasePanel implements StudioPanel {
    abstract readonly key: string;
    protected host: HTMLElement | null = null;
    private panelVisible = false;
    private dirty = true;

    mount(host: HTMLElement): void {
        this.host = host;
        this.onMount();
        this.dirty = true;
        this.flush();
    }

    setVisible(visible: boolean): void {
        this.panelVisible = visible;
        if (visible) this.flush();
    }

    /** Request a repaint: paints now if visible, otherwise defers until shown. */
    protected scheduleRender(): void {
        this.dirty = true;
        if (this.panelVisible) this.flush();
    }

    private flush(): void {
        if (!this.host || !this.dirty) return;
        this.dirty = false;
        this.paint();
    }

    /** One-time setup on mount, before the first paint. Override as needed. */
    protected onMount(): void {}

    /** Build the panel's DOM into `this.host`. Called only when visible and dirty. */
    protected abstract paint(): void;
}
