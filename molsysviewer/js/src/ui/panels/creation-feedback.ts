import type { PanelAction, PanelContext } from "./types";
import type { StudioActionResult } from "./saved-list-tools";
import { studioRequestId } from "./ui-helpers";

/** A creation draft belongs to the panel until its matching backend reply succeeds. */
export class CreationFeedback {
    private request: string | null = null;
    private message = "";
    private failed = false;
    constructor(private action: PanelAction, private domain: string, private pendingText = "Creating…") {}
    get pending(): boolean { return this.request !== null; }
    submit(details: Record<string, unknown>, emit: PanelContext["onAction"]): void {
        if (this.pending) return;
        this.request = studioRequestId(this.action);
        this.message = this.pendingText; this.failed = false;
        try { emit(this.action, { ...details, request_id: this.request }); }
        catch (error) { this.request = null; this.message = String(error); this.failed = true; }
    }
    update(result: StudioActionResult): "success" | "failure" | null {
        if (!this.request || result.request_id !== this.request || result.action !== this.action || result.domain !== this.domain) return null;
        this.request = null; this.failed = !result.ok;
        this.message = result.ok ? "Created." : result.error_message || "Creation failed. Your draft is kept.";
        return result.ok ? "success" : "failure";
    }
    mount(parent: HTMLElement): void {
        if (this.pending && typeof parent.querySelectorAll === "function") {
            for (const control of parent.querySelectorAll<HTMLInputElement | HTMLButtonElement | HTMLSelectElement | HTMLTextAreaElement>("input, button, select, textarea")) control.disabled = true;
        }
        if (this.message) {
            const status = document.createElement("div"); status.textContent = this.message;
            status.setAttribute("role", this.failed ? "alert" : "status");
            status.setAttribute("data-molsysviewer-creation-status", this.domain);
            parent.style.flexWrap = "wrap";
            Object.assign(status.style, { fontSize: "11px", overflowWrap: "anywhere", width: "100%", flexBasis: "100%", gridColumn: "1 / -1" });
            parent.appendChild(status);
        }
    }
}
