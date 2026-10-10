/** Unsaved secondary text fields, keyed by object and control rather than DOM nodes. */
export class EditorDrafts {
    private values = new Map<string, { tag: string; canonical: string; draft: string }>();
    pruneTargets(current: ReadonlySet<string>): void {
        for (const [key, value] of this.values) if (!current.has(value.tag)) this.values.delete(key);
    }
    mount(host: HTMLElement): void {
        if (typeof host.querySelectorAll !== "function") return;
        const current = new Set<string>();
        for (const field of host.querySelectorAll<HTMLInputElement>("input, textarea")) {
            if (field.type !== "text" && field.tagName !== "TEXTAREA") continue;
            const attr = Array.from(field.attributes).find(item => item.name.startsWith("data-molsysviewer-")
                && /-(rename(?:-input)?|layer(?:-input)?)$/.test(item.name));
            if (!attr) continue;
            const key = `${attr.name}:${attr.value}`; current.add(key);
            const canonical = field.value;
            const saved = this.values.get(key);
            if (saved?.canonical === canonical) field.value = saved.draft;
            else this.values.delete(key);
            field.addEventListener("input", () => this.values.set(key, { tag: attr.value, canonical, draft: field.value }));
        }
        // Cancelled editors and deleted/renamed objects cannot retain stale drafts.
        for (const key of this.values.keys()) if (!current.has(key)) this.values.delete(key);
    }
}
