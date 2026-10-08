/** Keyboard and focus ownership for compact menus with in-card submenus. */
let nextMenuId = 0;

type MenuPage = { view: HTMLDivElement; parent?: MenuPage; trigger?: HTMLButtonElement };

export class MenuNavigation {
    private current!: MenuPage;
    private readonly pages: MenuPage[] = [];
    private readonly submenuOpeners = new WeakMap<HTMLButtonElement, () => void>();
    private readonly id = `msv-menu-${++nextMenuId}`;

    constructor(
        private readonly host: HTMLElement,
        private readonly dismiss: () => void,
        private readonly onLayout: () => void,
    ) {
        host.addEventListener("keydown", event => this.handleKeyDown(event));
    }

    reset(title: string): HTMLDivElement {
        this.host.replaceChildren();
        this.pages.length = 0;
        const page = this.createPage(title);
        this.current = page;
        page.view.style.display = "block";
        return page.view;
    }

    addSubmenu(parent: HTMLDivElement, title: string, build: (view: HTMLDivElement) => void): void {
        const parentPage = this.pages.find(page => page.view === parent);
        if (!parentPage) throw new Error("A submenu requires a registered parent menu");
        const page = this.createPage(title);
        page.parent = parentPage;
        const back = this.button("‹ Back");
        back.setAttribute("data-molsysviewer-menu-back", "true");
        back.addEventListener("click", () => this.back());
        page.view.appendChild(back);
        const heading = document.createElement("div");
        heading.textContent = title;
        heading.setAttribute("role", "presentation");
        Object.assign(heading.style, { padding: "6px 10px", fontWeight: "600" });
        page.view.appendChild(heading);
        build(page.view);

        // A hosting surface must not advertise a submenu containing no actions.
        if (this.buttons(page.view).length <= 1) {
            page.view.remove();
            this.pages.splice(this.pages.indexOf(page), 1);
            return;
        }
        const trigger = this.button(`${title} ›`);
        trigger.setAttribute("data-molsysviewer-context-submenu", title);
        trigger.setAttribute("aria-haspopup", "menu");
        trigger.setAttribute("aria-expanded", "false");
        trigger.setAttribute("aria-controls", page.view.id);
        page.trigger = trigger;
        const open = () => this.show(page);
        this.submenuOpeners.set(trigger, open);
        trigger.addEventListener("click", open);
        parent.appendChild(trigger);
    }

    decorate(): void {
        for (const page of this.pages) {
            for (const button of this.buttons(page.view, true)) {
                if (!button.getAttribute?.("role")) button.setAttribute("role", "menuitem");
                button.tabIndex = -1;
            }
        }
    }

    focusFirst(): void { this.buttons(this.current.view)[0]?.focus(); }

    back(): boolean {
        if (!this.current.parent) return false;
        const page = this.current;
        this.show(page.parent!);
        page.trigger?.focus();
        return true;
    }

    containsCurrentPage(): boolean { return this.host.contains(this.current.view); }

    private createPage(title: string): MenuPage {
        const view = document.createElement("div");
        view.id = `${this.id}-${this.pages.length}`;
        view.setAttribute("role", "menu");
        view.setAttribute("aria-label", title);
        view.setAttribute("data-molsysviewer-menu-page", title);
        view.style.display = "none";
        const page = { view };
        this.pages.push(page);
        this.host.appendChild(view);
        return page;
    }

    private show(page: MenuPage): void {
        for (const item of this.pages) {
            const active = item === page;
            item.view.style.display = active ? "block" : "none";
            item.trigger?.setAttribute("aria-expanded", active ? "true" : "false");
        }
        this.current = page;
        this.host.scrollTop = 0;
        this.onLayout();
        this.focusFirst();
    }

    private button(label: string): HTMLButtonElement {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute("role", "menuitem");
        button.tabIndex = -1;
        Object.assign(button.style, {
            display: "block", width: "100%", padding: "8px 10px", border: "0",
            borderRadius: "8px", background: "transparent", color: "inherit",
            textAlign: "left", cursor: "pointer",
        });
        return button;
    }

    private buttons(view: HTMLElement, includeDisabled = false): HTMLButtonElement[] {
        const items: HTMLButtonElement[] = [];
        const visit = (element: HTMLElement) => {
            if (element.style.display === "none") return;
            if (element.tagName === "BUTTON" && (includeDisabled || !(element as HTMLButtonElement).disabled)) {
                items.push(element as HTMLButtonElement);
            }
            for (const child of Array.from(element.children)) visit(child as HTMLElement);
        };
        // Hidden submenu pages still need their own contents indexed.
        for (const child of Array.from(view.children)) visit(child as HTMLElement);
        return items;
    }

    private handleKeyDown(event: KeyboardEvent): void {
        if ((event.target as HTMLElement)?.closest?.("input, textarea, select, [contenteditable]")) return;
        if (!this.containsCurrentPage()) return; // An inline editor owns its inputs.
        const items = this.buttons(this.current.view);
        const index = items.indexOf(document.activeElement as HTMLButtonElement);
        let next: number | undefined;
        if (event.key === "ArrowDown") next = (index + 1) % items.length;
        if (event.key === "ArrowUp") next = (index - 1 + items.length) % items.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = items.length - 1;
        if (next !== undefined) items[next]?.focus();
        else if (event.key === "ArrowRight") {
            const open = this.submenuOpeners.get(document.activeElement as HTMLButtonElement);
            if (!open) return;
            open();
        } else if (event.key === "ArrowLeft") this.back();
        else if (event.key === "Escape") { if (!this.back()) this.dismiss(); }
        else if (event.key === "Enter" || event.key === " ") items[index]?.click();
        else if (event.key === "Tab") { this.dismiss(); return; }
        else return;
        event.preventDefault();
        event.stopPropagation();
    }
}
