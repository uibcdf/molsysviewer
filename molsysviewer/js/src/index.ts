// src/index.ts

import { MolSysViewerController } from "./managers/viewer-controller";
import { ViewerMessage } from "./messages/viewer-messages";
import { bootPopup } from "./popup/popup-logic";
import { PopupHostManager } from "./managers/popup-host";
import { buildControls } from "./ui/controls";
import { createLogger } from "./utils/logger";

// Re-export bootPopup so it is available in the bundle's public interface
export { bootPopup };

/**
 * NOTE FOR AUTOMATION AGENTS:
 * The generated bundle lives at ../viewer.js and should be rebuilt manually.
 * Do not edit viewer.js directly; modify TS sources under js/src/ instead.
 */
export default {
    render({ model, el }: { model: any; el: HTMLElement }) {
        const debug = !!model.get("debug_js");
        const sendLog = createLogger(model, debug);

        // Store commands from Python to replay them in the popout
        const commandLog: ViewerMessage[] = [];
        let isUpdatingFromPeer = false;

        // 1. Setup DOM
        const target = document.createElement("div");
        Object.assign(target.style, {
            width: "100%", height: "100%", minHeight: "400px", position: "relative",
            touchAction: "none", cursor: "grab"
        });
        target.addEventListener("pointerdown", () => target.style.cursor = "grabbing");
        target.addEventListener("pointerup", () => target.style.cursor = "grab");
        target.addEventListener("pointerleave", () => target.style.cursor = "grab");
        el.appendChild(target);

        // 2. Initialize Controller
        const controllerPromise = MolSysViewerController.create(target, msg => model.send(msg));

        // 3. Initialize Popup Manager
        // Use the URL of the currently executing script (the viewer bundle itself)
        // This is the most robust way to find the file, regardless of how Jupyter is serving it.
        const viewerJsPath = import.meta.url;
        console.log("[MolSysViewer] Using bundle path:", viewerJsPath);
        
        const popupMgr = new PopupHostManager(viewerJsPath);

        // 4. Build UI Controls
        controllerPromise.then(c => {
            const overlay = buildControls(c, model, (msg) => popupMgr.send("molsysviewer-sync-op", msg), () => popupMgr.open());
            target.appendChild(overlay);

            // 5. Setup Camera Sync (Host -> Popup)
            let hostCameraSyncTimer: ReturnType<typeof window.setTimeout> | null = null;
            c.plugin.canvas3d?.camera.events.changed.subscribe(() => {
                if (isUpdatingFromPeer) return;
                if (hostCameraSyncTimer) clearTimeout(hostCameraSyncTimer);
                hostCameraSyncTimer = setTimeout(() => {
                    popupMgr.send("molsysviewer-sync-camera", c.getCameraSnapshot());
                    hostCameraSyncTimer = null;
                }, 50);
            });
        });

        // 6. Handle Incoming Messages (Popup -> Host)
        window.addEventListener("message", async ev => {
            if (!ev.data || ev.data.from === "host") return;
            const { type, data } = ev.data;
            const controller = await controllerPromise;

            isUpdatingFromPeer = true;
            try {
                switch (type) {
                    case "molsysviewer-pop-ready":
                        popupMgr.isReady = true;
                        // Sync initial state to popup
                        popupMgr.send("molsysviewer-initial-sync", {
                            messages: [...commandLog],
                            cameraSnapshot: controller.getCameraSnapshot(),
                            isSpinActive: controller.isSpinActive,
                            isSwingActive: controller.isSwingActive,
                            isDarkMode: controller.isDarkMode,
                        });
                        isUpdatingFromPeer = false;
                        break;
                    case "molsysviewer-sync-op":
                        await controller.handleMessage(data as ViewerMessage);
                        isUpdatingFromPeer = false;
                        break;
                    case "molsysviewer-sync-camera":
                        if (data) {
                            controller.setCameraSnapshot(data, 0);
                            // Keep locked briefly to absorb echo
                            setTimeout(() => { isUpdatingFromPeer = false; }, 100);
                        } else {
                            isUpdatingFromPeer = false;
                        }
                        break;
                    case "molsysviewer-log-from-popout":
                        if (debug) sendLog("info", "[Popout Log]:", data.msg);
                        isUpdatingFromPeer = false;
                        break;
                    default:
                        // console.warn("[MolSysViewer Host] Unknown popout message type:", type);
                        isUpdatingFromPeer = false;
                        break;
                }
            } catch (e) {
                console.error("[MolSysViewer Host] Error handling popout message:", e);
                isUpdatingFromPeer = false;
            }
        });

        // 7. Handle Python Messages
        (async () => {
            try {
                const controller = await controllerPromise;
                model.send({ event: "ready" });
                const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
                if (Array.isArray(initialMessages) && initialMessages.length) {
                    for (const msg of initialMessages) {
                        await controller.handleMessage(msg);
                        commandLog.push(msg);
                    }
                }
            } catch (err) {
                console.error("[MolSysViewer] Init error:", err);
                sendLog("error", "[MolSysViewer] Init error:", err);
            }
        })();

        console.log("[MolSysViewer] widget render init");
        sendLog("info", "[MolSysViewer] widget render init");

        model.on("msg:custom", async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            if (debug) sendLog("info", "[MolSysViewer] msg from Python:", msg);
            try {
                const controller = await controllerPromise;
                await controller.handleMessage(msg);
                commandLog.push(msg);
                popupMgr.send("molsysviewer-sync-op", msg);
            } catch (error) {
                console.error("[MolSysViewer] Error handling message:", msg, error);
                sendLog("error", "[MolSysViewer] Error handling message:", msg, error);
            }
        });
    },
};
