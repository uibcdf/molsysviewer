import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { formatUnitLabel, makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";

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

    // Creation tabs
    private activeCreateTab: "active" | "saved" = "active";
    private endpointSettingsExpanded = false;

    // Saved selections creation parameters
    private selectedSavedKind: "distance" | "angle" | "dihedral" = "distance";
    private selectedSavedEndpoints: string[] = ["", "", "", ""];

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

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // 1. Title and visible summary header (unified like Regions)
        this.host.appendChild(makeSectionHeader("Measures"));
        this.host.appendChild(this.renderHeaderSummaryRow());

        // 2. Creation and settings card
        this.host.appendChild(this.renderCreateCard());

        // 3. Measurements list
        this.host.appendChild(makeSectionHeader("Measurements"));
        const list = document.createElement("div");
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

    private renderHeaderSummaryRow(): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "8px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.6)",
        });

        const visibleCount = this.measurements.filter(m => !m.hidden).length;
        const totalCount = this.measurements.length;
        const summaryText = document.createElement("span");
        summaryText.textContent = `${visibleCount} of ${totalCount} measurement${totalCount === 1 ? "" : "s"} visible`;
        row.appendChild(summaryText);

        const actions = document.createElement("div");
        Object.assign(actions.style, { display: "flex", gap: "6px" });
        for (const [label, action] of [
            ["Show all", "show_all_measurements"],
            ["Hide all", "hide_all_measurements"],
            ["Clear all", "clear_measurements"],
        ] as const) {
            const button = makeButton(label, () => {
                if (action === "clear_measurements" && !window.confirm("Delete all measurements?")) return;
                this.ctx.onAction(action);
            });
            button.setAttribute("data-molsysviewer-measurement-global", action);
            actions.appendChild(button);
        }
        row.appendChild(actions);
        return row;
    }

    private renderCreateCard(): HTMLDivElement {
        const container = card();
        container.setAttribute("data-molsysviewer-measurement-create-card", "true");

        // Tab selection headers
        const tabHeader = document.createElement("div");
        Object.assign(tabHeader.style, {
            display: "flex",
            gap: "8px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            paddingBottom: "6px",
            marginBottom: "8px",
        });

        const activeTab = document.createElement("div");
        activeTab.textContent = "Active Selection";
        Object.assign(activeTab.style, {
            fontSize: "11px",
            fontWeight: "700",
            cursor: "pointer",
            color: this.activeCreateTab === "active" ? "#6366f1" : "rgba(244,244,245,0.6)",
            borderBottom: this.activeCreateTab === "active" ? "2px solid #6366f1" : "none",
            paddingBottom: "4px",
        });
        activeTab.addEventListener("click", () => {
            this.activeCreateTab = "active";
            this.scheduleRender();
        });

        const savedTab = document.createElement("div");
        savedTab.textContent = "Saved Selections";
        Object.assign(savedTab.style, {
            fontSize: "11px",
            fontWeight: "700",
            cursor: "pointer",
            color: this.activeCreateTab === "saved" ? "#6366f1" : "rgba(244,244,245,0.6)",
            borderBottom: this.activeCreateTab === "saved" ? "2px solid #6366f1" : "none",
            paddingBottom: "4px",
        });
        savedTab.addEventListener("click", () => {
            this.activeCreateTab = "saved";
            this.scheduleRender();
        });

        tabHeader.appendChild(activeTab);
        tabHeader.appendChild(savedTab);
        container.appendChild(tabHeader);

        // Body depends on selected tab
        if (this.activeCreateTab === "active") {
            container.appendChild(this.renderActiveCreateBody());
        } else {
            container.appendChild(this.renderSavedCreateBody());
        }

        // Divider
        const divider = document.createElement("div");
        Object.assign(divider.style, {
            borderTop: "1px solid rgba(255,255,255,0.08)",
            margin: "8px 0 4px 0",
        });
        container.appendChild(divider);

        // Collapsible Endpoint settings
        const settingsToggle = document.createElement("div");
        settingsToggle.textContent = this.endpointSettingsExpanded ? "▼ Hide Endpoint Settings" : "▶ Show Endpoint Settings";
        Object.assign(settingsToggle.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.6)",
            cursor: "pointer",
            fontWeight: "600",
            padding: "4px 0",
            userSelect: "none",
        });
        settingsToggle.addEventListener("click", () => {
            this.endpointSettingsExpanded = !this.endpointSettingsExpanded;
            this.scheduleRender();
        });
        container.appendChild(settingsToggle);

        if (this.endpointSettingsExpanded) {
            container.appendChild(this.renderEndpointSettings());
        }

        return container;
    }

    private renderActiveCreateBody(): HTMLDivElement {
        const body = document.createElement("div");
        Object.assign(body.style, { display: "flex", flexDirection: "column", gap: "6px" });

        const count = this.selection.group_indices.length || this.selection.count_groups;
        const title = document.createElement("strong");
        title.textContent = `From active selection (${count} endpoint${count === 1 ? "" : "s"})`;
        Object.assign(title.style, { fontSize: "11px", color: "rgba(244,244,245,0.85)" });
        body.appendChild(title);

        const row = document.createElement("div");
        Object.assign(row.style, { display: "flex", gap: "6px" });
        for (const [kind, required] of [["distance", 2], ["angle", 3], ["dihedral", 4]] as const) {
            const button = makeButton(kind[0].toUpperCase() + kind.slice(1), () =>
                this.ctx.onAction("create_measurement", { kind })
            );
            button.disabled = !this.settings.systemLoaded || count !== required;
            button.style.opacity = button.disabled ? "0.42" : "1";
            button.setAttribute("data-molsysviewer-measurement-create-kind", kind);
            row.appendChild(button);
        }
        body.appendChild(row);

        const hint = document.createElement("div");
        hint.textContent = !this.settings.systemLoaded
            ? "Load a structure first."
            : count >= 2 && count <= 4
                ? `${count} endpoints can create a ${count === 2 ? "distance" : count === 3 ? "angle" : "dihedral"}.`
                : `Distance needs 2, angle 3, and dihedral 4 endpoints; you have ${count}.`;
        Object.assign(hint.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        body.appendChild(hint);

        return body;
    }

    private renderSavedCreateBody(): HTMLDivElement {
        const body = document.createElement("div");
        Object.assign(body.style, { display: "flex", flexDirection: "column", gap: "6px" });

        // Kind selector
        const kindRow = document.createElement("div");
        Object.assign(kindRow.style, {
            display: "grid",
            gridTemplateColumns: "100px 1fr",
            alignItems: "center",
            gap: "8px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.85)",
        });
        const kindLabel = document.createElement("span");
        kindLabel.textContent = "Measurement kind:";
        kindRow.appendChild(kindLabel);

        const kindSelect = makeStyledSelect(
            [
                { value: "distance", label: "Distance (2 endpoints)" },
                { value: "angle", label: "Angle (3 endpoints)" },
                { value: "dihedral", label: "Dihedral (4 endpoints)" },
            ],
            this.selectedSavedKind,
            (val) => {
                this.selectedSavedKind = val as any;
                this.scheduleRender();
            }
        );
        kindRow.appendChild(kindSelect);
        body.appendChild(kindRow);

        // Render endpoints selectors
        const requiredCount = this.selectedSavedKind === "distance" ? 2 : this.selectedSavedKind === "angle" ? 3 : 4;
        const savedOptions = [
            { value: "", label: "Select..." },
            ...this.savedSelections.map(s => ({ value: s.tag, label: `${s.tag} (${s.atom_count} atoms)` })),
        ];

        for (let i = 0; i < requiredCount; i++) {
            const epRow = document.createElement("div");
            Object.assign(epRow.style, {
                display: "grid",
                gridTemplateColumns: "100px 1fr",
                alignItems: "center",
                gap: "8px",
                fontSize: "11px",
                color: "rgba(244,244,245,0.85)",
            });
            const epLabel = document.createElement("span");
            epLabel.textContent = `Endpoint ${i + 1}:`;
            epRow.appendChild(epLabel);

            const epSelect = makeStyledSelect(
                savedOptions,
                this.selectedSavedEndpoints[i] || "",
                (val) => {
                    this.selectedSavedEndpoints[i] = val;
                    this.scheduleRender();
                }
            );
            epRow.appendChild(epSelect);
            body.appendChild(epRow);
        }

        // Create button
        const canCreate = this.settings.systemLoaded && Array.from({ length: requiredCount }).every((_, i) =>
            this.selectedSavedEndpoints[i] && this.savedSelections.some(s => s.tag === this.selectedSavedEndpoints[i])
        );

        const createButton = makeButton("Create Measurement", () => {
            const kind = this.selectedSavedKind;
            const picks = Array.from({ length: requiredCount }).map((_, i) => {
                const tag = this.selectedSavedEndpoints[i];
                const selection = this.savedSelections.find(s => s.tag === tag);
                return selection?.atom_indices ?? [];
            });
            this.ctx.onAction("create_measurement", { kind, picks });
        });
        createButton.disabled = !canCreate;
        createButton.style.opacity = createButton.disabled ? "0.42" : "1";
        Object.assign(createButton.style, { marginTop: "4px" });
        body.appendChild(createButton);

        return body;
    }

    private renderEndpointSettings(): HTMLDivElement {
        const body = document.createElement("div");
        Object.assign(body.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            marginTop: "6px",
            padding: "8px",
            background: "rgba(0,0,0,0.15)",
            borderRadius: "6px",
        });

        // 1. Radio policy selector
        const policyTitle = document.createElement("strong");
        policyTitle.textContent = "Endpoint Policy";
        Object.assign(policyTitle.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
        body.appendChild(policyTitle);

        for (const policy of ["atom", "centroid", "representative_atom"] as const) {
            const label = document.createElement("label");
            Object.assign(label.style, {
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "11px",
                color: "rgba(244,244,245,0.78)",
                cursor: "pointer",
            });
            const input = document.createElement("input");
            input.type = "radio";
            input.name = "molsysviewer-measurement-policy-create";
            input.value = policy;
            input.checked = this.settings.endpointPolicyDefault === policy;
            input.setAttribute("data-molsysviewer-measurement-policy", policy);
            input.addEventListener("change", () => this.ctx.onAction("set_measurement_endpoint_policy", { policy }));
            label.appendChild(input);
            label.appendChild(document.createTextNode(policy.replace(/_/g, " ")));
            body.appendChild(label);
        }

        // 2. Representative atoms configuration
        const reprTitle = document.createElement("strong");
        reprTitle.textContent = "Representative Atoms";
        Object.assign(reprTitle.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)", marginTop: "4px" });
        body.appendChild(reprTitle);

        for (const target of ["protein", "nucleic", "lipid", "other"] as const) {
            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "grid",
                gridTemplateColumns: "80px 1fr",
                alignItems: "center",
                gap: "6px",
                fontSize: "10px",
                color: "rgba(244,244,245,0.62)",
            });
            const label = document.createElement("span");
            label.textContent = target;
            row.appendChild(label);

            const input = document.createElement("input");
            input.type = "text";
            input.value = this.settings.representativeAtoms[target];
            input.disabled = this.settings.endpointPolicyDefault !== "representative_atom";
            input.setAttribute("data-molsysviewer-measurement-representative", target);
            Object.assign(input.style, {
                ...INPUT_STYLE,
                opacity: input.disabled ? "0.4" : "1",
            });
            input.addEventListener("change", () => this.ctx.onAction("set_measurement_representative_atom", { target, atom_name: input.value }));
            row.appendChild(input);
            body.appendChild(row);
        }

        const note = document.createElement("div");
        note.textContent = "The policy applies to future measurements only.";
        Object.assign(note.style, { fontSize: "9px", color: "rgba(244,244,245,0.48)", marginTop: "2px" });
        body.appendChild(note);

        return body;
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
