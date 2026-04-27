import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { MovieKeyframe } from "../../messages/viewer-messages";

export interface MovieContext {
    setTrajectoryFrame: (index: number) => Promise<void>;
    setCameraSnapshot: (snap: any, durationMs: number) => Promise<void>;
    getCameraSnapshot: () => Camera.Snapshot | undefined;
    showLayer: (tag: string) => Promise<void>;
    hideLayer: (tag: string) => Promise<void>;
    notify: ((msg: any) => void) | undefined;
}

function applyEasing(t: number, easing: string | undefined): number {
    switch (easing) {
        case "ease-in": return t * t;
        case "ease-out": return 1 - (1 - t) * (1 - t);
        case "ease-in-out": return t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t);
        default: return t;
    }
}

function lerp3(a: number[], b: number[], t: number): [number, number, number] {
    return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ];
}

function normalize3(v: number[]): [number, number, number] {
    const len = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (len < 1e-9) return [0, 1, 0];
    return [v[0] / len, v[1] / len, v[2] / len];
}

function computeVisibilityAt(keyframes: MovieKeyframe[], time_ms: number): Record<string, boolean> {
    const vis: Record<string, boolean> = {};
    for (const kf of keyframes) {
        if (kf.time_ms > time_ms) break;
        if (kf.layer_visibility) {
            Object.assign(vis, kf.layer_visibility);
        }
    }
    return vis;
}

export class MovieHandlers {
    private rafId?: number;
    private lastStructureIndex?: number;
    private lastMovieTime: number = 0;
    private lastVisibility: Record<string, boolean> = {};

    constructor(private context: MovieContext) {}

    play(keyframes: MovieKeyframe[], loop: boolean = false): void {
        this.stop();
        if (keyframes.length < 2) {
            console.warn("[MolSysViewer] play_movie: need at least 2 keyframes");
            return;
        }
        const totalDuration = keyframes[keyframes.length - 1].time_ms;
        if (totalDuration <= 0) {
            console.warn("[MolSysViewer] play_movie: total duration must be > 0");
            return;
        }
        const baseSnapshot = this.context.getCameraSnapshot();
        this.lastStructureIndex = undefined;
        this.lastMovieTime = 0;
        this.lastVisibility = {};

        const startRealTime = performance.now();

        const tick = (now: number) => {
            const elapsed = now - startRealTime;

            if (!loop && elapsed >= totalDuration) {
                this.applyState(keyframes, totalDuration, baseSnapshot);
                this.rafId = undefined;
                this.context.notify?.({ event: "movie_playback_done" });
                return;
            }

            const movieTime = loop ? elapsed % totalDuration : Math.min(elapsed, totalDuration);

            if (loop && movieTime < this.lastMovieTime) {
                // Loop restart — reset tracking so visibility gets re-applied from scratch
                this.lastVisibility = {};
                this.lastStructureIndex = undefined;
            }
            this.lastMovieTime = movieTime;

            this.applyState(keyframes, movieTime, baseSnapshot);
            this.rafId = requestAnimationFrame(tick);
        };

        this.rafId = requestAnimationFrame(tick);
    }

    stop(): void {
        if (this.rafId !== undefined) {
            cancelAnimationFrame(this.rafId);
            this.rafId = undefined;
        }
    }

    private applyState(keyframes: MovieKeyframe[], time_ms: number, baseSnapshot: Camera.Snapshot | undefined): void {
        const n = keyframes.length;

        // Find the segment enclosing time_ms
        let segEnd = n - 1;
        for (let i = 1; i < n; i++) {
            if (keyframes[i].time_ms >= time_ms) {
                segEnd = i;
                break;
            }
        }
        const segStart = Math.max(0, segEnd - 1);
        const kfA = keyframes[segStart];
        const kfB = keyframes[segEnd];

        const segDuration = kfB.time_ms - kfA.time_ms;
        const rawT = segDuration > 0 ? (time_ms - kfA.time_ms) / segDuration : 1.0;
        const t = applyEasing(Math.max(0, Math.min(1, rawT)), kfA.easing);

        // Camera
        const camA = kfA.camera;
        const camB = kfB.camera;
        if (camA && camB) {
            const pos = lerp3(camA.position, camB.position, t);
            const tgt = lerp3(camA.target, camB.target, t);
            const upRaw = lerp3(camA.up, camB.up, t);
            const up = normalize3(upRaw);
            const snap: any = baseSnapshot ? { ...baseSnapshot, position: pos, target: tgt, up } : { position: pos, target: tgt, up };
            void this.context.setCameraSnapshot(snap, 0);
        } else if (camA) {
            const snap: any = baseSnapshot
                ? { ...baseSnapshot, position: camA.position, target: camA.target, up: camA.up }
                : { position: camA.position, target: camA.target, up: camA.up };
            void this.context.setCameraSnapshot(snap, 0);
        }

        // Structure index
        const idxA = kfA.structure_index;
        const idxB = kfB.structure_index;
        if (idxA !== undefined && idxB !== undefined) {
            const idx = Math.round(idxA + (idxB - idxA) * t);
            if (idx !== this.lastStructureIndex) {
                this.lastStructureIndex = idx;
                void this.context.setTrajectoryFrame(idx);
            }
        }

        // Layer visibility — accumulate all keyframes up to time_ms
        const targetVis = computeVisibilityAt(keyframes, time_ms);
        for (const [tag, visible] of Object.entries(targetVis)) {
            if (this.lastVisibility[tag] !== visible) {
                this.lastVisibility[tag] = visible;
                if (visible) {
                    void this.context.showLayer(tag);
                } else {
                    void this.context.hideLayer(tag);
                }
            }
        }
    }
}
