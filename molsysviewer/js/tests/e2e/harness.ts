import { MolSysViewerController } from "../../src/managers/viewer-controller";

declare global {
    // eslint-disable-next-line no-var
    var Harness: { createController: typeof createController } | undefined;
}

export async function createController(targetId = "root") {
    const target = document.getElementById(targetId) ?? document.body;
    return await MolSysViewerController.create(target, msg => {
        // Expose last message for debugging if needed
        (window as any).__lastMessage = msg;
    });
}

if (typeof window !== "undefined") {
    (window as any).Harness = { createController };
}

