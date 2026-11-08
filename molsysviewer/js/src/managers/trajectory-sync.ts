import type { BoxDisplayProjection } from "../messages/box-display";
import type { PlaybackSnapshot } from "../messages/visual-state-snapshot";

/** Project applied host frames and their resolved cell; mirrors own no clock. */
export function syncTrajectoryFrames(controller: {
    onTrajectoryState(callback: (state: { currentFrame: number }) => void): () => void;
    boxDisplay?: { readonly projection?: BoxDisplayProjection };
    trajectory?: { getPlaybackSnapshot(): PlaybackSnapshot; readonly feedbackRevision?: number };
}, enabled: () => boolean, send: (message: any) => void): () => void {
    let previous: string | undefined;
    return controller.onTrajectoryState(state => {
        const box = controller.boxDisplay?.projection;
        const playback = controller.trajectory?.getPlaybackSnapshot();
        const revision = controller.trajectory?.feedbackRevision;
        const key = JSON.stringify([state.currentFrame, box, playback, revision]);
        const changed = previous !== key;
        previous = key;
        if (changed && enabled()) send({ op: "set_trajectory_frame", index: state.currentFrame,
            ...(revision === undefined ? {} : { navigation_revision: revision }),
            ...(box ? { box_display: box } : {}), ...(playback ? { playback_projection: playback } : {}) });
    });
}
