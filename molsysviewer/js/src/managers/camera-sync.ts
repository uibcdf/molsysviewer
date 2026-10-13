/** Relay resolved viewpoints, including focus transitions and the final draw.
 * Incoming projections are consumed without echo; automatic motion has one
 * host clock and popup controllers retain its settings as followers.
 */
export class CameraSync {
    private key = "";
    private timer?: ReturnType<typeof setTimeout>;
    private subscription?: { unsubscribe(): void };
    private disposed = false;

    constructor(private readonly controller: {
        plugin: any;
        getCameraSnapshot(): any;
        setCameraSnapshot(snapshot: any, duration?: number): Promise<void>;
    }, private readonly options: {
        enabled(): boolean;
        interacting(): boolean;
        send(snapshot: any): void;
    }) {
        this.subscription = controller.plugin.canvas3d?.didDraw?.subscribe(() => this.onDraw());
    }

    private fingerprint(snapshot: any): string {
        return JSON.stringify(snapshot, (_key, value) =>
            typeof value === "number" ? Math.round(value * 1e8) / 1e8 : value);
    }

    private onDraw() {
        if (this.disposed) return;
        const snapshot = this.controller.getCameraSnapshot();
        if (!snapshot) return;
        const key = this.fingerprint(snapshot);
        if (!this.options.enabled() || key === this.key) return;
        // Throttle rather than debounce: a continuous animation must not
        // postpone its camera projection until the animation stops.
        if (this.timer === undefined) this.timer = setTimeout(() => {
            this.timer = undefined;
            if (this.disposed || !this.options.enabled()) return;
            const current = this.controller.getCameraSnapshot();
            const currentKey = this.fingerprint(current);
            if (!current || currentKey === this.key) return;
            this.key = currentKey;
            this.options.send(current);
        }, 20);
    }

    async apply(snapshot: any) {
        if (!snapshot || this.disposed || this.options.interacting()) return;
        if (this.timer !== undefined) clearTimeout(this.timer);
        this.timer = undefined;
        this.key = this.fingerprint(snapshot);
        // Equal draws are the acknowledgement. A different viewpoint on the
        // next draw is new input/motion and must not be swallowed as an echo.
        if (this.key === this.fingerprint(this.controller.getCameraSnapshot())) return;
        await this.controller.setCameraSnapshot(snapshot, 0);
    }

    dispose() {
        this.disposed = true;
        if (this.timer !== undefined) clearTimeout(this.timer);
        this.subscription?.unsubscribe();
    }
}
