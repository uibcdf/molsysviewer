import type { SystemSyncStateMessage } from "../messages/viewer-messages";

/** Stops old-index interaction while Python reconciles a scientific edit. */
export class SystemSyncOverlay {
    private readonly root = document.createElement("div");
    private readonly text = document.createElement("p");
    private readonly update = document.createElement("button");
    private readonly previousInert = new Map<HTMLElement, boolean>();
    private previousFocus: HTMLElement | null = null;
    private readonly guardKey = (event: KeyboardEvent) => {
        if (this.root.style.display !== "none" && this.host.contains(event.target as Node)) {
            // Mol* also observes window keys. Keep native button/Tab defaults,
            // while preventing scene shortcuts behind the pending-state sheet.
            event.stopImmediatePropagation();
        }
    };

    constructor(private readonly host: HTMLElement, onUpdate: () => void) {
        this.root.setAttribute("data-molsysviewer-system-sync", "true");
        this.root.setAttribute("role", "status");
        this.root.setAttribute("aria-live", "polite");
        Object.assign(this.root.style, {
            display: "none", position: "absolute", inset: "0", zIndex: "1000",
            alignItems: "center", justifyContent: "center", flexDirection: "column",
            padding: "24px", boxSizing: "border-box", textAlign: "center",
            background: "rgba(25, 28, 32, 0.88)", color: "#f3f4f6",
            fontFamily: "system-ui, sans-serif", fontSize: "14px", gap: "12px",
        });
        this.root.tabIndex = -1;
        this.update.textContent = "Update view";
        this.update.type = "button";
        this.update.addEventListener("click", () => {
            this.update.disabled = true;
            onUpdate();
        });
        this.root.append(this.text, this.update);
        this.host.appendChild(this.root);
        for (const name of ["keydown", "keyup", "keypress"]) window.addEventListener(name, this.guardKey as EventListener, true);
    }

    setState(message: SystemSyncStateMessage): void {
        const state = message.state;
        if (state === "synchronized") {
            this.root.style.display = "none";
            this.restoreInteraction();
            return;
        }
        if (this.root.style.display === "none") {
            this.previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        }
        for (const child of Array.from(this.host.children)) {
            if (!(child instanceof HTMLElement) || child === this.root) continue;
            if (!this.previousInert.has(child)) this.previousInert.set(child, child.inert);
            child.inert = true;
        }
        this.root.style.display = "flex";
        const retry = state === "pending" || state === "sync_failed";
        this.text.textContent = state === "pending" ? "The molecular system has changed. Update the view to continue."
            : state === "sync_failed" ? "The molecular edit is complete. Retry the view update to continue."
                : state === "uncertain" ? "The edit could not be verified. Replace the system explicitly to continue."
                    : state === "closed" ? "This view is closed." : "Updating the molecular system…";
        this.update.style.display = retry ? "block" : "none";
        this.update.disabled = !retry;
        if (this.previousFocus && this.host.contains(this.previousFocus) && !this.root.contains(document.activeElement)) {
            (retry ? this.update : this.root).focus({ preventScroll: true });
        }
    }

    private restoreInteraction(): void {
        for (const [element, previous] of this.previousInert) element.inert = previous;
        this.previousInert.clear();
        if (this.root.contains(document.activeElement) && this.previousFocus?.isConnected) {
            this.previousFocus.focus({ preventScroll: true });
        }
        this.previousFocus = null;
    }

    dispose(): void {
        for (const name of ["keydown", "keyup", "keypress"]) window.removeEventListener(name, this.guardKey as EventListener, true);
        this.restoreInteraction();
        this.root.remove();
    }
}
