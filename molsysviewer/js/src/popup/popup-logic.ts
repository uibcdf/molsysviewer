// src/popup/popup-logic.ts

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
        try { openerWin.postMessage({ type, data, from: "popup" }, "*"); } catch (e) {}
    };

    const container = document.getElementById("molsysviewer-pop");
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
    
    // Create a new instance of MolSysViewerController for the popout
    const popControllerPromise = (async () => {
        // Wait a tick to ensure DOM is ready
        await new Promise(r => setTimeout(r, 100));

        const ctrl = await MolSysViewerController.create(container, (msg: any) => {
            sendToHost("molsysviewer-log-from-popout", msg);
        });

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
        if (!ev.data || ev.data.from === "popup") return;
        const { type, data } = ev.data;
        // We need to await the controller promise created above
        const ctrl = await popControllerPromise;

        try {
            switch (type) {
                case "molsysviewer-initial-sync":
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
                    break;

                case "molsysviewer-sync-op":
                    await ctrl.handleMessage(data);
                    break;

                case "molsysviewer-sync-camera":
                    // Apply host camera update only if user is NOT fighting it
                    if (data && !isUserInteracting) {
                        ctrl.setCameraSnapshot(data, 0);
                    }
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

    const addBtn = (label: string, handler: () => void) => {
        const b = makeBtn(label, handler);
        b.style.pointerEvents = "auto";
        overlay.appendChild(b);
    };

    addBtn("Reset", async () => {
        const ctrl = await popControllerPromise;
        await ctrl.resetView();
        sendToHost("molsysviewer-sync-op", { op: "reset_view" });
    });
    addBtn("Full", async () => {
        const ctrl = await popControllerPromise;
        ctrl.toggleFullscreen();
    });
    addBtn("Bg", async () => {
        const ctrl = await popControllerPromise;
        await ctrl.toggleBackground();
        sendToHost("molsysviewer-sync-op", { op: "toggle_background", mode: ctrl.isDarkMode ? "dark" : "light" });
    });
    addBtn("Spin", async () => {
        const ctrl = await popControllerPromise;
        await ctrl.toggleSpin();
        sendToHost("molsysviewer-sync-op", { op: "toggle_spin", enable: ctrl.isSpinActive });
    });
    addBtn("Swing", async () => {
        const ctrl = await popControllerPromise;
        await ctrl.toggleSwing();
        sendToHost("molsysviewer-sync-op", { op: "toggle_swing", enable: ctrl.isSwingActive });
    });
    addBtn("Pop", () => {
        try { window.close(); } catch (e) {}
    });
    container.appendChild(overlay);

    // Trajectory controls
    const traj = document.createElement("div");
    traj.style.position = "absolute";
    traj.style.left = "8px";
    traj.style.bottom = "8px";
    traj.style.display = "flex";
    traj.style.alignItems = "center";
    traj.style.gap = "6px";
    traj.style.pointerEvents = "auto";

    let currentStep = 1;
    let currentFps = 30;

    const btnPrev = makeBtn("−", async () => {
        const ctrl = await popControllerPromise;
        ctrl.stepTrajectory(-currentStep);
        sendToHost("molsysviewer-sync-op", { op: "step_trajectory", by: -currentStep });
    });
    const btnPlay = makeBtn("▶", async () => {
        const ctrl = await popControllerPromise;
        ctrl.playTrajectory({ fps: currentFps, step: currentStep });
        sendToHost("molsysviewer-sync-op", { op: "set_trajectory_playback", action: "play", fps: currentFps, step: currentStep });
    });
    const btnPause = makeBtn("⏸", async () => {
        const ctrl = await popControllerPromise;
        ctrl.stopTrajectoryPlayback();
        sendToHost("molsysviewer-sync-op", { op: "set_trajectory_playback", action: "stop" });
    });
    const btnNext = makeBtn("+", async () => {
        const ctrl = await popControllerPromise;
        ctrl.stepTrajectory(currentStep);
        sendToHost("molsysviewer-sync-op", { op: "step_trajectory", by: currentStep });
    });

    [btnPrev, btnPlay, btnPause, btnNext].forEach(b => {
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
    slider.oninput = async () => {
        const val = Number(slider.value);
        if (!Number.isFinite(val)) return;
        const ctrl = await popControllerPromise;
        ctrl.setTrajectoryFrame(val);
        sendToHost("molsysviewer-sync-op", { op: "set_trajectory_frame", index: val });
    };

    const label = document.createElement("span");
    label.style.color = "rgba(255,255,255,0.8)";
    label.style.fontSize = "11px";
    label.style.minWidth = "60px";
    label.style.textAlign = "center";
    label.textContent = "0 / 0";

    traj.appendChild(btnPrev);
    traj.appendChild(btnPlay);
    traj.appendChild(btnPause);
    traj.appendChild(btnNext);
    traj.appendChild(slider);
    traj.appendChild(label);
    container.appendChild(traj);

    popControllerPromise.then(c => {
        c.onTrajectoryState(state => {
            var frameCount = state && typeof state.frameCount === "number" ? state.frameCount : 0;
            var current = state && typeof state.currentFrame === "number" ? state.currentFrame : 0;
            slider.max = frameCount > 0 ? String(frameCount - 1) : "0";
            slider.value = String(Math.min(current, frameCount > 0 ? frameCount - 1 : 0));
            label.textContent = frameCount > 0 ? `${current + 1} / ${frameCount}` : "0 / 0";
            var disabled = frameCount <= 1;
            [btnPrev, btnNext, slider, btnPlay, btnPause].forEach(function (el) {
              el.disabled = disabled;
            });
        });
    });

    // Notify host
    sendToHost("molsysviewer-pop-ready", null);
};
