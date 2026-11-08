import type { Camera } from "molstar/lib/mol-canvas3d/camera";

/** Detached temporal metadata from the same completed native draw. */
export type PlaybackSnapshot = {
    fps: number;
    step_size: number;
    mode: "loop" | "once" | "ping-pong";
    direction: "forward" | "backward";
    playing: boolean;
};

export type MovingVisualSnapshot = {
    snapshot: Camera.Snapshot;
    structure_index: number;
    playback: PlaybackSnapshot;
    box_structure_index?: number;
};
