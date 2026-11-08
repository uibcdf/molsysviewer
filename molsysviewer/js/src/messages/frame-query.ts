/** The authenticated host, rather than a domain payload, owns query routing. */
export function ownFrameQuery<T extends Record<string, unknown>>(message: T, endpoint: string): T {
    return message.event === "request_interaction_frame" || message.event === "request_dynamic_region_evaluation"
        ? { ...message, _query_endpoint_id: endpoint } : message;
}

/** A delayed frame reply can finish its own query without touching a newer frame. */
export function dynamicRegionReplyAction(reply: { frame?: number; request_id?: number }, currentFrame: number,
    pendingFrame: number | null, pendingRequest: number | null): "ignore" | "project" | "complete" | "apply" {
    if (typeof reply.frame !== "number" || !Number.isSafeInteger(reply.frame) || reply.frame < 0) return "ignore";
    if (reply.request_id === undefined) return reply.frame === currentFrame ? "project" : "ignore";
    if (reply.frame !== pendingFrame || reply.request_id !== pendingRequest) return "ignore";
    return reply.frame === currentFrame ? "apply" : "complete";
}
