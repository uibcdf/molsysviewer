import type { SceneState } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelContext } from "./types";
import { makeButton, makeCheckboxRow, makeSectionHeader, makeStyledSelect } from "./ui-helpers";

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
 * Studio → Export subpanel: publication-quality output (PNG figure presets,
 * multi-scale rendering, publication variant sets, standalone HTML exports, and session data).
 */
export class ExportPanel extends BasePanel {
    readonly key = "export";
    private state: SceneState = {};

    constructor(private readonly ctx: PanelContext) {
        super();
    }

    setScene(state: SceneState): void {
        this.state = { ...state };
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // 1. Section Header & Global Status Card
        this.host.appendChild(makeSectionHeader("Export"));
        this.host.appendChild(this.renderGlobalStatusCard());

        // 2. Publication Figures & Images Section
        this.host.appendChild(makeSectionHeader("Publication Figures & Images"));
        this.host.appendChild(this.renderFigureCard());

        // 3. Data & Standalone Views Section
        this.host.appendChild(makeSectionHeader("Data & Standalone Views"));
        this.host.appendChild(this.renderDataCard());
    }

    private renderGlobalStatusCard(): HTMLDivElement {
        const globalCard = card();
        Object.assign(globalCard.style, { marginBottom: "10px" });

        const currentPreset = this.state.figurePreset || "publication-light";
        const currentScale = typeof this.state.figureScale === "number" ? this.state.figureScale : 2.0;
        const estWidth = Math.round(1920 * currentScale);
        const estHeight = Math.round(1080 * currentScale);
        const presetName = currentPreset.includes("dark") ? "Dark Preset" : "Light Preset";

        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
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
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: "#34d399",
            boxShadow: "0 0 6px rgba(52,211,153,0.4)",
            flexShrink: "0",
        });
        info.appendChild(dot);
        const textSpan = document.createElement("span");
        textSpan.textContent = `${currentScale.toFixed(1)}x Scale (${estWidth} × ${estHeight} px) · ${presetName}`;
        info.appendChild(textSpan);
        row.appendChild(info);

        globalCard.appendChild(row);
        return globalCard;
    }

    private renderFigureCard(): HTMLDivElement {
        const figureCard = card();
        Object.assign(figureCard.style, { marginBottom: "10px", gap: "8px" });

        const currentPreset = this.state.figurePreset || "publication-light";
        const currentScale = typeof this.state.figureScale === "number" ? this.state.figureScale : 2.0;
        const currentVariants = this.state.figureVariants || ["dark", "transparent"];
        const isTransparent = currentVariants.includes("transparent");

        const updateFigureSpec = (preset: string, scale: number, trans: boolean) => {
            const variants = ["dark"];
            if (trans) variants.push("transparent");
            this.ctx.onAction("set_figure_spec", {
                figure_preset: preset,
                figure_scale: scale,
                figure_variants: variants,
            });
        };

        // Preset selector
        const presetRow = document.createElement("div");
        Object.assign(presetRow.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
        const presetLabel = document.createElement("span");
        presetLabel.textContent = "Style Preset";
        Object.assign(presetLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const presetSelect = makeStyledSelect(["Light", "Dark"],
            currentPreset.includes("dark") ? "Dark" : "Light", (val) => {
                const presetVal = val === "Dark" ? "publication-dark" : "publication-light";
                updateFigureSpec(presetVal, currentScale, isTransparent);
            },
        );
        presetRow.appendChild(presetLabel);
        presetRow.appendChild(presetSelect);
        figureCard.appendChild(presetRow);

        // Resolution Scale dropdown
        const scaleRow = document.createElement("div");
        Object.assign(scaleRow.style, { display: "flex", justifyContent: "space-between", alignItems: "center" });
        const scaleLabel = document.createElement("span");
        scaleLabel.textContent = "Resolution Scale";
        Object.assign(scaleLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const scaleSelect = makeStyledSelect(["1.0x (FHD)", "2.0x (2K)", "3.0x (3K)", "4.0x (4K)"], `${currentScale.toFixed(1)}x (${currentScale === 1 ? "FHD" : currentScale === 2 ? "2K" : currentScale === 3 ? "3K" : "4K"})`, (val) => {
            const scaleVal = parseFloat(val);
            updateFigureSpec(currentPreset, scaleVal, isTransparent);
        });
        scaleRow.appendChild(scaleLabel);
        scaleRow.appendChild(scaleSelect);
        figureCard.appendChild(scaleRow);

        // Transparency checkbox
        figureCard.appendChild(makeCheckboxRow("Transparent Background", isTransparent, (checked) => {
            updateFigureSpec(currentPreset, currentScale, checked);
        }));

        // Action Buttons
        const downloadRow = document.createElement("div");
        Object.assign(downloadRow.style, { display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" });

        const downloadButton = makeButton("Download PNG Image", () => {
            this.ctx.onAction("download_image");
        });
        downloadButton.style.padding = "6px 10px";
        downloadButton.style.fontSize = "11px";
        downloadButton.style.fontWeight = "600";

        downloadRow.appendChild(downloadButton);
        figureCard.appendChild(downloadRow);

        return figureCard;
    }

    private renderDataCard(): HTMLDivElement {
        const dataCard = card();
        Object.assign(dataCard.style, { marginBottom: "10px", gap: "8px" });

        const htmlRow = document.createElement("div");
        Object.assign(htmlRow.style, { display: "flex", flexDirection: "column", gap: "6px" });
        const htmlLabel = document.createElement("span");
        htmlLabel.textContent = "Save standalone interactive view as HTML page";
        Object.assign(htmlLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)" });

        const htmlButton = makeButton("Download Standalone HTML View", () => {
            this.ctx.onAction("export_html");
        });
        htmlButton.style.padding = "5px 10px";
        htmlButton.style.fontSize = "11px";

        htmlRow.appendChild(htmlLabel);
        htmlRow.appendChild(htmlButton);
        dataCard.appendChild(htmlRow);

        return dataCard;
    }
}
