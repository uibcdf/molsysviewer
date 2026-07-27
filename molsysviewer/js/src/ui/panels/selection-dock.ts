import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary } from "../group-panel";
import type { ManualQueryComposer } from "../query-composer";
import { makePurplishSegmentButton } from "./measures-panel";
import { makeStyledSelect } from "./ui-helpers";

export interface SelectionDockOptions {
    activeSelection: ActiveSelectionPayload;
    savedSelections: SavedSelectionSummary[];
    activeTab: "active" | "query" | "saved";
    buttonLabel?: string;
    queryComposer: ManualQueryComposer;
    onTabChange: (tab: "active" | "query" | "saved") => void;
    onCommitSelection: (atomIndices: number[]) => void;
    onActivateSavedSelection?: (item: SavedSelectionSummary) => void;
    dataAttributePrefix?: string;
}

export function renderSelectionDock(options: SelectionDockOptions): HTMLDivElement {
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

    const count = options.activeSelection.atom_indices.length;
    const hasActive = count > 0;
    const btnLabel = options.buttonLabel || "Set";
    const prefix = options.dataAttributePrefix || "selection-dock";

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
        const isTabActive = options.activeTab === tab.id;
        const tabBtn = makePurplishSegmentButton(
            tab.label,
            isTabActive,
            () => {
                options.onTabChange(tab.id);
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
    activeCard.setAttribute(`data-molsysviewer-${prefix}-active-selection-card`, "true");
    if (options.activeTab === "active") {
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
        useBtn.textContent = btnLabel;
        useBtn.setAttribute(`data-molsysviewer-${prefix}-slot-set`, "0");
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
            options.onCommitSelection([...options.activeSelection.atom_indices]);
        });
        activeCard.appendChild(useBtn);
        contentBox.appendChild(activeCard);
    }

    // 2. Select by Query Card
    const queryCard = document.createElement("div");
    queryCard.setAttribute(`data-molsysviewer-${prefix}-query-card`, "true");
    if (options.activeTab === "query") {
        Object.assign(queryCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "2px 0",
        });
        queryCard.appendChild(options.queryComposer.element());

        // Preset shortcuts row
        const presetRow = document.createElement("div");
        presetRow.setAttribute(`data-molsysviewer-${prefix}-query-presets`, "true");
        Object.assign(presetRow.style, {
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
            alignItems: "center",
            marginTop: "2px",
        });

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
            chip.setAttribute(`data-molsysviewer-${prefix}-query-preset`, preset.label);
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
                options.queryComposer.setExpression(preset.expression, "MolSysMT");
            });
            presetRow.appendChild(chip);
        }
        queryCard.appendChild(presetRow);
        contentBox.appendChild(queryCard);
    }

    // 3. Saved Selections Card
    const savedCard = document.createElement("div");
    savedCard.setAttribute(`data-molsysviewer-${prefix}-saved-selection-card`, "true");
    if (options.activeTab === "saved") {
        Object.assign(savedCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "2px 0",
        });

        if (options.savedSelections.length === 0) {
            const noSaved = document.createElement("div");
            noSaved.textContent = "No saved selections available.";
            Object.assign(noSaved.style, { fontSize: "11px", color: "rgba(244,244,245,0.5)" });
            savedCard.appendChild(noSaved);
        } else {
            const savedOptions = [
                { value: "", label: "Select saved selection to use..." },
                ...options.savedSelections.map(s => ({
                    value: s.tag,
                    label: `${s.tag} (${s.atom_count} atoms)`,
                })),
            ];

            const savedSelect = makeStyledSelect(savedOptions, "", (tag) => {
                if (!tag) return;
                const found = options.savedSelections.find(s => s.tag === tag);
                if (found) {
                    if (options.onActivateSavedSelection) {
                        options.onActivateSavedSelection(found);
                    }
                    options.onCommitSelection([...found.atom_indices]);
                }
            });

            savedSelect.setAttribute(`data-molsysviewer-${prefix}-saved-select`, "true");
            Object.assign(savedSelect.style, {
                width: "100%",
                padding: "5px 8px",
                fontSize: "11px",
            });
            savedCard.appendChild(savedSelect);
        }
        contentBox.appendChild(savedCard);
    }

    container.appendChild(contentBox);
    return container;
}
