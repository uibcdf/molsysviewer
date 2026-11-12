/** The authenticated connector supplies the editor owner and its source canvas. */
export function ownMovieIntent<T extends Record<string, any>>(message: T, owner: string, canvas: string): T {
    return message?.event === "interaction_context_action" && typeof message.action === "string"
        && message.action.startsWith("movie_")
        ? { ...message, _studio_owner_endpoint_id: owner, _capture_endpoint_id: canvas } : message;
}
