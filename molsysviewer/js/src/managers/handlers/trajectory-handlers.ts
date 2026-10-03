import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { UpdateTrajectory } from "molstar/lib/mol-plugin-state/actions/structure";
import {
    SetTrajectoryFrameMessage,
    SetTrajectoryPlaybackMessage,
    StepTrajectoryMessage,
    PartialCoordinatesUpdateMessage,
} from "../../messages/viewer-messages";
import { LoadedStructure, replaceMolSysTrajectory } from "../../plugin/structure";
import { ArrayTrajectory, Model } from "molstar/lib/mol-model/structure";
import { Task } from "molstar/lib/mol-task";
import { UUID } from "molstar/lib/mol-util/uuid";
import { CustomProperties } from "molstar/lib/mol-model/custom-property";

export interface TrajectoryContext {
    getLoadedStructure: () => LoadedStructure | undefined;
    notifyTrajectoryState: () => void;
    afterFrameApplied?: () => Promise<void>;
    /** Called when playback stops; receives the final frame index. */
    onPlaybackStopped?: (frame: number) => void;
    notify?: (msg: any) => void;
}

export interface TrajectoryState {
    frameCount: number;
    currentFrame: number;
    isPlaying: boolean;
    hasTrajectory: boolean;
    expectedFrameCount?: number;
}

/** Playback modes. Python's public API says "ping-pong"; the frontend has always
 * called it "palindrome", and the mismatch meant the mode was silently dropped. */
export type PlaybackMode = "loop" | "palindrome" | "once";

export function normalizePlaybackMode(mode: string | undefined | null): PlaybackMode {
    if (mode === "once") return "once";
    if (mode === "palindrome" || mode === "ping-pong") return "palindrome";
    return "loop";
}

/**
 * Next frame and travel delta for one playback tick.
 *
 * - `loop` wraps around, which is what Mol*'s `advance` did on its own.
 * - `once` clamps to the end frame and reports that playback should stop.
 * - `palindrome` reverses direction when it reaches either end.
 */
export function nextPlaybackStep(
    current: number,
    delta: number,
    frameCount: number,
    mode: PlaybackMode,
): { index: number; delta: number; stop: boolean } {
    if (frameCount < 1) return { index: 0, delta, stop: true };
    const raw = current + delta;
    if (raw >= 0 && raw < frameCount) return { index: raw, delta, stop: false };

    if (mode === "once") {
        return { index: delta > 0 ? frameCount - 1 : 0, delta, stop: true };
    }
    if (mode === "palindrome") {
        const bounced = -delta;
        const index = Math.min(frameCount - 1, Math.max(0, current + bounced));
        return { index, delta: bounced, stop: false };
    }
    const wrapped = ((raw % frameCount) + frameCount) % frameCount;
    return { index: wrapped, delta, stop: false };
}

export class TrajectoryHandlers {
    private readonly pendingFrames = new Set<Promise<void>>();
    private playbackTimer?: ReturnType<typeof setInterval>;
    private trajectoryPoll?: ReturnType<typeof setInterval>;
    private trajectoryListeners = new Set<(state: TrajectoryState) => void>();
    private expectedFrameCount?: number;

    constructor(private plugin: PluginContext, private context: TrajectoryContext) {}

    async partialCoordinatesUpdate(msg: PartialCoordinatesUpdateMessage) {
        const loaded = this.context.getLoadedStructure();
        const ref = loaded ? StateObjectRef.resolveRef(loaded.trajectory) : undefined;
        const trajectory = ref ? this.plugin.state.data.cells.get(ref)?.obj?.data : undefined;
        if (!loaded || !trajectory) throw new Error("No trajectory loaded for coordinate edit.");
        if (msg.coordinate_unit !== "angstrom") throw new Error("Coordinate edits require explicit angstrom units.");
        const count = trajectory.frameCount;
        if (!Array.isArray(msg.structure_indices) || new Set(msg.structure_indices).size !== msg.structure_indices.length
            || msg.structure_indices.some(i => !Number.isInteger(i) || i < 0 || i >= count)
            || msg.coordinates.length !== msg.structure_indices.length
            || msg.coordinates.some(frame => frame.length !== msg.atom_indices.length
                || frame.some(xyz => xyz.length !== 3 || xyz.some(value => !Number.isFinite(value))))) {
            throw new Error("Invalid coordinate edit structures or dimensions.");
        }
        const replacements = new Map(msg.structure_indices.map((frame, index) => [frame, msg.coordinates[index]]));
        const models = await this.plugin.runTask(Task.create("Revise trajectory coordinates", async ctx => {
            const frames: Model[] = [];
            for (let index = 0; index < count; index++) {
                const original = await Task.resolveInContext(trajectory.getFrameAtIndex(index), ctx) as Model;
                const coordinates = replacements.get(index);
                if (!coordinates) { frames.push(original); continue; }
                const inverse = Model.getInvertedAtomSourceIndex(original).invertedIndex;
                if (msg.atom_indices.some(atom => !Number.isInteger(atom) || atom < 0 || atom >= inverse.length)) {
                    throw new Error("Invalid coordinate edit atom indices.");
                }
                const atomic = original.atomicConformation;
                const x = Float32Array.from(atomic.x), y = Float32Array.from(atomic.y), z = Float32Array.from(atomic.z);
                msg.atom_indices.forEach((source, offset) => {
                    const atom = inverse[source], xyz = coordinates[offset];
                    x[atom] = xyz[0]; y[atom] = xyz[1]; z[atom] = xyz[2];
                });
                // Fresh model/conformation identities make Mol* rebuild dependent
                // units and their spatial caches. Other frames retain their arrays.
                const revised: Model = { ...original, id: UUID.create22(),
                    atomicConformation: { ...atomic, id: UUID.create22(), x, y, z },
                    customProperties: new CustomProperties(),
                    _staticPropertyData: { ...original._staticPropertyData },
                    _dynamicPropertyData: Object.create(null) };
                Model.TrajectoryInfo.set(revised, { index, size: count });
                frames.push(revised);
            }
            return frames;
        }));
        await replaceMolSysTrajectory(this.plugin, loaded, new ArrayTrajectory(models));
        this.updateTrajectoryState();
        if (msg.transaction_id !== undefined) this.context.notify?.({
            event: "trajectory_frame_rendered", transaction_id: msg.transaction_id,
        });
    }

    async stepTrajectory(msg: StepTrajectoryMessage | number) {
        const by = typeof msg === 'number' ? msg : (msg.by ?? 1);
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return;
        await PluginCommands.State.ApplyAction(this.plugin, {
            state: this.plugin.state.data,
            action: UpdateTrajectory.create({ action: "advance", by }),
        });
        this.updateTrajectoryState();
    }

    async setTrajectoryFrame(msg: SetTrajectoryFrameMessage | number) {
        const pending = this.applyTrajectoryFrame(msg);
        this.pendingFrames.add(pending);
        try { await pending; } finally { this.pendingFrames.delete(pending); }
    }

    private async applyTrajectoryFrame(msg: SetTrajectoryFrameMessage | number) {
        const index = typeof msg === 'number' ? msg : (msg.index ?? 0);
        const frameCount = this.getFrameCount();
        if (frameCount < 1) return;
        const clamped = Math.max(0, Math.min(frameCount - 1, Math.floor(index)));
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return;
        const models = this.getTrajectoryModels(trajRef);
        if (!models.length) return;
        const update = this.plugin.state.data.build();
        for (const m of models) {
            update.to(m).update({ modelIndex: clamped });
        }
        await this.plugin.runTask(this.plugin.state.data.updateTree(update));
        await this.context.afterFrameApplied?.();
        this.updateTrajectoryState();
    }

    async setTrajectoryPlayback(msg: SetTrajectoryPlaybackMessage) {
        const action = msg.action ?? "stop";
        const fps = msg.fps ?? 30;
        const step = msg.step ?? 1;
        const mode = msg.mode ?? "loop";
        const direction = msg.direction ?? "forward";
        if (action === "play") {
            await this.playTrajectory({ fps, mode, direction, step });
        } else {
            await this.stopTrajectoryPlayback();
        }
    }

    async playTrajectory(options: { fps?: number; mode?: PlaybackMode; direction?: "forward" | "backward"; step?: number } = {}) {
        const frameCount = this.getFrameCount();
        if (frameCount < 2) {
            console.warn("[MolSysViewer] playTrajectory ignored: trajectory has less than 2 frames");
            return;
        }

        const fps = options.fps ?? 30;
        const step = Math.max(1, Math.floor(options.step ?? 1));
        const direction = options.direction ?? "forward";
        const mode = normalizePlaybackMode(options.mode);

        // Stop any existing animation/timer first
        await this.stopTrajectoryPlayback();

        const intervalMs = Math.max(1, Math.floor(1000 / Math.max(fps, 1)));
        let delta = direction === "backward" ? -step : step;

        // `mode` used to be accepted and then ignored: playback always advanced
        // with Mol*'s wrap-around, so "loop" worked by accident while "once"
        // never stopped and "palindrome" never bounced.
        this.playbackTimer = setInterval(() => {
            const next = nextPlaybackStep(this.getCurrentFrameIndex(), delta, frameCount, mode);
            delta = next.delta;
            void this.setTrajectoryFrame(next.index);
            if (next.stop) void this.stopTrajectoryPlayback();
        }, intervalMs);

        if (this.trajectoryPoll) clearInterval(this.trajectoryPoll);
        this.trajectoryPoll = setInterval(() => {
            this.context.notifyTrajectoryState();
            this.notifyPlaybackFrameChanged(true);
        }, 200);
        this.updateTrajectoryState();
    }

    async stopTrajectoryPlayback() {
        const wasPlaying = !!this.playbackTimer;
        this.plugin.managers.animation.stop();
        if (this.playbackTimer) {
            clearInterval(this.playbackTimer);
            this.playbackTimer = void 0;
        }
        if (this.trajectoryPoll) {
            clearInterval(this.trajectoryPoll);
            this.trajectoryPoll = void 0;
        }
        await Promise.all(Array.from(this.pendingFrames));
        await this.context.afterFrameApplied?.();
        this.updateTrajectoryState();
        if (wasPlaying) {
            this.context.onPlaybackStopped?.(this.getCurrentFrameIndex());
        }
    }

    getTrajectoryState(): TrajectoryState {
        const hasTrajectory = !!this.getTrajectoryRef();
        let frameCount = this.getFrameCount();
        if (!hasTrajectory && (!frameCount || frameCount < 1) && this.expectedFrameCount !== undefined) {
            frameCount = this.expectedFrameCount;
        }
        const currentFrame = this.getCurrentFrameIndex();
        // Check our custom timer or Mol*'s built-in manager as a fallback
        const isPlaying = !!this.playbackTimer || this.plugin.managers.animation.isAnimating;
        return { frameCount, currentFrame, isPlaying, hasTrajectory, expectedFrameCount: this.expectedFrameCount };
    }

    onTrajectoryState(cb: (state: TrajectoryState) => void, opts?: { immediate?: boolean }): () => void {
        this.trajectoryListeners.add(cb);
        if (opts?.immediate ?? true) cb(this.getTrajectoryState());
        return () => this.trajectoryListeners.delete(cb);
    }

    setExpectedFrameCount(n: number | undefined) {
        this.expectedFrameCount = n;
        // Notify UI listeners immediately so the controls can update without waiting
        // for the trajectory to finish loading in Mol*.
        this.notifyListeners();
    }

    notifyListeners() {
        const state = this.getTrajectoryState();
        for (const cb of this.trajectoryListeners) cb(state);
    }

    private notifyPlaybackFrameChanged(isPlaying: boolean) {
        this.context.notify?.({
            event: "trajectory_frame_changed",
            frame: this.getCurrentFrameIndex(),
            is_playing: isPlaying,
        });
    }

    private updateTrajectoryState() {
        this.context.notifyTrajectoryState();
        this.notifyListeners();
    }

    private getTrajectoryRef(): StateObjectRef | undefined {
        return this.context.getLoadedStructure()?.trajectory;
    }

    private getTrajectoryModels(trajRef: StateObjectRef) {
        const all = this.plugin.state.data.selectQ(q => q.ofTransformer(StateTransforms.Model.ModelFromTrajectory));
        return all.filter(cell => cell.transform.parent === trajRef);
    }

    private getFrameCount(): number {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return 0;
        const resolvedTrajRef = StateObjectRef.resolveRef(trajRef);
        const cell = resolvedTrajRef ? this.plugin.state.data.cells.get(resolvedTrajRef) : undefined;
        const traj = cell?.obj?.data as any;
        return traj?.frameCount ?? 0;
    }

    getCurrentFrameIndex(): number {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return 0;
        const models = this.getTrajectoryModels(trajRef);
        const first = models[0];
        const params = first?.transform.params as any;
        const idx = params?.modelIndex ?? 0;
        return typeof idx === "number" ? idx : 0;
    }
}
