import type { PanelContext } from "./types";
import type { SystemFileBrowseResult } from "../../messages/viewer-messages";
import { LoadFilePicker } from "./load-file-picker";
import { makeButton, makeSettingsCard, makeStyledSelect, workflowHelp } from "./ui-helpers";

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

/** Persistent loading draft with a scrollable editor and fixed action/result. */
export class SystemLoadControls {
    readonly root = document.createElement("div");
    private readonly form = document.createElement("form");
    private readonly fields = document.createElement("fieldset");
    private readonly rowsHost = document.createElement("div");
    private readonly status = document.createElement("div");
    private readonly availability = document.createElement("div");
    private readonly input: HTMLSelectElement;
    private readonly operation: HTMLSelectElement;
    private readonly pair = document.createElement("input");
    private readonly pairing = document.createElement("div");
    private readonly submitButton: HTMLButtonElement;
    private readonly picker: LoadFilePicker;
    private readonly advanced = new WeakMap<SystemLoadRow, boolean>();
    private readonly summaries = new Map<SystemLoadRow, HTMLElement>();
    private readonly sourceInputs = new Map<SystemLoadRow, HTMLInputElement>();
    private rows: SystemLoadRow[] = [];
    private pickTarget?: SystemLoadRow;
    private pending: string | null = null;
    private serial = 0;
    private hasSystem = false;
    private pairingApplicable = false;

    constructor(private readonly ctx: PanelContext) {
        this.root.setAttribute("data-molsysviewer-system-load", "true");
        Object.assign(this.root.style, { display: "flex", flexDirection: "column", flex: "1 1 0", minHeight: "0", overflow: "hidden", fontSize: "12px" });
        Object.assign(this.form.style, { display: "flex", flexDirection: "column", flex: "1 1 0", minHeight: "0", gap: "6px" });
        this.form.addEventListener("submit", event => { event.preventDefault(); this.submit(); });
        Object.assign(this.fields.style, { margin: "0", padding: "0 4px 0 0", border: "0", display: "flex", flexDirection: "column", gap: "6px", minWidth: "0", minHeight: "0", flex: "1 1 0", overflowY: "auto" });
        this.rowsHost.style.flexShrink = "0";
        this.fields.appendChild(this.rowsHost);
        const add = makeButton("Add source", () => this.addRow());
        add.setAttribute("data-molsysviewer-load-add-source", "true");
        add.style.flex = "0 0 auto";
        this.fields.appendChild(add);
        this.input = makeStyledSelect([
            { value: "independent", label: "Independent systems: one per source" },
            { value: "complementary", label: "Complementary files: one system" },
        ], "independent", () => this.renderRows());
        this.input.setAttribute("data-molsysviewer-load-input-mode", "true");
        this.input.setAttribute("aria-label", "Source interpretation");
        this.input.style.flexShrink = "0";
        this.fields.appendChild(this.input);
        this.pair.type = "checkbox";
        this.pair.setAttribute("data-molsysviewer-load-pairing", "true");
        const pairingLabel = document.createElement("label");
        pairingLabel.append(this.pair, document.createTextNode(" Pair structures in their listed order"));
        this.pairing.appendChild(pairingLabel);
        const rule = document.createElement("div");
        rule.textContent = "Combining trajectories requires matching counts and times. Coordinates are not aligned; Whole keeps its current box.";
        Object.assign(rule.style, { fontSize: "11px", color: "rgba(244,244,245,0.7)" });
        this.pairing.appendChild(rule);
        this.pairing.style.flexShrink = "0";
        this.fields.appendChild(this.pairing);
        const tips = workflowHelp("loading", [
            "Files must be accessible to the running Python session. Browse selects files there; it does not upload files from your browser computer. You can also type a path or PDB ID.",
            "Several PDBs: add one source per system and choose Independent systems. Each source keeps its own region. No alignment is performed.",
            "Topology and trajectory: add both paths and choose Complementary files: one system. Options in the first source apply to the combined system.",
            "Options default to all atoms and structure 0 (the first frame). Enter all for a complete trajectory, or an ordered zero-based list such as 0, 8, 3.",
            "Appending structures requires an existing system with compatible atom identity and order. Selecting files only fills this draft; the primary button applies the chosen operation.",
        ]);
        tips.style.flexShrink = "0";
        this.fields.appendChild(tips);
        this.form.appendChild(this.fields);
        const footer = document.createElement("div");
        footer.setAttribute("data-molsysviewer-load-footer", "true");
        Object.assign(footer.style, { flexShrink: "0", display: "flex", flexDirection: "column", gap: "5px", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "6px" });
        this.operation = makeStyledSelect([
            { value: "add", label: "Add to Whole" }, { value: "replace", label: "Replace Whole" },
            { value: "append_structures", label: "Append structures" },
        ], "add", () => this.refreshState());
        this.operation.setAttribute("data-molsysviewer-load-operation", "true");
        this.operation.setAttribute("aria-label", "Load operation");
        footer.appendChild(this.operation);
        this.availability.setAttribute("data-molsysviewer-load-availability", "true");
        this.availability.style.fontSize = "11px";
        footer.appendChild(this.availability);
        this.submitButton = makeButton("Load system", () => this.submit());
        this.submitButton.type = "submit";
        this.submitButton.style.flex = "0 0 auto";
        this.submitButton.setAttribute("data-molsysviewer-load-submit", "true");
        footer.appendChild(this.submitButton);
        this.status.setAttribute("data-molsysviewer-load-status", "true");
        this.status.setAttribute("role", "status");
        Object.assign(this.status.style, { maxHeight: "48px", overflowY: "auto", overflowWrap: "anywhere", fontSize: "11px" });
        footer.appendChild(this.status);
        this.form.appendChild(footer);
        this.picker = new LoadFilePicker(ctx, paths => {
            const index = this.pickTarget ? this.rows.indexOf(this.pickTarget) : -1;
            if (index < 0) return;
            this.rows[index].source = paths[0];
            this.rows.splice(index + 1, 0, ...paths.slice(1).map(source => ({ source, label: "", selection: "all", structures: "0" })));
            this.renderRows();
            this.sourceInput(index)?.focus();
        }, () => {
            this.form.style.display = "flex";
            const index = this.pickTarget ? this.rows.indexOf(this.pickTarget) : -1;
            this.sourceInput(index)?.focus();
        });
        this.root.append(this.form, this.picker.root);
        this.addRow();
    }

    open(): void {}
    isPending(): boolean { return this.pending !== null; }
    updateFiles(result: SystemFileBrowseResult): void { this.picker.update(result); }

    setSystemAvailable(available: boolean): void {
        if (!available && this.pending) return; // Rebuilding a submitted load is not a new empty-session choice.
        this.hasSystem = available;
        if (!available && this.operation.value === "append_structures") this.operation.value = "add";
        this.refreshState();
    }

    updateResult(requestId: string, ok: boolean, atoms?: number, structures?: number, sources?: number, error?: string): boolean {
        if (requestId !== this.pending) return false;
        this.pending = null;
        if (ok && (atoms ?? 0) > 0) this.hasSystem = true;
        this.fields.disabled = false;
        this.root.setAttribute("aria-busy", "false");
        this.status.textContent = ok ? `Loaded: ${atoms} atoms, ${structures} structures, ${sources} source(s).` : (error || "Loading failed.");
        this.refreshState();
        return true;
    }

    private addRow(): void {
        this.rows.push({ source: "", label: "", selection: "all", structures: "0" });
        this.renderRows();
        this.sourceInput(this.rows.length - 1)?.focus();
    }

    private sourceInput(index: number): HTMLInputElement | null {
        return index < 0 ? null : this.sourceInputs.get(this.rows[index]) ?? null;
    }

    private renderRows(): void {
        this.rowsHost.replaceChildren();
        this.summaries.clear();
        this.sourceInputs.clear();
        this.rows.forEach((row, index) => {
            const card = makeSettingsCard(`Source ${index + 1}`);
            card.setAttribute("data-molsysviewer-load-source", String(index));
            const field = (parent: HTMLElement, key: keyof SystemLoadRow, label: string) => {
                const wrap = document.createElement("label");
                wrap.textContent = label;
                Object.assign(wrap.style, { display: "flex", flexDirection: "column", gap: "3px", minWidth: "0", flex: "1 1 auto" });
                const control = document.createElement("input"); control.type = "text"; control.value = row[key];
                control.setAttribute("data-molsysviewer-load-field", key);
                if (key === "source") this.sourceInputs.set(row, control);
                Object.assign(control.style, { width: "100%", boxSizing: "border-box", background: "rgba(255,255,255,0.05)", color: "#f4f4f5", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "4px", padding: "4px" });
                control.addEventListener("input", () => { row[key] = control.value; this.refreshState(); });
                wrap.appendChild(control); parent.appendChild(wrap);
            };
            const sourceRow = document.createElement("div");
            Object.assign(sourceRow.style, { display: "flex", alignItems: "flex-end", gap: "6px" });
            field(sourceRow, "source", "File path or PDB ID");
            const browse = makeButton("Browse…", () => {
                this.pickTarget = row;
                this.form.style.display = "none";
                this.picker.open();
            });
            browse.title = "Choose files accessible to the Python session";
            browse.style.flex = "0 0 auto";
            browse.setAttribute("data-molsysviewer-load-browse", String(index));
            sourceRow.appendChild(browse);
            card.appendChild(sourceRow);
            if (this.input.value === "independent" || index === 0) {
                const options = document.createElement("details");
                options.open = this.advanced.get(row) ?? false;
                options.setAttribute("data-molsysviewer-load-options", String(index));
                options.addEventListener("toggle", () => this.advanced.set(row, options.open));
                const summary = document.createElement("summary"); summary.style.cursor = "pointer";
                this.summaries.set(row, summary); options.appendChild(summary);
                field(options, "label", "Label (optional)");
                field(options, "selection", "Atoms: MolSysMT selection or [0, 2, ...]");
                field(options, "structures", "Structures: 0, 8, 3 or all (0-based)");
                card.appendChild(options);
            }
            if (this.rows.length > 1) {
                const remove = makeButton("Remove input", () => { this.rows.splice(index, 1); this.renderRows(); });
                remove.title = "Remove this input row; loaded atoms are unchanged.";
                remove.setAttribute("data-molsysviewer-load-remove-source", String(index)); card.appendChild(remove);
            }
            this.rowsHost.appendChild(card);
        });
        this.refreshState();
    }

    private refreshState(): void {
        this.input.style.display = this.rows.length > 1 ? "" : "none";
        this.operation.style.display = this.hasSystem ? "" : "none";
        this.operation.disabled = this.pending !== null;
        const append = this.operation.querySelector('option[value="append_structures"]') as HTMLOptionElement | null;
        if (append) append.disabled = !this.hasSystem || (this.rows.length > 1 && this.input.value === "independent");
        this.pairingApplicable = this.input.value === "independent" && this.rows.length > 1 && this.rows.some(row => {
            try { const value = systemStructureIndices(row.structures); return value === "all" || value.length > 1; } catch { return false; }
        });
        this.pairing.style.display = this.pairingApplicable ? "" : "none";
        this.pair.disabled = !this.pairingApplicable;
        for (const [row, summary] of this.summaries) {
            const frames = row.structures === "0" ? "first structure" : row.structures === "all" ? "all structures" : `structures: ${row.structures}`;
            summary.textContent = `Options · ${frames}${!row.selection.trim() || row.selection.trim() === "all" ? " · all atoms" : " · selected atoms"}`;
        }
        const multiple = this.input.value === "independent" && this.rows.length > 1;
        this.submitButton.textContent = this.pending ? "Loading…" : !this.hasSystem ? `Load system${multiple ? "s" : ""}`
            : this.operation.value === "replace" ? "Replace system"
            : this.operation.value === "append_structures" ? "Append structures" : `Add system${multiple ? "s" : ""}`;
        const invalidAppend = this.operation.value === "append_structures"
            && (!this.hasSystem || multiple);
        this.availability.textContent = invalidAppend ? "Append accepts one system: use complementary files or one source." : "";
        this.availability.style.display = invalidAppend ? "" : "none";
        this.submitButton.disabled = this.pending !== null || invalidAppend;
        this.status.style.display = this.status.textContent ? "" : "none";
    }

    private submit(): void {
        if (this.pending) return;
        try {
            if (this.operation.value === "append_structures" && !this.hasSystem) throw new Error("Load a system before appending structures.");
            const args = systemLoadArguments(this.rows, this.input.value as SystemInputMode, this.operation.value as SystemLoadMode, this.pairingApplicable && this.pair.checked);
            this.pending = `load-${Date.now()}-${++this.serial}-${Math.random().toString(36).slice(2)}`;
            this.fields.disabled = true; this.root.setAttribute("aria-busy", "true");
            this.status.textContent = "Loading…";
            this.refreshState();
            this.ctx.onAction("load_systems", { ...args, request_id: this.pending });
        } catch (error) {
            this.pending = null; this.fields.disabled = false; this.root.setAttribute("aria-busy", "false");
            this.status.textContent = String(error instanceof Error ? error.message : error);
            this.refreshState();
        }
    }
}
