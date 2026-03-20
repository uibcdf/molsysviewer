// src/index.ts

import { MolSysViewerController, suppressCanvasContextMenu } from "./managers/viewer-controller";
import { ViewerMessage } from "./messages/viewer-messages";
import { bootPopup } from "./popup/popup-logic";
import { PopupHostManager } from "./managers/popup-host";
import { buildControls } from "./ui/controls";
import { createLogger } from "./utils/logger";

const parseInitialTrajectoryInfo = (msgs: ViewerMessage[] | undefined) => {
    let frameCount: number | undefined = undefined;
    let multipleStructures = false;
    if (!Array.isArray(msgs)) return { frameCount, multipleStructures };
    for (const msg of msgs) {
        if (!msg || typeof msg !== "object") continue;
        if ((msg as any).op !== "load_molsys_payload") continue;
        const payload = (msg as any).payload;
        const structures = payload?.structures;
        if (Array.isArray(structures)) {
            frameCount = structures.length;
            multipleStructures = structures.length > 1;
        }
        if ((msg as any).multiple_structures === true) {
            multipleStructures = true;
        } else if ((msg as any).multiple_structures === false && frameCount === undefined) {
            multipleStructures = false;
        }
        break;
    }
    return { frameCount, multipleStructures };
};

// Re-export bootPopup so it is available in the bundle's public interface
export { bootPopup };
export { MolSysViewerController }; // Export Controller for Popup context usage
export async function bootDocsView(opts: {
    el: HTMLElement;
    initialMessages?: ViewerMessage[];
    ui?: any;
    runtimeUrl?: string;
}) {
    const debug = !!opts.ui?.debug_js;
    const sendLog = (level: string, ...args: any[]) => {
        if (!debug) return;
        // eslint-disable-next-line no-console
        console.log("[MolSysViewer docs]", level, ...args);
    };

    const commandLog: ViewerMessage[] = Array.isArray(opts.initialMessages) ? [...opts.initialMessages] : [];
    const ui = opts.ui || {};

    // Setup DOM
    const hostEl = opts.el;
    hostEl.innerHTML = "";
    const target = document.createElement("div");
    Object.assign(target.style, {
        width: "100%", height: "100%", minHeight: "400px", position: "relative",
        touchAction: "none", cursor: "default", overflow: "hidden"
    });

    // Track user interaction for camera sync logic
    let isUserInteracting = false;
    let wheelTimeout: ReturnType<typeof window.setTimeout> | null = null;
    const onPointerDown = () => { isUserInteracting = true; };
    const onPointerUpOrCancel = () => { isUserInteracting = false; };
    const onWheel = () => {
        isUserInteracting = true;
        if (wheelTimeout) clearTimeout(wheelTimeout);
        wheelTimeout = setTimeout(() => { isUserInteracting = false; }, 200);
    };

    target.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUpOrCancel);
    window.addEventListener("pointercancel", onPointerUpOrCancel);
    target.addEventListener("wheel", onWheel, { passive: true });

    hostEl.appendChild(target);

    // Initialize Controller (no-op notify)
    const controllerPromise = MolSysViewerController.create(target, () => {});

    // Popup manager: prefer runtime URL (docs-light), otherwise disable popout.
    const popupMgr = new PopupHostManager({
        moduleUrl: typeof opts.runtimeUrl === "string" ? opts.runtimeUrl : undefined,
        source: ""
    });

    const enablePopout = !!ui.enable_popout && !!opts.runtimeUrl;

    // Minimal model stub for buildControls
    const model = {
        get: (k: string) => (k in ui ? ui[k] : undefined),
        on: (_: string, __: any) => {},
        off: (_: string, __: any) => {}
    };

    // Build UI Controls & Setup Sync
    controllerPromise.then(c => {
        // If initial messages include a MolSys payload, pre-seed the frame count so the
        // trajectory bar can appear immediately (avoids a brief "buttons first, bar later" flicker).
        const trajInfo = parseInitialTrajectoryInfo(commandLog);
        if (trajInfo.frameCount !== undefined) {
            c.trajectory.setExpectedFrameCount(trajInfo.frameCount);
        }

        const sendSync = (msg: ViewerMessage) => {
            if (!msg) return;
            commandLog.push(msg);
            popupMgr.send("molsysviewer-sync-op", msg);
        };
        const overlay = buildControls(
            c,
            model,
            sendSync,
            target,
            enablePopout ? () => popupMgr.open() : undefined,
            {
                initialHasTrajectory: trajInfo.multipleStructures || (trajInfo.frameCount ?? 0) > 1,
                initialFrameCount: trajInfo.frameCount,
            }
        );
        target.appendChild(overlay);

        // Camera sync (Host -> Popup)
        if (c.plugin.canvas3d) {
            let hostCameraSyncTimer: ReturnType<typeof window.setTimeout> | null = null;
            const c3d = c.plugin.canvas3d;
            const syncCamera = () => {
                if (!popupMgr.isReady || !isUserInteracting) return;
                if (hostCameraSyncTimer) clearTimeout(hostCameraSyncTimer);
                hostCameraSyncTimer = setTimeout(() => {
                    popupMgr.send("molsysviewer-sync-camera", c.getCameraSnapshot());
                    hostCameraSyncTimer = null;
                }, 20);
            };
            const onCameraFrame = () => syncCamera();
            if (c3d.didDraw) {
                c3d.didDraw.subscribe(onCameraFrame);
            }
        }
    });

    // Handle Incoming Messages (Popup -> Host)
    const messageHandler = async (ev: MessageEvent) => {
        if (!ev.data || ev.data.from === "host") return;
        const { type, data } = ev.data;
        if (!type || typeof type !== "string" || !type.startsWith("molsysviewer-")) return;
        const controller = await controllerPromise;
        try {
            switch (type) {
                case "molsysviewer-pop-ready":
                    popupMgr.isReady = true;
                    popupMgr.send("molsysviewer-initial-sync", {
                        messages: [...commandLog],
                        cameraSnapshot: controller.getCameraSnapshot(),
                        isSpinActive: controller.isSpinActive,
                        isSwingActive: controller.isSwingActive,
                        isDarkMode: controller.isDarkMode,
                        autohide: !!ui.autohide_controls
                    });
                    break;
                case "molsysviewer-sync-op":
                    if (data) await controller.handleMessage(data as ViewerMessage);
                    break;
                case "molsysviewer-sync-camera":
                    if (data && !isUserInteracting) {
                        controller.setCameraSnapshot(data, 0);
                    }
                    break;
                case "molsysviewer-log-from-popout":
                    sendLog("info", "[Popout Log]:", data?.msg);
                    break;
            }
        } catch (e) {
            console.error("[MolSysViewer docs] Error handling popout message:", e);
        }
    };
    window.addEventListener("message", messageHandler);

    // Replay initial messages
    (async () => {
        try {
            const controller = await controllerPromise;
            const initial = Array.isArray(opts.initialMessages) ? opts.initialMessages : [];
            for (const msg of initial) {
                if (msg) await controller.handleMessage(msg);
            }
        } catch (err) {
            console.error("[MolSysViewer docs] Init error:", err);
        }
    })();
}

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
        // Serialize message handling to preserve order when many messages arrive at once
        // (e.g. flush of pending messages right after "ready").
        let messageQueue: Promise<void> = Promise.resolve();

        // 1. Setup DOM
        const target = document.createElement("div");
        Object.assign(target.style, {
            width: "100%", height: "100%", minHeight: "400px", position: "relative",
            touchAction: "none", cursor: "default", overflow: "hidden" // Default cursor
        });
        const releaseNotebookContextMenuSuppression = suppressCanvasContextMenu(el, target);
        
        // Track user interaction for "Master/Slave" camera sync logic
        let isUserInteracting = false;
        let wheelTimeout: ReturnType<typeof window.setTimeout> | null = null;

        const onPointerDown = () => { 
            // target.style.cursor = "grabbing"; // No change, keep default
            isUserInteracting = true;
        };
        const onPointerUpOrCancel = () => { 
            // target.style.cursor = "grab"; // No change, keep default
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
        target.addEventListener("wheel", onWheel, { passive: true }); // Make sure this line is not cut off
        
        el.appendChild(target);

        // 2. Initialize Controller
        const controllerPromise = MolSysViewerController.create(target, msg => model.send(msg));

        // 3. Initialize Popup Manager with Payload
        // Prefer explicit popup_js_source (for legacy/overrides), but fall back to the widget's ESM source.
        const popupJsSource = model.get("popup_js_source");
        const esmSource = model.get("_esm");
        const viewerJsSource = popupJsSource || esmSource;
        if (!viewerJsSource) {
            console.warn("[MolSysViewer] No viewer JS source found in model ('popup_js_source' or '_esm'). Popout will be disabled.");
        } else {
            const sourceKind = popupJsSource ? "popup_js_source" : "_esm";
            console.log(`[MolSysViewer] Popout source: ${sourceKind} (length=${viewerJsSource.length})`);
        }

        const popupMgr = new PopupHostManager(viewerJsSource || "");
        const enablePopout = !!model.get("enable_popout");

        // 4. Build UI Controls & Setup Sync
        controllerPromise.then(c => {
            // Pre-seed the expected frame count from the initial message buffer so the
            // trajectory bar can appear immediately (avoids a brief "buttons first, bar later" flicker).
            const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
            const trajInfo = parseInitialTrajectoryInfo(initialMessages);
            if (trajInfo.frameCount !== undefined) {
                c.trajectory.setExpectedFrameCount(trajInfo.frameCount);
            }

            const overlay = buildControls(
                c,
                model,
                (msg) => popupMgr.send("molsysviewer-sync-op", msg),
                target,
                enablePopout ? () => popupMgr.open() : undefined,
                {
                    initialHasTrajectory: trajInfo.multipleStructures || (trajInfo.frameCount ?? 0) > 1,
                    initialFrameCount: trajInfo.frameCount,
                }
            );
            target.appendChild(overlay);

            // 5. Setup Camera Sync (Host -> Popup)
            if (c.plugin.canvas3d) {
                let hostCameraSyncTimer: ReturnType<typeof window.setTimeout> | null = null;
                let cameraSnapshotTimer: ReturnType<typeof window.setTimeout> | null = null;
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

                const scheduleCameraSnapshot = () => {
                    if (cameraSnapshotTimer) clearTimeout(cameraSnapshotTimer);
                    cameraSnapshotTimer = setTimeout(() => {
                        const snapshot = c.getCameraSnapshot();
                        if (snapshot) {
                            model.send({ event: "camera_snapshot", snapshot });
                        }
                        cameraSnapshotTimer = null;
                    }, 300);
                };

                const onCameraFrame = () => {
                    syncCamera();
                    scheduleCameraSnapshot();
                };

                // Force usage of didDraw for reliable interactive sync, matching the popup's working logic
                if (c3d.didDraw) {
                    c3d.didDraw.subscribe(onCameraFrame);
                    console.log("[MolSysViewer] Host: Sync via didDraw (interactive camera movements).");
                } else if (c3d.camera.events?.changed) {
                    c3d.camera.events.changed.subscribe(onCameraFrame);
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
                            autohide: !!model.get("autohide_controls")
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

        const enqueueMessage = (msg: ViewerMessage, opts?: { syncToPopup?: boolean }) => {
            messageQueue = messageQueue
                .then(async () => {
                    if (!msg || typeof msg !== "object") return;
                    if (debug) sendLog("info", "[MolSysViewer] msg from Python:", msg);
                    const controller = await controllerPromise;
                    await controller.handleMessage(msg);
                    commandLog.push(msg);
                    if (opts?.syncToPopup) popupMgr.send("molsysviewer-sync-op", msg);
                })
                .catch((error) => {
                    console.error("[MolSysViewer] Error handling message:", msg, error);
                    sendLog("error", "[MolSysViewer] Error handling message:", msg, error);
                });
        };

        // 7. Handle Python Messages
        (async () => {
            try {
                model.send({ event: "ready" });
                const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
                if (Array.isArray(initialMessages) && initialMessages.length) {
                    for (const msg of initialMessages) {
                        if (msg) {
                            enqueueMessage(msg, { syncToPopup: false });
                        }
                    }
                    await messageQueue;
                }
            } catch (err) {
                console.error("[MolSysViewer] Init error:", err);
                sendLog("error", "[MolSysViewer] Init error:", err);
            }
        })();

        console.log("[MolSysViewer] widget render init");
        sendLog("info", "[MolSysViewer] widget render init");

        const onCustomMsg = (msg: ViewerMessage) => {
            if (msg && (msg as any).op === "request_camera_snapshot") {
                controllerPromise.then(c => {
                    const snapshot = c.getCameraSnapshot();
                    if (snapshot) {
                        model.send({ event: "camera_snapshot", snapshot });
                    }
                });
                return;
            }
            if (msg && (msg as any).op === "request_image_export") {
                controllerPromise.then(async c => {
                    const data_uri = await c.getImageDataUri({
                        width: typeof (msg as any).width === "number" ? (msg as any).width : undefined,
                        height: typeof (msg as any).height === "number" ? (msg as any).height : undefined,
                        scale: typeof (msg as any).scale === "number" ? (msg as any).scale : undefined,
                        transparent: !!(msg as any).transparent,
                    });
                    if (typeof data_uri === "string" && data_uri) {
                        model.send({
                            event: "image_export",
                            data_uri,
                            scale: typeof (msg as any).scale === "number" ? (msg as any).scale : 1,
                            transparent: !!(msg as any).transparent,
                            width: typeof (msg as any).width === "number" ? (msg as any).width : undefined,
                            height: typeof (msg as any).height === "number" ? (msg as any).height : undefined,
                            format: "png",
                        });
                    }
                });
                return;
            }
            enqueueMessage(msg, { syncToPopup: true });
        };

        model.on("msg:custom", onCustomMsg);
        
        // Sync autohide setting to popup
        model.on("change:autohide_controls", () => {
            popupMgr.send("molsysviewer-sync-autohide", { enabled: !!model.get("autohide_controls") });
        });

        // RETURN CLEANUP FUNCTION (supported by anywidget)
        return () => {
            console.log("[MolSysViewer] Disposing widget...");
            
            // 1. Remove global listeners
            window.removeEventListener("message", messageHandler);
            window.removeEventListener("pointerup", onPointerUpOrCancel);
            window.removeEventListener("pointercancel", onPointerUpOrCancel);
            target.removeEventListener("pointerdown", onPointerDown);
            target.removeEventListener("wheel", onWheel);
            releaseNotebookContextMenuSuppression();

            // 2. Remove model listeners
            model.off("msg:custom", onCustomMsg);

            // 3. Dispose Mol* plugin to free WebGL context
            controllerPromise.then(c => {
                try {
                    c.dispose();
                    console.log("[MolSysViewer] Mol* controller disposed.");
                } catch (e) {
                    console.error("[MolSysViewer] Error disposing plugin:", e);
                }
            });

            // 4. Close popup if open
            popupMgr.close();
        };
    },
};
