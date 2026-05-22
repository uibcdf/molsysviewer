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
import { LoadedStructure } from "../../plugin/structure";

export interface TrajectoryContext {
    getLoadedStructure: () => LoadedStructure | undefined;
    notifyTrajectoryState: () => void;
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

export class TrajectoryHandlers {
    private playbackTimer?: ReturnType<typeof setInterval>;
    private trajectoryPoll?: ReturnType<typeof setInterval>;
    private trajectoryListeners = new Set<(state: TrajectoryState) => void>();
    private expectedFrameCount?: number;

    constructor(private plugin: PluginContext, private context: TrajectoryContext) {}

    async partialCoordinatesUpdate(msg: PartialCoordinatesUpdateMessage) {
        const loaded = this.context.getLoadedStructure();
        if (!loaded || !loaded.structure) {
            console.warn("[TrajectoryHandlers] partialCoordinatesUpdate ignored: no structure loaded");
            return;
        }
        const cell = this.plugin.state.data.cells.get(loaded.structure);
        if (!cell || !cell.obj) {
            console.warn("[TrajectoryHandlers] partialCoordinatesUpdate ignored: structure node not found");
            return;
        }
        const structure = cell.obj.data;
        if (!structure || !structure.models) {
            console.warn("[TrajectoryHandlers] partialCoordinatesUpdate ignored: structure data not found");
            return;
        }

        let updated = false;
        for (const model of structure.models) {
            const atomicConformation = model.atomicConformation;
            if (!atomicConformation) continue;
            const { x, y, z } = atomicConformation;
            for (let i = 0; i < msg.atom_indices.length; i++) {
                const atomIdx = msg.atom_indices[i];
                const coords = msg.coordinates[i];
                if (coords && atomIdx >= 0 && atomIdx < x.length) {
                    x[atomIdx] = coords[0];
                    y[atomIdx] = coords[1];
                    z[atomIdx] = coords[2];
                    updated = true;
                }
            }
        }

        if (updated) {
            const currentId = (structure as any).conformation?.id ?? "0";
            const newId = typeof currentId === "number" ? currentId + 1 : `${currentId}_upd`;
            if (structure.conformation) {
                (structure as any).conformation.id = newId;
            }
            
            const update = this.plugin.state.data.build();
            update.to(loaded.structure);
            await this.plugin.runTask(this.plugin.state.data.updateTree(update));
        }

        if (msg.transaction_id !== undefined && this.context.notify) {
            this.context.notify({
                event: "trajectory_frame_rendered",
                transaction_id: msg.transaction_id,
            });
        }
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

    async playTrajectory(options: { fps?: number; mode?: "loop" | "palindrome" | "once"; direction?: "forward" | "backward"; step?: number } = {}) {
        const frameCount = this.getFrameCount();
        if (frameCount < 2) {
            console.warn("[MolSysViewer] playTrajectory ignored: trajectory has less than 2 frames");
            return;
        }

        const fps = options.fps ?? 30;
        const step = Math.max(1, Math.floor(options.step ?? 1));
        const direction = options.direction ?? "forward";

        // Stop any existing animation/timer first
        await this.stopTrajectoryPlayback();

        const intervalMs = Math.max(1, Math.floor(1000 / Math.max(fps, 1)));
        const delta = direction === "backward" ? -step : step;

        this.playbackTimer = setInterval(() => {
            void this.stepTrajectory(delta);
        }, intervalMs);

        if (this.trajectoryPoll) clearInterval(this.trajectoryPoll);
        this.trajectoryPoll = setInterval(() => this.context.notifyTrajectoryState(), 200);
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
        const cell = this.plugin.state.data.cells.get(trajRef);
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
