// src/popup/popup-logic.ts

import {
    decodePopupEvent,
    encodePopupMessage,
    isPopupChannelIdentity,
} from "../messages/popup-channel";
import {
    RUNTIME_PROTOCOL_VERSION,
    RuntimeMessageRouter,
    type RuntimeDirection,
    type RuntimeEnvelope,
} from "../messages/runtime-router";
import { ArrayNativeStreamReceiver } from "../messages/array-native-stream";
import { popupActionAllows } from "../messages/runtime-actions";

/**
 * This function contains the entire logic that runs INSIDE the popup window.
 * IMPORTANT: This function is serialized via .toString() and executed in a separate window context.
 * Therefore, it MUST NOT rely on any external closure variables, imports, or scope from this file.
 * It can only use:
 * 1. Standard browser APIs (window, document, etc.)
 * 2. Variables explicitly injected into the popup's window object (e.g. window.molsysviewer_path)
 * 3. Globals exposed by the viewer bundle loaded inside the popup (e.g. window.MolSysViewerController)
 */
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
        if (!openerWin || openerWin.closed) return;
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
        const origin = window.location?.origin;
        const targetOrigin = origin && origin !== "null" ? origin : "*";
        try { openerWin.postMessage(encodePopupMessage(popupChannel, envelope), targetOrigin); } catch (e) {}
    };

    // Inject minimal styles for the trajectory slider to match the host look
    const injectSliderStyles = () => {
        if (document.getElementById("molsysviewer-pop-slider-style")) return;
        const css = `
            .molsysviewer-slider {
                background: transparent;
                height: 16px;
                border-radius: 999px;
                overflow: visible;
            }
            .molsysviewer-slider::-webkit-slider-runnable-track {
                background: rgba(200,200,200,0.35) !important;
                height: 16px;
                border-radius: 999px;
            }
            .molsysviewer-slider::-moz-range-track {
                background: rgba(200,200,200,0.35) !important;
                height: 16px;
                border-radius: 999px;
            }
            .molsysviewer-slider::-ms-track {
                background: rgba(200,200,200,0.35) !important;
                height: 16px;
                border-radius: 999px;
                border: none;
                color: transparent;
            }
            .molsysviewer-slider::-webkit-slider-thumb {
                -webkit-appearance: none !important;
                appearance: none !important;
                width: 16px;
                height: 16px;
                border-radius: 50% !important;
                background: rgb(80,80,80) !important;
                border: none !important;
                box-shadow: none !important;
                margin-top: 0px;
            }
            .molsysviewer-slider::-moz-range-thumb {
                width: 16px;
                height: 16px;
                border-radius: 50% !important;
                background: rgb(80,80,80) !important;
                border: none !important;
            }
            .molsysviewer-slider::-ms-thumb {
                width: 16px;
                height: 16px;
                border-radius: 50% !important;
                background: rgb(80,80,80) !important;
                border: none !important;
            }
        `;
        const el = document.createElement("style");
        el.id = "molsysviewer-pop-slider-style";
        el.textContent = css;
        document.head.appendChild(el);
    };
    injectSliderStyles();

    const container = document.getElementById("molsysviewer-pop");
    const loading = document.getElementById("molsysviewer-loading");
    let isUserInteracting = false; // Only send camera updates when user is interacting
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
            window.setTimeout(() => {
                try { loading.remove(); } catch (e) {}
            }, 300);
        }
    };

    const revealTimer = window.setTimeout(revealViewer, 2500);

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
        }, undefined, initOptions);

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

            const c3d = ctrl.plugin.canvas3d!;
            let popCameraSyncTimer: any = null;

            // Define the sync function
            const syncCamera = () => {
                // Crucial: Only sync if the change comes from USER INTERACTION
                if (!isUserInteracting) return;
                
                if (popCameraSyncTimer) clearTimeout(popCameraSyncTimer);
                popCameraSyncTimer = setTimeout(() => {
                    sendToHost("molsysviewer-sync-camera", ctrl.getCameraSnapshot());
                    popCameraSyncTimer = null;
                }, 20);
            };

            // Use didDraw for interactive camera synchronization as it's directly tied to rendering updates.
            if (c3d.didDraw) {
                c3d.didDraw.subscribe(syncCamera);
                console.log("MolSysViewer Popout: Sync via didDraw (interactive camera movements).");
            } else {
                console.warn("MolSysViewer Popout: didDraw event not found for sync.");
            }
        });

        return ctrl;
    })();

    // Logic to handle incoming messages
    window.addEventListener("message", async (ev) => {
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
        const type = routed.envelope.action;
        const data: any = routed.envelope.payload;
        // We need to await the controller promise created above
        const ctrl = await popControllerPromise;

        try {
            switch (type) {
                case "molsysviewer-initial-sync":
                    // Before the messages: the subpanels render as the summaries
                    // arrive, and System needs its hierarchy to be there already.
                    if (Array.isArray(data.hierarchyItems)) {
                        ctrl.setHierarchyItems(data.hierarchyItems);
                    }
                    if (Array.isArray(data.messages)) {
                        for (const msg of data.messages) {
                            await ctrl.handleMessage(msg);
                        }
                    }
                    if (data.cameraSnapshot) {
                        ctrl.setCameraSnapshot(data.cameraSnapshot, 0);
                    }
                    if (data.isSpinActive) await ctrl.toggleSpin(true);
                    if (data.isSwingActive) await ctrl.toggleSwing(true);
                    if (data.isDarkMode) await ctrl.toggleBackground("dark");
                    
                    // Sync UI state
                    if (data.viewerMode) ctrl.setViewerMode(data.viewerMode);
                    if (data.controlsMode) ctrl.setControlsMode(data.controlsMode);
                    if (data.panelModeStyle) ctrl.setPanelModeStyle(data.panelModeStyle);
                    if (ctrl.sharedShell) {
                        if (data.isAmbient !== undefined) ctrl.sharedShell.setAmbient(data.isAmbient);
                        if (data.isSplit !== undefined) ctrl.sharedShell.setSplit(data.isSplit);
                    }

                    // Sync autohide state
                    if (data.autohide !== undefined) updateAutohide(!!data.autohide);
                    window.clearTimeout(revealTimer);
                    revealViewer();
                    break;

                case "molsysviewer-sync-ui":
                    if (data.viewerMode) ctrl.setViewerMode(data.viewerMode);
                    if (data.controlsMode) ctrl.setControlsMode(data.controlsMode);
                    if (data.panelModeStyle) ctrl.setPanelModeStyle(data.panelModeStyle);
                    if (ctrl.sharedShell) {
                        if (data.isAmbient !== undefined) ctrl.sharedShell.setAmbient(data.isAmbient);
                        if (data.isSplit !== undefined) ctrl.sharedShell.setSplit(data.isSplit);
                    }
                    break;

                case "molsysviewer-sync-autohide":
                    updateAutohide(!!data.enabled);
                    break;

                case "molsysviewer-sync-op":
                    await ctrl.handleMessage(data);
                    break;

                case "molsysviewer-sync-hierarchy":
                    // The host's structure changed; adopt the hierarchy it derived.
                    if (Array.isArray(data?.items)) ctrl.setHierarchyItems(data.items);
                    break;

                case "molsysviewer-sync-camera":
                    // Apply host camera update only if user is NOT fighting it
                    if (data && !isUserInteracting) {
                        ctrl.setCameraSnapshot(data, 0);
                    }
                    break;

                // D4: Python streams this popup its own typed molecular
                // generation; the host only relays. Acknowledgements travel back
                // the same way, so the stream stays flow-controlled end to end.
                case "molsysviewer-structure-data":
                    await arrayNativeStream.handle(data?.message, relayedBuffers(data));
                    break;
            }
        } catch (e) {
            console.error("Popout sync error", e);
        }
    });

    // Re-implement button making helper inside popup scope
    const makeBtn = (label: string, onClick: () => void) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = label;
        btn.style.padding = "2px 6px";
        btn.style.fontSize = "11px";
        btn.style.lineHeight = "16px";
        btn.style.height = "22px";
        btn.style.minHeight = "22px";
        btn.style.boxSizing = "border-box";
        btn.style.display = "inline-flex";
        btn.style.alignItems = "center";
        btn.style.justifyContent = "center";
        btn.style.border = "1px solid rgba(255,255,255,0.5)";
        btn.style.borderRadius = "4px";
        btn.style.background = "rgba(0,0,0,0.5)";
        btn.style.color = "#fff";
        btn.style.cursor = "pointer";
        btn.addEventListener("click", onClick);
        return btn;
    };

    const overlay = document.createElement("div");
    overlay.className = "molsysviewer-controls";
    overlay.style.position = "absolute";
    overlay.style.top = "8px";
    overlay.style.right = "8px";
    overlay.style.display = "flex";
    overlay.style.gap = "6px";
    overlay.style.zIndex = "10";
    overlay.style.pointerEvents = "none";
    overlay.style.flexWrap = "nowrap";
    // Add transition for smooth autohide
    overlay.style.transition = "opacity 150ms ease";

    const addBtn = (label: string, handler: () => void): HTMLButtonElement | undefined => {
        if (initOptions.isPanelOnly) return undefined;
        const b = makeBtn(label, handler);
        b.style.pointerEvents = "auto";
        overlay.appendChild(b);
        return b;
    };

    // ... (Button definitions remain same) ...

    // Autohide Logic for Popup
    let autohide = false; // Default state, will be synced from host
    
    const applyShow = (visible: boolean) => {
        if (autohide) {
            overlay.style.opacity = visible ? "1" : "0";
            overlay.style.pointerEvents = visible ? "auto" : "none";
        } else {
            overlay.style.opacity = "1";
            overlay.style.pointerEvents = "auto";
        }
    };

    const onEnter = () => applyShow(true);
    const onLeave = () => applyShow(false);

    const updateAutohide = (enabled: boolean) => {
        if (enabled === autohide) return;
        autohide = enabled;
        
        if (autohide) {
            // Enable listeners
            container?.addEventListener("pointerenter", onEnter);
            container?.addEventListener("pointerleave", onLeave);
            applyShow(false); // Initially hide until enter
        } else {
            // Disable listeners
            container?.removeEventListener("pointerenter", onEnter);
            container?.removeEventListener("pointerleave", onLeave);
            applyShow(true); // Always show
        }
    };

    // ... (Logic to handle incoming messages - update switch) ...
    // Insert this case into the existing switch(type) block in the message listener:
    /*
                case "molsysviewer-sync-autohide":
                    updateAutohide(!!data.enabled);
                    break;
                
                case "molsysviewer-initial-sync":
                    // ... (existing sync logic) ...
                    if (data.autohide !== undefined) updateAutohide(!!data.autohide);
                    break;
    */
    // I will apply the changes to the message listener below in a separate replacement block or merge logic.
    
    addBtn("Reset", async () => {
        sendToHost("molsysviewer-sync-op", { op: "reset_view" });
    });
    addBtn("Full", async () => {
        const ctrl = await popControllerPromise;
        ctrl.toggleFullscreen();
    });
    addBtn("Bg", async () => {
        sendToHost("molsysviewer-sync-op", { op: "toggle_background" });
    });
    addBtn("Spin", async () => {
        sendToHost("molsysviewer-sync-op", { op: "toggle_spin" });
    });
    addBtn("Swing", async () => {
        sendToHost("molsysviewer-sync-op", { op: "toggle_swing" });
    });
    let isUiVisible = true;
    const uiBtn = addBtn("UI", async () => {
        const ctrl = await popControllerPromise;
        isUiVisible = !isUiVisible;
        ctrl.sharedShell?.setVisible(isUiVisible);
        if (uiBtn) uiBtn.style.background = isUiVisible ? "rgba(0,0,0,0.5)" : "rgba(239,68,68,0.6)";
    });
    addBtn("Pop", () => {
        try { window.close(); } catch (e) {}
    });
    if (initOptions.isPanelOnly) {
        overlay.style.display = "none";
    }
    container?.appendChild(overlay);

    // ... (Trajectory controls creation) ...


    // Trajectory controls (as an extension of the top-right buttons)
    const traj = document.createElement("div");
    traj.style.display = "none"; // show only for multi-structure systems
    traj.style.alignItems = "center";
    traj.style.gap = "6px";
    traj.style.pointerEvents = "auto";
    traj.style.marginLeft = "6px";

    let currentStep = 1;
    let currentFps = 30;

    const btnPrev = makeBtn("−", async () => {
        sendToHost("molsysviewer-sync-op", { op: "step_trajectory", by: -currentStep });
    });
    
    const btnPlayPause = makeBtn("▶", async () => {
        const ctrl = await popControllerPromise;
        const isPlaying = ctrl.trajectory.getTrajectoryState().isPlaying; // Get current state
        if (isPlaying) {
            sendToHost("molsysviewer-sync-op", { op: "set_trajectory_playback", action: "stop" });
        } else {
            sendToHost("molsysviewer-sync-op", { op: "set_trajectory_playback", action: "play", fps: currentFps, step: currentStep });
        }
    });
    btnPlayPause.style.paddingTop = "0px";
    btnPlayPause.style.paddingBottom = "0px";
    btnPlayPause.style.lineHeight = "18px";
    btnPlayPause.style.minWidth = "28px";
    btnPlayPause.style.width = "28px";
    btnPlayPause.title = "Play/Pause Trajectory";

    const btnNext = makeBtn("+", async () => {
        sendToHost("molsysviewer-sync-op", { op: "step_trajectory", by: currentStep });
    });

    [btnPrev, btnPlayPause, btnNext].forEach(b => {
        b.style.pointerEvents = "auto";
    });

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "0";
    slider.value = "0";
    slider.className = "molsysviewer-slider";
    slider.style.width = "160px";
    slider.style.flex = "0 0 160px";
    slider.style.pointerEvents = "auto";
    slider.style.appearance = "none";
    (slider.style as any).WebkitAppearance = "none";
    (slider.style as any).MozAppearance = "none";
    slider.style.setProperty("accent-color", "transparent");
    const updateSliderBg = () => {
        const track = "rgba(200,200,200,0.35)";
        slider.style.background = track;
    };
    slider.oninput = async () => {
        const val = Number(slider.value);
        if (!Number.isFinite(val)) return;
        sendToHost("molsysviewer-sync-op", { op: "set_trajectory_frame", index: val });
        updateSliderBg();
    };

    const label = document.createElement("span");
    label.style.color = "rgba(0,0,0,0.55)";
    label.style.fontSize = "11px";
    label.style.minWidth = "60px";
    label.style.textAlign = "center";
    label.style.padding = "0px";
    label.style.height = "16px";
    label.style.lineHeight = "16px";
    label.style.boxSizing = "border-box";
    label.style.border = "0";
    label.style.borderRadius = "0";
    label.style.background = "transparent";
    label.textContent = "0 / 0";

    traj.appendChild(btnPrev);
    traj.appendChild(btnPlayPause);
    traj.appendChild(btnNext);
    traj.appendChild(slider);
    traj.appendChild(label);
    
    if (initOptions.isPanelOnly) {
        traj.style.display = "none";
    } else {
        overlay.appendChild(traj);
    }

    popControllerPromise.then(c => {
        const applyState = (state: any) => {
            const frameCount = state.frameCount;
            const current = state.currentFrame;
            const isPlaying = state.isPlaying;

            traj.style.display = frameCount > 1 ? "flex" : "none";
            slider.max = frameCount > 0 ? String(frameCount - 1) : "0";
            slider.value = String(Math.min(current, frameCount > 0 ? frameCount - 1 : 0));
            updateSliderBg();
            label.textContent = frameCount > 0 ? `${current + 1} / ${frameCount}` : "0 / 0";
            const disabled = !state.hasTrajectory || frameCount <= 1;
            [btnPrev, btnNext, slider, btnPlayPause].forEach(el => {
                (el as HTMLButtonElement | HTMLInputElement).disabled = disabled;
            });
            
            // Update Play/Pause button text
            btnPlayPause.textContent = isPlaying ? "⏸" : "▶";
            btnPlayPause.title = isPlaying ? "Pause Trajectory" : "Play Trajectory";
            overlay.style.opacity = "1";
            overlay.style.display = "flex";
        };
        c.onTrajectoryState(applyState, { immediate: false });
        const initialState = c.trajectory.getTrajectoryState();
        if (initialState.hasTrajectory || initialState.expectedFrameCount !== undefined) {
            applyState(initialState);
        }
    });

    // Notify host
    sendToHost(initOptions.isPanelOnly ? "molsysviewer-panel-ready" : "molsysviewer-pop-ready", null);
};
