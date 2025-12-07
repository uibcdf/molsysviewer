// src/index.ts

import { MolSysViewerController } from "./managers/viewer-controller";
import { ViewerMessage } from "./messages/viewer-messages";
import { bootPopup } from "./popup/popup-logic";
import { PopupHostManager } from "./managers/popup-host";
import { buildControls } from "./ui/controls";
import { createLogger } from "./utils/logger";

// Re-export bootPopup so it is available in the bundle's public interface
export { bootPopup };
export { MolSysViewerController }; // Export Controller for Popup context usage

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

        // 1. Setup DOM
        const target = document.createElement("div");
        Object.assign(target.style, {
            width: "100%", height: "100%", minHeight: "400px", position: "relative",
            touchAction: "none", cursor: "grab"
        });
        
        // Track user interaction for "Master/Slave" camera sync logic
        let isUserInteracting = false;
        let wheelTimeout: ReturnType<typeof window.setTimeout> | null = null;

        const onPointerDown = () => { 
            target.style.cursor = "grabbing";
            isUserInteracting = true;
        };
        const onPointerUpOrCancel = () => { 
            target.style.cursor = "grab";
            isUserInteracting = false;
        };
        const onWheel = () => {
            isUserInteracting = true;
            if (wheelTimeout) clearTimeout(wheelTimeout);
            wheelTimeout = setTimeout(() => { isUserInteracting = false; }, 200);
        };

        target.addEventListener("pointerdown", onPointerDown);
        window.addEventListener("pointerup", onPointerUpOrCancel);
        window.addEventListener("pointercancel", onPointerUpOrCancel);
        target.addEventListener("wheel", onWheel, { passive: true });
        
        el.appendChild(target);

        // 2. Initialize Controller
        const controllerPromise = MolSysViewerController.create(target, msg => model.send(msg));

        // 3. Initialize Popup Manager with Payload
        const viewerJsSource = model.get("popup_js_source");
        if (!viewerJsSource) {
            console.warn("[MolSysViewer] 'popup_js_source' not found in model. Popout might fail.");
        } else {
            console.log("[MolSysViewer] Initialized with payload source length:", viewerJsSource.length);
        }
        
        const popupMgr = new PopupHostManager(viewerJsSource || "");

        // 4. Build UI Controls & Setup Sync
        controllerPromise.then(c => {
            const overlay = buildControls(c, model, (msg) => popupMgr.send("molsysviewer-sync-op", msg), () => popupMgr.open());
            target.appendChild(overlay);

            // 5. Setup Camera Sync (Host -> Popup)
            if (c.plugin.canvas3d) {
                let hostCameraSyncTimer: ReturnType<typeof window.setTimeout> | null = null;
                const c3d = c.plugin.canvas3d;

                const syncCamera = () => {
                    // Only sync if popout is open AND user is actively interacting with this viewer
                    if (!popupMgr.isReady || !isUserInteracting) return;
                    
                    if (hostCameraSyncTimer) clearTimeout(hostCameraSyncTimer);
                    hostCameraSyncTimer = setTimeout(() => {
                        popupMgr.send("molsysviewer-sync-camera", c.getCameraSnapshot());
                        hostCameraSyncTimer = null;
                    }, 20); // Fast debounce
                };

                // Force usage of didDraw for reliable interactive sync, matching the popup's working logic
                if (c3d.didDraw) {
                    c3d.didDraw.subscribe(syncCamera);
                    console.log("[MolSysViewer] Host: Sync via didDraw (interactive camera movements).");
                } else if (c3d.camera.events?.changed) {
                    c3d.camera.events.changed.subscribe(syncCamera);
                    console.log("[MolSysViewer] Host: Sync via camera.events.changed (fallback).");
                } else {
                    console.warn("[MolSysViewer] Host: No suitable camera event found for sync.");
                }
            } else {
                console.warn("[MolSysViewer] Host: plugin.canvas3d is undefined. Camera sync disabled.");
            }
        });

        // 6. Handle Incoming Messages (Popup -> Host)
        const messageHandler = async (ev: MessageEvent) => {
            // Self-cleaning: remove listener if widget is removed from DOM
            if (!document.body.contains(el)) {
                window.removeEventListener("message", messageHandler);
                return;
            }

            if (!ev.data || ev.data.from === "host") return;
            
            const { type, data } = ev.data;
            // Filter out internal or unknown messages to reduce log spam
            if (!type || typeof type !== 'string' || !type.startsWith("molsysviewer-")) return;

            const controller = await controllerPromise;

            try {
                switch (type) {
                    case "molsysviewer-pop-ready":
                        popupMgr.isReady = true;
                        // Sync initial state to popup
                        popupMgr.send("molsysviewer-initial-sync", {
                            messages: [...commandLog], // Sending sanitized copy
                            cameraSnapshot: controller.getCameraSnapshot(),
                            isSpinActive: controller.isSpinActive,
                            isSwingActive: controller.isSwingActive,
                            isDarkMode: controller.isDarkMode,
                        });
                        break;

                    case "molsysviewer-sync-op":
                        // Operations (style, color) are always applied
                        console.log("[MolSysViewer Host] Received sync-op:", data);
                        if (data) await controller.handleMessage(data as ViewerMessage);
                        break;

                    case "molsysviewer-sync-camera":
                        // Apply camera from popup ONLY if user is NOT interacting with host
                        if (data && !isUserInteracting) {
                            controller.setCameraSnapshot(data, 0);
                        }
                        break;

                    case "molsysviewer-log-from-popout":
                        if (debug) sendLog("info", "[Popout Log]:", data?.msg);
                        break;
                }
            } catch (e) {
                console.error("[MolSysViewer Host] Error handling popout message:", e);
            }
        };
        
        window.addEventListener("message", messageHandler);

        // 7. Handle Python Messages
        (async () => {
            try {
                const controller = await controllerPromise;
                model.send({ event: "ready" });
                const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
                if (Array.isArray(initialMessages) && initialMessages.length) {
                    for (const msg of initialMessages) {
                        if (msg) {
                            await controller.handleMessage(msg);
                            commandLog.push(msg);
                        }
                    }
                }
            } catch (err) {
                console.error("[MolSysViewer] Init error:", err);
                sendLog("error", "[MolSysViewer] Init error:", err);
            }
        })();

        console.log("[MolSysViewer] widget render init");
        sendLog("info", "[MolSysViewer] widget render init");

        const onCustomMsg = async (msg: ViewerMessage) => {
            if (!msg || typeof msg !== "object") return;
            if (debug) sendLog("info", "[MolSysViewer] msg from Python:", msg);
            try {
                const controller = await controllerPromise;
                await controller.handleMessage(msg);
                
                // Sanitize log
                if (msg && typeof msg === 'object') {
                    commandLog.push(msg);
                    popupMgr.send("molsysviewer-sync-op", msg);
                }
            } catch (error) {
                console.error("[MolSysViewer] Error handling message:", msg, error);
                sendLog("error", "[MolSysViewer] Error handling message:", msg, error);
            }
        };

        model.on("msg:custom", onCustomMsg);

        // RETURN CLEANUP FUNCTION (supported by anywidget)
        return () => {
            console.log("[MolSysViewer] Disposing widget...");
            
            // 1. Remove global listeners
            window.removeEventListener("message", messageHandler);
            window.removeEventListener("pointerup", onPointerUpOrCancel);
            window.removeEventListener("pointercancel", onPointerUpOrCancel);
            target.removeEventListener("pointerdown", onPointerDown);
            target.removeEventListener("wheel", onWheel);

            // 2. Remove model listeners
            model.off("msg:custom", onCustomMsg);

            // 3. Dispose Mol* plugin to free WebGL context
            controllerPromise.then(c => {
                try {
                    c.plugin.dispose();
                    console.log("[MolSysViewer] Mol* plugin disposed.");
                } catch (e) {
                    console.error("[MolSysViewer] Error disposing plugin:", e);
                }
            });

            // 4. Close popup if open
            popupMgr.close();
        };
    },
};