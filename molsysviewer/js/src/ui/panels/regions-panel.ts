import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { RegionDetails, RegionSummary, SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelAction, PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { FALLBACK_PRESETS, bindContinuousHistory, createStyleDraftControls, makeStyleControlRow } from "./style-composer";
import { ManualQueryComposer } from "../query-composer";

/**
 * Studio -> Regions subpanel.
 *
 * Self-contained module: owns all region view-state (inspect set, style-composer target) and
 * its DOM. Receives domain state via typed setters (setRegions, setStyleOptions,
 * updateDetails, setCurrentSelection) and talks to the host only
 * through the injected PanelContext plus an onFocusRegion callback.
 */
export class RegionsPanel extends BasePanel {
    readonly key = "regions";

    // Domain state (pushed from the controller)
    private regions: RegionSummary[] = [];
    private regionStyleRepresentations: string[] = [];
    private regionStylePresets: string[] = [];
    private currentSelection: ActiveSelectionPayload = { count_atoms: 0 } as ActiveSelectionPayload;
    private savedSelections: SavedSelectionSummary[] = [];
    private wholeHidden = false;

    // View state (owned locally)
    private activeStyleRegionTag: string | null = null;
    private regionRenameTag: string | null = null;
    private regionRenameCollisionTag: string | null = null;
    private readonly regionInspectOpen = new Set<string>();
    private readonly regionDetails = new Map<string, RegionDetails>();
    private readonly regionDetailsRequests = new Map<string, number>();
    private nextRegionDetailsRequest = 1;
    private continuousHistoryEdit = false;
    private continuousHistoryRenderPending = false;
    private historyState = { canUndo: false, canRedo: false };
    private readonly regionStyleBackups = new Map<string, { representation: string | undefined; preset: string | undefined; params: any }>();

    // Region creation components
    private regionsQueryComposer: ManualQueryComposer | null = null;
    private regionsCheatSheetOpen = false;
    private showRegionCreateForm = false;
    private regionCreateInput: HTMLInputElement | null = null;

    constructor(
        private readonly ctx: PanelContext,
        private readonly onFocusRegion: (tag: string) => void,
    ) {
        super();
    }

    private scheduleExternalRender(): void {
        if (this.continuousHistoryEdit) {
            this.continuousHistoryRenderPending = true;
            return;
        }
        this.scheduleRender();
    }

    private finishContinuousHistoryEdit(): void {
        this.ctx.onAction("end_scene_history_coalescing");
        this.continuousHistoryEdit = false;
        if (!this.continuousHistoryRenderPending) return;
        this.continuousHistoryRenderPending = false;
        setTimeout(() => this.scheduleRender(), 0);
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        const tags = this.regions.map(item => item.tag);
        for (const tag of [...this.regionInspectOpen]) {
            if (!tags.includes(tag)) {
                this.regionInspectOpen.delete(tag);
                this.regionDetails.delete(tag);
                this.regionDetailsRequests.delete(tag);
            }
        }
        if (this.activeStyleRegionTag && !tags.includes(this.activeStyleRegionTag)) {
            this.activeStyleRegionTag = null;
        }
        this.ctx.setBadge(String(items.length));
        this.scheduleExternalRender();
    }

    setStyleOptions(options: { representations: string[]; presets: string[]; wholeHidden?: boolean }): void {
        this.regionStyleRepresentations = [...options.representations];
        this.regionStylePresets = [...options.presets];
        this.wholeHidden = options.wholeHidden === true;
        this.scheduleExternalRender();
    }

    updateHistory(state: { canUndo: boolean; canRedo: boolean }): void {
        this.historyState = state;
        this.scheduleExternalRender();
    }

    updateDetails(details: RegionDetails): void {
        const expectedRequest = this.regionDetailsRequests.get(details.tag);
        if (
            expectedRequest === undefined
            || details.request_id !== expectedRequest
            || !this.regionInspectOpen.has(details.tag)
        ) {
            return;
        }
        this.regionDetails.set(details.tag, details);
        this.scheduleExternalRender();
    }

    /** Query composer previews for regions. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        if (!this.regionsQueryComposer) return false;
        const updated = this.regionsQueryComposer.updatePreview(preview);
        if (updated && preview.ok === true) {
            const { expression, syntax } = this.regionsQueryComposer.value();
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

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        this.scheduleRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.scheduleRender();
    }

    /** Whether a region with this tag currently exists (used by the Selection -> Region bridge). */
    hasRegion(tag: string): boolean {
        return this.regions.some(region => region.tag === tag);
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // Header Regions
        this.host.appendChild(makeSectionHeader("Regions"));

        // 1. Resumen global de visibilidad
        const summaryCard = document.createElement("div");
        summaryCard.setAttribute("data-molsysviewer-region-summary-card", "true");
        Object.assign(summaryCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "8px 10px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.035)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "10px",
        });

        const totalRegions = this.regions.length;
        const visibleRegionsCount = this.regions.filter(region => !region.hidden).length;

        // Row 1: Visibility summary count and Show all/Hide all buttons
        const row1 = document.createElement("div");
        Object.assign(row1.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            gap: "10px",
        });

        const regionsInfo = document.createElement("div");
        Object.assign(regionsInfo.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.75)",
        });

        const regionsDot = document.createElement("span");
        const anyVisible = totalRegions > 0 && visibleRegionsCount > 0;
        Object.assign(regionsDot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: anyVisible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: anyVisible ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        regionsInfo.appendChild(regionsDot);
        regionsInfo.appendChild(document.createTextNode(`${visibleRegionsCount} of ${totalRegions} region${totalRegions === 1 ? "" : "s"} visible`));
        row1.appendChild(regionsInfo);

        const actionsCol = document.createElement("div");
        Object.assign(actionsCol.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        const showAll = makeButton("Show all", () => this.ctx.onAction("show_all_regions"));
        showAll.setAttribute("data-molsysviewer-region-show-all", "true");
        const hideAll = makeButton("Hide all", () => this.ctx.onAction("hide_all_regions"));
        hideAll.setAttribute("data-molsysviewer-region-hide-all", "true");

        for (const btn of [showAll, hideAll]) {
            btn.style.padding = "3px 6px";
            btn.style.fontSize = "10px";
            btn.style.whiteSpace = "nowrap";
            btn.style.flex = "0 0 auto";
            actionsCol.appendChild(btn);
        }
        row1.appendChild(actionsCol);
        summaryCard.appendChild(row1);

        // Row 2: Whole structure visibility info
        const row2 = document.createElement("div");
        Object.assign(row2.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
        });

        const wholeInfo = document.createElement("div");
        Object.assign(wholeInfo.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.75)",
        });

        const wholeDot = document.createElement("span");
        const wholeVisible = !this.wholeHidden;
        Object.assign(wholeDot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: wholeVisible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: wholeVisible ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        wholeInfo.appendChild(wholeDot);
        wholeInfo.appendChild(document.createTextNode(`Whole Structure: ${wholeVisible ? "Visible" : "Hidden"}`));
        row2.appendChild(wholeInfo);
        summaryCard.appendChild(row2);

        this.host.appendChild(summaryCard);

        // 2. Sección de Creación: "New Region"
        this.host.appendChild(makeSectionHeader("New Region"));
        this.renderNewRegionElements(this.host);

        // 3. Lista de regiones creadas: "Saved Regions"
        this.host.appendChild(makeSectionHeader("Saved Regions"));
        const list = document.createElement("div");
        list.setAttribute("data-molsysviewer-region-list", "true");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });
        this.host.appendChild(list);

        if (this.regions.length > 0) {
            const sorted = [...this.regions].sort((a, b) => a.tag.localeCompare(b.tag));
            for (const item of sorted) {
                list.appendChild(this.renderRegionCard(item));
            }
        } else {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No regions yet.";
            list.appendChild(emptyLabel);
        }
    }

    private getRepresentationOptions(includeBase = true): Array<string | { value: string; label: string }> {
        const fallbackRepresentations = [
            "backbone",
            "ball-and-stick",
            "carbohydrate",
            "cartoon",
            "ellipsoid",
            "gaussian-surface",
            "gaussian-volume",
            "line",
            "molecular-surface",
            "point",
            "putty",
            "spacefill",
        ];
        const representations = this.regionStyleRepresentations.length > 0
            ? this.regionStyleRepresentations
            : fallbackRepresentations;
        const presets = this.regionStylePresets.length > 0
            ? this.regionStylePresets
            : [];
        const options: Array<string | { value: string; label: string }> = [];
        if (includeBase) options.push({ value: "", label: "Base" });
        options.push({ value: "inherit", label: "Inherit" });
        options.push(...representations);
        options.push(...presets.map(preset => ({ value: `preset:${preset}`, label: `Preset: ${preset}` })));
        return options;
    }

    private regionHasOwnVisual(item: RegionSummary): boolean {
        return Boolean(item.representation || item.preset);
    }

    private renderRegionCard(item: RegionSummary): HTMLDivElement {
        const card = document.createElement("div");
        card.setAttribute("data-molsysviewer-region-card", item.tag);
        card.setAttribute("data-molsysviewer-region-hidden", String(item.hidden));
        Object.assign(card.style, {
            display: "flex",
            flexDirection: "column",
            gap: "7px",
            padding: "9px 10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.035)",
            opacity: item.hidden ? "0.58" : "1",
            transition: "background 0.1s ease",
            cursor: "pointer",
        });

        card.addEventListener("mouseenter", () => {
            card.style.background = "rgba(255,255,255,0.06)";
        });
        card.addEventListener("mouseleave", () => {
            card.style.background = "rgba(255,255,255,0.035)";
        });

        const isVisible = !item.hidden;
        const hasVisual = this.regionHasOwnVisual(item);

        const dot = document.createElement("span");
        dot.setAttribute("data-molsysviewer-region-visibility", item.tag);
        Object.assign(dot.style, {
            width: "7px",
            height: "7px",
            borderRadius: "999px",
            background: isVisible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: isVisible && hasVisual ? "0 0 8px rgba(52,211,153,0.5)" : "none",
            flexShrink: "0",
            marginRight: "6px",
            cursor: hasVisual ? "pointer" : "not-allowed",
        });
        if (!hasVisual) {
            dot.title = "This base region has no visual representation to toggle.";
        }

        const toggleVisibility = () => {
            if (hasVisual) {
                this.ctx.onAction("toggle_region_visibility", { tag: item.tag });
            }
        };

        dot.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleVisibility();
        });

        card.addEventListener("click", (e) => {
            if (e && e.target && e.target !== card && e.target !== topRow && e.target !== title && e.target !== dot) {
                return;
            }
            e?.preventDefault();
            e?.stopPropagation();
            toggleVisibility();
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
        title.appendChild(dot);

        const label = document.createElement("span");
        label.textContent = item.tag;
        label.setAttribute("data-molsysviewer-region-focus", item.tag);
        label.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
        label.style.cursor = "pointer";
        label.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.onFocusRegion(item.tag);
        });
        title.appendChild(label);

        const subtitle = document.createElement("span");
        Object.assign(subtitle.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
            marginLeft: "6px",
            fontWeight: "normal",
        });
        subtitle.textContent = `(${item.atom_count} atoms · ${item.preset ?? item.representation ?? "base"}${item.owner ? ` · from ${item.owner}` : ""})`;
        title.appendChild(subtitle);
        topRow.appendChild(title);
        card.appendChild(topRow);

        // Buttons container row
        const btnRow = document.createElement("div");
        btnRow.setAttribute("data-molsysviewer-region-buttons-row", item.tag);
        Object.assign(btnRow.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
        });

        const visibilityBtn = makeButton(item.hidden ? "Show" : "Hide", () => toggleVisibility());
        visibilityBtn.setAttribute("data-molsysviewer-region-visibility", item.tag);
        if (!hasVisual) {
            visibilityBtn.disabled = true;
            visibilityBtn.style.opacity = "0.42";
            visibilityBtn.style.cursor = "not-allowed";
            visibilityBtn.title = "This base region has no visual representation to hide.";
        }

        const renameBtn = makeButton("Rename", () => {
            this.regionRenameTag = item.tag;
            this.scheduleRender();
        });
        renameBtn.setAttribute("data-molsysviewer-region-rename", item.tag);

        const styleBtn = makeButton("Style", () => {
            if (this.activeStyleRegionTag === item.tag) {
                this.activeStyleRegionTag = null;
                this.regionStyleBackups.delete(item.tag);
            } else {
                this.activeStyleRegionTag = item.tag;
                this.regionStyleBackups.set(item.tag, {
                    representation: item.representation,
                    preset: item.preset,
                    params: item.representation_params ? JSON.parse(JSON.stringify(item.representation_params)) : {},
                });
            }
            this.scheduleRender();
        });
        styleBtn.setAttribute("data-molsysviewer-region-style", item.tag);

        const inspectBtn = makeButton("Inspect", () => {
            if (this.regionInspectOpen.has(item.tag)) {
                this.regionInspectOpen.delete(item.tag);
                this.regionDetailsRequests.delete(item.tag);
                this.scheduleRender();
                return;
            }
            this.regionInspectOpen.add(item.tag);
            this.requestRegionDetails(item.tag);
            this.scheduleRender();
        });
        inspectBtn.setAttribute("data-molsysviewer-region-inspect", item.tag);

        const deleteBtn = makeButton("🗑", () => this.ctx.onAction("delete_region", { tag: item.tag }));
        deleteBtn.setAttribute("data-molsysviewer-region-delete", item.tag);

        for (const btn of [visibilityBtn, renameBtn, styleBtn, inspectBtn, deleteBtn]) {
            btn.style.flex = "0 1 auto";
            btn.style.padding = "3px 6px";
            btn.style.fontSize = "10px";
            btnRow.appendChild(btn);
        }
        card.appendChild(btnRow);

        if (this.regionRenameTag === item.tag) {
            const form = document.createElement("div");
            form.setAttribute("data-molsysviewer-region-rename-form", item.tag);
            Object.assign(form.style, {
                display: "flex",
                gap: "6px",
                marginTop: "4px",
            });
            const input = document.createElement("input");
            input.type = "text";
            input.value = item.tag;
            input.setAttribute("data-molsysviewer-region-rename-input", item.tag);
            Object.assign(input.style, {
                flex: "1 1 0",
                background: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "6px",
                padding: "4px 6px",
                color: "#fff",
                fontSize: "11px",
                outline: "none",
            });
            const confirmRename = () => {
                const newTag = input.value.trim();
                if (!newTag || newTag === item.tag) {
                    this.regionRenameTag = null;
                    this.scheduleRender();
                    return;
                }
                const collision = this.regions.some(region => region.tag === newTag);
                if (collision) {
                    this.regionRenameCollisionTag = newTag;
                    this.scheduleRender();
                    return;
                }
                this.ctx.onAction("rename_region", { tag: item.tag, new_tag: newTag });
                this.regionRenameTag = null;
                this.regionRenameCollisionTag = null;
            };
            input.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    confirmRename();
                } else if (event.key === "Escape") {
                    event.preventDefault();
                    this.regionRenameTag = null;
                    this.scheduleRender();
                }
            });
            const submit = makeButton("Rename", confirmRename);
            submit.setAttribute("data-molsysviewer-region-rename-confirm", item.tag);
            const cancel = makeButton("Cancel", () => {
                this.regionRenameTag = null;
                this.scheduleRender();
            });
            form.appendChild(input);
            form.appendChild(submit);
            form.appendChild(cancel);
            card.appendChild(form);

            if (this.regionRenameCollisionTag !== null) {
                const collisionTag = this.regionRenameCollisionTag;
                const collision = document.createElement("div");
                collision.setAttribute("data-molsysviewer-region-rename-collision", collisionTag);
                collision.textContent = `"${collisionTag}" already exists.`;
                const chooseRename = makeButton("Rename", () => {
                    this.regionRenameCollisionTag = null;
                    this.scheduleRender();
                });
                chooseRename.setAttribute("data-molsysviewer-region-collision-rename", "rename");
                const overwrite = makeButton("Overwrite", () => {
                    this.ctx.onAction("delete_region", { tag: collisionTag });
                    this.ctx.onAction("rename_region", { tag: item.tag, new_tag: collisionTag });
                    this.regionRenameTag = null;
                    this.regionRenameCollisionTag = null;
                });
                overwrite.setAttribute("data-molsysviewer-region-collision-overwrite", "rename");
                const cancelCollision = makeButton("Cancel", () => {
                    this.regionRenameTag = null;
                    this.regionRenameCollisionTag = null;
                    this.scheduleRender();
                });
                cancelCollision.setAttribute("data-molsysviewer-region-collision-cancel", "rename");
                collision.appendChild(chooseRename);
                collision.appendChild(overwrite);
                collision.appendChild(cancelCollision);
                card.appendChild(collision);
            }
        }

        if (this.activeStyleRegionTag === item.tag) {
            card.appendChild(this.renderStyleComposer(item));
        }
        if (this.regionInspectOpen.has(item.tag)) {
            card.appendChild(this.renderRegionInspect(item.tag));
        }

        return card;
    }

    private requestRegionDetails(tag: string): void {
        this.regionDetails.delete(tag);
        const requestId = this.nextRegionDetailsRequest++;
        this.regionDetailsRequests.set(tag, requestId);
        this.ctx.onAction("get_region_details", {
            tag,
            request_id: requestId,
        });
    }

    private renderRegionInspect(tag: string): HTMLDivElement {
        const panel = document.createElement("div");
        panel.setAttribute("data-molsysviewer-region-inspect-panel", tag);
        const details = this.regionDetails.get(tag);
        if (!details) {
            panel.textContent = "Loading...";
            return panel;
        }
        const center = details.center_nm.map(value => Number(value).toFixed(3)).join(", ");
        panel.setAttribute("data-molsysviewer-region-inspect-frame", String(details.structure_index));
        for (const [key, value] of [
            ["atoms", String(details.atom_count)],
            ["groups", String(details.group_count)],
            ["chains", String(details.chain_count)],
            ["frame", String(details.structure_index)],
        ]) {
            const metric = document.createElement("div");
            metric.setAttribute("data-molsysviewer-region-inspect-metric", key);
            metric.textContent = `${key}: ${value}`;
            panel.appendChild(metric);
        }
        const centerRow = document.createElement("div");
        centerRow.setAttribute("data-molsysviewer-region-inspect-center", "true");
        centerRow.textContent = `center [nm]: ${center}`;
        panel.appendChild(centerRow);
        const modeRow = document.createElement("div");
        modeRow.setAttribute("data-molsysviewer-region-inspect-mode", "true");
        modeRow.textContent = `mode: ${details.mode ?? "static"} · order: ${details.order ?? 0}${details.broken ? " · broken recipe" : ""}`;
        panel.appendChild(modeRow);
        if (details.provenance && Object.keys(details.provenance).length > 0) {
            const provenance = document.createElement("div");
            provenance.setAttribute("data-molsysviewer-region-inspect-provenance", "true");
            provenance.textContent = `provenance: ${JSON.stringify(details.provenance)}`;
            panel.appendChild(provenance);
        }
        const refresh = makeButton("Refresh", () => {
            this.requestRegionDetails(tag);
            this.scheduleRender();
        });
        refresh.setAttribute("data-molsysviewer-region-inspect-refresh", tag);
        refresh.title = "Refresh details for the current trajectory frame.";
        panel.appendChild(refresh);
        return panel;
    }

    private renderStyleComposer(item: RegionSummary): HTMLDivElement {
        const tag = item.tag;
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-region-style-composer", tag);
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "8px 10px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.03)",
            border: "1px dashed rgba(255,255,255,0.08)",
            marginTop: "4px",
            marginBottom: "4px",
        });

        const representations = this.getRepresentationOptions(true)
            .filter(option => typeof option === "string" || !option.value.startsWith("preset:"));
        const presets = this.regionStylePresets.length > 0
            ? this.regionStylePresets
            : FALLBACK_PRESETS;
        const params = item.representation_params ?? {};
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            flexWrap: "nowrap",
            marginBottom: "4px",
        });

        const title = document.createElement("div");
        title.textContent = "Style Options";
        title.setAttribute("data-molsysviewer-region-style-options-title", tag);
        Object.assign(title.style, {
            fontSize: "10px",
            fontWeight: "700",
            letterSpacing: "0.04em",
            color: "rgba(244,244,245,0.85)",
        });
        header.appendChild(title);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            alignItems: "center",
            gap: "4px",
            flexWrap: "nowrap",
        });

        const undoBtn = makeButton("Undo", () => {
            this.ctx.onAction("undo_active_selection");
        });
        undoBtn.setAttribute("data-molsysviewer-region-style-undo", tag);
        undoBtn.title = "Undo last action";
        undoBtn.disabled = !this.historyState.canUndo;
        if (undoBtn.disabled) {
            undoBtn.style.opacity = "0.42";
            undoBtn.style.cursor = "not-allowed";
        }
        actions.appendChild(undoBtn);

        const redoBtn = makeButton("Redo", () => {
            this.ctx.onAction("redo_active_selection");
        });
        redoBtn.setAttribute("data-molsysviewer-region-style-redo", tag);
        redoBtn.title = "Redo last action";
        redoBtn.disabled = !this.historyState.canRedo;
        if (redoBtn.disabled) {
            redoBtn.style.opacity = "0.42";
            redoBtn.style.cursor = "not-allowed";
        }
        actions.appendChild(redoBtn);

        const revertBtn = makeButton("Revert", () => {
            const backup = this.regionStyleBackups.get(tag);
            if (backup) {
                this.ctx.onAction("set_region_representation", {
                    tag,
                    ...(backup.preset
                        ? { preset: backup.preset }
                        : { representation: backup.representation ?? "inherit" }),
                    params: backup.params,
                });
            }
        });
        revertBtn.setAttribute("data-molsysviewer-region-style-revert", tag);
        revertBtn.title = "Revert region representation and colors to session start";
        actions.appendChild(revertBtn);

        for (const btn of [undoBtn, redoBtn, revertBtn]) {
            btn.style.flex = "0 1 auto";
            btn.style.padding = "2px 5px";
            btn.style.fontSize = "9px";
        }

        header.appendChild(actions);
        container.appendChild(header);

        const controls = createStyleDraftControls({
            id: tag,
            dataPrefix: "region-style",
            representations,
            presets,
            currentRepresentation: item.representation,
            currentPreset: item.preset,
            params,
            opacityDisabled: !this.regionHasOwnVisual(item),
            opacityDisabledTitle: "Opacity requires a region visual. Choose Inherit or a representation first.",
        });
        const representationSelect = controls.representationSelect;
        const presetSelect = controls.presetSelect;
        const opacity = controls.opacityInput;
        const quality = controls.qualitySelect;
        const customColorInput = controls.customColorInput;
        const colorScheme = controls.colorSchemeSelect;
        container.appendChild(controls.representationRow);
        container.appendChild(controls.presetRow);

        container.appendChild(controls.qualityRow);
        container.appendChild(controls.colorRow);
        container.appendChild(controls.opacityRow);

        const attributeRow = document.createElement("div");
        Object.assign(attributeRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            flexWrap: "wrap",
        });
        const attributeElement = makeStyledSelect(
            ["atom", "group"],
            typeof params.color_attribute_element === "string" ? params.color_attribute_element : "atom",
            () => {},
        );
        attributeElement.setAttribute("data-molsysviewer-region-style-color-attribute-element", tag);
        const palette = makeStyledSelect(
            ["viridis", "plasma", "magma", "inferno", "cividis", "turbo"],
            typeof params.color_attribute_palette === "string" ? params.color_attribute_palette : "viridis",
            () => {},
        );
        palette.setAttribute("data-molsysviewer-region-style-color-attribute-palette", tag);
        const valueRange = document.createElement("input");
        valueRange.type = "text";
        valueRange.placeholder = "range min,max";
        valueRange.value = Array.isArray(params.color_attribute_range)
            ? params.color_attribute_range.join(",")
            : "";
        valueRange.setAttribute("data-molsysviewer-region-style-color-attribute-range", tag);
        Object.assign(valueRange.style, {
            width: "86px",
            background: "rgba(0,0,0,0.28)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "3px 6px",
            color: "#f4f4f5",
            fontSize: "11px",
        });
        const attribute = makeStyledSelect(
            [
                { value: "", label: "None" },
                ...(item.available_attributes ?? []),
            ],
            typeof params.color_attribute === "string" ? params.color_attribute : "",
            (value) => {
                if (!value) return;
                const range = valueRange.value
                    .split(",")
                    .map(part => Number(part.trim()))
                    .filter(value => Number.isFinite(value));
                this.ctx.onAction("color_region_by_attribute", {
                    tag,
                    attribute: value,
                    element: attributeElement.value,
                    palette: palette.value,
                    ...(range.length === 2 ? { value_range: [range[0], range[1]] } : {}),
                    replace: true,
                });
            },
        );
        attribute.setAttribute("data-molsysviewer-region-style-color-attribute", tag);
        const resetColors = makeButton("Reset colors", () =>
            this.ctx.onAction("reset_region_colors", { tag })
        );
        resetColors.setAttribute("data-molsysviewer-region-style-reset-colors", tag);
        attributeRow.appendChild(attribute);
        attributeRow.appendChild(attributeElement);
        attributeRow.appendChild(palette);
        attributeRow.appendChild(valueRange);
        attributeRow.appendChild(resetColors);
        container.appendChild(makeStyleControlRow("Color by", attributeRow));

        const buildStyleAction = (): { action: PanelAction; details: Record<string, unknown> } => {
            const selectedPreset = presetSelect.value;
            const selectedRepresentation = representationSelect.value;
            const nextParams: Record<string, unknown> = {
                ...params,
                alpha: Number(opacity.value),
                quality: quality.value,
            };
            if (colorScheme.value === "uniform") {
                delete nextParams.color_scheme;
                delete nextParams.molstar_color_theme;
                nextParams.color = customColorInput.value;
            } else if (colorScheme.value) {
                delete nextParams.color;
                delete nextParams.molstar_color_theme;
                nextParams.color_scheme = colorScheme.value;
            }
            return {
                action: "set_region_representation",
                details: {
                    tag,
                    ...(selectedPreset
                        ? { preset: selectedPreset }
                        : selectedRepresentation
                            ? { representation: selectedRepresentation }
                            : item.preset
                                ? { preset: item.preset }
                                : { representation: item.representation ?? "inherit" }),
                    params: nextParams,
                },
            };
        };

        const triggerLiveUpdate = () => {
            const next = buildStyleAction();
            this.ctx.onAction(next.action, next.details);
        };

        representationSelect.addEventListener("change", triggerLiveUpdate);
        presetSelect.addEventListener("change", triggerLiveUpdate);
        quality.addEventListener("change", triggerLiveUpdate);
        colorScheme.addEventListener("change", triggerLiveUpdate);
        customColorInput.addEventListener("change", triggerLiveUpdate);

        bindContinuousHistory(
            opacity,
            () => {
                this.continuousHistoryEdit = true;
                this.ctx.onAction("begin_scene_history_coalescing");
            },
            () => this.finishContinuousHistoryEdit(),
        );
        opacity.addEventListener("input", () => {
            if (!this.regionHasOwnVisual(item)) return;
            const next = buildStyleAction();
            this.ctx.onAction(next.action, next.details);
        });

        return container;
    }

    private renderNewRegionElements(parent: HTMLElement): void {
        const INPUT_STYLE = {
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "4px 8px",
            color: "#fff",
            fontSize: "11px",
            outline: "none",
        };

        const activeCount = this.currentSelection?.count_atoms ?? 0;
        const hasActive = activeCount > 0;

        // 1. Active Selection Card
        const activeCard = document.createElement("div");
        activeCard.setAttribute("data-molsysviewer-region-active-selection-card", "true");
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
            fontSize: "11px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.52)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
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
            countText.textContent = `${activeCount} atom${activeCount === 1 ? "" : "s"} in ${groupCount} group${groupCount === 1 ? "" : "s"}`;
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

        const newRegionBtn = makeButton("New region", () => {
            this.showRegionCreateForm = !this.showRegionCreateForm;
            this.scheduleRender();
            if (this.showRegionCreateForm) {
                setTimeout(() => this.regionCreateInput?.focus?.(), 0);
            }
        });
        newRegionBtn.setAttribute("data-molsysviewer-region-create-btn", "true");
        newRegionBtn.disabled = !hasActive;
        newRegionBtn.style.opacity = hasActive ? "1" : "0.42";
        newRegionBtn.style.padding = "4px 8px";
        newRegionBtn.style.fontSize = "11px";
        newRegionBtn.style.whiteSpace = "nowrap";

        const deselectBtn = makeButton("Deselect", () => {
            this.ctx.onAction("set_active_selection_operation", { operation: "none" });
            this.showRegionCreateForm = false;
            this.scheduleRender();
        });
        deselectBtn.setAttribute("data-molsysviewer-region-deselect-btn", "true");
        deselectBtn.disabled = !hasActive;
        deselectBtn.style.opacity = hasActive ? "1" : "0.42";
        deselectBtn.style.padding = "4px 8px";
        deselectBtn.style.fontSize = "11px";
        deselectBtn.style.whiteSpace = "nowrap";

        btnRow.appendChild(newRegionBtn);
        btnRow.appendChild(deselectBtn);
        row1.appendChild(btnRow);

        activeCard.appendChild(row1);

        // Region name input form (without Cancel button)
        if (this.showRegionCreateForm && hasActive) {
            const form = document.createElement("div");
            form.setAttribute("data-molsysviewer-region-create-form", "true");
            Object.assign(form.style, {
                display: "flex",
                gap: "6px",
                marginTop: "6px",
                width: "100%",
            });

            const input = document.createElement("input");
            input.type = "text";
            input.placeholder = "Region name...";
            input.setAttribute("data-molsysviewer-region-create-input", "true");
            this.regionCreateInput = input;
            Object.assign(input.style, {
                flex: "1 1 auto",
                ...INPUT_STYLE,
            });

            const confirmCreate = () => {
                const val = input.value.trim();
                if (!val) return;
                const exists = this.regions.some(r => r.tag === val);
                if (exists) {
                    const doOverwrite = typeof confirm === "function" ? confirm(`A region named "${val}" already exists. Overwrite?`) : true;
                    if (doOverwrite) {
                        this.ctx.onAction("delete_region", { tag: val });
                        this.ctx.onAction("create_region_from_selection", { tag: val });
                    } else {
                        return;
                    }
                } else {
                    this.ctx.onAction("create_region_from_selection", { tag: val });
                }
                this.showRegionCreateForm = false;
                this.scheduleRender();
            };

            input.addEventListener("keydown", (e) => {
                e.stopPropagation();
                if (e.key === "Enter") {
                    e.preventDefault();
                    confirmCreate();
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    this.showRegionCreateForm = false;
                    this.scheduleRender();
                }
            });

            const confirmBtn = makeButton("Create", confirmCreate);
            confirmBtn.setAttribute("data-molsysviewer-region-create-confirm", "true");
            Object.assign(confirmBtn.style, {
                background: "#6366f1",
                border: "0",
                borderRadius: "6px",
                padding: "4px 8px",
                color: "#fff",
                fontSize: "11px",
                fontWeight: "600",
                cursor: "pointer",
            });

            form.appendChild(input);
            form.appendChild(confirmBtn);
            activeCard.appendChild(form);
        }

        parent.appendChild(activeCard);

        // 2. Select by Query Card
        const queryCard = document.createElement("div");
        queryCard.setAttribute("data-molsysviewer-region-query-card", "true");
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
        qHeader.textContent = "Select by Query";
        Object.assign(qHeader.style, {
            fontSize: "11px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.52)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
        });
        queryCard.appendChild(qHeader);

        const composer = this.getRegionsQueryComposer();
        queryCard.appendChild(composer.element());

        // Shortcuts Row
        const presetRow = document.createElement("div");
        presetRow.setAttribute("data-molsysviewer-regions-query-presets", "true");
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
            chip.setAttribute("data-molsysviewer-regions-query-preset", preset.label);
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
        if (this.regionsCheatSheetOpen) {
            const cheatSheet = document.createElement("div");
            cheatSheet.setAttribute("data-molsysviewer-regions-cheatsheet", "true");
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
                row.setAttribute("data-molsysviewer-regions-cheatsheet-example", label);
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
        savedCard.setAttribute("data-molsysviewer-region-activate-saved-card", "true");
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
            fontSize: "11px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.52)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
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

    private getRegionsQueryComposer(): ManualQueryComposer {
        if (!this.regionsQueryComposer) {
            const helpBtn = makeButton("?", () => {
                this.regionsCheatSheetOpen = !this.regionsCheatSheetOpen;
                this.scheduleRender();
            });
            helpBtn.setAttribute("data-molsysviewer-regions-cheatsheet-toggle", "true");
            Object.assign(helpBtn.style, {
                flex: "0 0 30px",
                width: "30px",
                padding: "6px 0",
                fontWeight: "700",
            });

            this.regionsQueryComposer = new ManualQueryComposer(
                "regions",
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
        return this.regionsQueryComposer;
    }
}
