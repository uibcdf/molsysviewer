import type { ActiveSelectionPayload } from "../../managers/active-selection";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";

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
    private newText = "";
    private nextStyle = defaultStyle();
    private editTextTag: string | null = null;
    private editDetailsTag: string | null = null;
    private selectedTag: string | null = null;
    private coalescing = false;

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

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.selection = selection;
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Annotations"));
        this.host.appendChild(this.renderCreate());
        this.host.appendChild(makeSectionHeader("Labels"));

        const list = document.createElement("div");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "7px" });
        if (this.annotations.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No annotations yet.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "11px" });
            list.appendChild(empty);
        } else {
            for (const item of this.annotations) list.appendChild(this.renderAnnotation(item));
        }
        this.host.appendChild(list);
        this.host.appendChild(this.renderGlobalActions());
        this.host.appendChild(this.renderStyle());
    }

    private selectionCount(): number {
        return this.selection.count_atoms || this.selection.atom_indices.length || this.settings.activeSelectionCount;
    }

    private renderCreate(): HTMLDivElement {
        const section = card();
        section.setAttribute("data-molsysviewer-annotation-create", "true");
        const input = document.createElement("input");
        input.value = this.newText;
        input.placeholder = "Annotation text";
        input.setAttribute("data-molsysviewer-annotation-create-text", "true");
        const add = makeButton("Add", () => {
            const text = input.value.trim();
            if (!text) return;
            this.newText = "";
            this.ctx.onAction("create_annotation", { text, label_style: { ...this.nextStyle } });
        });
        add.setAttribute("data-molsysviewer-annotation-create-confirm", "true");
        const updateDisabled = () => {
            add.disabled = !this.settings.systemLoaded || this.selectionCount() === 0 || !input.value.trim();
            add.style.opacity = add.disabled ? "0.42" : "1";
        };
        input.addEventListener("input", () => { this.newText = input.value; updateDisabled(); });
        input.addEventListener("keydown", event => {
            if (event.key === "Enter" && !add.disabled) add.click();
        });
        section.appendChild(input);
        section.appendChild(add);
        const hint = document.createElement("div");
        const count = this.selectionCount();
        hint.textContent = !this.settings.systemLoaded
            ? "Load a structure first."
            : count === 0
                ? "Select atoms to anchor the annotation."
                : `Anchored to the active selection (${count} atom${count === 1 ? "" : "s"}).`;
        Object.assign(hint.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        section.appendChild(hint);
        updateDisabled();
        return section;
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

        const focus = makeButton("⌖", () => this.onFocus(item.atomIndices));
        focus.title = "Focus annotation anchor";
        focus.disabled = item.atomIndices.length === 0;
        focus.setAttribute("data-molsysviewer-annotation-focus", item.tag);
        const eye = makeButton(item.hidden ? "⦻" : "👁", () =>
            this.ctx.onAction("toggle_annotation_visibility", { tag: item.tag })
        );
        eye.title = item.hidden ? "Show annotation" : "Hide annotation";
        eye.setAttribute("data-molsysviewer-annotation-visibility", item.tag);
        const more = makeButton("⋯", () => {
            this.selectedTag = item.tag;
            this.editDetailsTag = this.editDetailsTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        more.title = "Rename, layer, or re-anchor";
        more.setAttribute("data-molsysviewer-annotation-more", item.tag);
        const remove = makeButton("×", () => this.ctx.onAction("delete_annotation", { tag: item.tag }));
        remove.title = "Delete annotation";
        remove.setAttribute("data-molsysviewer-annotation-delete", item.tag);
        for (const button of [focus, eye, more, remove]) {
            button.style.flex = "0 0 auto";
            head.appendChild(button);
        }
        row.appendChild(head);

        const identity = document.createElement("div");
        identity.textContent = item.broken
            ? `${item.tag} · anchor broken${item.owner ? ` · from ${item.owner}` : ""}`
            : `${item.tag} · ${item.nAtoms} atom${item.nAtoms === 1 ? "" : "s"}${item.layerTag && item.layerTag !== item.tag ? ` · layer: ${item.layerTag}` : ""}${item.owner ? ` · from ${item.owner}` : ""}`;
        identity.setAttribute("data-molsysviewer-annotation-identity", item.tag);
        Object.assign(identity.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        row.appendChild(identity);
        if (this.editDetailsTag === item.tag) row.appendChild(this.renderDetails(item));
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
        Object.assign(editor.style, { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px" });
        const rename = document.createElement("input");
        rename.value = item.tag;
        rename.setAttribute("data-molsysviewer-annotation-rename-input", item.tag);
        const renameButton = makeButton("Rename", () =>
            this.ctx.onAction("rename_annotation", { tag: item.tag, new_tag: rename.value.trim() })
        );
        renameButton.setAttribute("data-molsysviewer-annotation-rename", item.tag);
        rename.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                renameButton.click();
            }
        });
        const layer = document.createElement("input");
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "No user layer";
        layer.setAttribute("data-molsysviewer-annotation-layer-input", item.tag);
        const layerButton = makeButton("Set layer", () =>
            this.ctx.onAction("set_annotation_layer", { tag: item.tag, layer: layer.value.trim() || null })
        );
        layerButton.setAttribute("data-molsysviewer-annotation-layer", item.tag);
        layer.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                layerButton.click();
            }
        });
        const reanchor = makeButton("Use active selection", () =>
            this.ctx.onAction("reanchor_annotation", { tag: item.tag })
        );
        reanchor.disabled = this.selectionCount() === 0;
        reanchor.style.opacity = reanchor.disabled ? "0.42" : "1";
        reanchor.setAttribute("data-molsysviewer-annotation-reanchor", item.tag);
        editor.appendChild(rename);
        editor.appendChild(renameButton);
        editor.appendChild(layer);
        editor.appendChild(layerButton);
        editor.appendChild(reanchor);
        return editor;
    }

    private renderGlobalActions(): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "flex", gap: "6px", marginTop: "8px" });
        for (const [label, action] of [
            ["Show all", "show_all_annotations"],
            ["Hide all", "hide_all_annotations"],
            ["Clear all", "clear_annotations"],
        ] as const) {
            const button = makeButton(label, () => {
                if (action === "clear_annotations" && !window.confirm("Delete all annotations?")) return;
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
