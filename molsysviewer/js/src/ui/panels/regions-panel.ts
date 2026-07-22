import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { RegionDetails, RegionSummary, SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelAction, PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { FALLBACK_PRESETS, bindContinuousHistory, createStyleDraftControls, makeStyleControlRow } from "./style-composer";

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
        this.ctx.setBadge(String(items.length));
        this.scheduleExternalRender();
    }

    setStyleOptions(options: { representations: string[]; presets: string[]; wholeHidden?: boolean }): void {
        this.regionStyleRepresentations = [...options.representations];
        this.regionStylePresets = [...options.presets];
        this.wholeHidden = options.wholeHidden === true;
        this.scheduleExternalRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
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

    /** Query composer previews are no longer owned by the Regions panel. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        return false;
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
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

        // Global Actions: Show all, Hide all
        const globalRow = document.createElement("div");
        Object.assign(globalRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "6px",
            marginBottom: "10px",
        });
        const showAll = makeButton("Show all", () => this.ctx.onAction("show_all_regions"));
        showAll.setAttribute("data-molsysviewer-region-show-all", "true");
        const hideAll = makeButton("Hide all", () => this.ctx.onAction("hide_all_regions"));
        hideAll.setAttribute("data-molsysviewer-region-hide-all", "true");
        globalRow.appendChild(showAll);
        globalRow.appendChild(hideAll);
        this.host.appendChild(globalRow);

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
            background: isVisible && hasVisual ? "#34d399" : "rgba(244,244,245,0.28)",
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

        const renameBtn = makeButton("Rename", () => {
            this.regionRenameTag = item.tag;
            this.scheduleRender();
        });
        renameBtn.setAttribute("data-molsysviewer-region-rename", item.tag);

        const styleBtn = makeButton("Style", () => {
            this.activeStyleRegionTag = this.activeStyleRegionTag === item.tag ? null : item.tag;
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

        for (const btn of [renameBtn, styleBtn, inspectBtn, deleteBtn]) {
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
                if (event.key !== "Enter") return;
                event.preventDefault();
                confirmRename();
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
        const draftHeading = document.createElement("div");
        draftHeading.textContent = "Style draft";
        draftHeading.setAttribute("data-molsysviewer-region-style-draft-heading", tag);
        Object.assign(draftHeading.style, {
            fontSize: "10px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.55)",
        });
        container.appendChild(draftHeading);

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

        const immediateHeading = document.createElement("div");
        immediateHeading.textContent = "Immediate adjustments";
        immediateHeading.setAttribute("data-molsysviewer-region-style-immediate-heading", tag);
        Object.assign(immediateHeading.style, {
            fontSize: "10px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.55)",
            paddingTop: "2px",
        });
        container.appendChild(controls.qualityRow);
        container.appendChild(controls.colorRow);
        container.appendChild(immediateHeading);
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
            this.ctx.onAction("set_region_representation", {
                tag,
                ...(item.preset
                    ? { preset: item.preset }
                    : { representation: item.representation }),
                params: {
                    ...params,
                    alpha: Number(opacity.value),
                },
            });
        });

        const actionsRow = document.createElement("div");
        Object.assign(actionsRow.style, {
            display: "flex",
            justifyContent: "flex-end",
            gap: "6px",
            width: "100%",
            marginTop: "4px",
        });

        const cancelBtn = makeButton("Cancel", () => {
            this.activeStyleRegionTag = null;
            this.scheduleRender();
        });
        cancelBtn.setAttribute("data-molsysviewer-region-style-cancel", tag);
        Object.assign(cancelBtn.style, {
            flex: "0 0 auto",
            fontSize: "10px",
            padding: "3px 8px",
        });

        const applyBtn = makeButton("Apply Style", () => {
            const next = buildStyleAction();
            this.ctx.onAction(next.action, next.details);
            this.activeStyleRegionTag = null;
            this.scheduleRender();
        });
        applyBtn.setAttribute("data-molsysviewer-region-style-apply", tag);
        Object.assign(applyBtn.style, {
            flex: "0 0 auto",
            fontSize: "10px",
            padding: "3px 8px",
            background: "rgba(16,185,129,0.15)",
            border: "1px solid rgba(16,185,129,0.3)",
        });
        applyBtn.addEventListener("mouseenter", () => {
            applyBtn.style.background = "rgba(16,185,129,0.25)";
            applyBtn.style.border = "1px solid rgba(16,185,129,0.5)";
        });
        applyBtn.addEventListener("mouseleave", () => {
            applyBtn.style.background = "rgba(16,185,129,0.15)";
            applyBtn.style.border = "1px solid rgba(16,185,129,0.3)";
        });

        actionsRow.appendChild(cancelBtn);
        actionsRow.appendChild(applyBtn);
        container.appendChild(actionsRow);

        return container;
    }
}
