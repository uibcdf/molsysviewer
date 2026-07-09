import type { ActiveSelectionPayload } from "../../managers/active-selection";
import { ManualQueryComposer } from "../query-composer";
import type { RegionDetails, RegionSummary, SelectionQueryPreview } from "../group-panel";
import { PanelContext, StudioPanel } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";

/**
 * Studio -> Regions subpanel.
 *
 * Self-contained module: owns all region view-state (create origin, collision
 * dialogs, inspect set, boolean-composer selection, style-composer target) and
 * its DOM. Receives domain state via typed setters (setRegions, setStyleOptions,
 * updateDetails, updatePreview, setCurrentSelection) and talks to the host only
 * through the injected PanelContext plus an onFocusRegion callback.
 */
export class RegionsPanel implements StudioPanel {
    readonly key = "regions";
    private host: HTMLElement | null = null;

    // Domain state (pushed from the controller)
    private regions: RegionSummary[] = [];
    private regionStyleRepresentations: string[] = [];
    private regionStylePresets: string[] = [];
    private currentSelection: ActiveSelectionPayload = { count_atoms: 0 } as ActiveSelectionPayload;

    // View state (owned locally)
    private activeStyleRegionTag: string | null = null;
    private regionQueryComposer: ManualQueryComposer | null = null;
    private regionCreateOrigin: "active" | "query" | "split" = "active";
    private regionCreateTag = "";
    private regionCreateRepresentation = "";
    private regionSplitLevel: "chain" | "molecule" | "entity" = "chain";
    private regionRenameTag: string | null = null;
    private regionCreateCollision: { action: string; details: Record<string, unknown>; tag: string } | null = null;
    private regionRenameCollisionTag: string | null = null;
    private regionBooleanA = "";
    private regionBooleanB = "";
    private regionBooleanOperation: "union" | "intersection" | "difference" = "union";
    private regionBooleanOutput = "";
    private regionComposeCollision: { tag: string; details: Record<string, unknown> } | null = null;
    private readonly regionInspectOpen = new Set<string>();
    private readonly regionDetails = new Map<string, RegionDetails>();
    private readonly regionDetailsRequests = new Map<string, number>();
    private nextRegionDetailsRequest = 1;
    private regionBooleanAttention = false;
    private regionBooleanComposerElement: HTMLDivElement | null = null;

    constructor(
        private readonly ctx: PanelContext,
        private readonly onFocusRegion: (tag: string) => void,
    ) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        const tags = this.regions.map(item => item.tag);
        if (!tags.includes(this.regionBooleanA)) {
            this.regionBooleanA = tags[0] ?? "";
        }
        if (!tags.includes(this.regionBooleanB) || this.regionBooleanB === this.regionBooleanA) {
            this.regionBooleanB = tags.find(tag => tag !== this.regionBooleanA) ?? "";
        }
        for (const tag of [...this.regionInspectOpen]) {
            if (!tags.includes(tag)) {
                this.regionInspectOpen.delete(tag);
                this.regionDetails.delete(tag);
                this.regionDetailsRequests.delete(tag);
            }
        }
        this.ctx.setBadge(String(items.length));
        this.render();
    }

    setStyleOptions(options: { representations: string[]; presets: string[] }): void {
        this.regionStyleRepresentations = [...options.representations];
        this.regionStylePresets = [...options.presets];
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
        this.render();
    }

    /** Route a query preview; returns true if it belonged to this panel's composer. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        if (this.regionQueryComposer?.updatePreview(preview)) {
            this.render();
            return true;
        }
        return false;
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        if (this.regionCreateOrigin === "active") {
            this.render();
        }
    }

    /** Whether a region with this tag currently exists (used by the Selection -> Region bridge). */
    hasRegion(tag: string): boolean {
        return this.regions.some(region => region.tag === tag);
    }

    render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Create & Global Actions"));
        this.host.appendChild(this.renderRegionCreateSection());
        this.host.appendChild(makeSectionHeader("Boolean Composition"));
        this.host.appendChild(this.renderRegionBooleanComposer());
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

    private getRegionQueryComposer(): ManualQueryComposer {
        if (this.regionQueryComposer === null) {
            this.regionQueryComposer = new ManualQueryComposer("region", (details) => {
                this.ctx.onAction("selection_query_preview_request", details);
            });
        }
        return this.regionQueryComposer;
    }

    private renderRegionCreateSection(): HTMLDivElement {
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
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "6px",
        });
        for (const [origin, label] of [
            ["active", "Active"],
            ["query", "Query"],
            ["split", "Split"],
        ] as const) {
            const button = makeButton(label, () => {
                this.regionCreateOrigin = origin;
                this.render();
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
            [
                { value: "", label: "Base" },
                "cartoon",
                "backbone",
                "ball-and-stick",
                "line",
                "spacefill",
                "putty",
            ],
            this.regionCreateRepresentation,
            (value) => { this.regionCreateRepresentation = value; },
        );
        representation.setAttribute("data-molsysviewer-region-create-representation", "true");
        if (this.regionCreateOrigin !== "split") {
            optionsRow.appendChild(tagInput);
        }
        optionsRow.appendChild(representation);
        container.appendChild(optionsRow);

        const createWithCollision = (action: string, details: Record<string, unknown>) => {
            const tag = this.regionCreateTag.trim();
            const emit = () => {
                this.ctx.onAction(action, {
                    ...details,
                    ...(tag ? { tag } : {}),
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            };
            if (tag && this.regions.some(region => region.tag === tag)) {
                this.regionCreateCollision = { action, details, tag };
                this.render();
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
            create.disabled = !composer.isVerifiedNonEmpty();
            if (create.disabled) {
                create.style.opacity = "0.42";
                create.style.cursor = "not-allowed";
            }
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
            const split = makeButton("Split", () => {
                this.ctx.onAction("make_regions_by", {
                    element: this.regionSplitLevel,
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
            });
            split.setAttribute("data-molsysviewer-region-split", "true");
            splitRow.appendChild(level);
            splitRow.appendChild(split);
            container.appendChild(splitRow);
        }

        if (this.regionCreateCollision !== null) {
            const collision = document.createElement("div");
            collision.setAttribute("data-molsysviewer-region-create-collision", this.regionCreateCollision.tag);
            collision.textContent = `"${this.regionCreateCollision.tag}" already exists.`;
            const rename = makeButton("Rename", () => {
                this.regionCreateCollision = null;
                this.render();
            });
            rename.setAttribute("data-molsysviewer-region-collision-rename", "create");
            const overwrite = makeButton("Overwrite", () => {
                const pending = this.regionCreateCollision;
                if (pending === null) return;
                this.ctx.onAction("delete_region", { tag: pending.tag });
                this.ctx.onAction(pending.action, {
                    ...pending.details,
                    tag: pending.tag,
                    ...(this.regionCreateRepresentation
                        ? { representation: this.regionCreateRepresentation }
                        : {}),
                });
                this.regionCreateTag = "";
                this.regionCreateCollision = null;
            });
            overwrite.setAttribute("data-molsysviewer-region-collision-overwrite", "create");
            const cancel = makeButton("Cancel", () => {
                this.regionCreateCollision = null;
                this.render();
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
                this.regionBooleanB = item.overlap_tags![0];
                this.regionBooleanOperation = "difference";
                this.regionComposeCollision = null;
                this.regionBooleanAttention = true;
                this.render();
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
        const rename = makeButton("Rename", () => {
            this.regionRenameTag = item.tag;
            this.render();
        });
        rename.setAttribute("data-molsysviewer-region-rename", item.tag);
        const style = makeButton("Style", () => {
            this.activeStyleRegionTag = this.activeStyleRegionTag === item.tag ? null : item.tag;
            this.render();
        });
        style.setAttribute("data-molsysviewer-region-style", item.tag);
        const inspect = makeButton("Inspect", () => {
            if (this.regionInspectOpen.has(item.tag)) {
                this.regionInspectOpen.delete(item.tag);
                this.regionDetailsRequests.delete(item.tag);
                this.render();
                return;
            }
            this.regionInspectOpen.add(item.tag);
            this.requestRegionDetails(item.tag);
            this.render();
        });
        inspect.setAttribute("data-molsysviewer-region-inspect", item.tag);
        for (const button of [isolate, complement, rename, duplicate, reset, style, inspect]) {
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
                    this.render();
                    return;
                }
                const collision = this.regions.some(region => region.tag === newTag);
                if (collision) {
                    this.regionRenameCollisionTag = newTag;
                    this.render();
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
                this.render();
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
                    this.render();
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
                    this.render();
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
        container.setAttribute("data-molsysviewer-region-boolean-current-a", this.regionBooleanA);
        container.setAttribute("data-molsysviewer-region-boolean-current-b", this.regionBooleanB);
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
            if (this.regionBooleanB === value) {
                this.regionBooleanB = tags.find(tag => tag !== value) ?? "";
                this.render();
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
            },
        );
        operation.setAttribute("data-molsysviewer-region-boolean-operation", "true");
        const right = makeStyledSelect(tags, this.regionBooleanB, value => {
            this.regionBooleanB = value;
        });
        right.setAttribute("data-molsysviewer-region-boolean-b", "true");
        container.appendChild(left);
        container.appendChild(operation);
        container.appendChild(right);

        const output = document.createElement("input");
        output.type = "text";
        output.placeholder = "Output name (optional)";
        output.value = this.regionBooleanOutput;
        output.setAttribute("data-molsysviewer-region-boolean-output", "true");
        output.addEventListener("input", () => {
            this.regionBooleanOutput = output.value;
        });
        const create = makeButton("Create", () => {
            if (!this.regionBooleanA || !this.regionBooleanB || this.regionBooleanA === this.regionBooleanB) {
                return;
            }
            const tag = this.regionBooleanOutput.trim();
            const details = {
                tag_a: this.regionBooleanA,
                tag_b: this.regionBooleanB,
                op: this.regionBooleanOperation,
                ...(tag ? { new_tag: tag } : {}),
            };
            if (tag && tags.includes(tag)) {
                this.regionComposeCollision = { tag, details };
                this.render();
                return;
            }
            this.ctx.onAction("compose_regions", details);
            this.regionBooleanOutput = "";
        });
        create.disabled = tags.length < 2 || !this.regionBooleanA || !this.regionBooleanB;
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
                this.render();
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
                this.render();
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
        const refresh = makeButton("Refresh", () => {
            this.requestRegionDetails(tag);
            this.render();
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

        const makeControlRow = (label: string, control: HTMLElement): HTMLDivElement => {
            const row = document.createElement("div");
            Object.assign(row.style, {
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
            row.appendChild(text);
            row.appendChild(control);
            return row;
        };

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
        const fallbackPresets = [
            "atomic-detail",
            "auto",
            "coarse-surface",
            "empty",
            "polymer-and-ligand",
            "polymer-cartoon",
        ];
        const representations = this.regionStyleRepresentations.length > 0
            ? this.regionStyleRepresentations
            : fallbackRepresentations;
        const presets = this.regionStylePresets.length > 0
            ? this.regionStylePresets
            : fallbackPresets;
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

        let representationSelect: HTMLSelectElement;
        let presetSelect: HTMLSelectElement;
        representationSelect = makeStyledSelect(
            [{ value: "", label: "Base" }, ...representations],
            item.preset ? "" : (item.representation ?? ""),
            (value) => {
                if (value) presetSelect.value = "";
            },
        );
        representationSelect.setAttribute("data-molsysviewer-region-style-representation", tag);
        presetSelect = makeStyledSelect(
            [{ value: "", label: "No preset" }, ...presets],
            item.preset ?? "",
            (value) => {
                if (value) representationSelect.value = "";
            },
        );
        presetSelect.setAttribute("data-molsysviewer-region-style-preset", tag);
        container.appendChild(makeControlRow("Representation", representationSelect));
        container.appendChild(makeControlRow("Preset", presetSelect));

        const immediateHeading = document.createElement("div");
        immediateHeading.textContent = "Immediate adjustments";
        immediateHeading.setAttribute("data-molsysviewer-region-style-immediate-heading", tag);
        Object.assign(immediateHeading.style, {
            fontSize: "10px",
            fontWeight: "600",
            color: "rgba(244,244,245,0.55)",
            paddingTop: "2px",
        });
        const opacityWrap = document.createElement("div");
        Object.assign(opacityWrap.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const opacity = document.createElement("input");
        opacity.type = "range";
        opacity.min = "0";
        opacity.max = "1";
        opacity.step = "0.05";
        opacity.value = String(typeof params.alpha === "number" ? params.alpha : 1);
        opacity.setAttribute("data-molsysviewer-region-style-opacity", tag);
        const opacityValue = document.createElement("span");
        opacityValue.textContent = Number(opacity.value).toFixed(2);
        opacityValue.setAttribute("data-molsysviewer-region-style-opacity-value", tag);
        opacity.addEventListener("input", () => {
            opacityValue.textContent = Number(opacity.value).toFixed(2);
        });
        opacityWrap.appendChild(opacity);
        opacityWrap.appendChild(opacityValue);
        const opacityRow = makeControlRow("Opacity", opacityWrap);

        const qualityValues = ["auto", "lowest", "lower", "low", "medium", "high", "higher", "highest", "custom"];
        const quality = makeStyledSelect(
            qualityValues,
            typeof params.quality === "string" ? params.quality : "auto",
            () => {},
        );
        quality.setAttribute("data-molsysviewer-region-style-quality", tag);
        container.appendChild(makeControlRow("Quality", quality));

        const customColorInput = document.createElement("input");
        customColorInput.type = "color";
        customColorInput.value = "#3b82f6";
        customColorInput.setAttribute("data-molsysviewer-region-style-uniform-color", tag);
        Object.assign(customColorInput.style, {
            width: "24px",
            height: "24px",
            border: "1px solid rgba(255,255,255,0.25)",
            borderRadius: "4px",
            padding: "0",
            background: "transparent",
            cursor: "pointer",
            boxSizing: "border-box",
            overflow: "hidden",
            outline: "none",
        });

        const colorScheme = makeStyledSelect(
            [
                { value: "", label: "Keep current" },
                { value: "element_cpk", label: "Element (CPK)" },
                { value: "chain_default", label: "Chain" },
                { value: "secondary_structure_default", label: "Secondary structure" },
                { value: "physicochemical", label: "Physicochemical" },
                { value: "residue_name", label: "Residue name" },
                { value: "molecule_type", label: "Molecule type" },
                { value: "entity_default", label: "Entity" },
                { value: "illustrative_default", label: "Illustrative" },
                { value: "uniform", label: "Uniform color" },
            ],
            typeof params.color_scheme === "string" ? params.color_scheme : "",
            (val) => {
                customColorInput.style.display = val === "uniform" ? "inline-block" : "none";
            },
        );
        colorScheme.setAttribute("data-molsysviewer-region-style-color-scheme", tag);
        customColorInput.style.display = colorScheme.value === "uniform" ? "inline-block" : "none";

        const colorRight = document.createElement("div");
        Object.assign(colorRight.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        colorRight.appendChild(customColorInput);
        colorRight.appendChild(colorScheme);
        container.appendChild(makeControlRow("Color", colorRight));
        container.appendChild(immediateHeading);
        container.appendChild(opacityRow);

        const attributeRow = document.createElement("div");
        Object.assign(attributeRow.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
        });
        const attribute = makeStyledSelect(
            [
                { value: "", label: "None" },
                ...(item.available_attributes ?? []),
            ],
            "",
            (value) => {
                if (!value) return;
                this.ctx.onAction("color_region_by_attribute", {
                    tag,
                    attribute: value,
                });
            },
        );
        attribute.setAttribute("data-molsysviewer-region-style-color-attribute", tag);
        const resetColors = makeButton("Reset colors", () =>
            this.ctx.onAction("reset_region_colors", { tag })
        );
        resetColors.setAttribute("data-molsysviewer-region-style-reset-colors", tag);
        attributeRow.appendChild(attribute);
        attributeRow.appendChild(resetColors);
        container.appendChild(makeControlRow("Color by", attributeRow));

        const buildStyleAction = () => {
            const selectedPreset = presetSelect.value;
            const selectedRepresentation = representationSelect.value;
            if (!selectedPreset && !selectedRepresentation) {
                return { action: "reset_region_representation", details: { tag } };
            }
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
                        : { representation: selectedRepresentation }),
                    params: nextParams,
                },
            };
        };
        opacity.addEventListener("change", () => {
            if (!item.representation && !item.preset) return;
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
            this.render();
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
            this.render();
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
