export interface FloatingDataCardOptions {
    tag: string;
    title: string;
    width?: number;
    height?: number;
    left?: number;
    top?: number;
    onClose?: () => void;
    onPopout?: () => void;
    onResize?: (width: number, height: number) => void;
}

/**
 * Generic resizable, draggable, floating Data Card container.
 *
 * Provides a sleek windowing shell over the 3D canvas with header drag handles,
 * title bar, and 4 header control buttons (Toggle Opacity, Popout, Minimize/Restore, Close)
 * matching the visual design system of FloatingPanelShell.
 */
export class FloatingDataCard {
    public readonly card: HTMLDivElement;
    public readonly header: HTMLDivElement;
    public readonly titleElement: HTMLDivElement;
    public readonly body: HTMLDivElement;
    public readonly opacityButton: HTMLButtonElement;
    public readonly popoutButton: HTMLButtonElement;
    public readonly minimizeButton: HTMLButtonElement;
    public readonly closeButton: HTMLButtonElement;
    public readonly resizeHandle: HTMLDivElement;

    public minimized = false;
    private resizeObserver?: ResizeObserver;
    private popoutWindow: Window | null = null;
    private releaseGesture?: () => void;
    private releasePopout?: () => void;
    private disposed = false;
    private visible = true;
    private bottomInset = 0;
    private bodyDisplay = "";
    private readonly desiredSize: { width: number; height: number };
    private readonly status: HTMLDivElement;

    constructor(
        private readonly host: HTMLElement,
        public readonly options: FloatingDataCardOptions,
    ) {
        this.desiredSize = { width: Math.max(240, options.width ?? 450), height: Math.max(42, options.height ?? 210) };
        // Main floating container
        this.card = document.createElement("div");
        this.card.setAttribute("data-molsysviewer-datacard", options.tag);
        this.card.setAttribute("role", "region");
        this.card.setAttribute("aria-label", options.title);
        this.card.style.opacity = "0.90";
        Object.assign(this.card.style, {
            position: "absolute",
            zIndex: "15",
            pointerEvents: "auto",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            boxSizing: "border-box",
            overflow: "hidden",
            background: "rgba(18, 18, 22, 0.88)",
            backdropFilter: "blur(12px)",
            webkitBackdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: "12px",
            boxShadow: "0 12px 32px rgba(0, 0, 0, 0.4)",
            color: "#f4f4f5",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "12px",
            userSelect: "none",
            minWidth: "240px",
            minHeight: "42px",
            width: `${options.width ?? 450}px`,
            height: `${options.height ?? 210}px`,
        });

        // Set initial position if provided or default to bottom-center stack
        if (options.left !== undefined && options.top !== undefined) {
            this.card.style.left = `${options.left}px`;
            this.card.style.top = `${options.top}px`;
        } else {
            // Stack gracefully at bottom center
            this.card.style.bottom = "16px";
            this.card.style.left = "50%";
            this.card.style.transform = "translateX(-50%)";
        }

        // Header (drag handle)
        this.header = document.createElement("div");
        this.header.setAttribute("data-molsysviewer-datacard-header", options.tag);
        Object.assign(this.header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            padding: "6px 10px",
            background: "rgba(255, 255, 255, 0.04)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            cursor: "grab",
            flexShrink: "0",
        });

        // Title container (ONLY title text, no subtitle)
        const titleBox = document.createElement("div");
        Object.assign(titleBox.style, {
            display: "flex",
            alignItems: "center",
            minWidth: "0",
            flex: "1 1 auto",
            overflow: "hidden",
        });

        this.titleElement = document.createElement("div");
        this.titleElement.textContent = options.title;
        Object.assign(this.titleElement.style, {
            fontSize: "11px",
            fontWeight: "700",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "rgba(244, 244, 245, 0.9)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
        });
        titleBox.appendChild(this.titleElement);
        this.header.appendChild(titleBox);

        // Header action buttons container (4 buttons: Opacity, Popout, Minimize, Close)
        const buttonGroup = document.createElement("div");
        Object.assign(buttonGroup.style, {
            display: "flex",
            alignItems: "center",
            gap: "2px",
            flexShrink: "0",
        });

        // Helper to style header action buttons consistently with FloatingPanelShell
        const styleHeaderButton = (btn: HTMLButtonElement, title: string, iconSvg: string) => {
            btn.type = "button";
            btn.title = title;
            btn.setAttribute("aria-label", title);
            btn.innerHTML = iconSvg;
            Object.assign(btn.style, {
                background: "transparent",
                border: "none",
                color: "rgba(255, 255, 255, 0.45)",
                cursor: "pointer",
                padding: "3px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "4px",
                flexShrink: "0",
            });
            btn.addEventListener("mouseenter", () => { btn.style.color = "rgba(255, 255, 255, 0.9)"; });
            btn.addEventListener("mouseleave", () => { btn.style.color = "rgba(255, 255, 255, 0.45)"; });
        };

        // 1. Toggle opacity button (3 levels: 0.90, 0.70, 0.45)
        this.opacityButton = document.createElement("button");
        styleHeaderButton(
            this.opacityButton,
            "Toggle opacity",
            `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="8" cy="8" r="6"/><path d="M8 2v12a6 6 0 0 0 0-12z" fill="currentColor"/></svg>`
        );
        this.opacityButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const states = [0.90, 0.70, 0.45];
            const currentOpacity = parseFloat(this.card.style.opacity) || states[0];
            let idx = states.indexOf(currentOpacity);
            if (idx === -1) {
                let minDiff = Infinity;
                idx = 0;
                for (let i = 0; i < states.length; i++) {
                    const diff = Math.abs(states[i] - currentOpacity);
                    if (diff < minDiff) {
                        minDiff = diff;
                        idx = i;
                    }
                }
            }
            const nextIdx = (idx + 1) % states.length;
            this.card.style.opacity = String(states[nextIdx]);
        });
        buttonGroup.appendChild(this.opacityButton);

        // 2. Popout button (ALWAYS PRESENT)
        this.popoutButton = document.createElement("button");
        styleHeaderButton(
            this.popoutButton,
            "Popout card to external window",
            `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="7" height="7" rx="1"/><path d="M12 3h1v1M13 3L8 8"/></svg>`
        );
        this.popoutButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (options.onPopout) {
                options.onPopout();
            } else {
                this.openPopoutWindow();
            }
        });
        buttonGroup.appendChild(this.popoutButton);

        // 3. Minimize button
        this.minimizeButton = document.createElement("button");
        styleHeaderButton(
            this.minimizeButton,
            "Minimize",
            `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="8" x2="13" y2="8"/></svg>`
        );
        this.minimizeButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleMinimize();
        });
        buttonGroup.appendChild(this.minimizeButton);

        // 4. Close button
        this.closeButton = document.createElement("button");
        styleHeaderButton(
            this.closeButton,
            "Close",
            `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>`
        );
        this.closeButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (options.onClose) {
                options.onClose();
            } else {
                this.hide();
            }
        });
        buttonGroup.appendChild(this.closeButton);
        this.header.appendChild(buttonGroup);

        this.status = document.createElement("div");
        this.status.setAttribute("data-molsysviewer-datacard-status", options.tag);
        this.status.setAttribute("role", "alert");
        Object.assign(this.status.style, { display: "none", padding: "6px 10px", flexShrink: "0", overflowWrap: "anywhere" });

        // Body content area
        this.body = document.createElement("div");
        this.body.setAttribute("data-molsysviewer-datacard-body", options.tag);
        Object.assign(this.body.style, {
            position: "relative",
            flex: "1 1 auto",
            width: "100%",
            height: "100%",
            minHeight: "0",
            overflow: "hidden",
            boxSizing: "border-box",
        });

        // Bottom-Right Corner Resize Handle
        this.resizeHandle = document.createElement("div");
        this.resizeHandle.setAttribute("data-molsysviewer-datacard-resize", options.tag);
        this.resizeHandle.title = "Resize card";
        this.resizeHandle.tabIndex = 0;
        this.resizeHandle.setAttribute("role", "group");
        this.resizeHandle.setAttribute("aria-label", "Resize card with arrow keys");
        this.resizeHandle.innerHTML = `<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M8 2L2 8M8 5L5 8M8 8L8 8" stroke="rgba(255,255,255,0.4)" stroke-width="1.2" stroke-linecap="round"/></svg>`;
        Object.assign(this.resizeHandle.style, {
            position: "absolute",
            right: "2px",
            bottom: "2px",
            width: "14px",
            height: "14px",
            cursor: "se-resize",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: "10",
            opacity: "0.6",
        });
        this.resizeHandle.addEventListener("mouseenter", () => { this.resizeHandle.style.opacity = "1"; });
        this.resizeHandle.addEventListener("mouseleave", () => { this.resizeHandle.style.opacity = "0.6"; });

        this.card.appendChild(this.header);
        this.card.appendChild(this.status);
        this.card.appendChild(this.body);
        this.card.appendChild(this.resizeHandle);

        this.setupDragging();
        this.setupResizing();
        this.setupResizeObserver();

        this.host.appendChild(this.card);
        this.fitToHost();
    }

    /** One active gesture owns exactly one pair of temporary window listeners. */
    private startGesture(move: (event: MouseEvent) => void, finish: () => void): void {
        this.releaseGesture?.();
        const end = () => {
            window.removeEventListener("mousemove", move);
            window.removeEventListener("mouseup", end);
            window.removeEventListener("blur", end);
            this.releaseGesture = undefined;
            finish();
        };
        this.releaseGesture = end;
        window.addEventListener("mousemove", move);
        window.addEventListener("mouseup", end);
        window.addEventListener("blur", end);
    }

    private setupDragging(): void {
        this.header.addEventListener("mousedown", event => {
            if (this.disposed || event.button !== 0 || (event.target as HTMLElement).closest("button, input, select")) return;
            event.preventDefault();
            this.releaseGesture?.();
            this.fitToHost();
            const left = this.card.offsetLeft, top = this.card.offsetTop;
            const x = event.clientX, y = event.clientY;
            this.header.style.cursor = "grabbing";
            this.card.style.zIndex = "25";
            this.startGesture(move => {
                this.card.style.left = `${left + move.clientX - x}px`;
                this.card.style.top = `${top + move.clientY - y}px`;
                this.fitToHost();
            }, () => {
                this.header.style.cursor = "grab";
                this.card.style.zIndex = "15";
            });
        });
    }

    private resizeTo(width: number, height: number): void {
        this.desiredSize.width = Math.max(240, width);
        this.desiredSize.height = Math.max(140, height);
        this.fitToHost();
    }

    private setupResizing(): void {
        this.resizeHandle.addEventListener("mousedown", event => {
            if (this.disposed || this.minimized || event.button !== 0) return;
            event.preventDefault();
            event.stopPropagation();
            this.releaseGesture?.();
            const width = this.card.offsetWidth, height = this.card.offsetHeight;
            const x = event.clientX, y = event.clientY;
            this.startGesture(move => this.resizeTo(width + move.clientX - x, height + move.clientY - y),
                () => {});
        });
        this.resizeHandle.addEventListener("keydown", event => {
            if (this.disposed || this.minimized) return;
            const deltas: Record<string, [number, number]> = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] };
            const delta = deltas[event.key];
            if (!delta || event.ctrlKey || event.metaKey || event.altKey) return;
            event.preventDefault(); event.stopPropagation();
            this.resizeTo(this.card.offsetWidth + delta[0], this.card.offsetHeight + delta[1]);
        });
    }

    /** Reserve space for host-owned controls without changing the desired size. */
    public setBottomInset(pixels: number): void {
        this.bottomInset = Number.isFinite(pixels) ? Math.max(0, pixels) : 0;
        this.fitToHost(); this.measureBody();
    }

    private fitToHost(): void {
        const width = this.host.clientWidth, height = Math.max(0, this.host.clientHeight - this.bottomInset);
        if (this.disposed || !width || !height) return;
        const margin = Math.min(4, width / 4, height / 4);
        let left = parseFloat(this.card.style.left) || 0, top = parseFloat(this.card.style.top) || 0;
        if (this.card.style.transform?.includes("translateX") || !this.card.style.top) {
            const rect = this.card.getBoundingClientRect(), host = this.host.getBoundingClientRect();
            left = rect.left - host.left; top = rect.top - host.top;
            this.card.style.transform = "none";
            this.card.style.bottom = "auto";
        }
        const w = Math.min(this.desiredSize.width, width - 2 * margin);
        const h = Math.min(this.desiredSize.height, height - 2 * margin);
        this.card.style.minWidth = `${Math.min(240, w)}px`;
        this.card.style.minHeight = `${Math.min(42, h)}px`;
        this.card.style.width = `${w}px`;
        this.card.style.height = this.minimized ? "auto" : `${h}px`;
        const visibleHeight = this.minimized ? this.card.offsetHeight : h;
        this.card.style.left = `${Math.max(margin, Math.min(left, width - w - margin))}px`;
        this.card.style.top = `${Math.max(margin, Math.min(top, height - visibleHeight - margin))}px`;
    }

    private measuredSize = { width: 0, height: 0 };
    private measureBody(): void {
        if (this.disposed || (this.minimized && !this.popoutWindow)) return;
        const width = this.body.clientWidth, height = this.body.clientHeight;
        if (width > 0 && height > 0 && (width !== this.measuredSize.width || height !== this.measuredSize.height)) {
            this.measuredSize = { width, height };
            this.options.onResize?.(width, height);
        }
    }

    private setupResizeObserver(): void {
        if (typeof ResizeObserver === "undefined") return;
        this.resizeObserver = new ResizeObserver(() => { this.fitToHost(); this.measureBody(); });
        this.resizeObserver.observe(this.host);
        this.resizeObserver.observe(this.card);
        this.resizeObserver.observe(this.body);
    }

    private showPopupError(blocked: boolean): void {
        this.status.setAttribute("data-molsysviewer-datacard-error", blocked ? "popup_blocked" : "popup_bootstrap_failed");
        this.status.replaceChildren();
        const text = document.createElement("div");
        text.textContent = blocked
            ? "The browser blocked this window. Allow popups for this page, then try again."
            : "The card window could not be prepared. Your data is still here. Try again or continue in this card.";
        this.status.appendChild(text);
        for (const [label, action] of [["Try again", () => this.openPopoutWindow()],
            ["Dismiss", () => { this.status.style.display = "none"; }]] as const) {
            const button = document.createElement("button");
            button.type = "button"; button.textContent = label;
            button.addEventListener("click", action);
            this.status.appendChild(button);
        }
        this.status.style.display = "block";
        this.popoutButton.focus();
    }

    private returnFromPopout(win: Window): void {
        if (this.popoutWindow !== win) return;
        this.releasePopout?.();
        this.releasePopout = undefined;
        this.popoutWindow = null;
        this.card.appendChild(this.body);
        if (this.disposed) return;
        this.card.style.display = this.visible ? "flex" : "none";
        this.fitToHost(); this.measureBody();
        if (this.visible) this.popoutButton.focus();
    }

    private closePopout(): void {
        const win = this.popoutWindow;
        if (!win) return;
        this.returnFromPopout(win);
        if (!win.closed) win.close();
    }

    public setTitle(title: string): void {
        if (this.disposed) return;
        this.options.title = title;
        this.card.setAttribute("aria-label", title);
        this.titleElement.textContent = title;
        if (this.popoutWindow && !this.popoutWindow.closed) {
            const doc = this.popoutWindow.document;
            doc.title = title || "MolSysViewer Data Card";
            const header = doc.getElementById("card-pop-header");
            if (header) header.textContent = title;
        }
    }

    public openPopoutWindow(): void {
        if (this.disposed || !this.visible) return;
        this.releaseGesture?.();
        if (this.popoutWindow && !this.popoutWindow.closed) {
            this.setTitle(this.options.title);
            this.popoutWindow.focus();
            return;
        }
        if (this.popoutWindow) this.returnFromPopout(this.popoutWindow);
        let win: Window | null = null;
        try {
            if (this.minimized) this.toggleMinimize();
            win = window.open("", "_blank", "width=520,height=280");
            if (!win) { this.showPopupError(true); return; }
            const doc = win.document;
            doc.open();
            doc.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>MolSysViewer Data Card</title>
      <style>
        html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #121216; color: #f4f4f5; font-family: "IBM Plex Sans", system-ui, sans-serif; }
        #card-pop-host { width: 100%; height: 100%; display: flex; flex-direction: column; }
        #card-pop-header { padding: 8px 12px; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; background: rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.08); color: rgba(244,244,245,0.9); }
        #card-pop-body { flex: 1 1 auto; position: relative; width: 100%; height: 100%; min-height: 0; overflow: auto; }
      </style>
    </head>
    <body>
      <div id="card-pop-host">
        <div id="card-pop-header"></div>
        <div id="card-pop-body"></div>
      </div>
    </body>
    </html>
            `);
            doc.close();
            const popBody = doc.getElementById("card-pop-body");
            const header = doc.getElementById("card-pop-header");
            if (!popBody || !header) throw new Error("The card window has no content host.");
            doc.title = this.options.title || "MolSysViewer Data Card";
            header.textContent = this.options.title;
            popBody.appendChild(this.body);
            this.popoutWindow = win;
            const popup = win;
            const returned = () => this.returnFromPopout(popup);
            const resized = () => this.measureBody();
            const interval = window.setInterval(() => { if (popup.closed) returned(); }, 800);
            popup.addEventListener("beforeunload", returned);
            popup.addEventListener("resize", resized);
            this.releasePopout = () => {
                window.clearInterval(interval);
                try {
                    popup.removeEventListener("beforeunload", returned);
                    popup.removeEventListener("resize", resized);
                } catch { /* A navigated window can retire its same-origin listener surface. */ }
            };
            this.status.style.display = "none";
            this.card.style.display = "none";
            this.measureBody();
        } catch {
            if (win) {
                this.returnFromPopout(win);
                if (this.body.parentElement !== this.card) this.card.appendChild(this.body);
                if (!win.closed) win.close();
            }
            this.card.style.display = "flex";
            this.showPopupError(false);
        }
    }

    public toggleMinimize(): void {
        if (this.disposed) return;
        this.releaseGesture?.();
        this.minimized = !this.minimized;
        if (this.minimized) {
            this.bodyDisplay = this.body.style.display;
            this.body.style.display = "none";
        } else this.body.style.display = this.bodyDisplay;
        this.resizeHandle.style.display = this.minimized ? "none" : "flex";
        const title = this.minimized ? "Restore" : "Minimize";
        this.minimizeButton.title = title;
        this.minimizeButton.setAttribute("aria-label", title);
        const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        for (const [name, value] of Object.entries({ width: "13", height: "13", viewBox: "0 0 16 16",
            fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round" })) icon.setAttribute(name, value);
        const mark = document.createElementNS("http://www.w3.org/2000/svg", this.minimized ? "rect" : "line");
        const attributes = this.minimized ? { x: "3", y: "3", width: "10", height: "10", rx: "1" }
            : { x1: "3", y1: "8", x2: "13", y2: "8" };
        for (const [name, value] of Object.entries(attributes)) mark.setAttribute(name, value);
        icon.appendChild(mark); this.minimizeButton.replaceChildren(icon);
        this.fitToHost();
        if (!this.minimized) this.measureBody();
    }

    public show(): void {
        if (this.disposed) return;
        if (this.popoutWindow?.closed) this.returnFromPopout(this.popoutWindow);
        this.visible = true;
        this.card.style.display = this.popoutWindow && !this.popoutWindow.closed ? "none" : "flex";
        this.fitToHost(); this.measureBody();
    }

    public hide(): void {
        if (this.disposed) return;
        this.visible = false;
        this.releaseGesture?.();
        this.closePopout();
        this.card.style.display = "none";
    }

    public dispose(): void {
        if (this.disposed) return;
        this.disposed = true;
        this.releaseGesture?.();
        this.closePopout();
        this.resizeObserver?.disconnect();
        this.card.remove();
    }
}
