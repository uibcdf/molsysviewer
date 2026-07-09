// Contracts for the Studio subpanel architecture.
//
// Each subpanel is a self-contained module (a class) that owns its own view
// state and DOM, receives its slice of domain state through typed setters, and
// talks to the host only through the injected `PanelContext`. `GroupPanel` is
// the orchestrator: it builds the tabs, mounts the panels, routes domain state
// to them, and forwards their actions to the controller.

/**
 * The narrow, explicit contract a panel is allowed to use to reach the host.
 * Kept intentionally small so panels stay decoupled from `GroupPanel` internals.
 */
export interface PanelContext {
    /** Emit an action towards the controller (same channel as the legacy `onAction`). */
    onAction(action: string, details?: Record<string, unknown>): void;
    /** Set this panel's own tab badge text. */
    setBadge(text: string): void;
}

/**
 * Common lifecycle every subpanel module implements. Concrete panels add their
 * own typed `set*`/`update*` methods for their domain slice; `GroupPanel` holds
 * a concrete-typed reference to call those.
 */
export interface StudioPanel {
    /** Stable tab key, matching the sidebar registration. */
    readonly key: string;
    /** Attach the panel to its section host (called once). */
    mount(host: HTMLElement): void;
    /** Tell the panel whether it is the visible tab (drives render-on-show). */
    setVisible(visible: boolean): void;
}
