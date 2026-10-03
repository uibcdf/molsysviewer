import type { PanelContext } from "./types";
import { makeButton, makeSettingsCard, makeStyledSelect } from "./ui-helpers";

export interface SystemLoadRow {
    source: string;
    label: string;
    selection: string;
    structures: string;
}
export type SystemInputMode = "independent" | "complementary";
export type SystemLoadMode = "add" | "replace" | "append_structures";

/** Parse a user-declared ordered structure selection without rounding indices. */
export function systemStructureIndices(text: string): "all" | number[] {
    text = text.trim();
    if (text === "all") return text;
    if (text.startsWith("[") !== text.endsWith("]")) throw new Error("Structure-list brackets must be paired.");
    const parts = text.replace(/^\[/, "").replace(/\]$/, "").split(",").map(part => part.trim());
    if (!parts.length || parts.some(part => !/^\d+$/.test(part))) {
        throw new Error("Structures must be 'all' or a comma-separated list of nonnegative integers.");
    }
    const indices = parts.map(Number);
    if (indices.some(index => !Number.isSafeInteger(index)) || new Set(indices).size !== indices.length) {
        throw new Error("Structure indices must be unique integers that can be represented exactly.");
    }
    return indices;
}

function atomSelection(text: string): string | number[] {
    text = text.trim() || "all";
    if (!text.startsWith("[")) return text;
    const values = JSON.parse(text);
    if (!Array.isArray(values) || !values.length || values.some(value => !Number.isSafeInteger(value) || value < 0)) {
        throw new Error("Atom indices must be a nonempty list of nonnegative integers.");
    }
    return values;
}

/** Translate Studio input intention to the existing, explicit public load contract. */
export function systemLoadArguments(rows: SystemLoadRow[], input: SystemInputMode, mode: SystemLoadMode, pair: boolean): Record<string, unknown> {
    if (!rows.length || rows.some(row => !row.source.trim())) throw new Error("Enter a path or PDB ID for every source.");
    if (input !== "independent" && input !== "complementary") throw new Error("Unknown source interpretation.");
    if (!["add", "replace", "append_structures"].includes(mode)) throw new Error("Unknown load operation.");
    const multiple = input === "independent" && rows.length > 1;
    if (multiple && mode === "append_structures") throw new Error("Append structures accepts one system, including its complementary files.");
    const sources = rows.map(row => row.source.trim());
    const selectedRows = multiple ? rows : rows.slice(0, 1);
    const selections = selectedRows.map(row => atomSelection(row.selection));
    const structures = selectedRows.map(row => systemStructureIndices(row.structures));
    return {
        molecular_system: sources.length === 1 ? sources[0] : sources,
        multiple, mode,
        ...(multiple ? { labels: rows.map(row => row.label.trim() || null) } : { label: rows[0].label.trim() || null }),
        selection: multiple ? selections : selections[0],
        structure_indices: multiple ? structures : structures[0],
        structure_pairing: pair ? "by_index" : null,
    };
}

/** Persistent loading draft: hierarchy/frame refreshes never reconstruct this form. */
export class SystemLoadControls {
    readonly root: HTMLDetailsElement;
    private readonly fields: HTMLFieldSetElement;
    private readonly rowsHost: HTMLDivElement;
    private readonly status: HTMLDivElement;
    private readonly input: HTMLSelectElement;
    private readonly operation: HTMLSelectElement;
    private readonly pair: HTMLInputElement;
    private rows: SystemLoadRow[] = [];
    private pending: string | null = null;
    private serial = 0;

    constructor(private readonly ctx: PanelContext) {
        this.root = document.createElement("details");
        this.root.setAttribute("data-molsysviewer-system-load", "true");
        Object.assign(this.root.style, { flex: "0 0 auto", maxHeight: "50%", overflowY: "auto", fontSize: "11px" });
        const summary = document.createElement("summary");
        summary.textContent = "Load systems";
        summary.style.cursor = "pointer";
        this.root.appendChild(summary);
        const card = makeSettingsCard("Sources");
        this.root.appendChild(card);
        this.fields = document.createElement("fieldset");
        Object.assign(this.fields.style, { margin: "0", padding: "0", border: "0", display: "flex", flexDirection: "column", gap: "8px", minWidth: "0" });
        card.appendChild(this.fields);
        this.input = makeStyledSelect([
            { value: "independent", label: "Independent systems" },
            { value: "complementary", label: "Complementary files: one system" },
        ], "independent", () => this.renderRows());
        this.input.setAttribute("data-molsysviewer-load-input-mode", "true");
        this.fields.appendChild(this.input);
        this.operation = makeStyledSelect([
            { value: "add", label: "Add to whole" }, { value: "replace", label: "Replace whole" },
            { value: "append_structures", label: "Append structures of the current system" },
        ], "add", () => {});
        this.operation.setAttribute("data-molsysviewer-load-operation", "true");
        this.fields.appendChild(this.operation);
        const hint = document.createElement("div");
        hint.textContent = "Enter file paths accessible to the running Python session, or PDB IDs. Each independent system becomes part of whole; multiple sources get their own regions.";
        hint.style.color = "rgba(244,244,245,0.65)";
        this.fields.appendChild(hint);
        this.rowsHost = document.createElement("div");
        this.fields.appendChild(this.rowsHost);
        const add = makeButton("Add source", () => { this.addRow(); });
        add.setAttribute("data-molsysviewer-load-add-source", "true");
        this.fields.appendChild(add);
        const pairing = document.createElement("label");
        this.pair = document.createElement("input"); this.pair.type = "checkbox";
        this.pair.setAttribute("data-molsysviewer-load-pairing", "true");
        pairing.appendChild(this.pair);
        pairing.appendChild(document.createTextNode(" Pair selected structures in their listed order"));
        this.fields.appendChild(pairing);
        const rule = document.createElement("div");
        rule.textContent = "For combining several structures per source, declare pairing. Counts and available times must match. Coordinates are not aligned; whole keeps its first/current box.";
        rule.style.color = "rgba(244,244,245,0.65)";
        this.fields.appendChild(rule);
        const submit = makeButton("Load", () => this.submit());
        submit.setAttribute("data-molsysviewer-load-submit", "true");
        this.fields.appendChild(submit);
        this.status = document.createElement("div");
        this.status.setAttribute("data-molsysviewer-load-status", "true");
        this.status.setAttribute("role", "status");
        card.appendChild(this.status);
        this.addRow();
    }

    open(): void { this.root.open = true; }

    isPending(): boolean { return this.pending !== null; }

    updateResult(requestId: string, ok: boolean, atoms?: number, structures?: number, sources?: number, error?: string): void {
        if (requestId !== this.pending) return;
        this.pending = null; this.fields.disabled = false;
        this.root.setAttribute("aria-busy", "false");
        this.status.textContent = ok ? `Loaded: ${atoms} atoms, ${structures} structures, ${sources} source(s).` : (error || "Loading failed.");
    }

    private addRow(): void {
        this.rows.push({ source: "", label: "", selection: "all", structures: "0" });
        this.renderRows();
    }

    private renderRows(): void {
        this.rowsHost.replaceChildren();
        this.rows.forEach((row, index) => {
            const card = makeSettingsCard(`Source ${index + 1}`);
            card.setAttribute("data-molsysviewer-load-source", String(index));
            const field = (key: keyof SystemLoadRow, label: string) => {
                const wrap = document.createElement("label");
                wrap.textContent = label;
                Object.assign(wrap.style, { display: "flex", flexDirection: "column", gap: "3px" });
                const control = document.createElement("input"); control.type = "text"; control.value = row[key];
                control.setAttribute("data-molsysviewer-load-field", key);
                Object.assign(control.style, { width: "100%", boxSizing: "border-box", background: "rgba(255,255,255,0.05)", color: "#f4f4f5", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "4px", padding: "4px" });
                control.addEventListener("input", () => { row[key] = control.value; });
                wrap.appendChild(control); card.appendChild(wrap);
            };
            field("source", "File path or PDB ID");
            if (this.input.value === "independent" || index === 0) {
                field("label", "Label (optional)");
                field("selection", "Atoms: MolSysMT selection or [0, 2, ...]");
                field("structures", "Structures: 0, 8, 3 or all (0-based)");
            }
            if (this.rows.length > 1) {
                const remove = makeButton("Remove source", () => { this.rows.splice(index, 1); this.renderRows(); });
                remove.setAttribute("data-molsysviewer-load-remove-source", String(index)); card.appendChild(remove);
            }
            this.rowsHost.appendChild(card);
        });
    }

    private submit(): void {
        if (this.pending) return;
        try {
            const args = systemLoadArguments(this.rows, this.input.value as SystemInputMode, this.operation.value as SystemLoadMode, this.pair.checked);
            this.pending = `load-${Date.now()}-${++this.serial}-${Math.random().toString(36).slice(2)}`;
            this.fields.disabled = true; this.root.setAttribute("aria-busy", "true");
            this.status.textContent = "Loading…";
            this.ctx.onAction("load_systems", { ...args, request_id: this.pending });
        } catch (error) {
            this.pending = null; this.fields.disabled = false; this.root.setAttribute("aria-busy", "false");
            this.status.textContent = String(error instanceof Error ? error.message : error);
        }
    }
}
