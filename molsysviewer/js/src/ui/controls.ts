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
    btn.style.cursor = "pointer";
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
            background: rgba(0,0,0,0.5) !important;
            border: none !important;
            box-shadow: none !important;
            margin-top: 0px;
        }
        .molsysviewer-slider::-webkit-slider-thumb:hover,
        .molsysviewer-slider::-webkit-slider-thumb:active,
        .molsysviewer-slider::-webkit-slider-thumb:focus {
            background: rgba(0,0,0,0.5) !important;
            border: none !important;
            box-shadow: none !important;
        }
        .molsysviewer-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50% !important;
            background: rgba(0,0,0,0.5) !important;
            border: none !important;
        }
        .molsysviewer-slider::-moz-range-thumb:hover,
        .molsysviewer-slider::-moz-range-thumb:active,
        .molsysviewer-slider::-moz-range-thumb:focus {
            background: rgba(0,0,0,0.5) !important;
            border: none !important;
        }
        .molsysviewer-slider::-ms-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50% !important;
            background: rgba(0,0,0,0.5) !important;
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
        btn.style.cursor = "pointer";
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
    onPopClick?: () => void
) => {
    injectStyles();

    const overlay = document.createElement("div");
    overlay.className = "molsysviewer-controls";
    overlay.style.position = "absolute";
    overlay.style.display = "flex";
    overlay.style.gap = "6px";
    overlay.style.zIndex = "10";
    overlay.style.pointerEvents = "none";
    overlay.style.flexWrap = "nowrap";

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

    let currentStep = 1;
    let currentFps = 30;

    const btnPrev = makeButton("−", () => {
        c.stepTrajectory(-currentStep);
        sendSync({ op: "step_trajectory", by: -currentStep });
    });
    const btnPlay = makeButton("▶", () => {
        c.playTrajectory({ fps: currentFps, step: currentStep });
        sendSync({
            op: "set_trajectory_playback",
            action: "play",
            fps: currentFps,
            step: currentStep,
        });
    });
    btnPlay.style.paddingTop = "0px";
    btnPlay.style.paddingBottom = "0px";
    btnPlay.style.lineHeight = "18px";
    const btnPause = makeButton("⏸", () => {
        c.stopTrajectoryPlayback();
        sendSync({ op: "set_trajectory_playback", action: "stop" });
    });
    btnPause.style.paddingTop = "0px";
    btnPause.style.paddingBottom = "0px";
    btnPause.style.lineHeight = "18px";
    const btnNext = makeButton("+", () => {
        c.stepTrajectory(currentStep);
        sendSync({ op: "step_trajectory", by: currentStep });
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
        const pct = max > min ? Math.min(100, Math.max(0, ((val - min) * 100) / (max - min))) : 0;
        const fill = "rgba(128,128,128,0.8)";
        const track = "rgba(200,200,200,0.35)";
        slider.style.background = `linear-gradient(to right, ${fill} 0%, ${fill} ${pct}%, ${track} ${pct}%, ${track} 100%)`;
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
    traj.appendChild(btnPlay);
    traj.appendChild(btnPause);
    traj.appendChild(btnNext);
    traj.appendChild(slider);
    traj.appendChild(label);
    traj.appendChild(stepControl.wrapper);
    traj.appendChild(fpsControl.wrapper);

    overlay.appendChild(traj);

    // Trajectory listener to update UI
    c.onTrajectoryState(state => {
        const frameCount = state.frameCount;
        const current = state.currentFrame;
        slider.max = frameCount > 0 ? String(frameCount - 1) : "0";
        slider.value = String(Math.min(current, frameCount > 0 ? frameCount - 1 : 0));
        updateSliderBg();
        label.textContent = frameCount > 0 ? `${current + 1} / ${frameCount}` : "0 / 0";
        const disabled = frameCount <= 1;
        [btnPrev, btnNext, slider, btnPlay, btnPause].forEach(el => {
            (el as HTMLButtonElement | HTMLInputElement).disabled = disabled;
        });
    });

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
    const target = c.plugin.canvas3d?.props.canvas?.parentElement ?? document.body; // Best guess for interaction target

    const applyShow = (visible: boolean) => {
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
        target.addEventListener("mouseenter", onEnter);
        target.addEventListener("mouseleave", onLeave);
    };
    const disableAutohide = () => {
        target.removeEventListener("mouseenter", onEnter);
        target.removeEventListener("mouseleave", onLeave);
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
