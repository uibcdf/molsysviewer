export interface ProjectedTrajectoryState {
    frame: number;
    frameCount: number;
    isPlaying: boolean;
    fps: number;
    step: number;
    mode: "loop" | "once" | "ping-pong";
    direction: "forward" | "backward";
}

export type ProjectedTrajectoryIntent =
    | { action: "set_trajectory_frame"; index: number }
    | { action: "step_trajectory"; by: number }
    | {
        action: "set_trajectory_playback";
        playback_action: "play" | "stop";
        fps?: number;
        step?: number;
        mode?: ProjectedTrajectoryState["mode"];
        direction?: ProjectedTrajectoryState["direction"];
    };

const button = (label: string, title: string): HTMLButtonElement => {
    const element = document.createElement("button");
    element.type = "button";
    element.textContent = label;
    element.title = title;
    Object.assign(element.style, {
        width: "30px", height: "28px", padding: "0", borderRadius: "6px",
        border: "1px solid rgba(255,255,255,.18)", background: "rgba(18,18,22,.9)",
        color: "#f5f7fa", font: "13px/1 system-ui,sans-serif", cursor: "default",
    });
    return element;
};

/**
 * Controller-free trajectory scrubber driven by an authoritative projection.
 *
 * The component knows neither Mol* nor the transport. Integrated, browser and
 * Qt hosts can map its semantic intents to their own session port.
 */
export class ProjectedTrajectoryControls {
    readonly root: HTMLDivElement;
    private readonly previous = button("−", "Previous frame");
    private readonly playPause = button("▶", "Play trajectory");
    private readonly next = button("+", "Next frame");
    private readonly slider = document.createElement("input");
    private readonly label = document.createElement("span");
    private state: ProjectedTrajectoryState = {
        frame: 0,
        frameCount: 0,
        isPlaying: false,
        fps: 30,
        step: 1,
        mode: "loop",
        direction: "forward",
    };

    constructor(
        host: HTMLElement,
        private readonly emit: (intent: ProjectedTrajectoryIntent) => void,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-trajectory-controls", "true");
        Object.assign(this.root.style, {
            position: "absolute", left: "50%", bottom: "14px", transform: "translateX(-50%)",
            zIndex: "3", display: "none", alignItems: "center", gap: "6px", padding: "6px",
            borderRadius: "8px", border: "1px solid rgba(255,255,255,.12)",
            background: "rgba(8,11,16,.78)", boxShadow: "0 4px 16px rgba(0,0,0,.3)",
            pointerEvents: "auto",
        });

        this.previous.setAttribute("data-molsysviewer-trajectory-step", "previous");
        this.playPause.setAttribute("data-molsysviewer-trajectory-playback", "play");
        this.next.setAttribute("data-molsysviewer-trajectory-step", "next");
        this.slider.type = "range";
        this.slider.min = "0";
        this.slider.max = "0";
        this.slider.value = "0";
        this.slider.setAttribute("data-molsysviewer-trajectory-frame", "true");
        Object.assign(this.slider.style, { width: "180px", accentColor: "#e6edf3" });
        this.label.setAttribute("data-molsysviewer-trajectory-label", "true");
        Object.assign(this.label.style, {
            minWidth: "62px", color: "#f5f7fa", font: "11px/1.2 system-ui,sans-serif",
            textAlign: "center",
        });

        this.previous.addEventListener("click", () => this.emit({ action: "step_trajectory", by: -this.state.step }));
        this.next.addEventListener("click", () => this.emit({ action: "step_trajectory", by: this.state.step }));
        this.playPause.addEventListener("click", () => {
            if (this.state.isPlaying) {
                this.emit({ action: "set_trajectory_playback", playback_action: "stop" });
            } else {
                this.emit({
                    action: "set_trajectory_playback",
                    playback_action: "play",
                    fps: this.state.fps,
                    step: this.state.step,
                    mode: this.state.mode,
                    direction: this.state.direction,
                });
            }
        });
        this.slider.addEventListener("input", () => this.renderLabel(Number(this.slider.value)));
        this.slider.addEventListener("change", () => {
            const index = Number(this.slider.value);
            if (Number.isInteger(index)) this.emit({ action: "set_trajectory_frame", index });
        });

        this.root.append(this.previous, this.playPause, this.next, this.slider, this.label);
        host.appendChild(this.root);
        this.render();
    }

    apply(value: Record<string, unknown>): void {
        const frameCount = nonNegativeInteger(value.frame_count, this.state.frameCount);
        const maximum = Math.max(0, frameCount - 1);
        this.state = {
            frame: Math.min(nonNegativeInteger(value.frame, this.state.frame), maximum),
            frameCount,
            isPlaying: value.is_playing === true,
            fps: positiveInteger(value.fps, this.state.fps),
            step: positiveInteger(value.step, this.state.step),
            mode: value.mode === "once" || value.mode === "ping-pong" ? value.mode : "loop",
            direction: value.direction === "backward" ? "backward" : "forward",
        };
        this.render();
    }

    dispose(): void {
        this.root.remove();
    }

    get currentFrame(): number {
        return this.state.frame;
    }

    private render(): void {
        const enabled = this.state.frameCount > 1;
        this.root.style.display = enabled ? "flex" : "none";
        this.slider.max = String(Math.max(0, this.state.frameCount - 1));
        this.slider.value = String(this.state.frame);
        for (const control of [this.previous, this.playPause, this.next, this.slider]) control.disabled = !enabled;
        this.playPause.textContent = this.state.isPlaying ? "⏸" : "▶";
        this.playPause.title = this.state.isPlaying ? "Pause trajectory" : "Play trajectory";
        this.playPause.setAttribute("data-molsysviewer-trajectory-playback", this.state.isPlaying ? "stop" : "play");
        this.renderLabel(this.state.frame);
    }

    private renderLabel(frame: number): void {
        this.label.textContent = this.state.frameCount > 0
            ? `${Math.min(frame, this.state.frameCount - 1) + 1} / ${this.state.frameCount}`
            : "0 / 0";
    }
}

const nonNegativeInteger = (value: unknown, fallback: number): number =>
    typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : fallback;

const positiveInteger = (value: unknown, fallback: number): number =>
    typeof value === "number" && Number.isInteger(value) && value > 0 ? value : fallback;
