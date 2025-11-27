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
        const target = document.createElement("div");
        target.style.width = "100%";
        target.style.height = "100%";
        target.style.minHeight = "400px";
        target.style.position = "relative";

        el.appendChild(target);

        const controllerPromise = MolSysViewerController.create(target);

        const makeButton = (label: string, onClick: () => void) => {
            const btn = document.createElement("button");
            btn.textContent = label;
            btn.style.padding = "2px 6px";
            btn.style.fontSize = "11px";
            btn.style.border = "1px solid rgba(255,255,255,0.5)";
            btn.style.borderRadius = "4px";
            btn.style.background = "rgba(0,0,0,0.5)";
            btn.style.color = "#fff";
            btn.style.cursor = "pointer";
            btn.addEventListener("click", onClick);
            return btn;
        };

        const send = (msg: ViewerMessage) => model.send(msg);

        const controllerReady = controllerPromise.then(c => {
            const showControls = !!model.get("show_controls");
            if (showControls) {
                const overlay = document.createElement("div");
                overlay.style.position = "absolute";
                overlay.style.top = "8px";
                overlay.style.left = "8px";
                overlay.style.display = "flex";
                overlay.style.gap = "6px";
                overlay.style.zIndex = "10";
                overlay.style.pointerEvents = "none";

                const mk = (label: string, handler: () => void) => {
                    const b = makeButton(label, handler);
                    b.style.pointerEvents = "auto";
                    overlay.appendChild(b);
                };

                mk("Reset", () => c.resetView());
                mk("Full", () => c.toggleFullscreen());
                mk("Bg", () => c.toggleBackground());
                mk("Spin", () => c.toggleSpin());
                mk("Swing", () => c.toggleSwing());

                target.appendChild(overlay);
            }
            return c;
        });

        (async () => {
            try {
                await controllerReady;
                model.send({ event: "ready" });
                const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
                if (Array.isArray(initialMessages) && initialMessages.length) {
                    const controller = await controllerReady;
                    for (const msg of initialMessages) {
                        await controller.handleMessage(msg);
                    }
                }
            } catch (err) {
                console.error("[MolSysViewer] Error inicializando plugin:", err);
            }
        })();

        console.log("[MolSysViewer] widget render inicial");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            console.log("[MolSysViewer] mensaje desde Python:", msg);
            try {
                const controller = await controllerReady;
                await controller.handleMessage(msg);
            } catch (error) {
                console.error("[MolSysViewer] Error manejando mensaje:", msg, error);
            }
        });
    },
};
