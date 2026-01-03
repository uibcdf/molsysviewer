import { MolSysViewerController } from "../managers/viewer-controller";
import { ViewerMessage } from "../messages/viewer-messages";

// Helper to send sync messages to popout
type SyncCallback = (msg: ViewerMessage) => void;

const makeButton = (label: string, onClick: () => void) => {
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
    btn.style.cursor = "default"; // Reverted from !important
    btn.style.userSelect = "none";
    btn.addEventListener("click", onClick);
    return btn;
};

const injectStyles = () => {
    if (document.getElementById("molsysviewer-traj-style")) return;
    const css = `
        .molsysviewer-controls,
        .molsysviewer-controls * {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
        }
        .molsysviewer-traj-input::-webkit-inner-spin-button,
        .molsysviewer-traj-input::-webkit-outer-spin-button {
            -webkit-appearance: none !important;
            appearance: none !important;
            -moz-appearance: none !important;
            margin: 0 !important;
        }
        .molsysviewer-traj-input {
            -moz-appearance: textfield !important;
            appearance: none !important;
            -webkit-appearance: none !important;
            color: rgba(255,255,255,0.9);
            background: rgba(40,40,40,0.6);
            caret-color: transparent;
        }
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
        .molsysviewer-slider::-webkit-slider-thumb:hover,
        .molsysviewer-slider::-webkit-slider-thumb:active,
        .molsysviewer-slider::-webkit-slider-thumb:focus {
            background: rgb(80,80,80) !important;
            border: none !important;
            box-shadow: none !important;
        }
        .molsysviewer-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50% !important;
            background: rgb(80,80,80) !important;
            border: none !important;
        }
        .molsysviewer-slider::-moz-range-thumb:hover,
        .molsysviewer-slider::-moz-range-thumb:active,
        .molsysviewer-slider::-moz-range-thumb:focus {
            background: rgba(80,80,80,0.95) !important;
            border: none !important;
        }
        .molsysviewer-slider::-ms-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50% !important;
            background: rgba(80,80,80,0.95) !important;
            border: none !important;
        }
    `;
    const el = document.createElement("style");
    el.id = "molsysviewer-traj-style";
    el.textContent = css;
    document.head.appendChild(el);
};

const makeNumberControl = (initial: number, onChange: (n: number) => void, title: string) => {
    const wrapper = document.createElement("div");
    wrapper.style.position = "relative";
    wrapper.style.display = "inline-block";
    wrapper.style.width = "52px";
    wrapper.style.height = "22px";

    const input = document.createElement("input");
    input.type = "text";
    input.value = String(initial);
    input.style.width = "52px";
    input.style.height = "22px";
    input.style.fontSize = "11px";
    input.style.boxSizing = "border-box";
    input.style.color = "rgba(255,255,255,0.9)";
    input.style.background = "rgba(40,40,40,0.6)";
    input.style.border = "1px solid rgba(255,255,255,0.55)";
    input.style.borderRadius = "4px";
    input.style.padding = "0 18px 0 4px";
    input.style.appearance = "none";
    (input.style as any).MozAppearance = "textfield";
    (input.style as any).WebkitAppearance = "none";
    input.className = "molsysviewer-traj-input";
    input.title = title;
    input.setAttribute("inputmode", "numeric");
    input.setAttribute("pattern", "[0-9]*");
    input.onchange = () => {
        const val = Number(input.value);
        const n = Number.isFinite(val) && val > 0 ? Math.floor(val) : initial;
        onChange(n);
        input.value = String(n);
    };

    const spinner = document.createElement("div");
    spinner.style.position = "absolute";
    spinner.style.top = "1px";
    spinner.style.right = "2px";
    spinner.style.width = "14px";
    spinner.style.height = "18px";
    spinner.style.display = "flex";
    spinner.style.flexDirection = "column";
    spinner.style.alignItems = "center";

    const mkArrow = (char: string, delta: number, extraTop: string = "0px") => {
        const btn = document.createElement("div");
        btn.textContent = char;
        btn.style.fontSize = "10px";
        btn.style.lineHeight = "10px";
        btn.style.height = "9px";
        btn.style.color = "#ffffff";
        btn.style.background = "transparent";
        btn.style.border = "none";
        btn.style.textAlign = "center";
        btn.style.cursor = "default"; // Changed from pointer
        btn.style.marginTop = extraTop;
        btn.onclick = () => {
            const val = Number(input.value);
            const next = Number.isFinite(val) ? val + delta : delta;
            const n = next > 0 ? Math.floor(next) : 1;
            onChange(n);
            input.value = String(n);
        };
        return btn;
    };

    const upBtn = mkArrow("▲", 1, "0px");
    const downBtn = mkArrow("▼", -1, "1px");
    spinner.appendChild(upBtn);
    spinner.appendChild(downBtn);

    wrapper.appendChild(input);
    wrapper.appendChild(spinner);
    return { wrapper, input };
};

export const buildControls = (
    c: MolSysViewerController, 
    model: any, 
    sendSync: SyncCallback,
    container: HTMLElement,
    onPopClick?: () => void,
    opts?: { initialHasTrajectory?: boolean; initialFrameCount?: number }
) => {
    injectStyles();

    const overlay = document.createElement("div");
    // ... (rest of the overlay creation code remains same until Autohide logic) ...
    overlay.className = "molsysviewer-controls";
    overlay.style.position = "absolute";
    overlay.style.display = "flex";
    overlay.style.gap = "6px";
    overlay.style.zIndex = "10";
    overlay.style.pointerEvents = "none";
    overlay.style.flexWrap = "nowrap";
    overlay.style.opacity = "0"; // Reveal after initial trajectory state to avoid flash
    overlay.style.display = "none"; // Keep hidden until we know if trajectory bar is needed

    const mk = (label: string, handler: () => void) => {
        const b = makeButton(label, handler);
        b.style.pointerEvents = "auto";
        overlay.appendChild(b);
    };

    mk("Reset", async () => {
        await c.resetView();
        sendSync({ op: "reset_view" });
    });
    mk("Full", () => c.toggleFullscreen());
    mk("Bg", async () => {
        await c.toggleBackground();
        sendSync({ op: "toggle_background", mode: c.isDarkMode ? "dark" : "light" });
    });
    mk("Spin", async () => {
        await c.toggleSpin();
        sendSync({ op: "toggle_spin", enable: c.isSpinActive });
    });
    mk("Swing", async () => {
        await c.toggleSwing();
        sendSync({ op: "toggle_swing", enable: c.isSwingActive });
    });
    if (onPopClick) mk("Pop", onPopClick);

    // Trajectory controls
    const traj = document.createElement("div");
    traj.style.display = "flex";
    traj.style.alignItems = "center";
    traj.style.gap = "6px";
    traj.style.pointerEvents = "auto";
    traj.style.marginLeft = "6px";
    traj.style.paddingLeft = "0px";
    traj.style.borderLeft = "0px";
    // Hide the trajectory bar by default; update immediately based on known state.
    traj.style.display = "none";

    let currentStep = 1;
    let currentFps = 30;

    const btnPrev = makeButton("−", () => {
        c.stepTrajectory(-currentStep);
        sendSync({ op: "step_trajectory", by: -currentStep });
    });
    
    const btnPlayPause = makeButton("▶ / ⏸", () => {
        const isPlaying = c.trajectory.getTrajectoryState().isPlaying;
        if (isPlaying) {
            c.stopTrajectoryPlayback();
            sendSync({ op: "set_trajectory_playback", action: "stop" });
        } else {
            c.playTrajectory({ fps: currentFps, step: currentStep });
            sendSync({
                op: "set_trajectory_playback",
                action: "play",
                fps: currentFps,
                step: currentStep,
            });
        }
    });
    btnPlayPause.style.paddingTop = "0px";
    btnPlayPause.style.paddingBottom = "0px";
    btnPlayPause.style.lineHeight = "18px";

    const btnNext = makeButton("+", () => {
        c.stepTrajectory(currentStep);
        sendSync({ op: "step_trajectory", by: currentStep });
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
    slider.style.background = "transparent";
    slider.style.appearance = "none";
    (slider.style as any).WebkitAppearance = "none";
    (slider.style as any).MozAppearance = "none";
    slider.style.setProperty("accent-color", "transparent");
    slider.style.borderRadius = "999px";
    slider.style.overflow = "visible";
    
    const updateSliderBg = () => {
        const min = Number(slider.min) || 0;
        const max = Number(slider.max) || 0;
        const val = Number(slider.value) || 0;
        // Keep a flat track to avoid visible gaps under the thumb; no filled gradient.
        const _ = { min, max, val }; // satisfy lints
        const track = "rgba(200,200,200,0.35)";
        slider.style.background = track;
    };
    slider.oninput = () => {
        const val = Number(slider.value);
        if (!Number.isFinite(val)) return;
        void c.setTrajectoryFrame(val);
        sendSync({ op: "set_trajectory_frame", index: val });
        updateSliderBg();
    };
    updateSliderBg();

    const label = document.createElement("span");
    label.style.color = "rgba(0,0,0,0.5)";
    label.style.fontSize = "11px";
    label.style.minWidth = "60px";
    label.style.textAlign = "center";
    label.textContent = "0 / 0";

    const stepControl = makeNumberControl(1, n => { currentStep = n; }, "Step size");
    const fpsControl = makeNumberControl(5, n => { currentFps = n; }, "FPS");

    traj.appendChild(btnPrev);
    traj.appendChild(btnPlayPause);
    traj.appendChild(btnNext);
    traj.appendChild(slider);
    traj.appendChild(label);
    traj.appendChild(stepControl.wrapper);
    traj.appendChild(fpsControl.wrapper);

    overlay.appendChild(traj);

    const initialHasTrajectory = !!opts?.initialHasTrajectory;
    const initialFrameCount = typeof opts?.initialFrameCount === "number" ? opts.initialFrameCount : undefined;
    if (initialHasTrajectory) {
        const fc = initialFrameCount && initialFrameCount > 0 ? initialFrameCount : 2;
        traj.style.display = fc > 1 ? "flex" : "none";
        slider.max = fc > 0 ? String(Math.max(fc - 1, 1)) : "1";
        slider.value = "0";
        updateSliderBg();
        label.textContent = fc > 0 ? `1 / ${fc}` : "0 / 0";
        // Keep controls disabled until a real trajectory state arrives.
        [btnPrev, btnNext, slider, btnPlayPause].forEach(el => {
            (el as HTMLButtonElement | HTMLInputElement).disabled = true;
        });
    }

    // Trajectory listener to update UI
    let hasSeenState = false;
    const applyTrajectoryState = (state: ReturnType<typeof c.trajectory.getTrajectoryState>) => {
        hasSeenState = true;
        const frameCount = state.frameCount;
        const current = state.currentFrame;
        traj.style.display = frameCount > 1 ? "flex" : "none";
        slider.max = frameCount > 0 ? String(frameCount - 1) : "0";
        slider.value = String(Math.min(current, frameCount > 0 ? frameCount - 1 : 0));
        updateSliderBg();
        label.textContent = frameCount > 0 ? `${current + 1} / ${frameCount}` : "0 / 0";
        const disabled = !state.hasTrajectory || frameCount <= 1;
        [btnPrev, btnNext, slider, btnPlayPause].forEach(el => {
            (el as HTMLButtonElement | HTMLInputElement).disabled = disabled;
        });

        // Update button appearance based on playback state
        if (state.isPlaying) {
            btnPlayPause.textContent = "⏸";
            btnPlayPause.title = "Pause Trajectory";
        } else {
            btnPlayPause.textContent = "▶";
            btnPlayPause.title = "Play Trajectory";
        }
        // Reveal overlay after first state application
        overlay.style.display = "flex";
        overlay.style.opacity = "1";
        overlay.style.pointerEvents = "none";
    };
    c.onTrajectoryState(applyTrajectoryState, { immediate: false });
    // If the trajectory state is already known (e.g., expected frame count pre-seeded),
    // apply it immediately; otherwise wait for the first update to avoid a "buttons only" flash.
    const initialState = c.trajectory.getTrajectoryState();
    if (initialState.hasTrajectory || initialState.expectedFrameCount !== undefined) {
        applyTrajectoryState(initialState);
    }

    // Placement and Autohide logic
    const placeOverlay = () => {
        const pos = model.get("controls_position") as string[] | undefined;
        const posFs = model.get("controls_position_fullscreen") as string[] | undefined;
        const isFs = !!document.fullscreenElement;
        const use = isFs && Array.isArray(posFs) ? posFs : Array.isArray(pos) ? pos : ["top", "right"];
        overlay.style.top = use?.includes("top") ? "8px" : "";
        overlay.style.bottom = use?.includes("bottom") ? "8px" : "";
        overlay.style.left = use?.includes("left") ? "8px" : "";
        overlay.style.right = use?.includes("right") ? "8px" : "";
    };
    placeOverlay();
    document.addEventListener("fullscreenchange", placeOverlay);
    model.on("change:controls_position", placeOverlay);
    model.on("change:controls_position_fullscreen", placeOverlay);

    let autohide = !!model.get("autohide_controls");
    const target = container; // Use passed container

    const applyShow = (visible: boolean) => {
        if (!hasSeenState) return; // Do not toggle visibility until first state is applied
        if (autohide) {
            overlay.style.opacity = visible ? "1" : "0";
            overlay.style.pointerEvents = visible ? "auto" : "none";
        } else {
            overlay.style.display = visible ? "flex" : "none";
        }
    };
    const onEnter = () => applyShow(!!model.get("show_controls"));
    const onLeave = () => applyShow(false);

    const enableAutohide = () => {
        overlay.style.transition = "opacity 150ms ease";
        applyShow(!!model.get("show_controls"));
        target.addEventListener("pointerenter", onEnter); // Changed to pointerenter
        target.addEventListener("pointerleave", onLeave); // Changed to pointerleave
    };
    const disableAutohide = () => {
        target.removeEventListener("pointerenter", onEnter);
        target.removeEventListener("pointerleave", onLeave);
        overlay.style.opacity = "1";
        overlay.style.pointerEvents = "auto";
        applyShow(!!model.get("show_controls"));
    };

    if (autohide) enableAutohide();
    else applyShow(!!model.get("show_controls"));

    model.on("change:show_controls", () => applyShow(!!model.get("show_controls")));
    model.on("change:autohide_controls", () => {
        const next = !!model.get("autohide_controls");
        if (next === autohide) return;
        autohide = next;
        if (autohide) {
            enableAutohide();
            applyShow(false);
        } else {
            disableAutohide();
        }
    });

    return overlay;
};
