import type { SceneState } from "../group-panel";
import { PanelContext, StudioPanel } from "./types";
import { makeButton, makeCheckboxRow, makeSectionHeader, makeSettingsCard, makeStyledSelect } from "./ui-helpers";

/**
 * Studio → Export subpanel: publication-quality output (PNG figure preset,
 * resolution scale, transparency, and standalone HTML export). Reads the
 * current `SceneState` and emits export actions.
 */
export class ExportPanel implements StudioPanel {
    readonly key = "export";
    private host: HTMLElement | null = null;
    private state: SceneState = {};

    constructor(private readonly ctx: PanelContext) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    setScene(state: SceneState): void {
        this.state = { ...state };
        this.render();
    }

    private render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Export Settings"));

        const grid = document.createElement("div");
        Object.assign(grid.style, {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            paddingBottom: "10px",
        });
        this.host.appendChild(grid);

        // C. Figure Export Card
        const exportCard = makeSettingsCard("Figure Export");
        grid.appendChild(exportCard);

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

        // C1. Preset selector
        const presetRow = document.createElement("div");
        Object.assign(presetRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const presetLabel = document.createElement("span");
        presetLabel.textContent = "Preset";
        Object.assign(presetLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const presetSelect = makeStyledSelect(["Light", "Dark"],
            currentPreset.includes("dark") ? "Dark" : "Light", (val) => {
                const presetVal = val === "Dark" ? "publication-dark" : "publication-light";
                updateFigureSpec(presetVal, currentScale, isTransparent);
            },
        );
        presetRow.appendChild(presetLabel);
        presetRow.appendChild(presetSelect);
        exportCard.appendChild(presetRow);

        // C2. Resolution Scale dropdown
        const scaleRow = document.createElement("div");
        Object.assign(scaleRow.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });
        const scaleLabel = document.createElement("span");
        scaleLabel.textContent = "Resolution Scale";
        Object.assign(scaleLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        const scaleSelect = makeStyledSelect(["1.0x", "2.0x", "3.0x", "4.0x"], `${currentScale.toFixed(1)}x`, (val) => {
            const scaleVal = parseFloat(val.replace("x", ""));
            updateFigureSpec(currentPreset, scaleVal, isTransparent);
        });
        scaleRow.appendChild(scaleLabel);
        scaleRow.appendChild(scaleSelect);
        exportCard.appendChild(scaleRow);

        // C3. Transparency checkbox
        exportCard.appendChild(makeCheckboxRow("Transparent Background", isTransparent, (checked) => {
            updateFigureSpec(currentPreset, currentScale, checked);
        }));

        // C4. Download button
        const downloadRow = document.createElement("div");
        Object.assign(downloadRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            width: "100%",
            marginTop: "6px",
        });
        const downloadButton = makeButton("Download Image File", () => {
            this.ctx.onAction("download_image");
        });
        downloadRow.appendChild(downloadButton);
        exportCard.appendChild(downloadRow);

        // D. Data & State Card
        const dataCard = makeSettingsCard("Data & State");
        grid.appendChild(dataCard);

        const htmlRow = document.createElement("div");
        Object.assign(htmlRow.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            width: "100%",
        });
        const htmlLabel = document.createElement("span");
        htmlLabel.textContent = "Save standalone view as HTML page";
        Object.assign(htmlLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)" });
        const htmlButton = makeButton("Download HTML View", () => {
            this.ctx.onAction("export_html");
        });
        htmlRow.appendChild(htmlLabel);
        htmlRow.appendChild(htmlButton);
        dataCard.appendChild(htmlRow);
    }
}
