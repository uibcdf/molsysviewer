/** One visibility policy for control-area/canvas hover and keyboard access. */
export class ControlsVisibility {
    private readonly release: Array<() => void> = [];
    private keyboardFocus = false;
    private touchRevealed = false;
    private disposed = false;
    private introductionStarted = false;
    private introducing = false;
    private introductionTimer?: ReturnType<typeof setTimeout>;

    constructor(
        private readonly host: HTMLElement,
        private readonly surface: HTMLElement,
        private readonly hotspot: HTMLElement,
        private readonly config: () => { visible: boolean; autohide: boolean; scope: string; suppressed?: boolean },
    ) {
        hotspot.setAttribute("data-molsysviewer-controls-hotspot", "true");
        hotspot.setAttribute("role", "button");
        hotspot.setAttribute("aria-label", "Show canvas controls");
        const listen = (target: EventTarget, event: string, callback: EventListener) => {
            target.addEventListener(event, callback);
            this.release.push(() => target.removeEventListener(event, callback));
        };
        const refresh = () => this.refresh();
        for (const element of [host, hotspot, surface]) {
            listen(element, "pointerenter", refresh);
            listen(element, "pointerleave", refresh);
        }
        listen(host, "focusin", refresh);
        listen(host, "focusout", () => queueMicrotask(refresh));
        listen(document, "keydown", () => { this.keyboardFocus = true; this.refresh(); });
        listen(document, "pointermove", () => {
            if (!this.keyboardFocus) return;
            this.keyboardFocus = false;
            this.refresh();
        });
        listen(document, "pointerdown", event => {
            this.keyboardFocus = false;
            if (!surface.contains(event.target as Node) && !hotspot.contains(event.target as Node)) this.touchRevealed = false;
            this.refresh();
        });
        listen(hotspot, "pointerdown", event => {
            event.stopPropagation();
            this.keyboardFocus = false;
            this.touchRevealed = (event as PointerEvent).pointerType === "touch";
            hotspot.focus();
            this.refresh();
        });
        listen(hotspot, "keydown", event => {
            const key = (event as KeyboardEvent).key;
            if (key !== "Enter" && key !== " ") return;
            event.preventDefault();
            event.stopPropagation();
            surface.querySelector<HTMLButtonElement>("button:not([disabled])")?.focus();
        });
        surface.style.transition = "opacity 200ms ease";
        this.refresh();
    }

    refresh(): void {
        if (this.disposed) return;
        const { visible, autohide, scope, suppressed } = this.config();
        const available = visible && !suppressed;
        // Start when controls first become available, including after slow loading.
        // A new mode owns a new lifetime; hover, frame and layout updates do not
        // restart this discovery window. Explicit visibility still wins.
        if (available && !this.introductionStarted) {
            this.introductionStarted = true;
            if (autohide) {
                this.introducing = true;
                this.introductionTimer = setTimeout(() => {
                    this.introducing = false;
                    this.refresh();
                }, 2000);
            }
        }
        const focused = this.surface.contains(document.activeElement) || document.activeElement === this.hotspot;
        const hovered = scope === "canvas" ? this.host.matches(":hover")
            : this.hotspot.matches(":hover") || this.surface.matches(":hover");
        const show = available && (!autohide || this.introducing || hovered || (this.keyboardFocus && focused) || this.touchRevealed);
        this.surface.style.opacity = show ? "1" : "0";
        this.surface.style.visibility = show ? "visible" : "hidden";
        this.surface.style.pointerEvents = show ? "auto" : "none";
        this.surface.setAttribute("aria-hidden", show ? "false" : "true");
        this.hotspot.style.display = available && autohide ? "block" : "none";
        this.hotspot.tabIndex = available && autohide ? 0 : -1;
    }

    dispose(): void {
        this.disposed = true;
        clearTimeout(this.introductionTimer);
        for (const release of this.release) release();
    }
}
