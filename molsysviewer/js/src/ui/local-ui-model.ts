/** Normalize historical UI projections without reviving retired text controls. */
export function normalizeControlsMode(mode: unknown): "compact" | "cinema" {
    return mode === "cinema" ? "cinema" : "compact";
}

export function normalizeViewerMode(mode: unknown): "standard" | "cinema" {
    return mode === "cinema" ? "cinema" : "standard";
}

/** Observable UI traits for exported pages and popups without a widget model. */
export function createLocalUiModel(initial: Record<string, unknown> = {}, onSave?: (values: Record<string, unknown>) => void) {
    const values: Record<string, unknown> = {
        viewer_mode: "standard", controls_mode: "compact", panel_mode_style: "integrated",
        show_controls: true, autohide_controls: true, autohide_scope: "controls",
        controls_position: ["top", "right"], controls_position_fullscreen: ["top", "right"],
        ...initial,
    };
    values.controls_mode = normalizeControlsMode(values.controls_mode);
    values.viewer_mode = normalizeViewerMode(values.viewer_mode);
    const listeners = new Map<string, Set<() => void>>();
    return {
        get: (key: string) => values[key],
        set(key: string, value: unknown) {
            if (key === "controls_mode") value = normalizeControlsMode(value);
            if (key === "viewer_mode") value = normalizeViewerMode(value);
            if (values[key] === value) return;
            values[key] = value;
            for (const listener of [...(listeners.get(`change:${key}`) || [])]) listener();
        },
        on(event: string, callback: () => void) {
            if (!listeners.has(event)) listeners.set(event, new Set());
            listeners.get(event)!.add(callback);
        },
        off(event: string, callback: () => void) { listeners.get(event)?.delete(callback); },
        save_changes() { onSave?.({ ...values }); },
    };
}
