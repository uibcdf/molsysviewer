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
        // Preserve the user's in-progress field (rename input, slider, query box)
        // across the repaint so a background update never steals focus/caret.
        const snapshot = this.captureActiveField();
        this.paint();
        this.restoreActiveField(snapshot);
    }

    private captureActiveField(): { selector: string; value: string; start: number | null; end: number | null } | null {
        try {
            const doc = this.host?.ownerDocument;
            const active = doc?.activeElement as HTMLInputElement | null;
            if (!active || !this.host || typeof this.host.contains !== "function" || !this.host.contains(active)) return null;
            const tag = active.tagName;
            if (tag !== "INPUT" && tag !== "TEXTAREA") return null;
            const attr = Array.from(active.attributes ?? []).find(a => a.name.startsWith("data-molsysviewer-"));
            if (!attr) return null;
            return {
                selector: `[${attr.name}="${attr.value}"]`,
                value: active.value,
                start: active.selectionStart ?? null,
                end: active.selectionEnd ?? null,
            };
        } catch {
            return null;
        }
    }

    private restoreActiveField(snap: { selector: string; value: string; start: number | null; end: number | null } | null): void {
        if (!snap || !this.host) return;
        try {
            const el = this.host.querySelector(snap.selector) as HTMLInputElement | null;
            if (!el) return;
            el.value = snap.value;
            el.focus();
            if (typeof el.setSelectionRange === "function") {
                const end = snap.end ?? snap.value.length;
                el.setSelectionRange(snap.start ?? end, end);
            }
        } catch {
            // best-effort; never break a paint over focus restoration
        }
    }

    /** One-time setup on mount, before the first paint. Override as needed. */
    protected onMount(): void {}

    /** Build the panel's DOM into `this.host`. Called only when visible and dirty. */
    protected abstract paint(): void;
}
