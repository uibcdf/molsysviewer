import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { UpdateTrajectory } from "molstar/lib/mol-plugin-state/actions/structure";
import {
    SetTrajectoryFrameMessage,
    SetTrajectoryPlaybackMessage,
    StepTrajectoryMessage,
} from "../../messages/viewer-messages";
import { LoadedStructure } from "../../plugin/structure";

export interface TrajectoryContext {
    getLoadedStructure: () => LoadedStructure | undefined;
    notifyTrajectoryState: () => void;
}

export interface TrajectoryState {
    frameCount: number;
    currentFrame: number;
    isPlaying: boolean;
}

export class TrajectoryHandlers {
    private playbackTimer?: ReturnType<typeof setInterval>;
    private trajectoryPoll?: ReturnType<typeof setInterval>;
    private trajectoryListeners = new Set<(state: TrajectoryState) => void>();

    constructor(private plugin: PluginContext, private context: TrajectoryContext) {}

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
    }

    getTrajectoryState(): TrajectoryState {
        const frameCount = this.getFrameCount();
        const currentFrame = this.getCurrentFrameIndex();
        const isPlaying = this.plugin.managers.animation.isAnimating;
        return { frameCount, currentFrame, isPlaying };
    }

    onTrajectoryState(cb: (state: TrajectoryState) => void): () => void {
        this.trajectoryListeners.add(cb);
        cb(this.getTrajectoryState());
        return () => this.trajectoryListeners.delete(cb);
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

    private getCurrentFrameIndex(): number {
        const trajRef = this.getTrajectoryRef();
        if (!trajRef) return 0;
        const models = this.getTrajectoryModels(trajRef);
        const first = models[0];
        const params = first?.transform.params as any;
        const idx = params?.modelIndex ?? 0;
        return typeof idx === "number" ? idx : 0;
    }
}
