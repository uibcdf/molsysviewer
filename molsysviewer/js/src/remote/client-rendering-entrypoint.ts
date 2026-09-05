import { render } from "../index";
import { RemoteFileControls, type RemoteUploadResult } from "../ui/remote-file-controls";

export interface RemoteRenderedClientOptions {
    el: HTMLElement;
    websocketUrl: string;
    viewerId: string;
    sessionId: string;
    endpointId: string;
    actorId: string;
}

type DataHeader = {
    kind: "data";
    message: Record<string, unknown>;
    bufferCount: number;
    byteLengths: number[];
};

function isEnvelope(message: Record<string, unknown>): boolean {
    return message.protocolVersion === 1
        && typeof message.viewerId === "string"
        && typeof message.sessionId === "string"
        && typeof message.endpointId === "string"
        && typeof message.messageId === "string"
        && typeof message.direction === "string"
        && typeof message.action === "string"
        && !!message.payload;
}

/** Adapt the authenticated session socket to the four-method AnyWidget model seam. */
export async function bootRemoteRenderedClient(options: RemoteRenderedClientOptions) {
    const { el } = options;
    Object.assign(el.style, { position: "relative", overflow: "hidden", background: "#080b10" });
    const status = document.createElement("div");
    status.setAttribute("data-molsysviewer-remote-status", "connecting");
    Object.assign(status.style, {
        position: "absolute", left: "12px", bottom: "12px", zIndex: "4",
        padding: "6px 9px", borderRadius: "6px", background: "rgba(15,18,24,.82)",
        color: "#f5f7fa", font: "12px/1.3 system-ui,sans-serif", pointerEvents: "none",
    });
    status.textContent = "Connecting to MolSysViewer…";
    el.append(status);

    let socket: WebSocket | null = null;
    let socketRegistered = false;
    let closed = false;
    let serverClosing = false;
    let terminalFailure = false;
    let reconnectTimer = 0;
    let reconnectAttempt = 0;
    const maxReconnectAttempts = 3;
    const setStatus = (state: string, text: string) => {
        status.setAttribute("data-molsysviewer-remote-status", state);
        status.textContent = text;
        status.style.display = state === "ready" ? "none" : "block";
    };
    const listeners = new Map<string, Set<(...args: any[]) => void>>();
    const values: Record<string, unknown> = {
        runtime_viewer_id: options.viewerId,
        runtime_session_id: options.sessionId,
        runtime_endpoint_id: options.endpointId,
        runtime_actor_id: options.actorId,
        runtime_actor_kind: "human",
        initial_messages: [],
        debug_js: false,
        enable_popout: false,
        panel_mode_style: "drawer",
        controls_mode: "classic",
        viewer_mode: "integrated",
        autohide_controls: true,
    };
    const model = {
        get: (name: string) => values[name],
        on(name: string, callback: (...args: any[]) => void) {
            const bucket = listeners.get(name) ?? new Set();
            bucket.add(callback);
            listeners.set(name, bucket);
        },
        off(name: string, callback: (...args: any[]) => void) {
            listeners.get(name)?.delete(callback);
        },
        send(message: Record<string, unknown>) {
            const envelope = isEnvelope(message);
            if (!socket || socket.readyState !== WebSocket.OPEN || !socketRegistered) {
                // Lifecycle acknowledgements belong to the interrupted binary
                // generation and transient events describe a connection that no
                // longer exists; neither may be replayed on the fresh attachment.
                // User commands/requests still fail visibly while disconnected.
                if (
                    !envelope
                    || closed
                    || serverClosing
                    || message.direction === "event"
                    || message.direction === "ack"
                ) return;
                throw new Error("remote rendered client socket is not open");
            }
            socket.send(JSON.stringify(
                envelope
                    ? { kind: "control", envelope: message }
                    : { kind: "raw", message },
            ));
        },
    };

    let disposeRender: (() => void) | undefined;
    let fileControls: RemoteFileControls | undefined;
    let hasRendered = false;
    let resolveRegistration!: () => void;
    let rejectRegistration!: (error: Error) => void;
    const registration = new Promise<void>((resolve, reject) => {
        resolveRegistration = resolve;
        rejectRegistration = reject;
    });
    void registration.catch(() => undefined);

    const emitCustom = (message: Record<string, unknown>, buffers: DataView[] = []) => {
        for (const callback of listeners.get("msg:custom") ?? []) callback(message, buffers);
    };
    const downloadArtifact = (payload: Record<string, unknown>) => {
        if (typeof payload.url !== "string" || typeof payload.filename !== "string") return;
        const url = new URL(payload.url, window.location.href);
        if (url.origin !== window.location.origin) {
            throw new Error("remote download URL escaped the authenticated session origin");
        }
        const link = document.createElement("a");
        link.href = url.href;
        link.download = payload.filename;
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
    const announceReady = () => model.send({
        event: "ready",
        capabilities: {
            binary_structure_data: [1],
            max_buffer_bytes: 16 * 1024 * 1024,
            transferable_array_buffer: false,
        },
    });
    const handleJson = (candidate: WebSocket, value: any, state: { registered: boolean; header: DataHeader | null; buffers: DataView[] }) => {
        if (value?.kind === "registered") {
            state.registered = true;
            if (candidate === socket) socketRegistered = true;
            reconnectAttempt = 0;
            if (!hasRendered) {
                hasRendered = true;
                disposeRender = render({ model, el: options.el });
                fileControls = new RemoteFileControls(options.el, uploadFile);
            } else {
                announceReady();
            }
            setStatus("ready", "Connected");
            resolveRegistration();
            return;
        }
        if (!state.registered) throw new Error("remote rendered client received traffic before registration");
        if (value?.kind === "session-closing") {
            serverClosing = true;
            setStatus("disconnected", "Remote session disconnected");
            candidate.close(1000, "server closed session");
            return;
        }
        if (value?.kind === "control") {
            if (value.envelope?.action === "remote_download_ready") {
                downloadArtifact(value.envelope.payload ?? {});
                return;
            }
            if (value.envelope?.action === "remote_download_failed") {
                console.error(
                    "[MolSysViewer remote download]",
                    String(value.envelope?.payload?.message ?? "Download failed"),
                );
                return;
            }
            emitCustom(value.envelope);
            return;
        }
        if (value?.kind === "data") {
            if (state.header !== null || !Number.isInteger(value.bufferCount) || value.bufferCount < 0
                || !Array.isArray(value.byteLengths) || value.byteLengths.length !== value.bufferCount
                || value.byteLengths.some((length: unknown) => !Number.isInteger(length) || Number(length) < 0)) {
                throw new Error("remote rendered client data header is malformed");
            }
            state.header = value as DataHeader;
            state.buffers = [];
            if (state.header.bufferCount === 0) {
                emitCustom(state.header.message);
                state.header = null;
            }
            return;
        }
        throw new Error("remote rendered client received an unknown wire message");
    };

    const scheduleReconnect = () => {
        if (closed || serverClosing || terminalFailure || reconnectTimer) return;
        reconnectAttempt += 1;
        if (reconnectAttempt > maxReconnectAttempts) {
            setStatus("disconnected", "Remote session disconnected");
            return;
        }
        setStatus("reconnecting", `Reconnecting (${reconnectAttempt}/${maxReconnectAttempts})…`);
        reconnectTimer = window.setTimeout(() => {
            reconnectTimer = 0;
            connectSocket();
        }, 250 * 2 ** (reconnectAttempt - 1));
    };
    const connectSocket = () => {
        const candidate = new WebSocket(options.websocketUrl, ["molsysviewer-session-v1"]);
        candidate.binaryType = "arraybuffer";
        socket = candidate;
        socketRegistered = false;
        const state = { registered: false, header: null as DataHeader | null, buffers: [] as DataView[] };
        let queue = Promise.resolve();
        const timer = window.setTimeout(() => candidate.close(), 10_000);
        candidate.addEventListener("message", event => {
            queue = queue.then(() => {
                if (typeof event.data === "string") {
                    handleJson(candidate, JSON.parse(event.data), state);
                    return;
                }
                if (state.header === null || !(event.data instanceof ArrayBuffer)) {
                    throw new Error("unexpected remote rendered client binary frame");
                }
                const index = state.buffers.length;
                if (event.data.byteLength !== state.header.byteLengths[index]) {
                    throw new Error("remote rendered client binary frame length mismatch");
                }
                state.buffers.push(new DataView(event.data));
                if (state.buffers.length === state.header.bufferCount) {
                    const complete = state.header;
                    const buffers = state.buffers;
                    state.header = null;
                    state.buffers = [];
                    emitCustom(complete.message, buffers);
                }
            }).catch(error => {
                rejectRegistration(error instanceof Error ? error : new Error(String(error)));
                console.error("[MolSysViewer remote rendered client] wire failure", error);
                terminalFailure = true;
                setStatus("failed", "Remote session protocol failed");
                candidate.close(1011, "client wire failure");
            });
        });
        candidate.addEventListener("open", () => {
            window.clearTimeout(timer);
            setStatus("connecting", "Authenticating remote session…");
            candidate.send(JSON.stringify({
                kind: "register",
                protocolVersion: 1,
                viewerId: options.viewerId,
                sessionId: options.sessionId,
                endpointId: options.endpointId,
                role: "browser-client",
                actorId: options.actorId,
                actorKind: "human",
                capabilities: ["command-origin", "input-send", "render", "structure-receive", "workbench"],
            }));
        }, { once: true });
        candidate.addEventListener("error", () => {
            if (!hasRendered) {
                setStatus("failed", "Remote session connection failed");
                rejectRegistration(new Error("remote rendered client WebSocket failed"));
            } else if (!closed && !serverClosing && !terminalFailure) {
                setStatus("degraded", "Remote session connection interrupted…");
            }
        }, { once: true });
        candidate.addEventListener("close", () => {
            window.clearTimeout(timer);
            if (socket !== candidate) return;
            state.registered = false;
            socketRegistered = false;
            if (!hasRendered) rejectRegistration(new Error("remote rendered client socket closed"));
            scheduleReconnect();
        });
    };
    connectSocket();
    await registration;
    return {
        get socket() {
            if (!socket) throw new Error("remote rendered client socket is unavailable");
            return socket;
        },
        get registered() {
            return socketRegistered;
        },
        close() {
            if (closed) return;
            closed = true;
            socketRegistered = false;
            window.clearTimeout(reconnectTimer);
            fileControls?.dispose();
            disposeRender?.();
            socket?.close(1000, "client closed");
            status.remove();
        },
    };
}
