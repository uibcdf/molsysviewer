import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";
import type { InteractionSummary, InteractionAnalysisSummary, InteractionInspection, InteractionSummariesMessage, InteractionCalculationFamily } from "../../managers/handlers/interaction-handlers";
import type { ActiveSelectionPayload } from "../../managers/active-selection";
import type { SavedSelectionSummary, SelectionQueryPreview } from "../group-panel";
import { ManualQueryComposer } from "../query-composer";
import { renderSelectionDock } from "./selection-dock";
import { calculationCriteria, initialCalculationCriterion, scientificParameters, changeScientificUnit,
    type ScientificValues } from "./interaction-calculation-controls";

const box = () => {
    const el = document.createElement("div");
    Object.assign(el.style, { display: "flex", flexDirection: "column", gap: "7px", padding: "10px",
        borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.035)" });
    return el;
};
function append(parent: HTMLElement, ...children: Array<Node | string>) {
    for (const child of children) parent.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
}
const row = () => { const el = document.createElement("div"); Object.assign(el.style, { display: "flex", gap: "4px", flexWrap: "wrap" }); return el; };
const note = (text: string) => { const el = document.createElement("div"); el.textContent = text; Object.assign(el.style, { fontSize: "11px", color: "rgba(244,244,245,0.65)", overflowWrap: "anywhere" }); return el; };
function field(parent: HTMLElement, label: string, value: string, key: string, change: (value: string) => void, type = "text", identity?: string) {
    const wrap = document.createElement("label"); wrap.appendChild(note(label));
    const input = document.createElement("input"); input.type = type; input.value = value;
    // BasePanel restores the first data attribute. Scientific identity changes
    // with criterion/unit, so an old focused value cannot overwrite a new one.
    if (identity) input.setAttribute("data-molsysviewer-interaction-control", identity);
    input.setAttribute("data-molsysviewer-interaction-field", key);
    Object.assign(input.style, { width: "100%", boxSizing: "border-box", minWidth: "0", background: "rgba(0,0,0,0.2)",
        border: "1px solid rgba(255,255,255,0.12)", borderRadius: "6px", padding: "4px 6px", color: "#fff", fontSize: "11px" });
    input.addEventListener("input", () => change(input.value)); wrap.appendChild(input); parent.appendChild(wrap); return input;
}
function select(parent: HTMLElement, values: Array<[string, string]>, current: string, change: (value: string) => void) {
    const el = document.createElement("select"); Object.assign(el.style, { width: "100%", minWidth: "0", color: "#fff", background: "#272335", padding: "5px", borderRadius: "6px" });
    for (const [value, text] of values) { const option = document.createElement("option"); option.value = value; option.textContent = text; el.appendChild(option); }
    el.value = current; el.addEventListener("change", () => change(el.value)); parent.appendChild(el); return el;
}
function indices(value: string, allowCurrent = false): "all" | "current" | number[] {
    const text = value.trim(); if (text === "all" || (allowCurrent && text === "current")) return text as "all" | "current";
    if (!/^\d+(\s*,\s*\d+)*$/.test(text)) throw new Error("Use all, current (calculation), or comma-separated integer indices.");
    return text.split(",").map(v => Number(v.trim()));
}
const statusText = (item: InteractionSummary) => {
    if (item.status === "render-error") return "Interaction rendering failed. Check viewer diagnostics.";
    if (item.status === "unavailable") return "Interaction projection unavailable. Return to this structure to retry.";
    if (item.status === "pending") return "Loading this structure…";
    if (item.status === "render-limit") return "Display exceeds the occurrence or byte preparation budget. Reduce the display filter.";
    if (item.status === "unevaluated") return "Not evaluated";
    if (item.status === "excluded") return "Excluded by display filter";
    if (item.status === "broken") return "Analysis or selection needs repair";
    if (!item.n_observations) return "Evaluated · no matching observations";
    return `${item.hidden || item.layer_hidden ? 0 : item.n_supported} drawn / ${item.n_observations} observations · ${item.hidden || item.layer_hidden ? 0 : item.n_segments ?? item.n_supported} segments${item.n_skipped ? ` · ${item.n_skipped} unsupported` : ""}`;
};

export class InteractionsPanel extends BasePanel {
    readonly key = "interactions";
    private items: InteractionSummary[] = [];
    private analyses: InteractionAnalysisSummary[] = [];
    private families: InteractionCalculationFamily[] = [];
    private criteria = new Map<string, string>();
    private scientificDrafts = new Map<string, ScientificValues>();
    private frame = 0;
    private loaded = false;
    private backendAvailable = true;
    private source = "calculate";
    private name = "hbonds";
    private stored = "";
    private kind = "hbond";
    private calcStructures = "current";
    private calcAtomScope = "all";
    private pbc = false;
    private filename = "";
    private fileAnalysis = "";
    private aligned = false;
    private atomMap = "";
    private frameMap = "";
    private tag = "";
    private layer = "";
    private mode = "involving_selection";
    private displayStructures = "all";
    private types = "";
    private exclusive = false;
    private a: number[] | null = null;
    private b: number[] | null = null;
    private slot: "a" | "b" = "a";
    private selection: ActiveSelectionPayload | null = null;
    private saved: SavedSelectionSummary[] = [];
    private dockTab: "active" | "query" | "saved" = "active";
    private composer: ManualQueryComposer;
    private editing: string | null = null;
    private inspecting: string | null = null;
    private inspection: InteractionInspection | null = null;
    private requestId = 0;
    private error = "";
    private creationRequest = 0;
    private busy: number | null = null;
    private filtersOpen = false;
    private analysesOpen = false;
    private filtersDetails: HTMLDetailsElement | null = null;
    private analysesDetails: HTMLDetailsElement | null = null;
    private color = "#34d399";
    private radius = "0.025";
    private alpha = "0.85";
    constructor(private ctx: PanelContext) {
        super(); this.composer = new ManualQueryComposer("interactions", details => ctx.onAction("selection_query_preview_request", details), undefined, { buttonLabel: "Select" });
    }
    setSummary(message: InteractionSummariesMessage) {
        const previous = this.items.find(item => item.tag === this.inspecting);
        const next = message.interactions.find(item => item.tag === this.inspecting);
        if (this.frame !== message.frame || (this.inspecting && previous?.query_revision !== next?.query_revision)) {
            this.inspection = null; this.inspecting = null; this.requestId++;
        }
        this.backendAvailable = message.backend_available ?? this.backendAvailable;
        this.families = message.calculation_families ?? this.families;
        if (this.families.length && !this.families.some(family => family.kind === this.kind)) this.kind = this.families[0].kind;
        this.items = message.interactions; this.analyses = message.analyses; this.loaded = message.system_loaded; this.frame = message.frame;
        if (!this.analyses.some(item => item.name === this.stored)) this.stored = this.analyses[0]?.name ?? "";
        this.ctx.setBadge(String(this.items.length)); this.scheduleRender();
    }
    setFrame(items: InteractionSummary[], frame: number) { this.setSummary({ op: "set_interaction_summaries", interactions: items, analyses: this.analyses, system_loaded: this.loaded, frame }); }
    setSelection(selection: ActiveSelectionPayload) { this.selection = selection; this.scheduleRender(); }
    setSavedSelections(items: SavedSelectionSummary[]) { this.saved = items; this.scheduleRender(); }
    updateQuery(preview: SelectionQueryPreview) {
        const updated = this.composer.updatePreview(preview);
        if (updated && preview.ok === true) {
            const { expression, syntax } = this.composer.value();
            if (expression) this.ctx.onAction("apply_selection_query", { expression, syntax, op: "replace" });
        }
        return updated;
    }
    updateInspection(requestId: number, result: InteractionInspection) {
        if (requestId !== this.requestId || result.frame !== this.frame || result.tag !== this.inspecting) return;
        const item = this.items.find(item => item.tag === result.tag);
        if (!item || item.analysis_revision !== result.analysis_revision || item.query_revision !== result.query_revision) return;
        this.inspection = result; this.scheduleRender();
    }
    updateCreationResult(requestId: number, ok: boolean, name?: string, error?: string) {
        if (requestId !== this.busy) return;
        this.busy = null;
        if (ok && name) { this.source = "stored"; this.stored = name; this.tag = ""; }
        this.error = error ?? "";
        this.scheduleRender();
    }
    private emit(action: Parameters<PanelContext["onAction"]>[0], details?: Record<string, unknown>) {
        this.error = ""; try { this.ctx.onAction(action, details); } catch (error) { this.busy = null; this.error = String(error); } this.scheduleRender();
    }
    private filter() { return { selection: this.a ?? "all", selection_2: this.mode === "between_selections" ? this.b : null,
        mode: this.mode, exclusive: this.mode === "between_selections" && this.exclusive, structure_indices: indices(this.displayStructures),
        interaction_types: this.types.trim() ? this.types.split(",").map(v => v.trim()).filter(Boolean) : null }; }
    private inspect(tag: string, offset = 0) { this.inspecting = tag; this.inspection = null; this.emit("inspect_interaction", { tag, frame: this.frame, offset, request_id: ++this.requestId }); }
    private criterion() {
        const key = this.criteria.get(this.kind) ?? initialCalculationCriterion(this.kind,
            this.families.find(item => item.kind === this.kind)?.default_parameters);
        return calculationCriteria(this.kind).find(item => item.key === key);
    }
    private scientificDraft() {
        const key = `${this.kind}:${this.criterion()?.key}`;
        if (!this.scientificDrafts.has(key)) this.scientificDrafts.set(key, {});
        return this.scientificDrafts.get(key)!;
    }
    private paintScientificControls(parent: HTMLElement) {
        const criteria = calculationCriteria(this.kind), criterion = this.criterion();
        if (!criterion) { parent.appendChild(note("No Studio controls are available for this family.")); return; }
        const heading = document.createElement("label"); heading.appendChild(note("Scientific criterion")); parent.appendChild(heading);
        if (criteria.length > 1) {
            const chooser = select(heading, criteria.map(item => [item.key, item.label]), criterion.key,
                value => { this.criteria.set(this.kind, value); this.scheduleRender(); });
            chooser.setAttribute("data-molsysviewer-interaction-criterion", "true");
        } else heading.appendChild(note(criterion.label));
        parent.appendChild(note(criterion.help));
        parent.appendChild(note("Blank optional fields use the criterion's defaults. Scientific values are stored with the analysis."));
        const draft = this.scientificDraft();
        for (const control of criterion.controls) {
            const group = document.createElement("div"); parent.appendChild(group);
            if (control.type === "choice") {
                const label = document.createElement("label"); label.appendChild(note(control.label)); group.appendChild(label);
                const chooser = select(label, control.choices!, draft[control.key] || "", value => draft[control.key] = value);
                chooser.setAttribute("data-molsysviewer-interaction-field", `parameter-${control.key}`);
            } else if (control.type === "names") {
                field(group, control.label, draft[control.key] || "", `parameter-${control.key}`, value => draft[control.key] = value,
                    "text", `${this.kind}:${criterion.key}:${control.key}`);
            } else {
                const inputRow = row(); group.appendChild(inputRow);
                const unit = draft[`${control.key}-unit`] || (control.type === "length" ? "nm" : "degrees");
                const keys = control.type === "angle-range" ? [`${control.key}-min`, `${control.key}-max`] : [control.key];
                if (control.type === "angle-range") group.prepend(note(control.label));
                keys.forEach((key, index) => {
                    const cell = document.createElement("div"); cell.style.flex = "1"; cell.style.minWidth = "0"; inputRow.appendChild(cell);
                    const input = field(cell, control.type === "angle-range" ? index === 0 ? "Minimum" : "Maximum" : control.label,
                        draft[key] || "", `parameter-${key}`, value => draft[key] = value, "number", `${this.kind}:${criterion.key}:${key}:${unit}`);
                    input.step = "any"; input.min = "0"; input.placeholder = control.required ? "Required" : "Method default";
                    if (control.type !== "length") input.max = String(unit === "degrees" ? 180 : Math.PI);
                    if (control.required) input.setAttribute("aria-required", "true");
                });
                const unitChooser = select(inputRow, control.type === "length" ? [["nm", "nm"], ["angstroms", "Å"]] : [["degrees", "°"], ["radians", "rad"]],
                    unit, value => { changeScientificUnit(draft, control, value); this.scheduleRender(); });
                unitChooser.style.width = "66px"; unitChooser.style.alignSelf = "end";
                unitChooser.setAttribute("aria-label", `${control.label} unit`);
                unitChooser.setAttribute("data-molsysviewer-interaction-field", `parameter-${control.key}-unit`);
            }
        }
    }
    protected paint() {
        if (!this.host) return;
        // Native toggle events are queued: read the live state before rebuilding.
        const previousFilters = this.filtersDetails;
        if (previousFilters) this.filtersOpen = previousFilters.open;
        const previousAnalyses = this.analysesDetails;
        if (previousAnalyses) this.analysesOpen = previousAnalyses.open;
        this.host.replaceChildren(); Object.assign(this.host.style, { display: "flex", flexDirection: "column", gap: "9px" });
        this.host.appendChild(makeSectionHeader("Interactions"));
        if (!this.backendAvailable) this.host.appendChild(note("Interactions requires a compatible MolSysMT backend. Other viewer tools remain available."));
        const enabled = this.items.filter(item => !item.hidden).length;
        this.host.appendChild(note(`${enabled}/${this.items.length} sets enabled · structure ${this.frame}`));
        const all = row(); append(all, makeButton("Show all", () => this.emit("show_all_interactions")), makeButton("Hide all", () => this.emit("hide_all_interactions"))); this.host.appendChild(all);
        if (this.error) this.host.appendChild(note(this.error));
        const form = box(); form.appendChild(makeSectionHeader(this.editing ? `Edit ${this.editing}` : "New interaction set")); this.host.appendChild(form);
        if (!this.editing) {
            const tabs = row(); for (const [value, text] of [["calculate", "Calculate"], ["stored", "Stored analysis"], ["file", "H5MSM file"]]) {
                const btn = makeButton(text, () => { this.source = value; this.scheduleRender(); }); btn.setAttribute("data-molsysviewer-interaction-source", value); if (this.source === value) btn.style.background = "rgba(139,92,246,0.25)"; tabs.appendChild(btn);
            } form.appendChild(tabs);
            if (this.source === "stored") {
                select(form, this.analyses.map(item => [item.name, `${item.name} · ${item.n_occurrences} observations`]), this.stored, value => { this.stored = value; this.scheduleRender(); });
                const analysis = this.analyses.find(item => item.name === this.stored);
                if (analysis) form.appendChild(note(`${analysis.method} · ${analysis.n_evaluated_structures}/${analysis.n_structures} structures evaluated`));
            } else {
                field(form, "Store analysis as", this.name, "name", value => this.name = value);
                if (this.source === "calculate") {
                    const familyLabel = document.createElement("label"); familyLabel.appendChild(note("Interaction family")); form.appendChild(familyLabel);
                    const chooser = select(familyLabel, this.families.map(family => [family.kind, family.label]), this.kind, value => {
                        this.kind = value; this.scheduleRender();
                    });
                    chooser.setAttribute("data-molsysviewer-interaction-kind", "true");
                    this.paintScientificControls(form);
                    if (["ionic_contact", "pi_pi", "cation_pi"].includes(this.kind)) form.appendChild(note("Compound participants use centroid guides. Reported measurements keep the calculation's definition."));
                    if (["disulfide_candidate", "metal_coordination_candidate"].includes(this.kind)) form.appendChild(note("Geometric candidates; covalent topology is unchanged."));
                    const scopeLabel = document.createElement("label"); scopeLabel.appendChild(note("Calculate atoms")); form.appendChild(scopeLabel);
                    const scope = select(scopeLabel, [["all", "All atoms"], ["a", "Within staged A"], ["between", "Between staged A and B"]],
                        this.calcAtomScope, value => { this.calcAtomScope = value; this.scheduleRender(); });
                    scope.setAttribute("data-molsysviewer-interaction-calc-scope", "true");
                    scope.querySelector<HTMLOptionElement>('option[value="between"]')!.disabled = this.kind === "disulfide_candidate";
                    form.appendChild(note(this.calcAtomScope === "all" ? "Calculation covers all atoms. A/B below filter the display only."
                        : `Calculation uses staged ${this.calcAtomScope === "a" ? "A" : "A and B"} below; atoms outside this scope are not evaluated.`));
                    field(form, "Calculate structures: current, all, or indices", this.calcStructures, "calc-structures", value => this.calcStructures = value);
                    const pbc = document.createElement("label"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = this.pbc; cb.onchange = () => this.pbc = cb.checked; append(pbc, cb, " Periodic boundary conditions"); form.appendChild(pbc);
                } else {
                    field(form, "H5MSM path in the Python session", this.filename, "filename", value => this.filename = value);
                    field(form, "Analysis name inside the file", this.fileAnalysis, "file-analysis", value => this.fileAnalysis = value);
                    field(form, "Source atom indices in destination order (optional)", this.atomMap, "atom-map", value => this.atomMap = value);
                    field(form, "Source structure indices in destination order (optional)", this.frameMap, "frame-map", value => this.frameMap = value);
                    const agreement = document.createElement("label"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = this.aligned;
                    cb.setAttribute("data-molsysviewer-interaction-aligned", "true"); cb.onchange = () => { this.aligned = cb.checked; this.scheduleRender(); };
                    append(agreement, cb, " I declare that atom and structure indices match this system."); form.appendChild(agreement);
                }
            }
        }
        field(form, "Set tag (empty = automatic)", this.tag, "tag", value => this.tag = value);
        field(form, "Layer (empty = automatic)", this.layer, "layer", value => this.layer = value);
        const details = document.createElement("details"); this.filtersDetails = details; details.setAttribute("data-molsysviewer-interaction-filters", "true"); details.open = !!this.editing || this.filtersOpen; details.addEventListener("toggle", () => { if (details.isConnected) this.filtersOpen = details.open; }); const title = document.createElement("summary"); title.textContent = "Display filter and selections"; details.appendChild(title); form.appendChild(details);
        select(details, [["involving_selection", "All interactions involving the selection"], ["within_selection", "Only within the selection"], ["across_selection_boundary", "Between the selection and the rest"], ["between_selections", "Between selections A and B"]], this.mode, value => { this.mode = value; this.scheduleRender(); });
        details.appendChild(note(`A: ${this.a ? `${this.a.length} atoms` : "all atoms"} · B: ${this.b ? `${this.b.length} atoms` : "unset"}`));
        const slots = row(); append(slots, makeButton("Stage A", () => { this.slot = "a"; this.scheduleRender(); }), makeButton("Stage B", () => { this.slot = "b"; this.scheduleRender(); }), makeButton("Reset selections", () => { this.a = this.b = null; this.scheduleRender(); })); details.appendChild(slots);
        if (this.selection) details.appendChild(renderSelectionDock({ activeSelection: this.selection, savedSelections: this.saved,
            activeTab: this.dockTab, buttonLabel: `Use as ${this.slot.toUpperCase()}`, queryComposer: this.composer,
            dataAttributePrefix: "interaction", onTabChange: tab => { this.dockTab = tab; this.scheduleRender(); },
            onCommitSelection: atoms => { this[this.slot] = [...atoms]; this.scheduleRender(); }, onActivateSavedSelection: item => this.emit("activate_selection", { tag: item.tag }) }));
        field(details, "Display structures: all or indices", this.displayStructures, "display-structures", value => this.displayStructures = value);
        field(details, "Interaction types (comma-separated; empty = all)", this.types, "types", value => this.types = value);
        if (this.mode === "between_selections") { const label = document.createElement("label"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = this.exclusive; cb.onchange = () => this.exclusive = cb.checked; append(label, cb, " Restrict participants to A ∪ B"); details.appendChild(label); }
        if (this.editing) {
            form.appendChild(note("Calculation parameters are fixed. Calculate a new analysis to change cutoffs."));
            field(form, "Color", this.color, "color", value => this.color = value, "color");
            field(form, "Radius (nm)", this.radius, "radius", value => this.radius = value, "number");
            field(form, "Opacity (0–1)", this.alpha, "alpha", value => this.alpha = value, "number");
        }
        const submit = makeButton(this.busy !== null ? "Working…" : this.editing ? "Apply changes" : this.source === "calculate" ? "Calculate and create set" : this.source === "file" ? "Load and create set" : "Create set", () => {
            try {
                if (this.mode === "between_selections" && (!this.a || !this.b)) throw new Error("Stage disjoint selections A and B first.");
                const filter = this.filter();
                if (this.editing) this.emit("edit_interaction", { tag: this.editing, new_tag: this.tag, layer_tag: this.layer,
                    filter, color: this.color, radius_nm: Number(this.radius), radius_unit: "nm", alpha: Number(this.alpha) });
                else {
                    const calculation: Record<string, unknown> = { kind: this.kind, selection: "all",
                        structure_indices: this.source === "calculate" ? indices(this.calcStructures, true) : "current", pbc: this.pbc };
                    if (this.source === "calculate") {
                        calculation.parameters = scientificParameters(this.kind, this.criterion()?.key ?? "", this.scientificDraft());
                        if (this.calcAtomScope !== "all") {
                            if (!this.a?.length) throw new Error("Stage a nonempty selection A for this calculation scope.");
                            calculation.selection = [...this.a];
                            if (this.calcAtomScope === "between") {
                                if (this.kind === "disulfide_candidate") throw new Error("Disulfide candidates support all atoms or within A; choose a supported calculation scope.");
                                const selectedA = new Set(this.a);
                                if (!this.b?.length || this.b.some(atom => selectedA.has(atom))) throw new Error("Stage nonempty disjoint selections A and B for this calculation scope.");
                                calculation.selection_2 = [...this.b];
                            }
                        }
                    }
                    this.busy = ++this.creationRequest;
                    this.emit("create_interaction", { request_id: this.busy, source: this.source, analysis_name: this.source === "stored" ? this.stored : this.name,
                        tag: this.tag, layer_tag: this.layer, filter, calculation, filename: this.filename, file_analysis_name: this.fileAnalysis,
                        assume_aligned: this.aligned, atom_indices: this.source === "file" && this.atomMap ? indices(this.atomMap) : null,
                        structure_indices: this.source === "file" && this.frameMap ? indices(this.frameMap) : null });
                }
            } catch (error) { this.busy = null; this.error = String(error); this.scheduleRender(); }
        });
        submit.disabled = this.busy !== null || !this.loaded || !this.backendAvailable || (!this.editing && this.source === "calculate" && (!this.families.length || !this.criterion())) || (!this.editing && this.source === "file" && !this.aligned) || (!this.editing && this.source === "stored" && !this.stored);
        submit.setAttribute("data-molsysviewer-interaction-create", "true"); form.appendChild(submit);
        if (this.editing) form.appendChild(makeButton("Done editing", () => { this.editing = null; this.tag = this.layer = ""; this.scheduleRender(); }));
        this.host.appendChild(makeSectionHeader("Saved sets"));
        if (!this.items.length) this.host.appendChild(note("No interaction sets. Calculate an analysis or load one from H5MSM."));
        for (const item of this.items) {
            const card = box(); card.setAttribute("data-molsysviewer-interaction-set", item.tag);
            append(card, note(`${item.tag} · ${item.analysis_name}`), note(statusText(item)), note(`${item.hidden ? "Hidden" : item.layer_hidden ? "Hidden by layer" : "Enabled"} · layer ${item.layer_tag}`));
            const actions = row();
            for (const [text, action] of [["Focus", "focus_interaction"], [item.hidden ? "Show" : "Hide", "toggle_interaction_visibility"], ["Delete", "delete_interaction"]] as const) { const button = makeButton(text, () => this.emit(action, { tag: item.tag })); if (action === "focus_interaction") button.disabled = !item.n_supported; actions.appendChild(button); }
            actions.appendChild(makeButton("Edit", () => { this.editing = item.tag; this.tag = item.tag; this.layer = item.layer_tag; this.a = item.filter.selection === "all" ? null : [...item.filter.selection]; this.b = Array.isArray(item.filter.selection_2) ? [...item.filter.selection_2] : null;
                this.mode = item.filter.mode; this.displayStructures = item.filter.structure_indices === "all" ? "all" : item.filter.structure_indices.join(","); this.types = item.filter.interaction_types?.join(",") ?? ""; this.exclusive = item.filter.exclusive;
                this.color = `#${item.style.color.toString(16).padStart(6, "0")}`; this.radius = String(item.style.radius_nm); this.alpha = String(item.style.alpha); this.scheduleRender(); }));
            actions.appendChild(makeButton("Inspect", () => this.inspect(item.tag))); card.appendChild(actions);
            if (this.inspecting === item.tag) {
                if (!this.inspection) card.appendChild(note("Requesting current structure observations…"));
                else {
                    const data = this.inspection; card.appendChild(note(`${data.method} · ${data.total} observations · ${JSON.stringify(data.parameters)}`));
                    card.appendChild(note(`Calculation scope: ${JSON.stringify(data.evaluation_scope)}`));
                    if (data.limit_reason) card.appendChild(note(data.limit_reason));
                    for (const observation of data.observations) {
                        const detail = box();
                        detail.setAttribute("data-molsysviewer-interaction-observation", String(observation.occurrence_index));
                        detail.appendChild(note(`#${observation.occurrence_index} ${observation.interaction_type} · ${observation.participants.map(p => `${p.role} [${p.atom_indices.join(",")}]`).join(" → ")} · ${Object.entries(observation.measurements).map(([name, value]) => `${name}: ${value ?? "unavailable"} ${data.measure_units[name] ?? ""}`).join("; ")} · evidence ${observation.evidence ?? ""}${observation.image_vectors ? ` · images ${JSON.stringify(observation.image_vectors)}` : ""}`));
                        const actions = row();
                        const identity = { tag: item.tag, frame: data.frame, occurrence_index: observation.occurrence_index,
                            analysis_revision: data.analysis_revision, query_revision: data.query_revision };
                        for (const [label, action] of [["Select participants", "select_interaction_observation"], ["Focus participants", "focus_interaction_observation"]] as const) {
                            const button = makeButton(label, () => this.emit(action, identity));
                            button.setAttribute("data-molsysviewer-interaction-observation-action", action);
                            actions.appendChild(button);
                        }
                        detail.appendChild(actions); card.appendChild(detail);
                    }
                    const pagination = row(); if (data.offset) pagination.appendChild(makeButton("Previous", () => this.inspect(item.tag, Math.max(0, data.offset - 50))));
                    if (data.status !== "inspection-limit" && data.next_offset != null) pagination.appendChild(makeButton("Next", () => this.inspect(item.tag, data.next_offset!))); card.appendChild(pagination);
                }
            } this.host.appendChild(card);
        }
        const stored = document.createElement("details"); this.analysesDetails = stored; stored.setAttribute("data-molsysviewer-interaction-analyses", "true"); stored.open = this.analysesOpen; stored.addEventListener("toggle", () => { if (stored.isConnected) this.analysesOpen = stored.open; }); const summary = document.createElement("summary"); summary.textContent = `Stored analyses (${this.analyses.length})`; stored.appendChild(summary);
        for (const analysis of this.analyses) {
            const card = box(); card.appendChild(note(`${analysis.name} · ${analysis.n_occurrences} observations · ${analysis.n_evaluated_structures}/${analysis.n_structures} structures · ${analysis.n_references} visual references`));
            card.appendChild(note(`${analysis.method} · ${JSON.stringify(analysis.parameters)} · ${JSON.stringify(analysis.software)}`));
            const actions = row(); actions.appendChild(makeButton("Use", () => { this.source = "stored"; this.stored = analysis.name; this.editing = null; this.scheduleRender(); }));
            const remove = makeButton("Delete analysis", () => this.emit("delete_interaction_analysis", { analysis_name: analysis.name })); remove.disabled = analysis.n_references > 0; remove.title = "Deleting an analysis clears scene undo history."; actions.appendChild(remove); card.appendChild(actions); stored.appendChild(card);
        } this.host.appendChild(stored);
    }
}
