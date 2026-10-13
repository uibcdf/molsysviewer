/** Project applied host frames; popup endpoints never run a competing clock. */
export function syncTrajectoryFrames(controller: {
    onTrajectoryState(callback: (state: { currentFrame: number }) => void): () => void;
}, enabled: () => boolean, send: (message: any) => void): () => void {
    let previous: number | undefined;
    return controller.onTrajectoryState(state => {
        const changed = previous !== state.currentFrame;
        previous = state.currentFrame;
        if (changed && enabled()) send({ op: "set_trajectory_frame", index: state.currentFrame });
    });
}
