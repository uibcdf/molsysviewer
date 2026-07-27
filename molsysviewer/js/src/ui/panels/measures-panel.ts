import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { formatUnitLabel, makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { ManualQueryComposer } from "../query-composer";
import { renderSelectionDock } from "./selection-dock";

export type MeasurementSummary = {
    kind: "distance" | "angle" | "dihedral" | "measurement";
    tag: string;
    owner?: string;
    layerTag?: string;
    picks: number;
    hidden: boolean;
    atomIndices: number[];
    value: number | null;
    unit: string;
    endpointLabels: string[];
    endpointPolicy: string;
    broken: boolean;
    brokenReason?: string;
};

export type MeasurementSettings = {
    endpointPolicyDefault: "atom" | "centroid" | "representative_atom";
    representativeAtoms: Record<"protein" | "nucleic" | "lipid" | "other", string>;
    structureIndex: number;
    systemLoaded: boolean;
};

export type MeasurementSeries = {
    tag: string;
    requestId: number | null;
    unit: string;
    nFrames: number;
    sparkline: number[];
    sparklineIndices: number[];
    seriesIndex: number | null;
};

const defaultSettings = (): MeasurementSettings => ({
    endpointPolicyDefault: "centroid",
    representativeAtoms: { protein: "CA", nucleic: "P", lipid: "P", other: "" },
    structureIndex: 0,
    systemLoaded: false,
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
    padding: "4px 8px",
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

function formatValue(item: MeasurementSummary): string {
    if (item.broken || item.value === null || !Number.isFinite(item.value)) return "—";
    const unit = item.unit.trim().toLowerCase();
    const digits = unit === "nanometer" || unit === "nanometers" || unit === "nm"
        || unit === "radian" || unit === "radians" ? 3
        : item.kind === "distance" ? 2 : 1;
    return `${item.value.toFixed(digits)} ${formatUnitLabel(item.unit)}`;
}

export function makePurplishSegmentButton(
    text: string,
    isActive: boolean,
    onClick: () => void,
    padding = "6px 0",
    fontSize = "11px",
): HTMLButtonElement {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = text;

    const bgNormal = isActive ? "#6366f1" : "rgba(99, 102, 241, 0.16)";
    const bgHover  = isActive ? "#4f46e5" : "rgba(99, 102, 241, 0.28)";
    const borderNormal = isActive ? "1px solid #818cf8" : "1px solid rgba(129, 140, 248, 0.3)";
    const borderHover  = isActive ? "1px solid #a5b4fc" : "1px solid rgba(129, 140, 248, 0.5)";

    Object.assign(btn.style, {
        flex: "1 1 0",
        padding,
        fontSize,
        fontWeight: isActive ? "700" : "500",
        textAlign: "center",
        background: bgNormal,
        border: borderNormal,
        borderRadius: "6px",
        color: isActive ? "#ffffff" : "#c7d2fe",
        cursor: "pointer",
        transition: "all 0.12s ease",
    });

    btn.addEventListener("mouseenter", () => {
        btn.style.background = bgHover;
        btn.style.border = borderHover;
    });
    btn.addEventListener("mouseleave", () => {
        btn.style.background = bgNormal;
        btn.style.border = borderNormal;
    });
    btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
    });

    return btn;
}

export class MeasuresPanel extends BasePanel {
    readonly key = "measures";
    private measurements: MeasurementSummary[] = [];
    private settings = defaultSettings();
    private selection: ActiveSelectionPayload = emptySelection();
    private savedSelections: SavedSelectionSummary[] = [];
    private readonly expandedSeries = new Set<string>();
    private readonly seriesByTag = new Map<string, MeasurementSeries>();
    private readonly expectedSeriesRequest = new Map<string, number>();
    private nextSeriesRequest = 1;
    private editTag: string | null = null;
    private inlineTab: "active" | "query" | "saved" = "active";

    private selectedSavedKind: "distance" | "angle" | "dihedral" = "distance";
    private stagedSlots: ({
        atom_indices: number[];
        summary: string;
        endpointType: string;
        policy: string;
    } | null)[] = [null, null, null, null];

    private activeSlotExpansion: number | null = null;

    private measuresQueryComposer: ManualQueryComposer | null = null;
    private measuresCheatSheetOpen = false;

    constructor(private readonly ctx: PanelContext) { super(); }

    setMeasurements(measurements: MeasurementSummary[], settings: MeasurementSettings): void {
        this.measurements = [...measurements];
        this.settings = settings;
        this.ctx.setBadge(String(measurements.length));
        this.scheduleRender();
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.selection = selection;
        if (this.activeSlotExpansion !== null && selection.atom_indices && selection.atom_indices.length > 0) {
            const activeCount = selection.atom_indices.length;
            const endpointType = activeCount === 1 ? "Atom" : "Centroid";
            const summaryText = `${activeCount} atom${activeCount === 1 ? "" : "s"} · ${endpointType}`;
            this.stagedSlots[this.activeSlotExpansion] = {
                atom_indices: [...selection.atom_indices],
                summary: summaryText,
                endpointType,
                policy: "centroid",
            };
            this.activeSlotExpansion = null;
        }
        this.scheduleRender();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.scheduleRender();
    }

    updateSeries(payload: MeasurementSeries): void {
        const expected = this.expectedSeriesRequest.get(payload.tag);
        if (expected === undefined || payload.requestId !== expected) return;
        this.seriesByTag.set(payload.tag, payload);
        this.scheduleRender();
    }

    /** Query composer previews for measures. */
    updatePreview(preview: SelectionQueryPreview): boolean {
        if (!this.measuresQueryComposer) return false;
        const updated = this.measuresQueryComposer.updatePreview(preview);
        if (updated && preview.ok === true) {
            const { expression, syntax } = this.measuresQueryComposer.value();
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

        // Header Measures
        this.host.appendChild(makeSectionHeader("Measures"));

        // 1. Global Visibility summary card (unified like Regions)
        this.host.appendChild(this.renderGlobalVisibilityCard());

        // 2. Sección "New measurement"
        this.host.appendChild(makeSectionHeader("New measurement"));
        this.renderNewMeasurementElements(this.host);

        // 3. Sección "Saved measurements"
        this.host.appendChild(makeSectionHeader("Saved measurements"));
        const list = document.createElement("div");
        list.setAttribute("data-molsysviewer-measurement-list", "true");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "7px" });
        if (this.measurements.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No measurements yet. Select endpoints and choose a kind above.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "11px" });
            list.appendChild(empty);
        } else {
            for (const item of this.measurements) list.appendChild(this.renderMeasurement(item));
        }
        this.host.appendChild(list);
    }

    private renderGlobalVisibilityCard(): HTMLDivElement {
        const summaryCard = document.createElement("div");
        summaryCard.setAttribute("data-molsysviewer-measurement-summary-card", "true");
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

        const totalCount = this.measurements.length;
        const visibleCount = this.measurements.filter(m => !m.hidden).length;

        // Row 1: Visibility count and Actions
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
        info.appendChild(document.createTextNode(`${visibleCount} of ${totalCount} measurement${totalCount === 1 ? "" : "s"} visible`));
        row.appendChild(info);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });
        for (const [label, action] of [
            ["Show all", "show_all_measurements"],
            ["Hide all", "hide_all_measurements"],
        ] as const) {
            const button = makeButton(label, () => {
                this.ctx.onAction(action);
            });
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            button.style.whiteSpace = "nowrap";
            button.setAttribute("data-molsysviewer-measurement-global", action);
            actions.appendChild(button);
        }
        row.appendChild(actions);
        summaryCard.appendChild(row);

        return summaryCard;
    }

    private isSavedSelectionActive(item: SavedSelectionSummary): boolean {
        const activeIndices = this.selection?.atom_indices;
        if (!activeIndices || !item.atom_indices) return false;
        if (activeIndices.length !== item.atom_indices.length) return false;
        const s = new Set(activeIndices);
        return item.atom_indices.every(idx => s.has(idx));
    }

    private getMeasuresQueryComposer(): ManualQueryComposer {
        if (!this.measuresQueryComposer) {
            const helpBtn = makeButton("?", () => {
                this.measuresCheatSheetOpen = !this.measuresCheatSheetOpen;
                this.scheduleRender();
            });
            helpBtn.setAttribute("data-molsysviewer-measures-cheatsheet-toggle", "true");
            Object.assign(helpBtn.style, {
                flex: "0 0 30px",
                width: "30px",
                padding: "6px 0",
                fontWeight: "700",
            });

            this.measuresQueryComposer = new ManualQueryComposer(
                "measures",
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
        return this.measuresQueryComposer;
    }

    private renderNewMeasurementElements(parent: HTMLElement): void {
        const count = this.selection.atom_indices.length;
        const hasActive = count > 0;

        // Mode segment buttons row
        const modeRow = document.createElement("div");
        Object.assign(modeRow.style, {
            display: "flex",
            gap: "6px",
            marginBottom: "10px",
        });
        for (const kind of ["distance", "angle", "dihedral"] as const) {
            const isActive = this.selectedSavedKind === kind;
            const btn = makePurplishSegmentButton(
                kind[0].toUpperCase() + kind.slice(1),
                isActive,
                () => {
                    this.selectedSavedKind = kind;
                    this.stagedSlots = [null, null, null, null];
                    this.activeSlotExpansion = null;
                    this.scheduleRender();
                },
                "6px 0",
                "11px"
            );
            btn.setAttribute("data-molsysviewer-measurement-mode-btn", kind);
            modeRow.appendChild(btn);
        }
        parent.appendChild(modeRow);

        const requiredCount = this.selectedSavedKind === "distance" ? 2 : this.selectedSavedKind === "angle" ? 3 : 4;

        // 1. Staged Slots Card (holds Selection rows and Inline Selection Mechanism)
        const slotsCard = document.createElement("div");
        slotsCard.setAttribute("data-molsysviewer-measurement-slots-card", "true");
        Object.assign(slotsCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "10px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.035)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "10px",
        });

        for (let i = 0; i < requiredCount; i++) {
            const slot = this.stagedSlots[i];
            const isExpanded = this.activeSlotExpansion === i;

            const slotWrapper = document.createElement("div");
            Object.assign(slotWrapper.style, {
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                padding: "6px 8px",
                background: isExpanded ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.15)",
                border: "1px solid " + (isExpanded ? "rgba(255,255,255,0.16)" : "rgba(255,255,255,0.05)"),
                borderRadius: "6px",
            });

            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "10px",
                fontSize: "11px",
            });

            const leftPart = document.createElement("div");
            Object.assign(leftPart.style, {
                display: "flex",
                alignItems: "center",
                gap: "8px",
                flex: "1 1 0",
                minWidth: "0",
            });

            const label = document.createElement("strong");
            label.textContent = `Selection ${i + 1}:`;
            label.style.color = "#fff";
            label.style.flexShrink = "0";
            leftPart.appendChild(label);

            const selectBtn = makeButton(slot ? slot.summary : "Set selection ▼", () => {
                if (!isExpanded) {
                    this.inlineTab = hasActive ? "active" : "query";
                }
                this.activeSlotExpansion = isExpanded ? null : i;
                this.scheduleRender();
            });
            selectBtn.style.flex = "1 1 auto";
            selectBtn.style.textAlign = "left";
            selectBtn.style.overflow = "hidden";
            selectBtn.style.textOverflow = "ellipsis";
            selectBtn.style.whiteSpace = "nowrap";
            selectBtn.style.fontSize = "11px";
            selectBtn.style.padding = "4px 8px";
            selectBtn.style.background = isExpanded ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.06)";
            selectBtn.style.borderColor = isExpanded ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.12)";
            selectBtn.style.color = slot ? "#34d399" : "rgba(244,244,245,0.75)";
            leftPart.appendChild(selectBtn);
            row.appendChild(leftPart);

            // Action buttons (Clear only)
            const actions = document.createElement("div");
            Object.assign(actions.style, {
                display: "flex",
                gap: "4px",
                alignItems: "center",
                flexShrink: "0",
            });

            // Clear button
            const clearBtn = makeButton("Clear", () => {
                this.stagedSlots[i] = null;
                this.scheduleRender();
            });
            clearBtn.disabled = !slot;
            clearBtn.style.opacity = clearBtn.disabled ? "0.42" : "1";
            clearBtn.style.padding = "2px 6px";
            clearBtn.style.fontSize = "10px";
            clearBtn.style.whiteSpace = "nowrap";
            clearBtn.setAttribute("data-molsysviewer-measurement-slot-clear", String(i));
            actions.appendChild(clearBtn);

            row.appendChild(actions);
            slotWrapper.appendChild(row);

            // Inline Selection Mechanism Expansion under Slot i
            if (isExpanded) {
                const mechanismInline = this.renderSelectionMechanismInline(i, requiredCount);
                slotWrapper.appendChild(mechanismInline);
            }

            slotsCard.appendChild(slotWrapper);
        }

        // Divider
        const divider = document.createElement("div");
        Object.assign(divider.style, {
            borderTop: "1px solid rgba(255,255,255,0.06)",
            marginTop: "8px",
            paddingTop: "8px",
        });
        slotsCard.appendChild(divider);

        // Name input & Create row
        const formRow = document.createElement("div");
        Object.assign(formRow.style, {
            display: "flex",
            gap: "6px",
            width: "100%",
        });

        const nameInput = document.createElement("input");
        nameInput.type = "text";
        nameInput.placeholder = "Measurement name (optional)...";
        Object.assign(nameInput.style, {
            flex: "1 1 auto",
            ...INPUT_STYLE,
        });
        nameInput.setAttribute("data-molsysviewer-measurement-name-input", "true");
        formRow.appendChild(nameInput);

        const requiredSlots = this.stagedSlots.slice(0, requiredCount);
        const canCreate = this.settings.systemLoaded && requiredSlots.every(slot => slot !== null);

        const createButton = makeButton("Create", () => {
            const picks = requiredSlots.map(slot => slot!.atom_indices);
            const endpoint_policy = requiredSlots[0]?.policy;
            const details: Record<string, any> = {
                kind: this.selectedSavedKind,
                picks,
                endpoint_policy,
            };
            const tag = (nameInput.value || "").trim();
            if (tag) {
                details.tag = tag;
            }
            this.ctx.onAction("create_measurement", details);
            nameInput.value = "";
            this.stagedSlots = [null, null, null, null];
            this.activeSlotExpansion = null;
            this.scheduleRender();
        });
        createButton.disabled = !canCreate;
        createButton.style.opacity = createButton.disabled ? "0.42" : "1";
        Object.assign(createButton.style, {
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
        createButton.setAttribute("data-molsysviewer-measurement-create-kind", this.selectedSavedKind);
        formRow.appendChild(createButton);

        slotsCard.appendChild(formRow);
        parent.appendChild(slotsCard);
    }

    private renderSelectionMechanismInline(slotIndex: number, requiredCount: number): HTMLDivElement {
        const container = document.createElement("div");
        Object.assign(container.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginTop: "6px",
            padding: "8px",
            borderRadius: "6px",
            background: "rgba(0, 0, 0, 0.2)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
        });

        const count = this.selection.atom_indices.length;
        const hasActive = count > 0;

        const activeTab = this.inlineTab;

        // Segmented Mini-Dock Header
        const tabRow = document.createElement("div");
        Object.assign(tabRow.style, {
            display: "flex",
            gap: "4px",
            padding: "2px",
            borderRadius: "5px",
        });

        const tabs = [
            { id: "active" as const, label: "Active selection" },
            { id: "query" as const, label: "Select by query" },
            { id: "saved" as const, label: "Saved selections" },
        ];

        for (const tab of tabs) {
            const isTabActive = activeTab === tab.id;
            const tabBtn = makePurplishSegmentButton(
                tab.label,
                isTabActive,
                () => {
                    this.inlineTab = tab.id;
                    this.scheduleRender();
                },
                "4px 0",
                "10px"
            );
            tabRow.appendChild(tabBtn);
        }
        container.appendChild(tabRow);

        // Tab Content Area
        const contentBox = document.createElement("div");
        Object.assign(contentBox.style, { marginTop: "4px" });

        // 1. Active Selection Card
        const activeCard = document.createElement("div");
        activeCard.setAttribute("data-molsysviewer-measurement-active-selection-card", "true");
        if (activeTab === "active") {
            Object.assign(activeCard.style, {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "6px",
                padding: "4px 2px",
            });

            const leftWrap = document.createElement("div");
            Object.assign(leftWrap.style, {
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "11px",
                fontWeight: "600",
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
            leftWrap.appendChild(document.createTextNode(hasActive ? `${count} atom${count === 1 ? "" : "s"} selected` : "No active selection"));
            activeCard.appendChild(leftWrap);

            const useBtn = document.createElement("button");
            useBtn.type = "button";
            useBtn.textContent = "Set";
            useBtn.setAttribute("data-molsysviewer-measurement-slot-set", String(slotIndex));
            useBtn.disabled = !hasActive;

            const greenNormal = "#34d399";
            const greenHover = "#10b981";

            Object.assign(useBtn.style, {
                flex: "0 0 auto",
                padding: "4px 12px",
                fontSize: "11px",
                fontWeight: "700",
                background: greenNormal,
                border: "0",
                borderRadius: "6px",
                color: "#000000",
                cursor: hasActive ? "pointer" : "default",
                opacity: hasActive ? "1" : "0.42",
                transition: "all 0.12s ease",
            });

            useBtn.addEventListener("mouseenter", () => {
                if (hasActive) {
                    useBtn.style.background = greenHover;
                }
            });
            useBtn.addEventListener("mouseleave", () => {
                if (hasActive) {
                    useBtn.style.background = greenNormal;
                }
            });
            useBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!hasActive) return;
                const endpointType = count === 1 ? "Atom" : "Centroid";
                this.stagedSlots[slotIndex] = {
                    atom_indices: [...this.selection.atom_indices],
                    summary: `${count} atom${count === 1 ? "" : "s"} · ${endpointType}`,
                    endpointType,
                    policy: "centroid",
                };
                this.activeSlotExpansion = null;
                this.scheduleRender();
            });
            activeCard.appendChild(useBtn);
        } else {
            activeCard.style.display = "none";
        }

        const deselectBtn = makeButton("Deactivate", () => {
            this.ctx.onAction("set_active_selection_operation", { operation: "none" });
            this.scheduleRender();
        });
        deselectBtn.disabled = !hasActive;
        deselectBtn.style.display = "none"; // Kept for data attribute test selector
        deselectBtn.setAttribute("data-molsysviewer-measurement-active-deselect", "true");
        activeCard.appendChild(deselectBtn);
        contentBox.appendChild(activeCard);

        // 2. Select by Query Card
        const queryCard = document.createElement("div");
        queryCard.setAttribute("data-molsysviewer-measurement-query-card", "true");
        if (activeTab === "query") {
            Object.assign(queryCard.style, { display: "flex", flexDirection: "column", gap: "6px" });

            const composer = this.getMeasuresQueryComposer();
            queryCard.appendChild(composer.element());

            const presetRow = document.createElement("div");
            presetRow.setAttribute("data-molsysviewer-measurement-query-presets", "true");
            Object.assign(presetRow.style, { display: "flex", flexWrap: "wrap", gap: "4px", alignItems: "center" });

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
                chip.setAttribute("data-molsysviewer-measurement-query-preset", preset.label);
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
        } else {
            queryCard.style.display = "none";
        }
        contentBox.appendChild(queryCard);

        // 3. Saved Selection Card
        const savedCard = document.createElement("div");
        savedCard.setAttribute("data-molsysviewer-measurement-activate-saved-card", "true");
        if (activeTab === "saved") {
            Object.assign(savedCard.style, { display: "flex", flexDirection: "column", gap: "4px" });

            const savedOptions = [
                { value: "", label: "Select saved selection to use..." },
                ...this.savedSelections.map(s => ({ value: s.tag, label: `${s.tag} (${s.atom_count} atoms)` })),
            ];
            const savedSelect = makeStyledSelect(
                savedOptions,
                "",
                (val) => {
                    if (val) {
                        const found = this.savedSelections.find(s => s.tag === val);
                        if (found && found.atom_indices) {
                            const countAtoms = found.atom_indices.length;
                            const endpointType = countAtoms === 1 ? "Atom" : "Centroid";
                            this.stagedSlots[slotIndex] = {
                                atom_indices: [...found.atom_indices],
                                summary: `${found.tag} (${countAtoms} atoms) · ${endpointType}`,
                                endpointType,
                                policy: "centroid",
                            };
                            this.ctx.onAction("activate_selection", { tag: val });
                            this.activeSlotExpansion = null;
                            this.scheduleRender();
                        }
                    }
                }
            );
            savedCard.appendChild(savedSelect);
        } else {
            savedCard.style.display = "none";
        }
        contentBox.appendChild(savedCard);

        container.appendChild(contentBox);
        return container;
    }

    private renderMeasurement(item: MeasurementSummary): HTMLDivElement {
        const row = card();
        row.setAttribute("data-molsysviewer-measurement-tag", item.tag);
        row.setAttribute("data-molsysviewer-measurement-broken", String(item.broken));
        row.style.opacity = item.hidden ? "0.42" : "1";
        if (item.brokenReason) row.title = item.brokenReason;

        const head = document.createElement("div");
        Object.assign(head.style, { display: "flex", alignItems: "center", gap: "8px" });
        const value = document.createElement("div");
        value.textContent = formatValue(item);
        value.setAttribute("data-molsysviewer-measurement-value", item.tag);
        Object.assign(value.style, {
            flex: "1 1 0", fontSize: "18px", fontWeight: "700",
            color: item.broken ? "rgba(244,244,245,0.46)" : "#f4f4f5",
        });
        head.appendChild(value);
        const eye = makeButton(item.hidden ? "⦻" : "👁", () =>
            this.ctx.onAction("toggle_measurement_visibility", { tag: item.tag }));
        eye.setAttribute("data-molsysviewer-measurement-visibility", item.tag);
        const focus = makeButton("Focus", () => this.ctx.onAction("focus_measurement", { tag: item.tag }));
        focus.setAttribute("data-molsysviewer-measurement-focus", item.tag);

        for (const button of [eye, focus]) {
            button.style.flex = "0 0 auto";
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            head.appendChild(button);
        }

        const edit = makeButton("Edit", () => {
            this.editTag = this.editTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        edit.setAttribute("data-molsysviewer-measurement-more", item.tag);
        edit.setAttribute("data-molsysviewer-measurement-edit-toggle", item.tag);
        edit.style.padding = "3px 6px";
        edit.style.fontSize = "10px";
        head.appendChild(edit);

        const destroy = makeButton("🗑", () => this.ctx.onAction("delete_measurement", { tag: item.tag }));
        destroy.setAttribute("data-molsysviewer-measurement-delete", item.tag);
        destroy.style.padding = "3px 6px";
        destroy.style.fontSize = "10px";
        head.appendChild(destroy);

        row.appendChild(head);

        if (this.editTag === item.tag) {
            const editor = document.createElement("div");
            Object.assign(editor.style, { display: "flex", flexDirection: "column", gap: "6px", marginTop: "6px", padding: "6px", background: "rgba(0,0,0,0.15)", borderRadius: "4px" });

            const renameRow = document.createElement("div");
            Object.assign(renameRow.style, { display: "flex", gap: "6px" });
            const renameInput = document.createElement("input");
            renameInput.type = "text";
            renameInput.placeholder = "New name";
            renameInput.value = item.tag;
            renameInput.setAttribute("data-molsysviewer-measurement-rename-input", item.tag);
            this.styleControl(renameInput);
            renameInput.style.flex = "1 1 auto";

            const renameBtn = makeButton("Rename", () => {
                const newTag = renameInput.value.trim();
                if (newTag && newTag !== item.tag) {
                    this.ctx.onAction("rename_measurement", { tag: item.tag, new_tag: newTag });
                }
            });
            renameBtn.setAttribute("data-molsysviewer-measurement-rename", item.tag);
            renameRow.appendChild(renameInput);
            renameRow.appendChild(renameBtn);
            editor.appendChild(renameRow);

            const layerRow = document.createElement("div");
            Object.assign(layerRow.style, { display: "flex", gap: "6px" });
            const layerInput = document.createElement("input");
            layerInput.type = "text";
            layerInput.placeholder = "Layer name";
            layerInput.value = item.layerTag || "";
            layerInput.setAttribute("data-molsysviewer-measurement-layer-input", item.tag);
            this.styleControl(layerInput);
            layerInput.style.flex = "1 1 auto";

            const layerBtn = makeButton("Set layer", () => {
                const layer = layerInput.value.trim();
                this.ctx.onAction("set_measurement_layer", { tag: item.tag, layer });
            });
            layerBtn.setAttribute("data-molsysviewer-measurement-layer", item.tag);
            layerRow.appendChild(layerInput);
            layerRow.appendChild(layerBtn);
            editor.appendChild(layerRow);

            row.appendChild(editor);
        }

        const sub = document.createElement("div");
        Object.assign(sub.style, { display: "flex", justifyContent: "space-between", fontSize: "10px", color: "rgba(244,244,245,0.52)" });
        const summaryText = `${item.kind} · ${item.picks} pick${item.picks === 1 ? "" : "s"}${item.owner ? ` · from ${item.owner}` : ""}`;
        sub.appendChild(document.createTextNode(summaryText));
        row.appendChild(sub);

        if (item.endpointLabels.length > 0) {
            const endpoints = document.createElement("div");
            endpoints.setAttribute("data-molsysviewer-measurement-endpoints", item.tag);
            Object.assign(endpoints.style, { fontSize: "10px", color: "rgba(244,244,245,0.72)" });
            endpoints.textContent = item.endpointLabels.join(" → ");
            row.appendChild(endpoints);
        }

        // Series / Sparkline Expansion
        const seriesData = this.seriesByTag.get(item.tag);
        const isSeriesExpanded = this.expandedSeries.has(item.tag);

        const seriesRow = document.createElement("div");
        Object.assign(seriesRow.style, { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" });

        const seriesToggleBtn = makeButton(isSeriesExpanded ? "Hide Series" : "Show Trajectory Series", () => {
            if (isSeriesExpanded) {
                this.expandedSeries.delete(item.tag);
            } else {
                this.expandedSeries.add(item.tag);
                const reqId = this.nextSeriesRequest++;
                this.expectedSeriesRequest.set(item.tag, reqId);
                this.ctx.onAction("request_measurement_series", { tag: item.tag, request_id: reqId });
            }
            this.scheduleRender();
        });
        seriesToggleBtn.setAttribute("data-molsysviewer-measurement-series-toggle", item.tag);
        seriesToggleBtn.style.padding = "2px 6px";
        seriesToggleBtn.style.fontSize = "10px";
        seriesRow.appendChild(seriesToggleBtn);

        row.appendChild(seriesRow);

        if (isSeriesExpanded && seriesData) {
            const sparklineBox = document.createElement("div");
            sparklineBox.setAttribute("data-molsysviewer-measurement-series", item.tag);
            Object.assign(sparklineBox.style, {
                display: "flex", flexDirection: "column", gap: "4px", padding: "6px",
                borderRadius: "4px", background: "rgba(0,0,0,0.2)", marginTop: "4px",
            });
            const sparkText = document.createElement("div");
            sparkText.style.fontSize = "10px";
            sparkText.style.color = "rgba(244,244,245,0.7)";
            sparkText.textContent = `Trajectory (${seriesData.nFrames} frames): avg ${seriesData.sparkline.length > 0 ? (seriesData.sparkline.reduce((a, b) => a + b, 0) / seriesData.sparkline.length).toFixed(2) : "—"} ${formatUnitLabel(seriesData.unit)}`;
            sparklineBox.appendChild(sparkText);
            row.appendChild(sparklineBox);
        }

        return row;
    }

    private styleControl(control: HTMLInputElement | HTMLSelectElement): void {
        Object.assign(control.style, {
            minWidth: "0", background: "rgba(0,0,0,0.28)", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px", padding: "5px 7px", color: "#f4f4f5", fontSize: "11px", outline: "none",
        });
    }
}
