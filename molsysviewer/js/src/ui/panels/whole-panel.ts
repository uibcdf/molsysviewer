import type { WholeDetails, WholeSummary } from "../group-panel";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { PanelContext, StudioPanel } from "./types";
import { FALLBACK_PRESETS, FALLBACK_REPRESENTATIONS, bindContinuousHistory, createStyleDraftControls } from "./style-composer";

function labelFromToken(value: string): string {
    return value
        .replace(/_/g, " ")
        .replace(/-/g, " ")
        .replace(/\b\w/g, letter => letter.toUpperCase());
}

function row(label: string, control: HTMLElement): HTMLDivElement {
    const item = document.createElement("div");
    Object.assign(item.style, {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "8px",
        width: "100%",
    });
    const text = document.createElement("span");
    text.textContent = label;
    Object.assign(text.style, {
        fontSize: "11px",
        color: "rgba(244,244,245,0.7)",
    });
    item.appendChild(text);
    item.appendChild(control);
    return item;
}

function card(): HTMLDivElement {
    const el = document.createElement("div");
    Object.assign(el.style, {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "10px",
        borderRadius: "6px",
        background: "rgba(255,255,255,0.035)",
        border: "1px solid rgba(255,255,255,0.08)",
    });
    return el;
}

function note(text: string, warning = false): HTMLDivElement {
    const el = document.createElement("div");
    el.textContent = text;
    Object.assign(el.style, {
        fontSize: "10px",
        color: warning ? "#fbbf24" : "rgba(244,244,245,0.6)",
        borderLeft: `2px solid ${warning ? "rgba(251,191,36,0.5)" : "rgba(99,102,241,0.4)"}`,
        paddingLeft: "6px",
        lineHeight: "1.35",
    });
    return el;
}

export class WholePanel implements StudioPanel {
    readonly key = "whole";
    private host: HTMLElement | null = null;
    private visible = false;
    private summary: WholeSummary | null = null;
    private details: WholeDetails | null = null;
    private requestId = 0;
    private continuousHistoryEdit = false;
    private continuousHistoryRenderPending = false;
    private historyState = { canUndo: false, canRedo: false };

    constructor(private readonly ctx: PanelContext) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    setVisible(visible: boolean): void {
        this.visible = visible;
        if (visible) {
            this.render();
        }
    }

    setSummary(summary: WholeSummary | null): void {
        this.summary = summary;
        this.ctx.setBadge(summary ? (summary.visible ? "Visible" : "Hidden") : "None");
        if (this.continuousHistoryEdit) {
            this.continuousHistoryRenderPending = true;
        } else {
            this.render();
        }
    }

    updateDetails(details: WholeDetails): void {
        this.details = details;
        this.render();
    }

    updateHistory(state: { canUndo: boolean; canRedo: boolean }): void {
        this.historyState = state;
        this.render();
    }
    private render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        Object.assign(this.host.style, {
            flexDirection: "column",
            gap: "12px",
            minHeight: "0",
        });
        this.host.appendChild(makeSectionHeader("Whole"));
        if (!this.summary) {
            const empty = document.createElement("div");
            empty.textContent = "No whole summary received yet.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.56)", fontSize: "12px" });
            this.host.appendChild(empty);
            return;
        }
        this.host.appendChild(this.renderPresenceHero());
        this.host.appendChild(this.renderRepresentation());
        this.host.appendChild(this.renderColour());
    }

    private renderPresenceHero(): HTMLDivElement {
        const summary = this.summary!;
        const section = card();
        section.setAttribute("data-molsysviewer-whole-presence", "true");

        // Header bar with Title, Status Dot, and 3 Actions: [ Hide / Show ] [ Undo ] [ Reset ]
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            flexWrap: "wrap",
        });

        const title = document.createElement("div");
        Object.assign(title.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            color: "#f4f4f5",
            fontWeight: "700",
            fontSize: "12px",
        });

        const dot = document.createElement("span");
        dot.setAttribute("data-molsysviewer-whole-visible-dot", String(summary.visible));
        Object.assign(dot.style, {
            width: "7px",
            height: "7px",
            borderRadius: "999px",
            background: summary.visible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: summary.visible ? "0 0 8px rgba(52,211,153,0.5)" : "none",
            flexShrink: "0",
        });
        title.appendChild(dot);
        title.appendChild(document.createTextNode("Whole Structure"));
        header.appendChild(title);

        // Action Buttons: Hide/Show, Undo, Reset
        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            alignItems: "center",
            gap: "4px",
            flexWrap: "nowrap",
        });

        const toggle = makeButton(summary.visible ? "Hide" : "Show", () => {
            if (summary.visible && summary.none_state_region_count > 0) {
                const ok = window.confirm(`${summary.none_state_region_count} region(s) have no own representation and will disappear while the whole is hidden.`);
                if (!ok) return;
            }
            this.ctx.onAction("set_whole_visibility", { visible: !summary.visible });
        });
        toggle.setAttribute("data-molsysviewer-whole-visibility", summary.visible ? "hide" : "show");
        actions.appendChild(toggle);

        const undoBtn = makeButton("↶ Undo", () => {
            this.ctx.onAction("undo_active_selection");
        });
        undoBtn.setAttribute("data-molsysviewer-whole-undo", "true");
        undoBtn.title = "Undo last action";
        undoBtn.disabled = !this.historyState.canUndo;
        if (undoBtn.disabled) {
            undoBtn.style.opacity = "0.42";
            undoBtn.style.cursor = "not-allowed";
        }
        actions.appendChild(undoBtn);

        const redoBtn = makeButton("↷ Redo", () => {
            this.ctx.onAction("redo_active_selection");
        });
        redoBtn.setAttribute("data-molsysviewer-whole-redo", "true");
        redoBtn.title = "Redo last action";
        redoBtn.disabled = !this.historyState.canRedo;
        if (redoBtn.disabled) {
            redoBtn.style.opacity = "0.42";
            redoBtn.style.cursor = "not-allowed";
        }
        actions.appendChild(redoBtn);

        const resetBtn = makeButton("Reset", () => {
            this.ctx.onAction("reset_whole_representation");
            this.ctx.onAction("reset_whole_colors");
        });
        resetBtn.title = "Reset whole representation and colors to base";
        actions.appendChild(resetBtn);

        header.appendChild(actions);
        section.appendChild(header);

        // System information summary (integrated into Card 1)
        const composition = summary.composition ?? this.details?.composition;
        const contains = summary.contains ?? this.details?.contains;

        if (composition && (composition.atoms || composition.groups || composition.chains || composition.molecules)) {
            const infoLine = document.createElement("div");
            infoLine.setAttribute("data-molsysviewer-whole-inspect-details", "true");
            infoLine.textContent = [
                `${composition.atoms ?? 0} atoms`,
                `${composition.groups ?? 0} groups`,
                `${composition.chains ?? 0} chains`,
                `${composition.molecules ?? 0} molecules`,
            ].join(" · ");
            Object.assign(infoLine.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.75)",
                marginTop: "4px",
            });
            section.appendChild(infoLine);
        }

        if (contains) {
            const presentItems: string[] = [];
            for (const [key, val] of Object.entries(contains)) {
                if (val === true) {
                    presentItems.push(`1 ${key}`);
                } else if (typeof val === "number" && val > 0) {
                    const label = val === 1 ? key : `${key}s`;
                    presentItems.push(`${val} ${label}`);
                }
            }
            if (presentItems.length > 0) {
                const containsLine = document.createElement("div");
                containsLine.textContent = `Contains: ${presentItems.join(" · ")}`;
                Object.assign(containsLine.style, {
                    fontSize: "11px",
                    color: "#38bdf8",
                    fontWeight: "500",
                    marginTop: "2px",
                });
                section.appendChild(containsLine);
            }
        }

        if (summary.none_state_region_count > 0) {
            section.appendChild(note(`${summary.none_state_region_count} region(s) have no representation of their own and will disappear.`, true));
        }

        return section;
    }

    private renderRepresentation(): HTMLDivElement {
        const summary = this.summary!;
        const params = summary.params ?? {};
        const section = card();
        section.setAttribute("data-molsysviewer-whole-representation", "true");

        // Card section title
        const cardTitle = document.createElement("div");
        cardTitle.textContent = "Representation";
        Object.assign(cardTitle.style, {
            fontSize: "11px",
            fontWeight: "700",
            letterSpacing: "0.04em",
            color: "rgba(244,244,245,0.85)",
            marginBottom: "2px",
        });
        section.appendChild(cardTitle);

        if (summary.scene_style_name) {
            section.appendChild(note(`Scene style: ${summary.scene_style_name}. Editing below clears this name.`));
        }

        const controls = createStyleDraftControls({
            id: "true",
            dataPrefix: "whole",
            representations: [{ value: "", label: "Base" }, ...FALLBACK_REPRESENTATIONS],
            presets: FALLBACK_PRESETS,
            currentRepresentation: summary.representation,
            currentPreset: summary.preset,
            params,
        });

        const representation = controls.representationSelect;
        const preset = controls.presetSelect;
        const opacity = controls.opacityInput;
        const quality = controls.qualitySelect;

        // Apply on-the-fly when selects change
        const triggerLiveUpdate = () => {
            this.ctx.onAction("set_whole_representation", {
                ...(preset.value ? { preset: preset.value } : representation.value ? { representation: representation.value } : {}),
                params: { ...params, alpha: Number(opacity.value), quality: quality.value },
            });
        };

        representation.addEventListener("change", triggerLiveUpdate);
        preset.addEventListener("change", triggerLiveUpdate);
        quality.addEventListener("change", triggerLiveUpdate);

        section.appendChild(controls.representationRow);
        section.appendChild(controls.presetRow);

        bindContinuousHistory(
            opacity,
            () => {
                this.continuousHistoryEdit = true;
                this.ctx.onAction("begin_scene_history_coalescing");
            },
            () => {
                this.ctx.onAction("end_scene_history_coalescing");
                this.continuousHistoryEdit = false;
                if (!this.continuousHistoryRenderPending) return;
                this.continuousHistoryRenderPending = false;
                setTimeout(() => this.render(), 0);
            },
        );

        opacity.addEventListener("input", () => {
            this.ctx.onAction("set_whole_representation", {
                ...(preset.value ? { preset: preset.value } : representation.value ? { representation: representation.value } : {}),
                params: { ...params, alpha: Number(opacity.value), quality: quality.value },
            });
        });

        section.appendChild(controls.opacityRow);
        section.appendChild(controls.qualityRow);

        if (summary.inheriting_region_count > 0) {
            section.appendChild(note(`${summary.inheriting_region_count} region(s) inherit this representation and will follow it.`));
        }

        return section;
    }

    private renderColour(): HTMLDivElement {
        const summary = this.summary!;
        const section = card();
        section.setAttribute("data-molsysviewer-whole-colour", "true");

        // Card section title
        const cardTitle = document.createElement("div");
        cardTitle.textContent = "Color Scheme";
        Object.assign(cardTitle.style, {
            fontSize: "11px",
            fontWeight: "700",
            letterSpacing: "0.04em",
            color: "rgba(244,244,245,0.85)",
            marginBottom: "2px",
        });
        section.appendChild(cardTitle);

        const scheme = makeStyledSelect(
            (summary.color_schemes || []).length
                ? summary.color_schemes.map(value => ({ value, label: labelFromToken(value) }))
                : [{ value: "", label: "No schemes available" }],
            summary.color_scheme ?? "",
            value => {
                if (value) this.ctx.onAction("set_whole_color_scheme", { scheme: value });
            },
        );
        scheme.setAttribute("data-molsysviewer-whole-color-scheme", "true");
        section.appendChild(row("Theme", scheme));

        const uniform = document.createElement("input");
        uniform.type = "color";
        uniform.value = "#3b82f6";
        uniform.setAttribute("data-molsysviewer-whole-uniform-color", "true");
        uniform.addEventListener("change", () => {
            this.ctx.onAction("set_whole_representation", {
                representation: summary.representation ?? undefined,
                preset: summary.preset ?? undefined,
                params: { ...summary.params, color: uniform.value },
            });
        });
        section.appendChild(row("Uniform", uniform));

        const attrWrap = document.createElement("div");
        Object.assign(attrWrap.style, { display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" });
        const attr = makeStyledSelect([{ value: "", label: "None" }, ...(summary.available_attributes || [])], "", () => {});
        attr.setAttribute("data-molsysviewer-whole-color-attribute", "true");
        const palette = makeStyledSelect(["viridis", "plasma", "magma", "inferno", "cividis", "turbo"], "viridis", () => {});
        palette.setAttribute("data-molsysviewer-whole-color-attribute-palette", "true");
        const range = document.createElement("input");
        range.type = "text";
        range.placeholder = "range min,max";
        range.setAttribute("data-molsysviewer-whole-color-attribute-range", "true");
        Object.assign(range.style, {
            width: "86px",
            background: "rgba(0,0,0,0.28)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "3px 6px",
            color: "#f4f4f5",
            fontSize: "11px",
        });

        const commit = makeButton("Apply", () => {
            if (!attr.value) return;
            const parsed = range.value.split(",").map(part => Number(part.trim())).filter(value => Number.isFinite(value));
            this.ctx.onAction("color_whole_by_attribute", {
                attribute: attr.value,
                element: "atom",
                palette: palette.value,
                ...(parsed.length === 2 ? { value_range: [parsed[0], parsed[1]] } : {}),
                replace: true,
            });
        });
        commit.setAttribute("data-molsysviewer-whole-color-attribute-apply", "true");

        attrWrap.appendChild(attr);
        attrWrap.appendChild(palette);
        attrWrap.appendChild(range);
        attrWrap.appendChild(commit);
        section.appendChild(row("Colour by", attrWrap));

        section.appendChild(note(`Base layer · covered by ${summary.covering_layer_count} region layer(s).`));

        return section;
    }
}
