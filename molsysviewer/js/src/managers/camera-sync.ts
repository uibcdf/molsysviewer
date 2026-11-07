import { Binding } from "molstar/lib/mol-util/binding";
import { DefaultTrackballBindings } from "molstar/lib/mol-canvas3d/controls/trackball";

type Subscription = { unsubscribe(): void };
type CameraIntent = { revision: number; inputSerial: number; applied: boolean; superseded: boolean; completed: boolean };
type AuthorityPlan = { kind: "consume" } | { kind: "intent"; intent: CameraIntent };
type PeerReceipt = { snapshot: any; revision?: number; inputSerial: number };

export type CameraIntentApplication = {
    signal: AbortSignal;
    beforeResolve(): void;
    registerCleanup(release: () => void): void;
};

function revision(value: unknown): value is number {
    return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

/** Receipt-time state exists before a renderer or its scene queue is ready. */
export class CameraSyncState {
    revision?: number;
    completedRevision = 0;
    inputSerial = 0;
    authorityInputSerial = 0;
    intent?: CameraIntent;
    private lastIntentRevision = -1;
    private readonly authority = new WeakMap<object, AuthorityPlan>();
    private readonly peers = new WeakMap<object, PeerReceipt | null>();
    private readonly bootstraps = new WeakMap<object, PeerReceipt>();

    receive(message: any): void {
        if (!message || typeof message !== "object" || this.authority.has(message)) return;
        if (message.op === "set_camera_sync_revision") {
            if (revision(message.camera_revision) && (this.revision === undefined || message.camera_revision > this.revision)) this.revision = message.camera_revision;
            this.authority.set(message, { kind: "consume" });
        } else if (["set_camera_snapshot", "reset_view", "reset_camera", "zoom", "zoom_to_position"].includes(message.op)) {
            const next = message.camera_revision;
            if (!revision(next)) {
                if (this.revision !== undefined) this.authority.set(message, { kind: "consume" });
                return;
            }
            if ((this.revision !== undefined && next < this.revision) || next <= this.lastIntentRevision) {
                this.authority.set(message, { kind: "consume" });
                return;
            }
            this.revision = next;
            this.lastIntentRevision = next;
            this.authorityInputSerial = this.inputSerial;
            const intent = this.intent = { revision: next, inputSerial: this.inputSerial, applied: false, superseded: false, completed: false };
            this.authority.set(message, { kind: "intent", intent });
        }
    }

    receivePeer(packet: any): void {
        if (!packet || typeof packet !== "object" || this.peers.has(packet)) return;
        const versioned = "snapshot" in packet || "camera_revision" in packet;
        const valid = versioned ? revision(packet.camera_revision) && this.revision !== undefined
            && packet.camera_revision === this.revision && packet.snapshot && typeof packet.snapshot === "object"
            : this.revision === undefined;
        this.peers.set(packet, valid ? { snapshot: versioned ? packet.snapshot : packet,
            revision: versioned ? packet.camera_revision : undefined, inputSerial: this.inputSerial } : null);
    }

    receiveBootstrap(data: any): void {
        if (data?.cameraSnapshot && typeof data === "object") this.bootstraps.set(data, {
            snapshot: data.cameraSnapshot, revision: revision(data.cameraSnapshotRevision) ? data.cameraSnapshotRevision : undefined,
            inputSerial: this.inputSerial,
        });
    }

    plan(message: any): AuthorityPlan | undefined { return this.authority.get(message); }
    peer(packet: any): PeerReceipt | null { this.receivePeer(packet); return this.peers.get(packet) ?? null; }
    bootstrap(data: any): PeerReceipt | undefined { return this.bootstraps.get(data); }
    canApply(intent: CameraIntent): boolean {
        return this.intent === intent && !intent.superseded && !intent.applied
            && intent.revision === this.revision && intent.inputSerial === this.inputSerial;
    }
    userInput(): void {
        this.inputSerial++;
        if (this.intent) this.intent.superseded = true;
    }
}

type DrawWait = {
    revision: number; kind: "authority" | "peer" | "bootstrap" | "input" | "navigation";
    inputSerial: number; abort: AbortController; target?: any;
    terminalDrawRequested?: boolean;
    releaseState?: () => void; releaseController?: () => void;
};

/** Relay drawn viewpoints with the authority intent that actually completed. */
export class CameraSync {
    private key = "";
    private timer?: ReturnType<typeof setTimeout>;
    private readonly subscriptions: Subscription[] = [];
    private disposed = false;
    private wait?: DrawWait;
    private drawn?: { snapshot: any; revision?: number };

    constructor(private readonly controller: {
        plugin: any;
        getCameraSnapshot(): any;
        setCameraSnapshot(snapshot: any, duration?: number): Promise<void>;
        handleMessage?(message: any, options?: { throwOnError?: boolean; cameraIntent?: CameraIntentApplication }): Promise<void>;
        setCameraNavigationHandler?(factory: () => CameraIntentApplication | undefined): () => void;
    }, private readonly options: {
        enabled(): boolean;
        interacting(): boolean;
        send(packet: any): void;
    }, readonly state = new CameraSyncState()) {
        const canvas = controller.plugin.canvas3d;
        let replay = true;
        const draw = canvas?.didDraw?.subscribe(() => { if (!replay) this.onDraw(); });
        replay = false;
        if (draw) this.subscriptions.push(draw);
        const committed = canvas?.commited?.subscribe(() => this.onCommitted());
        if (committed) this.subscriptions.push(committed);
        const releaseNavigation = controller.setCameraNavigationHandler?.(() => {
            if (this.disposed) return undefined;
            this.state.userInput();
            this.releaseWait(true);
            if (this.state.revision === undefined) return undefined;
            const wait = this.wait = { kind: "navigation", revision: this.state.revision,
                inputSerial: this.state.inputSerial, abort: new AbortController() } as DrawWait;
            return this.application(wait);
        });
        if (releaseNavigation) this.subscriptions.push({ unsubscribe: releaseNavigation });
        const input = canvas?.input;
        const bindings = () => ({ ...DefaultTrackballBindings, ...canvas?.controls?.props?.bindings });
        const subscribe = (stream: any, accepts: (event: any) => boolean) => {
            const sub = stream?.subscribe((event: any) => { if (accepts(event)) this.onUserInput(); });
            if (sub) this.subscriptions.push(sub);
        };
        const buttonMatch = (names: string[], event: any) => names.some(name => bindings()?.[name]
            && Binding.match(bindings()[name], event.buttons, event.modifiers));
        subscribe(input?.drag, event => buttonMatch(["dragRotate", "dragRotateZ", "dragPan", "dragZoom", "dragFocus", "dragFocusZoom"], event));
        subscribe(input?.wheel, event => buttonMatch(["scrollZoom", "scrollFocus", "scrollFocusZoom"], event));
        subscribe(input?.pinch, event => buttonMatch(["dragPan", "scrollZoom"], event));
        subscribe(input?.move, event => !!input?.pointerLock && !!(event.movementX || event.movementY));
        subscribe(input?.keyDown, event => Object.entries(bindings() ?? {}).some(([name, binding]) =>
            name.startsWith("key") && Binding.matchKey(binding as any, event.code, event.modifiers, event.key)));
    }

    get completedRevision(): number | undefined {
        if (this.state.revision === undefined || (this.state.intent?.revision === this.state.completedRevision && !this.state.intent.completed)) return undefined;
        return this.state.completedRevision;
    }

    private fingerprint(snapshot: any, cameraRevision?: number): string {
        const value = cameraRevision === undefined ? snapshot : { snapshot, camera_revision: cameraRevision };
        return JSON.stringify(value, (_key, number) => typeof number === "number" ? Math.round(number * 1e8) / 1e8 : number);
    }

    private reached(snapshot: any, target: any): boolean {
        const near = (a: number, b: number) => Number.isFinite(a) && Number.isFinite(b)
            && Math.abs(a - b) <= 1e-6 * Math.max(1, Math.abs(a), Math.abs(b));
        for (const field of ["position", "target"]) {
            if (!target?.[field] || !snapshot?.[field] || !Array.from(target[field]).every((value: any, index) => near(value, snapshot[field][index]))) return false;
        }
        const a = snapshot.up, b = target.up;
        const an = a && Math.hypot(...a), bn = b && Math.hypot(...b);
        if (!an || !bn || !Array.from(b).every((value: any, index) => near(value / bn, a[index] / an))) return false;
        return snapshot.mode === target.mode && near(snapshot.fov, target.fov)
            && near(snapshot.radius, Math.min(target.radius, snapshot.radiusMax));
    }

    private releaseWait(cancel: boolean): void {
        const wait = this.wait;
        if (!wait) return;
        this.wait = undefined;
        wait.releaseState?.();
        if (cancel) wait.abort.abort();
        wait.releaseController?.();
        // Once its provider is detached, retiring this signal cannot cancel a
        // newer reset that now owns the canvas.
        if (!cancel) wait.abort.abort();
    }

    private onUserInput(): void {
        if (this.disposed) return;
        this.state.userInput();
        this.releaseWait(true);
        if (this.state.revision !== undefined) this.wait = { kind: "input", revision: this.state.revision,
            inputSerial: this.state.inputSerial, abort: new AbortController() };
    }

    private onCommitted(): void {
        const wait = this.wait, canvas = this.controller.plugin.canvas3d;
        if (this.disposed || !wait || wait.terminalDrawRequested || !wait.target
            || wait.revision !== this.state.revision || wait.inputSerial !== this.state.inputSerial
            || canvas?.camera?.transition?.inTransition) return;
        const snapshot = this.controller.getCameraSnapshot();
        if (!snapshot || !this.reached(snapshot, wait.target)) return;
        // A same-pose transition can finish on a tick that does not render.
        // Request its final draw once; only didDraw may complete the intent.
        wait.terminalDrawRequested = true;
        canvas.requestDraw();
    }

    private onDraw() {
        if (this.disposed) return;
        const snapshot = this.controller.getCameraSnapshot();
        if (!snapshot) return;
        const wait = this.wait, canvas = this.controller.plugin.canvas3d;
        if (wait && wait.revision <= (this.state.revision ?? -1) && wait.inputSerial === this.state.inputSerial
            && (wait.kind === "input" || (wait.target && !canvas?.camera?.transition?.inTransition && this.reached(snapshot, wait.target)))) {
            this.state.completedRevision = Math.max(this.state.completedRevision, wait.revision);
            if (this.state.intent?.revision === wait.revision) this.state.intent.completed = true;
            this.releaseWait(false);
        }
        const cameraRevision = this.completedRevision;
        this.drawn = { snapshot, revision: cameraRevision };
        if (this.state.revision !== undefined && cameraRevision !== this.state.revision) return;
        const key = this.fingerprint(snapshot, cameraRevision);
        if (!this.options.enabled() || key === this.key) return;
        // A timer relays the latest actual drawn sample, never an undrawn state
        // labeled with an authority revision that has not completed.
        if (this.timer === undefined) this.timer = setTimeout(() => {
            this.timer = undefined;
            if (this.disposed || !this.options.enabled() || !this.drawn) return;
            const current = this.drawn;
            if (this.state.revision !== undefined && current.revision !== this.state.revision) return;
            const currentKey = this.fingerprint(current.snapshot, current.revision);
            if (currentKey === this.key) return;
            this.key = currentKey;
            this.options.send(current.revision === undefined ? current.snapshot
                : { snapshot: current.snapshot, camera_revision: current.revision });
        }, 20);
    }

    private async applyVersioned(message: any, cameraRevision: number, kind: DrawWait["kind"]): Promise<void> {
        this.releaseWait(false);
        const wait = this.wait = { kind, revision: cameraRevision, inputSerial: this.state.inputSerial,
            abort: new AbortController() } as DrawWait;
        await this.controller.handleMessage?.(message, { throwOnError: true, cameraIntent: this.application(wait) });
    }

    private application(wait: DrawWait): CameraIntentApplication {
        const canvas = this.controller.plugin.canvas3d;
        return {
            signal: wait.abort.signal,
            registerCleanup: release => { wait.releaseController = release; },
            beforeResolve: () => {
                if (this.wait !== wait || wait.abort.signal.aborted) return;
                let replay = true;
                const subscription = canvas.camera.stateChanged.subscribe(() => {
                    if (replay || this.wait !== wait || wait.abort.signal.aborted) return;
                    subscription.unsubscribe();
                    wait.releaseState = undefined;
                    wait.target = structuredClone(canvas.camera.transition.target);
                });
                replay = false;
                wait.releaseState = () => subscription.unsubscribe();
            },
        };
    }

    /** Returns true when this private camera protocol consumed the message. */
    async handleMessage(message: any): Promise<boolean> {
        const plan = this.state.plan(message);
        if (!plan) return false;
        if (plan.kind === "intent" && this.state.canApply(plan.intent)) {
            plan.intent.applied = true;
            await this.applyVersioned(message, plan.intent.revision, "authority");
        }
        return true;
    }

    async apply(packet: any) {
        const receipt = this.state.peer(packet);
        if (!receipt || this.disposed || receipt.inputSerial !== this.state.inputSerial) return;
        if (receipt.revision === undefined) {
            if (this.state.revision !== undefined || this.options.interacting()) return;
            this.key = this.fingerprint(receipt.snapshot);
            if (this.key !== this.fingerprint(this.controller.getCameraSnapshot())) await this.controller.setCameraSnapshot(receipt.snapshot, 0);
            return;
        }
        if (receipt.revision !== this.state.revision || (this.options.interacting()
            && this.state.inputSerial > this.state.authorityInputSerial)) return;
        if (this.wait?.revision === receipt.revision && ["input", "navigation"].includes(this.wait.kind)) return;
        if (this.state.intent) this.state.intent.superseded = true;
        this.key = this.fingerprint(receipt.snapshot, receipt.revision);
        await this.applyVersioned({ op: "set_camera_snapshot", snapshot: receipt.snapshot, duration_ms: 0 }, receipt.revision, "peer");
    }

    async applyBootstrap(data: any): Promise<void> {
        const receipt = this.state.bootstrap(data);
        if (!receipt || this.disposed || receipt.inputSerial !== this.state.inputSerial) return;
        if (this.state.revision === undefined) { await this.apply(receipt.snapshot); return; }
        if (receipt.revision === undefined) return;
        const completed = receipt.revision ?? 0;
        if (completed > this.state.revision || completed < this.state.completedRevision) return;
        if (this.state.intent && !this.state.intent.superseded
            && this.state.completedRevision < this.state.intent.revision && this.state.intent.revision > completed) return;
        if (completed === this.state.revision && this.state.intent) this.state.intent.superseded = true;
        this.key = this.fingerprint(receipt.snapshot, completed);
        await this.applyVersioned({ op: "set_camera_snapshot", snapshot: receipt.snapshot, duration_ms: 0 }, completed, "bootstrap");
    }

    dispose() {
        this.disposed = true;
        if (this.timer !== undefined) clearTimeout(this.timer);
        this.releaseWait(true);
        for (const subscription of this.subscriptions) subscription.unsubscribe();
    }
}
