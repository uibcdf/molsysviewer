import type { SystemSyncStateMessage } from "../messages/viewer-messages";

/** Stops old-index interaction while Python reconciles a scientific edit. */
export class SystemSyncOverlay {
    private readonly root = document.createElement("div");
    private readonly text = document.createElement("p");
    private readonly update = document.createElement("button");
    private readonly readerHost = document.createElement("section");
    private reader: HTMLElement | null = null;
    private readerSlot: Comment | null = null;
    private state: SystemSyncStateMessage["state"] = "synchronized";
    private readonly previousInert = new Map<HTMLElement, boolean>();
    private previousFocus: HTMLElement | null = null;
    private readonly guardKey = (event: KeyboardEvent) => {
        const target = event.composedPath()[0] as Node;
        if (this.root.style.display !== "none" && this.host.contains(target)) {
            // Let reader inputs receive their own events; the sheet's bubble
            // listener stops them before Mol*'s window-level key observers.
            if (this.root.contains(target)) return;
            event.stopImmediatePropagation();
        }
    };

    constructor(private readonly host: HTMLElement, onUpdate: () => void) {
        this.root.setAttribute("data-molsysviewer-system-sync", "true");
        this.root.setAttribute("role", "region");
        this.root.setAttribute("aria-label", "Molecular system update");
        this.text.setAttribute("role", "status");
        this.text.setAttribute("aria-live", "polite");
        Object.assign(this.root.style, {
            display: "none", position: "absolute", inset: "0", zIndex: "1000",
            alignItems: "center", justifyContent: "center", flexDirection: "column",
            padding: "24px", boxSizing: "border-box", textAlign: "center",
            background: "rgba(25, 28, 32, 0.88)", color: "#f3f4f6",
            fontFamily: "system-ui, sans-serif", fontSize: "14px", gap: "12px",
        });
        Object.assign(this.text.style, { margin: "0", flexShrink: "0" });
        this.root.tabIndex = -1;
        this.readerHost.setAttribute("data-molsysviewer-sync-reader", "true");
        this.readerHost.setAttribute("aria-label", "Inspect the updated molecular system");
        Object.assign(this.readerHost.style, {
            display: "none", width: "100%", maxWidth: "720px", minHeight: "0",
            overflow: "auto", textAlign: "left", background: "#242a31",
            border: "1px solid rgba(255,255,255,0.18)", borderRadius: "10px",
            padding: "16px", boxSizing: "border-box", flex: "0 1 auto",
        });
        this.update.textContent = "Update view";
        this.update.type = "button";
        Object.assign(this.update.style, {
            padding: "8px 16px", borderRadius: "8px", border: "1px solid #7c8da4",
            background: "#394a61", color: "#fff", font: "inherit", cursor: "pointer", flexShrink: "0",
        });
        this.update.addEventListener("click", () => {
            this.update.disabled = true;
            onUpdate();
        });
        this.root.append(this.text, this.update, this.readerHost);
        for (const name of ["keydown", "keyup", "keypress", "pointerdown", "pointerup", "pointermove",
            "mousedown", "mouseup", "mousemove", "click", "dblclick", "contextmenu", "wheel", "touchstart", "touchmove"]) {
            this.root.addEventListener(name, event => event.stopPropagation());
        }
        this.host.appendChild(this.root);
        for (const name of ["keydown", "keyup", "keypress"]) window.addEventListener(name, this.guardKey as EventListener, true);
    }

    setState(message: SystemSyncStateMessage): void {
        const state = message.state;
        const active = this.activeElement();
        this.state = state;
        if (state === "synchronized") {
            this.restoreReader();
            this.root.style.display = "none";
            this.restoreInteraction();
            if (active instanceof HTMLElement && this.reader?.contains(active)) active.focus({ preventScroll: true });
            return;
        }
        if (this.root.style.display === "none") {
            this.previousFocus = active instanceof HTMLElement ? active : null;
        }
        this.root.style.display = "flex";
        this.updateReader();
        for (const child of Array.from(this.host.children)) {
            if (!(child instanceof HTMLElement) || child === this.root) continue;
            if (!this.previousInert.has(child)) this.previousInert.set(child, child.inert);
            child.inert = true;
        }
        const retry = state === "pending" || state === "sync_failed";
        this.text.textContent = state === "pending" ? "The molecular system has changed. Update the view to continue."
            : state === "sync_failed" ? "The molecular edit is complete. Retry the view update to continue."
                : state === "uncertain" ? "The edit could not be verified. Replace the system explicitly to continue."
                    : state === "closed" ? "This view is closed." : "Updating the molecular system…";
        if (retry && this.readerSlot) {
            this.text.textContent += " You can still inspect the updated system below; the scene remains paused.";
        }
        this.update.style.display = retry ? "block" : "none";
        this.update.disabled = !retry;
        if (this.previousFocus && this.host.contains(this.previousFocus) && !this.root.contains(this.activeElement())) {
            (retry ? this.update : this.root).focus({ preventScroll: true });
        }
    }

    /** Host-owned, already mounted reader; never mounts or navigates an addon. */
    setReader(reader: HTMLElement | null): void {
        this.restoreReader();
        this.reader = reader;
        this.updateReader();
    }

    private updateReader(): void {
        if ((this.state !== "pending" && this.state !== "sync_failed") || !this.reader) {
            this.restoreReader();
            return;
        }
        if (!this.readerSlot && this.host.contains(this.reader) && this.reader.parentNode) {
            const active = this.activeElement();
            this.readerSlot = document.createComment("mounted addon reader");
            this.reader.before(this.readerSlot);
            this.readerHost.appendChild(this.reader);
            this.readerHost.scrollTop = 0;
            this.readerHost.style.display = "block";
            if (active instanceof HTMLElement && this.reader.contains(active)) active.focus({ preventScroll: true });
        }
    }

    private restoreReader(): void {
        if (this.readerSlot) {
            const active = this.activeElement();
            if (this.reader && this.readerSlot.parentNode) this.readerSlot.replaceWith(this.reader);
            else this.reader?.remove();
            this.readerSlot.remove();
            this.readerSlot = null;
            if (active instanceof HTMLElement && this.reader?.contains(active)) active.focus({ preventScroll: true });
        }
        this.readerHost.style.display = "none";
    }

    private restoreInteraction(): void {
        for (const [element, previous] of this.previousInert) element.inert = previous;
        this.previousInert.clear();
        if (this.root.contains(this.activeElement()) && this.previousFocus?.isConnected) {
            this.previousFocus.focus({ preventScroll: true });
        }
        this.previousFocus = null;
    }

    private activeElement(): Element | null {
        return (this.host.getRootNode() as Document | ShadowRoot).activeElement;
    }

    dispose(): void {
        for (const name of ["keydown", "keyup", "keypress"]) window.removeEventListener(name, this.guardKey as EventListener, true);
        this.restoreReader();
        this.reader = null;
        this.restoreInteraction();
        this.root.remove();
    }
}
