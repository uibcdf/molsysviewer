import type { ViewerMessage } from "./viewer-messages";

/** Translate canvas trajectory feedback into one Python authority command. */
export function trajectorySyncToAuthority(msg: ViewerMessage): Record<string, unknown> | null {
    if (msg.op === "set_trajectory_frame") {
        return { event: "interaction_context_action", action: msg.op, index: msg.index };
    }
    if (msg.op === "step_trajectory") {
        return { event: "interaction_context_action", action: msg.op, by: msg.by };
    }
    if (msg.op === "set_trajectory_playback") {
        return {
            event: "interaction_context_action",
            action: msg.op,
            playback_action: msg.action,
            ...(msg.fps === undefined ? {} : { fps: msg.fps }),
            ...(msg.step === undefined ? {} : { step: msg.step }),
        };
    }
    return null;
}
