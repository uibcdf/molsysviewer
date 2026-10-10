import { studioRequestId, makeButton } from "./ui-helpers";
import type { PanelContext } from "./types";
import { ListSearch } from "../list-search";

export type StudioActionResult = { action: string; request_id: string; domain: string; ok: boolean; error_message?: string };
const attributes: Record<string, string> = {
    regions: "region-card", selections: "saved-selection-card", annotations: "annotation-tag",
    measurements: "measurement-tag", shapes: "shape-tag", layers: "layer-card", interactions: "interaction-set",
};

/** Local list state: filtering/marking never changes molecular selection or visibility. */
export class SavedListTools {
    private search = new ListSearch();
    private marked = new Set<string>();
    private pending: string | null = null;
    private confirmation: string[] | null = null;
    private message = "";
    private batchOpen = false;
    private rows: Array<{ tag: string; row: HTMLElement; text: string; display: string }> = [];
    constructor(readonly domain: string, private ctx: PanelContext, private repaint: () => void) {}
    pruneTargets(current: ReadonlySet<string>): void {
        for (const tag of this.marked) if (!current.has(tag)) this.marked.delete(tag);
        if (this.confirmation) this.confirmation = this.confirmation.filter(tag => current.has(tag));
    }
    updateResult(result: StudioActionResult): void {
        if (result.request_id !== this.pending) return;
        this.pending = null;
        this.message = result.ok ? "Completed. Use Undo to restore the previous scene." : result.error_message || "The batch failed.";
        if (result.ok) this.marked.clear();
        this.repaint();
    }
    mount(host: HTMLElement): void {
        if (typeof host.querySelectorAll !== "function") return;
        const attr = `data-molsysviewer-${attributes[this.domain]}`;
        this.rows = Array.from(host.querySelectorAll<HTMLElement>(`[${attr}]`))
            .map(row => ({ tag: row.getAttribute(attr)!, row, text: row.getAttribute("data-molsysviewer-list-search-text") || row.textContent?.toLocaleLowerCase() || "", display: row.style.display }));
        const current = new Set(this.rows.map(row => row.tag));
        for (const tag of this.marked) if (!current.has(tag)) this.marked.delete(tag);
        const toolbar = document.createElement("div"); toolbar.setAttribute("data-molsysviewer-list-tools", this.domain);
        Object.assign(toolbar.style, { display: "flex", flexDirection: "column", gap: "6px", padding: "8px 0" });
        const input = this.search.field(`Search saved ${this.domain}`, () => refresh());
        input.setAttribute("data-molsysviewer-list-search", this.domain);
        const status = document.createElement("div"); status.setAttribute("role", "status"); status.style.fontSize = "11px";
        const actions = document.createElement("div"); Object.assign(actions.style, { display: "flex", flexWrap: "wrap", gap: "5px" });
        const management = document.createElement("details"); management.open = this.batchOpen;
        management.setAttribute("data-molsysviewer-list-management", this.domain);
        const summary = document.createElement("summary"); summary.textContent = "Manage marked items";
        Object.assign(summary.style, { fontSize: "11px", cursor: "pointer" });
        management.append(summary, actions);
        const batchButtons: HTMLButtonElement[] = [];
        const matches = () => this.rows.filter(item => this.search.matches(`${item.tag} ${item.text}`));
        const refresh = () => {
            const visible = new Set(matches());
            for (const item of this.rows) { item.row.hidden = !visible.has(item); item.row.style.display = visible.has(item) ? item.display : "none"; }
            status.textContent = `${visible.size}/${this.rows.length} matches · ${this.marked.size} marked${visible.size === 0 && this.rows.length ? " · No matches" : ""}`;
            for (const button of batchButtons) button.disabled = !this.marked.size || this.pending !== null;
            mark.disabled = !visible.size || this.pending !== null;
            clear.disabled = !this.marked.size || this.pending !== null;
        };
        toolbar.append(input, status, management);
        const mark = makeButton("Mark matches", () => { for (const item of matches()) this.marked.add(item.tag); this.confirmation = null; this.repaint(); });
        const clear = makeButton("Clear marks", () => { this.marked.clear(); this.confirmation = null; this.repaint(); });
        mark.setAttribute("data-molsysviewer-list-mark-matches", this.domain);
        clear.setAttribute("data-molsysviewer-list-clear-marks", this.domain);
        mark.disabled = clear.disabled = this.pending !== null;
        actions.append(mark, clear);
        const operations = this.domain === "selections" ? ["delete"] : this.domain === "layers" ? ["show", "hide", "ungroup"] : ["show", "hide", "delete"];
        const submit = (operation: string, tags: string[]) => {
            this.pending = studioRequestId(`${this.domain}-batch`); this.message = "Working…"; this.confirmation = null;
            try { this.ctx.onAction("batch_scene_objects", { domain: this.domain, operation, tags, request_id: this.pending }); }
            catch (error) { this.pending = null; this.message = String(error); }
            this.repaint();
        };
        for (const operation of operations) {
            const button = makeButton(`${operation[0].toUpperCase()}${operation.slice(1)} marked`, () => {
                const tags = [...this.marked];
                if (operation === "delete") { this.confirmation = tags; this.repaint(); }
                else submit(operation, tags);
            });
            button.setAttribute("data-molsysviewer-list-batch", `${this.domain}:${operation}`);
            batchButtons.push(button); actions.appendChild(button);
        }
        if (this.confirmation) {
            const tags = this.confirmation.filter(tag => current.has(tag));
            const confirm = document.createElement("div"); confirm.setAttribute("data-molsysviewer-list-confirmation", this.domain);
            confirm.textContent = `Delete ${tags.length} marked ${this.domain}: ${tags.join(", ")}? This includes marked rows hidden by the search. ${this.domain === "interactions" ? "Stored analyses are kept. " : ""}This can be undone.`;
            const yes = makeButton("Confirm deletion", () => submit("delete", tags)); yes.disabled = !tags.length || this.pending !== null;
            confirm.append(yes, makeButton("Cancel", () => { this.confirmation = null; this.repaint(); })); management.appendChild(confirm);
        }
        if (this.message) { const note = document.createElement("div"); note.textContent = this.message; note.setAttribute("role", "status"); toolbar.appendChild(note); }
        for (const item of this.rows) {
            const label = document.createElement("label"); Object.assign(label.style, { fontSize: "11px", display: "flex", gap: "5px", alignItems: "center" });
            label.setAttribute("data-molsysviewer-mark-label", this.domain);
            label.style.display = this.batchOpen ? "flex" : "none";
            const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.checked = this.marked.has(item.tag); checkbox.disabled = this.pending !== null;
            checkbox.setAttribute("aria-label", `Mark ${this.domain}: ${item.tag}`);
            checkbox.setAttribute("data-molsysviewer-list-mark", `${this.domain}:${item.tag}`);
            label.addEventListener("click", event => event.stopPropagation());
            checkbox.onchange = () => {
                if (checkbox.checked) this.marked.add(item.tag); else this.marked.delete(item.tag);
                this.confirmation = null;
                management.querySelector('[data-molsysviewer-list-confirmation]')?.remove();
                refresh();
            };
            label.append(checkbox, "Mark"); item.row.prepend(label);
        }
        management.addEventListener("toggle", () => {
            this.batchOpen = management.open;
            for (const label of host.querySelectorAll<HTMLElement>('[data-molsysviewer-mark-label]')) label.style.display = this.batchOpen ? "flex" : "none";
        });
        if (this.rows.length) this.rows[0].row.before(toolbar);
        else host.appendChild(toolbar);
        refresh();
    }
}
