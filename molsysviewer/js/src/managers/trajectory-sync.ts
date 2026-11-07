import type { BoxDisplayProjection } from "../messages/box-display";

/** Project applied host frames and their resolved cell; mirrors own no clock. */
export function syncTrajectoryFrames(controller: {
    onTrajectoryState(callback: (state: { currentFrame: number }) => void): () => void;
    boxDisplay?: { readonly projection?: BoxDisplayProjection };
}, enabled: () => boolean, send: (message: any) => void): () => void {
    let previous: string | undefined;
    return controller.onTrajectoryState(state => {
        const box = controller.boxDisplay?.projection;
        const key = JSON.stringify([state.currentFrame, box]);
        const changed = previous !== key;
        previous = key;
        if (changed && enabled()) send({ op: "set_trajectory_frame", index: state.currentFrame,
            ...(box ? { box_display: box } : {}) });
    });
}
