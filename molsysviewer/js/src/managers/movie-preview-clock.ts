import { compileMovieTimeline } from "./movie-timeline";

type PreviewRequest = { id: string; recipe?: unknown; start_time_ms?: number; loop?: boolean };
type Clock = {
    id: string;
    timeline: ReturnType<typeof compileMovieTimeline>;
    origin: number;
    start: number;
    loop: boolean;
};

/** One clock per primary renderer. The next sample is selected at a completed draw. */
export class MoviePreviewClock {
    private current?: Clock;

    prepare(request: PreviewRequest, now = performance.now()) {
        if (!request || typeof request.id !== "string" || !request.id) throw new Error("Invalid Movie preview ID.");
        if (request.recipe !== undefined) {
            if (this.current?.id === request.id) throw new Error("Movie preview was already started.");
            const timeline = compileMovieTimeline(request.recipe, { trackedVisibility: true });
            const start = request.start_time_ms;
            if (typeof start !== "number" || !Number.isFinite(start) || start < 0 || start > timeline.duration_ms
                || typeof request.loop !== "boolean") {
                throw new Error("Invalid Movie preview start.");
            }
            this.current = { id: request.id, timeline, origin: now, start, loop: request.loop };
        }
        const clock = this.current;
        if (clock?.id !== request.id) throw new Error("Movie preview is no longer current.");
        return (drawnAt = performance.now()) => {
            if (clock !== this.current) throw new Error("Movie preview was replaced before its draw.");
            const duration = clock.timeline.duration_ms;
            const elapsed = clock.start + Math.max(0, drawnAt - clock.origin);
            const at = clock.loop ? elapsed % duration : Math.min(elapsed, duration);
            return clock.timeline.evaluate(at);
        };
    }

    release(id?: string): void {
        if (id === undefined || this.current?.id === id) this.current = undefined;
    }
}
