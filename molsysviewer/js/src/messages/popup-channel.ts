import type { RuntimeEnvelope } from "./runtime-router";

export const POPUP_CHANNEL_PROTOCOL_VERSION = 1 as const;

export type PopupMode = "canvas" | "panel";

export type PopupChannelIdentity = {
    protocolVersion: typeof POPUP_CHANNEL_PROTOCOL_VERSION;
    viewerId: string;
    sessionId: string;
    authorityEndpointId: string;
    hostEndpointId: string;
    popupEndpointId: string;
    token: string;
    mode: PopupMode;
};

export type PopupWireMessage = {
    channel: PopupChannelIdentity;
    envelope: RuntimeEnvelope;
};

function nonEmptyString(value: unknown): value is string {
    return typeof value === "string" && value.trim().length > 0;
}

export function createSecureRuntimeId(prefix: string): string {
    const cryptography = globalThis.crypto;
    const uuid = cryptography?.randomUUID?.();
    if (uuid) return `${prefix}-${uuid}`;
    if (!cryptography?.getRandomValues) {
        throw new Error("Secure popup channel identity requires Web Crypto");
    }
    const words = cryptography.getRandomValues(new Uint32Array(4));
    return `${prefix}-${[...words].map(word => word.toString(16).padStart(8, "0")).join("")}`;
}

export function createPopupChannelIdentity(
    viewerId: string,
    sessionId: string,
    mode: PopupMode,
    authorityEndpointId = "python",
    hostEndpointId = "host",
): PopupChannelIdentity {
    if (
        !nonEmptyString(viewerId)
        || !nonEmptyString(sessionId)
        || !nonEmptyString(authorityEndpointId)
        || !nonEmptyString(hostEndpointId)
    ) {
        throw new Error("Popup channel requires viewer, session, authority, and host identity");
    }
    return {
        protocolVersion: POPUP_CHANNEL_PROTOCOL_VERSION,
        viewerId,
        sessionId,
        authorityEndpointId,
        hostEndpointId,
        popupEndpointId: createSecureRuntimeId(mode === "canvas" ? "canvas-popup" : "panel-popup"),
        token: createSecureRuntimeId("token"),
        mode,
    };
}

export function isPopupChannelIdentity(value: unknown): value is PopupChannelIdentity {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const channel = value as Partial<PopupChannelIdentity>;
    return (
        channel.protocolVersion === POPUP_CHANNEL_PROTOCOL_VERSION
        && nonEmptyString(channel.viewerId)
        && nonEmptyString(channel.sessionId)
        && nonEmptyString(channel.authorityEndpointId)
        && nonEmptyString(channel.hostEndpointId)
        && nonEmptyString(channel.popupEndpointId)
        && nonEmptyString(channel.token)
        && (channel.mode === "canvas" || channel.mode === "panel")
    );
}

export function samePopupChannel(
    actual: unknown,
    expected: PopupChannelIdentity,
): actual is PopupChannelIdentity {
    if (!isPopupChannelIdentity(actual)) return false;
    return (
        actual.viewerId === expected.viewerId
        && actual.sessionId === expected.sessionId
        && actual.authorityEndpointId === expected.authorityEndpointId
        && actual.hostEndpointId === expected.hostEndpointId
        && actual.popupEndpointId === expected.popupEndpointId
        && actual.token === expected.token
        && actual.mode === expected.mode
    );
}

export function encodePopupMessage(
    channel: PopupChannelIdentity,
    envelope: RuntimeEnvelope,
): PopupWireMessage {
    return { channel, envelope };
}

export function decodePopupMessage(
    value: unknown,
    expected: PopupChannelIdentity,
): PopupWireMessage | null {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const message = value as Partial<PopupWireMessage>;
    if (!samePopupChannel(message.channel, expected)) return null;
    if (!message.envelope || typeof message.envelope !== "object") return null;
    return message as PopupWireMessage;
}

export function decodePopupEvent(
    event: Pick<MessageEvent, "source" | "data">,
    expectedSource: MessageEventSource,
    expectedChannel: PopupChannelIdentity,
    expectedEndpointIds?: ReadonlySet<string>,
): PopupWireMessage | null {
    if (event.source !== expectedSource) return null;
    const message = decodePopupMessage(event.data, expectedChannel);
    if (
        !message
        || (
            expectedEndpointIds
            && !expectedEndpointIds.has(message.envelope.endpointId)
        )
    ) {
        return null;
    }
    return message;
}
