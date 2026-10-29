import type { MolSysViewerController } from "../managers/viewer-controller";

type RequestController = Pick<MolSysViewerController, "getCameraSnapshot" | "getImageDataUri">;

export function isFrontendRequest(message: any): boolean {
    return message?.op === "request_camera_snapshot" || message?.op === "request_image_export";
}

/** Camera/image replies belong to the live frontend, irrespective of its connector. */
export async function handleFrontendRequest(controller: RequestController, message: any, send: (event: any) => void): Promise<void> {
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
