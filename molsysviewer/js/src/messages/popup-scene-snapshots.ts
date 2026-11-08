import type { ViewerMessage } from "./viewer-messages";

type Mode = "canvas" | "panel";
type Failure = "request_timeout" | "transfer_timeout" | "cancelled" | "superseded" | "disposed" | "send_failed" | "invalid_snapshot";
export type PopupSceneSnapshotResult = { ok: true; messages: ViewerMessage[] } | { ok: false; reason: Failure };
type Entry = {
    id: string; mode: Mode; endpoint: string | null; stream?: string; generation?: number;
    timer?: ReturnType<typeof setTimeout>; settled: boolean;
    resolve: (result: PopupSceneSnapshotResult) => void;
};

/** A correlated scene reply waits behind its own flow-controlled molecular load.
 * Response silence and molecular progress have separate, bounded deadlines. */
export class PopupSceneSnapshots {
    private readonly pending = new Map<string, Entry>();
    private readonly latest = new Map<Mode, Entry>();
    private disposed = false;

    constructor(private readonly responseMs = 5000, private readonly transferMs = 30000) {}

    request(id: string | null | undefined, mode: Mode, endpoint: string | null) {
        this.cancel(mode, "superseded");
        let entry: Entry;
        const promise = new Promise<PopupSceneSnapshotResult>(resolve => {
            entry = { id: id ?? "", mode, endpoint, settled: false, resolve };
            this.latest.set(mode, entry);
            if (this.disposed || !id) {
                this.finish(entry, { ok: false, reason: this.disposed ? "disposed" : "send_failed" });
                return;
            }
            this.pending.set(id, entry);
            this.arm(entry, this.responseMs, "request_timeout");
        });
        return { promise, isCurrent: () => !this.disposed && this.latest.get(mode) === entry! };
    }

    has(mode: Mode): boolean { return [...this.pending.values()].some(entry => entry.mode === mode); }

    resolve(id: string | undefined, messages: unknown): void {
        const entry = id ? this.pending.get(id) : undefined;
        if (!entry) return;
        this.finish(entry, Array.isArray(messages)
            ? { ok: true, messages: messages as ViewerMessage[] }
            : { ok: false, reason: "invalid_snapshot" });
    }

    /** Only authenticated traffic for this exact destination/generation counts
     * as progress. A foreign acknowledgement cannot keep a request alive. */
    structure(endpoint: string, message: any): void {
        const entry = this.latest.get("canvas");
        if (!entry || entry.settled || entry.endpoint !== endpoint) return;
        const stream = typeof message?.stream_id === "string" && Number.isSafeInteger(message.generation) && message.generation > 0
            ? `${message.stream_id}:${message.generation}` : undefined;
        if (message?.op === "load_molsys_payload") {
            entry.stream = undefined;
            this.arm(entry, this.transferMs, "transfer_timeout");
        } else if (message?.op === "structure_data_begin" && stream) {
            if (entry.generation !== undefined && message.generation <= entry.generation) return;
            entry.stream = stream;
            entry.generation = message.generation;
            this.arm(entry, this.transferMs, "transfer_timeout");
        } else if (message?.event === "structure_data_json_complete") {
            entry.stream = undefined;
            this.arm(entry, this.responseMs, "request_timeout");
        } else if (stream && entry.stream === stream) {
            if (message.op === "structure_data_cancel" || message.event === "structure_data_complete") {
                entry.stream = undefined;
                this.arm(entry, this.responseMs, "request_timeout");
            } else if (message.op === "structure_data_chunk" || message.event === "structure_data_begin_ack"
                || message.event === "structure_data_chunk_ack") {
                this.arm(entry, this.transferMs, "transfer_timeout");
            }
        }
    }

    cancel(mode: Mode, reason: Failure = "cancelled"): void {
        const entry = this.latest.get(mode);
        if (entry) this.finish(entry, { ok: false, reason });
        this.latest.delete(mode);
    }

    dispose(): void {
        this.disposed = true;
        this.cancel("canvas", "disposed");
        this.cancel("panel", "disposed");
    }

    private arm(entry: Entry, ms: number, reason: Failure): void {
        if (entry.timer !== undefined) clearTimeout(entry.timer);
        entry.timer = setTimeout(() => this.finish(entry, { ok: false, reason }), ms);
    }

    private finish(entry: Entry, result: PopupSceneSnapshotResult): void {
        if (entry.settled) return;
        entry.settled = true;
        if (entry.timer !== undefined) clearTimeout(entry.timer);
        this.pending.delete(entry.id);
        entry.resolve(result);
    }
}
