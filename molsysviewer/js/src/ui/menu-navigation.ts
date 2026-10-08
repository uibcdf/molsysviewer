/** Layout, keyboard and focus ownership for one adaptive secondary menu. */
let nextMenuId = 0;

const unavailableItems = new WeakSet<HTMLButtonElement>();

export function isMenuItemDisabled(button: HTMLButtonElement): boolean {
    return button.disabled || unavailableItems.has(button);
}

/** Menu items remain focusable; native form controls retain native disabled. */
export function setMenuItemDisabled(button: HTMLButtonElement, disabled: boolean): void {
    button.disabled = false;
    if (disabled) unavailableItems.add(button);
    else unavailableItems.delete(button);
    button.setAttribute("aria-disabled", disabled ? "true" : "false");
    button.style.opacity = disabled ? "0.45" : "1";
}

type MenuPage = {
    view: HTMLDivElement;
    parent?: MenuPage;
    trigger?: HTMLButtonElement;
    back?: HTMLButtonElement;
    hint?: HTMLDivElement;
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), Math.max(min, max));

export class MenuNavigation {
    private current!: MenuPage;
    private readonly pages: MenuPage[] = [];
    private readonly submenuOpeners = new WeakMap<HTMLButtonElement, () => void>();
    private readonly id = `msv-menu-${++nextMenuId}`;
    private editor?: { page: MenuPage; contents?: Element[]; title: string };

    constructor(
        private readonly host: HTMLElement,
        private readonly dismiss: () => void,
        private readonly onLayout: () => void,
    ) {
        host.addEventListener("keydown", event => this.handleKeyDown(event));
        host.addEventListener("focusin", () => this.updateHint());
        host.addEventListener("scroll", () => this.onLayout(), true);
    }

    reset(title: string): HTMLDivElement {
        this.host.replaceChildren();
        this.pages.length = 0;
        this.editor = undefined;
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
        page.back = back;
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
        trigger.addEventListener("click", () => {
            if (this.current === page) {
                this.restoreEditor();
                this.show(parentPage);
                trigger.focus();
            } else open();
        });
        parent.appendChild(trigger);
    }

    decorate(): void {
        for (const page of this.pages) {
            for (const button of this.buttons(page.view, true)) {
                if (!button.getAttribute?.("role")) button.setAttribute("role", "menuitem");
                button.tabIndex = -1;
                if (button.disabled) setMenuItemDisabled(button, true);
            }
            if (!page.hint) {
                // A reason must not move an action between pointerdown and
                // click when focus leaves an unavailable item.
                const hintAnchor = document.createElement("div");
                Object.assign(hintAnchor.style, { position: "sticky", bottom: "0", height: "0", pointerEvents: "none" });
                page.hint = document.createElement("div");
                page.hint.id = `${page.view.id}-reason`;
                page.hint.setAttribute("data-molsysviewer-menu-disabled-reason", "true");
                page.hint.setAttribute("role", "note");
                page.hint.setAttribute("aria-live", "polite");
                Object.assign(page.hint.style, { display: "none", position: "absolute", bottom: "0", left: "0", right: "0",
                    background: "#222226", padding: "8px", fontSize: "12px", borderTop: "1px solid rgba(255,255,255,0.12)" });
                hintAnchor.appendChild(page.hint);
                page.view.appendChild(hintAnchor);
            }
            for (const button of this.buttons(page.view, true)) {
                button.setAttribute("aria-describedby", page.hint.id);
            }
        }
    }

    focusFirst(): void { this.buttons(this.current.view)[0]?.focus(); }

    back(): boolean {
        if (this.editor) {
            const page = this.editor.page;
            this.restoreEditor();
            this.show(page.parent && !this.pages.includes(page) ? page.parent : page);
            return true;
        }
        if (!this.current.parent) return false;
        const page = this.current;
        this.show(page.parent!);
        page.trigger?.focus();
        return true;
    }

    containsCurrentPage(): boolean { return this.host.contains(this.current.view); }

    /** Replace secondary contents with a nonmodal form; retain the root card. */
    beginEditor(title: string): HTMLDivElement {
        this.restoreEditor();
        const page = this.current.parent ? this.current : this.createPage(title);
        if (!page.parent) page.parent = this.pages[0];
        this.editor = { page, contents: page === this.current ? Array.from(page.view.children) : undefined,
            title: page.view.getAttribute?.("aria-label") || title };
        page.view.replaceChildren();
        page.view.setAttribute("role", "dialog");
        page.view.setAttribute("aria-modal", "false");
        page.view.setAttribute("aria-label", title);
        this.current = page;
        this.onLayout();
        return page.view;
    }

    /** Cards are bounded to the actual hosting canvas, including popouts. */
    layout(width: number, height: number, anchorX: number, anchorY: number): { left: number; top: number; width: number; height: number } {
        const margin = 4;
        const cardWidth = Math.min(260, Math.max(0, width - 2 * margin));
        const maxHeight = Math.max(0, height - 2 * margin);
        const lateral = width >= 2 * cardWidth + 2 * margin - 1;
        const main = this.pages[0];
        const child = this.current.parent ? this.current : undefined;
        for (const page of this.pages) {
            page.view.style.display = page === this.current || (lateral && page === main) ? "block" : "none";
            page.view.style.width = `${cardWidth}px`;
            page.view.style.maxHeight = `${maxHeight}px`;
            if (page.back) page.back.style.display = lateral ? "none" : "block";
            page.trigger?.setAttribute("aria-expanded", page === child ? "true" : "false");
        }
        let mainLeft = clamp(anchorX, margin, width - cardWidth - margin);
        const rightLimit = width - 2 * cardWidth - margin + 1;
        const leftLimit = cardWidth + margin - 1;
        // Reserve a viable lateral position when opening the root so that
        // opening a child does not shift its parent under the pointer.
        if (lateral && mainLeft > rightLimit && mainLeft < leftLimit) {
            mainLeft = mainLeft - rightLimit <= leftLimit - mainLeft ? rightLimit : leftLimit;
        }
        const mainHeight = (lateral || !child ? main.view : child.view).offsetHeight || 0;
        const mainTop = clamp(anchorY, margin, height - mainHeight - margin);
        let childLeft = mainLeft, childTop = mainTop;
        let childHeight = child?.view.offsetHeight || 0;
        if (child && lateral) {
            childLeft = mainLeft <= rightLimit ? mainLeft + cardWidth - 1 : mainLeft - cardWidth + 1;
            childTop = clamp(mainTop + (child.trigger?.offsetTop || 0) - (main.view.scrollTop || 0),
                margin, height - childHeight - margin);
        }
        if (!child) childHeight = 0;
        const left = child && lateral ? Math.min(mainLeft, childLeft) : mainLeft;
        const top = child && lateral ? Math.min(mainTop, childTop) : mainTop;
        main.view.style.left = `${mainLeft - left}px`;
        main.view.style.top = `${mainTop - top}px`;
        if (child) {
            child.view.style.left = `${childLeft - left}px`;
            child.view.style.top = `${childTop - top}px`;
        }
        this.host.setAttribute("data-molsysviewer-menu-layout", lateral ? "lateral" : "inline");
        return { left, top, width: child && lateral ? 2 * cardWidth - 1 : cardWidth,
            height: Math.max(mainTop + mainHeight, childTop + childHeight) - top };
    }

    refreshAvailability(): void { this.updateHint(); }

    private restoreEditor(): void {
        if (!this.editor) return;
        const { page, contents, title } = this.editor;
        if (contents) {
            page.view.replaceChildren(...contents);
            page.view.setAttribute("role", "menu");
            page.view.setAttribute("aria-label", title);
            page.view.removeAttribute?.("aria-modal");
        } else {
            page.view.remove();
            this.pages.splice(this.pages.indexOf(page), 1);
            this.current = page.parent!;
        }
        this.editor = undefined;
    }

    private updateHint(): void {
        if (this.editor) return;
        const focused = document.activeElement as HTMLButtonElement;
        let changed = false;
        for (const page of this.pages) {
            if (!page.hint) continue;
            const reason = page.view.contains(focused) && isMenuItemDisabled(focused)
                ? focused.title || "This action is unavailable for the current target." : "";
            if (page.hint.textContent !== reason) { page.hint.textContent = reason; changed = true; }
            page.hint.style.display = reason ? "block" : "none";
        }
        if (changed) this.onLayout();
    }

    private createPage(title: string): MenuPage {
        const view = document.createElement("div");
        view.id = `${this.id}-${this.pages.length}`;
        view.setAttribute("role", "menu");
        view.setAttribute("aria-label", title);
        view.setAttribute("data-molsysviewer-menu-page", title);
        view.style.display = "none";
        Object.assign(view.style, { position: "absolute", boxSizing: "border-box", padding: "6px",
            overflowY: "auto", overflowX: "hidden", pointerEvents: "auto", borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.15)", background: "rgba(26,26,30,0.96)",
            boxShadow: "0 16px 40px rgba(0,0,0,0.35)", scrollbarWidth: "thin",
            scrollbarColor: "rgba(255,255,255,0.25) transparent" });
        const page = { view };
        this.pages.push(page);
        this.host.appendChild(view);
        return page;
    }

    private show(page: MenuPage): void {
        this.restoreEditor();
        for (const item of this.pages) {
            const active = item === page;
            item.view.style.display = active ? "block" : "none";
            item.trigger?.setAttribute("aria-expanded", active ? "true" : "false");
        }
        this.current = page;
        if (page.parent) page.view.scrollTop = 0;
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
        if (this.editor?.page.view.contains(event.target as Node)) return;
        const page = this.pages.find(item => item.view.style.display !== "none" && item.view.contains(event.target as Node)) || this.current;
        const items = this.buttons(page.view, true);
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
        else if (event.key === "Enter" || event.key === " ") {
            if (items[index] && !isMenuItemDisabled(items[index])) items[index].click();
        }
        else if (event.key === "Tab") { this.dismiss(); return; }
        else return;
        event.preventDefault();
        event.stopPropagation();
    }
}
