import { overlayDescriptor, MovieOverlayError, type MovieOverlaySnapshot, type OverlayId } from "../ui/movie-overlay-composition";

type ImageController = {
    getImageDataUri(options: { width: number; height: number; transparent: boolean; preset: string; sampleLevel: number; signal: AbortSignal; movieOverlays?: MovieOverlaySnapshot }): Promise<unknown>;
    readMovieExportOverlays?(): string[];
    snapshotMovieOverlays?(width: number, height: number, required: OverlayId[]): MovieOverlaySnapshot;
};

// A cancelled request cannot abort Mol*'s screenshot task midway through GPU
// work. Keep that helper reserved until it really settles; a replacement job
// must not race its canvas/settings or accumulate waiting screenshot tasks.
const active = new WeakSet<object>();

export async function captureMovieFrame(controller: ImageController, value: any, timeout: number,
    signal?: AbortSignal): Promise<Record<string, unknown>> {
    if (!value || typeof value !== "object" || typeof value.job_id !== "string" || !value.job_id
        || !Number.isSafeInteger(value.frame_index) || value.frame_index < 0
        || !Number.isInteger(value.width) || !Number.isInteger(value.height)
        || value.width < 16 || value.height < 16 || value.width > 8192 || value.height > 8192
        || value.width * value.height > 2 ** 24 || typeof value.include_overlays !== "boolean"
        || !Number.isInteger(value.sample_level) || value.sample_level < 0 || value.sample_level > 5) {
        throw new Error("Invalid Movie frame capture.");
    }
    if (!controller.readMovieExportOverlays) throw new Error("Movie overlay inspection is unavailable.");
    const version = value.overlay_capture_version;
    if (version !== undefined && (version !== 1 || !value.include_overlays || !controller.snapshotMovieOverlays
        || !Array.isArray(value.required_overlays) || !value.required_overlays.length || value.required_overlays.some((row: any) =>
            !row || !["trajectory_plot", "colour_legend"].includes(row.kind) || typeof row.tag !== "string" || !row.tag))) {
        throw new Error("Unsupported Movie overlay capture contract.");
    }
    const overlays = version === 1 ? controller.snapshotMovieOverlays!(value.width, value.height, value.required_overlays) : undefined;
    const originalOverlays = overlays ? JSON.stringify(overlays) : undefined;
    if (version === undefined && value.include_overlays && controller.readMovieExportOverlays().length) {
        throw new Error("Visible DOM overlays require explicit exclusion from Movie export.");
    }
    if (active.has(controller)) throw new Error("A previous Movie screenshot is still retiring.");
    if (signal?.aborted) throw new DOMException("Movie frame cancelled.", "AbortError");
    active.add(controller);
    const owned = new AbortController();
    const image = Promise.resolve().then(() => controller.getImageDataUri({
        width: value.width, height: value.height, transparent: false, preset: "current", sampleLevel: value.sample_level, signal: owned.signal,
        ...(overlays ? { movieOverlays: overlays } : {}),
    }));
    void image.then(() => active.delete(controller), () => active.delete(controller));
    let timer: ReturnType<typeof setTimeout> | undefined;
    let abort: (() => void) | undefined;
    const deadline = new Promise<never>((_, reject) => {
        timer = setTimeout(() => { owned.abort(); reject(new Error("Movie screenshot timed out.")); }, timeout);
        abort = () => { owned.abort(); reject(new DOMException("Movie frame cancelled.", "AbortError")); };
        signal?.addEventListener("abort", abort, { once: true });
    });
    try {
        const result = await Promise.race([image, deadline]);
        if (typeof result !== "string" || !result.startsWith("data:image/png;base64,")) {
            throw new Error("Movie screenshot failed to return PNG content.");
        }
        if (overlays && JSON.stringify(controller.snapshotMovieOverlays!(value.width, value.height, value.required_overlays)) !== originalOverlays) {
            throw new MovieOverlayError("MovieOverlayChanged", "Movie overlay content or layout changed during screenshot.");
        }
        return { job_id: value.job_id, frame_index: value.frame_index, width: value.width, height: value.height,
            include_overlays: value.include_overlays, sample_level: value.sample_level, data_uri: result,
            ...(overlays ? { overlay_capture_version: 1, required_overlays: value.required_overlays, composition: overlayDescriptor(overlays) } : {}) };
    } finally {
        if (timer !== undefined) clearTimeout(timer);
        if (abort) signal?.removeEventListener("abort", abort);
    }
}
