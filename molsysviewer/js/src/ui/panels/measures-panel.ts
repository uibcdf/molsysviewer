import type { ActiveSelectionPayload } from "../../managers/active-selection";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";

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

function card(): HTMLDivElement {
    const element = document.createElement("div");
    Object.assign(element.style, {
        display: "flex", flexDirection: "column", gap: "7px", padding: "10px",
        borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.035)",
    });
    return element;
}

function labelUnit(unit: string): string {
    if (unit === "angstrom") return "Å";
    if (unit === "degree" || unit === "degrees") return "°";
    return unit;
}

function formatValue(item: MeasurementSummary): string {
    if (item.broken || item.value === null || !Number.isFinite(item.value)) return "—";
    const digits = item.kind === "distance" ? 2 : 1;
    return `${item.value.toFixed(digits)} ${labelUnit(item.unit)}`;
}

export class MeasuresPanel extends BasePanel {
    readonly key = "measures";
    private measurements: MeasurementSummary[] = [];
    private settings = defaultSettings();
    private selection: ActiveSelectionPayload = emptySelection();
    private readonly expandedSeries = new Set<string>();
    private readonly seriesByTag = new Map<string, MeasurementSeries>();
    private readonly expectedSeriesRequest = new Map<string, number>();
    private nextSeriesRequest = 1;
    private editTag: string | null = null;

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

    updateSeries(payload: MeasurementSeries): void {
        const expected = this.expectedSeriesRequest.get(payload.tag);
        if (expected === undefined || payload.requestId !== expected) return;
        this.seriesByTag.set(payload.tag, payload);
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Measures"));
        this.host.appendChild(this.renderCreate());
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
        this.host.appendChild(this.renderGlobalActions());
        this.host.appendChild(this.renderSettings());
    }

    private endpointCount(): number {
        return this.selection.group_indices.length || this.selection.count_groups;
    }

    private renderCreate(): HTMLDivElement {
        const section = card();
        section.setAttribute("data-molsysviewer-measurement-create", "true");
        const count = this.endpointCount();
        const title = document.createElement("strong");
        title.textContent = `From active selection (${count} endpoint${count === 1 ? "" : "s"})`;
        Object.assign(title.style, { fontSize: "12px", color: "#f4f4f5" });
        section.appendChild(title);
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
        section.appendChild(row);
        const hint = document.createElement("div");
        hint.textContent = !this.settings.systemLoaded
            ? "Load a structure first."
            : count >= 2 && count <= 4
                ? `${count} endpoints can create a ${count === 2 ? "distance" : count === 3 ? "angle" : "dihedral"}.`
                : `Distance needs 2, angle 3, and dihedral 4 endpoints; you have ${count}.`;
        Object.assign(hint.style, { fontSize: "10px", color: "rgba(244,244,245,0.58)" });
        section.appendChild(hint);
        return section;
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
            context.strokeStyle = "#60a5fa";
            context.lineWidth = 1.5;
            context.beginPath();
            values.forEach((point, index) => {
                const x = index * (canvas.width - 1) / (values.length - 1);
                const y = canvas.height - 3 - (point - min) * (canvas.height - 6) / span;
                if (index === 0) context.moveTo(x, y); else context.lineTo(x, y);
            });
            context.stroke();
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
        Object.assign(editor.style, { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px" });
        const rename = document.createElement("input");
        rename.value = item.tag;
        rename.setAttribute("data-molsysviewer-measurement-rename-input", item.tag);
        const renameButton = makeButton("Rename", () => this.ctx.onAction("rename_measurement", { tag: item.tag, new_tag: rename.value }));
        renameButton.setAttribute("data-molsysviewer-measurement-rename", item.tag);
        const layer = document.createElement("input");
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "No user layer";
        layer.setAttribute("data-molsysviewer-measurement-layer-input", item.tag);
        const layerButton = makeButton("Set layer", () => this.ctx.onAction("set_measurement_layer", { tag: item.tag, layer: layer.value || null }));
        layerButton.setAttribute("data-molsysviewer-measurement-layer", item.tag);
        editor.appendChild(rename);
        editor.appendChild(renameButton);
        editor.appendChild(layer);
        editor.appendChild(layerButton);
        return editor;
    }

    private renderGlobalActions(): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "flex", gap: "6px", marginTop: "8px" });
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
            row.appendChild(button);
        }
        return row;
    }

    private renderSettings(): HTMLDivElement {
        const section = card();
        section.appendChild(makeSectionHeader("Endpoint policy"));
        for (const policy of ["atom", "centroid", "representative_atom"] as const) {
            const label = document.createElement("label");
            const input = document.createElement("input");
            input.type = "radio";
            input.name = "molsysviewer-measurement-policy";
            input.value = policy;
            input.checked = this.settings.endpointPolicyDefault === policy;
            input.setAttribute("data-molsysviewer-measurement-policy", policy);
            input.addEventListener("change", () => this.ctx.onAction("set_measurement_endpoint_policy", { policy }));
            label.appendChild(input);
            label.appendChild(document.createTextNode(` ${policy.replace(/_/g, " ")}`));
            Object.assign(label.style, { fontSize: "11px", color: "rgba(244,244,245,0.78)" });
            section.appendChild(label);
        }
        for (const target of ["protein", "nucleic", "lipid", "other"] as const) {
            const row = document.createElement("label");
            row.textContent = `${target} `;
            const input = document.createElement("input");
            input.value = this.settings.representativeAtoms[target];
            input.disabled = this.settings.endpointPolicyDefault !== "representative_atom";
            input.setAttribute("data-molsysviewer-measurement-representative", target);
            input.addEventListener("change", () => this.ctx.onAction("set_measurement_representative_atom", { target, atom_name: input.value }));
            row.appendChild(input);
            Object.assign(row.style, { fontSize: "10px", color: "rgba(244,244,245,0.62)" });
            section.appendChild(row);
        }
        const note = document.createElement("div");
        note.textContent = "The policy applies to future measurements only.";
        Object.assign(note.style, { fontSize: "9px", color: "rgba(244,244,245,0.48)" });
        section.appendChild(note);
        return section;
    }
}
