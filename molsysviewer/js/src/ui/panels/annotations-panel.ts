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

        // 4. Label Style Card
        this.host.appendChild(this.renderStyle());
    }

    private selectionCount(): number {
        return this.selection.count_atoms || this.selection.atom_indices.length || this.settings.activeSelectionCount;
    }

    private renderNewAnnotationElements(parent: HTMLElement): void {
        const activeCount = this.selection.atom_indices.length;
        const hasActive = activeCount > 0;

        // 1. Active Selection Card
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

        // Right: Action Buttons (Deactivate wrapper)
        const btnRow = document.createElement("div");
        Object.assign(btnRow.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        const deactivateBtn = makeButton("Deactivate", () => {
            this.ctx.onAction("set_active_selection_operation", { operation: "none" });
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

        // 2. Select by Query Card
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

        // 3. Activate Saved Selection Card
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

        // 4. Creation Input Form
        const createCard = card();
        createCard.setAttribute("data-molsysviewer-annotation-create-card", "true");
        Object.assign(createCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
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
            this.ctx.onAction("create_annotation", { text, label_style: { ...this.nextStyle } });
        });
        addBtn.setAttribute("data-molsysviewer-annotation-create-confirm", "true");
        addBtn.disabled = !this.settings.systemLoaded || !hasActive || !this.newText.trim();
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
            addBtn.disabled = !this.settings.systemLoaded || !hasActive || !this.newText.trim();
            addBtn.style.opacity = addBtn.disabled ? "0.42" : "1";
        });
        textInput.addEventListener("keydown", event => {
            if (event.key === "Enter" && !addBtn.disabled) addBtn.click();
        });

        const hint = document.createElement("div");
        hint.textContent = !this.settings.systemLoaded
            ? "Load a structure first."
            : !hasActive
                ? "Select atoms to anchor the annotation."
                : `Anchored to the active selection (${activeCount} atom${activeCount === 1 ? "" : "s"}).`;
        Object.assign(hint.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        createCard.appendChild(hint);

        parent.appendChild(createCard);
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

        const styleBtn = makeButton("Style", () => {
            this.selectedTag = item.tag;
            this.scheduleRender();
        });
        styleBtn.title = "Select style";
        styleBtn.setAttribute("data-molsysviewer-annotation-style-select", item.tag);

        const remove = makeButton("🗑", () => this.ctx.onAction("delete_annotation", { tag: item.tag }));
        remove.title = "Delete annotation";
        remove.setAttribute("data-molsysviewer-annotation-delete", item.tag);

        for (const button of [focus, eye, editBtn, styleBtn, remove]) {
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

        return editor;
    }

    private renderGlobalActions(): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "flex", gap: "6px", marginBottom: "8px" });
        for (const [label, action] of [
            ["Show all", "show_all_annotations"],
            ["Hide all", "hide_all_annotations"],
        ] as const) {
            const button = makeButton(label, () => {
                this.ctx.onAction(action);
            });
            button.setAttribute("data-molsysviewer-annotation-global", action);
            row.appendChild(button);
        }
        return row;
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
