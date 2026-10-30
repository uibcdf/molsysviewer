import type { SystemFileBrowseResult } from "../../messages/viewer-messages";
import type { PanelContext } from "./types";
import { makeButton } from "./ui-helpers";

/** A bounded Python-host directory view, or the Qt host's native picker reply. */
export class LoadFilePicker {
    readonly root = document.createElement("div");
    private readonly path = document.createElement("input");
    private readonly hidden = document.createElement("input");
    private readonly entries = document.createElement("div");
    private readonly status = document.createElement("div");
    private readonly choose: HTMLButtonElement;
    private readonly next: HTMLButtonElement;
    private readonly parent: HTMLButtonElement;
    private readonly go: HTMLButtonElement;
    private pending: string | null = null;
    private directory = "";
    private parentPath: string | null = null;
    private cursor: [number, string, string] | null = null;
    private selected = new Set<string>();

    constructor(private ctx: PanelContext, private onPick: (paths: string[]) => void, private onClose: () => void) {
        this.root.setAttribute("data-molsysviewer-load-file-picker", "true");
        this.root.tabIndex = -1;
        this.root.addEventListener("keydown", event => {
            if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); this.close(); }
        });
        Object.assign(this.root.style, { display: "none", flex: "1 1 0", minHeight: "0", flexDirection: "column", gap: "6px" });
        const title = document.createElement("div");
        title.textContent = "Files on the machine running Python";
        title.style.fontWeight = "700";
        title.title = "Choosing files fills the inputs; it does not load them.";
        this.path.setAttribute("aria-label", "Python directory");
        this.path.type = "text";
        Object.assign(this.path.style, { width: "100%", minWidth: "0", boxSizing: "border-box", padding: "4px", color: "#f4f4f5", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "4px" });
        this.path.addEventListener("keydown", event => {
            if (event.key === "Enter") { event.preventDefault(); this.request(this.path.value); }
        });
        const navigation = document.createElement("div");
        Object.assign(navigation.style, { display: "flex", gap: "6px", flexWrap: "wrap" });
        this.go = makeButton("Open folder", () => this.request(this.path.value));
        this.parent = makeButton("Parent folder", () => { if (this.parentPath) this.request(this.parentPath); });
        const hiddenLabel = document.createElement("label");
        this.hidden.type = "checkbox";
        this.hidden.addEventListener("change", () => this.request(this.directory));
        hiddenLabel.append(this.hidden, document.createTextNode(" Show hidden files"));
        navigation.append(this.go, this.parent, hiddenLabel);
        Object.assign(this.entries.style, { flex: "1 1 0", minHeight: "0", overflowY: "auto", display: "flex", flexDirection: "column", gap: "3px" });
        this.entries.setAttribute("aria-label", "Python files and folders");
        this.status.setAttribute("role", "status");
        Object.assign(this.status.style, { fontSize: "11px", maxHeight: "48px", overflowY: "auto", overflowWrap: "anywhere" });
        const footer = document.createElement("div");
        Object.assign(footer.style, { flexShrink: "0", display: "flex", flexWrap: "wrap", gap: "6px" });
        this.choose = makeButton("Use selected files", () => {
            const paths = Array.from(this.selected);
            if (paths.length) { this.close(); this.onPick(paths); }
        });
        this.next = makeButton("Next page", () => { if (this.cursor) this.request(this.directory, this.cursor); });
        footer.append(this.choose, this.next, makeButton("Cancel", () => this.close()));
        this.root.append(title, this.path, navigation, this.entries, this.status, footer);
    }

    open(): void {
        this.selected.clear();
        this.root.style.display = "flex";
        this.entries.replaceChildren();
        this.root.focus({ preventScroll: true });
        this.request(this.directory);
    }

    private close(): void {
        this.pending = null;
        this.root.style.display = "none";
        this.onClose();
    }

    private request(directory: string, after?: [number, string, string]): void {
        if (this.pending) return;
        this.pending = `files-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        this.status.textContent = "Choosing files…";
        this.refreshControls();
        try {
            this.ctx.onAction("browse_load_files", { request_id: this.pending, directory, show_hidden: this.hidden.checked, after });
        } catch (error) {
            this.update({ op: "system_file_browse_result", request_id: this.pending, ok: false, error_message: String(error) });
        }
    }

    update(result: SystemFileBrowseResult): void {
        if (result.request_id !== this.pending) return;
        this.pending = null;
        if (!result.ok) {
            this.status.textContent = result.error_message || "Could not browse this directory.";
        } else if (result.kind === "selection") {
            const paths = result.paths ?? [];
            this.close();
            if (paths.length) this.onPick(paths);
        } else {
            this.directory = result.directory ?? "";
            this.path.value = this.directory;
            this.parentPath = result.parent ?? null;
            this.cursor = result.next_cursor ?? null;
            this.entries.replaceChildren();
            for (const entry of result.entries ?? []) {
                if (entry.is_directory) {
                    const button = makeButton(entry.name + "/", () => this.request(entry.path));
                    button.title = entry.path;
                    button.style.textAlign = "left";
                    button.style.flex = "0 0 auto";
                    this.entries.appendChild(button);
                } else {
                    const label = document.createElement("label");
                    label.title = entry.path;
                    label.style.overflowWrap = "anywhere";
                    const check = document.createElement("input"); check.type = "checkbox";
                    check.checked = this.selected.has(entry.path);
                    check.addEventListener("change", () => {
                        if (check.checked) this.selected.add(entry.path); else this.selected.delete(entry.path);
                        this.refreshControls();
                        this.status.textContent = `${this.selected.size} file(s) selected.`;
                    });
                    label.append(check, document.createTextNode(" " + entry.name));
                    this.entries.appendChild(label);
                }
            }
            this.status.textContent = `${this.selected.size} file(s) selected.`;
            if (this.root.contains(document.activeElement)) this.path.focus({ preventScroll: true });
        }
        this.refreshControls();
    }

    private refreshControls(): void {
        const busy = this.pending !== null;
        this.path.disabled = this.hidden.disabled = this.go.disabled = busy;
        this.parent.disabled = busy || !this.parentPath;
        this.next.disabled = busy || !this.cursor;
        this.next.style.display = this.cursor ? "" : "none";
        this.choose.disabled = busy || !this.selected.size;
    }
}
