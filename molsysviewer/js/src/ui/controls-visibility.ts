/** One visibility policy for control-area/canvas hover and keyboard access. */
export class ControlsVisibility {
    private readonly release: Array<() => void> = [];
    private keyboardFocus = false;
    private touchRevealed = false;
    private disposed = false;
    private introductionStarted = false;
    private introducing = false;
    private introductionTimer?: ReturnType<typeof setTimeout>;
    private focusFrame?: number;

    constructor(
        private readonly host: HTMLElement,
        private readonly surface: HTMLElement,
        private readonly hotspot: HTMLElement,
        private readonly config: () => { visible: boolean; autohide: boolean; scope: string; suppressed?: boolean },
        private readonly motion?: { shown: string; hidden: string },
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
            this.keyboardFocus = true;
            this.refresh();
            // A visibility transition reversal can commit after the first frame.
            // Transfer focus only when the actual surface permits it, and stop
            // if the user leaves the hotspot or the controls become unavailable.
            if (this.focusFrame !== undefined) cancelAnimationFrame(this.focusFrame);
            const focusControls = () => {
                this.focusFrame = undefined;
                if (this.disposed || document.activeElement !== hotspot || surface.inert) return;
                if (getComputedStyle(surface).visibility !== "visible") {
                    this.focusFrame = requestAnimationFrame(focusControls);
                    return;
                }
                const button = [...surface.querySelectorAll<HTMLButtonElement>("button:not([disabled])")]
                    .find(candidate => candidate.getClientRects().length > 0
                        && getComputedStyle(candidate).visibility === "visible");
                button?.focus();
                // Chromium can still reject focus in the frame committing the
                // reversal. Confirm the transfer rather than assuming focus().
                if (document.activeElement === hotspot) {
                    this.focusFrame = requestAnimationFrame(focusControls);
                }
            };
            this.focusFrame = requestAnimationFrame(focusControls);
        });
        surface.style.transition = motion
            ? "transform 250ms cubic-bezier(0.25, 0.8, 0.25, 1), opacity 200ms ease, visibility 0s linear"
            : "opacity 200ms ease, visibility 0s linear";
        surface.style.willChange = motion ? "opacity, transform" : "opacity";
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
        // Fade the entire surface before removing it from painting. Disable all
        // descendants immediately, including buttons with pointerEvents=auto.
        this.surface.style.transitionDelay = this.motion
            ? (show ? "0s, 0s, 0s" : "0s, 0s, 250ms")
            : (show ? "0s, 0s" : "0s, 200ms");
        this.surface.inert = !show;
        if (this.motion) this.surface.style.transform = show ? this.motion.shown : this.motion.hidden;
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
        if (this.focusFrame !== undefined) cancelAnimationFrame(this.focusFrame);
        for (const release of this.release) release();
    }
}
