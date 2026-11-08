import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { performance } from "node:perf_hooks";

/** JSON-lines fixture transport. Requests create fresh scenarios; EOF owns cleanup. */
export class PythonFixtureBridge {
    private readonly child;
    private readonly lines;
    private stderr = "";
    private sequence = 0;
    private stopped = false;
    private readonly pending = new Map<number, { resolve: (value: any) => void; reject: (error: Error) => void;
        timer: NodeJS.Timeout; started: number; label: string }>();
    private readonly transport = { responseCount: 0, responseBytes: 0, maxResponseBytes: 0,
        maxPending: 0, observations: [] as Array<{ id: number; label: string; elapsedMs: number; bytes: number }> };
    private readonly observeTransport: boolean;

    constructor(script: string, cwd: string, private readonly timeoutMs = 90000,
        options: { args?: readonly string[], env?: NodeJS.ProcessEnv, observeTransport?: boolean } = {}) {
        this.observeTransport = options.observeTransport ?? false;
        this.child = spawn(process.env.PYTHON || "python", [script, "--serve", ...(options.args ?? [])],
            { cwd, env: options.env, stdio: ["pipe", "pipe", "pipe"] });
        this.lines = createInterface({ input: this.child.stdout });
        this.child.stderr.on("data", chunk => { this.stderr = (this.stderr + chunk).slice(-65536); });
        this.child.on("error", error => this.fail(error));
        this.child.stdin.on("error", error => this.fail(error));
        this.child.on("exit", (code, signal) => {
            this.stopped = true;
            if (this.pending.size) this.fail(new Error(`Python fixture worker exited (${code ?? signal}): ${this.stderr}`));
        });
        this.lines.on("line", line => {
            try {
                const response = JSON.parse(line);
                const request = this.pending.get(response.id);
                if (!request) throw new Error(`Unexpected Python fixture response: ${line.slice(0, 300)}`);
                if (this.observeTransport) {
                    const bytes = Buffer.byteLength(line);
                    this.transport.responseCount++; this.transport.responseBytes += bytes;
                    this.transport.maxResponseBytes = Math.max(this.transport.maxResponseBytes, bytes);
                    this.transport.observations.push({ id: response.id, label: request.label,
                        elapsedMs: performance.now() - request.started, bytes });
                    if (this.transport.observations.length > 128) this.transport.observations.shift();
                }
                clearTimeout(request.timer);
                this.pending.delete(response.id);
                if (response.error) request.reject(new Error(response.error)); else request.resolve(response.result);
            } catch (error) { this.fail(error instanceof Error ? error : new Error(String(error))); }
        });
    }

    request(events: unknown[] = [], family?: string): Promise<any> {
        if (this.stopped) return Promise.reject(new Error(`Python fixture worker is closed: ${this.stderr}`));
        const id = ++this.sequence;
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => this.fail(new Error(`Python fixture request ${id} exceeded ${this.timeoutMs} ms: ${this.stderr}`)), this.timeoutMs);
            const first: any = events[0];
            const payload = first?.payload ?? first;
            this.pending.set(id, { resolve, reject, timer, started: performance.now(),
                label: payload?.moving_fixture ?? payload?.event ?? payload?.op ?? "bootstrap" });
            if (this.observeTransport) this.transport.maxPending = Math.max(this.transport.maxPending, this.pending.size);
            this.child.stdin.write(JSON.stringify({ id, events, family }) + "\n", error => { if (error) this.fail(error); });
        });
    }

    getTransportObservation() {
        return { ...this.transport, observations: this.transport.observations.map(item => ({ ...item })) };
    }

    private fail(error: Error) {
        this.stopped = true;
        for (const request of this.pending.values()) { clearTimeout(request.timer); request.reject(error); }
        this.pending.clear();
        this.child.kill("SIGTERM");
    }

    async close(): Promise<void> {
        if (this.child.exitCode !== null || this.child.signalCode !== null) { this.lines.close(); return; }
        await new Promise<void>(resolve => {
            const timer = setTimeout(() => this.child.kill("SIGKILL"), 5000);
            this.child.once("exit", () => { clearTimeout(timer); resolve(); });
            this.child.stdin.end();
        });
        this.lines.close();
        this.stopped = true;
    }
}
