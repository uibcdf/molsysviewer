import manifest from "../../../remote_protocol.json";

export const REMOTE_PROTOCOL_VERSION = 1 as const;

const raw = manifest as {
    protocol_version: number;
    signaling_kinds: string[];
    input_kinds: string[];
    pointer_phases: string[];
    pointer_types: string[];
    key_phases: string[];
    max_key_code_length: number;
    max_viewport_dimension: number;
    max_device_pixel_ratio: number;
};

if (raw.protocol_version !== REMOTE_PROTOCOL_VERSION) {
    throw new Error(`remote_protocol.json protocol_version must be ${REMOTE_PROTOCOL_VERSION}`);
}

export const SIGNALING_KINDS: ReadonlySet<string> = new Set(raw.signaling_kinds);
export const INPUT_KINDS: ReadonlySet<string> = new Set(raw.input_kinds);
export const POINTER_PHASES: ReadonlySet<string> = new Set(raw.pointer_phases);
export const POINTER_TYPES: ReadonlySet<string> = new Set(raw.pointer_types);
export const KEY_PHASES: ReadonlySet<string> = new Set(raw.key_phases);

export type RemotePacketValidation =
    | { status: "accepted"; packet: Record<string, unknown> }
    | { status: "rejected"; reason: string; detail: string };
type RemotePacketRejection = Extract<RemotePacketValidation, { status: "rejected" }>;

export interface ExpectedRemoteIdentity {
    viewerId?: string;
    sessionId?: string;
    endpointId?: string;
}

function accepted(packet: Record<string, unknown>): RemotePacketValidation {
    return { status: "accepted", packet };
}

function rejected(reason: string, detail: string): RemotePacketValidation {
    return { status: "rejected", reason, detail };
}

function nonEmpty(value: unknown): value is string {
    return typeof value === "string" && value.trim().length > 0;
}

function finiteNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

function common(
    value: unknown,
    expected: ExpectedRemoteIdentity,
): RemotePacketRejection | Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return rejected("malformed-packet", "Packet must be an object");
    }
    const packet = value as Record<string, unknown>;
    if (!Number.isInteger(packet.protocolVersion)) {
        return rejected("malformed-packet", "protocolVersion must be an integer");
    }
    if (packet.protocolVersion !== REMOTE_PROTOCOL_VERSION) {
        return rejected("protocol-mismatch", `Unsupported protocol ${packet.protocolVersion}`);
    }
    for (const key of ["viewerId", "sessionId", "endpointId", "kind"]) {
        if (!nonEmpty(packet[key])) {
            return rejected("malformed-packet", `${key} must be a non-empty string`);
        }
    }
    for (const key of ["viewerId", "sessionId", "endpointId"] as const) {
        if (expected[key] !== undefined && packet[key] !== expected[key]) {
            return rejected(
                "identity-mismatch",
                `${key} belongs to ${String(packet[key])}, expected ${expected[key]}`,
            );
        }
    }
    if (!packet.payload || typeof packet.payload !== "object" || Array.isArray(packet.payload)) {
        return rejected("malformed-payload", "payload must be an object");
    }
    return packet;
}

function isRejection(
    value: RemotePacketRejection | Record<string, unknown>,
): value is RemotePacketRejection {
    return value.status === "rejected";
}

export function validateSignalingPacket(
    value: unknown,
    expected: ExpectedRemoteIdentity = {},
): RemotePacketValidation {
    const checked = common(value, expected);
    if (isRejection(checked)) return checked;
    if (!nonEmpty(checked.messageId)) {
        return rejected("malformed-packet", "messageId must be a non-empty string");
    }
    const kind = checked.kind as string;
    const payload = checked.payload as Record<string, unknown>;
    if (!SIGNALING_KINDS.has(kind)) return rejected("unknown-kind", `Unknown signaling kind ${kind}`);
    if ((kind === "offer" || kind === "answer") && !nonEmpty(payload.sdp)) {
        return rejected("malformed-payload", `${kind} requires non-empty sdp`);
    }
    if (kind === "ice-candidate") {
        if (!nonEmpty(payload.candidate)) {
            return rejected("malformed-payload", "ice-candidate requires candidate");
        }
        if (payload.sdpMid !== null && payload.sdpMid !== undefined && !nonEmpty(payload.sdpMid)) {
            return rejected("malformed-payload", "sdpMid must be null or non-empty");
        }
        if (
            payload.sdpMLineIndex !== null
            && payload.sdpMLineIndex !== undefined
            && (!Number.isInteger(payload.sdpMLineIndex) || (payload.sdpMLineIndex as number) < 0)
        ) {
            return rejected("malformed-payload", "sdpMLineIndex must be null or non-negative");
        }
    }
    return accepted(checked);
}

export function validateInputPacket(
    value: unknown,
    expected: ExpectedRemoteIdentity = {},
): RemotePacketValidation {
    const checked = common(value, expected);
    if (isRejection(checked)) return checked;
    if (
        !Number.isSafeInteger(checked.sequence)
        || (checked.sequence as number) < 0
    ) {
        return rejected("malformed-packet", "sequence must be a non-negative safe integer");
    }
    if (!finiteNumber(checked.timestampMs) || checked.timestampMs < 0) {
        return rejected("malformed-packet", "timestampMs must be finite and non-negative");
    }
    if (!checked.viewport || typeof checked.viewport !== "object" || Array.isArray(checked.viewport)) {
        return rejected("malformed-packet", "viewport must be an object");
    }
    const viewport = checked.viewport as Record<string, unknown>;
    for (const dimension of ["width", "height"]) {
        const item = viewport[dimension];
        if (!finiteNumber(item) || item <= 0 || item > raw.max_viewport_dimension) {
            return rejected("malformed-packet", `viewport.${dimension} is out of bounds`);
        }
    }
    const dpr = viewport.devicePixelRatio;
    if (!finiteNumber(dpr) || dpr <= 0 || dpr > raw.max_device_pixel_ratio) {
        return rejected("malformed-packet", "viewport.devicePixelRatio is out of bounds");
    }
    const kind = checked.kind as string;
    const payload = checked.payload as Record<string, unknown>;
    if (!INPUT_KINDS.has(kind)) return rejected("unknown-kind", `Unknown input kind ${kind}`);
    const failure = validateInputPayload(kind, payload);
    return failure ?? accepted(checked);
}

function validateInputPayload(
    kind: string,
    payload: Record<string, unknown>,
): RemotePacketValidation | null {
    const modifiers = payload.modifiers ?? {};
    if (!modifiers || typeof modifiers !== "object" || Array.isArray(modifiers)) {
        return rejected("malformed-payload", "modifiers must be an object");
    }
    for (const [key, value] of Object.entries(modifiers)) {
        if (!["alt", "ctrl", "meta", "shift"].includes(key) || typeof value !== "boolean") {
            return rejected("malformed-payload", "modifiers must contain only boolean modifier keys");
        }
    }
    if (kind === "pointer" || kind === "wheel" || kind === "context-menu") {
        for (const coordinate of ["x", "y"]) {
            const item = payload[coordinate];
            if (!finiteNumber(item) || item < 0 || item > 1) {
                return rejected("malformed-payload", `${coordinate} must be normalized to [0, 1]`);
            }
        }
    }
    if (kind === "pointer") {
        if (!POINTER_PHASES.has(String(payload.phase))) {
            return rejected("malformed-payload", "pointer phase is invalid");
        }
        if (!POINTER_TYPES.has(String(payload.pointerType))) {
            return rejected("malformed-payload", "pointerType is invalid");
        }
        if (!Number.isInteger(payload.pointerId) || (payload.pointerId as number) < 0) {
            return rejected("malformed-payload", "pointerId must be non-negative");
        }
        if (!Number.isInteger(payload.button) || (payload.button as number) < -1 || (payload.button as number) > 5) {
            return rejected("malformed-payload", "button is out of bounds");
        }
        if (!Number.isInteger(payload.buttons) || (payload.buttons as number) < 0) {
            return rejected("malformed-payload", "buttons must be non-negative");
        }
    } else if (kind === "wheel") {
        for (const delta of ["deltaX", "deltaY"]) {
            if (!finiteNumber(payload[delta])) {
                return rejected("malformed-payload", `${delta} must be finite`);
            }
        }
        if (![0, 1, 2].includes(payload.deltaMode as number)) {
            return rejected("malformed-payload", "deltaMode must be 0, 1 or 2");
        }
    } else if (kind === "key") {
        if (!KEY_PHASES.has(String(payload.phase))) {
            return rejected("malformed-payload", "key phase is invalid");
        }
        if (!nonEmpty(payload.code) || payload.code.length > raw.max_key_code_length) {
            return rejected("malformed-payload", "key code is invalid");
        }
        if (typeof payload.repeat !== "boolean") {
            return rejected("malformed-payload", "key repeat must be boolean");
        }
    } else {
        if (!nonEmpty(payload.requestId) || payload.requestId.length > 128) {
            return rejected("malformed-payload", "context-menu requestId is invalid");
        }
    }
    return null;
}
