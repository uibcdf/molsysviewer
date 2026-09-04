import { MolSysViewerController } from "../managers/viewer-controller";
import { ViewerMessage } from "../messages/viewer-messages";
import { HelpOverlay } from "./help-overlay";



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

const makeMinimalTrajButton = (svgInner: string, title: string, onClick: () => void) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.title = title;
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;">${svgInner}</svg>`;
    Object.assign(btn.style, {
        width: "28px",
        height: "28px",
        minWidth: "28px",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "0",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "6px",
        background: "rgba(18, 18, 22, 0.75)",
        color: "rgba(255, 255, 255, 0.75)",
        cursor: "default",
        userSelect: "none",
        pointerEvents: "auto",
        boxSizing: "border-box",
        boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
        transition: "all 120ms ease",
    });
    btn.addEventListener("mouseenter", () => {
        btn.style.background = "rgba(18, 18, 22, 0.95)";
        btn.style.borderColor = "rgba(255, 255, 255, 0.35)";
        btn.style.color = "rgba(255, 255, 255, 0.98)";
    });
    btn.addEventListener("mouseleave", () => {
        btn.style.background = "rgba(18, 18, 22, 0.75)";
        btn.style.borderColor = "rgba(255, 255, 255, 0.15)";
        btn.style.color = "rgba(255, 255, 255, 0.75)";
    });
    btn.addEventListener("click", onClick);
    return btn;
};

const injectStyles = () => {
    let el = document.getElementById("molsysviewer-traj-style") as HTMLStyleElement | null;
    if (!el) {
        el = document.createElement("style");
        el.id = "molsysviewer-traj-style";
        document.head.appendChild(el);
    }
    const css = `
        .molsysviewer-controls {
            font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "DejaVu Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
        }
        .molsysviewer-controls button,
        .molsysviewer-controls input,
        .molsysviewer-controls select,
        .molsysviewer-controls textarea,
        .molsysviewer-controls span {
            font-family: inherit;
        }
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
        .molsysviewer-slider-minimal {
            background: transparent;
            height: 4px;
            border-radius: 999px;
            overflow: visible;
        }
        .molsysviewer-slider-minimal::-webkit-slider-runnable-track {
            background: rgba(255, 255, 255, 0.3) !important;
            height: 4px;
            border-radius: 999px;
        }
        .molsysviewer-slider-minimal::-moz-range-track {
            background: rgba(255, 255, 255, 0.3) !important;
            height: 4px;
            border-radius: 999px;
        }
        .molsysviewer-slider-minimal::-ms-track {
            background: rgba(255, 255, 255, 0.3) !important;
            height: 4px;
            border-radius: 999px;
            border: none;
            color: transparent;
        }
        .molsysviewer-slider-minimal::-webkit-slider-thumb {
            -webkit-appearance: none !important;
            appearance: none !important;
            width: 10px;
            height: 10px;
            border-radius: 50% !important;
            background: #ffffff !important;
            border: none !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
            margin-top: -3px;
            cursor: default;
        }
        .molsysviewer-slider-minimal::-webkit-slider-thumb:hover,
        .molsysviewer-slider-minimal::-webkit-slider-thumb:active {
            background: #ffffff !important;
            box-shadow: 0 1px 5px rgba(0,0,0,0.6) !important;
        }
        .molsysviewer-slider-minimal::-moz-range-thumb {
            width: 10px;
            height: 10px;
            border-radius: 50% !important;
            background: #ffffff !important;
            border: none !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
            cursor: default;
        }
        .molsysviewer-slider-minimal::-moz-range-thumb:hover,
        .molsysviewer-slider-minimal::-moz-range-thumb:active {
            background: #ffffff !important;
        }
        .molsysviewer-slider-minimal::-ms-thumb {
            width: 10px;
            height: 10px;
            border-radius: 50% !important;
            background: #ffffff !important;
            border: none !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
        }
        .molsysviewer-traj-capsule {
            height: 28px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 10px;
            background: rgba(18, 18, 22, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
        }
    `;
    el.textContent = css;
};

const makeNumberControl = (initial: number, onChange: (n: number) => void, title: string, minimal = false) => {
    const wrapper = document.createElement("div");
    wrapper.style.position = "relative";
    wrapper.style.display = "inline-block";
    wrapper.style.width = minimal ? "42px" : "52px";
    wrapper.style.height = minimal ? "28px" : "22px";

    const input = document.createElement("input");
    input.type = "text";
    input.value = String(initial);
    input.style.width = minimal ? "42px" : "52px";
    input.style.height = minimal ? "28px" : "22px";
    input.style.fontSize = minimal ? "11px" : "11px";
    input.style.fontFamily = '"IBM Plex Sans", system-ui, sans-serif';
    input.style.fontWeight = minimal ? "600" : "normal";
    input.style.textAlign = "center";
    input.style.boxSizing = "border-box";
    if (minimal) {
        input.style.color = "rgba(255,255,255,0.9)";
        input.style.background = "rgba(18, 18, 22, 0.75)";
        input.style.border = "1px solid rgba(255,255,255,0.15)";
        input.style.borderRadius = "6px";
        input.style.padding = "0 14px 0 6px";
    } else {
        input.style.color = "rgba(255,255,255,0.9)";
        input.style.background = "rgba(40,40,40,0.6)";
        input.style.border = "1px solid rgba(255,255,255,0.55)";
        input.style.borderRadius = "4px";
        input.style.padding = "0 18px 0 4px";
    }
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
    spinner.style.width = minimal ? "12px" : "14px";
    spinner.style.height = minimal ? "26px" : "18px";
    spinner.style.display = "flex";
    spinner.style.flexDirection = "column";
    spinner.style.alignItems = "center";

    const mkArrow = (charOrSvg: string, delta: number, extraTop: string = "0px") => {
        const btn = document.createElement("div");
        if (minimal) {
            btn.innerHTML = charOrSvg;
            btn.style.display = "flex";
            btn.style.alignItems = "center";
            btn.style.justifyContent = "center";
            btn.style.width = "12px";
            btn.style.height = "12px";
        } else {
            btn.textContent = charOrSvg;
            btn.style.fontSize = "10px";
            btn.style.lineHeight = "10px";
            btn.style.height = "9px";
        }
        btn.style.color = "rgba(255, 255, 255, 0.75)";
        btn.style.background = "transparent";
        btn.style.border = "none";
        btn.style.textAlign = "center";
        btn.style.cursor = "default";
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

    const upBtn = mkArrow(
        minimal 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6" viewBox="0 0 8 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1.5,4.5 4,2 6.5,4.5"/></svg>`
            : "▲", 
        1, 
        "0px"
    );
    const downBtn = mkArrow(
        minimal 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6" viewBox="0 0 8 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1.5,1.5 4,4 6.5,1.5"/></svg>`
            : "▼", 
        -1, 
        minimal ? "2px" : "0px"
    );
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
    opts?: { initialHasTrajectory?: boolean; initialFrameCount?: number },
    onPanelPopClick?: () => void
) => {
    const controlsMode = (model.get("controls_mode") as string) || "classic";
    const isCinema = controlsMode === "cinema";
    const isMinimal = controlsMode === "minimal" || isCinema;

    const helpOverlay = new HelpOverlay(container);

    const onHelpKey = (ev: KeyboardEvent) => {
        if ((ev.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return;
        if (!container.contains(ev.target as Node)) return;
        if (ev.key.toLowerCase() === "h") {
            ev.preventDefault();
            ev.stopPropagation();
            helpOverlay.toggle();
        }
    };
    window.addEventListener("keydown", onHelpKey, true);

    if (isCinema) {
        // Render a subtle, elegant, self-dismissing helper toast for accessibility
        const toast = document.createElement("div");
        toast.textContent = "Cinema Mode active. Press N/W for panels, H for help.";
        Object.assign(toast.style, {
            position: "absolute",
            bottom: "24px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(18, 18, 22, 0.88)",
            color: "rgba(244, 244, 245, 0.95)",
            padding: "8px 16px",
            borderRadius: "999px",
            fontSize: "11px",
            fontWeight: "500",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            border: "1px solid rgba(255, 255, 255, 0.12)",
            boxShadow: "0 8px 24px rgba(0, 0, 0, 0.35)",
            zIndex: "100",
            pointerEvents: "none",
            transition: "opacity 0.8s ease-in-out",
            opacity: "1",
        });
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => {
                toast.remove();
            }, 800);
        }, 3200);
    }

    injectStyles();

    let overlay: HTMLDivElement | undefined;
    if (!isCinema) {
        overlay = document.createElement("div");
        overlay.className = "molsysviewer-controls";
        overlay.style.position = "absolute";
        overlay.style.display = "flex";
        overlay.style.gap = "6px";
        overlay.style.zIndex = "10";
        overlay.style.pointerEvents = "none";
        overlay.style.flexWrap = "nowrap";
        overlay.style.opacity = "0"; // Reveal after initial trajectory state to avoid flash
        overlay.style.opacity = "0";
        overlay.style.display = "none";
    }

    const panelModeStyle = (model.get("panel_mode_style") as string) || "drawer";


    const traj = document.createElement("div");
    traj.setAttribute("data-molsysviewer-trajectory-controls", "true");
    traj.style.display = "flex";
    traj.style.alignItems = "center";
    traj.style.gap = "6px";
    traj.style.pointerEvents = "auto";
    traj.style.marginLeft = isMinimal ? "0px" : "6px";
    traj.style.marginRight = isMinimal ? "10px" : "0px";
    traj.style.paddingLeft = "0px";
    traj.style.borderLeft = "0px";
    traj.style.display = "none";

    let currentStep = 1;
    let currentFps = 30;

    let btnPrev: HTMLButtonElement | undefined;
    let btnNext: HTMLButtonElement | undefined;
    let stepControl: any = null;
    let fpsControl: any = null;
    let trajCapsule: HTMLDivElement | undefined;

    const btnPlayPause = isMinimal
        ? makeMinimalTrajButton(`<polygon points="5,3 13,8 5,13" fill="currentColor"/>`, "Play Trajectory", () => {
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
          })
        : makeButton("▶ / ⏸", () => {
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
    btnPlayPause.setAttribute("data-molsysviewer-trajectory-playback", "play");
    if (isMinimal) {
        btnPrev = makeMinimalTrajButton(`<rect x="3" y="3" width="2" height="10" fill="currentColor"/><polygon points="12,3 6,8 12,13" fill="currentColor"/>`, "Previous Step", () => {
            c.stepTrajectory(-currentStep);
            sendSync({ op: "step_trajectory", by: -currentStep });
        });
        btnNext = makeMinimalTrajButton(`<polygon points="4,3 10,8 4,13" fill="currentColor"/><rect x="11" y="3" width="2" height="10" fill="currentColor"/>`, "Next Step", () => {
            c.stepTrajectory(currentStep);
            sendSync({ op: "step_trajectory", by: currentStep });
        });
    } else {
        btnPlayPause.style.paddingTop = "0px";
        btnPlayPause.style.paddingBottom = "0px";
        btnPlayPause.style.lineHeight = "18px";
        btnPlayPause.style.minWidth = "28px";
        btnPlayPause.style.width = "28px";

        btnPrev = makeButton("−", () => {
            c.stepTrajectory(-currentStep);
            sendSync({ op: "step_trajectory", by: -currentStep });
        });
        btnNext = makeButton("+", () => {
            c.stepTrajectory(currentStep);
            sendSync({ op: "step_trajectory", by: currentStep });
        });
    }
    btnPrev?.setAttribute("data-molsysviewer-trajectory-step", "previous");
    btnNext?.setAttribute("data-molsysviewer-trajectory-step", "next");

    const slider = document.createElement("input");
    slider.setAttribute("data-molsysviewer-trajectory-frame", "true");
    slider.type = "range";
    slider.min = "0";
    slider.max = "0";
    slider.value = "0";
    slider.className = isMinimal ? "molsysviewer-slider-minimal" : "molsysviewer-slider";
    slider.style.width = isMinimal ? "100px" : "160px";
    slider.style.flex = isMinimal ? "0 0 100px" : "0 0 160px";
    slider.style.background = "transparent";
    slider.style.appearance = "none";
    (slider.style as any).WebkitAppearance = "none";
    (slider.style as any).MozAppearance = "none";
    slider.style.setProperty("accent-color", "transparent");
    slider.style.borderRadius = "999px";
    slider.style.overflow = "visible";
    
    const updateSliderBg = () => {
        if (isMinimal) {
            slider.style.background = "transparent";
        } else {
            const track = "rgba(200,200,200,0.35)";
            slider.style.background = track;
        }
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
    label.setAttribute("data-molsysviewer-trajectory-label", "true");
    if (isMinimal) {
        label.style.color = "rgba(255, 255, 255, 0.85)";
        label.style.fontSize = "11px";
        label.style.fontFamily = '"IBM Plex Sans", system-ui, sans-serif';
        label.style.fontWeight = "600";
        label.style.minWidth = "42px";
        label.style.textAlign = "right";
    } else {
        label.style.color = "rgba(0,0,0,0.5)";
        label.style.fontSize = "11px";
        label.style.minWidth = "60px";
        label.style.textAlign = "center";
    }
    label.textContent = "0 / 0";

    if (isMinimal) {
        trajCapsule = document.createElement("div");
        trajCapsule.className = "molsysviewer-traj-capsule";
        trajCapsule.appendChild(slider);
        trajCapsule.appendChild(label);

        traj.appendChild(trajCapsule);
        if (btnPrev) traj.appendChild(btnPrev);
        traj.appendChild(btnPlayPause);
        if (btnNext) traj.appendChild(btnNext);

        if (isCinema) {
            stepControl = makeNumberControl(1, n => {
                currentStep = n;
                const state = c.trajectory.getTrajectoryState();
                if (state.isPlaying) {
                    c.playTrajectory({ fps: currentFps, step: currentStep });
                }
            }, "Step size", true);

            fpsControl = makeNumberControl(30, n => {
                currentFps = n;
                const state = c.trajectory.getTrajectoryState();
                if (state.isPlaying) {
                    c.playTrajectory({ fps: currentFps, step: currentStep });
                }
            }, "FPS", true);

            traj.appendChild(stepControl.wrapper);
            traj.appendChild(fpsControl.wrapper);
        }
    } else {
        stepControl = makeNumberControl(1, n => {
            currentStep = n;
            const state = c.trajectory.getTrajectoryState();
            if (state.isPlaying) {
                btnPlayPause.setAttribute("data-molsysviewer-trajectory-playback", "stop");
                c.playTrajectory({ fps: currentFps, step: currentStep });
            }
        }, "Step size", isMinimal);

        fpsControl = makeNumberControl(30, n => {
            currentFps = n;
            const state = c.trajectory.getTrajectoryState();
            if (state.isPlaying) {
                c.playTrajectory({ fps: currentFps, step: currentStep });
            }
        }, "FPS", isMinimal);

        if (btnPrev) traj.appendChild(btnPrev);
        traj.appendChild(btnPlayPause);
        if (btnNext) traj.appendChild(btnNext);
        traj.appendChild(slider);
        traj.appendChild(label);
        traj.appendChild(stepControl.wrapper);
        traj.appendChild(fpsControl.wrapper);
    }

    if (isCinema) {
        Object.assign(traj.style, {
            position: "absolute",
            bottom: "12px",
            left: "50%",
            transform: "translateX(-50%) translateY(45px)",
            opacity: "0",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            zIndex: "10",
            pointerEvents: "auto",
            transition: "transform 0.25s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.2s ease",
        });

        const triggerArea = document.createElement("div");
        Object.assign(triggerArea.style, {
            position: "absolute",
            bottom: "0px",
            left: "0px",
            width: "100%",
            height: "56px",
            zIndex: "9",
            pointerEvents: "auto",
            background: "transparent",
        });

        const showScrubber = () => {
            traj.style.transform = "translateX(-50%) translateY(0)";
            traj.style.opacity = "1";
        };
        const hideScrubber = () => {
            traj.style.transform = "translateX(-50%) translateY(45px)";
            traj.style.opacity = "0";
        };

        triggerArea.addEventListener("mouseenter", showScrubber);
        traj.addEventListener("mouseenter", showScrubber);

        triggerArea.addEventListener("mouseleave", (e) => {
            if (e.relatedTarget !== traj && !traj.contains(e.relatedTarget as Node)) {
                hideScrubber();
            }
        });
        traj.addEventListener("mouseleave", (e) => {
            if (e.relatedTarget !== triggerArea && !triggerArea.contains(e.relatedTarget as Node)) {
                hideScrubber();
            }
        });

        container.appendChild(triggerArea);
        container.appendChild(traj);
    } else if (overlay) {
        overlay.appendChild(traj);
    }

    let fullscreenBtn: HTMLButtonElement | null = null;

    if (controlsMode === "minimal" && overlay) {
        const ICON_PANEL = `<rect x="2" y="2" width="12" height="12" rx="1.5"/><line x1="5.5" y1="2.5" x2="5.5" y2="13.5"/>`;
        const ICON_FULLSCREEN = `<polyline points="2,5 2,2 5,2"/><polyline points="11,2 14,2 14,5"/><polyline points="14,11 14,14 11,14"/><polyline points="5,14 2,14 2,11"/>`;
        const ICON_POPUP = `<line x1="5.5" y1="10.5" x2="11.5" y2="4.5"/><polyline points="8,4 12,4 12,8"/><polyline points="5.5,7 3,7 3,13 9,13 9,10.5"/>`;

        const mkIcon = (svgInner: string, title: string, handler: () => void) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.title = title;
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${svgInner}</svg>`;
            Object.assign(btn.style, {
                width: "28px",
                height: "28px",
                minWidth: "28px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "0",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                borderRadius: "6px",
                background: "rgba(18, 18, 22, 0.75)",
                color: "rgba(255, 255, 255, 0.75)",
                cursor: "default",
                userSelect: "none",
                pointerEvents: "auto",
                boxSizing: "border-box",
                boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
                transition: "all 120ms ease",
            });
            btn.addEventListener("mouseenter", () => {
                btn.style.background = "rgba(18, 18, 22, 0.95)";
                btn.style.borderColor = "rgba(255, 255, 255, 0.35)";
                btn.style.color = "rgba(255, 255, 255, 0.98)";
            });
            btn.addEventListener("mouseleave", () => {
                btn.style.background = "rgba(18, 18, 22, 0.75)";
                btn.style.borderColor = "rgba(255, 255, 255, 0.15)";
                btn.style.color = "rgba(255, 255, 255, 0.75)";
            });
            btn.addEventListener("click", handler);
            overlay!.appendChild(btn);
            return btn;
        };

        mkIcon(ICON_PANEL, "Panel mode (N / W)", () => c.togglePanelMode());
        fullscreenBtn = mkIcon(ICON_FULLSCREEN, "Fullscreen", () => c.toggleFullscreen());
        if (onPopClick) mkIcon(ICON_POPUP, "Open popup", onPopClick);
        const ICON_HELP = `<circle cx="8" cy="8" r="6"/><path d="M6.2,6.5a1.9,1.9,0,0,1,3.8,0c0,1.9-1.9,1.9-1.9,3" stroke-linecap="round" stroke-linejoin="round"/><line x1="8" y1="12.8" x2="8" y2="12.8" stroke-width="2" stroke-linecap="round"/>`;
        mkIcon(ICON_HELP, "Help (H)", () => helpOverlay.toggle());
    } else if (overlay) {
        const mk = (label: string, handler: () => void) => {
            const b = makeButton(label, handler);
            b.style.pointerEvents = "auto";
            overlay!.appendChild(b);
            return b;
        };

        mk("Reset", async () => {
            await c.resetView();
            sendSync({ op: "reset_view" });
        });
        fullscreenBtn = mk("Full", () => c.toggleFullscreen());
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
        mk("Help", () => helpOverlay.toggle());
        if (panelModeStyle === "floating" || panelModeStyle === "floating-unified" || panelModeStyle === "integrated") {
            mk("Panel", () => c.togglePanelMode());
        }
    }

    let hasSeenState = false;
    let lastIsPlaying: boolean | null = null;
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
        const elsToDisable = [slider, btnPlayPause];
        if (btnPrev) elsToDisable.push(btnPrev);
        if (btnNext) elsToDisable.push(btnNext);
        if (stepControl) elsToDisable.push(stepControl.input);
        if (fpsControl) elsToDisable.push(fpsControl.input);
        elsToDisable.forEach(el => {
            (el as HTMLButtonElement | HTMLInputElement).disabled = disabled;
        });

        if (state.isPlaying !== lastIsPlaying) {
            lastIsPlaying = state.isPlaying;
            if (state.isPlaying) {
                if (isMinimal) {
                    btnPlayPause.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;"><rect x="4" y="3" width="2.5" height="10" fill="currentColor"/><rect x="9.5" y="3" width="2.5" height="10" fill="currentColor"/></svg>`;
                } else {
                    btnPlayPause.textContent = "⏸";
                }
                btnPlayPause.title = "Pause Trajectory";
            } else {
                btnPlayPause.setAttribute("data-molsysviewer-trajectory-playback", "play");
                if (isMinimal) {
                    btnPlayPause.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;"><polygon points="5,3 13,8 5,13" fill="currentColor"/></svg>`;
                } else {
                    btnPlayPause.textContent = "▶";
                }
                btnPlayPause.title = "Play Trajectory";
            }
        }
        if (overlay) {
            overlay.style.display = "flex";
            overlay.style.opacity = "1";
            overlay.style.pointerEvents = "none";
        }
    };

    c.onTrajectoryState(applyTrajectoryState, { immediate: false });
    const initialState = c.trajectory.getTrajectoryState();
    if (initialState.hasTrajectory || initialState.expectedFrameCount !== undefined) {
        applyTrajectoryState(initialState);
    }

    const hotspot = document.createElement("div");
    Object.assign(hotspot.style, {
        position: "absolute",
        width: "130px",
        height: "55px",
        zIndex: "9", // Below the overlay (10) so buttons receive clicks
        background: "transparent",
        pointerEvents: "auto",
        display: "none",
    });
    container.appendChild(hotspot);

    const placeOverlay = () => {
        if (!overlay) return;
        const isFullscreen = !!document.fullscreenElement;
        const rawPos = isFullscreen
            ? model.get("controls_position_fullscreen")
            : model.get("controls_position");

        let use: string[] = ["top", "right"];
        if (Array.isArray(rawPos)) {
            use = rawPos;
        } else if (typeof rawPos === "string") {
            if (rawPos === "top-left") use = ["top", "left"];
            else if (rawPos === "top-right") use = ["top", "right"];
            else if (rawPos === "bottom-left") use = ["bottom", "left"];
            else if (rawPos === "bottom-center") use = ["bottom", "center"];
            else if (rawPos === "bottom-right") use = ["bottom", "right"];
        }

        const gap = isFullscreen ? "36px" : "12px";

        // Position overlay
        overlay.style.top = use.includes("top") ? gap : "";
        overlay.style.bottom = use.includes("bottom") ? gap : "";
        overlay.style.left = use.includes("left") ? gap : "";
        overlay.style.right = use.includes("right") ? gap : "";
        overlay.style.transform = "";

        if (use.includes("center")) {
            overlay.style.left = "50%";
            overlay.style.transform = "translateX(-50%)";
        }

        // Position hotspot to match the active corner
        hotspot.style.top = use.includes("top") ? "0" : "";
        hotspot.style.bottom = use.includes("bottom") ? "0" : "";
        hotspot.style.left = use.includes("left") ? "0" : "";
        hotspot.style.right = use.includes("right") ? "0" : "";
        hotspot.style.transform = "";

        if (use.includes("center")) {
            hotspot.style.left = "50%";
            hotspot.style.transform = "translateX(-50%)";
        }

        // Dynamic hotspot sizing to accommodate the gap and overlay size
        if (isFullscreen) {
            hotspot.style.width = "200px";
            hotspot.style.height = "85px";
        } else {
            hotspot.style.width = "130px";
            hotspot.style.height = "55px";
        }
    };

    const ICON_EXIT_FULLSCREEN = `<polyline points="5,2 5,5 2,5"/><polyline points="11,2 11,5 14,5"/><polyline points="14,11 11,11 11,14"/><polyline points="2,11 5,11 5,14"/>`;

    const updateFullscreenButtonState = () => {
        const isFullscreen = !!document.fullscreenElement;
        if (fullscreenBtn) {
            if (controlsMode === "minimal") {
                const svg = fullscreenBtn.querySelector("svg");
                if (svg) {
                    const path = isFullscreen ? ICON_EXIT_FULLSCREEN : `<polyline points="2,5 2,2 5,2"/><polyline points="11,2 14,2 14,5"/><polyline points="14,11 14,14 11,14"/><polyline points="5,14 2,14 2,11"/>`;
                    svg.innerHTML = path;
                }
                fullscreenBtn.title = isFullscreen ? "Exit Fullscreen" : "Fullscreen";
            } else {
                fullscreenBtn.textContent = isFullscreen ? "Exit" : "Full";
            }
        }
    };

    if (overlay) {
        let autohide = !!model.get("autohide_controls");
        let isHovered = false;
        let fadeTimeout: any = null;
        const target = container;

        const shouldHideControls = () => {
            const isHelpOpen = helpOverlay.isVisible();
            const isFloatingPanelOpen = !!c.sharedShell && 
                                        c.sharedShell.isVisible() && 
                                        c.sharedShell.isExpanded && 
                                        !c.sharedShell.isSplit && 
                                        !c.sharedShell.isAmbient;
            return isHelpOpen || isFloatingPanelOpen;
        };

        const applyShow = (visible: boolean) => {
            if (!hasSeenState) return;
            const forceHide = shouldHideControls();
            if (autohide) {
                overlay!.style.opacity = (visible && !forceHide) ? "1" : "0";
                overlay!.style.pointerEvents = (visible && !forceHide) ? "auto" : "none";
            } else {
                overlay!.style.display = (visible && !forceHide) ? "flex" : "none";
            }
        };

        const triggerTemporaryShow = () => {
            if (!autohide) return;
            const isFullscreen = !!document.fullscreenElement;
            const isSplit = c.sharedShell?.isSplit;
            if (!isFullscreen && !isSplit) return;

            if (fadeTimeout) clearTimeout(fadeTimeout);
            applyShow(true);
            fadeTimeout = setTimeout(() => {
                if (!isHovered) {
                    applyShow(false);
                }
            }, 1500);
        };

        const onEnterWhole = () => {
            isHovered = true;
            applyShow(true);
        };

        const onLeaveWhole = () => {
            isHovered = false;
            applyShow(false);
        };

        const onEnterHotspot = () => {
            isHovered = true;
            if (fadeTimeout) clearTimeout(fadeTimeout);
            applyShow(true);
        };

        const onLeaveHotspot = () => {
            isHovered = false;
            applyShow(false);
        };

        const updateAutohideMode = () => {
            if (!autohide) return;
            const isFullscreen = !!document.fullscreenElement;
            const isSplit = c.sharedShell?.isSplit;
            const useCornerHotspot = isFullscreen || isSplit;
            
            target.removeEventListener("pointerenter", onEnterWhole);
            target.removeEventListener("pointerleave", onLeaveWhole);
            hotspot.removeEventListener("pointerenter", onEnterHotspot);
            hotspot.removeEventListener("pointerleave", onLeaveHotspot);
            overlay!.removeEventListener("pointerenter", onEnterHotspot);
            overlay!.removeEventListener("pointerleave", onLeaveHotspot);

            if (useCornerHotspot) {
                hotspot.style.display = "block";
                hotspot.addEventListener("pointerenter", onEnterHotspot);
                hotspot.addEventListener("pointerleave", onLeaveHotspot);
                overlay!.addEventListener("pointerenter", onEnterHotspot);
                overlay!.addEventListener("pointerleave", onLeaveHotspot);
            } else {
                hotspot.style.display = "none";
                target.addEventListener("pointerenter", onEnterWhole);
                target.addEventListener("pointerleave", onLeaveWhole);
            }
        };

        placeOverlay();
        updateFullscreenButtonState();
        document.addEventListener("fullscreenchange", () => {
            const isFullscreen = !!document.fullscreenElement;
            if (isFullscreen) {
                const isDark = c.isDarkMode;
                container.style.backgroundColor = isDark ? "#101010" : "#ffffff";
            } else {
                container.style.backgroundColor = "";
            }
            placeOverlay();
            updateFullscreenButtonState();
            updateAutohideMode();
            triggerTemporaryShow();
        });
        model.on("change:controls_position", placeOverlay);
        model.on("change:controls_position_fullscreen", placeOverlay);

        helpOverlay.onVisibilityChange = () => {
            applyShow(autohide ? isHovered : !!model.get("show_controls"));
        };

        c.registerLayoutChangeListener((state) => {
            updateAutohideMode();
            if (state.isSplit && state.visible && state.expanded) {
                triggerTemporaryShow();
            }
            applyShow(autohide ? isHovered : !!model.get("show_controls"));
        });

        const enableAutohide = () => {
            overlay!.style.transition = "opacity 250ms ease-in-out";
            updateAutohideMode();
            triggerTemporaryShow();
        };

        const disableAutohide = () => {
            hotspot.style.display = "none";
            target.removeEventListener("pointerenter", onEnterWhole);
            target.removeEventListener("pointerleave", onLeaveWhole);
            hotspot.removeEventListener("pointerenter", onEnterHotspot);
            hotspot.removeEventListener("pointerleave", onLeaveHotspot);
            overlay!.removeEventListener("pointerenter", onEnterHotspot);
            overlay!.removeEventListener("pointerleave", onLeaveHotspot);
            
            overlay!.style.opacity = "1";
            overlay!.style.pointerEvents = "auto";
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
    }

    return overlay;
};
