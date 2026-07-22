import { ActiveSelectionItem, ActiveSelectionPayload, ActiveSelectionSetOperation } from "../../managers/active-selection";
import { ManualQueryComposer } from "../query-composer";
import type { SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";

/**
 * Studio -> Selection subpanel.
 *
 * Self-contained module: owns the manual query composer, guided chips (shortcuts),
 * cheat-sheet, and the saved-selections manager. Receives domain state via
 * updateSelection / updateHistory / setSavedSelections / updatePreview and talks
 * to the host through the injected PanelContext plus onSelect, onActivateSavedSelection
 * and a regionExists bridge callback.
 */
export class SelectionPanel extends BasePanel {
    readonly key = "selection";
    private static readonly SELECTION_STYLE_ID = "molsysviewer-selection-panel-design-system";

    // Domain state
    private currentSelection: ActiveSelectionPayload = { count_atoms: 0 } as ActiveSelectionPayload;
    private savedSelections: SavedSelectionSummary[] = [];

    // View state
    private selectionQueryComposer: ManualQueryComposer | null = null;
    private helpBtn: HTMLButtonElement | null = null;
    private selectionCheatSheetOpen = false;
    private selectionCanUndo = false;
    private selectionCanRedo = false;

    private showActiveSelectionSaveForm = false;
    private activeSelectionSaveInput: HTMLInputElement | null = null;

    constructor(
        private readonly ctx: PanelContext,
        private readonly onSelect: (items: ActiveSelectionItem[], op: ActiveSelectionSetOperation) => void,
        private readonly onActivateSavedSelection: (tag: string) => void,
        private readonly regionExists: (tag: string) => boolean,
    ) {
        super();
    }

    protected onMount(): void {
        const host = this.host!;
        host.tabIndex = 0;
        host.setAttribute("data-molsysviewer-selection-panel", "true");
        host.addEventListener("keydown", (event) => this.handleSelectionPanelKeydown(event));
        SelectionPanel.ensureDesignSystemStyles();
    }

    private updateBadge(): void {
        const activeCount = this.currentSelection?.count_atoms ?? 0;
        const savedCount = this.savedSelections.length;
        this.ctx.setBadge(`${activeCount} atom${activeCount === 1 ? "" : "s"} active · ${savedCount} saved`);
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        if (selection.count_atoms === 0) {
            this.showActiveSelectionSaveForm = false;
        }
        this.updateBadge();
        this.scheduleRender();
    }

    updateHistory(state: { canUndo: boolean; canRedo: boolean }): void {
        this.selectionCanUndo = state.canUndo;
        this.selectionCanRedo = state.canRedo;
        this.scheduleRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.updateBadge();
        this.scheduleRender();
    }

    /** Route a query preview belonging to this panel's manual composer. */
    updatePreview(preview: SelectionQueryPreview): void {
        const composer = this.getSelectionQueryComposer();
        const updated = composer.updatePreview(preview);
        if (updated && preview.ok === true) {
            const { expression, syntax } = composer.value();
            if (expression) {
                // Select the atoms immediately in the viewer
                this.ctx.onAction("apply_selection_query", {
                    expression,
                    syntax,
                    op: "replace",
                });
            }
        }
    }

    static ensureDesignSystemStyles(): void {
        if (typeof document === "undefined") return;
        if (document.getElementById?.(SelectionPanel.SELECTION_STYLE_ID)) return;
        if (!document.head) return;

        const style = document.createElement("style");
        style.id = SelectionPanel.SELECTION_STYLE_ID;
        style.textContent = `
[data-molsysviewer-group-panel] {
    --bg-sidebar: #12131a;
    --bg-card: rgba(255, 255, 255, 0.03);
    --bg-card-hover: rgba(255, 255, 255, 0.06);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --accent-indigo: #6366f1;
    --accent-indigo-soft: rgba(99, 102, 241, 0.16);
    --accent-indigo-border: rgba(129, 140, 248, 0.34);
    --accent-indigo-glow: 0 0 12px rgba(99, 102, 241, 0.25);
    --text-primary: #f4f4f5;
    --text-secondary: rgba(244, 244, 245, 0.68);
    --text-muted: rgba(244, 244, 245, 0.48);
}



[data-molsysviewer-selection-active-card],
[data-molsysviewer-selection-query-composer="true"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.055), rgba(255,255,255,0.012)) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.055);
    backdrop-filter: blur(12px);
}

[data-molsysviewer-selection-query-composer="true"]:focus-within {
    border-color: rgba(99, 102, 241, 0.36) !important;
    box-shadow: var(--accent-indigo-glow), inset 0 1px 0 rgba(255,255,255,0.06);
}

[data-molsysviewer-query-input="selection"]:focus,
[data-molsysviewer-query-syntax="selection"]:focus {
    border-color: rgba(99, 102, 241, 0.46) !important;
    box-shadow: var(--accent-indigo-glow);
    outline: none;
}

[data-molsysviewer-selection-query-preset] {
    background: var(--accent-indigo-soft) !important;
    border-color: var(--accent-indigo-border) !important;
    transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}

[data-molsysviewer-selection-query-preset]:hover {
    background: rgba(99, 102, 241, 0.24) !important;
    border-color: rgba(165, 180, 252, 0.48) !important;
    transform: translateY(-1px);
}

[data-molsysviewer-saved-selection-list] {
    background: transparent;
}

[data-molsysviewer-saved-selection-card] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1),
        transform 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[data-molsysviewer-saved-selection-card]:hover,
[data-molsysviewer-saved-selection-card][data-molsysviewer-selection-row-hover="true"] {
    background: var(--bg-card-hover) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
    transform: translateY(-1px);
}

[data-molsysviewer-saved-selection-card][data-molsysviewer-selection-row-active="true"] {
    border-left: 3px solid var(--accent-indigo) !important;
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, rgba(255,255,255,0.03) 100%) !important;
}

[data-molsysviewer-query-status="selection"][data-molsysviewer-query-status-value="ok"] {
    text-shadow: 0 0 10px rgba(134, 239, 172, 0.18);
}

[data-molsysviewer-query-status="selection"][data-molsysviewer-query-status-value="error"] {
    text-shadow: 0 0 10px rgba(252, 165, 165, 0.16);
}



[data-molsysviewer-region-create],
[data-molsysviewer-region-boolean-composer],
[data-molsysviewer-region-card] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
}

[data-molsysviewer-region-card] {
    transition: background 0.16s ease, border-color 0.16s ease, opacity 0.16s ease,
        transform 0.16s ease;
}

[data-molsysviewer-region-card]:hover {
    background: var(--bg-card-hover) !important;
    border-color: rgba(255, 255, 255, 0.14) !important;
    transform: translateY(-1px);
}

[data-molsysviewer-region-overlap] {
    color: #facc15 !important;
    border-color: rgba(250, 204, 21, 0.34) !important;
    background: rgba(250, 204, 21, 0.08) !important;
}

[data-molsysviewer-region-boolean-composer][data-molsysviewer-region-boolean-attention="true"] {
    border-color: var(--accent-indigo) !important;
    box-shadow: var(--accent-indigo-glow);
    animation: molsysviewer-region-attention 0.9s ease;
}

@keyframes molsysviewer-region-attention {
    0%, 100% { box-shadow: none; }
    45% { box-shadow: var(--accent-indigo-glow); }
}

[data-molsysviewer-region-style-composer] {
    border-color: var(--accent-indigo-border) !important;
    background: rgba(99, 102, 241, 0.055) !important;
}

[data-molsysviewer-region-style-opacity] {
    accent-color: var(--accent-indigo);
}

[data-molsysviewer-region-inspect-panel] {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 5px 10px;
    padding: 8px;
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.14);
    color: var(--text-secondary);
    font-size: 10px;
}

[data-molsysviewer-region-inspect-center] {
    grid-column: 1 / -1;
    font-variant-numeric: tabular-nums;
}
`;
        document.head.appendChild(style);
    }

    private handleSelectionPanelKeydown(event: KeyboardEvent): void {
        if (!(event.ctrlKey || event.metaKey)) return;
        if (this.isEditableTarget(event.target)) return;
        const key = event.key.toLowerCase();
        if (key === "z" && !event.shiftKey) {
            if (!this.selectionCanUndo) return;
            event.preventDefault();
            event.stopPropagation();
            this.ctx.onAction("undo_active_selection");
        } else if (key === "y" || (key === "z" && event.shiftKey)) {
            if (!this.selectionCanRedo) return;
            event.preventDefault();
            event.stopPropagation();
            this.ctx.onAction("redo_active_selection");
        }
    }

    private isEditableTarget(target: EventTarget | null): boolean {
        const node = target as HTMLElement | null;
        if (!node) return false;
        const tagName = node.tagName?.toLowerCase();
        return tagName === "input" || tagName === "textarea" || tagName === "select" || node.isContentEditable === true;
    }

    private isSavedSelectionActive(item: SavedSelectionSummary): boolean {
        const activeIndices = this.currentSelection?.atom_indices;
        if (!activeIndices || !item.atom_indices) return false;
        if (activeIndices.length === 0 || item.atom_indices.length === 0) return false;
        if (activeIndices.length !== item.atom_indices.length) return false;
        for (let i = 0; i < activeIndices.length; i++) {
            if (activeIndices[i] !== item.atom_indices[i]) return false;
        }
        return true;
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // Title and line separator
        this.host.appendChild(makeSectionHeader("Selections"));

        // A. Active Selection Card
        this.host.appendChild(this.renderActiveSelectionCard());

        // B. Query Composer
        this.host.appendChild(this.renderSelectionQueryComposer());

        // C. Saved Selections Area
        this.host.appendChild(makeSectionHeader("Saved Selections"));
        const savedList = document.createElement("div");
        savedList.setAttribute("data-molsysviewer-saved-selection-list", "true");
        Object.assign(savedList.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.host.appendChild(savedList);

        if (this.savedSelections.length > 0) {
            const sorted = [...this.savedSelections].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                const card = document.createElement("div");
                card.setAttribute("data-molsysviewer-group-panel-row", "true");
                card.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
                card.setAttribute("data-molsysviewer-saved-selection-card", item.tag);
                Object.assign(card.style, {
                    display: "flex",
                    flexDirection: "column",
                    padding: "8px 10px",
                    borderRadius: "8px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.06)",
                    gap: "6px",
                    transition: "background 0.1s ease",
                    cursor: "pointer",
                });
                card.addEventListener("mouseenter", () => {
                    card.setAttribute("data-molsysviewer-selection-row-hover", "true");
                    card.style.background = "rgba(255,255,255,0.09)";
                });
                card.addEventListener("mouseleave", () => {
                    card.setAttribute("data-molsysviewer-selection-row-hover", "false");
                    card.style.background = "rgba(255,255,255,0.05)";
                });
                const isActive = this.isSavedSelectionActive(item);

                card.addEventListener("click", (e) => {
                    if (e && e.target && e.target !== card) {
                        return;
                    }
                    e?.preventDefault();
                    e?.stopPropagation();
                    if (isActive) {
                        this.ctx.onAction("set_active_selection_operation", { operation: "none" });
                    } else {
                        this.onActivateSavedSelection(item.tag);
                    }
                });

                // Top row (Title & Meta)
                const topRow = document.createElement("div");
                Object.assign(topRow.style, {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                });
                const title = document.createElement("div");
                Object.assign(title.style, {
                    fontSize: "12px",
                    fontWeight: "600",
                    color: "#f4f4f5",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    display: "flex",
                    alignItems: "center",
                });

                const dot = document.createElement("span");
                dot.setAttribute("data-molsysviewer-saved-selection-active-dot", String(isActive));
                Object.assign(dot.style, {
                    width: "7px",
                    height: "7px",
                    borderRadius: "999px",
                    background: isActive ? "#34d399" : "rgba(244,244,245,0.28)",
                    boxShadow: isActive ? "0 0 8px rgba(52,211,153,0.5)" : "none",
                    flexShrink: "0",
                    marginRight: "6px",
                });
                title.appendChild(dot);
                title.appendChild(document.createTextNode(item.tag));

                const subtitle = document.createElement("span");
                Object.assign(subtitle.style, {
                    fontSize: "10px",
                    color: "rgba(244,244,245,0.56)",
                    marginLeft: "6px",
                    fontWeight: "normal",
                });
                const levelText = item.element_level ? ` · ${item.element_level} level` : " · group level";
                subtitle.textContent = `(${item.atom_count} atoms${levelText})`;
                title.appendChild(subtitle);
                topRow.appendChild(title);
                card.appendChild(topRow);

                // Buttons container row
                const btnRow = document.createElement("div");
                btnRow.setAttribute("data-molsysviewer-saved-selection-buttons-row", item.tag);
                Object.assign(btnRow.style, {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px",
                });

                // Inline form container (Rename / Region / Label)
                const inlineForm = document.createElement("div");
                Object.assign(inlineForm.style, {
                    display: "none",
                    flexDirection: "row",
                    gap: "6px",
                    marginTop: "2px",
                });
                const inlineInput = document.createElement("input");
                inlineInput.type = "text";
                Object.assign(inlineInput.style, {
                    flex: "1 1 0",
                    background: "rgba(0,0,0,0.2)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "6px",
                    padding: "4px 6px",
                    color: "#fff",
                    fontSize: "11px",
                    outline: "none",
                });
                card.appendChild(inlineForm);

                const showForm = (mode: "rename" | "region" | "label") => {
                    btnRow.style.display = "none";
                    inlineForm.replaceChildren();
                    inlineInput.value = "";
                    inlineInput.placeholder = mode === "rename" ? "New name..." : mode === "region" ? "Region name..." : "Label text...";

                    const inlineConfirm = document.createElement("button");
                    inlineConfirm.type = "button";
                    inlineConfirm.textContent = mode === "rename" ? "Rename" : mode === "region" ? "Create" : "Add Label";
                    inlineConfirm.setAttribute("data-molsysviewer-saved-selection-confirm", item.tag);
                    inlineConfirm.setAttribute("data-molsysviewer-saved-selection-confirm-mode", mode);
                    Object.assign(inlineConfirm.style, {
                        background: "#6366f1",
                        border: "0",
                        borderRadius: "6px",
                        padding: "4px 8px",
                        color: "#fff",
                        fontSize: "11px",
                        fontWeight: "600",
                        cursor: "pointer",
                    });

                    const inlineCancel = document.createElement("button");
                    inlineCancel.type = "button";
                    inlineCancel.textContent = "Cancel";
                    Object.assign(inlineCancel.style, {
                        background: "rgba(255,255,255,0.08)",
                        border: "0",
                        borderRadius: "6px",
                        padding: "4px 8px",
                        color: "#e4e4e7",
                        fontSize: "11px",
                        cursor: "pointer",
                    });

                    inlineConfirm.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const val = inlineInput.value.trim();
                        if (!val) return;
                        if (mode === "rename") {
                            const exists = this.savedSelections.some(s => s.tag === val);
                            if (exists) {
                                if (val === item.tag) {
                                    inlineForm.style.display = "none";
                                    btnRow.style.display = "flex";
                                    return;
                                }
                                const doOverwrite = typeof confirm === "function" ? confirm(`A saved selection named "${val}" already exists. Overwrite?`) : true;
                                if (doOverwrite) {
                                    this.ctx.onAction("delete_selection", { tag: val });
                                    this.ctx.onAction("rename_selection", { tag: item.tag, new_tag: val });
                                } else {
                                    return;
                                }
                            } else {
                                this.ctx.onAction("rename_selection", { tag: item.tag, new_tag: val });
                            }
                        } else if (mode === "region") {
                            const exists = this.regionExists(val);
                            if (exists) {
                                const doOverwrite = typeof confirm === "function" ? confirm(`A region named "${val}" already exists. Overwrite?`) : true;
                                if (doOverwrite) {
                                    this.ctx.onAction("delete_region", { tag: val });
                                    this.ctx.onAction("create_region_from_saved_selection", { selection_tag: item.tag, tag: val });
                                } else {
                                    return;
                                }
                            } else {
                                this.ctx.onAction("create_region_from_saved_selection", { selection_tag: item.tag, tag: val });
                            }
                        } else if (mode === "label") {
                            this.ctx.onAction("create_label_from_saved_selection", { selection_tag: item.tag, text: val });
                        }
                        inlineForm.style.display = "none";
                        btnRow.style.display = "flex";
                    });

                    inlineCancel.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        inlineForm.style.display = "none";
                        btnRow.style.display = "flex";
                    });

                    inlineInput.onkeydown = (e) => {
                        e.stopPropagation();
                        if (e.key === "Enter") {
                            e.preventDefault();
                            inlineConfirm.click();
                        } else if (e.key === "Escape") {
                            e.preventDefault();
                            inlineCancel.click();
                        }
                    };

                    inlineForm.appendChild(inlineInput);
                    inlineForm.appendChild(inlineConfirm);
                    inlineForm.appendChild(inlineCancel);

                    inlineForm.style.display = "flex";
                    inlineInput.focus?.();
                };

                const activateBtn = makeButton(isActive ? "Deactivate" : "Activate", () => {
                    if (isActive) {
                        this.ctx.onAction("set_active_selection_operation", { operation: "none" });
                    } else {
                        this.onActivateSavedSelection(item.tag);
                    }
                });
                activateBtn.setAttribute("data-molsysviewer-saved-selection-activate", item.tag);

                const renameBtn = makeButton("Rename", () => showForm("rename"));
                renameBtn.setAttribute("data-molsysviewer-saved-selection-rename", item.tag);
                const regionBtn = makeButton("Region", () => showForm("region"));
                regionBtn.setAttribute("data-molsysviewer-saved-selection-to-region", item.tag);
                const labelBtn = makeButton("Annotation", () => showForm("label"));
                labelBtn.setAttribute("data-molsysviewer-saved-selection-to-label", item.tag);

                const deleteBtn = makeButton("🗑", () => this.ctx.onAction("delete_selection", { tag: item.tag }));
                deleteBtn.setAttribute("data-molsysviewer-saved-selection-delete", item.tag);

                for (const btn of [activateBtn, renameBtn, regionBtn, labelBtn, deleteBtn]) {
                    btn.style.flex = "0 1 auto";
                    btn.style.padding = "3px 6px";
                    btn.style.fontSize = "10px";
                    btnRow.appendChild(btn);
                }

                card.appendChild(btnRow);
                savedList.appendChild(card);
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No saved selections yet.";
            savedList.appendChild(emptyLabel);
        }
    }

    private renderActiveSelectionCard(): HTMLDivElement {
        const card = document.createElement("div");
        card.setAttribute("data-molsysviewer-active-selection-card", "true");
        Object.assign(card.style, {
            display: "flex",
            flexDirection: "column",
            padding: "8px 10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.035)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "10px",
        });

        const activeCount = this.currentSelection?.count_atoms ?? 0;
        const hasActive = activeCount > 0;

        // Row 1: Single line container (Dot, Title, Count, and Buttons)
        const row1 = document.createElement("div");
        Object.assign(row1.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
            gap: "6px 10px",
            flexWrap: "wrap",
        });

        // Left: Dot and Title
        const leftWrap = document.createElement("div");
        Object.assign(leftWrap.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "12px",
            fontWeight: "700",
            color: "#f4f4f5",
        });

        const dot = document.createElement("span");
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: hasActive ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: hasActive ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        leftWrap.appendChild(dot);
        leftWrap.appendChild(document.createTextNode("Active Selection"));
        row1.appendChild(leftWrap);

        // Middle/Right-ish: Count text
        const countText = document.createElement("span");
        Object.assign(countText.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.6)",
            marginLeft: "auto",
            marginRight: "4px",
        });
        if (hasActive) {
            const groupCount = this.currentSelection?.count_groups ?? 0;
            const molCount = this.currentSelection?.molecule_indices?.length ?? 0;
            const entCount = this.currentSelection?.entity_indices?.length ?? 0;
            const atomsStr = `${activeCount} atom${activeCount === 1 ? "" : "s"}`;
            const groupsStr = `${groupCount} group${groupCount === 1 ? "" : "s"}`;
            const molsStr = `${molCount} molecule${molCount === 1 ? "" : "s"}`;
            const entsStr = `${entCount} entit${entCount === 1 ? "y" : "ies"}`;
            countText.textContent = `${atomsStr} in ${groupsStr}, ${molsStr} and ${entsStr}`;
        } else {
            countText.textContent = "No selection";
        }
        row1.appendChild(countText);

        // Right: Action Buttons
        const btnRow = document.createElement("div");
        Object.assign(btnRow.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        const deselectBtn = makeButton("Deselect", () => {
            this.ctx.onAction("set_active_selection_operation", { operation: "none" });
            this.showActiveSelectionSaveForm = false;
            this.scheduleRender();
        });
        deselectBtn.setAttribute("data-molsysviewer-active-selection-deselect", "true");
        if (!hasActive) {
            deselectBtn.disabled = true;
            deselectBtn.style.opacity = "0.42";
            deselectBtn.style.cursor = "not-allowed";
        }

        const saveBtn = makeButton("Save...", () => {
            this.showActiveSelectionSaveForm = !this.showActiveSelectionSaveForm;
            this.scheduleRender();
            if (this.showActiveSelectionSaveForm) {
                setTimeout(() => this.activeSelectionSaveInput?.focus?.(), 0);
            }
        });
        saveBtn.setAttribute("data-molsysviewer-active-selection-save-toggle", "true");
        if (!hasActive) {
            saveBtn.disabled = true;
            saveBtn.style.opacity = "0.42";
            saveBtn.style.cursor = "not-allowed";
        }

        for (const btn of [saveBtn, deselectBtn]) {
            btn.style.padding = "4px 8px";
            btn.style.fontSize = "11px";
            btnRow.appendChild(btn);
        }
        row1.appendChild(btnRow);
        card.appendChild(row1);

        // Save Input Form (expanded below row1 if showActiveSelectionSaveForm is true)
        if (this.showActiveSelectionSaveForm && hasActive) {
            const form = document.createElement("div");
            form.setAttribute("data-molsysviewer-active-selection-save-form", "true");
            Object.assign(form.style, {
                display: "flex",
                gap: "6px",
                marginTop: "6px",
                width: "100%",
            });

            const input = document.createElement("input");
            input.type = "text";
            input.placeholder = "Selection name...";
            input.setAttribute("data-molsysviewer-active-selection-save-input", "true");
            this.activeSelectionSaveInput = input;
            Object.assign(input.style, {
                flex: "1 1 auto",
                background: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "6px",
                padding: "4px 8px",
                color: "#fff",
                fontSize: "11px",
                outline: "none",
            });

            const submitForm = () => {
                const tag = input.value.trim();
                if (!tag) return;
                const exists = this.savedSelections.some(s => s.tag === tag);
                if (exists) {
                    const doOverwrite = typeof confirm === "function" ? confirm(`A saved selection named "${tag}" already exists. Overwrite?`) : true;
                    if (doOverwrite) {
                        this.ctx.onAction("delete_selection", { tag });
                        this.ctx.onAction("save_selection", { tag });
                    } else {
                        return;
                    }
                } else {
                    this.ctx.onAction("save_selection", { tag });
                }
                this.showActiveSelectionSaveForm = false;
                this.scheduleRender();
            };

            const cancelForm = () => {
                this.showActiveSelectionSaveForm = false;
                this.scheduleRender();
            };

            // Prevent panel keydowns from firing while typing inside input
            input.addEventListener("keydown", (e) => {
                e.stopPropagation();
                if (e.key === "Enter") {
                    e.preventDefault();
                    submitForm();
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    cancelForm();
                }
            });

            const confirmBtn = makeButton("Create", submitForm);
            confirmBtn.setAttribute("data-molsysviewer-active-selection-save-confirm", "true");
            Object.assign(confirmBtn.style, {
                background: "#6366f1",
                border: "0",
                borderRadius: "6px",
                padding: "4px 8px",
                color: "#fff",
                fontSize: "11px",
                fontWeight: "600",
                flex: "0 0 auto",
            });

            form.appendChild(input);
            form.appendChild(confirmBtn);
            card.appendChild(form);
        }

        return card;
    }

    private renderSelectionQueryComposer(): HTMLDivElement {
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-selection-query-composer", "true");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.05)",
        });

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "700",
            color: "#f4f4f5",
        });
        title.textContent = "Select by Query";
        container.appendChild(title);

        const composer = this.getSelectionQueryComposer();
        if (this.helpBtn) {
            this.helpBtn.title = this.selectionCheatSheetOpen ? "Hide selection query examples" : "Show selection query examples";
        }
        container.appendChild(composer.element());



        // Shortcuts Row
        const presetRow = document.createElement("div");
        presetRow.setAttribute("data-molsysviewer-selection-query-presets", "true");
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
            chip.title = preset.expression;
            chip.setAttribute("data-molsysviewer-selection-query-preset", preset.label);
            Object.assign(chip.style, {
                background: "rgba(99,102,241,0.12)",
                border: "1px solid rgba(129,140,248,0.24)",
                borderRadius: "999px",
                padding: "3px 8px",
                color: "#c7d2fe",
                fontSize: "10px",
                lineHeight: "14px",
                cursor: "pointer",
            });
            chip.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                composer.setExpression(preset.expression, "MolSysMT");
            });
            presetRow.appendChild(chip);
        }
        container.appendChild(presetRow);

        if (this.selectionCheatSheetOpen) {
            const cheatSheet = document.createElement("div");
            cheatSheet.setAttribute("data-molsysviewer-selection-cheatsheet", "true");
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
                row.setAttribute("data-molsysviewer-selection-cheatsheet-example", label);
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
            container.appendChild(cheatSheet);
        }

        return container;
    }



    private getSelectionQueryComposer(): ManualQueryComposer {
        if (this.selectionQueryComposer === null) {
            this.helpBtn = makeButton("?", () => {
                this.selectionCheatSheetOpen = !this.selectionCheatSheetOpen;
                this.scheduleRender();
            });
            this.helpBtn.setAttribute("data-molsysviewer-selection-cheatsheet-toggle", "true");
            Object.assign(this.helpBtn.style, {
                flex: "0 0 30px",
                width: "30px",
                padding: "6px 0",
                fontWeight: "700",
            });

            this.selectionQueryComposer = new ManualQueryComposer(
                "selection",
                (details) => {
                    this.ctx.onAction("selection_query_preview_request", details);
                },
                () => {},
                {
                    buttonLabel: "Select",
                    hideSyntax: true,
                    middleElement: this.helpBtn
                }
            );
        }
        return this.selectionQueryComposer;
    }
}
