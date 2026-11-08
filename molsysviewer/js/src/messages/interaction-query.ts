/** The authenticated host, rather than a domain payload, owns query routing. */
export function ownInteractionQuery<T extends Record<string, unknown>>(message: T, endpoint: string): T {
    return message.event === "request_interaction_frame"
        ? { ...message, _query_endpoint_id: endpoint } : message;
}
