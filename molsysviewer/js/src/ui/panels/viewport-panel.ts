import type { SceneState, SectionSettings, SectionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelContext } from "./types";
import { makeButton, makeCheckboxRow, makeSectionHeader, makeSettingsCard, makeStyledSelect } from "./ui-helpers";

/**
 * Studio → Viewport subpanel: live camera and render configuration
 * (background, spin/swing, projection mode, fog). Reads the current
 * `SceneState` pushed from the controller and emits scene actions.
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
        viewportCard.appendChild(makeCheckboxRow("Auto-Rotate (Spin)", !!this.state.isSpinActive, (checked) => {
            this.ctx.onAction("toggle_spin", { enabled: checked });
        }));

        // A3. Swing toggle
        viewportCard.appendChild(makeCheckboxRow("Oscillate (Swing)", !!this.state.isSwingActive, (checked) => {
            this.ctx.onAction("toggle_swing", { enabled: checked });
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

        this.host.appendChild(this.renderSections());
    }

    private renderSections(): HTMLDivElement {
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
            Object.assign(empty.style, { fontSize: "11px", color: "rgba(244,244,245,0.5)", padding: "6px 2px" });
            section.appendChild(empty);
            return section;
        }

        for (const item of this.sections) section.appendChild(this.renderSectionItem(item));
        return section;
    }

    private renderSectionItem(item: SectionSummary): HTMLDivElement {
        const card = document.createElement("div");
        card.setAttribute("data-molsysviewer-section-row", item.tag);
        Object.assign(card.style, {
            display: "flex", flexDirection: "column", gap: "7px", padding: "8px",
            border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px",
            background: "rgba(255,255,255,0.035)", opacity: item.hidden ? "0.62" : "1",
        });

        const top = document.createElement("div");
        Object.assign(top.style, { display: "flex", alignItems: "center", gap: "6px", minWidth: "0" });
        const identity = document.createElement("div");
        Object.assign(identity.style, { display: "flex", flexDirection: "column", flex: "1 1 auto", minWidth: "0" });
        const tag = document.createElement("strong");
        tag.textContent = item.tag;
        Object.assign(tag.style, { fontSize: "11px", overflow: "hidden", textOverflow: "ellipsis" });
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
        Object.assign(visibility.style, { flex: "0 0 auto" });
        Object.assign(remove.style, { flex: "0 0 auto" });
        top.appendChild(visibility);
        top.appendChild(remove);
        card.appendChild(top);

        card.appendChild(this.vectorEditor(item, "Point (nm)", "point", item.point));
        card.appendChild(this.vectorEditor(item, "Normal", "normal", item.normal));
        const invert = makeCheckboxRow("Invert clipping side", item.invert, checked => {
            this.ctx.onAction("set_section_invert", { tag: item.tag, invert: checked });
        });
        invert.setAttribute("data-molsysviewer-section-invert", item.tag);
        card.appendChild(invert);
        return card;
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
            input.step = kind === "point" ? "0.01" : "0.05";
            input.value = String(Number(value.toFixed(4)));
            input.setAttribute(`data-molsysviewer-section-${kind}-${axis}`, item.tag);
            Object.assign(input.style, { width: "100%", minWidth: "0", boxSizing: "border-box", fontSize: "10px" });
            input.addEventListener("focus", () => this.beginCoalescing());
            input.addEventListener("pointerdown", () => this.beginCoalescing());
            input.addEventListener("change", () => {
                const vector = inputs.map(control => Number(control.value));
                if (!vector.every(Number.isFinite)) return;
                if (kind === "normal" && Math.hypot(...vector) < 1e-10) return;
                this.ctx.onAction(kind === "point" ? "set_section_point" : "set_section_normal", kind === "point"
                    ? { tag: item.tag, point: { magnitude: vector, unit: "nm" } }
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
