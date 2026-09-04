import { validateSignalingPacket } from "../messages/remote-protocol";
import {
    RemoteWorkbench,
    type RemoteDownloadArtifact,
    type RemoteWorkbenchAction,
} from "./remote-workbench";
import type { RemoteUploadResult } from "../ui/remote-file-controls";

export interface RemoteBrowserClientOptions {
    el: HTMLElement;
    websocketUrl: string;
    viewerId: string;
    sessionId: string;
    endpointId: string;
    actorId: string;
    workerEndpointId: string;
    iceServers?: RTCIceServer[];
}

export interface RemoteBrowserClientRuntime {
    video: HTMLVideoElement;
    workbench: RemoteWorkbench;
    socket: WebSocket;
    peerConnection(): RTCPeerConnection | null;
    close(): void;
}

type Point = { x: number; y: number };

function modifiers(event: MouseEvent | KeyboardEvent) {
    return {
        alt: event.altKey,
        ctrl: event.ctrlKey,
        meta: event.metaKey,
        shift: event.shiftKey,
    };
}

/** Boot a Mol*-free remote viewport backed by the server render worker. */
export async function bootRemoteBrowserClient(
    options: RemoteBrowserClientOptions,
): Promise<RemoteBrowserClientRuntime> {
    const { el } = options;
    el.replaceChildren();
    Object.assign(el.style, { position: "relative", overflow: "hidden", background: "#080b10" });

    const video = document.createElement("video");
    video.autoplay = true;
    video.playsInline = true;
    video.muted = true;
    Object.assign(video.style, {
        position: "absolute", inset: "0", width: "100%", height: "100%", objectFit: "contain",
    });
    const inputSurface = document.createElement("div");
    inputSurface.tabIndex = 0;
    inputSurface.setAttribute("aria-label", "Remote molecular viewport");
    Object.assign(inputSurface.style, {
        position: "absolute", inset: "0", outline: "none", touchAction: "none", cursor: "default",
    });
    const status = document.createElement("div");
    status.setAttribute("data-molsysviewer-remote-status", "connecting");
    Object.assign(status.style, {
        position: "absolute", left: "12px", bottom: "12px", zIndex: "2",
        padding: "6px 9px", borderRadius: "6px", background: "rgba(15,18,24,.82)",
        color: "#f5f7fa", font: "12px/1.3 system-ui,sans-serif", pointerEvents: "none",
    });
    status.textContent = "Connecting to MolSysViewer…";
    el.append(video, inputSurface, status);

    let socket: WebSocket | null = null;
    let connection: RTCPeerConnection | null = null;
    let inputChannel: RTCDataChannel | null = null;
    let closed = false;
    let serverClosing = false;
    let terminalFailure = false;
    let signalSequence = 0;
    let controlSequence = 0;
    let inputSequence = 0;
    let registered = false;
    let pendingCandidates: RTCIceCandidateInit[] = [];
    let pendingMove: PointerEvent | null = null;
    let moveFrame = 0;
    let reconnectTimer = 0;
    let disconnectTimer = 0;
    let mediaRouteTimer = 0;
    let reconnectAttempt = 0;
    const maxReconnectAttempts = 3;

    const setStatus = (state: string, text: string) => {
        status.setAttribute("data-molsysviewer-remote-status", state);
        status.textContent = text;
        status.style.display = state === "ready" ? "none" : "block";
    };
    const sendJson = (value: Record<string, unknown>) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) throw new Error("remote client socket is not open");
        socket.send(JSON.stringify(value));
    };
    const sendControl = (
        action: string,
        payload: Record<string, unknown>,
        direction: "command" | "request",
    ) => {
        const messageId = `${options.endpointId}:control:${++controlSequence}`;
        sendJson({
            kind: "control",
            envelope: {
                protocolVersion: 1,
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: options.endpointId,
                targetEndpointId: `python:${options.viewerId}`,
                messageId,
                operationId: messageId,
                direction,
                action,
                payload: { event: action, ...payload },
                actorId: options.actorId,
                actorKind: "human",
            },
        });
    };
    const emitWorkbench = (intent: RemoteWorkbenchAction) => {
        sendControl(
            intent.action,
            intent.details ?? {},
            intent.action === "selection_query_preview_request" ? "request" : "command",
        );
    };
    const downloadArtifact = (artifact: RemoteDownloadArtifact) => {
        const url = new URL(artifact.url, window.location.href);
        if (url.origin !== window.location.origin) {
            throw new Error("remote download URL escaped the authenticated session origin");
        }
        const link = document.createElement("a");
        link.href = url.href;
        link.download = artifact.filename;
        link.style.display = "none";
        document.body.appendChild(link);
        link.click();
        link.remove();
    };
    const uploadFile = async (file: File): Promise<RemoteUploadResult> => {
        const form = new FormData();
        form.append("file", file, file.name);
        const response = await fetch(new URL("./upload", window.location.href), {
            method: "POST",
            credentials: "same-origin",
            cache: "no-store",
            body: form,
        });
        let value: any;
        try {
            value = await response.json();
        } catch {
            throw new Error(`Molecular upload failed with HTTP ${response.status}`);
        }
        if (!response.ok || value?.uploaded !== true) {
            throw new Error(String(value?.message ?? `Molecular upload failed with HTTP ${response.status}`));
        }
        return {
            filename: String(value.filename ?? file.name),
            nAtoms: Number(value.n_atoms ?? 0),
            nStructures: Number(value.n_structures ?? 0),
        };
    };
    const workbench = new RemoteWorkbench(el, emitWorkbench, downloadArtifact, uploadFile);
    const emitSignal = (kind: string, payload: Record<string, unknown>) => {
        sendJson({
            kind: "signal",
            packet: {
                protocolVersion: 1,
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: options.endpointId,
                messageId: `${options.endpointId}:signal:${++signalSequence}`,
                kind,
                payload,
            },
        });
    };

    const videoPoint = (event: PointerEvent | WheelEvent): Point | null => {
        const rect = inputSurface.getBoundingClientRect();
        const sourceWidth = video.videoWidth || rect.width;
        const sourceHeight = video.videoHeight || rect.height;
        const scale = Math.min(rect.width / sourceWidth, rect.height / sourceHeight);
        const width = sourceWidth * scale;
        const height = sourceHeight * scale;
        const left = rect.left + (rect.width - width) / 2;
        const top = rect.top + (rect.height - height) / 2;
        if (event.clientX < left || event.clientX > left + width || event.clientY < top || event.clientY > top + height) {
            return null;
        }
        return { x: (event.clientX - left) / width, y: (event.clientY - top) / height };
    };
    const sendInput = (kind: string, payload: Record<string, unknown>) => {
        const rect = inputSurface.getBoundingClientRect();
        const packet = {
            protocolVersion: 1,
            viewerId: options.viewerId,
            sessionId: options.sessionId,
            endpointId: options.endpointId,
            sequence: ++inputSequence,
            timestampMs: performance.now(),
            kind,
            viewport: {
                width: Math.max(1, rect.width),
                height: Math.max(1, rect.height),
                devicePixelRatio: window.devicePixelRatio || 1,
            },
            payload,
        };
        const encoded = JSON.stringify(packet);
        if (inputChannel?.readyState === "open") inputChannel.send(encoded);
        else sendJson({ kind: "input", packet });
    };
    const sendPointer = (event: PointerEvent) => {
        const point = videoPoint(event);
        if (!point) return;
        sendInput("pointer", {
            phase: event.type === "pointerdown" ? "down" :
                event.type === "pointerup" ? "up" :
                    event.type === "pointercancel" ? "cancel" : "move",
            pointerType: ["mouse", "pen", "touch"].includes(event.pointerType) ? event.pointerType : "mouse",
            pointerId: event.pointerId,
            ...point,
            button: event.button,
            buttons: event.buttons,
            modifiers: modifiers(event),
        });
    };
    const onPointer = (event: PointerEvent) => {
        if (event.type === "pointerdown") {
            inputSurface.focus();
            inputSurface.setPointerCapture(event.pointerId);
        }
        if (event.type === "pointermove") {
            pendingMove = event;
            if (!moveFrame) {
                moveFrame = requestAnimationFrame(() => {
                    moveFrame = 0;
                    if (pendingMove) sendPointer(pendingMove);
                    pendingMove = null;
                });
            }
            return;
        }
        sendPointer(event);
    };
    for (const type of ["pointerdown", "pointermove", "pointerup", "pointercancel"] as const) {
        inputSurface.addEventListener(type, onPointer);
    }
    inputSurface.addEventListener("wheel", event => {
        event.preventDefault();
        const point = videoPoint(event);
        if (!point) return;
        sendInput("wheel", {
            ...point,
            deltaX: event.deltaX,
            deltaY: event.deltaY,
            deltaMode: event.deltaMode,
            modifiers: modifiers(event),
        });
    }, { passive: false });
    for (const type of ["keydown", "keyup"] as const) {
        inputSurface.addEventListener(type, event => {
            sendInput("key", {
                phase: type === "keydown" ? "down" : "up",
                code: event.code,
                repeat: event.repeat,
                modifiers: modifiers(event),
            });
        });
    }

    const handleSignal = async (value: unknown) => {
        const validation = validateSignalingPacket(value, {
            viewerId: options.viewerId,
            sessionId: options.sessionId,
            endpointId: options.workerEndpointId,
        });
        if (validation.status === "rejected") {
            throw new Error(`${validation.reason}: ${validation.detail}`);
        }
        const packet = validation.packet;
        const kind = packet.kind as string;
        const payload = packet.payload as Record<string, unknown>;
        if (kind === "offer") {
            connection?.close();
            const peer = new RTCPeerConnection({ iceServers: options.iceServers ?? [] });
            connection = peer;
            pendingCandidates = [];
            peer.addEventListener("icecandidate", event => {
                emitSignal(
                    event.candidate ? "ice-candidate" : "ice-complete",
                    event.candidate ? { ...event.candidate.toJSON() } : {},
                );
            });
            peer.addEventListener("track", event => {
                video.srcObject = event.streams[0] ?? new MediaStream([event.track]);
                void video.play();
            });
            peer.addEventListener("datachannel", event => {
                if (event.channel.label !== "input") {
                    event.channel.close();
                    return;
                }
                inputChannel = event.channel;
                inputChannel.addEventListener("open", () => {
                    sendJson({ kind: "peer-state", state: "input-open" });
                });
            });
            peer.addEventListener("connectionstatechange", () => {
                if (connection !== peer) return;
                if (peer.connectionState === "connected") {
                    window.clearTimeout(disconnectTimer);
                    window.clearTimeout(mediaRouteTimer);
                    reconnectAttempt = 0;
                    setStatus("ready", "Connected");
                    sendJson({ kind: "peer-state", state: "connected" });
                }
                else if (peer.connectionState === "failed") {
                    setStatus("degraded", "Video connection failed; reconnecting…");
                    socket?.close(4001, "video connection failed");
                }
                else if (peer.connectionState === "disconnected") {
                    setStatus("degraded", "Video connection interrupted…");
                    window.clearTimeout(disconnectTimer);
                    disconnectTimer = window.setTimeout(() => {
                        if (connection === peer && peer.connectionState === "disconnected") {
                            socket?.close(4002, "video connection stalled");
                        }
                    }, 2_000);
                }
                else if (peer.connectionState === "closed") {
                    if (!closed && !terminalFailure) setStatus("disconnected", "Remote session disconnected");
                }
                else setStatus("negotiating", `Video: ${peer.connectionState}`);
            });
            peer.addEventListener("iceconnectionstatechange", () => {
                if (connection !== peer) return;
                if (["checking", "connected", "completed"].includes(peer.iceConnectionState)) {
                    setStatus("negotiating", `Remote video route: ${peer.iceConnectionState}`);
                }
            });
            setStatus("negotiating", "Negotiating remote video…");
            await peer.setRemoteDescription({ type: "offer", sdp: payload.sdp as string });
            for (const candidate of pendingCandidates.splice(0)) await peer.addIceCandidate(candidate);
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            emitSignal("answer", { sdp: answer.sdp ?? "" });
            window.clearTimeout(mediaRouteTimer);
            mediaRouteTimer = window.setTimeout(() => {
                if (
                    connection === peer
                    && !["connected", "completed"].includes(peer.iceConnectionState)
                ) {
                    terminalFailure = true;
                    setStatus(
                        "failed",
                        "No WebRTC media route. Configure TURN or use client rendering.",
                    );
                    stopPeer();
                }
            }, 15_000);
            return;
        }
        if (kind === "ice-candidate") {
            const candidate = payload as RTCIceCandidateInit;
            if (connection?.remoteDescription) await connection.addIceCandidate(candidate);
            else pendingCandidates.push(candidate);
        }
    };

    const stopPeer = () => {
        window.clearTimeout(disconnectTimer);
        window.clearTimeout(mediaRouteTimer);
        inputChannel?.close();
        inputChannel = null;
        const previous = connection;
        connection = null;
        previous?.close();
        for (const track of (video.srcObject as MediaStream | null)?.getTracks() ?? []) track.stop();
        video.srcObject = null;
    };

    const scheduleReconnect = () => {
        if (closed || terminalFailure || reconnectTimer) return;
        reconnectAttempt += 1;
        if (reconnectAttempt > maxReconnectAttempts) {
            setStatus("disconnected", "Remote session disconnected");
            return;
        }
        const delay = 250 * 2 ** (reconnectAttempt - 1);
        setStatus("reconnecting", `Reconnecting (${reconnectAttempt}/${maxReconnectAttempts})…`);
        reconnectTimer = window.setTimeout(() => {
            reconnectTimer = 0;
            void connectSocket(false).catch(() => undefined);
        }, delay);
    };

    const handleSocketMessage = (candidate: WebSocket, event: MessageEvent) => {
        void (async () => {
            const value = JSON.parse(String(event.data));
            if (value?.kind === "registered") {
                registered = true;
                setStatus("negotiating", "Starting remote video…");
                sendControl(
                    "request_popup_scene_snapshot",
                    { mode: "panel", popup_endpoint_id: options.endpointId },
                    "request",
                );
                return;
            }
            if (!registered) throw new Error("remote client received traffic before registration");
            if (value?.kind === "session-closing") {
                serverClosing = true;
                setStatus("disconnected", "Remote session disconnected");
                candidate.close(1000, "server closed session");
                return;
            }
            if (value?.kind === "session-state") {
                if (value.state === "recovering") {
                    stopPeer();
                    setStatus("recovering", "Recovering remote renderer…");
                    return;
                }
                if (value.state === "recovered") {
                    setStatus("negotiating", "Restarting remote video…");
                    return;
                }
                if (value.state === "failed") {
                    terminalFailure = true;
                    stopPeer();
                    setStatus("failed", String(value.detail ?? "Remote renderer failed"));
                    return;
                }
                throw new Error("remote client received an unknown session state");
            }
            if (value?.kind === "signal") {
                await handleSignal(value.packet);
                return;
            }
            if (value?.kind === "control") {
                const envelope = value.envelope;
                if (
                    !envelope || typeof envelope !== "object"
                    || envelope.protocolVersion !== 1
                    || envelope.viewerId !== options.viewerId
                    || envelope.sessionId !== options.sessionId
                    || envelope.endpointId !== `python:${options.viewerId}`
                    || (envelope.targetEndpointId !== undefined && envelope.targetEndpointId !== options.endpointId)
                    || !envelope.payload || typeof envelope.payload !== "object"
                    || (envelope.payload.event ?? envelope.payload.op) !== envelope.action
                ) {
                    throw new Error("remote client received an invalid control envelope");
                }
                if (envelope.action === "popup_scene_snapshot") {
                    const messages = envelope.payload.messages;
                    if (!Array.isArray(messages)) throw new Error("panel snapshot messages are malformed");
                    for (const message of messages) workbench.apply(message);
                } else {
                    workbench.apply(envelope.payload);
                }
                return;
            }
            throw new Error("remote client received an unknown wire message");
        })().catch(error => {
            if (socket !== candidate) return;
            console.error("[MolSysViewer remote client] wire failure", error);
            terminalFailure = true;
            setStatus("failed", "Remote session protocol failed");
            candidate.close(1011, "client wire failure");
        });
    };

    const connectSocket = (initial: boolean): Promise<void> => new Promise((resolve, reject) => {
        registered = false;
        stopPeer();
        const candidate = new WebSocket(options.websocketUrl, ["molsysviewer-session-v1"]);
        socket = candidate;
        const timer = window.setTimeout(() => {
            candidate.close();
            reject(new Error("remote client WebSocket timed out"));
        }, 10_000);
        candidate.addEventListener("message", event => handleSocketMessage(candidate, event));
        candidate.addEventListener("open", () => {
            window.clearTimeout(timer);
            if (socket !== candidate) return;
            candidate.send(JSON.stringify({
                kind: "register",
                protocolVersion: 1,
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: options.endpointId,
                role: "browser-client",
                actorId: options.actorId,
                actorKind: "human",
                capabilities: ["command-origin", "input-send", "video-receive", "workbench"],
            }));
            resolve();
        }, { once: true });
        candidate.addEventListener("error", () => {
            window.clearTimeout(timer);
            if (socket === candidate && !closed && !terminalFailure) {
                setStatus("degraded", "Remote session connection interrupted…");
            }
            reject(new Error("remote client WebSocket failed"));
        }, { once: true });
        candidate.addEventListener("close", event => {
            window.clearTimeout(timer);
            if (socket !== candidate) return;
            registered = false;
            stopPeer();
            if (!closed && !serverClosing && !terminalFailure) {
                scheduleReconnect();
            }
        });
    });

    await connectSocket(true);

    return {
        video,
        workbench,
        get socket() {
            if (!socket) throw new Error("remote client socket is unavailable");
            return socket;
        },
        peerConnection: () => connection,
        close() {
            if (closed) return;
            closed = true;
            window.clearTimeout(reconnectTimer);
            window.clearTimeout(disconnectTimer);
            if (moveFrame) cancelAnimationFrame(moveFrame);
            workbench.dispose();
            stopPeer();
            socket?.close(1000, "client closed");
        },
    };
}
