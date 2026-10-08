/** Observable UI traits for exported pages and popups without a widget model. */
export function createLocalUiModel(initial: Record<string, unknown> = {}) {
    const values: Record<string, unknown> = {
        viewer_mode: "integrated", controls_mode: "minimal", panel_mode_style: "integrated",
        show_controls: true, autohide_controls: true, autohide_scope: "controls",
        controls_position: ["top", "right"], controls_position_fullscreen: ["top", "right"],
        ...initial,
    };
    const listeners = new Map<string, Set<() => void>>();
    return {
        get: (key: string) => values[key],
        set(key: string, value: unknown) {
            if (values[key] === value) return;
            values[key] = value;
            for (const listener of [...(listeners.get(`change:${key}`) || [])]) listener();
        },
        on(event: string, callback: () => void) {
            if (!listeners.has(event)) listeners.set(event, new Set());
            listeners.get(event)!.add(callback);
        },
        off(event: string, callback: () => void) { listeners.get(event)?.delete(callback); },
        save_changes() {},
    };
}
