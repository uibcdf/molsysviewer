import { MolSysViewerController } from "../../src/managers/viewer-controller";

declare global {
    // eslint-disable-next-line no-var
    var Harness: { createController: typeof createController } | undefined;
}

export async function createController(targetId = "root") {
    const target = document.getElementById(targetId) ?? document.body;
    (window as any).__messages = [];
    const controller = await MolSysViewerController.create(target, msg => {
        (window as any).__lastMessage = msg;
        (window as any).__messages.push(msg);
    });
    (window as any).__controller = controller;
    return controller;
}

if (typeof window !== "undefined") {
    (window as any).Harness = { createController };
}

