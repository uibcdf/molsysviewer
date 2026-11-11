import type { MolSysViewerController } from "../managers/viewer-controller";
import { readCanvasDraw } from "../managers/canvas-draw";
import type { MovingVisualSnapshot } from "./visual-state-snapshot";

type RequestController = Pick<MolSysViewerController, "getCameraSnapshot" | "getImageDataUri" | "onTrajectoryState" | "plugin">
    & Partial<Pick<MolSysViewerController, "moviePreviewClock">>
    & { prepareMovingVisualCapture?(): void; readMovingVisualState?(): MovingVisualSnapshot | undefined };

export type VisualStateCaptureReservation = {
    signal: AbortSignal;
    refused?: boolean;
    release(): void;
};

function captureKey(message: any): string | null {
    return typeof message?.request_id === "string" && message.request_id.length > 0
        && typeof message?.capture_revision === "string" && message.capture_revision.length > 0
        ? JSON.stringify([message.request_id, message.capture_revision]) : null;
}

/** One renderer's capture lifetimes, reserved before its scene barrier queues. */
export class VisualStateCaptureRequests {
    private readonly pending = new Map<string, AbortController>();
    private readonly retired = new Set<string>();
    private closed = false;

    reserve(message: any): VisualStateCaptureReservation | null {
        const key = captureKey(message);
        if (!key || this.closed || this.pending.has(key) || this.retired.has(key)) return null;
        const controller = new AbortController();
        if (this.pending.size >= 32) {
            this.retire(key);
            return { signal: controller.signal, refused: true, release() {} };
        }
        this.pending.set(key, controller);
        return { signal: controller.signal, release: () => {
            if (this.pending.get(key) === controller) this.pending.delete(key);
            this.retire(key);
        } };
    }

    cancel(message: any): void {
        const key = captureKey(message);
        if (!key || this.closed) return;
        const controller = this.pending.get(key);
        this.pending.delete(key);
        this.retire(key);
        controller?.abort();
    }

    dispose(): void {
        this.closed = true;
        for (const controller of this.pending.values()) controller.abort();
        this.pending.clear();
        this.retired.clear();
    }

    private retire(key: string): void {
        if (this.closed) return;
        this.retired.add(key);
        while (this.retired.size > 64) this.retired.delete(this.retired.values().next().value!);
    }
}

export function isFrontendControl(message: any): boolean {
    return message?.op === "cancel_visual_state";
}

/** File verdicts release controls independently of scene/draw progress. */
export function isStudioWorkFileResult(message: any): boolean {
    return message?.op === "studio_action_result"
        && (message.action === "save_work_file" || message.action === "cancel_work_file");
}

export function isFrontendRequest(message: any): boolean {
    return message?.op === "request_camera_snapshot" || message?.op === "request_image_export" || message?.op === "request_visual_state";
}

/** Start only after the scene prefix, leaving v2's dependent replies runnable. */
export async function captureAtScenePrefix(controller: RequestController, message: any,
    send: (event: any) => void, capture: VisualStateCaptureReservation): Promise<void> {
    const pending = handleFrontendRequest(controller, message, send, capture);
    if (message.capture_version === 2) {
        // Reservations own the signal/deadline/subscription until completion.
        // A failing transport callback must not become an unhandled rejection.
        void pending.catch(error => console.error("[MolSysViewer] Visual capture reply failed", error));
    } else await pending;
}

/** Camera/image replies belong to the live frontend, irrespective of its connector. */
export async function handleFrontendRequest(controller: RequestController, message: any, send: (event: any) => void,
    capture?: VisualStateCaptureReservation): Promise<void> {
    if (message.op === "request_visual_state") {
        const correlation = { event: "visual_state_snapshot", request_id: message.request_id,
            capture_revision: message.capture_revision };
        try {
            if (capture?.signal.aborted) return;
            if (capture?.refused) throw new Error("Too many pending canvas captures.");
            const canvas = controller.plugin.canvas3d;
            if (!canvas) throw new Error("No live canvas is available for capture.");
            const timeout = Number(message.capture_timeout_ms);
            if (message.capture_version === 2) {
                if (!controller.readMovingVisualState) throw new Error("Moving capture is unavailable on this renderer.");
                controller.prepareMovingVisualCapture?.();
                const nextMovieSample = message.movie_preview === undefined ? undefined
                    : controller.moviePreviewClock?.prepare(message.movie_preview);
                if (message.movie_preview !== undefined && !nextMovieSample) {
                    throw new Error("Movie preview is unavailable on this renderer.");
                }
                let sample: MovingVisualSnapshot | undefined;
                const captured = await readCanvasDraw(canvas, () => ({ ...sample!,
                    ...(nextMovieSample ? { movie_next_sample: nextMovieSample() } : {}) }),
                    Number.isFinite(timeout) && timeout > 0 ? Math.min(timeout, 30000) : 5000,
                    capture?.signal, () => !!(sample = controller.readMovingVisualState!()));
                if (!capture?.signal.aborted) send({ ...correlation, ok: true, capture_version: 2, ...captured });
                return;
            }
            // Read inside the didDraw callback. A Promise continuation can run
            // after another subscriber has advanced the model or camera.
            const { snapshot, structure_index } = await readCanvasDraw(canvas, () => {
                let structure_index: number | undefined;
                const release = controller.onTrajectoryState(state => { structure_index = state.currentFrame; }, { immediate: true });
                release();
                return { snapshot: controller.getCameraSnapshot(), structure_index };
            }, Number.isFinite(timeout) && timeout > 0 ? Math.min(timeout, 30000) : 5000, capture?.signal);
            if (!capture?.signal.aborted) send({ ...correlation, ok: !!snapshot, snapshot, structure_index });
        } catch (error) {
            if (!capture?.signal.aborted) send({ ...correlation, ok: false, error_type: error instanceof Error ? error.name : "Error" });
        } finally {
            capture?.release();
        }
        return;
    }
    if (message.op === "request_camera_snapshot") {
        const snapshot = controller.getCameraSnapshot();
        if (snapshot) send({ event: "camera_snapshot", snapshot });
        return;
    }
    if (message.op !== "request_image_export") throw new Error("Unknown frontend request.");
    const options = {
        width: typeof message.width === "number" ? message.width : undefined,
        height: typeof message.height === "number" ? message.height : undefined,
        scale: typeof message.scale === "number" ? message.scale : undefined,
        transparent: !!message.transparent,
        preset: typeof message.preset === "string" ? message.preset : undefined,
        cameraSnapshot: message.camera_snapshot && typeof message.camera_snapshot === "object" ? message.camera_snapshot : undefined,
    };
    const result = await controller.getImageDataUri(options);
    const metadata = {
        event: "image_export", scale: options.scale ?? 1, transparent: options.transparent,
        preset: options.preset ?? "current", width: options.width, height: options.height, format: "png",
    };
    if (typeof result === "string" && result) send({ ...metadata, data_uri: result });
    else if (result && typeof result === "object" && result.success === false) send({ ...result, ...metadata });
}
