import type { ViewerMessage } from "./viewer-messages";

const STRUCTURE_LOAD_OPS = new Set([
    "load_molsys_payload",
    "load_molsys_payload_ref",
    "load_molsys_array_payload_ref",
    "load_structure_from_string",
    "load_pdb_string",
    "load_structure_from_url",
    "load_pdb_id",
]);

const PANEL_PROJECTION_OPS = new Set([
    "set_region_summaries",
    "set_layer_summaries",
    "set_annotation_summaries",
    "set_measurement_summaries",
    "set_shape_summaries",
    "set_section_summaries",
    "set_whole_summary",
    "set_history_state",
    "set_active_selection",
    "clear_active_selection",
    "region_details",
    "whole_details",
    "measurement_series",
    "dynamic_region_evaluation_warning",
    "selection_query_preview",
    "set_addon_runtime_summary",
    "set_addon_context_items",
    "mount_addon_panel",
    "addon_panel_message",
    "backend_error_occurred",
    "set_panel_mode",
    "set_workspace",
    "set_workspace_panel",
]);

const LAST_WRITE_WINS_OPS = new Set([
    "set_trajectory_frame",
    "set_trajectory_playback",
    "set_region_summaries",
    "set_layer_summaries",
    "set_annotation_summaries",
    "set_measurement_summaries",
    "set_shape_summaries",
    "set_section_summaries",
    "set_whole_summary",
    "set_history_state",
    "set_active_selection",
    "set_panel_mode",
    "set_canvas_visibility",
    "set_legend",
    "set_trajectory_plot",
    "update_visibility",
]);

function operation(message: ViewerMessage): string {
    return typeof (message as { op?: unknown }).op === "string"
        ? String((message as { op: string }).op)
        : "";
}

export class PopupReplayLog {
    private entries: ViewerMessage[] = [];

    constructor(initialMessages: readonly ViewerMessage[] = []) {
        for (const message of initialMessages) this.record(message);
    }

    record(message: ViewerMessage): void {
        if (!message || typeof message !== "object") return;
        const op = operation(message);
        if (!op) return;

        if (op === "clear_all") {
            this.entries = [];
            return;
        }
        if (STRUCTURE_LOAD_OPS.has(op)) {
            this.entries = [message];
            return;
        }
        if (LAST_WRITE_WINS_OPS.has(op)) {
            const index = this.entries.findIndex(entry => operation(entry) === op);
            if (index >= 0) {
                this.entries[index] = message;
                return;
            }
        }
        this.entries.push(message);
    }

    snapshot(mode: "canvas" | "panel"): ViewerMessage[] {
        const source =
            mode === "panel"
                ? this.entries.filter(message => PANEL_PROJECTION_OPS.has(operation(message)))
                : this.entries;
        return [...source];
    }

    get size(): number {
        return this.entries.length;
    }
}
