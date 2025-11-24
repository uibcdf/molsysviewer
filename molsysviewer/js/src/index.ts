// src/index.ts

import { MolSysViewerController } from "./managers/viewer-controller";
import { ViewerMessage } from "./messages/viewer-messages";

/**
 * NOTE FOR AUTOMATION AGENTS:
 * The generated bundle lives at ../viewer.js and should be rebuilt manually.
 * Do not edit viewer.js directly; modify TS sources under js/src/ instead.
 */
export default {
    render({ model, el }: { model: any; el: HTMLElement }) {
        const controllerPromise = MolSysViewerController.create(el);

        (async () => {
            try {
                await controllerPromise;
                model.send({ event: "ready" });
            } catch (err) {
                console.error("[MolSysViewer] Error inicializando plugin:", err);
            }
        })();

        console.log("[MolSysViewer] widget render inicial");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            console.log("[MolSysViewer] mensaje desde Python:", msg);
            try {
                const controller = await controllerPromise;
                await controller.handleMessage(msg);
            } catch (error) {
                console.error("[MolSysViewer] Error manejando mensaje:", msg, error);
            }
        });
    },
};
