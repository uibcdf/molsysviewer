import type { SceneState } from "../group-panel";
import { PanelContext, StudioPanel } from "./types";
import { makeCheckboxRow, makeSectionHeader, makeSettingsCard, makeStyledSelect } from "./ui-helpers";

/**
 * Studio → Viewport subpanel: live camera and render configuration
 * (background, spin/swing, projection mode, fog). Reads the current
 * `SceneState` pushed from the controller and emits scene actions.
 */
export class ViewportPanel implements StudioPanel {
    readonly key = "viewport";
    private host: HTMLElement | null = null;
    private state: SceneState = {};

    constructor(private readonly ctx: PanelContext) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    setScene(state: SceneState): void {
        this.state = { ...state };
        let badge = state.isDarkMode ? "Dark" : "Light";
        if (state.isSpinActive) badge += " · Spin";
        this.ctx.setBadge(badge);
        this.render();
    }

    private render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Viewport Settings"));

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            paddingBottom: "10px",
        });
        this.host.appendChild(grid);

        // A. Viewport Card
        const viewportCard = makeSettingsCard("Viewport Settings");
        grid.appendChild(viewportCard);

        // A1. Background toggle
        const bgRow = document.createElement("div");
        Object.assign(bgRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const bgLabel = document.createElement("span");
        bgLabel.textContent = "Background";
        Object.assign(bgLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const bgSelect = makeStyledSelect(["Dark", "Light"], this.state.isDarkMode ? "Dark" : "Light", (val) => {
            this.ctx.onAction("toggle_background", { mode: val.toLowerCase() });
        });
        bgRow.appendChild(bgLabel);
        bgRow.appendChild(bgSelect);
        viewportCard.appendChild(bgRow);

        // A2. Spin toggle
        viewportCard.appendChild(makeCheckboxRow("Auto-Rotate (Spin)", !!this.state.isSpinActive, () => {
            this.ctx.onAction("toggle_spin");
        }));

        // A3. Swing toggle
        viewportCard.appendChild(makeCheckboxRow("Oscillate (Swing)", !!this.state.isSwingActive, () => {
            this.ctx.onAction("toggle_swing");
        }));

        // B. Camera Card
        const cameraCard = makeSettingsCard("Camera Projection");
        grid.appendChild(cameraCard);

        // B1. Projection Mode
        const projRow = document.createElement("div");
        Object.assign(projRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const projLabel = document.createElement("span");
        projLabel.textContent = "Projection";
        Object.assign(projLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const projSelect = makeStyledSelect(["Perspective", "Orthographic"],
            this.state.cameraMode === "orthographic" ? "Orthographic" : "Perspective", (val) => {
                this.ctx.onAction("set_camera_mode", { mode: val.toLowerCase() });
            },
        );
        projRow.appendChild(projLabel);
        projRow.appendChild(projSelect);
        cameraCard.appendChild(projRow);

        // B2. Fog enabled
        const fogEnabled = !!this.state.fogEnabled;
        const fogIntensity = typeof this.state.fogIntensity === "number" ? this.state.fogIntensity : 0.5;

        cameraCard.appendChild(makeCheckboxRow("Fog Enabled", fogEnabled, (checked) => {
            this.ctx.onAction("set_fog", { enable: checked, intensity: fogIntensity });
        }));

        // B3. Fog intensity slider
        const fogSliderRow = document.createElement("div");
        Object.assign(fogSliderRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            marginTop: "2px",
        });
        const fogSliderLabel = document.createElement("div");
        Object.assign(fogSliderLabel.style, {
            display: "flex",
            justifyContent: "space-between",
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
        });
        fogSliderLabel.innerHTML = `<span>Fog Intensity</span><span>${Math.round(fogIntensity * 100)}%</span>`;

        const fogSlider = document.createElement("input");
        fogSlider.type = "range";
        fogSlider.min = "0.0";
        fogSlider.max = "1.0";
        fogSlider.step = "0.05";
        fogSlider.value = String(fogIntensity);
        fogSlider.disabled = !fogEnabled;
        Object.assign(fogSlider.style, {
            width: "100%",
            height: "4px",
            borderRadius: "2px",
            background: "rgba(255,255,255,0.12)",
            outline: "none",
            cursor: fogEnabled ? "pointer" : "not-allowed",
            opacity: fogEnabled ? "1" : "0.5",
        });
        fogSlider.addEventListener("change", () => {
            const intensity = parseFloat(fogSlider.value);
            this.ctx.onAction("set_fog", { enable: fogEnabled, intensity });
        });

        fogSliderRow.appendChild(fogSliderLabel);
        fogSliderRow.appendChild(fogSlider);
        cameraCard.appendChild(fogSliderRow);
    }
}
