// src/popup/popup-logic.ts

import {
    decodePopupEvent,
    encodePopupMessage,
    isPopupChannelIdentity,
    popupTargetOrigin,
} from "../messages/popup-channel";
import {
    RUNTIME_PROTOCOL_VERSION,
    RuntimeMessageRouter,
    type RuntimeDirection,
    type RuntimeEnvelope,
} from "../messages/runtime-router";
import { ArrayNativeStreamReceiver } from "../messages/array-native-stream";
import { popupActionAllows } from "../messages/runtime-actions";
import { mountControls } from "../ui/controls";
import { createLocalUiModel } from "../ui/local-ui-model";
import { CameraSync, CameraSyncState } from "../managers/camera-sync";
import { trajectorySyncToAuthority } from "../messages/trajectory-intent";
import { handleFrontendRequest, isFrontendControl, isFrontendRequest, isStudioWorkFileResult,
    VisualStateCaptureRequests, captureAtScenePrefix, type VisualStateCaptureReservation } from "../messages/frontend-requests";

/** Boot the popup through the same imported runtime module as its host. */
export const bootPopup = async (loadedModule?: any) => {
    const openerWin = window.opener;
    if (!openerWin) {
        console.error("MolSysViewer Popout: Opened without opener");
        return;
    }

    const initOptions = (window as any).molsysviewer_init_options || {};
    const popupChannel = (window as any).molsysviewer_popup_channel;
    if (!isPopupChannelIdentity(popupChannel)) {
        console.error("MolSysViewer Popout: Missing secure popup channel identity");
        return;
    }
    const runtimeRouter = new RuntimeMessageRouter(
        popupChannel.viewerId,
        popupChannel.sessionId,
    );
    runtimeRouter.registerEndpoint({
        endpointId: popupChannel.authorityEndpointId,
        role: "python",
    });
    runtimeRouter.registerEndpoint({
        endpointId: popupChannel.hostEndpointId,
        role: "widget-host",
    });
    runtimeRouter.registerEndpoint({
        endpointId: popupChannel.popupEndpointId,
        role: popupChannel.mode === "canvas" ? "canvas-popup" : "panel-popup",
    });
    let popupMessageCounter = 0;
    let popupDisposed = false;
    const visualStateCaptures = new VisualStateCaptureRequests();
    const cameraSyncState = new CameraSyncState();
    
    // Load the viewer module dynamically using the global path set by the opener
    let MolSysViewerController;
    
    // If module is passed directly (preferred), use it. Otherwise try to load it.
    if (loadedModule) {
        if (loadedModule.MolSysViewerController) {
            MolSysViewerController = loadedModule.MolSysViewerController;
        } else if (loadedModule.default && loadedModule.default.MolSysViewerController) {
            MolSysViewerController = loadedModule.default.MolSysViewerController;
        }
    }

    if (!MolSysViewerController) {
        try {
            // @ts-ignore: window.molsysviewer_path is injected by the host
            const path = (window as any).molsysviewer_path;
            if (path) {
                const module = await import(path);
                
                if (module.MolSysViewerController) {
                    MolSysViewerController = module.MolSysViewerController;
                } else if (module.default && module.default.MolSysViewerController) {
                    MolSysViewerController = module.default.MolSysViewerController;
                } else if ((window as any).MolSysViewerController) {
                    MolSysViewerController = (window as any).MolSysViewerController;
                }
            }
        } catch (err) {
            console.error("MolSysViewer Popout: Failed to load viewer module", err);
            return;
        }
    }
    
    if (!MolSysViewerController) {
        // Last ditch effort: check global
        MolSysViewerController = (window as any).MolSysViewerController;
    }

    if (!MolSysViewerController) {
        console.error("MolSysViewer Popout: MolSysViewerController not found");
        return;
    }

    const sendToHost = (type: string, data: any) => {
        if (popupDisposed || !openerWin || openerWin.closed) return;
        const direction: RuntimeDirection =
            type === "molsysviewer-sync-op"
            || type === "molsysviewer-popup-interaction"
                ? "command"
                : "event";
        const envelope: RuntimeEnvelope = {
            protocolVersion: RUNTIME_PROTOCOL_VERSION,
            viewerId: popupChannel.viewerId,
            sessionId: popupChannel.sessionId,
            endpointId: popupChannel.popupEndpointId,
            targetEndpointId:
                direction === "command"
                    ? popupChannel.authorityEndpointId
                    : popupChannel.hostEndpointId,
            messageId: `${popupChannel.popupEndpointId}:${++popupMessageCounter}`,
            direction,
            action: type,
            payload: data,
        };
        if (runtimeRouter.route(envelope).status !== "accepted") return;
        const targetOrigin = popupTargetOrigin(window.location);
        try { openerWin.postMessage(encodePopupMessage(popupChannel, envelope), targetOrigin); } catch (e) {}
    };

    const container = document.getElementById("molsysviewer-pop");
    if (container) {
        container.tabIndex = 0;
        Object.assign(container.style, { touchAction: "none", outline: "none", cursor: "default" });
    }
    let loading = document.getElementById("molsysviewer-loading");
    let loadingRemoval: number | undefined;
    let sceneReady = false;
    let cameraSync: CameraSync | undefined;
    let isUserInteracting = false; // Local input has priority over incoming viewpoints.
    let wheelTimeout: any = null;

    // Track user interaction state
    container?.addEventListener("pointerdown", () => { isUserInteracting = true; });
    window.addEventListener("pointerup", () => { isUserInteracting = false; });
    window.addEventListener("pointercancel", () => { isUserInteracting = false; });
    
    // Track wheel (zoom) interaction
    container?.addEventListener("wheel", () => {
        isUserInteracting = true;
        if (wheelTimeout) clearTimeout(wheelTimeout);
        wheelTimeout = setTimeout(() => { isUserInteracting = false; }, 200);
    }, { passive: true });
    
    const revealViewer = () => {
        if (container) {
            container.style.opacity = "1";
        }
        if (loading) {
            loading.style.opacity = "0";
            loading.style.pointerEvents = "none";
            const completed = loading;
            loadingRemoval = window.setTimeout(() => {
                try { completed.remove(); } catch (e) {}
                if (loading === completed) loading = null;
                loadingRemoval = undefined;
            }, 300);
        }
    };

    const showBootstrapState = (failed: boolean) => {
        sceneReady = false;
        if (loadingRemoval !== undefined) window.clearTimeout(loadingRemoval);
        loadingRemoval = undefined;
        if (!loading) {
            loading = document.createElement("div");
            loading.id = "molsysviewer-loading";
            document.body.appendChild(loading);
        }
        loading.textContent = "";
        loading.role = failed ? "alert" : "status";
        loading.style.opacity = "1";
        loading.style.pointerEvents = "auto";
        if (!failed) {
            const spinner = document.createElement("div");
            spinner.className = "spinner";
            loading.appendChild(spinner);
        }
        const text = document.createElement("div");
        text.textContent = failed ? "Your scene could not be loaded. You can try again." : "Loading your scene…";
        loading.appendChild(text);
        if (failed) {
            const retry = document.createElement("button");
            retry.type = "button";
            retry.textContent = "Try again";
            retry.addEventListener("click", () => {
                retry.disabled = true;
                showBootstrapState(false);
                sendToHost(initOptions.isPanelOnly ? "molsysviewer-panel-ready" : "molsysviewer-pop-ready", null);
            }, { once: true });
            loading.appendChild(retry);
        }
    };

    // D4: this popup assembles its own typed molecular generation from the
    // chunks Python addressed to it (the host only relays). Acknowledgements go
    // back through the host, so the one-chunk-in-flight discipline holds end to
    // end and nobody keeps a spare full copy of the coordinates.
    const relayedBuffers = (payload: any): DataView[] => {
        const buffers = payload?.buffers;
        if (!Array.isArray(buffers)) return [];
        return buffers.map((buffer: any) =>
            buffer instanceof DataView
                ? buffer
                : new DataView(
                    buffer.buffer ?? buffer,
                    buffer.byteOffset ?? 0,
                    buffer.byteLength ?? (buffer.buffer ?? buffer).byteLength,
                ),
        );
    };
    const arrayNativeStream = new ArrayNativeStreamReceiver(
        event => sendToHost("molsysviewer-structure-data-ack", event),
        async (begin, payload) => {
            const ctrl = await popControllerPromise;
            await ctrl.loadArrayNativeMolSysPayload(payload, begin.label);
        },
    );

    let applyingHostState = false;
    let pendingUiSave = false;
    const uiModel = createLocalUiModel({
        viewer_mode: initOptions.viewerMode || "standard",
        controls_mode: initOptions.controlsMode || "compact",
        panel_mode_style: initOptions.panelModeStyle || "integrated",
        ...initOptions.uiState,
        // A separate Studio window always uses its own split shell.
        ...(initOptions.isPanelOnly ? { panel_mode_style: "split" } : {}),
    }, () => {
        if (applyingHostState || pendingUiSave) return;
        pendingUiSave = true;
        queueMicrotask(() => {
            pendingUiSave = false;
            if (!applyingHostState) sendToHost("molsysviewer-popup-ui", ctrlUiState());
        });
    });
    const ctrlUiState = () => Object.fromEntries([
        "viewer_mode", "controls_mode", "panel_mode_style", "show_controls", "autohide_controls",
        "autohide_scope", "controls_position", "controls_position_fullscreen",
    ].filter(trait => !initOptions.isPanelOnly || trait !== "panel_mode_style")
        .map(trait => [trait, uiModel.get(trait)]));
    const updateControlsUi = (data: any) => {
        for (const [field, trait] of Object.entries({
            autohide: "autohide_controls", autohideScope: "autohide_scope", showControls: "show_controls",
            controlsPosition: "controls_position", controlsPositionFullscreen: "controls_position_fullscreen",
        })) if (data[field] !== undefined) uiModel.set(trait, data[field]);
    };
    // The notebook adopts the panel window, but this canvas owns the shell
    // being detached. Its return observer must have this endpoint's lifetime.
    let detachedPanelWindow: Window | null = null;
    let panelReturnTimer: number | undefined;
    const stopPanelReturnObserver = () => {
        if (panelReturnTimer !== undefined) window.clearInterval(panelReturnTimer);
        panelReturnTimer = undefined;
        detachedPanelWindow = null;
    };
    // Create a new instance of MolSysViewerController for the popout
    const popControllerPromise = (async () => {
        // Wait a tick to ensure DOM is ready
        await new Promise(r => setTimeout(r, 100));

        const ctrl = await MolSysViewerController.create(container, (msg: any) => {
            // Forward all interaction and context action events to the host so Python receives and executes them
            if (msg && typeof msg === "object" && typeof msg.event === "string") {
                sendToHost("molsysviewer-popup-interaction", msg);
            } else {
                sendToHost("molsysviewer-log-from-popout", msg);
            }
        }, undefined, { ...initOptions, model: uiModel,
            onPanelPopClick: initOptions.enablePanelPopout && !initOptions.isPanelOnly
                ? () => {
                    if (openerWin.closed) return;
                    const size = ctrl.getPanelPopupSize();
                    // Reserve on the click itself; a later postMessage handler
                    // cannot rely on the browser retaining user activation.
                    const reserved = window.open(
                        "", "_blank", `width=${size.width},height=${size.height}`);
                    if (!reserved) return; // A blocked popup must leave Studio usable.
                    stopPanelReturnObserver();
                    detachedPanelWindow = reserved;
                    ctrl.saveHostPanelState();
                    ctrl.setCanvasVisibility(true);
                    ctrl.sharedShell?.setVisible(false);
                    panelReturnTimer = window.setInterval(() => {
                        if (!reserved.closed) return;
                        stopPanelReturnObserver();
                        ctrl.restoreHostPanelState();
                    }, 1000);
                    (window as any).__molsysviewer_pending_panel_window = reserved;
                    sendToHost("molsysviewer-popup-panel", { panel: ctrl.getActivePanel() });
                } : undefined,
        });

        ctrl.setCameraMotionFollower?.(true);
        ctrl.setTrajectoryFollower?.(true);
        ctrl.onTogglePanelModeOverride = () => {
            if (!detachedPanelWindow || detachedPanelWindow.closed) return false;
            detachedPanelWindow.close();
            return true;
        };
        if (initOptions.isPanelOnly) {
            ctrl.setCanvasVisibility(false);
            if (ctrl.sharedShell) {
                ctrl.sharedShell.setSplit(true);
                ctrl.sharedShell.setVisible(true);
            }
            const activePanel = initOptions.activePanel || "navigate";
            void ctrl.handleMessage({ op: "set_panel_mode", panel: activePanel, expanded: true });
        }

        // Helper to wait for canvas3d to be ready (async init)
        const waitForCanvas3d = async (retries = 50): Promise<boolean> => {
            for (let i = 0; i < retries; i++) {
                if (ctrl.plugin?.canvas3d) return true; // Only need canvas3d to exist for didDraw
                
                if (i % 10 === 0) {
                    console.log(`[Popout] Waiting for Canvas3D... (${i}/${retries})`, {
                        plugin: !!ctrl.plugin,
                        canvas3d: !!ctrl.plugin?.canvas3d
                    });
                }
                await new Promise(r => setTimeout(r, 100));
            }
            return false;
        };

        // Initialize sync logic once canvas is ready
        waitForCanvas3d().then((ready) => {
            if (!ready) {
                console.warn("MolSysViewer Popout: Canvas3D failed to initialize after timeout (visuals may work but sync won't).");
                return;
            }

            cameraSync = new CameraSync(ctrl, {
                enabled: () => sceneReady && !initOptions.isPanelOnly,
                interacting: () => isUserInteracting,
                send: snapshot => sendToHost("molsysviewer-sync-camera", snapshot),
            }, cameraSyncState);

        });

        return ctrl;
    })();

    // Logic to handle incoming messages
    const acceptPopupMessage = (ev: MessageEvent) => {
        const message = decodePopupEvent(ev, openerWin, popupChannel);
        if (!message) return;
        if (
            message.envelope.endpointId !== popupChannel.authorityEndpointId
            && message.envelope.endpointId !== popupChannel.hostEndpointId
        ) return;
        const routed = runtimeRouter.route(message.envelope);
        if (routed.status !== "accepted") return;
        if (!popupActionAllows(routed.envelope.action, routed.envelope.direction)) {
            sendToHost("molsysviewer-runtime-contract-rejected", {
                seam: "popup-inbound",
                reason: "undeclared-popup-action",
                detail: `${routed.envelope.action}:${routed.envelope.direction}`,
            });
            console.warn(
                `[MolSysViewer Popup] refused host action ${routed.envelope.action} `
                + `as ${routed.envelope.direction}: not declared in runtime_actions.json`,
            );
            return;
        }
        const type = routed.envelope.action, data = routed.envelope.payload as any;
        if (type === "molsysviewer-sync-op") cameraSyncState.receive(data);
        if (type === "molsysviewer-sync-camera") cameraSyncState.receivePeer(data);
        if (type === "molsysviewer-initial-sync") {
            if (Array.isArray(data.messages)) for (const message of data.messages) cameraSyncState.receive(message);
            cameraSyncState.receiveBootstrap(data);
        }
        return { type, data };
    };
    const handlePopupMessage = async (type: string, data: any, capture?: VisualStateCaptureReservation) => {
        if (popupDisposed || capture?.signal.aborted) return;
        // We need to await the controller promise created above
        const ctrl = await popControllerPromise;
        if (popupDisposed || capture?.signal.aborted) return;

        applyingHostState = type === "molsysviewer-initial-sync"
            || type === "molsysviewer-sync-ui" || type === "molsysviewer-sync-autohide";
        try {
            switch (type) {
                case "molsysviewer-initial-sync":
                    if (data.bootstrapError || !Array.isArray(data.messages)) {
                        showBootstrapState(true);
                        break;
                    }
                    // Before the messages: the subpanels render as the summaries
                    // arrive, and System needs its hierarchy to be there already.
                    if (Array.isArray(data.hierarchyItems)) {
                        ctrl.setHierarchyItems(data.hierarchyItems);
                    }
                    if (Array.isArray(data.messages)) {
                        for (const msg of data.messages) {
                            if (!(await cameraSync?.handleMessage(msg))) await ctrl.handleMessage(msg);
                        }
                    }
                    if (Number.isInteger(data.trajectoryFrame) && data.trajectoryFrame >= 0) {
                        await ctrl.handleMessage({ op: "set_trajectory_frame", index: data.trajectoryFrame,
                            box_display: data.boxDisplay, playback_projection: data.playback,
                            navigation_revision: data.navigationRevision });
                    }
                    if (data.cameraSnapshot) {
                        await cameraSync?.applyBootstrap(data);
                    }
                    if (data.isSpinActive) await ctrl.toggleSpin(true);
                    if (data.isSwingActive) await ctrl.toggleSwing(true);
                    if (data.isDarkMode) await ctrl.toggleBackground("dark");
                    
                    // Sync UI state
                    if (data.viewerMode) ctrl.setViewerMode(data.viewerMode);
                    if (data.controlsMode) ctrl.setControlsMode(data.controlsMode);
                    if (initOptions.isPanelOnly) ctrl.setPanelModeStyle("split");
                    else if (data.panelModeStyle) ctrl.setPanelModeStyle(data.panelModeStyle);
                    if (ctrl.sharedShell) {
                        if (data.isAmbient !== undefined) ctrl.sharedShell.setAmbient(data.isAmbient);
                        if (initOptions.isPanelOnly) ctrl.sharedShell.setSplit(true);
                        else if (data.isSplit !== undefined) ctrl.sharedShell.setSplit(data.isSplit);
                    }

                    // Sync autohide state
                    updateControlsUi(data);
                    revealViewer();
                    sceneReady = true;
                    break;

                case "molsysviewer-sync-ui":
                    updateControlsUi(data);
                    if (data.viewerMode) ctrl.setViewerMode(data.viewerMode);
                    if (data.controlsMode) ctrl.setControlsMode(data.controlsMode);
                    if (initOptions.isPanelOnly) ctrl.setPanelModeStyle("split");
                    else if (data.panelModeStyle) ctrl.setPanelModeStyle(data.panelModeStyle);
                    if (ctrl.sharedShell) {
                        if (initOptions.isPanelOnly) ctrl.sharedShell.setSplit(true);
                    }
                    break;

                case "molsysviewer-sync-autohide":
                    updateControlsUi({ autohide: !!data.enabled, autohideScope: data.scope });
                    break;

                case "molsysviewer-sync-op":
                    if (isFrontendRequest(data)) {
                        // The inbound queue is the canvas barrier. A detached
                        // Studio has no visible canvas and must never sample its
                        // hidden controller in place of its originating viewer.
                        if ((initOptions.isPanelOnly || !sceneReady) && data.op === "request_visual_state") {
                            capture?.release();
                            sendToHost("molsysviewer-popup-interaction", {
                                event: "visual_state_snapshot", request_id: data.request_id,
                                capture_revision: data.capture_revision, ok: false, error_type: "NoLiveCanvas",
                            });
                        } else {
                            const send = (event: any) => sendToHost("molsysviewer-popup-interaction", event);
                            if (capture) await captureAtScenePrefix(ctrl, data, send, capture);
                            else await handleFrontendRequest(ctrl, data, send);
                        }
                    } else {
                        if (!(await cameraSync?.handleMessage(data))) await ctrl.handleMessage(data);
                    }
                    break;

                case "molsysviewer-sync-hierarchy":
                    // The host's structure changed; adopt the hierarchy it derived.
                    if (Array.isArray(data?.items)) ctrl.setHierarchyItems(data.items);
                    break;

                case "molsysviewer-sync-camera":
                    // Apply host camera update only if user is NOT fighting it
                    await cameraSync?.apply(data);
                    break;

                // D4: Python streams this popup its own typed molecular
                // generation; the host only relays. Acknowledgements travel back
                // the same way, so the stream stays flow-controlled end to end.
                case "molsysviewer-structure-data":
                    if (data?.message?.op === "load_molsys_payload") {
                        await ctrl.handleMessage(data.message);
                        sendToHost("molsysviewer-structure-data-ack", {
                            event: "structure_data_json_complete",
                        });
                    } else {
                        await arrayNativeStream.handle(data?.message, relayedBuffers(data));
                    }
                    break;
            }
        } catch (e) {
            console.error("Popout sync error", e);
            if (type === "molsysviewer-initial-sync") showBootstrapState(true);
        } finally {
            applyingHostState = false;
        }
    };
    let popupInboundQueue = Promise.resolve();
    const onPopupMessage = (ev: MessageEvent) => {
        if (popupDisposed) return;
        // Authenticate and deduplicate once, before choosing a dispatch lane.
        const accepted = acceptPopupMessage(ev);
        if (!accepted) return;
        const { type, data } = accepted;
        if (type === "molsysviewer-sync-op" && isFrontendControl(data)) {
            visualStateCaptures.cancel(data);
            return;
        }
        if (type === "molsysviewer-sync-op" && isStudioWorkFileResult(data)) {
            popControllerPromise.then(ctrl => { if (!popupDisposed) return ctrl.handleMessage(data); })
                .catch(error => console.error("Popout file verdict delivery failed", error));
            return;
        }
        const capture = type === "molsysviewer-sync-op" && data?.op === "request_visual_state"
            ? visualStateCaptures.reserve(data) : undefined;
        if (capture === null) return;
        popupInboundQueue = popupInboundQueue
            .then(() => handlePopupMessage(type, data, capture))
            .finally(() => { if (data?.capture_version !== 2) capture?.release(); })
            .catch(error => { capture?.release(); console.error("Popout message queue error", error); });
    };
    window.addEventListener("message", onPopupMessage);

    // Canvas controls share mode, reveal policy and lifetime with the widget.
    // A panel-only popup has no canvas controls or hidden trajectory bar.
    const controlsProvider = loadedModule?.mountControls || mountControls;
    const ctrl = await popControllerPromise;
    if (!initOptions.isPanelOnly) controlsProvider(ctrl, uiModel,
        (msg: any) => {
            const authorityAction = trajectorySyncToAuthority(msg);
            if (authorityAction && initOptions.hasAuthority !== false) {
                sendToHost("molsysviewer-popup-interaction", authorityAction);
            } else {
                sendToHost("molsysviewer-sync-op", msg);
            }
        }, container!, () => window.close(),
        { popupButtonTitle: "Close popup" });
    window.addEventListener("pagehide", () => {
        popupDisposed = true;
        visualStateCaptures.dispose();
        window.removeEventListener("message", onPopupMessage);
        sceneReady = false;
        stopPanelReturnObserver();
        cameraSync?.dispose();
        if (wheelTimeout) clearTimeout(wheelTimeout);
        if (loadingRemoval !== undefined) window.clearTimeout(loadingRemoval);
        ctrl.dispose();
    }, { once: true });
    // Notify host
    sendToHost(initOptions.isPanelOnly ? "molsysviewer-panel-ready" : "molsysviewer-pop-ready", null);
};
