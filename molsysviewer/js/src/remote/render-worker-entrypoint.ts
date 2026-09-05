import { MolSysViewerController } from "../managers/viewer-controller";
import { ArrayNativeStreamReceiver } from "../messages/array-native-stream";
import type {
    StructureDataBeginMessage,
    StructureDataCancelMessage,
    StructureDataChunkMessage,
} from "../messages/array-native-transport";
import { DATA_PLANE_ACTIONS, RAW_ACTIONS, categoryOf } from "../messages/runtime-actions";
import { RemoteInputAdapter } from "../messages/remote-input-adapter";
import type { RuntimeEnvelope } from "../messages/runtime-router";
import type { RuntimeDirection } from "../messages/runtime-router";
import type { ViewerMessage } from "../messages/viewer-messages";
import { RenderWorkerPeer, type RemoteHumanIdentity } from "./render-worker-peer";

export interface RenderWorkerBootOptions {
    el: HTMLElement;
    websocketUrl: string;
    viewerId: string;
    sessionId: string;
    endpointId: string;
    width?: number;
    height?: number;
    frameRate?: number;
    maxBitrate?: number;
    iceServers?: RTCIceServer[];
}

export interface RenderWorkerRuntime {
    controller: MolSysViewerController;
    socket: WebSocket;
    peerDiagnostics(): Promise<Record<string, unknown>>;
    close(): void;
}

type DataHeader = {
    kind: "data";
    message: StructureDataBeginMessage | StructureDataChunkMessage | StructureDataCancelMessage;
    bufferCount: number;
    byteLengths: number[];
};

const INBOUND_DIRECTIONS = new Set<RuntimeDirection>(["projection", "request", "ack", "error"]);

function actionOf(message: Record<string, unknown>): string | null {
    if (typeof message.event === "string" && message.event) return message.event;
    if (typeof message.op === "string" && message.op) return message.op;
    return null;
}

function assertInboundEnvelope(
    value: unknown,
    options: RenderWorkerBootOptions,
): RuntimeEnvelope<Record<string, unknown>> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        throw new Error("render-worker control envelope is malformed");
    }
    const envelope = value as RuntimeEnvelope<Record<string, unknown>>;
    if (
        envelope.protocolVersion !== 1
        || envelope.viewerId !== options.viewerId
        || envelope.sessionId !== options.sessionId
        || envelope.endpointId !== `python:${options.viewerId}`
        || (envelope.targetEndpointId !== undefined && envelope.targetEndpointId !== options.endpointId)
        || !INBOUND_DIRECTIONS.has(envelope.direction)
        || !envelope.payload
        || typeof envelope.payload !== "object"
        || Array.isArray(envelope.payload)
        || actionOf(envelope.payload) !== envelope.action
    ) {
        throw new Error("render-worker control envelope identity or payload is invalid");
    }
    return envelope;
}

/** Boot the canvas-only runtime used by the managed server render worker. */
export async function bootRenderWorker(options: RenderWorkerBootOptions): Promise<RenderWorkerRuntime> {
    const { el } = options;
    el.replaceChildren();
    const target = document.createElement("div");
    target.tabIndex = 0;
    Object.assign(target.style, {
        width: options.width ? `${options.width}px` : "100%",
        height: options.height ? `${options.height}px` : "100%",
        position: "relative", overflow: "hidden", touchAction: "none",
    });
    el.appendChild(target);

    const socket = new WebSocket(options.websocketUrl, ["molsysviewer-internal-v1"]);
    socket.binaryType = "arraybuffer";
    let outboundSequence = 0;
    let registered = false;
    let closed = false;
    let dataHeader: DataHeader | null = null;
    let dataBuffers: DataView[] = [];
    let messageQueue = Promise.resolve();
    const pendingDomainMessages: Record<string, unknown>[] = [];
    let resolveRegistration!: () => void;
    let rejectRegistration!: (error: Error) => void;
    const registrationPromise = new Promise<void>((resolve, reject) => {
        resolveRegistration = resolve;
        rejectRegistration = reject;
    });
    // The controller can still be initializing when an early socket failure
    // rejects registration. Mark it handled immediately; awaiting the original
    // promise below still propagates the same failure deterministically.
    void registrationPromise.catch(() => undefined);

    const sendJson = (value: Record<string, unknown>) => {
        if (socket.readyState !== WebSocket.OPEN) throw new Error("render-worker socket is not open");
        socket.send(JSON.stringify(value));
    };
    const sendDomainNow = (message: Record<string, unknown>) => {
        const action = actionOf(message);
        if (!action) throw new Error("render-worker outbound message has no action");
        if (RAW_ACTIONS.has(action) || DATA_PLANE_ACTIONS.has(action)) {
            sendJson({ kind: "raw", message });
            return;
        }
        const direction = categoryOf(action);
        if (!direction) throw new Error(`render-worker emitted unknown action ${action}`);
        // A render worker is never the command actor. Once the session host has
        // bound its single authenticated human client, interaction commands use
        // that endpoint/actor identity; initialization noise before that point is
        // discarded instead of being mislabeled as a system command.
        const humanOrigin = direction === "command" || direction === "request";
        if (humanOrigin && !clientIdentity) return;
        const sourceEndpointId = humanOrigin ? clientIdentity!.endpointId : options.endpointId;
        const sourceActorId = humanOrigin ? clientIdentity!.actorId : options.endpointId;
        const envelope: RuntimeEnvelope<Record<string, unknown>> = {
            protocolVersion: 1,
            viewerId: options.viewerId,
            sessionId: options.sessionId,
            endpointId: sourceEndpointId,
            targetEndpointId: `python:${options.viewerId}`,
            messageId: `${sourceEndpointId}:${++outboundSequence}`,
            direction,
            action,
            payload: message,
            actorId: sourceActorId,
            actorKind: humanOrigin ? "human" : "system",
        };
        sendJson({ kind: "control", envelope: envelope as unknown as Record<string, unknown> });
    };
    const sendDomain = (message: Record<string, unknown>) => {
        if (!registered) {
            pendingDomainMessages.push(message);
            return;
        }
        sendDomainNow(message);
    };

    const controllerPromise = MolSysViewerController.create(
        target,
        message => sendDomain(message),
        undefined,
        { hasAuthority: true, hasInitialStructures: false },
    );
    const arrayReceiver = new ArrayNativeStreamReceiver(
        event => sendDomain(event),
        async (begin, payload) => {
            const controller = await controllerPromise;
            await controller.loadArrayNativeMolSysPayload(payload, begin.label);
        },
    );
    let inputAdapter: RemoteInputAdapter | null = null;
    let peer: RenderWorkerPeer | null = null;
    let clientIdentity: RemoteHumanIdentity | null = null;

    const handleData = async (header: DataHeader, buffers: DataView[]) => {
        await arrayReceiver.handle(header.message, buffers);
    };
    const handleJson = async (value: any) => {
        if (value?.kind === "registered") {
            await controllerPromise;
            const canvas = target.querySelector("canvas");
            if (!canvas) throw new Error("render-worker controller did not create a canvas");
            registered = true;
            for (const pending of pendingDomainMessages.splice(0)) sendDomainNow(pending);
            sendDomainNow({
                event: "ready",
                capabilities: {
                    binary_structure_data: [1],
                    max_buffer_bytes: 16 * 1024 * 1024,
                    transferable_array_buffer: true,
                    render_worker: true,
                },
            });
            resolveRegistration();
            return;
        }
        if (!registered) throw new Error("render-worker received traffic before registration");
        if (value?.kind === "peer-start") {
            if (
                typeof value.clientEndpointId !== "string"
                || !value.clientEndpointId
                || typeof value.actorId !== "string"
                || !value.actorId
            ) {
                throw new Error("render-worker peer identity is malformed");
            }
            const peerIceServers = Array.isArray(value.iceServers)
                ? value.iceServers as RTCIceServer[]
                : options.iceServers;
            const canvas = target.querySelector("canvas");
            if (!canvas) throw new Error("render-worker peer started before canvas creation");
            peer?.close();
            clientIdentity = {
                endpointId: value.clientEndpointId,
                actorId: value.actorId,
            };
            inputAdapter = new RemoteInputAdapter(canvas, {
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: clientIdentity.endpointId,
            });
            const controller = await controllerPromise;
            peer = new RenderWorkerPeer(
                canvas,
                {
                    viewerId: options.viewerId,
                    sessionId: options.sessionId,
                    workerEndpointId: options.endpointId,
                    frameRate: options.frameRate,
                    maxBitrate: options.maxBitrate,
                    iceServers: peerIceServers,
                },
                packet => sendJson({ kind: "signal", packet }),
                inputAdapter,
                sequence => sendJson({ kind: "peer-state", state: "input-received", sequence }),
                () => controller.plugin.canvas3d?.requestDraw(),
            );
            await peer.start(clientIdentity);
            controller.plugin.canvas3d?.requestDraw();
            window.setTimeout(() => controller.plugin.canvas3d?.requestDraw(), 100);
            return;
        }
        if (value?.kind === "peer-stop") {
            peer?.close();
            peer = null;
            inputAdapter = null;
            clientIdentity = null;
            return;
        }
        if (value?.kind === "signal") {
            if (!peer) throw new Error("render-worker received signaling before peer start");
            await peer.handleSignal(value.packet);
            return;
        }
        if (value?.kind === "control") {
            const envelope = assertInboundEnvelope(value.envelope, options);
            if (envelope.action === "request_image_export") {
                const request = envelope.payload as Record<string, unknown>;
                const controller = await controllerPromise;
                const result = await controller.getImageDataUri({
                    width: typeof request.width === "number" ? request.width : undefined,
                    height: typeof request.height === "number" ? request.height : undefined,
                    scale: typeof request.scale === "number" ? request.scale : undefined,
                    transparent: request.transparent === true,
                    preset: typeof request.preset === "string" ? request.preset : undefined,
                    cameraSnapshot: request.camera_snapshot && typeof request.camera_snapshot === "object"
                        ? request.camera_snapshot as any : undefined,
                });
                sendDomain({
                    event: "image_export",
                    request_id: request.request_id,
                    ...(typeof result === "string"
                        ? { data_uri: result, success: true }
                        : result as Record<string, unknown>),
                    format: "png",
                });
                return;
            }
            await (await controllerPromise).handleMessage(envelope.payload as ViewerMessage);
            return;
        }
        if (value?.kind === "data") {
            if (dataHeader !== null) throw new Error("nested render-worker data header");
            if (
                !Number.isInteger(value.bufferCount)
                || value.bufferCount < 0
                || !Array.isArray(value.byteLengths)
                || value.byteLengths.length !== value.bufferCount
                || value.byteLengths.some((length: unknown) => !Number.isInteger(length) || Number(length) < 0)
            ) {
                throw new Error("render-worker data header is malformed");
            }
            dataHeader = value as DataHeader;
            dataBuffers = [];
            if (dataHeader.bufferCount === 0) {
                const complete = dataHeader;
                dataHeader = null;
                await handleData(complete, []);
            }
            return;
        }
        if (value?.kind === "input") {
            if (!clientIdentity || !inputAdapter) {
                throw new Error("render-worker input arrived before client binding");
            }
            const result = inputAdapter.handle(value.packet);
            if (result.status === "rejected") throw new Error(`${result.reason}: ${result.detail}`);
            return;
        }
        throw new Error("render-worker received an unknown wire message");
    };

    socket.addEventListener("message", event => {
        messageQueue = messageQueue.then(async () => {
            if (typeof event.data === "string") {
                await handleJson(JSON.parse(event.data));
                return;
            }
            if (dataHeader === null || !(event.data instanceof ArrayBuffer)) {
                throw new Error("unexpected render-worker binary frame");
            }
            const index = dataBuffers.length;
            if (event.data.byteLength !== dataHeader.byteLengths[index]) {
                throw new Error("render-worker binary frame length mismatch");
            }
            dataBuffers.push(new DataView(event.data));
            if (dataBuffers.length === dataHeader.bufferCount) {
                const complete = dataHeader;
                const buffers = dataBuffers;
                dataHeader = null;
                dataBuffers = [];
                await handleData(complete, buffers);
            }
        }).catch(error => {
            console.error("[MolSysViewer render worker] wire failure", error);
            rejectRegistration(error instanceof Error ? error : new Error(String(error)));
            socket.close(1011, "worker wire failure");
        });
    });

    await new Promise<void>((resolve, reject) => {
        const timer = window.setTimeout(() => reject(new Error("render-worker WebSocket timed out")), 10_000);
        socket.addEventListener("open", () => {
            window.clearTimeout(timer);
            sendJson({
                kind: "register",
                protocolVersion: 1,
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: options.endpointId,
                role: "render-worker",
                actorId: options.endpointId,
                actorKind: "system",
                capabilities: ["input-receive", "render", "structure-receive", "video-send"],
            });
            resolve();
        }, { once: true });
        socket.addEventListener("error", () => {
            window.clearTimeout(timer);
            const error = new Error("render-worker WebSocket failed");
            rejectRegistration(error);
            reject(error);
        }, { once: true });
        socket.addEventListener("close", () => {
            rejectRegistration(new Error("render-worker WebSocket closed during registration"));
        }, { once: true });
    });
    const controller = await controllerPromise;
    let registrationTimer = 0;
    try {
        await Promise.race([
            registrationPromise,
            new Promise<never>((_resolve, reject) => {
                registrationTimer = window.setTimeout(
                    () => reject(new Error("render-worker registration timed out")),
                    10_000,
                );
            }),
        ]);
    } finally {
        window.clearTimeout(registrationTimer);
    }
    el.setAttribute("data-molsysviewer-render-worker", "booted");
    return {
        controller,
        socket,
        peerDiagnostics: () => peer?.diagnostics() ?? Promise.resolve({ peer: null }),
        close() {
            if (closed) return;
            closed = true;
            arrayReceiver.dispose();
            peer?.close();
            controller.dispose();
            socket.close(1000, "worker closed");
        },
    };
}
