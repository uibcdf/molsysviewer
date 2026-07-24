import type { SceneState, SectionSettings, SectionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelContext } from "./types";
import { formatUnitLabel, makeButton, makeCheckboxRow, makeSectionHeader, makeStyledSelect } from "./ui-helpers";

function card(): HTMLDivElement {
    const element = document.createElement("div");
    Object.assign(element.style, {
        display: "flex", flexDirection: "column", gap: "7px", padding: "10px",
        borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.035)",
    });
    return element;
}

/**
 * Studio → Viewport subpanel: live camera, render environment configuration
 * (background, lighting, fog, spin/swing, projection mode) and world clipping planes.
 */
export class ViewportPanel extends BasePanel {
    readonly key = "viewport";
    private state: SceneState = {};
    private sections: SectionSummary[] = [];
    private sectionSettings: SectionSettings = { activeSelectionCount: 0, systemLoaded: false };
    private coalescing = false;

    constructor(private readonly ctx: PanelContext) {
        super();
    }

    setScene(state: SceneState): void {
        this.state = { ...state };
        let badge = state.isDarkMode ? "Dark" : "Light";
        if (state.isSpinActive) badge += " · Spin";
        this.ctx.setBadge(badge);
        this.scheduleRender();
    }

    setSections(items: SectionSummary[], settings: SectionSettings): void {
        this.sections = items.map(item => ({
            ...item,
            point: [...item.point] as [number, number, number],
            normal: [...item.normal] as [number, number, number],
        }));
        this.sectionSettings = { ...settings };
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // 1. Section Header & Global Status Card
        this.host.appendChild(makeSectionHeader("Viewport"));
        this.host.appendChild(this.renderGlobalStatusCard());

        // 2. Camera & Environment Section
        this.host.appendChild(makeSectionHeader("Camera & Environment"));
        this.host.appendChild(this.renderEnvironmentCard());

        // 3. Clipping Sections Section
        this.host.appendChild(this.renderSectionsSection());
    }

    private renderGlobalStatusCard(): HTMLDivElement {
        const globalCard = card();
        Object.assign(globalCard.style, { marginBottom: "10px" });

        const isDark = !!this.state.isDarkMode;
        const modeLabel = this.state.cameraMode === "orthographic" ? "Orthographic" : "Perspective";
        const bgLabel = isDark ? "Dark Mode" : "Light Mode";
        const spinText = this.state.isSpinActive ? " · Spin" : "";
        const swingText = this.state.isSwingActive ? " · Swing" : "";
        const clipText = this.sections.length > 0 ? ` · ${this.sections.length} Section${this.sections.length === 1 ? "" : "s"}` : "";

        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            gap: "8px",
        });

        const info = document.createElement("div");
        Object.assign(info.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.75)",
        });

        const dot = document.createElement("span");
        const activeState = isDark || !!this.state.isSpinActive || !!this.state.isSwingActive;
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: activeState ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: activeState ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        info.appendChild(dot);
        const textSpan = document.createElement("span");
        textSpan.textContent = `${modeLabel} · ${bgLabel}${spinText}${swingText}${clipText}`;
        info.appendChild(textSpan);
        row.appendChild(info);

        // Fast Camera Reset
        const resetBtn = makeButton("Reset View", () => {
            this.ctx.onAction("reset_view");
        });
        resetBtn.style.padding = "3px 6px";
        resetBtn.style.fontSize = "10px";
        resetBtn.title = "Reset camera position to default bounds";
        row.appendChild(resetBtn);

        globalCard.appendChild(row);
        return globalCard;
    }

    private renderEnvironmentCard(): HTMLDivElement {
        const envCard = card();
        Object.assign(envCard.style, { marginBottom: "10px", gap: "8px" });

        // Projection mode
        const projRow = document.createElement("div");
        Object.assign(projRow.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
        const projLabel = document.createElement("span");
        projLabel.textContent = "Projection Mode";
        Object.assign(projLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const projSelect = makeStyledSelect(["Perspective", "Orthographic"],
            this.state.cameraMode === "orthographic" ? "Orthographic" : "Perspective", (val) => {
                this.ctx.onAction("set_camera_mode", { mode: val.toLowerCase() });
            },
        );
        projRow.appendChild(projLabel);
        projRow.appendChild(projSelect);
        envCard.appendChild(projRow);

        // Background preset
        const bgRow = document.createElement("div");
        Object.assign(bgRow.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
        const bgLabel = document.createElement("span");
        bgLabel.textContent = "Background Color";
        Object.assign(bgLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const bgSelect = makeStyledSelect(["Dark", "Light"], this.state.isDarkMode ? "Dark" : "Light", (val) => {
            this.ctx.onAction("toggle_background", { mode: val.toLowerCase() });
        });
        bgRow.appendChild(bgLabel);
        bgRow.appendChild(bgSelect);
        envCard.appendChild(bgRow);

        // Animations (Spin & Swing)
        const animRow = document.createElement("div");
        Object.assign(animRow.style, { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" });
        animRow.appendChild(makeCheckboxRow("Auto-Rotate (Spin)", !!this.state.isSpinActive, (checked) => {
            this.ctx.onAction("toggle_spin", { enabled: checked });
        }));
        animRow.appendChild(makeCheckboxRow("Oscillate (Swing)", !!this.state.isSwingActive, (checked) => {
            this.ctx.onAction("toggle_swing", { enabled: checked });
        }));
        envCard.appendChild(animRow);

        // Fog enabled & slider
        const fogEnabled = !!this.state.fogEnabled;
        const fogIntensity = typeof this.state.fogIntensity === "number" ? this.state.fogIntensity : 0.15;

        const fogHeaderRow = makeCheckboxRow("Depth Fog", fogEnabled, (checked) => {
            this.ctx.onAction("set_fog", { enable: checked, intensity: fogIntensity });
        });
        envCard.appendChild(fogHeaderRow);

        const fogSliderRow = document.createElement("div");
        Object.assign(fogSliderRow.style, { display: "flex", flexDirection: "column", gap: "2px" });
        const fogSliderLabel = document.createElement("div");
        Object.assign(fogSliderLabel.style, { display: "flex", justifyContent: "space-between", fontSize: "10px", color: "rgba(244,244,245,0.56)" });
        fogSliderLabel.innerHTML = `<span>Fog Intensity</span><span>${Math.round(fogIntensity * 100)}%</span>`;

        const fogSlider = document.createElement("input");
        fogSlider.type = "range";
        fogSlider.min = "0.0";
        fogSlider.max = "1.0";
        fogSlider.step = "0.05";
        fogSlider.value = String(fogIntensity);
        fogSlider.disabled = !fogEnabled;
        Object.assign(fogSlider.style, {
            width: "100%", height: "4px", borderRadius: "2px",
            background: "rgba(255,255,255,0.12)", outline: "none",
            cursor: fogEnabled ? "pointer" : "not-allowed", opacity: fogEnabled ? "1" : "0.5",
        });
        fogSlider.addEventListener("change", () => {
            const intensity = parseFloat(fogSlider.value);
            this.ctx.onAction("set_fog", { enable: fogEnabled, intensity });
        });
        fogSliderRow.appendChild(fogSliderLabel);
        fogSliderRow.appendChild(fogSlider);
        envCard.appendChild(fogSliderRow);

        return envCard;
    }

    private renderSectionsSection(): HTMLDivElement {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-viewport-sections", "true");
        Object.assign(section.style, { display: "flex", flexDirection: "column", gap: "7px", paddingBottom: "10px" });

        const heading = makeSectionHeader("Clipping Sections");
        const create = makeButton("Create from selection", () => {
            this.ctx.onAction("create_section_from_selection");
        });
        create.disabled = !this.sectionSettings.systemLoaded || this.sectionSettings.activeSelectionCount === 0;
        create.title = create.disabled ? "Select atoms before creating a clipping section" : "Create at the active selection center";
        create.setAttribute("data-molsysviewer-create-section", "true");
        Object.assign(create.style, { flex: "0 0 auto", padding: "4px 7px", opacity: create.disabled ? "0.45" : "1" });
        heading.appendChild(create);
        section.appendChild(heading);

        if (this.sections.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No clipping sections";
            Object.assign(empty.style, { fontSize: "11px", color: "rgba(244,244,245,0.5)", padding: "4px 2px" });
            section.appendChild(empty);
            return section;
        }

        for (const item of this.sections) section.appendChild(this.renderSectionItem(item));
        return section;
    }

    private renderSectionItem(item: SectionSummary): HTMLDivElement {
        const cardItem = card();
        cardItem.setAttribute("data-molsysviewer-section-row", item.tag);
        if (item.hidden) cardItem.style.opacity = "0.62";

        const top = document.createElement("div");
        Object.assign(top.style, { display: "flex", alignItems: "center", gap: "6px", minWidth: "0" });
        const identity = document.createElement("div");
        Object.assign(identity.style, { display: "flex", flexDirection: "column", flex: "1 1 auto", minWidth: "0" });
        const tag = document.createElement("strong");
        tag.textContent = item.tag;
        Object.assign(tag.style, { fontSize: "11px", overflow: "hidden", textOverflow: "ellipsis", color: "#f4f4f5" });
        identity.appendChild(tag);
        if (item.owner) {
            const owner = document.createElement("span");
            owner.textContent = item.owner;
            Object.assign(owner.style, { fontSize: "9px", color: "rgba(244,244,245,0.48)" });
            identity.appendChild(owner);
        }
        top.appendChild(identity);

        const visibility = makeButton(item.hidden ? "Show" : "Hide", () => this.ctx.onAction("set_section_visibility", {
            tag: item.tag, visible: item.hidden,
        }));
        visibility.setAttribute("data-molsysviewer-section-visibility", item.tag);

        const remove = makeButton("Delete", () => this.ctx.onAction("remove_section", { tag: item.tag }));
        remove.setAttribute("data-molsysviewer-section-delete", item.tag);

        for (const btn of [visibility, remove]) {
            btn.style.flex = "0 0 auto";
            btn.style.padding = "3px 6px";
            btn.style.fontSize = "10px";
        }
        top.appendChild(visibility);
        top.appendChild(remove);
        cardItem.appendChild(top);

        cardItem.appendChild(this.vectorEditor(item, `Point (${formatUnitLabel(item.unit)})`, "point", item.point));
        cardItem.appendChild(this.vectorEditor(item, "Normal", "normal", item.normal));

        const invertRow = makeCheckboxRow("Invert clipping side", item.invert, checked => {
            this.ctx.onAction("set_section_invert", { tag: item.tag, invert: checked });
        });
        invertRow.setAttribute("data-molsysviewer-section-invert", item.tag);

        // Flip Normal button
        const flipBtn = makeButton("Flip Normal", () => {
            const flippedNormal = item.normal.map(v => -v) as [number, number, number];
            this.ctx.onAction("set_section_normal", { tag: item.tag, normal: flippedNormal });
        });
        flipBtn.style.padding = "2px 6px";
        flipBtn.style.fontSize = "9px";
        flipBtn.style.marginLeft = "auto";

        const bottomRow = document.createElement("div");
        Object.assign(bottomRow.style, { display: "flex", alignItems: "center", justifyContent: "space-between" });
        bottomRow.appendChild(invertRow);
        bottomRow.appendChild(flipBtn);
        cardItem.appendChild(bottomRow);

        return cardItem;
    }

    private vectorEditor(
        item: SectionSummary,
        labelText: string,
        kind: "point" | "normal",
        values: [number, number, number],
    ): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "grid", gridTemplateColumns: "72px repeat(3, minmax(0, 1fr))", gap: "5px", alignItems: "center" });
        const label = document.createElement("span");
        label.textContent = labelText;
        Object.assign(label.style, { fontSize: "10px", color: "rgba(244,244,245,0.62)" });
        row.appendChild(label);

        const inputs = values.map((value, axis) => {
            const input = document.createElement("input");
            input.type = "number";
            const lengthUnit = item.unit.trim().toLowerCase();
            input.step = kind === "point"
                ? (lengthUnit === "nanometer" || lengthUnit === "nanometers" || lengthUnit === "nm" ? "0.01" : "0.1")
                : "0.05";
            input.value = String(Number(value.toFixed(4)));
            input.setAttribute(`data-molsysviewer-section-${kind}-${axis}`, item.tag);
            Object.assign(input.style, {
                width: "100%", minWidth: "0", boxSizing: "border-box", fontSize: "10px",
                background: "rgba(0,0,0,0.28)", border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "4px", padding: "3px 5px", color: "#f4f4f5", outline: "none",
            });
            input.addEventListener("focus", () => this.beginCoalescing());
            input.addEventListener("pointerdown", () => this.beginCoalescing());
            input.addEventListener("change", () => {
                const vector = inputs.map(control => Number(control.value));
                if (!vector.every(Number.isFinite)) return;
                if (kind === "normal" && Math.hypot(...vector) < 1e-10) return;
                if (kind === "point" && !item.unit) return;
                this.ctx.onAction(kind === "point" ? "set_section_point" : "set_section_normal", kind === "point"
                    ? { tag: item.tag, point: { magnitude: vector, unit: item.unit } }
                    : { tag: item.tag, normal: vector });
                this.endCoalescing();
            });
            input.addEventListener("blur", () => this.endCoalescing());
            row.appendChild(input);
            return input;
        });
        return row;
    }

    private beginCoalescing(): void {
        if (this.coalescing) return;
        this.coalescing = true;
        this.ctx.onAction("begin_scene_history_coalescing");
    }

    private endCoalescing(): void {
        if (!this.coalescing) return;
        this.coalescing = false;
        this.ctx.onAction("end_scene_history_coalescing");
    }
}
