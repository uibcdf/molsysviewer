/** Persist native disclosure state independently of DOM reconstruction. */
export class PanelDisclosures {
    private states = new Map<string, boolean>();
    private mounted = new Map<string, boolean>();
    private host?: HTMLElement;
    openCreation(): void {
        this.states.set("creation", true);
        const current = this.host?.querySelector<HTMLDetailsElement>('details[data-molsysviewer-disclosure="creation"]');
        if (current) current.open = true;
    }
    capture(): void {
        if (!this.host?.querySelectorAll) return;
        for (const item of this.host.querySelectorAll<HTMLDetailsElement>("details[data-molsysviewer-disclosure]")) {
            const key = item.dataset.molsysviewerDisclosure!;
            if (this.states.has(key) || item.open !== this.mounted.get(key)) this.states.set(key, item.open);
        }
    }
    mount(host: HTMLElement, defaultOpen: boolean): void {
        this.host = host;
        if (typeof host.querySelectorAll !== "function") return;
        const heading = Array.from(host.children).find(node => node.getAttribute("data-molsysviewer-section-heading")?.startsWith("New "));
        if (!heading) return;
        const details = document.createElement("details"); details.setAttribute("data-molsysviewer-disclosure", "creation");
        details.open = this.states.get("creation") ?? defaultOpen;
        const summary = document.createElement("summary"); summary.textContent = heading.textContent;
        Object.assign(summary.style, { fontSize: "13px", fontWeight: "600", padding: "6px 0", cursor: "pointer" });
        details.appendChild(summary); heading.before(details);
        summary.addEventListener("click", () => this.states.set("creation", !details.open));
        let node = heading.nextElementSibling;
        while (node && !node.hasAttribute("data-molsysviewer-section-heading")) {
            const next = node.nextElementSibling; details.appendChild(node); node = next;
        }
        heading.remove();
        for (const item of host.querySelectorAll<HTMLDetailsElement>("details[data-molsysviewer-disclosure]")) {
            const saved = this.states.get(item.dataset.molsysviewerDisclosure!);
            if (saved !== undefined) item.open = saved;
            this.mounted.set(item.dataset.molsysviewerDisclosure!, item.open);
        }
    }
}

/** Optional fields use the same native disclosure as creation sections. */
export function advancedFields(key: string, ...children: HTMLElement[]): HTMLDetailsElement {
    const details = document.createElement("details");
    details.setAttribute("data-molsysviewer-disclosure", key);
    const summary = document.createElement("summary"); summary.textContent = "Advanced options";
    Object.assign(summary.style, { fontSize: "11px", cursor: "pointer", padding: "5px 0" });
    details.append(summary, ...children);
    return details;
}
