// R1 AnyWidget seam adapter: wrap browser->Python messages into RuntimeEnvelopes
// and unwrap/validate Python->browser projections. The widget host is a single
// endpoint on a 1:1 pipe to Python (the authority), so this is a thin adapter,
// NOT a second router — the popup topology keeps the browser-side router.

import type { RuntimeEnvelope } from "./runtime-router";
import {
    DATA_PLANE_ACTIONS,
    RAW_ACTIONS,
    OUTBOUND_REQUESTS,
    categoryOf,
} from "./runtime-actions";

const RUNTIME_PROTOCOL_VERSION = 1 as const;

// Directions Python may legitimately originate toward the browser.
const INBOUND_DIRECTIONS: ReadonlySet<string> = new Set(["projection", "request", "ack", "error"]);

export type UnwrapResult =
    | { kind: "raw" }                       // not an envelope: bootstrap/data-plane, use existing path
    // `envelope` is carried so the seam can correlate a response to its request;
    // domain handlers still receive only `message`.
    | { kind: "message"; message: Record<string, unknown>; envelope: RuntimeEnvelope }
    | { kind: "rejected"; reason: string; detail: string };

export type WrapResult =
    | { kind: "send"; message: Record<string, unknown> }
    | { kind: "rejected"; reason: string; detail: string };

function nonEmpty(value: unknown): value is string {
    return typeof value === "string" && value.trim() !== "";
}

// browser -> Python messages key their action on `event`; any `op` is a nested
// domain field (e.g. {event: "interaction_context_action", op: "add_region"}).
function outboundActionOf(message: Record<string, unknown>): string | null {
    return nonEmpty(message.event) ? message.event : null;
}

// Python -> browser payloads key on `op` (projection ops / request ops), or
// `event` for the few event-shaped responses.
function payloadActionOf(message: Record<string, unknown>): string | null {
    if (nonEmpty(message.op)) return message.op;
    if (nonEmpty(message.event)) return message.event;
    return null;
}

function looksLikeEnvelope(value: unknown): value is Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const v = value as Record<string, unknown>;
    return (
        typeof v.protocolVersion === "number"
        && typeof v.direction === "string"
        && typeof v.action === "string"
        && "payload" in v
    );
}

export class WidgetEnvelopeAdapter {
    readonly pythonEndpoint: string;
    readonly widgetHostEndpoint: string;
    private sequence = 0;

    constructor(
        private readonly viewerId: string,
        private readonly sessionId: string,
        private readonly identity?: {
            endpointId: string;
            actorId?: string;
            actorKind?: "human" | "agent" | "system";
        },
    ) {
        this.pythonEndpoint = `python:${viewerId}`;
        this.widgetHostEndpoint = identity?.endpointId || `widget-host:${sessionId}`;
    }

    /** browser -> Python. `send` carries the wire message (raw for raw/data-plane
     * actions, an envelope otherwise); `rejected` must NOT reach `model.send`. */
    wrapOutbound(message: Record<string, unknown>): WrapResult {
        const action = outboundActionOf(message);
        if (action === null) {
            return { kind: "rejected", reason: "no-action", detail: "outbound message has no event action" };
        }
        if (RAW_ACTIONS.has(action) || DATA_PLANE_ACTIONS.has(action)) {
            return { kind: "send", message };
        }
        if (OUTBOUND_REQUESTS.has(action)) {
            // Python-originated only; the browser must never originate these.
            return { kind: "rejected", reason: "outbound-only", detail: action };
        }
        const category = categoryOf(action);
        if (category === undefined) {
            // The manifest is complete; an unknown action is a contract defect.
            return { kind: "rejected", reason: "unknown-action", detail: action };
        }
        const envelope: RuntimeEnvelope = {
            protocolVersion: RUNTIME_PROTOCOL_VERSION,
            viewerId: this.viewerId,
            sessionId: this.sessionId,
            endpointId: this.widgetHostEndpoint,
            targetEndpointId: this.pythonEndpoint,
            messageId: `wh-${this.sessionId}-${++this.sequence}`,
            direction: category,
            action,
            payload: message,
            ...(this.identity?.actorId ? { actorId: this.identity.actorId } : {}),
            ...(this.identity?.actorKind ? { actorKind: this.identity.actorKind } : {}),
        };
        return { kind: "send", message: envelope as unknown as Record<string, unknown> };
    }

    /** Python -> browser. `raw` means "not an envelope, use the existing dispatch",
     * and is allowed ONLY for bootstrap/source and data-plane actions. */
    unwrapInbound(value: unknown): UnwrapResult {
        if (!looksLikeEnvelope(value)) {
            const action =
                value && typeof value === "object" && !Array.isArray(value)
                    ? payloadActionOf(value as Record<string, unknown>)
                    : null;
            if (action !== null && (RAW_ACTIONS.has(action) || DATA_PLANE_ACTIONS.has(action))) {
                return { kind: "raw" };
            }
            return { kind: "rejected", reason: "unenveloped-control-message", detail: action ?? "(no action)" };
        }
        const env = value as unknown as RuntimeEnvelope;
        if (env.protocolVersion !== RUNTIME_PROTOCOL_VERSION) {
            return { kind: "rejected", reason: "protocol-mismatch", detail: String(env.protocolVersion) };
        }
        if (env.viewerId !== this.viewerId) {
            return { kind: "rejected", reason: "viewer-mismatch", detail: env.viewerId };
        }
        if (env.sessionId !== this.sessionId) {
            return { kind: "rejected", reason: "session-mismatch", detail: env.sessionId };
        }
        if (env.endpointId !== this.pythonEndpoint) {
            return { kind: "rejected", reason: "unknown-source", detail: env.endpointId };
        }
        if (env.targetEndpointId !== undefined && env.targetEndpointId !== this.widgetHostEndpoint) {
            return { kind: "rejected", reason: "unknown-target", detail: String(env.targetEndpointId) };
        }
        if (!INBOUND_DIRECTIONS.has(env.direction)) {
            return { kind: "rejected", reason: "direction-not-allowed", detail: env.direction };
        }
        if (!env.payload || typeof env.payload !== "object" || Array.isArray(env.payload)) {
            return { kind: "rejected", reason: "malformed-payload", detail: env.action };
        }
        const payload = env.payload as Record<string, unknown>;
        if (payloadActionOf(payload) !== env.action) {
            return { kind: "rejected", reason: "action-payload-mismatch", detail: env.action };
        }
        return { kind: "message", message: payload, envelope: env };
    }
}
