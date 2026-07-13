import type { ActiveSelectionPayload } from "../../managers/active-selection";
import { ManualQueryComposer } from "../query-composer";
import type { RegionDetails, RegionSummary, SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import { PanelAction, PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { FALLBACK_PRESETS, bindContinuousHistory, createStyleDraftControls, makeStyleControlRow } from "./style-composer";

/**
 * Studio -> Regions subpanel.
 *
 * Self-contained module: owns all region view-state (create origin, collision
 * dialogs, inspect set, boolean-composer selection, style-composer target) and
 * its DOM. Receives domain state via typed setters (setRegions, setStyleOptions,
 * updateDetails, updatePreview, setCurrentSelection) and talks to the host only
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
    private regionQueryComposer: ManualQueryComposer | null = null;
    /** Live ref to the create-from-query button, so typing updates only it. */
    private queryCreateButton: HTMLButtonElement | null = null;
    private regionCreateOrigin: "active" | "query" | "split" | "saved" = "active";
    private regionCreateTag = "";
    private regionCreateRepresentation = "";
    private regionSplitLevel: "chain" | "molecule" | "entity" = "chain";
    private regionSplitScope: "all" | "active" = "all";
    private regionSavedSelectionTag = "";
    private regionRenameTag: string | null = null;
    private regionCreateCollision: { action: PanelAction; details: Record<string, unknown>; tag: string } | null = null;
    private regionRenameCollisionTag: string | null = null;
    private regionBooleanA = "";
    private regionBooleanTargets = new Set<string>();
    private regionBooleanOperation: "union" | "intersection" | "difference" = "union";
    private regionBooleanOutput = "";
    private regionComposeCollision: { tag: string; details: Record<string, unknown> } | null = null;
    private readonly regionInspectOpen = new Set<string>();
    private readonly regionDetails = new Map<string, RegionDetails>();
    private readonly regionDetailsRequests = new Map<string, number>();
    private nextRegionDetailsRequest = 1;
    private regionBooleanAttention = false;
    private regionBooleanComposerElement: HTMLDivElement | null = null;
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
        // A blur can be caused by pressing another control. Let that control's
        // click complete before replacing the panel DOM with the pending state.
        setTimeout(() => this.scheduleRender(), 0);
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        const tags = this.regions.map(item => item.tag);
        if (!tags.includes(this.regionBooleanA)) {
            this.regionBooleanA = tags[0] ?? "";
        }
        for (const tag of [...this.regionBooleanTargets]) {
            if (!tags.includes(tag) || tag === this.regionBooleanA) {
                this.regionBooleanTargets.delete(tag);
            }
        }
        if (this.regionBooleanTargets.size === 0) {
            const fallback = tags.find(tag => tag !== this.regionBooleanA);
            if (fallback) this.regionBooleanTargets.add(fallback);
        }
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
        if (!this.regionCreateRepresentation && this.wholeHidden) {
            this.regionCreateRepresentation = "inherit";
        }
        this.scheduleExternalRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        const tags = this.savedSelections.map(item => item.tag);
        if (!tags.includes(this.regionSavedSelectionTag)) {
            this.regionSavedSelectionTag = tags[0] ?? "";
        }
        if (this.regionCreateOrigin === "saved") {
            this.scheduleExternalRender();
        }
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

    /** Route a query preview; returns true if it belonged to this panel's composer. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        if (this.regionQueryComposer?.updatePreview(preview)) {
            // The composer repaints its own status line; only the create button
            // depends on verification, so update it in place, not the whole panel.
            this.syncQueryCreateButton();
            return true;
        }
        return false;
    }

    /**
     * Enable/disable the create-from-query button from the composer's verification
     * state. Typing invalidates the preview, so this must run on every composer
     * change — in place, without repainting the panel.
     */
    private syncQueryCreateButton(): void {
        const button = this.queryCreateButton;
        if (!button) return;
        const verified = this.regionQueryComposer?.isVerifiedNonEmpty() ?? false;
        button.disabled = !verified;
        button.style.opacity = verified ? "1" : "0.42";
        button.style.cursor = verified ? "pointer" : "not-allowed";
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        if (this.regionCreateOrigin === "active") {
            this.scheduleExternalRender();
        }
    }

    /** Whether a region with this tag currently exists (used by the Selection -> Region bridge). */
    hasRegion(tag: string): boolean {
        return this.regions.some(region => region.tag === tag);
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Create & Global Actions"));
        this.host.appendChild(this.renderRegionCreateSection());
        this.host.appendChild(makeSectionHeader("Regions"));

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
        } else if (this.regionCreateOrigin === "split") {
            const emptyLabel = document.createElement("div");
            Object.assign(emptyLabel.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            emptyLabel.textContent = "No regions yet.";
            list.appendChild(emptyLabel);
        }
        this.host.appendChild(makeSectionHeader("Boolean Composition"));
        this.host.appendChild(this.renderRegionBooleanComposer());
    }

    private getRegionQueryComposer(): ManualQueryComposer {
        if (this.regionQueryComposer === null) {
            this.regionQueryComposer = new ManualQueryComposer("region", (details) => {
                this.ctx.onAction("selection_query_preview_request", details);
            }, () => this.syncQueryCreateButton());
        }
        return this.regionQueryComposer;
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

    private renderRegionCreateSection(): HTMLDivElement {
        // Only the "query" origin renders the create-from-query button.
        this.queryCreateButton = null;
        const container = document.createElement("div");
        container.setAttribute("data-molsysviewer-region-create", "true");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.03)",
        });

        const originRow = document.createElement("div");
        Object.assign(originRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: "6px",
        });
        for (const [origin, label] of [
            ["active", "Active"],
            ["query", "Query"],
            ["split", "Split"],
            ["saved", "Saved"],
        ] as const) {
            const button = makeButton(label, () => {
                this.regionCreateOrigin = origin;
                this.scheduleRender();
            });
            button.setAttribute("data-molsysviewer-region-create-origin", origin);
            if (this.regionCreateOrigin === origin) {
                button.style.borderColor = "rgba(99,102,241,0.7)";
                button.style.background = "rgba(99,102,241,0.18)";
            }
            originRow.appendChild(button);
        }
        container.appendChild(originRow);

        const optionsRow = document.createElement("div");
        Object.assign(optionsRow.style, {
            display: "grid",
            gridTemplateColumns: this.regionCreateOrigin === "split"
                ? "minmax(110px, 1fr)"
                : "minmax(0, 1fr) minmax(110px, 0.7fr)",
            gap: "6px",
        });
        const tagInput = document.createElement("input");
        tagInput.type = "text";
        tagInput.value = this.regionCreateTag;
        tagInput.placeholder = "Name (optional)";
        tagInput.setAttribute("data-molsysviewer-region-create-tag", "true");
        tagInput.addEventListener("input", () => {
            this.regionCreateTag = tagInput.value;
        });
        const representation = makeStyledSelect(
            this.getRepresentationOptions(true),
            this.regionCreateRepresentation,
            (value) => { this.regionCreateRepresentation = value; },
        );
        representation.setAttribute("data-molsysviewer-region-create-representation", "true");
        if (this.regionCreateOrigin !== "split") {
            optionsRow.appendChild(tagInput);
        }
        optionsRow.appendChild(representation);
        container.appendChild(optionsRow);

        const createWithCollision = (action: PanelAction, details: Record<string, unknown>) => {
            const tag = this.regionCreateTag.trim();
            const initialVisual =
                this.regionCreateRepresentation.startsWith("preset:")
                    ? { preset: this.regionCreateRepresentation.slice("preset:".length) }
                    : this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {};
            const emit = () => {
                this.ctx.onAction(action, {
                    ...details,
                    ...(tag ? { tag } : {}),
                    ...initialVisual,
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            };
            if (tag && this.regions.some(region => region.tag === tag)) {
                this.regionCreateCollision = { action, details, tag };
                this.scheduleRender();
                return;
            }
            emit();
        };

        if (this.regionCreateOrigin === "active") {
            const create = makeButton("Create from active selection", () => {
                createWithCollision("create_region_from_selection", {});
            });
            create.setAttribute("data-molsysviewer-region-create-active", "true");
            create.disabled = this.currentSelection.count_atoms <= 0;
            if (create.disabled) {
                create.style.opacity = "0.42";
                create.style.cursor = "not-allowed";
                create.title = "Select atoms before creating a region.";
            }
            container.appendChild(create);
        } else if (this.regionCreateOrigin === "query") {
            const composer = this.getRegionQueryComposer();
            container.appendChild(composer.element());
            const create = makeButton("Create from query", () => {
                const query = composer.value();
                if (!query.expression || !composer.isVerifiedNonEmpty()) return;
                createWithCollision("create_region_from_query", query);
            });
            create.setAttribute("data-molsysviewer-region-create-query", "true");
            this.queryCreateButton = create;
            this.syncQueryCreateButton();
            container.appendChild(create);
        } else {
            const splitRow = document.createElement("div");
            Object.assign(splitRow.style, {
                display: "flex",
                gap: "6px",
            });
            const level = makeStyledSelect(
                ["chain", "molecule", "entity"],
                this.regionSplitLevel,
                (value) => {
                    this.regionSplitLevel = value === "molecule"
                        ? "molecule"
                        : value === "entity" ? "entity" : "chain";
                },
            );
            level.setAttribute("data-molsysviewer-region-split-level", "true");
            const scope = makeStyledSelect(
                [
                    { value: "all", label: "All atoms" },
                    { value: "active", label: "Active selection" },
                ],
                this.regionSplitScope,
                (value) => {
                    this.regionSplitScope = value === "active" ? "active" : "all";
                    this.scheduleRender();
                },
            );
            scope.setAttribute("data-molsysviewer-region-split-scope", "true");
            const split = makeButton("Split", () => {
                if (this.regionSplitScope === "active" && this.currentSelection.count_atoms <= 0) return;
                if (this.currentSelection.count_atoms > 250 && typeof window !== "undefined" && typeof window.confirm === "function") {
                    const ok = window.confirm(`Split may create many regions from ${this.currentSelection.count_atoms} selected atoms. Continue?`);
                    if (!ok) return;
                }
                this.ctx.onAction("make_regions_by", {
                    element: this.regionSplitLevel,
                    ...(this.regionSplitScope === "active" ? { selection: "active" } : {}),
                    ...(this.regionCreateRepresentation.startsWith("preset:")
                        ? { preset: this.regionCreateRepresentation.slice("preset:".length) }
                        : this.regionCreateRepresentation ? { representation: this.regionCreateRepresentation } : {}),
                });
            });
            split.setAttribute("data-molsysviewer-region-split", "true");
            split.disabled = this.regionSplitScope === "active" && this.currentSelection.count_atoms <= 0;
            if (split.disabled) {
                split.style.opacity = "0.42";
                split.style.cursor = "not-allowed";
                split.title = "Select atoms before splitting over the active selection.";
            }
            splitRow.appendChild(level);
            splitRow.appendChild(scope);
            splitRow.appendChild(split);
            container.appendChild(splitRow);
        }

        if (this.regionCreateOrigin === "saved") {
            const savedRow = document.createElement("div");
            Object.assign(savedRow.style, {
                display: "flex",
                gap: "6px",
            });
            const savedTags = this.savedSelections.map(item => item.tag);
            const saved = makeStyledSelect(savedTags, this.regionSavedSelectionTag, value => {
                this.regionSavedSelectionTag = value;
            });
            saved.setAttribute("data-molsysviewer-region-create-saved-select", "true");
            const createSaved = makeButton("Create from saved selection", () => {
                if (!this.regionSavedSelectionTag) return;
                createWithCollision("create_region_from_saved_selection", {
                    selection_tag: this.regionSavedSelectionTag,
                });
            });
            createSaved.setAttribute("data-molsysviewer-region-create-saved", "true");
            createSaved.disabled = savedTags.length === 0;
            if (createSaved.disabled) {
                createSaved.style.opacity = "0.42";
                createSaved.style.cursor = "not-allowed";
                createSaved.title = "Save a selection before creating a region from it.";
            }
            savedRow.appendChild(saved);
            savedRow.appendChild(createSaved);
            container.appendChild(savedRow);
        }

        if (this.regionCreateCollision !== null) {
            const collision = document.createElement("div");
            collision.setAttribute("data-molsysviewer-region-create-collision", this.regionCreateCollision.tag);
            collision.textContent = `"${this.regionCreateCollision.tag}" already exists.`;
            const rename = makeButton("Rename", () => {
                this.regionCreateCollision = null;
                this.scheduleRender();
            });
            rename.setAttribute("data-molsysviewer-region-collision-rename", "create");
            const overwrite = makeButton("Overwrite", () => {
                const pending = this.regionCreateCollision;
                if (pending === null) return;
                this.ctx.onAction("delete_region", { tag: pending.tag });
                this.ctx.onAction(pending.action, {
                    ...pending.details,
                    tag: pending.tag,
                    ...(this.regionCreateRepresentation.startsWith("preset:")
                        ? { preset: this.regionCreateRepresentation.slice("preset:".length) }
                        : this.regionCreateRepresentation ? { representation: this.regionCreateRepresentation } : {}),
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            });
            overwrite.setAttribute("data-molsysviewer-region-collision-overwrite", "create");
            const cancel = makeButton("Cancel", () => {
                this.regionCreateCollision = null;
                this.scheduleRender();
            });
            cancel.setAttribute("data-molsysviewer-region-collision-cancel", "create");
            collision.appendChild(rename);
            collision.appendChild(overwrite);
            collision.appendChild(cancel);
            container.appendChild(collision);
        }

        const globalRow = document.createElement("div");
        Object.assign(globalRow.style, {
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "6px",
            paddingTop: "2px",
        });
        const showAll = makeButton("Show all", () => this.ctx.onAction("show_all_regions"));
        showAll.setAttribute("data-molsysviewer-region-show-all", "true");
        const hideAll = makeButton("Hide all", () => this.ctx.onAction("hide_all_regions"));
        hideAll.setAttribute("data-molsysviewer-region-hide-all", "true");
        globalRow.appendChild(showAll);
        globalRow.appendChild(hideAll);
        container.appendChild(globalRow);
        return container;
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
        });

        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const focus = makeButton(item.tag, () => this.onFocusRegion(item.tag));
        focus.setAttribute("data-molsysviewer-region-focus", item.tag);
        focus.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
        focus.style.flex = "1 1 auto";
        focus.style.textAlign = "left";
        const hint = document.createElement("span");
        hint.textContent = `${item.atom_count} atoms · ${item.preset ?? item.representation ?? "base"}`;
        Object.assign(hint.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.58)",
        });
        focus.appendChild(hint);
        header.appendChild(focus);

        if ((item.overlap_tags?.length ?? 0) > 0 && !item.hidden) {
            const overlap = makeButton("⚠", () => {
                this.regionBooleanA = item.tag;
                this.regionBooleanTargets = new Set(
                    (item.overlap_tags ?? []).filter(tag => tag !== item.tag),
                );
                this.regionBooleanOperation = "difference";
                this.regionComposeCollision = null;
                this.regionBooleanAttention = true;
                this.scheduleRender();
                this.regionBooleanComposerElement?.scrollIntoView?.({
                    behavior: "smooth",
                    block: "nearest",
                });
            });
            overlap.setAttribute("data-molsysviewer-region-overlap", item.tag);
            overlap.title = `Overlaps: ${item.overlap_tags!.join(", ")}`;
            overlap.setAttribute("aria-label", overlap.title);
            header.appendChild(overlap);
        }
        const visibility = makeButton(item.hidden ? "Show" : "Hide", () =>
            this.ctx.onAction("toggle_region_visibility", { tag: item.tag })
        );
        visibility.setAttribute("data-molsysviewer-region-visibility", item.tag);
        if (!this.regionHasOwnVisual(item)) {
            visibility.disabled = true;
            visibility.style.opacity = "0.42";
            visibility.style.cursor = "not-allowed";
            visibility.title = "This base region has no visual representation to hide.";
        }
        const remove = makeButton("Delete", () =>
            this.ctx.onAction("delete_region", { tag: item.tag })
        );
        remove.setAttribute("data-molsysviewer-region-delete", item.tag);
        header.appendChild(visibility);
        header.appendChild(remove);
        card.appendChild(header);

        const actions = document.createElement("div");
        actions.setAttribute("data-molsysviewer-region-actions", item.tag);
        Object.assign(actions.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
        });
        const isolate = makeButton("Isolate", () =>
            this.ctx.onAction("show_only_region", { tag: item.tag })
        );
        isolate.setAttribute("data-molsysviewer-region-isolate", item.tag);
        const complement = makeButton("Complement", () =>
            this.ctx.onAction("create_complementary_region", { tag: item.tag })
        );
        complement.setAttribute("data-molsysviewer-region-complement", item.tag);
        const duplicate = makeButton("Duplicate", () =>
            this.ctx.onAction("duplicate_region", { tag: item.tag })
        );
        duplicate.setAttribute("data-molsysviewer-region-duplicate", item.tag);
        const reset = makeButton("Reset repr", () =>
            this.ctx.onAction("reset_region_representation", { tag: item.tag })
        );
        reset.setAttribute("data-molsysviewer-region-reset", item.tag);
        const raise = makeButton("Raise", () =>
            this.ctx.onAction("raise_region_to_front", { tag: item.tag })
        );
        raise.setAttribute("data-molsysviewer-region-raise", item.tag);
        const lower = makeButton("Lower", () =>
            this.ctx.onAction("send_region_to_back", { tag: item.tag })
        );
        lower.setAttribute("data-molsysviewer-region-lower", item.tag);
        const rename = makeButton("Rename", () => {
            this.regionRenameTag = item.tag;
            this.scheduleRender();
        });
        rename.setAttribute("data-molsysviewer-region-rename", item.tag);
        const style = makeButton("Style", () => {
            this.activeStyleRegionTag = this.activeStyleRegionTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        style.setAttribute("data-molsysviewer-region-style", item.tag);
        const inspect = makeButton("Inspect", () => {
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
        inspect.setAttribute("data-molsysviewer-region-inspect", item.tag);
        for (const button of [isolate, complement, rename, duplicate, reset, raise, lower, style, inspect]) {
            button.style.fontSize = "10px";
            button.style.padding = "3px 6px";
            actions.appendChild(button);
        }
        card.appendChild(actions);

        if (this.regionRenameTag === item.tag) {
            const form = document.createElement("div");
            form.setAttribute("data-molsysviewer-region-rename-form", item.tag);
            Object.assign(form.style, {
                display: "flex",
                gap: "6px",
            });
            const input = document.createElement("input");
            input.type = "text";
            input.value = item.tag;
            input.setAttribute("data-molsysviewer-region-rename-input", item.tag);
            input.style.flex = "1 1 0";
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

    private renderRegionBooleanComposer(): HTMLDivElement {
        const container = document.createElement("div");
        this.regionBooleanComposerElement = container;
        container.setAttribute("data-molsysviewer-region-boolean-composer", "true");
        container.setAttribute(
            "data-molsysviewer-region-boolean-attention",
            String(this.regionBooleanAttention),
        );
        if (this.regionBooleanAttention) {
            this.regionBooleanAttention = false;
        }
        container.setAttribute("data-molsysviewer-region-boolean-current-a", this.regionBooleanA);
        container.setAttribute(
            "data-molsysviewer-region-boolean-current-b",
            Array.from(this.regionBooleanTargets).join(","),
        );
        container.setAttribute(
            "data-molsysviewer-region-boolean-current-operation",
            this.regionBooleanOperation,
        );
        Object.assign(container.style, {
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) minmax(120px, 0.8fr) minmax(0, 1fr)",
            gap: "6px",
            padding: "10px",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "8px",
        });
        const tags = this.regions.map(item => item.tag);
        const left = makeStyledSelect(tags, this.regionBooleanA, value => {
            this.regionBooleanA = value;
            this.regionBooleanTargets.delete(value);
            if (this.regionBooleanTargets.size === 0) {
                const fallback = tags.find(tag => tag !== value);
                if (fallback) this.regionBooleanTargets.add(fallback);
                this.scheduleRender();
            }
        });
        left.setAttribute("data-molsysviewer-region-boolean-a", "true");
        const operation = makeStyledSelect(
            [
                { value: "union", label: "Union (A ∪ B)" },
                { value: "intersection", label: "Intersection (A ∩ B)" },
                { value: "difference", label: "Difference (A − B)" },
            ],
            this.regionBooleanOperation,
            value => {
                this.regionBooleanOperation = value === "intersection"
                    ? "intersection"
                    : value === "difference" ? "difference" : "union";
                if (this.regionBooleanOperation === "intersection" && this.regionBooleanTargets.size > 1) {
                    this.regionBooleanTargets = new Set([Array.from(this.regionBooleanTargets)[0]]);
                }
                this.scheduleRender();
            },
        );
        operation.setAttribute("data-molsysviewer-region-boolean-operation", "true");
        container.appendChild(left);
        container.appendChild(operation);

        const targetContainer = document.createElement("div");
        targetContainer.setAttribute("data-molsysviewer-region-boolean-targets", "true");
        Object.assign(targetContainer.style, {
            display: "flex",
            flexDirection: "column",
            gap: "3px",
        });
        const candidateTags = tags.filter(tag => tag !== this.regionBooleanA);
        if (this.regionBooleanOperation === "intersection") {
            const current = Array.from(this.regionBooleanTargets).find(tag => candidateTags.includes(tag)) ?? candidateTags[0] ?? "";
            if (current && (this.regionBooleanTargets.size !== 1 || !this.regionBooleanTargets.has(current))) {
                this.regionBooleanTargets = new Set([current]);
            }
            const right = makeStyledSelect(candidateTags, current, value => {
                this.regionBooleanTargets = new Set(value ? [value] : []);
            });
            right.setAttribute("data-molsysviewer-region-boolean-b", "true");
            targetContainer.appendChild(right);
        } else {
            for (const tag of candidateTags) {
                const row = document.createElement("label");
                Object.assign(row.style, {
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    fontSize: "11px",
                    color: "rgba(244,244,245,0.72)",
                });
                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.checked = this.regionBooleanTargets.has(tag);
                checkbox.setAttribute("data-molsysviewer-region-boolean-target", tag);
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        this.regionBooleanTargets.add(tag);
                    } else {
                        this.regionBooleanTargets.delete(tag);
                    }
                });
                const label = document.createElement("span");
                label.textContent = tag;
                row.appendChild(checkbox);
                row.appendChild(label);
                targetContainer.appendChild(row);
            }
        }
        container.appendChild(targetContainer);

        const output = document.createElement("input");
        output.type = "text";
        output.placeholder = "Output name (optional)";
        output.value = this.regionBooleanOutput;
        output.setAttribute("data-molsysviewer-region-boolean-output", "true");
        output.addEventListener("input", () => {
            this.regionBooleanOutput = output.value;
        });
        const create = makeButton("Create", () => {
            const operandTags = Array.from(this.regionBooleanTargets)
                .filter(tag => tag && tag !== this.regionBooleanA && tags.includes(tag));
            if (!this.regionBooleanA || operandTags.length === 0) {
                return;
            }
            const tag = this.regionBooleanOutput.trim();
            const details = {
                tag_a: this.regionBooleanA,
                operand_tags: operandTags,
                op: this.regionBooleanOperation,
                ...(tag ? { new_tag: tag } : {}),
            };
            if (tag && tags.includes(tag)) {
                this.regionComposeCollision = { tag, details };
                this.scheduleRender();
                return;
            }
            this.ctx.onAction("compose_regions", details);
            this.regionBooleanOutput = "";
            this.regionBooleanAttention = false;
        });
        create.disabled = tags.length < 2 || !this.regionBooleanA || this.regionBooleanTargets.size === 0;
        create.setAttribute("data-molsysviewer-region-boolean-create", "true");
        container.appendChild(output);
        container.appendChild(create);

        if (this.regionComposeCollision !== null) {
            const collision = document.createElement("div");
            collision.setAttribute(
                "data-molsysviewer-region-boolean-collision",
                this.regionComposeCollision.tag,
            );
            collision.textContent = `"${this.regionComposeCollision.tag}" already exists.`;
            const rename = makeButton("Rename", () => {
                this.regionComposeCollision = null;
                this.scheduleRender();
            });
            const overwrite = makeButton("Overwrite", () => {
                const pending = this.regionComposeCollision;
                if (pending === null) return;
                this.ctx.onAction("compose_regions", {
                    ...pending.details,
                    overwrite: true,
                });
                this.regionBooleanOutput = "";
                this.regionComposeCollision = null;
            });
            overwrite.setAttribute("data-molsysviewer-region-boolean-overwrite", "true");
            const cancel = makeButton("Cancel", () => {
                this.regionComposeCollision = null;
                this.scheduleRender();
            });
            collision.appendChild(rename);
            collision.appendChild(overwrite);
            collision.appendChild(cancel);
            container.appendChild(collision);
        }
        return container;
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

    // ── 3. Overlays Section Rendering ────────────────────────



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
