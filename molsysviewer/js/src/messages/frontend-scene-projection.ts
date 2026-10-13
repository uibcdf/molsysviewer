import type { ViewerMessage } from "./viewer-messages";

/** Context actions already performed by the local browser controller. */
export const FRONTEND_CONTEXT_ACTIONS = new Set([
    "reset_view", "focus_target", "focus_region", "focus_selection",
    "toggle_background", "toggle_spin", "toggle_swing",
]);

/** Equivalent portable projection for an exported scene with no Python owner. */
export function frontendSceneProjection(event: any): ViewerMessage | null {
    if (event?.event === "interaction_active_selection_changed") return {
        op: "set_active_selection", atom_indices: [...event.atom_indices],
        items: event.items?.map((item: any) => ({ ...item })),
    };
    if (event?.event === "section_moved") return {
        op: "sync_section_position", tag: event.tag, point: event.point, normal: event.normal,
    };
    if (event?.event !== "interaction_context_action") return null;
    if (event.action === "toggle_background") return { op: event.action, mode: event.mode };
    if (event.action === "toggle_spin" || event.action === "toggle_swing") return { op: event.action, enable: event.enabled };
    // Focus/reset are relayed as resolved camera snapshots, never a second
    // fit-to-window operation with another viewport's aspect ratio.
    return null;
}
