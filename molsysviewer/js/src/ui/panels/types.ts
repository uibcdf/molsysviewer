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
/**
 * The closed set of action names a subpanel may emit towards the controller.
 * Typing `onAction` against this makes a mistyped action a compile error while
 * keeping call sites as plain string literals. Keep in sync with the controller
 * dispatcher and the Python `core.py` handlers.
 */
export type PanelAction =
    // Selection
    | "apply_selection_query"
    | "selection_query_preview_request"
    | "set_active_selection_operation"
    | "expand_selection"
    | "save_selection"
    | "rename_selection"
    | "delete_selection"
    | "compose_saved_selection"
    | "add_label_from_selection"
    | "create_label_from_saved_selection"
    | "undo_active_selection"
    | "redo_active_selection"
    // Selection -> Region / Region creation
    | "create_region_from_selection"
    | "create_region_from_saved_selection"
    | "create_region_from_query"
    | "make_regions_by"
    // Region lifecycle & style
    | "delete_region"
    | "rename_region"
    | "toggle_region_visibility"
    | "show_only_region"
    | "create_complementary_region"
    | "duplicate_region"
    | "compose_regions"
    | "reset_region_representation"
    | "set_region_representation"
    | "color_region_by_attribute"
    | "reset_region_colors"
    | "get_region_details"
    | "show_all_regions"
    | "hide_all_regions"
    // Layer membership
    | "set_region_layer"
    | "remove_region_from_layer"
    | "set_layer_visibility"
    | "delete_layer_group"
    // Whole lifecycle & style
    | "set_whole_representation"
    | "reset_whole_representation"
    | "set_whole_visibility"
    | "focus_whole"
    | "set_whole_color_scheme"
    | "color_whole_by_attribute"
    | "reset_whole_colors"
    | "reset_all_colors"
    | "get_whole_details"
    // Viewport / Export
    | "toggle_background"
    | "toggle_spin"
    | "toggle_swing"
    | "set_camera_mode"
    | "set_fog"
    | "set_figure_spec"
    | "download_image"
    | "export_html";

export interface PanelContext {
    /** Emit an action towards the controller (same channel as the legacy `onAction`). */
    onAction(action: PanelAction, details?: Record<string, unknown>): void;
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
