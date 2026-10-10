import type { PanelAction, PanelContext } from "./types";
import type { StudioActionResult } from "./saved-list-tools";
import { makeButton, makeCheckboxRow, makeStyledSelect, studioRequestId, workflowHelp } from "./ui-helpers";

/** Persistent file draft. File bytes stay in Python, not in the widget transport. */
export class WorkFileControls {
    readonly root = document.createElement("div");
    private kind: HTMLSelectElement;
    private path = document.createElement("input");
    private description = document.createElement("div");
    private status = document.createElement("div");
    private confirmation = document.createElement("div");
    private save: HTMLButtonElement;
    private restore: HTMLButtonElement;
    private overwrite: HTMLInputElement;
    private systemLoaded = false;
    private pending: { id: string; action: PanelAction; path: string; kind: string } | null = null;

    constructor(private ctx: PanelContext, private hasAuthority: boolean) {
        this.root.setAttribute("data-molsysviewer-work-files", "true");
        Object.assign(this.root.style, { display: "flex", flexDirection: "column", gap: "8px", padding: "10px", fontSize: "11px",
            borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.035)" });
        this.kind = makeStyledSelect([
            { value: "state", label: "Scene state · JSON" },
            { value: "session", label: "Session · MSV · experimental" },
        ], "state", () => { this.cancelConfirmation(); this.update(); });
        this.kind.setAttribute("aria-label", "Work file format");
        this.path.type = "text";
        this.path.setAttribute("aria-label", "Path in Python session");
        this.path.setAttribute("data-molsysviewer-work-file-path", "true");
        this.path.addEventListener("input", () => { this.cancelConfirmation(); this.update(); });
        const pathLabel = document.createElement("label"); pathLabel.textContent = "Path in Python session"; pathLabel.appendChild(this.path);
        Object.assign(this.path.style, { display: "block", boxSizing: "border-box", width: "100%", marginTop: "4px",
            background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "6px",
            padding: "4px 6px", color: "#fff", fontSize: "11px" });
        const location = document.createElement("div");
        location.textContent = "Paths refer to files on the machine running Python. Relative paths use its working directory; this is not a browser upload or download.";
        location.style.color = "rgba(244,244,245,0.65)";
        const overwriteRow = makeCheckboxRow("Allow overwriting an existing file", false, () => {});
        this.overwrite = overwriteRow.querySelector<HTMLInputElement>("input")!;
        this.overwrite.setAttribute("aria-label", "Allow overwriting an existing file");
        this.save = makeButton("Save file", () => this.submit("save_work_file"));
        this.save.setAttribute("data-molsysviewer-work-file-save", "true");
        this.restore = makeButton("Restore file…", () => this.askRestore());
        this.restore.setAttribute("data-molsysviewer-work-file-restore", "true");
        this.status.setAttribute("data-molsysviewer-work-file-status", "true");
        this.status.setAttribute("role", "status");
        this.status.style.overflowWrap = "anywhere";
        this.root.append(this.kind, this.description, pathLabel, location, overwriteRow, this.save, this.restore,
            this.confirmation, this.status, workflowHelp("work-files", [
                "State example: review.json saves scene settings and objects. Restore it after loading the matching molecular system; it contains no coordinates or calculated analyses.",
                "Session example: review.msv saves the molecular system, all loaded structures, named interaction analyses and scene. MSV is experimental, may be large, and is not an archival format.",
                "Restoration replaces the saved scene and clears Undo/Redo. Session restoration also replaces the molecular system. Save your current work first if you need to return to it.",
            ]));
        this.update();
    }

    setSystemLoaded(loaded: boolean): void { this.systemLoaded = loaded; this.update(); }

    updateResult(result: StudioActionResult): boolean {
        const request = this.pending;
        if (!request || result.request_id !== request.id || result.action !== request.action || result.domain !== "export") return false;
        this.pending = null;
        this.status.setAttribute("role", result.ok ? "status" : "alert");
        this.status.textContent = result.ok
            ? `${request.action === "save_work_file" ? "Saved" : "Restored"} ${request.kind === "state" ? "scene state" : "experimental session"}: ${request.path}`
            : result.error_message || "File operation failed. Your path is kept.";
        this.update();
        return request.action === "restore_work_file";
    }

    private cancelConfirmation(): void { this.confirmation.replaceChildren(); }

    private askRestore(): void {
        if (this.restore.disabled) return;
        this.cancelConfirmation();
        const text = document.createElement("div");
        text.textContent = `Restore ${this.path.value.trim()}? This replaces ${this.kind.value === "session" ? "the molecular system and scene" : "the scene on the current molecular system"} and clears Undo/Redo. Save current work first to keep it.`;
        const accept = makeButton("Confirm restore", () => this.submit("restore_work_file"));
        accept.setAttribute("data-molsysviewer-work-file-confirm", "true");
        this.confirmation.append(text, accept, makeButton("Cancel", () => this.cancelConfirmation()));
        accept.focus();
    }

    private submit(action: "save_work_file" | "restore_work_file"): void {
        if (this.pending || !this.hasAuthority || !this.path.value.trim()) return;
        const path = this.path.value.trim(), kind = this.kind.value;
        this.pending = { id: studioRequestId(action), action, path, kind };
        this.cancelConfirmation();
        this.status.setAttribute("role", "status");
        this.status.textContent = action === "save_work_file" ? "Saving…" : "Restoring…";
        this.update();
        try {
            this.ctx.onAction(action, { request_id: this.pending.id, file_kind: kind, path,
                ...(action === "save_work_file" ? { overwrite: this.overwrite.checked } : { confirmed: true }) });
        } catch (error) {
            this.pending = null; this.status.setAttribute("role", "alert"); this.status.textContent = String(error); this.update();
        }
    }

    private update(): void {
        const session = this.kind.value === "session", busy = this.pending !== null;
        this.description.textContent = session
            ? "Experimental MSV: molecular system, structures, named analyses and scene. Future versions may reject older session files."
            : "JSON: scene settings and objects. Restore on the matching molecular system; molecular data and analyses are not included.";
        this.path.placeholder = session ? "review.msv" : "review.json";
        for (const control of [this.kind, this.path, this.overwrite]) control.disabled = busy || !this.hasAuthority;
        const missingPath = !this.path.value.trim();
        this.save.disabled = busy || !this.hasAuthority || missingPath || (session && !this.systemLoaded);
        this.restore.disabled = busy || !this.hasAuthority || missingPath || (!session && !this.systemLoaded);
        this.save.title = !this.hasAuthority ? "Requires a live Python session." : session && !this.systemLoaded ? "Load a molecular system before saving a session." : "Save to the Python filesystem.";
        this.restore.title = !this.hasAuthority ? "Requires a live Python session." : !session && !this.systemLoaded ? "Load the matching molecular system first." : "Review confirmation before replacing current work.";
        if (!this.hasAuthority) this.status.textContent = "Saving and restoring work requires a live Python session. PNG download remains available.";
    }
}
