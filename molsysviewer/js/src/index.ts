// src/index.ts

import { MolSysViewerController, suppressCanvasContextMenu } from "./managers/viewer-controller";
import { ViewerMessage } from "./messages/viewer-messages";
import { bootPopup } from "./popup/popup-logic";
import { PopupHostManager } from "./managers/popup-host";
import { buildControls } from "./ui/controls";
import { createLogger } from "./utils/logger";
import type {
    LoadMolSysArrayPayloadMessage,
    StructureDataBeginMessage,
    StructureDataCancelMessage,
    StructureDataChunkMessage,
} from "./messages/array-native-transport";
import { ArrayNativeStreamReceiver } from "./messages/array-native-stream";
import { PopupReplayLog } from "./messages/popup-replay-log";
import { WidgetEnvelopeAdapter } from "./messages/widget-envelope";

/**
 * Given an `interaction_measurement_created` event, build the corresponding
 * `add_*_measurement` op that can be replayed in another canvas.
 * Returns null if the event is not a recognised measurement event.
 */
function buildMeasurementOpFromInteractionEvent(event: any): ViewerMessage | null {
    if (!event || event.event !== "interaction_measurement_created") return null;
    const action: string = event.action;
    const op =
        action === "distance" ? "add_distance_measurement" :
        action === "angle"    ? "add_angle_measurement"    :
        action === "dihedral" ? "add_dihedral_measurement" :
        null;
    if (!op) return null;
    return {
        op,
        tag: event.tag,
        options: {
            tag: event.tag,
            picks_atom_indices: event.picks_atom_indices ?? [],
            endpoint_policy: event.endpoint_policy,
            endpoint_kinds: event.endpoint_kinds,
            endpoint_labels: event.endpoint_labels,
            endpoint_atom_indices: event.endpoint_atom_indices,
        },
    } as unknown as ViewerMessage;
}

const parseInitialTrajectoryInfo = (msgs: ViewerMessage[] | undefined) => {
    let frameCount: number | undefined = undefined;
    let multipleStructures = false;
    let hasStructures = false;
    if (!Array.isArray(msgs)) return { frameCount, multipleStructures, hasStructures };
    for (const msg of msgs) {
        if (!msg || typeof msg !== "object") continue;
        if ((msg as any).op === "load_molsys_payload") {
            hasStructures = true;
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
        } else if ((msg as any).op === "load_molsys_payload_ref") {
            hasStructures = true;
            if (typeof (msg as any).n_structures === "number") {
                frameCount = (msg as any).n_structures;
                multipleStructures = (frameCount ?? 0) > 1;
            } else if ((msg as any).multiple_structures === true) {
                multipleStructures = true;
            }
        }
    }
    return { frameCount, multipleStructures, hasStructures };
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

    const initialMessages = Array.isArray(opts.initialMessages) ? opts.initialMessages : [];
    const popupReplay = new PopupReplayLog(initialMessages);
    const ui = opts.ui || {};
    const notifyHost = (event: Record<string, any>) => {
        if (!event || typeof event !== "object") return;
        if (ui.host_event_transport !== "url-scheme") return;
        try {
            const payload = encodeURIComponent(JSON.stringify(event));
            const url = `molsysviewer://event?payload=${payload}`;
            void fetch(url).catch((error) => {
                console.error("[MolSysViewer docs] Could not notify host:", error);
            });
        } catch (error) {
            console.error("[MolSysViewer docs] Could not notify host:", error);
        }
    };

    const messageMeta = (msg: ViewerMessage) => ({
        id: (msg as any)?.id,
        generation: (msg as any)?.generation,
        op: (msg as any)?.op,
    });

    const notifyRenderReady = (msg: ViewerMessage) => {
        const meta = messageMeta(msg);
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => {
                notifyHost({ event: "render_ready", ...meta });
            });
        });
    };

    (window as any).__molsysviewerDocsHandleMessage = async (msg: ViewerMessage) => {
        const meta = messageMeta(msg);
        try {
            const controller = await controllerPromise;
            await controller.handleMessage(msg);
            popupReplay.record(msg);
            notifyHost({ event: "message_ack", phase: "handled", ...meta });
            if ((msg as any)?.op === "load_molsys_payload" || (msg as any)?.op === "load_molsys_payload_ref") {
                notifyHost({ event: "structure_ready", ...meta });
                notifyRenderReady(msg);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            notifyHost({ event: "message_error", phase: "handled", error: message, ...meta });
            throw error;
        }
    };

    // Setup DOM
    const hostEl = opts.el;
    hostEl.innerHTML = "";
    const target = document.createElement("div");
    Object.assign(target.style, {
        width: "100%", height: "100%", minHeight: "300px", position: "relative",
        touchAction: "none", cursor: "default", overflow: "hidden"
    });

    setupWidgetResizer(hostEl, target, (w, h) => {
        hostEl.style.height = `${h}px`;
        target.style.height = `${h}px`;
        controllerPromise.then(c => {
            c.plugin.canvas3d?.requestResize();
        });
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

    const trajInfo = parseInitialTrajectoryInfo(initialMessages);

    // Initialize Controller (no-op notify)
    const panelModeStyle = (ui.panel_mode_style as string) || "drawer";
    const controllerPromise = MolSysViewerController.create(target, () => {}, undefined, { 
        panelModeStyle,
        hasInitialStructures: trajInfo.hasStructures,
    });

    // Popup manager: prefer runtime URL (docs-light), otherwise disable popout.
    const popupMgr = new PopupHostManager({
        moduleUrl: typeof opts.runtimeUrl === "string" ? opts.runtimeUrl : undefined,
        source: "",
        viewerId: typeof ui.runtime_viewer_id === "string" ? ui.runtime_viewer_id : undefined,
        sessionId: typeof ui.runtime_session_id === "string" ? ui.runtime_session_id : undefined,
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
        if (trajInfo.frameCount !== undefined) {
            c.trajectory.setExpectedFrameCount(trajInfo.frameCount);
        }

        const sendSync = (msg: ViewerMessage) => {
            if (!msg) return;
            popupReplay.record(msg);
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
        if (overlay) target.appendChild(overlay);

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
        const popupMessage = popupMgr.receive(ev);
        if (!popupMessage) return;
        const { type } = popupMessage;
        const data: any = popupMessage.data;
        const controller = await controllerPromise;
        try {
            switch (type) {
                case "molsysviewer-pop-ready":
                    popupMgr.isReady = true;
                    popupMgr.send("molsysviewer-initial-sync", {
                        messages: popupReplay.snapshot("canvas"),
                        cameraSnapshot: controller.getCameraSnapshot(),
                        isSpinActive: controller.isSpinActive,
                        isSwingActive: controller.isSwingActive,
                        isDarkMode: controller.isDarkMode,
                        autohide: !!ui.autohide_controls
                    });
                    break;
                case "molsysviewer-sync-op":
                    if (data) await controller.handleMessage(data as ViewerMessage);
                    if (data) popupReplay.record(data as ViewerMessage);
                    if (data) popupMgr.send("molsysviewer-sync-op", data);
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
            notifyHost({ event: "ready" });
        } catch (err) {
            console.error("[MolSysViewer docs] Init error:", err);
            const message = err instanceof Error ? err.message : String(err);
            notifyHost({ event: "frontend_error", phase: "init", error: message });
        }
    })();
}

function setupWidgetResizer(
    host: HTMLElement,
    target: HTMLElement,
    onResize: (width: number, height: number) => void
) {
    host.style.position = "relative";
    
    const handle = document.createElement("div");
    Object.assign(handle.style, {
        position: "absolute",
        left: "0",
        right: "0",
        bottom: "0",
        height: "8px",
        cursor: "ns-resize",
        background: "rgba(255, 255, 255, 0.04)",
        borderTop: "1px solid rgba(255, 255, 255, 0.08)",
        zIndex: "1000",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "background 150ms"
    });
    
    const dots = document.createElement("div");
    Object.assign(dots.style, {
        width: "24px",
        height: "3px",
        borderRadius: "1.5px",
        background: "rgba(255, 255, 255, 0.2)",
        transition: "background 150ms"
    });
    handle.appendChild(dots);

    handle.addEventListener("mouseenter", () => {
        handle.style.background = "rgba(255, 255, 255, 0.12)";
        dots.style.background = "rgba(255, 255, 255, 0.5)";
    });
    handle.addEventListener("mouseleave", () => {
        handle.style.background = "rgba(255, 255, 255, 0.04)";
        dots.style.background = "rgba(255, 255, 255, 0.2)";
    });

    handle.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        const startY = e.clientY;
        const startHeight = host.clientHeight;
        
        const onPointerMove = (moveEvent: PointerEvent) => {
            const deltaY = moveEvent.clientY - startY;
            const newHeight = Math.max(300, startHeight + deltaY);
            onResize(host.clientWidth, newHeight);
        };

        const onPointerUp = () => {
            window.removeEventListener("pointermove", onPointerMove);
            window.removeEventListener("pointerup", onPointerUp);
        };

        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
    });

    host.appendChild(handle);
}

/**
 * NOTE FOR AUTOMATION AGENTS:
 * The generated bundle lives at ../viewer.js and should be rebuilt manually.
 * Do not edit viewer.js directly; modify TS sources under js/src/ instead.
 */
export default {
    render({ model, el }: { model: any; el: HTMLElement }) {
        const debug = !!model.get("debug_js");

        // R1 seam: every browser->Python message goes through sendToPython, which
        // envelopes control messages (raw/data-plane pass through). The widget.py
        // bootstrap (request_widget_runtime_source) runs before this adapter and
        // stays raw by design. Rejected messages are observable and never sent.
        const envelopeAdapter = new WidgetEnvelopeAdapter(
            String(model.get("runtime_viewer_id") || ""),
            String(model.get("runtime_session_id") || ""),
        );
        const reportContractRejection = (seam: string, reason: string, detail: string) => {
            console.error(`[MolSysViewer] runtime contract rejected ${seam} (${reason}): ${detail}`);
            const diagnostic = envelopeAdapter.wrapOutbound({
                event: "runtime_contract_rejected",
                seam,
                reason,
                detail,
            });
            if (diagnostic.kind === "send") model.send(diagnostic.message);
        };
        let sendLog: ReturnType<typeof createLogger>;
        /** Sends to Python; returns the envelope messageId so a request can be
         *  correlated to its answer, or null when the adapter rejected it. */
        const sendToPython = (message: Record<string, unknown>): string | null => {
            const result = envelopeAdapter.wrapOutbound(message);
            if (result.kind === "send") {
                model.send(result.message);
                return (result.message as { messageId?: string }).messageId ?? null;
            }
            reportContractRejection("widget-outbound", result.reason, result.detail);
            return null;
        };
        sendLog = createLogger(model, debug, sendToPython);

        // R2: the canonical popup scene snapshot is built by Python from live
        // state. The host requests it on popup ready and resolves the pending
        // promise when the correlated projection arrives.
        const pendingSceneSnapshots = new Map<
            string,
            { mode: "canvas" | "panel"; settle: (messages: ViewerMessage[] | null) => void }
        >();
        /** Cancel requests owned by an endpoint that went away, instead of
         *  leaving them pending until their timeout. */
        const cancelSceneSnapshotsFor = (mode: "canvas" | "panel") => {
            for (const [messageId, entry] of [...pendingSceneSnapshots]) {
                if (entry.mode !== mode) continue;
                pendingSceneSnapshots.delete(messageId);
                entry.settle(null);
            }
        };
        const requestPopupSceneSnapshot = (
            mode: "canvas" | "panel",
            popupEndpointId: string | null,
        ): Promise<ViewerMessage[] | null> =>
            new Promise(resolve => {
                const messageId = sendToPython({
                    event: "request_popup_scene_snapshot",
                    mode,
                    popup_endpoint_id: popupEndpointId,
                });
                if (!messageId) {
                    resolve(null);
                    return;
                }
                let done = false;
                const settle = (messages: ViewerMessage[] | null) => {
                    if (done) return;
                    done = true;
                    pendingSceneSnapshots.delete(messageId);
                    resolve(messages);
                };
                pendingSceneSnapshots.set(messageId, { mode, settle });
                // Never leave a popup blocked on a lost answer: fall back to the
                // compatibility replay if Python does not respond.
                window.setTimeout(() => settle(null), 5000);
            });

        const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
        const trajInfo = parseInitialTrajectoryInfo(initialMessages);

        // Avoid retaining superseded molecular generations and current-state
        // updates. Non-reducible scene operations remain replayable until a
        // canonical Python scene projection replaces this journal.
        // R2: the interactive path bootstraps popups from Python's canonical
        // snapshot, so it keeps no replay journal. Recording one cost memory that
        // grew with the session, and falling back to it could have shown a popup a
        // scene Python no longer had. bootDocsView still uses PopupReplayLog: a
        // static HTML export has no Python to ask.
        // Serialize message handling to preserve order when many messages arrive at once
        // (e.g. flush of pending messages right after "ready").
        let messageQueue: Promise<void> = Promise.resolve();

        // 1. Setup DOM
        const target = document.createElement("div");
        target.tabIndex = 0;
        target.classList.add("molsysviewer-host");
        Object.assign(target.style, {
            width: "100%", height: "100%", minHeight: "300px", position: "relative",
            touchAction: "none", cursor: "default", overflow: "hidden", outline: "none" // Default cursor, focus outline hidden
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
        
        target.tabIndex = 0;
        target.addEventListener("keydown", (e: KeyboardEvent) => {
            if (e.key === "v" || e.key === "V") {
                const active = document.activeElement;
                if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.hasAttribute("contenteditable"))) {
                    return;
                }
                e.preventDefault();
                e.stopPropagation();
                controllerPromise.then(c => {
                    const isHidden = c.canvasHost.style.display === "none";
                    c.setCanvasVisibility(isHidden);
                });
            }
        });
        
        el.appendChild(target);

        // Setup interactive resizing
        setupWidgetResizer(el, target, (w, h) => {
            el.style.height = `${h}px`;
            target.style.height = `${h}px`;
            
            sendToPython({ event: "widget_resize", height: h, width: w });
            controllerPromise.then(c => {
                c.plugin.canvas3d?.requestResize();
            });
        });

        // 2. Initialize Popup Manager. The popup source is resolved lazily so the
        // notebook state does not need a second synced copy of the AnyWidget bundle.
        const legacyPopupJsSource = model.get("popup_js_source");
        const esmSource = model.get("_esm");
        const esmLooksLikeFullRuntime =
            typeof esmSource === "string" &&
            esmSource.includes("bootPopup") &&
            esmSource.includes("MolSysViewerController");
        const cachedWidgetRuntime = (globalThis as any).__molsysviewer_anywidget_runtime__;
        let popupJsSourceCache =
            typeof legacyPopupJsSource === "string" && legacyPopupJsSource
                ? legacyPopupJsSource
                : typeof cachedWidgetRuntime?.source === "string" && cachedWidgetRuntime.source
                    ? cachedWidgetRuntime.source
                    : esmLooksLikeFullRuntime
                        ? esmSource
                        : "";
        let pendingPopupSource: Promise<string> | null = null;
        let resolvePendingPopupSource: ((source: string) => void) | null = null;
        let rejectPendingPopupSource: ((reason?: unknown) => void) | null = null;
        let popupSourceTimer: ReturnType<typeof window.setTimeout> | null = null;

        const requestPopupSource = (): Promise<string> => {
            if (popupJsSourceCache) return Promise.resolve(popupJsSourceCache);
            if (pendingPopupSource) return pendingPopupSource;
            pendingPopupSource = new Promise<string>((resolve, reject) => {
                resolvePendingPopupSource = resolve;
                rejectPendingPopupSource = reject;
                popupSourceTimer = setTimeout(() => {
                    reject(new Error("Timed out waiting for MolSysViewer popup source"));
                    pendingPopupSource = null;
                    resolvePendingPopupSource = null;
                    rejectPendingPopupSource = null;
                    popupSourceTimer = null;
                }, 10000);
                sendToPython({ event: "request_popup_source" });
            });
            return pendingPopupSource;
        };

        const popupMgr = new PopupHostManager({
            source: popupJsSourceCache || undefined,
            sourceProvider: requestPopupSource,
            viewerId: model.get("runtime_viewer_id"),
            sessionId: model.get("runtime_session_id"),
            onEndpointClosed: mode => cancelSceneSnapshotsFor(mode),
            onContractRejection: rejection => reportContractRejection(
                rejection.seam,
                rejection.reason,
                rejection.detail,
            ),
        });
        const enablePopout = !!model.get("enable_popout");

        // 3. Initialize Controller
        const panelModeStyle = (model.get("panel_mode_style") as string) || "drawer";
        const controllerPromise = MolSysViewerController.create(target, msg => {
            sendToPython(msg);
            // Sync interactive measurements to popup: the host already has them (created in-place),
            // so we retain the equivalent add_*_measurement op and forward it to any
            // open popup so it reflects the same measurement without going through Python round-trip.
            if (msg?.event === "interaction_measurement_created") {
                const op = buildMeasurementOpFromInteractionEvent(msg);
                if (op) {
                    popupMgr.send("molsysviewer-sync-op", op);
                }
            }
            // Sync section gizmo position to popup when user drags in host canvas.
            if (msg?.event === "section_moved") {
                const syncOp = { op: "sync_section_position", tag: msg.tag, point: msg.point, normal: msg.normal };
                popupMgr.send("molsysviewer-sync-op", syncOp);
            }
        }, undefined, { 
            panelModeStyle, 
            model,
            hasInitialStructures: trajInfo.hasStructures,
            onPanelPopClick: enablePopout ? () => {
                controllerPromise.then(c => {
                    c.saveHostPanelState();
                    if (c.canvasHost.style.display === "none") {
                        c.setCanvasVisibility(true);
                    }
                    if (c.sharedShell) {
                        c.sharedShell.setVisible(false);
                    }
                    popupMgr.open("panel");
                });
            } : undefined
        });
        const arrayNativeStream = new ArrayNativeStreamReceiver(
            event => sendToPython(event),
            async (begin, payload) => {
                const controller = await controllerPromise;
                await controller.loadArrayNativeMolSysPayload(payload, begin.label);
            },
        );

        // 4. Build UI Controls & Setup Sync
        controllerPromise.then(c => {
            // Auto-expand Jupyter/VS Code cell output area to prevent scrolling of molsysviewer.
            // This is a strictly local change traversing up only our widget's parent chain.
            const removeOutputLimits = () => {
                let parent: HTMLElement | null = target.parentElement;
                while (parent) {
                    if (parent.classList.contains("jp-OutputArea-child") || 
                        parent.classList.contains("jp-OutputArea-output") || 
                        parent.classList.contains("jp-OutputArea") || 
                        parent.classList.contains("output_subarea") ||
                        parent.classList.contains("vscode-notebook-cell-output-container") ||
                        parent.classList.contains("cell-output-ipywidget")) {
                        parent.style.maxHeight = "none";
                    }
                    if (parent.parentElement) {
                        parent = parent.parentElement;
                    } else {
                        const root = parent.getRootNode();
                        parent = root instanceof ShadowRoot ? (root.host as HTMLElement) : null;
                    }
                }
            };
            removeOutputLimits();
            setTimeout(removeOutputLimits, 100);
            setTimeout(removeOutputLimits, 500);

            c.onTogglePanelModeOverride = () => {
                if (popupMgr.panelWin && !popupMgr.panelWin.closed) {
                    popupMgr.close("panel");
                    return true;
                }
                return false;
            };

            // Pre-seed the expected frame count from the initial message buffer so the
            // trajectory bar can appear immediately (avoids a brief "buttons first, bar later" flicker).
            if (trajInfo.frameCount !== undefined) {
                c.trajectory.setExpectedFrameCount(trajInfo.frameCount);
            }

            let overlay: HTMLElement | undefined = undefined;
            const updateControls = () => {
                if (overlay) {
                    overlay.remove();
                }
                overlay = buildControls(
                    c,
                    model,
                    (msg) => popupMgr.send("molsysviewer-sync-op", msg),
                    target,
                    enablePopout ? () => popupMgr.open("canvas") : undefined,
                    {
                        initialHasTrajectory: trajInfo.multipleStructures || (trajInfo.frameCount ?? 0) > 1,
                        initialFrameCount: trajInfo.frameCount,
                    }
                );
                if (overlay) {
                    target.appendChild(overlay);
                }
            };
            updateControls();
            popupMgr.setController(c);

            model.on("change:controls_mode", () => {
                updateControls();
                popupMgr.send("molsysviewer-sync-ui", { controlsMode: model.get("controls_mode") });
            });
            model.on("change:viewer_mode", () => {
                popupMgr.send("molsysviewer-sync-ui", { viewerMode: model.get("viewer_mode") });
            });
            model.on("change:panel_mode_style", () => {
                popupMgr.send("molsysviewer-sync-ui", { panelModeStyle: model.get("panel_mode_style") });
            });

            if (c.sharedShell) {
                c.sharedShell.onLayoutChange = (state) => {
                    popupMgr.send("molsysviewer-sync-ui", state);
                    c.triggerLayoutChange(state);
                };
            }

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
                            sendToPython({ event: "camera_snapshot", snapshot });
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
                } else if (c3d.camera.stateChanged) {
                    c3d.camera.stateChanged.subscribe(onCameraFrame);
                    console.log("[MolSysViewer] Host: Sync via camera.stateChanged (fallback).");
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

            const popupMessage = popupMgr.receive(ev);
            if (!popupMessage) return;
            const { type } = popupMessage;
            const data: any = popupMessage.data;

            const controller = await controllerPromise;

            try {
                switch (type) {
                    case "molsysviewer-pop-ready": {
                        popupMgr.isReady = true;
                        // R2: bootstrap from Python's canonical current-scene
                        // projection; the replay journal is the fallback only.
                        const canvasSnapshot = await requestPopupSceneSnapshot(
                            "canvas",
                            popupMgr.popupEndpointId("canvas"),
                        );
                        // Endpoint-targeted: this bootstrap carries molecular data
                        // and must never reach a panel popup.
                        if (!canvasSnapshot) {
                            sendLog("error", "[MolSysViewer] canvas popup bootstrap: Python did not answer the scene snapshot request");
                        }
                        popupMgr.sendTo("canvas", "molsysviewer-initial-sync", {
                            messages: canvasSnapshot ?? [],
                            cameraSnapshot: controller.getCameraSnapshot(),
                            isSpinActive: controller.isSpinActive,
                            isSwingActive: controller.isSwingActive,
                            isDarkMode: controller.isDarkMode,
                            autohide: !!model.get("autohide_controls"),
                            viewerMode: controller.getViewerMode(),
                            controlsMode: controller.getControlsMode(),
                            panelModeStyle: controller.getPanelModeStyle(),
                            isAmbient: controller.sharedShell?.isAmbient,
                            isSplit: controller.sharedShell?.isSplit,
                        });
                        break;
                    }

                    case "molsysviewer-panel-ready": {
                        popupMgr.isPanelReady = true;
                        // R2: canonical UI-only projection from Python.
                        const panelSnapshot = await requestPopupSceneSnapshot(
                            "panel",
                            popupMgr.popupEndpointId("panel"),
                        );
                        if (!panelSnapshot) {
                            sendLog("error", "[MolSysViewer] panel popup bootstrap: Python did not answer the scene snapshot request");
                        }
                        // The System subpanel is the one Studio section built from
                        // the structure rather than from a Python summary. The panel
                        // snapshot carries no geometry by design, so the hierarchy
                        // the host already derived is relayed instead — one entry per
                        // group, and a single producer of the shape.
                        lastRelayedHierarchy = controller.getHierarchyItems();
                        popupMgr.sendTo("panel", "molsysviewer-initial-sync", {
                            messages: panelSnapshot ?? [],
                            hierarchyItems: lastRelayedHierarchy,
                            cameraSnapshot: controller.getCameraSnapshot(),
                            isSpinActive: controller.isSpinActive,
                            isSwingActive: controller.isSwingActive,
                            isDarkMode: controller.isDarkMode,
                            autohide: !!model.get("autohide_controls"),
                            viewerMode: controller.getViewerMode(),
                            controlsMode: controller.getControlsMode(),
                            panelModeStyle: controller.getPanelModeStyle(),
                            isAmbient: controller.sharedShell?.isAmbient,
                            isSplit: controller.sharedShell?.isSplit,
                        });
                        break;
                    }

                    case "molsysviewer-sync-op":
                        // The host applies a popup intent once, then projects the result
                        // to every popup endpoint, including the source.
                        if (data) await controller.handleMessage(data as ViewerMessage);
                        if (data) popupMgr.send("molsysviewer-sync-op", data);
                        break;

                    case "molsysviewer-structure-data-ack":
                        // The popup acknowledges its own stream; Python drives the
                        // next chunk from these, so they must reach the authority.
                        if (data) sendToPython(data);
                        break;

                    case "molsysviewer-sync-camera":
                        // Apply camera from popup ONLY if user is NOT interacting with host
                        if (data && !isUserInteracting) {
                            controller.setCameraSnapshot(data, 0);
                        }
                        break;

                    case "molsysviewer-popup-interaction":
                        // 1. Forward to Python so it is recorded.
                        if (data) sendToPython(data);
                        // 2. Apply to the host canvas (popup already has it, so do NOT re-sync to popup).
                        if (data) {
                            const op = buildMeasurementOpFromInteractionEvent(data);
                            if (op) enqueueMessage(op, { syncToPopup: false });
                        }
                        // 3. Sync section gizmo position to host when user drags in popup.
                        if (data?.event === "section_moved") {
                            const syncOp = { op: "sync_section_position", tag: data.tag, point: data.point, normal: data.normal };
                            enqueueMessage(syncOp as any, { syncToPopup: false });
                        }
                        break;

                    case "molsysviewer-log-from-popout":
                        if (debug) sendLog("info", "[Popout Log]:", data?.msg);
                        break;

                    case "molsysviewer-runtime-contract-rejected":
                        sendToPython({
                            event: "runtime_contract_rejected",
                            seam: data?.seam ?? "popup",
                            reason: data?.reason ?? "unknown",
                            detail: data?.detail ?? "unknown",
                        });
                        break;
                }
            } catch (e) {
                console.error("[MolSysViewer Host] Error handling popout message:", e);
            }
        };
        
        window.addEventListener("message", messageHandler);

        // Identity of the hierarchy last relayed to an open panel popup, so a
        // structure change reaches it without re-sending on every message.
        let lastRelayedHierarchy: unknown = null;

        const enqueueMessage = (msg: ViewerMessage, opts?: { syncToPopup?: boolean }) => {
            messageQueue = messageQueue
                .then(async () => {
                    if (!msg || typeof msg !== "object") return;
                    if (debug) sendLog("info", "[MolSysViewer] msg from Python:", msg);
                    const controller = await controllerPromise;
                    await controller.handleMessage(msg);
                    if (opts?.syncToPopup) popupMgr.send("molsysviewer-sync-op", msg);
                    if (popupMgr.isPanelOpen) {
                        const items = controller.getHierarchyItems();
                        if (items !== lastRelayedHierarchy) {
                            lastRelayedHierarchy = items;
                            popupMgr.sendTo("panel", "molsysviewer-sync-hierarchy", { items });
                        }
                    }
                })
                .catch((error) => {
                    console.error("[MolSysViewer] Error handling message:", msg, error);
                    sendLog("error", "[MolSysViewer] Error handling message:", msg, error);
                });
        };

        // 7. Handle Python Messages
        (async () => {
            try {
                const initialMessages = model.get("initial_messages") as ViewerMessage[] | undefined;
                if (Array.isArray(initialMessages) && initialMessages.length) {
                    for (const msg of initialMessages) {
                        if (msg) {
                            enqueueMessage(msg, { syncToPopup: false });
                        }
                    }
                    await messageQueue;
                }
                // D4: a canvas popup now receives its own typed generation,
                // streamed to its endpoint and relayed by the host, so enabling
                // popout no longer forces the whole viewer onto the JSON path.
                const binaryStructureData = [1];
                sendToPython({
                    event: "ready",
                    capabilities: {
                        binary_structure_data: binaryStructureData,
                        max_buffer_bytes: 16 * 1024 * 1024,
                        transferable_array_buffer: false,
                    },
                });
            } catch (err) {
                console.error("[MolSysViewer] Init error:", err);
                sendLog("error", "[MolSysViewer] Init error:", err);
            }
        })();

        console.log("[MolSysViewer] widget render init");
        sendLog("info", "[MolSysViewer] widget render init");

        const onCustomMsg = (
            msg:
                | ViewerMessage
                | LoadMolSysArrayPayloadMessage
                | StructureDataBeginMessage
                | StructureDataChunkMessage
                | StructureDataCancelMessage,
            buffers?: DataView[],
        ) => {
            // R1 seam: unwrap and validate Python->browser envelopes. `raw` keeps
            // the existing dispatch for bootstrap/data-plane; a rejected envelope is
            // observable and dropped; the command-duplicate ack is consumed here.
            const inbound = envelopeAdapter.unwrapInbound(msg);
            if (inbound.kind === "rejected") {
                reportContractRejection("widget-inbound", inbound.reason, inbound.detail);
                return;
            }
            if (inbound.kind === "message") {
                const event = (inbound.message as any).event;
                if (event === "command_duplicate_ack") return;
                if (event === "popup_scene_snapshot") {
                    // Consumed at the seam: resolve the request that asked for it.
                    const correlationId = inbound.envelope.correlationId;
                    const entry = correlationId ? pendingSceneSnapshots.get(correlationId) : undefined;
                    if (entry) {
                        entry.settle(((inbound.message as any).messages ?? []) as ViewerMessage[]);
                    }
                    return;
                }
                msg = inbound.message as typeof msg;
            }
            // D4: a message addressed to a popup endpoint is relayed, never
            // consumed. The host holds one chunk transiently while forwarding
            // and keeps no copy of the generation.
            const relayTarget = (msg as any)?.target_endpoint_id;
            if (typeof relayTarget === "string" && relayTarget) {
                const mode = relayTarget === popupMgr.popupEndpointId("canvas") ? "canvas"
                    : relayTarget === popupMgr.popupEndpointId("panel") ? "panel"
                    : null;
                if (!mode) {
                    sendLog("error", `[MolSysViewer] relay target is not an open endpoint: ${relayTarget}`);
                    return;
                }
                popupMgr.sendTo(mode, "molsysviewer-structure-data", {
                    message: msg,
                    buffers: buffers ?? [],
                });
                return;
            }
            if (
                msg && (
                    msg.op === "structure_data_begin" ||
                    msg.op === "structure_data_chunk" ||
                    msg.op === "structure_data_cancel"
                )
            ) {
                messageQueue = messageQueue
                    .then(() => arrayNativeStream.handle(msg, buffers ?? []))
                    .catch((error) => {
                        console.error("[MolSysViewer] Error handling array-native stream:", error);
                        sendLog("error", "[MolSysViewer] Error handling array-native stream:", error);
                    });
                return;
            }
            if (msg && msg.op === "load_molsys_array_payload") {
                messageQueue = messageQueue
                    .then(async () => {
                        const controller = await controllerPromise;
                        await controller.handleArrayNativeMolSysMessage(msg, buffers ?? []);
                    })
                    .catch((error) => {
                        console.error("[MolSysViewer] Error handling array-native payload:", error);
                        sendLog("error", "[MolSysViewer] Error handling array-native payload:", error);
                    });
                return;
            }
            if (msg && (msg as any).op === "popup_source") {
                const source = typeof (msg as any).source === "string" ? (msg as any).source : "";
                if (popupSourceTimer) {
                    window.clearTimeout(popupSourceTimer);
                    popupSourceTimer = null;
                }
                pendingPopupSource = null;
                if (source) {
                    popupJsSourceCache = source;
                    resolvePendingPopupSource?.(source);
                } else {
                    rejectPendingPopupSource?.(new Error("MolSysViewer popup source response was empty"));
                }
                resolvePendingPopupSource = null;
                rejectPendingPopupSource = null;
                return;
            }
            if (msg && (msg as any).op === "request_camera_snapshot") {
                controllerPromise.then(c => {
                    const snapshot = c.getCameraSnapshot();
                    if (snapshot) {
                        sendToPython({ event: "camera_snapshot", snapshot });
                    }
                });
                return;
            }
            if (msg && (msg as any).op === "request_image_export") {
                controllerPromise.then(async c => {
                    const imageExportResult = await c.getImageDataUri({
                        width: typeof (msg as any).width === "number" ? (msg as any).width : undefined,
                        height: typeof (msg as any).height === "number" ? (msg as any).height : undefined,
                        scale: typeof (msg as any).scale === "number" ? (msg as any).scale : undefined,
                        transparent: !!(msg as any).transparent,
                        preset: typeof (msg as any).preset === "string" ? (msg as any).preset : undefined,
                        cameraSnapshot:
                            (msg as any).camera_snapshot && typeof (msg as any).camera_snapshot === "object"
                                ? (msg as any).camera_snapshot
                                : undefined,
                    });
                    if (typeof imageExportResult === "string" && imageExportResult) {
                        sendToPython({
                            event: "image_export",
                            data_uri: imageExportResult,
                            scale: typeof (msg as any).scale === "number" ? (msg as any).scale : 1,
                            transparent: !!(msg as any).transparent,
                            preset: typeof (msg as any).preset === "string" ? (msg as any).preset : "current",
                            width: typeof (msg as any).width === "number" ? (msg as any).width : undefined,
                            height: typeof (msg as any).height === "number" ? (msg as any).height : undefined,
                            format: "png",
                        });
                    } else if (imageExportResult && typeof imageExportResult === "object" && (imageExportResult as any).success === false) {
                        sendToPython({
                            event: "image_export",
                            ...imageExportResult,
                            scale: typeof (msg as any).scale === "number" ? (msg as any).scale : 1,
                            transparent: !!(msg as any).transparent,
                            preset: typeof (msg as any).preset === "string" ? (msg as any).preset : "current",
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

            if (popupSourceTimer) {
                window.clearTimeout(popupSourceTimer);
                popupSourceTimer = null;
            }
            rejectPendingPopupSource?.(new Error("MolSysViewer widget disposed while waiting for popup source"));
            pendingPopupSource = null;
            resolvePendingPopupSource = null;
            rejectPendingPopupSource = null;

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
            popupMgr.dispose();
            arrayNativeStream.dispose();
        };
    },
};
