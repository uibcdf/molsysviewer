import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { formatUnitLabel, makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";
import { ManualQueryComposer } from "../query-composer";

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


    private selectedSavedKind: "distance" | "angle" | "dihedral" = "distance";
    private stagedSlots: ({
        atom_indices: number[];
        summary: string;
        endpointType: string;
        policy: string;
    } | null)[] = [null, null, null, null];

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
            const btn = makeButton(kind[0].toUpperCase() + kind.slice(1), () => {
                this.selectedSavedKind = kind;
                this.stagedSlots = [null, null, null, null];
                this.scheduleRender();
            });
            Object.assign(btn.style, {
                flex: "1 1 0",
                padding: "6px 0",
                fontSize: "11px",
                fontWeight: "600",
                textAlign: "center",
                background: isActive ? "#6366f1" : "rgba(255,255,255,0.06)",
                border: "1px solid " + (isActive ? "#6366f1" : "rgba(255,255,255,0.12)"),
                color: isActive ? "#fff" : "#f4f4f5",
            });
            btn.setAttribute("data-molsysviewer-measurement-mode-btn", kind);
            modeRow.appendChild(btn);
        }
        parent.appendChild(modeRow);

        const requiredCount = this.selectedSavedKind === "distance" ? 2 : this.selectedSavedKind === "angle" ? 3 : 4;

        // 1. Staged Slots Card (holds Selection rows and Creation Form)
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
            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "10px",
                padding: "6px 8px",
                background: "rgba(0,0,0,0.15)",
                borderRadius: "6px",
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

            const summary = document.createElement("span");
            Object.assign(summary.style, {
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                color: slot ? "rgba(244,244,245,0.85)" : "rgba(244,244,245,0.4)",
            });
            summary.textContent = slot ? slot.summary : "Empty";
            leftPart.appendChild(summary);
            row.appendChild(leftPart);

            // Action buttons (Set active selection and Clear)
            const actions = document.createElement("div");
            Object.assign(actions.style, {
                display: "flex",
                gap: "4px",
                alignItems: "center",
                flexShrink: "0",
            });

            // Set button
            const setBtn = makeButton("Set active selection", () => {
                const activeCount = this.selection.atom_indices.length;
                if (activeCount === 0) return;

                const endpointType = activeCount === 1 ? "Atom" : "Centroid";
                const summaryText = `${activeCount} atom${activeCount === 1 ? "" : "s"} · ${endpointType}`;

                this.stagedSlots[i] = {
                    atom_indices: [...this.selection.atom_indices],
                    summary: summaryText,
                    endpointType,
                    policy: "centroid",
                };
                this.scheduleRender();
            });
            setBtn.disabled = !hasActive;
            setBtn.style.opacity = setBtn.disabled ? "0.42" : "1";
            setBtn.style.padding = "2px 6px";
            setBtn.style.fontSize = "10px";
            setBtn.style.whiteSpace = "nowrap";
            setBtn.setAttribute("data-molsysviewer-measurement-slot-set", String(i));
            actions.appendChild(setBtn);

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
            slotsCard.appendChild(row);
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
            this.stagedSlots = [null, null, null, null]; // Clear slots after creation
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

        // 2. Active Selection Card
        const activeCard = document.createElement("div");
        activeCard.setAttribute("data-molsysviewer-measurement-active-selection-card", "true");
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
            countText.textContent = `${count} atom${count === 1 ? "" : "s"}`;
        } else {
            countText.textContent = "No selection";
        }
        activeRow.appendChild(countText);

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
            this.scheduleRender();
        });
        deselectBtn.disabled = !hasActive;
        deselectBtn.style.opacity = hasActive ? "1" : "0.42";
        deselectBtn.style.padding = "4px 8px";
        deselectBtn.style.fontSize = "11px";
        deselectBtn.style.whiteSpace = "nowrap";
        deselectBtn.setAttribute("data-molsysviewer-measurement-active-deselect", "true");
        btnRow.appendChild(deselectBtn);
        activeRow.appendChild(btnRow);

        activeCard.appendChild(activeRow);
        parent.appendChild(activeCard);

        // 3. Select by Query Card
        const queryCard = document.createElement("div");
        queryCard.setAttribute("data-molsysviewer-measurement-query-card", "true");
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

        const composer = this.getMeasuresQueryComposer();
        queryCard.appendChild(composer.element());

        // Shortcuts Row
        const presetRow = document.createElement("div");
        presetRow.setAttribute("data-molsysviewer-measurement-query-presets", "true");
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

        // Query Cheat Sheet
        if (this.measuresCheatSheetOpen) {
            const cheatSheet = document.createElement("div");
            cheatSheet.setAttribute("data-molsysviewer-measurement-cheatsheet", "true");
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
                row.setAttribute("data-molsysviewer-measurement-cheatsheet-example", label);
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
        savedCard.setAttribute("data-molsysviewer-measurement-activate-saved-card", "true");
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
            this.ctx.onAction("toggle_measurement_visibility", { tag: item.tag })
        );
        eye.title = item.hidden ? "Show measurement" : "Hide measurement";
        eye.setAttribute("data-molsysviewer-measurement-visibility", item.tag);
        const more = makeButton("⋯", () => { this.editTag = this.editTag === item.tag ? null : item.tag; this.scheduleRender(); });
        more.title = "Rename or move to layer";
        more.setAttribute("data-molsysviewer-measurement-more", item.tag);
        const remove = makeButton("×", () => this.ctx.onAction("delete_measurement", { tag: item.tag }));
        remove.title = "Delete measurement";
        remove.setAttribute("data-molsysviewer-measurement-delete", item.tag);
        for (const button of [eye, more, remove]) { button.style.flex = "0 0 auto"; head.appendChild(button); }
        row.appendChild(head);

        const identity = document.createElement("div");
        identity.textContent = `${item.kind} · ${item.tag}${item.layerTag && item.layerTag !== item.tag ? ` · layer: ${item.layerTag}` : ""}${item.owner ? ` · from ${item.owner}` : ""}`;
        Object.assign(identity.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        row.appendChild(identity);
        const endpoints = document.createElement("div");
        endpoints.textContent = item.endpointLabels.length ? item.endpointLabels.join(" → ") : `${item.picks} picks`;
        endpoints.setAttribute("data-molsysviewer-measurement-endpoints", item.tag);
        Object.assign(endpoints.style, { fontSize: "11px", color: "rgba(244,244,245,0.78)" });
        row.appendChild(endpoints);

        if (!item.broken) row.appendChild(this.renderSeries(item));
        if (this.editTag === item.tag) row.appendChild(this.renderEdit(item));
        return row;
    }

    private renderSeries(item: MeasurementSummary): HTMLElement {
        if (!this.expandedSeries.has(item.tag)) {
            const button = makeButton("Show trajectory", () => {
                this.expandedSeries.add(item.tag);
                const requestId = this.nextSeriesRequest++;
                this.expectedSeriesRequest.set(item.tag, requestId);
                this.ctx.onAction("request_measurement_series", { tag: item.tag, request_id: requestId });
                this.scheduleRender();
            });
            button.setAttribute("data-molsysviewer-measurement-series-toggle", item.tag);
            return button;
        }
        const payload = this.seriesByTag.get(item.tag);
        if (!payload) {
            const pending = document.createElement("div");
            pending.textContent = "Loading trajectory…";
            pending.setAttribute("data-molsysviewer-measurement-series-pending", item.tag);
            Object.assign(pending.style, { fontSize: "10px", color: "rgba(244,244,245,0.52)" });
            return pending;
        }
        const wrap = document.createElement("div");
        wrap.setAttribute("data-molsysviewer-measurement-series", item.tag);
        const canvas = document.createElement("canvas");
        canvas.width = 260;
        canvas.height = 38;
        Object.assign(canvas.style, { width: "100%", height: "38px" });
        wrap.appendChild(canvas);
        const context = canvas.getContext?.("2d");
        const values = payload.sparkline;
        if (context && values.length > 1) {
            const min = Math.min(...values);
            const span = Math.max(1e-12, Math.max(...values) - min);

            // 1. Draw gradient area fill
            const fill = context.createLinearGradient(0, 0, 0, canvas.height);
            fill.addColorStop(0, "rgba(96, 165, 250, 0.22)");
            fill.addColorStop(1, "rgba(96, 165, 250, 0)");
            context.fillStyle = fill;
            context.beginPath();
            context.moveTo(0, canvas.height);
            values.forEach((point, index) => {
                const x = index * (canvas.width - 1) / (values.length - 1);
                const y = canvas.height - 3 - (point - min) * (canvas.height - 6) / span;
                context.lineTo(x, y);
            });
            context.lineTo(canvas.width, canvas.height);
            context.closePath();
            context.fill();

            // 2. Stroke sparkline path
            context.strokeStyle = "#60a5fa";
            context.lineWidth = 1.5;
            context.beginPath();
            values.forEach((point, index) => {
                const x = index * (canvas.width - 1) / (values.length - 1);
                const y = canvas.height - 3 - (point - min) * (canvas.height - 6) / span;
                if (index === 0) context.moveTo(x, y); else context.lineTo(x, y);
            });
            context.stroke();

            // 3. Current frame marker
            if (payload.sparklineIndices.length === values.length) {
                const currentFrame = Math.max(0, Math.min(payload.nFrames - 1, this.settings.structureIndex));
                const markerIndex = payload.sparklineIndices.reduce((best, frame, index) =>
                    Math.abs(frame - currentFrame) < Math.abs(payload.sparklineIndices[best] - currentFrame) ? index : best
                , 0);
                const markerX = markerIndex * (canvas.width - 1) / (values.length - 1);
                context.strokeStyle = "rgba(244,244,245,0.72)";
                context.lineWidth = 1;
                context.beginPath();
                context.moveTo(markerX, 1);
                context.lineTo(markerX, canvas.height - 1);
                context.stroke();
            }
        }
        const caption = document.createElement("div");
        const frame = payload.nFrames > 0
            ? Math.max(0, Math.min(payload.nFrames - 1, this.settings.structureIndex)) + 1
            : 0;
        caption.textContent = `${payload.nFrames} frame${payload.nFrames === 1 ? "" : "s"} · current ${frame}`;
        caption.setAttribute("data-molsysviewer-measurement-series-caption", item.tag);
        Object.assign(caption.style, { fontSize: "9px", color: "rgba(244,244,245,0.46)" });
        wrap.appendChild(caption);
        return wrap;
    }

    private renderEdit(item: MeasurementSummary): HTMLDivElement {
        const editor = document.createElement("div");
        Object.assign(editor.style, { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px", marginTop: "6px" });

        const rename = document.createElement("input");
        rename.value = item.tag;
        rename.setAttribute("data-molsysviewer-measurement-rename-input", item.tag);
        Object.assign(rename.style, INPUT_STYLE);

        const renameButton = makeButton("Rename", () => this.ctx.onAction("rename_measurement", { tag: item.tag, new_tag: rename.value }));
        renameButton.setAttribute("data-molsysviewer-measurement-rename", item.tag);
        rename.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                renameButton.click();
            }
        });

        const layer = document.createElement("input");
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "No user layer";
        layer.setAttribute("data-molsysviewer-measurement-layer-input", item.tag);
        Object.assign(layer.style, INPUT_STYLE);

        const layerButton = makeButton("Set layer", () => this.ctx.onAction("set_measurement_layer", { tag: item.tag, layer: layer.value || null }));
        layerButton.setAttribute("data-molsysviewer-measurement-layer", item.tag);
        layer.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                layerButton.click();
            }
        });

        editor.appendChild(rename);
        editor.appendChild(renameButton);
        editor.appendChild(layer);
        editor.appendChild(layerButton);
        return editor;
    }
}
