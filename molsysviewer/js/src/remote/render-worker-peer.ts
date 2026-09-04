import { RemoteInputAdapter } from "../messages/remote-input-adapter";
import { validateSignalingPacket } from "../messages/remote-protocol";

export interface RemoteHumanIdentity {
    endpointId: string;
    actorId: string;
}

export interface RenderWorkerPeerOptions {
    viewerId: string;
    sessionId: string;
    workerEndpointId: string;
    frameRate?: number;
    maxBitrate?: number;
    iceServers?: RTCIceServer[];
}

/** One WebRTC video/input attachment owned by the render worker. */
export class RenderWorkerPeer {
    private connection: RTCPeerConnection | null = null;
    private stream: MediaStream | null = null;
    private inputChannel: RTCDataChannel | null = null;
    private client: RemoteHumanIdentity | null = null;
    private signalSequence = 0;
    private pendingCandidates: RTCIceCandidateInit[] = [];
    private observedInput = false;
    private frameKeepalive = 0;

    constructor(
        private readonly canvas: HTMLCanvasElement,
        private readonly options: RenderWorkerPeerOptions,
        private readonly sendSignal: (packet: Record<string, unknown>) => void,
        private readonly inputAdapter: RemoteInputAdapter,
        private readonly onFirstInput?: (sequence: number) => void,
        private readonly requestDraw?: () => void,
    ) {}

    get clientIdentity(): RemoteHumanIdentity | null {
        return this.client;
    }

    get peerConnection(): RTCPeerConnection | null {
        return this.connection;
    }

    async diagnostics(): Promise<Record<string, unknown>> {
        const stats: Record<string, unknown>[] = [];
        if (this.connection) {
            const report = await this.connection.getStats();
            report.forEach(item => {
                if (["outbound-rtp", "media-source", "codec", "candidate-pair"].includes(item.type)) {
                    stats.push(Object.fromEntries(Object.entries(item)));
                }
            });
        }
        return {
            connectionState: this.connection?.connectionState ?? null,
            iceConnectionState: this.connection?.iceConnectionState ?? null,
            iceGatheringState: this.connection?.iceGatheringState ?? null,
            signalingState: this.connection?.signalingState ?? null,
            localCandidateCount: candidateCount(this.connection?.localDescription?.sdp),
            remoteCandidateCount: candidateCount(this.connection?.remoteDescription?.sdp),
            canvas: { width: this.canvas.width, height: this.canvas.height },
            tracks: (this.stream?.getVideoTracks() ?? []).map(track => ({
                id: track.id,
                readyState: track.readyState,
                enabled: track.enabled,
                muted: track.muted,
                settings: track.getSettings(),
            })),
            stats,
        };
    }

    async start(client: RemoteHumanIdentity): Promise<void> {
        this.close();
        this.client = client;
        const connection = new RTCPeerConnection({ iceServers: this.options.iceServers ?? [] });
        this.connection = connection;
        connection.addEventListener("icecandidate", event => {
            this.emitSignal(
                event.candidate ? "ice-candidate" : "ice-complete",
                event.candidate ? { ...event.candidate.toJSON() } : {},
            );
        });
        connection.addEventListener("connectionstatechange", () => {
            if (["failed", "closed"].includes(connection.connectionState)) {
                this.inputChannel?.close();
            }
        });

        const frameRate = this.options.frameRate ?? 30;
        const stream = this.canvas.captureStream(frameRate);
        this.stream = stream;
        this.frameKeepalive = window.setInterval(() => this.requestCapturedFrame(), 2_000);
        for (const track of stream.getVideoTracks()) {
            track.contentHint = "detail";
            const sender = connection.addTrack(track, stream);
            const parameters = sender.getParameters();
            parameters.degradationPreference = "maintain-resolution";
            parameters.encodings = parameters.encodings?.length ? parameters.encodings : [{}];
            parameters.encodings[0].maxBitrate = this.options.maxBitrate ?? 8_000_000;
            parameters.encodings[0].maxFramerate = frameRate;
            parameters.encodings[0].scaleResolutionDownBy = 1;
            await sender.setParameters(parameters);
        }

        const input = connection.createDataChannel("input", { ordered: true });
        this.inputChannel = input;
        input.addEventListener("message", event => {
            try {
                const result = this.inputAdapter.handle(JSON.parse(String(event.data)));
                if (result.status === "rejected") {
                    throw new Error(`${result.reason}: ${result.detail}`);
                }
                if (!this.observedInput) {
                    this.observedInput = true;
                    this.onFirstInput?.(result.sequence);
                }
            } catch (error) {
                console.error("[MolSysViewer render worker] rejected input channel packet", error);
                input.close();
            }
        });

        const offer = await connection.createOffer();
        await connection.setLocalDescription(offer);
        this.requestCapturedFrame();
        this.emitSignal("offer", { sdp: offer.sdp ?? "" });
    }

    async handleSignal(value: unknown): Promise<void> {
        const client = this.client;
        const connection = this.connection;
        if (!client || !connection) throw new Error("render-worker peer has not started");
        const validation = validateSignalingPacket(value, {
            viewerId: this.options.viewerId,
            sessionId: this.options.sessionId,
            endpointId: client.endpointId,
        });
        if (validation.status === "rejected") {
            throw new Error(`${validation.reason}: ${validation.detail}`);
        }
        const packet = validation.packet;
        const kind = packet.kind as string;
        const payload = packet.payload as Record<string, unknown>;
        if (kind === "answer") {
            await connection.setRemoteDescription({ type: "answer", sdp: payload.sdp as string });
            for (const candidate of this.pendingCandidates.splice(0)) {
                await connection.addIceCandidate(candidate);
            }
            // A mostly static molecular scene may have completed its last draw
            // before the remote description existed. Canvas capture is then
            // allowed to deliver no initial frame even though ICE and the data
            // channel connect. Request after negotiation, with short follow-ups
            // covering encoder startup, so the first decoded frame is not tied
            // to an unrelated later camera interaction.
            this.requestCapturedFrame();
            window.setTimeout(() => this.requestCapturedFrame(), 100);
            window.setTimeout(() => this.requestCapturedFrame(), 500);
            return;
        }
        if (kind === "ice-candidate") {
            const candidate = payload as RTCIceCandidateInit;
            if (connection.remoteDescription) await connection.addIceCandidate(candidate);
            else this.pendingCandidates.push(candidate);
        }
    }

    close(): void {
        window.clearInterval(this.frameKeepalive);
        this.frameKeepalive = 0;
        this.inputChannel?.close();
        this.inputChannel = null;
        this.connection?.close();
        this.connection = null;
        for (const track of this.stream?.getTracks() ?? []) track.stop();
        this.stream = null;
        this.client = null;
        this.pendingCandidates = [];
        this.observedInput = false;
    }

    private emitSignal(kind: string, payload: Record<string, unknown>): void {
        this.sendSignal({
            protocolVersion: 1,
            viewerId: this.options.viewerId,
            sessionId: this.options.sessionId,
            endpointId: this.options.workerEndpointId,
            messageId: `${this.options.workerEndpointId}:signal:${++this.signalSequence}`,
            kind,
            payload,
        });
    }

    private requestCapturedFrame(): void {
        if (!this.stream) return;
        this.requestDraw?.();
        for (const track of this.stream.getVideoTracks()) {
            if (track.readyState === "live") {
                (track as CanvasCaptureMediaStreamTrack).requestFrame?.();
            }
        }
    }
}

function candidateCount(sdp: string | undefined): number {
    return sdp?.match(/^a=candidate:/gm)?.length ?? 0;
}
