import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { MovieKeyframe } from "../../messages/viewer-messages";

export interface MovieContext {
    setTrajectoryFrame: (index: number) => Promise<void>;
    setCameraSnapshot: (snap: any, durationMs: number) => Promise<void>;
    getCameraSnapshot: () => Camera.Snapshot | undefined;
    getImageDataUri: (options?: { width?: number; height?: number }) => Promise<string | undefined>;
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

function findSegment(keyframes: MovieKeyframe[], time_ms: number): [number, number] {
    const n = keyframes.length;
    let segEnd = n - 1;
    for (let i = 1; i < n; i++) {
        if (keyframes[i].time_ms >= time_ms) { segEnd = i; break; }
    }
    return [Math.max(0, segEnd - 1), segEnd];
}

function computeT(kfA: MovieKeyframe, kfB: MovieKeyframe, time_ms: number): number {
    const segDuration = kfB.time_ms - kfA.time_ms;
    const rawT = segDuration > 0 ? (time_ms - kfA.time_ms) / segDuration : 1.0;
    return applyEasing(Math.max(0, Math.min(1, rawT)), kfA.easing);
}

export class MovieHandlers {
    private rafId?: number;
    private lastStructureIndex?: number;
    private lastMovieTime: number = 0;
    private lastVisibility: Record<string, boolean> = {};

    constructor(private context: MovieContext) {}

    // ── Browser playback ──────────────────────────────────────────────────

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

    // ── Frame export ──────────────────────────────────────────────────────

    async exportFrames(
        keyframes: MovieKeyframe[],
        fps: number,
        totalFrames: number,
        widthPx: number | undefined,
        heightPx: number | undefined,
    ): Promise<void> {
        if (keyframes.length < 2 || totalFrames < 1) {
            console.warn("[MolSysViewer] exportFrames: need ≥ 2 keyframes and ≥ 1 frame");
            return;
        }
        const baseSnapshot = this.context.getCameraSnapshot();
        const exportVis: Record<string, boolean> = {};
        let exportStructureIndex: number | undefined;

        for (let i = 0; i < totalFrames; i++) {
            const time_ms = Math.min((i / fps) * 1000, keyframes[keyframes.length - 1].time_ms);
            await this.applyStateForExport(keyframes, time_ms, baseSnapshot, exportVis, exportStructureIndex);
            const dataUri = await this.context.getImageDataUri({ width: widthPx, height: heightPx });
            this.context.notify?.({
                event: "movie_frame",
                frame_index: i,
                total_frames: totalFrames,
                data_uri: dataUri ?? "",
            });
        }

        this.context.notify?.({ event: "movie_export_done", total_frames: totalFrames });
    }

    // ── Internal ──────────────────────────────────────────────────────────

    private applyState(keyframes: MovieKeyframe[], time_ms: number, baseSnapshot: Camera.Snapshot | undefined): void {
        const [segStart, segEnd] = findSegment(keyframes, time_ms);
        const kfA = keyframes[segStart];
        const kfB = keyframes[segEnd];
        const t = computeT(kfA, kfB, time_ms);

        const camA = kfA.camera, camB = kfB.camera;
        if (camA && camB) {
            const snap: any = baseSnapshot
                ? { ...baseSnapshot, position: lerp3(camA.position, camB.position, t), target: lerp3(camA.target, camB.target, t), up: normalize3(lerp3(camA.up, camB.up, t)) }
                : { position: lerp3(camA.position, camB.position, t), target: lerp3(camA.target, camB.target, t), up: normalize3(lerp3(camA.up, camB.up, t)) };
            void this.context.setCameraSnapshot(snap, 0);
        } else if (camA) {
            const snap: any = baseSnapshot
                ? { ...baseSnapshot, position: camA.position, target: camA.target, up: camA.up }
                : { position: camA.position, target: camA.target, up: camA.up };
            void this.context.setCameraSnapshot(snap, 0);
        }

        const idxA = kfA.structure_index, idxB = kfB.structure_index;
        if (idxA !== undefined && idxB !== undefined) {
            const idx = Math.round(idxA + (idxB - idxA) * t);
            if (idx !== this.lastStructureIndex) {
                this.lastStructureIndex = idx;
                void this.context.setTrajectoryFrame(idx);
            }
        }

        const targetVis = computeVisibilityAt(keyframes, time_ms);
        for (const [tag, visible] of Object.entries(targetVis)) {
            if (this.lastVisibility[tag] !== visible) {
                this.lastVisibility[tag] = visible;
                if (visible) void this.context.showLayer(tag);
                else void this.context.hideLayer(tag);
            }
        }
    }

    private async applyStateForExport(
        keyframes: MovieKeyframe[],
        time_ms: number,
        baseSnapshot: Camera.Snapshot | undefined,
        exportVis: Record<string, boolean>,
        _lastStructureIndex: number | undefined,
    ): Promise<void> {
        const [segStart, segEnd] = findSegment(keyframes, time_ms);
        const kfA = keyframes[segStart];
        const kfB = keyframes[segEnd];
        const t = computeT(kfA, kfB, time_ms);

        const camA = kfA.camera, camB = kfB.camera;
        if (camA && camB) {
            const snap: any = baseSnapshot
                ? { ...baseSnapshot, position: lerp3(camA.position, camB.position, t), target: lerp3(camA.target, camB.target, t), up: normalize3(lerp3(camA.up, camB.up, t)) }
                : { position: lerp3(camA.position, camB.position, t), target: lerp3(camA.target, camB.target, t), up: normalize3(lerp3(camA.up, camB.up, t)) };
            await this.context.setCameraSnapshot(snap, 0);
        } else if (camA) {
            const snap: any = baseSnapshot
                ? { ...baseSnapshot, position: camA.position, target: camA.target, up: camA.up }
                : { position: camA.position, target: camA.target, up: camA.up };
            await this.context.setCameraSnapshot(snap, 0);
        }

        const idxA = kfA.structure_index, idxB = kfB.structure_index;
        if (idxA !== undefined && idxB !== undefined) {
            const idx = Math.round(idxA + (idxB - idxA) * t);
            await this.context.setTrajectoryFrame(idx);
        }

        const targetVis = computeVisibilityAt(keyframes, time_ms);
        for (const [tag, visible] of Object.entries(targetVis)) {
            if (exportVis[tag] !== visible) {
                exportVis[tag] = visible;
                if (visible) await this.context.showLayer(tag);
                else await this.context.hideLayer(tag);
            }
        }
    }
}
