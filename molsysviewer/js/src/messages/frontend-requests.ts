import type { MolSysViewerController } from "../managers/viewer-controller";
import { waitForCanvasDraw } from "../managers/canvas-draw";

type RequestController = Pick<MolSysViewerController, "getCameraSnapshot" | "getImageDataUri" | "onTrajectoryState" | "plugin">;

export function isFrontendRequest(message: any): boolean {
    return message?.op === "request_camera_snapshot" || message?.op === "request_image_export" || message?.op === "request_visual_state";
}

/** Camera/image replies belong to the live frontend, irrespective of its connector. */
export async function handleFrontendRequest(controller: RequestController, message: any, send: (event: any) => void): Promise<void> {
    if (message.op === "request_visual_state") {
        const correlation = { event: "visual_state_snapshot", request_id: message.request_id,
            capture_revision: message.capture_revision };
        try {
            const canvas = controller.plugin.canvas3d;
            if (!canvas) throw new Error("No live canvas is available for capture.");
            const timeout = Number(message.capture_timeout_ms);
            await waitForCanvasDraw(canvas, Number.isFinite(timeout) && timeout > 0 ? Math.min(timeout, 30000) : 5000);
            // Called behind the scene queue. Sample camera/frame in one JS
            // turn after a completed draw, not a replayed camera notification.
            let structure_index: number | undefined;
            const release = controller.onTrajectoryState(state => { structure_index = state.currentFrame; }, { immediate: true });
            release();
            const snapshot = controller.getCameraSnapshot();
            send({ ...correlation, ok: !!snapshot, snapshot, structure_index });
        } catch (error) {
            send({ ...correlation, ok: false, error_type: error instanceof Error ? error.name : "Error" });
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
