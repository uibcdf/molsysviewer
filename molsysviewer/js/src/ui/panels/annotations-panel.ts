import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { ManualQueryComposer } from "../query-composer";

export type AnnotationLabelStyle = {
    color?: string;
    size_em?: number;
    background?: boolean;
    background_opacity?: number;
};

export type AnnotationSummary = {
    kind: string;
    tag: string;
    owner?: string;
    layerTag?: string;
    text: string;
    hidden: boolean;
    nAtoms: number;
    atomIndices: number[];
    anchor: { type: string; indices: number[] };
    style: AnnotationLabelStyle;
    broken: boolean;
    brokenReason?: string;
};

export type AnnotationSettings = {
    systemLoaded: boolean;
    activeSelectionCount: number;
};

const defaultStyle = (): Required<AnnotationLabelStyle> => ({
    color: "#ffffff",
    size_em: 1,
    background: true,
    background_opacity: 0.6,
});

const emptySelection = (): ActiveSelectionPayload => ({
    event: "interaction_active_selection_changed",
    source_kind: "empty",
    target_level: "none",
    element_level: "none",
    items: [],
    atom_indices: [],
    group_indices: [],
    component_indices: [],
    chain_indices: [],
    molecule_indices: [],
    entity_indices: [],
    count_atoms: 0,
    count_groups: 0,
    count_shapes: 0,
    count_annotations: 0,
});

const INPUT_STYLE = {
    background: "rgba(0,0,0,0.2)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "6px",
    padding: "4px 6px",
    color: "#fff",
    fontSize: "11px",
    outline: "none",
};

function card(): HTMLDivElement {
    const element = document.createElement("div");
    Object.assign(element.style, {
        display: "flex", flexDirection: "column", gap: "7px", padding: "10px",
        borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.035)",
    });
    return element;
}

function resolvedStyle(style: AnnotationLabelStyle): Required<AnnotationLabelStyle> {
    return { ...defaultStyle(), ...style };
}

export class AnnotationsPanel extends BasePanel {
    readonly key = "annotations";
    private annotations: AnnotationSummary[] = [];
    private settings: AnnotationSettings = { systemLoaded: false, activeSelectionCount: 0 };
    private selection = emptySelection();
    private savedSelections: SavedSelectionSummary[] = [];
    private newText = "";
    private nextStyle = defaultStyle();
    private editTextTag: string | null = null;
    private editDetailsTag: string | null = null;
    private selectedTag: string | null = null;
    private coalescing = false;

    private anchorType: "selection" | "coordinates" = "selection";
    private customPosition: [number, number, number] = [0.0, 0.0, 0.0];
    private nextOffsetMode: "camera" | "world" = "camera";
    private nextOffset: [number, number, number] = [0.0, 0.0, 0.0];
    private nextLeaderLine = false;
    private nextLeaderLineStyle: "solid" | "dashed" | "dotted" = "dashed";
    private stagedAnchor: number[] | null = null;

    private annotationsQueryComposer: ManualQueryComposer | null = null;
    private annotationsCheatSheetOpen = false;

    constructor(
        private readonly ctx: PanelContext,
        private readonly onFocus: (atomIndices: number[]) => void,
    ) { super(); }

    setAnnotations(items: AnnotationSummary[], settings: AnnotationSettings): void {
        this.annotations = [...items];
        this.settings = settings;
        if (this.selectedTag && !items.some(item => item.tag === this.selectedTag)) {
            this.selectedTag = null;
        }
        this.ctx.setBadge(String(items.length));
        this.scheduleRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.scheduleRender();
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.selection = selection;
        this.scheduleRender();
    }

    private isSavedSelectionActive(saved: SavedSelectionSummary): boolean {
        if (this.selection.atom_indices.length !== saved.atom_count) return false;
        const set = new Set(this.selection.atom_indices);
        for (const idx of saved.atom_indices) {
            if (!set.has(idx)) return false;
        }
        return true;
    }

    private getAnnotationsQueryComposer(): ManualQueryComposer {
        if (!this.annotationsQueryComposer) {
            const helpBtn = makeButton("?", () => {
                this.annotationsCheatSheetOpen = !this.annotationsCheatSheetOpen;
                this.scheduleRender();
            });
            helpBtn.setAttribute("data-molsysviewer-annotation-cheatsheet-toggle", "true");
            Object.assign(helpBtn.style, {
                flex: "0 0 30px",
                width: "30px",
                padding: "6px 0",
                fontWeight: "700",
            });

            this.annotationsQueryComposer = new ManualQueryComposer(
                "annotations",
                (details) => {
                    this.ctx.onAction("selection_query_preview_request", details);
                },
                () => {},
                {
                    buttonLabel: "Select",
                    hideSyntax: true,
                    middleElement: helpBtn
                }
            );
        }
        return this.annotationsQueryComposer;
    }

    /** Query composer previews for annotations. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        if (!this.annotationsQueryComposer) return false;
        const updated = this.annotationsQueryComposer.updatePreview(preview);
        if (updated && preview.ok === true) {
            const { expression, syntax } = this.annotationsQueryComposer.value();
            if (expression) {
                this.ctx.onAction("apply_selection_query", {
                    expression,
                    syntax,
                    op: "replace",
                });
            }
        }
        return updated;
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // 1. Header and Global Actions
        this.host.appendChild(makeSectionHeader("Annotations"));
        this.host.appendChild(this.renderGlobalActions());

        // 2. New Annotation Card
        this.host.appendChild(makeSectionHeader("New annotation"));
        const newAnnotationContainer = document.createElement("div");
        this.renderNewAnnotationElements(newAnnotationContainer);
        this.host.appendChild(newAnnotationContainer);

        // 3. Saved Annotations List
        this.host.appendChild(makeSectionHeader("Saved annotations"));
        const list = document.createElement("div");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "7px" });
        if (this.annotations.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No annotations yet.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "11px" });
            list.appendChild(empty);
        } else {
            for (const item of this.annotations) {
                list.appendChild(this.renderAnnotation(item));
            }
        }
        this.host.appendChild(list);
    }

    private selectionCount(): number {
        return this.selection.count_atoms || this.selection.atom_indices.length || this.settings.activeSelectionCount;
    }

    private renderNewAnnotationElements(parent: HTMLElement): void {
        const activeCount = this.selection.atom_indices.length;
        const hasActive = activeCount > 0;
        const canCreate = this.anchorType === "coordinates" ? !!this.newText.trim() : (this.stagedAnchor !== null && !!this.newText.trim());

        // 1. Creation Input Form & Style Selection (At the top of the section)
        const createCard = card();
        createCard.setAttribute("data-molsysviewer-annotation-create-card", "true");
        Object.assign(createCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            marginBottom: "10px",
        });

        const formRow = document.createElement("div");
        Object.assign(formRow.style, {
            display: "flex",
            gap: "6px",
            width: "100%",
        });

        const textInput = document.createElement("input");
        textInput.type = "text";
        textInput.value = this.newText;
        textInput.placeholder = "Annotation text...";
        Object.assign(textInput.style, {
            flex: "1 1 auto",
            ...INPUT_STYLE,
        });
        textInput.setAttribute("data-molsysviewer-annotation-create-text", "true");
        formRow.appendChild(textInput);

        const addBtn = makeButton("Create", () => {
            const text = textInput.value.trim();
            if (!text) return;
            this.newText = "";
            const atomIndices = this.anchorType === "selection" ? (this.stagedAnchor || []) : undefined;
            this.stagedAnchor = null;
            this.ctx.onAction("create_annotation", {
                text,
                label_style: { ...this.nextStyle },
                position: this.anchorType === "coordinates" ? [...this.customPosition] : undefined,
                atom_indices: atomIndices,
                offset_mode: this.nextOffsetMode,
                offset: [...this.nextOffset],
                leader_line: this.nextLeaderLine,
                leader_line_style: this.nextLeaderLineStyle,
            });
        });
        addBtn.setAttribute("data-molsysviewer-annotation-create-confirm", "true");
        addBtn.disabled = !this.settings.systemLoaded || !canCreate;
        addBtn.style.opacity = addBtn.disabled ? "0.42" : "1";
        Object.assign(addBtn.style, {
            flex: "0 0 auto",
            background: "#6366f1",
            border: "0",
            borderRadius: "6px",
            padding: "4px 10px",
            color: "#fff",
            fontSize: "11px",
            fontWeight: "600",
            cursor: "pointer",
        });
        formRow.appendChild(addBtn);
        createCard.appendChild(formRow);

        textInput.addEventListener("input", () => {
            this.newText = textInput.value;
            const updatedCanCreate = this.anchorType === "coordinates" ? !!this.newText.trim() : (this.stagedAnchor !== null && !!this.newText.trim());
            addBtn.disabled = !this.settings.systemLoaded || !updatedCanCreate;
            addBtn.style.opacity = addBtn.disabled ? "0.42" : "1";
        });
        textInput.addEventListener("keydown", event => {
            if (event.key === "Enter" && !addBtn.disabled) addBtn.click();
        });

        // Compact Style Row
        const styleRow = document.createElement("div");
        Object.assign(styleRow.style, {
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px 12px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
        });

        // Color Picker
        const colorLabel = document.createElement("label");
        Object.assign(colorLabel.style, {
            display: "flex",
            alignItems: "center",
            gap: "4px",
            cursor: "pointer",
        });
        colorLabel.appendChild(document.createTextNode("Color"));
        const colorInput = document.createElement("input");
        colorInput.type = "color";
        colorInput.value = this.nextStyle.color || "#ffffff";
        Object.assign(colorInput.style, {
            width: "18px",
            height: "18px",
            border: "1px solid rgba(255,255,255,0.2)",
            borderRadius: "4px",
            background: "transparent",
            padding: "0",
            cursor: "pointer",
        });
        colorInput.addEventListener("input", () => {
            this.nextStyle.color = colorInput.value;
            this.scheduleRender();
        });
        colorLabel.appendChild(colorInput);
        styleRow.appendChild(colorLabel);

        // Size Slider
        const sizeLabel = document.createElement("label");
        Object.assign(sizeLabel.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            flex: "1 1 0",
            minWidth: "60px",
            cursor: "pointer",
        });
        sizeLabel.appendChild(document.createTextNode("Size"));
        const sizeInput = document.createElement("input");
        sizeInput.type = "range";
        sizeInput.min = "0.5";
        sizeInput.max = "3";
        sizeInput.step = "0.1";
        sizeInput.value = String(this.nextStyle.size_em || 1);
        Object.assign(sizeInput.style, {
            flex: "1 1 0",
            height: "4px",
            borderRadius: "2px",
            background: "rgba(255,255,255,0.2)",
            outline: "none",
            cursor: "pointer",
        });
        sizeInput.addEventListener("input", () => {
            this.nextStyle.size_em = Number(sizeInput.value);
        });
        sizeInput.addEventListener("change", () => {
            this.scheduleRender();
        });
        sizeLabel.appendChild(sizeInput);
        styleRow.appendChild(sizeLabel);

        // Background Checkbox
        const bgLabel = document.createElement("label");
        Object.assign(bgLabel.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            cursor: "pointer",
        });
        const bgInput = document.createElement("input");
        bgInput.type = "checkbox";
        bgInput.checked = this.nextStyle.background !== false;
        Object.assign(bgInput.style, {
            cursor: "pointer",
        });
        bgLabel.appendChild(bgInput);
        bgLabel.appendChild(document.createTextNode("Bg"));
        styleRow.appendChild(bgLabel);

        // Background Opacity Slider
        const opacityLabel = document.createElement("label");
        Object.assign(opacityLabel.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            cursor: "pointer",
        });
        opacityLabel.appendChild(document.createTextNode("Bg Opacity"));
        const opacityInput = document.createElement("input");
        opacityInput.type = "range";
        opacityInput.min = "0";
        opacityInput.max = "1";
        opacityInput.step = "0.05";
        opacityInput.value = String(this.nextStyle.background_opacity ?? 0.9);
        Object.assign(opacityInput.style, {
            width: "50px",
            height: "4px",
            borderRadius: "2px",
            background: "rgba(255,255,255,0.2)",
            outline: "none",
            cursor: "pointer",
        });
        opacityInput.addEventListener("input", () => {
            this.nextStyle.background_opacity = Number(opacityInput.value);
        });
        opacityInput.addEventListener("change", () => {
            this.scheduleRender();
        });
        opacityLabel.appendChild(opacityInput);
        styleRow.appendChild(opacityLabel);

        // Update opacity visibility/enabled state based on background checkbox
        const updateOpacityState = () => {
            const hasBg = bgInput.checked;
            opacityInput.disabled = !hasBg;
            opacityLabel.style.opacity = hasBg ? "1" : "0.35";
        };
        updateOpacityState();

        bgInput.addEventListener("change", () => {
            this.nextStyle.background = bgInput.checked;
            updateOpacityState();
            this.scheduleRender();
        });

        createCard.appendChild(styleRow);

        // Offset & Tether Row
        const offsetRow = document.createElement("div");
        Object.assign(offsetRow.style, {
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px 12px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            marginTop: "6px",
            paddingTop: "6px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
        });

        // Offset Mode Dropdown
        const modeLabel = document.createElement("label");
        Object.assign(modeLabel.style, { display: "flex", alignItems: "center", gap: "4px" });
        modeLabel.appendChild(document.createTextNode("Offset Mode"));
        const modeSelect = makeStyledSelect([
            { value: "camera", label: "Camera Space" },
            { value: "world", label: "World Space" },
        ], this.nextOffsetMode, (val) => {
            this.nextOffsetMode = val as any;
            this.scheduleRender();
        });
        Object.assign(modeSelect.style, { padding: "2px 4px", fontSize: "10px" });
        modeLabel.appendChild(modeSelect);
        offsetRow.appendChild(modeLabel);

        // Offset Coordinates (X, Y, Z sliders or numbers)
        const unit = this.nextOffsetMode === "camera" ? "px" : "nm";
        ["X", "Y", "Z"].forEach((axis, idx) => {
            const axisLabel = document.createElement("label");
            Object.assign(axisLabel.style, { display: "flex", alignItems: "center", gap: "2px" });
            axisLabel.appendChild(document.createTextNode(`${axis} (${unit}):`));
            const valInput = document.createElement("input");
            valInput.type = "number";
            valInput.step = "0.5";
            valInput.value = String(this.nextOffset[idx]);
            Object.assign(valInput.style, {
                width: "45px",
                background: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "4px",
                padding: "2px 4px",
                color: "#fff",
                fontSize: "10px",
                textAlign: "center",
            });
            valInput.addEventListener("input", () => {
                this.nextOffset[idx] = Number(valInput.value) || 0.0;
            });
            axisLabel.appendChild(valInput);
            offsetRow.appendChild(axisLabel);
        });

        // Leader Line Checkbox
        const lineLabel = document.createElement("label");
        Object.assign(lineLabel.style, { display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" });
        const lineCheckbox = document.createElement("input");
        lineCheckbox.type = "checkbox";
        lineCheckbox.checked = this.nextLeaderLine;
        lineCheckbox.addEventListener("change", () => {
            this.nextLeaderLine = lineCheckbox.checked;
            this.scheduleRender();
        });
        lineLabel.appendChild(lineCheckbox);
        lineLabel.appendChild(document.createTextNode("Leader Line"));
        offsetRow.appendChild(lineLabel);

        createCard.appendChild(offsetRow);

        const hint = document.createElement("div");
        if (!this.settings.systemLoaded) {
            hint.textContent = "Load a structure first.";
        } else if (this.anchorType === "coordinates") {
            hint.textContent = "Anchored to the absolute coordinates specified below.";
        } else if (this.stagedAnchor === null) {
            hint.textContent = "Select atoms to anchor the annotation and click Anchor.";
        } else {
            const cnt = this.stagedAnchor.length;
            const desc = cnt === 1 ? "1 atom" : `centroid of ${cnt} atoms`;
            hint.textContent = `Anchored to the active selection (${desc})`;
        }
        Object.assign(hint.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)", marginTop: "2px" });
        createCard.appendChild(hint);

        parent.appendChild(createCard);

        // 2. Anchor Toggle Choice Row
        const anchorRow = document.createElement("div");
        Object.assign(anchorRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            marginBottom: "10px",
            padding: "8px 10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.04)",
        });
        anchorRow.appendChild(document.createTextNode("Anchor:"));

        const selRadioLabel = document.createElement("label");
        Object.assign(selRadioLabel.style, { display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" });
        const selRadio = document.createElement("input");
        selRadio.type = "radio";
        selRadio.name = "annotation-anchor-type";
        selRadio.checked = this.anchorType === "selection";
        selRadio.addEventListener("change", () => {
            this.anchorType = "selection";
            this.scheduleRender();
        });
        selRadioLabel.appendChild(selRadio);
        selRadioLabel.appendChild(document.createTextNode("Selection"));
        anchorRow.appendChild(selRadioLabel);

        const coordsRadioLabel = document.createElement("label");
        Object.assign(coordsRadioLabel.style, { display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" });
        const coordsRadio = document.createElement("input");
        coordsRadio.type = "radio";
        coordsRadio.name = "annotation-anchor-type";
        coordsRadio.checked = this.anchorType === "coordinates";
        coordsRadio.addEventListener("change", () => {
            this.anchorType = "coordinates";
            this.scheduleRender();
        });
        coordsRadioLabel.appendChild(coordsRadio);
        coordsRadioLabel.appendChild(document.createTextNode("Coordinates"));
        anchorRow.appendChild(coordsRadioLabel);

        parent.appendChild(anchorRow);

        // 3. Selection / Coordinate Cards
        if (this.anchorType === "coordinates") {
            const coordsCard = document.createElement("div");
            coordsCard.setAttribute("data-molsysviewer-annotation-coords-card", "true");
            Object.assign(coordsCard.style, {
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                padding: "10px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.05)",
                marginBottom: "10px",
            });

            const cHeader = document.createElement("div");
            cHeader.textContent = "Coordinate anchor (nm)";
            Object.assign(cHeader.style, {
                fontSize: "12px",
                fontWeight: "700",
                color: "#fff",
            });
            coordsCard.appendChild(cHeader);

            const inputRow = document.createElement("div");
            Object.assign(inputRow.style, {
                display: "flex",
                gap: "8px",
            });

            ["X", "Y", "Z"].forEach((axis, index) => {
                const col = document.createElement("div");
                Object.assign(col.style, { display: "flex", flexDirection: "column", gap: "2px", flex: "1 1 0" });

                const label = document.createElement("span");
                label.textContent = axis;
                Object.assign(label.style, { fontSize: "10px", color: "rgba(244,244,245,0.5)" });
                col.appendChild(label);

                const numInput = document.createElement("input");
                numInput.type = "number";
                numInput.step = "0.1";
                numInput.value = String(this.customPosition[index]);
                Object.assign(numInput.style, INPUT_STYLE);
                numInput.addEventListener("input", () => {
                    this.customPosition[index] = Number(numInput.value) || 0.0;
                });
                col.appendChild(numInput);
                inputRow.appendChild(col);
            });
            coordsCard.appendChild(inputRow);
            parent.appendChild(coordsCard);
        } else {
            // Render selection cards:
            // 2. Active Selection Card
            const activeCard = document.createElement("div");
            activeCard.setAttribute("data-molsysviewer-annotation-active-selection-card", "true");
            Object.assign(activeCard.style, {
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                padding: "8px 10px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.035)",
                border: "1px solid rgba(255,255,255,0.08)",
                marginBottom: "10px",
            });

            const activeRow = document.createElement("div");
            Object.assign(activeRow.style, {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                width: "100%",
                gap: "6px 10px",
            });

            const leftWrap = document.createElement("div");
            Object.assign(leftWrap.style, {
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                fontWeight: "700",
                color: "#fff",
            });
            const dot = document.createElement("span");
            Object.assign(dot.style, {
                width: "5px",
                height: "5px",
                borderRadius: "999px",
                background: hasActive ? "#34d399" : "rgba(244,244,245,0.28)",
                boxShadow: hasActive ? "0 0 6px rgba(52,211,153,0.4)" : "none",
                flexShrink: "0",
            });
            leftWrap.appendChild(dot);
            leftWrap.appendChild(document.createTextNode("Active selection"));
            activeRow.appendChild(leftWrap);

            const countText = document.createElement("span");
            Object.assign(countText.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.6)",
                marginLeft: "auto",
                marginRight: "4px",
            });
            if (hasActive) {
                countText.textContent = `${activeCount} atom${activeCount === 1 ? "" : "s"}`;
            } else {
                countText.textContent = "No selection";
            }
            activeRow.appendChild(countText);

            // Right: Action Buttons (Anchor and Deactivate)
            const btnRow = document.createElement("div");
            Object.assign(btnRow.style, {
                display: "flex",
                gap: "4px",
                alignItems: "center",
                flexShrink: "0",
            });

            const anchorBtn = makeButton("Anchor", () => {
                this.stagedAnchor = [...this.selection.atom_indices];
                this.scheduleRender();
            });
            anchorBtn.disabled = !hasActive;
            anchorBtn.style.opacity = hasActive ? "1" : "0.42";
            anchorBtn.style.padding = "4px 8px";
            anchorBtn.style.fontSize = "11px";
            anchorBtn.style.whiteSpace = "nowrap";
            anchorBtn.setAttribute("data-molsysviewer-annotation-active-anchor", "true");
            btnRow.appendChild(anchorBtn);

            const deactivateBtn = makeButton("Deactivate", () => {
                this.ctx.onAction("set_active_selection_operation", { operation: "none" });
                this.stagedAnchor = null;
                this.scheduleRender();
            });
            deactivateBtn.disabled = !hasActive;
            deactivateBtn.style.opacity = hasActive ? "1" : "0.42";
            deactivateBtn.style.padding = "4px 8px";
            deactivateBtn.style.fontSize = "11px";
            deactivateBtn.style.whiteSpace = "nowrap";
            deactivateBtn.setAttribute("data-molsysviewer-annotation-active-deactivate", "true");
            btnRow.appendChild(deactivateBtn);
            activeRow.appendChild(btnRow);

            activeCard.appendChild(activeRow);
            parent.appendChild(activeCard);

            // 3. Select by Query Card
            const queryCard = document.createElement("div");
            queryCard.setAttribute("data-molsysviewer-annotation-query-card", "true");
            Object.assign(queryCard.style, {
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                padding: "10px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.05)",
                marginBottom: "10px",
            });

            const qHeader = document.createElement("div");
            qHeader.textContent = "Select by query";
            Object.assign(qHeader.style, {
                fontSize: "12px",
                fontWeight: "700",
                color: "#fff",
            });
            queryCard.appendChild(qHeader);

            const composer = this.getAnnotationsQueryComposer();
            queryCard.appendChild(composer.element());

            // Shortcuts Row
            const presetRow = document.createElement("div");
            presetRow.setAttribute("data-molsysviewer-annotation-query-presets", "true");
            Object.assign(presetRow.style, {
                display: "flex",
                flexWrap: "wrap",
                gap: "5px",
                alignItems: "center",
            });
            const presetLabel = document.createElement("span");
            Object.assign(presetLabel.style, {
                fontSize: "10px",
                color: "rgba(244,244,245,0.52)",
                marginRight: "2px",
            });
            presetLabel.textContent = "shortcuts";
            presetRow.appendChild(presetLabel);

            const presets = [
                { label: "protein", expression: 'molecule_type=="protein"' },
                { label: "water", expression: 'molecule_type=="water"' },
                { label: "backbone", expression: 'atom_name in ["N", "CA", "C", "O"]' },
                { label: "sidechain", expression: 'atom_name not in ["N", "CA", "C", "O"]' },
                { label: "ligand", expression: 'molecule_type=="small molecule"' },
            ] as const;
            for (const preset of presets) {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.textContent = preset.label;
                chip.setAttribute("data-molsysviewer-annotation-query-preset", preset.label);
                Object.assign(chip.style, {
                    background: "rgba(99, 102, 241, 0.16)",
                    border: "1px solid rgba(129, 140, 248, 0.34)",
                    borderRadius: "9999px",
                    padding: "2px 6px",
                    color: "#c7d2fe",
                    fontSize: "9px",
                    fontWeight: "500",
                    cursor: "pointer",
                });
                chip.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    composer.setExpression(preset.expression, "MolSysMT");
                });
                presetRow.appendChild(chip);
            }
            queryCard.appendChild(presetRow);

            // Query Cheat Sheet
            if (this.annotationsCheatSheetOpen) {
                const cheatSheet = document.createElement("div");
                cheatSheet.setAttribute("data-molsysviewer-annotation-cheatsheet", "true");
                Object.assign(cheatSheet.style, {
                    display: "grid",
                    gridTemplateColumns: "1fr",
                    gap: "4px",
                    padding: "8px",
                    borderRadius: "6px",
                    background: "rgba(0,0,0,0.18)",
                    border: "1px solid rgba(255,255,255,0.08)",
                });
                const examples = [
                    ["Atom name", 'atom_name=="CA"'],
                    ["Group index", "group_index in [10, 15]"],
                    ["Chain", 'chain_id=="A"'],
                    ["Protein", 'molecule_type=="protein"'],
                    ["Nearby", "all within 5 angstroms of atom_index in [0]"],
                    ["Bonded", "bonded to atom_index in [0]"],
                ] as const;
                for (const [label, expression] of examples) {
                    const row = document.createElement("button");
                    row.type = "button";
                    row.setAttribute("data-molsysviewer-annotation-cheatsheet-example", label);
                    Object.assign(row.style, {
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "8px",
                        width: "100%",
                        background: "transparent",
                        border: "0",
                        padding: "3px 2px",
                        color: "#e4e4e7",
                        fontSize: "10px",
                        textAlign: "left",
                        cursor: "pointer",
                    });
                    const name = document.createElement("span");
                    name.textContent = label;
                    name.style.color = "rgba(244,244,245,0.62)";
                    const code = document.createElement("code");
                    code.textContent = expression;
                    Object.assign(code.style, {
                        color: "#c7d2fe",
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    });
                    row.appendChild(name);
                    row.appendChild(code);
                    row.addEventListener("click", (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        composer.setExpression(expression, "MolSysMT");
                    });
                    cheatSheet.appendChild(row);
                }
                queryCard.appendChild(cheatSheet);
            }
            parent.appendChild(queryCard);

            // 4. Activate Saved Selection Card
            const savedCard = document.createElement("div");
            savedCard.setAttribute("data-molsysviewer-annotation-activate-saved-card", "true");
            Object.assign(savedCard.style, {
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                padding: "8px 10px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.035)",
                border: "1px solid rgba(255,255,255,0.08)",
                marginBottom: "10px",
            });

            const sHeader = document.createElement("div");
            sHeader.textContent = "Activate saved selection";
            Object.assign(sHeader.style, {
                fontSize: "12px",
                fontWeight: "700",
                color: "#fff",
            });
            savedCard.appendChild(sHeader);

            let activeSavedTag = "";
            for (const s of this.savedSelections) {
                if (this.isSavedSelectionActive(s)) {
                    activeSavedTag = s.tag;
                    break;
                }
            }

            const savedOptions = [
                { value: "", label: "Select saved selection..." },
                ...this.savedSelections.map(s => ({ value: s.tag, label: `${s.tag} (${s.atom_count} atoms)` })),
            ];
            const savedSelect = makeStyledSelect(
                savedOptions,
                activeSavedTag,
                (val) => {
                    if (val) {
                        this.ctx.onAction("activate_selection", { tag: val });
                    } else {
                        this.ctx.onAction("set_active_selection_operation", { operation: "none" });
                    }
                }
            );
            savedCard.appendChild(savedSelect);
            parent.appendChild(savedCard);
        }
    }

    private renderAnnotation(item: AnnotationSummary): HTMLDivElement {
        const row = card();
        row.setAttribute("data-molsysviewer-annotation-tag", item.tag);
        row.setAttribute("data-molsysviewer-annotation-broken", String(item.broken));
        row.style.opacity = item.hidden ? "0.42" : "1";
        if (item.brokenReason) row.title = item.brokenReason;

        const head = document.createElement("div");
        Object.assign(head.style, { display: "flex", alignItems: "center", gap: "6px" });
        if (this.editTextTag === item.tag) {
            head.appendChild(this.renderTextEditor(item));
        } else {
            const text = document.createElement("button");
            text.type = "button";
            text.textContent = item.broken ? `⚠ ${item.text}` : item.text;
            text.title = "Edit annotation text";
            text.setAttribute("data-molsysviewer-annotation-text", item.tag);
            Object.assign(text.style, {
                flex: "1 1 0", minWidth: "0", overflow: "hidden", textOverflow: "ellipsis",
                whiteSpace: "nowrap", textAlign: "left", background: "transparent", border: "0",
                padding: "0", color: item.broken ? "#fbbf24" : "#f4f4f5",
                fontSize: "12px", fontWeight: "650", cursor: "text",
            });
            text.addEventListener("click", event => {
                event.preventDefault();
                event.stopPropagation();
                this.selectedTag = item.tag;
                this.editTextTag = item.tag;
                this.scheduleRender();
            });
            head.appendChild(text);
        }
        row.appendChild(head);

        // Action Buttons Row (btnRow container)
        const btnRow = document.createElement("div");
        Object.assign(btnRow.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            marginTop: "4px",
        });

        const focus = makeButton("Focus", () => this.onFocus(item.atomIndices));
        focus.title = "Focus annotation anchor";
        focus.disabled = item.atomIndices.length === 0;
        focus.setAttribute("data-molsysviewer-annotation-focus", item.tag);

        const eye = makeButton(item.hidden ? "⦻" : "👁", () =>
            this.ctx.onAction("toggle_annotation_visibility", { tag: item.tag })
        );
        eye.title = item.hidden ? "Show annotation" : "Hide annotation";
        eye.setAttribute("data-molsysviewer-annotation-visibility", item.tag);

        const editBtn = makeButton("Edit", () => {
            this.selectedTag = item.tag;
            this.editDetailsTag = this.editDetailsTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        editBtn.title = "Rename, layer, or re-anchor";
        editBtn.setAttribute("data-molsysviewer-annotation-more", item.tag);

        const remove = makeButton("🗑", () => this.ctx.onAction("delete_annotation", { tag: item.tag }));
        remove.title = "Delete annotation";
        remove.setAttribute("data-molsysviewer-annotation-delete", item.tag);

        for (const button of [focus, eye, editBtn, remove]) {
            button.style.flex = "0 1 auto";
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            btnRow.appendChild(button);
        }
        row.appendChild(btnRow);

        const identity = document.createElement("div");
        identity.textContent = item.broken
            ? `${item.tag} · anchor broken${item.owner ? ` · from ${item.owner}` : ""}`
            : `${item.tag} · ${item.nAtoms} atom${item.nAtoms === 1 ? "" : "s"}${item.layerTag && item.layerTag !== item.tag ? ` · layer: ${item.layerTag}` : ""}${item.owner ? ` · from ${item.owner}` : ""}`;
        identity.setAttribute("data-molsysviewer-annotation-identity", item.tag);
        Object.assign(identity.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)", marginTop: "4px" });
        row.appendChild(identity);

        if (this.editDetailsTag === item.tag) {
            row.appendChild(this.renderDetails(item));
        }
        return row;
    }

    private renderTextEditor(item: AnnotationSummary): HTMLInputElement {
        const input = document.createElement("input");
        input.value = item.text;
        input.setAttribute("data-molsysviewer-annotation-text-input", item.tag);
        input.addEventListener("focus", () => this.beginCoalescing());
        input.addEventListener("input", () => {
            const text = input.value.trim();
            if (text) this.ctx.onAction("set_annotation_text", { tag: item.tag, text });
        });
        input.addEventListener("keydown", event => {
            if (event.key === "Enter") this.finishTextEdit();
            if (event.key === "Escape") {
                if (input.value.trim() !== item.text) {
                    this.ctx.onAction("set_annotation_text", { tag: item.tag, text: item.text });
                }
                this.finishTextEdit();
            }
        });
        input.addEventListener("blur", () => this.finishTextEdit());
        setTimeout(() => {
            if (typeof input.focus === "function") input.focus();
        }, 0);
        return input;
    }

    private finishTextEdit(): void {
        if (this.editTextTag === null) return;
        this.editTextTag = null;
        this.endCoalescing();
        this.scheduleRender();
    }

    private renderDetails(item: AnnotationSummary): HTMLDivElement {
        const editor = document.createElement("div");
        Object.assign(editor.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginTop: "6px",
            padding: "8px",
            background: "rgba(0,0,0,0.12)",
            borderRadius: "6px",
        });

        // Rename Row
        const renameRow = document.createElement("div");
        Object.assign(renameRow.style, { display: "flex", gap: "6px" });
        const rename = document.createElement("input");
        rename.type = "text";
        rename.value = item.tag;
        Object.assign(rename.style, { flex: "1 1 auto", ...INPUT_STYLE });
        rename.setAttribute("data-molsysviewer-annotation-rename-input", item.tag);
        const renameButton = makeButton("Rename", () =>
            this.ctx.onAction("rename_annotation", { tag: item.tag, new_tag: rename.value.trim() })
        );
        renameButton.style.padding = "4px 8px";
        renameButton.style.fontSize = "11px";
        renameButton.style.flex = "0 0 auto";
        renameButton.setAttribute("data-molsysviewer-annotation-rename", item.tag);
        rename.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                renameButton.click();
            }
        });
        renameRow.appendChild(rename);
        renameRow.appendChild(renameButton);
        editor.appendChild(renameRow);

        // Layer Row
        const layerRow = document.createElement("div");
        Object.assign(layerRow.style, { display: "flex", gap: "6px" });
        const layer = document.createElement("input");
        layer.type = "text";
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "No user layer";
        Object.assign(layer.style, { flex: "1 1 auto", ...INPUT_STYLE });
        layer.setAttribute("data-molsysviewer-annotation-layer-input", item.tag);
        const layerButton = makeButton("Set layer", () =>
            this.ctx.onAction("set_annotation_layer", { tag: item.tag, layer: layer.value.trim() || null })
        );
        layerButton.style.padding = "4px 8px";
        layerButton.style.fontSize = "11px";
        layerButton.style.flex = "0 0 auto";
        layerButton.setAttribute("data-molsysviewer-annotation-layer", item.tag);
        layer.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                layerButton.click();
            }
        });
        layerRow.appendChild(layer);
        layerRow.appendChild(layerButton);
        editor.appendChild(layerRow);

        // Reanchor Button
        const reanchor = makeButton("Use active selection", () =>
            this.ctx.onAction("reanchor_annotation", { tag: item.tag })
        );
        reanchor.disabled = this.selectionCount() === 0;
        reanchor.style.opacity = reanchor.disabled ? "0.42" : "1";
        reanchor.style.padding = "4px 8px";
        reanchor.style.fontSize = "11px";
        reanchor.style.width = "100%";
        reanchor.setAttribute("data-molsysviewer-annotation-reanchor", item.tag);
        editor.appendChild(reanchor);

        // Style Header
        const sHeader = document.createElement("div");
        sHeader.textContent = "Style";
        Object.assign(sHeader.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(255,255,255,0.8)",
            marginTop: "4px",
            paddingTop: "4px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
        });
        editor.appendChild(sHeader);

        const style = resolvedStyle(item.style);

        // Color Row
        const color = document.createElement("input");
        color.type = "color";
        color.value = style.color;
        color.setAttribute("data-molsysviewer-annotation-style-color", item.tag);
        const bindContinuous = (inp: HTMLInputElement, readStyle: () => Required<AnnotationLabelStyle>) => {
            inp.addEventListener("focus", () => this.beginCoalescing());
            inp.addEventListener("pointerdown", () => this.beginCoalescing());
            inp.addEventListener("input", () => {
                this.ctx.onAction("set_annotation_style", { tag: item.tag, style: readStyle() });
            });
            inp.addEventListener("change", () => this.endCoalescing());
            inp.addEventListener("blur", () => this.endCoalescing());
        };
        bindContinuous(color, () => ({ ...style, color: color.value }));
        editor.appendChild(this.styleRow("Colour", color));

        // Size Row
        const size = document.createElement("input");
        size.type = "range";
        size.min = "0.5";
        size.max = "4";
        size.step = "0.1";
        size.value = String(style.size_em);
        size.setAttribute("data-molsysviewer-annotation-style-size", item.tag);
        bindContinuous(size, () => ({ ...style, size_em: Number(size.value) }));
        editor.appendChild(this.styleRow("Size", size));

        // Background Checkbox Row
        const background = document.createElement("input");
        background.type = "checkbox";
        background.checked = style.background;
        background.setAttribute("data-molsysviewer-annotation-style-background", item.tag);

        // Background Opacity Slider Row
        const opacity = document.createElement("input");
        opacity.type = "range";
        opacity.min = "0";
        opacity.max = "1";
        opacity.step = "0.05";
        opacity.value = String(style.background_opacity);
        opacity.disabled = !style.background;
        opacity.setAttribute("data-molsysviewer-annotation-style-background-opacity", item.tag);

        const updateOpacityEnabled = () => {
            opacity.disabled = !background.checked;
        };

        background.addEventListener("change", () => {
            updateOpacityEnabled();
            this.ctx.onAction("set_annotation_style", {
                tag: item.tag,
                style: { ...style, background: background.checked, background_opacity: Number(opacity.value) }
            });
        });
        bindContinuous(opacity, () => ({ ...style, background: background.checked, background_opacity: Number(opacity.value) }));

        editor.appendChild(this.styleRow("Background", background));
        editor.appendChild(this.styleRow("Background opacity", opacity));

        return editor;
    }

    private renderGlobalActions(): HTMLDivElement {
        const card = document.createElement("div");
        Object.assign(card.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "8px 10px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.035)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "10px",
        });

        const totalCount = this.annotations.length;
        const visibleCount = this.annotations.filter(m => !m.hidden).length;

        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            gap: "10px",
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
        const anyVisible = totalCount > 0 && visibleCount > 0;
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: anyVisible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: anyVisible ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        info.appendChild(dot);
        info.appendChild(document.createTextNode(`${visibleCount} of ${totalCount} annotation${totalCount === 1 ? "" : "s"} visible`));
        row.appendChild(info);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        for (const [label, action] of [
            ["Show all", "show_all_annotations"],
            ["Hide all", "hide_all_annotations"],
        ] as const) {
            const button = makeButton(label, () => {
                this.ctx.onAction(action);
            });
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            button.style.whiteSpace = "nowrap";
            button.setAttribute("data-molsysviewer-annotation-global", action);
            actions.appendChild(button);
        }
        row.appendChild(actions);
        card.appendChild(row);

        return card;
    }

    private renderStyle(): HTMLDivElement {
        const section = card();
        section.setAttribute("data-molsysviewer-annotation-style", this.selectedTag ?? "default");
        section.appendChild(makeSectionHeader("Label style"));
        const selected = this.annotations.find(item => item.tag === this.selectedTag);
        const style = selected ? resolvedStyle(selected.style) : this.nextStyle;
        const context = document.createElement("div");
        context.textContent = selected ? selected.text : "Next annotation";
        Object.assign(context.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        section.appendChild(context);

        const color = document.createElement("input");
        color.type = "color";
        color.value = style.color;
        color.setAttribute("data-molsysviewer-annotation-style-color", this.selectedTag ?? "default");
        this.bindContinuousStyle(color, () => ({ ...style, color: color.value }));
        section.appendChild(this.styleRow("Colour", color));

        const size = document.createElement("input");
        size.type = "range";
        size.min = "0.5";
        size.max = "4";
        size.step = "0.1";
        size.value = String(style.size_em);
        size.setAttribute("data-molsysviewer-annotation-style-size", this.selectedTag ?? "default");
        this.bindContinuousStyle(size, () => ({ ...style, size_em: Number(size.value) }));
        section.appendChild(this.styleRow("Size", size));

        const background = document.createElement("input");
        background.type = "checkbox";
        background.checked = style.background;
        background.setAttribute("data-molsysviewer-annotation-style-background", this.selectedTag ?? "default");
        background.addEventListener("change", () => this.applyStyle({ ...style, background: background.checked }));
        section.appendChild(this.styleRow("Background", background));

        const opacity = document.createElement("input");
        opacity.type = "range";
        opacity.min = "0";
        opacity.max = "1";
        opacity.step = "0.05";
        opacity.value = String(style.background_opacity);
        opacity.disabled = !style.background;
        opacity.setAttribute("data-molsysviewer-annotation-style-background-opacity", this.selectedTag ?? "default");
        this.bindContinuousStyle(opacity, () => ({ ...style, background_opacity: Number(opacity.value) }));
        section.appendChild(this.styleRow("Background opacity", opacity));
        return section;
    }

    private styleRow(labelText: string, input: HTMLInputElement): HTMLLabelElement {
        const label = document.createElement("label");
        label.textContent = labelText;
        Object.assign(label.style, {
            display: "grid", gridTemplateColumns: "110px 1fr", alignItems: "center",
            gap: "8px", fontSize: "10px", color: "rgba(244,244,245,0.7)",
        });
        label.appendChild(input);
        return label;
    }

    private bindContinuousStyle(
        input: HTMLInputElement,
        read: () => Required<AnnotationLabelStyle>,
    ): void {
        input.addEventListener("focus", () => this.beginCoalescing());
        input.addEventListener("pointerdown", () => this.beginCoalescing());
        input.addEventListener("input", () => this.applyStyle(read()));
        input.addEventListener("change", () => this.endCoalescing());
        input.addEventListener("blur", () => this.endCoalescing());
    }

    private applyStyle(style: Required<AnnotationLabelStyle>): void {
        if (this.selectedTag) {
            this.ctx.onAction("set_annotation_style", { tag: this.selectedTag, style });
        } else {
            this.nextStyle = style;
        }
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
