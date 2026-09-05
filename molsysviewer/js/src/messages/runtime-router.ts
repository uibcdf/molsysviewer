import { ENDPOINT_ROLE_CAPABILITIES } from "./runtime-actions";

export const RUNTIME_PROTOCOL_VERSION = 1 as const;

export type RuntimeDirection =
    | "command"
    | "projection"
    | "event"
    | "request"
    | "ack"
    | "error";

export type RuntimeEndpointRole =
    | "python"
    | "widget-host"
    | "qt-host"
    | "canvas"
    | "panel-popup"
    | "canvas-popup"
    | "browser-client"
    | "qt-client"
    | "render-worker"
    | "agent";

export type RuntimeActorKind = "human" | "agent" | "system";

export interface RuntimeEnvelope<T = unknown> {
    protocolVersion: typeof RUNTIME_PROTOCOL_VERSION;
    viewerId: string;
    sessionId: string;
    endpointId: string;
    targetEndpointId?: string;
    messageId: string;
    correlationId?: string;
    generation?: number;
    actorId?: string;
    actorKind?: RuntimeActorKind;
    causationId?: string;
    operationId?: string;
    deadlineUnixMs?: number;
    direction: RuntimeDirection;
    action: string;
    payload: T;
}

export interface RuntimeEndpoint {
    endpointId: string;
    role: RuntimeEndpointRole;
}

export type RuntimeRouteResult =
    | {
        status: "accepted";
        envelope: RuntimeEnvelope;
        recipientEndpointIds: string[];
    }
    | {
        status: "duplicate";
        envelope: RuntimeEnvelope;
        recipientEndpointIds: [];
    }
    | {
        status: "rejected";
        reason: RuntimeRouteRejection;
        detail: string;
    };

export type RuntimeRouteRejection =
    | "malformed-envelope"
    | "protocol-mismatch"
    | "viewer-mismatch"
    | "session-mismatch"
    | "unknown-source"
    | "unknown-target"
    | "direction-not-allowed"
    | "target-required"
    | "no-recipient";

const DIRECTIONS = new Set<RuntimeDirection>([
    "command",
    "projection",
    "event",
    "request",
    "ack",
    "error",
]);

const ROLES = new Set<RuntimeEndpointRole>(
    [...ENDPOINT_ROLE_CAPABILITIES.keys()] as RuntimeEndpointRole[],
);

const ACTOR_KINDS = new Set<RuntimeActorKind>(["human", "agent", "system"]);

const PROJECTION_RECIPIENT_ROLES = new Set<RuntimeEndpointRole>([
    "widget-host",
    "qt-host",
    "canvas",
    "panel-popup",
    "canvas-popup",
    "browser-client",
    "qt-client",
    "render-worker",
]);

function isNonEmptyString(value: unknown): value is string {
    return typeof value === "string" && value.trim().length > 0;
}

function isRuntimeDirection(value: unknown): value is RuntimeDirection {
    return typeof value === "string" && DIRECTIONS.has(value as RuntimeDirection);
}

function isRuntimeEndpointRole(value: unknown): value is RuntimeEndpointRole {
    return typeof value === "string" && ROLES.has(value as RuntimeEndpointRole);
}

function validateEnvelopeShape(value: unknown): RuntimeEnvelope | null {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const candidate = value as Partial<RuntimeEnvelope>;
    if (
        !Number.isInteger(candidate.protocolVersion)
        || !isNonEmptyString(candidate.viewerId)
        || !isNonEmptyString(candidate.sessionId)
        || !isNonEmptyString(candidate.endpointId)
        || !isNonEmptyString(candidate.messageId)
        || !isRuntimeDirection(candidate.direction)
        || !isNonEmptyString(candidate.action)
    ) {
        return null;
    }
    if (candidate.targetEndpointId !== undefined && !isNonEmptyString(candidate.targetEndpointId)) {
        return null;
    }
    if (candidate.correlationId !== undefined && !isNonEmptyString(candidate.correlationId)) {
        return null;
    }
    if ((candidate.actorId === undefined) !== (candidate.actorKind === undefined)) {
        return null;
    }
    if (candidate.actorId !== undefined && !isNonEmptyString(candidate.actorId)) {
        return null;
    }
    if (candidate.actorKind !== undefined && !ACTOR_KINDS.has(candidate.actorKind)) {
        return null;
    }
    if (candidate.causationId !== undefined && !isNonEmptyString(candidate.causationId)) {
        return null;
    }
    if (candidate.operationId !== undefined && !isNonEmptyString(candidate.operationId)) {
        return null;
    }
    if (
        candidate.deadlineUnixMs !== undefined
        && (!Number.isInteger(candidate.deadlineUnixMs) || candidate.deadlineUnixMs < 0)
    ) {
        return null;
    }
    if (
        candidate.generation !== undefined
        && (!Number.isInteger(candidate.generation) || candidate.generation < 0)
    ) {
        return null;
    }
    return candidate as RuntimeEnvelope;
}

function directionAllowed(role: RuntimeEndpointRole, direction: RuntimeDirection): boolean {
    if (direction === "projection") return role === "python";
    if (direction === "command" || direction === "request") return role !== "python";
    return true;
}

export class RuntimeMessageRouter {
    private readonly endpoints = new Map<string, RuntimeEndpointRole>();
    private readonly processedCommandIds = new Map<string, true>();

    constructor(
        readonly viewerId: string,
        readonly sessionId: string,
        private readonly maxProcessedCommands = 1024,
    ) {
        if (!isNonEmptyString(viewerId)) throw new ValueError("viewerId must be non-empty");
        if (!isNonEmptyString(sessionId)) throw new ValueError("sessionId must be non-empty");
        if (!Number.isInteger(maxProcessedCommands) || maxProcessedCommands < 1) {
            throw new ValueError("maxProcessedCommands must be a positive integer");
        }
    }

    registerEndpoint(endpoint: RuntimeEndpoint): void {
        if (
            !endpoint
            || !isNonEmptyString(endpoint.endpointId)
            || !isRuntimeEndpointRole(endpoint.role)
        ) {
            throw new ValueError("Invalid runtime endpoint");
        }
        if (this.endpoints.has(endpoint.endpointId)) {
            throw new ValueError(`Runtime endpoint already registered: ${endpoint.endpointId}`);
        }
        this.endpoints.set(endpoint.endpointId, endpoint.role);
    }

    unregisterEndpoint(endpointId: string): boolean {
        return this.endpoints.delete(endpointId);
    }

    hasEndpoint(endpointId: string): boolean {
        return this.endpoints.has(endpointId);
    }

    route(value: unknown): RuntimeRouteResult {
        const envelope = validateEnvelopeShape(value);
        if (!envelope) {
            return {
                status: "rejected",
                reason: "malformed-envelope",
                detail: "Runtime envelope is malformed",
            };
        }
        if (envelope.protocolVersion !== RUNTIME_PROTOCOL_VERSION) {
            return {
                status: "rejected",
                reason: "protocol-mismatch",
                detail: `Unsupported runtime protocol: ${envelope.protocolVersion}`,
            };
        }
        if (envelope.viewerId !== this.viewerId) {
            return {
                status: "rejected",
                reason: "viewer-mismatch",
                detail: `Envelope belongs to viewer ${envelope.viewerId}`,
            };
        }
        if (envelope.sessionId !== this.sessionId) {
            return {
                status: "rejected",
                reason: "session-mismatch",
                detail: `Envelope belongs to session ${envelope.sessionId}`,
            };
        }

        const sourceRole = this.endpoints.get(envelope.endpointId);
        if (!sourceRole) {
            return {
                status: "rejected",
                reason: "unknown-source",
                detail: `Unknown runtime endpoint: ${envelope.endpointId}`,
            };
        }
        if (!directionAllowed(sourceRole, envelope.direction)) {
            return {
                status: "rejected",
                reason: "direction-not-allowed",
                detail: `${sourceRole} cannot originate ${envelope.direction}`,
            };
        }

        if (envelope.direction === "command" && this.processedCommandIds.has(envelope.messageId)) {
            return {
                status: "duplicate",
                envelope,
                recipientEndpointIds: [],
            };
        }

        const recipients = this.resolveRecipients(envelope);
        if ("reason" in recipients) return recipients;

        if (envelope.direction === "command") {
            this.processedCommandIds.set(envelope.messageId, true);
            while (this.processedCommandIds.size > this.maxProcessedCommands) {
                const oldest = this.processedCommandIds.keys().next().value;
                if (oldest === undefined) break;
                this.processedCommandIds.delete(oldest);
            }
        }

        return {
            status: "accepted",
            envelope,
            recipientEndpointIds: recipients,
        };
    }

    private resolveRecipients(
        envelope: RuntimeEnvelope,
    ): string[] | Extract<RuntimeRouteResult, { status: "rejected" }> {
        if (envelope.targetEndpointId !== undefined) {
            if (!this.endpoints.has(envelope.targetEndpointId)) {
                return {
                    status: "rejected",
                    reason: "unknown-target",
                    detail: `Unknown target endpoint: ${envelope.targetEndpointId}`,
                };
            }
            return [envelope.targetEndpointId];
        }

        if (envelope.direction === "ack" || envelope.direction === "error") {
            return {
                status: "rejected",
                reason: "target-required",
                detail: `${envelope.direction} requires targetEndpointId`,
            };
        }

        let recipients: string[];
        if (
            envelope.direction === "command"
            || envelope.direction === "request"
            || envelope.direction === "event"
        ) {
            recipients = this.endpointIdsForRoles(new Set<RuntimeEndpointRole>(["python"]));
        } else {
            recipients = this.endpointIdsForRoles(PROJECTION_RECIPIENT_ROLES)
                .filter(endpointId => endpointId !== envelope.endpointId);
        }

        if (recipients.length === 0) {
            return {
                status: "rejected",
                reason: "no-recipient",
                detail: `No recipient is registered for ${envelope.direction}`,
            };
        }
        return recipients;
    }

    private endpointIdsForRoles(roles: ReadonlySet<RuntimeEndpointRole>): string[] {
        return [...this.endpoints.entries()]
            .filter(([, role]) => roles.has(role))
            .map(([endpointId]) => endpointId);
    }
}

class ValueError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "ValueError";
    }
}
