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
    private isDragging = false;
    private isResizing = false;
    private resizeObserver?: ResizeObserver;
    private storedHeight = "";
    private popoutWindow: Window | null = null;

    constructor(
        private readonly host: HTMLElement,
        public readonly options: FloatingDataCardOptions,
    ) {
        // Main floating container
        this.card = document.createElement("div");
        this.card.setAttribute("data-molsysviewer-datacard", options.tag);
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
        this.card.appendChild(this.body);
        this.card.appendChild(this.resizeHandle);

        this.setupDragging();
        this.setupResizing();
        this.setupResizeObserver();

        this.host.appendChild(this.card);
    }

    private setupDragging(): void {
        let startX = 0;
        let startY = 0;
        let startLeft = 0;
        let startTop = 0;

        const onStart = (clientX: number, clientY: number) => {
            this.isDragging = true;
            this.header.style.cursor = "grabbing";
            if (this.card.style.transform.includes("translateX")) {
                const rect = this.card.getBoundingClientRect();
                const hostRect = this.host.getBoundingClientRect();
                const currentLeft = rect.left - hostRect.left;
                const currentTop = rect.top - hostRect.top;
                this.card.style.bottom = "auto";
                this.card.style.transform = "none";
                this.card.style.left = `${currentLeft}px`;
                this.card.style.top = `${currentTop}px`;
            }
            startLeft = this.card.offsetLeft;
            startTop = this.card.offsetTop;
            startX = clientX;
            startY = clientY;
            this.card.style.zIndex = "25";
        };

        const onMove = (clientX: number, clientY: number) => {
            if (!this.isDragging) return;
            const deltaX = clientX - startX;
            const deltaY = clientY - startY;
            const hostW = this.host.clientWidth || 800;
            const hostH = this.host.clientHeight || 600;
            const cardW = this.card.offsetWidth;
            const cardH = this.card.offsetHeight;

            const left = Math.max(4, Math.min(startLeft + deltaX, hostW - cardW - 4));
            const top = Math.max(4, Math.min(startTop + deltaY, hostH - cardH - 4));

            this.card.style.left = `${left}px`;
            this.card.style.top = `${top}px`;
        };

        const onEnd = () => {
            if (!this.isDragging) return;
            this.isDragging = false;
            this.header.style.cursor = "grab";
            this.card.style.zIndex = "15";
        };

        this.header.addEventListener("mousedown", (e) => {
            if ((e.target as HTMLElement).closest("button, input, select")) return;
            e.preventDefault();
            onStart(e.clientX, e.clientY);

            const mouseMove = (me: MouseEvent) => onMove(me.clientX, me.clientY);
            const mouseUp = () => {
                onEnd();
                window.removeEventListener("mousemove", mouseMove);
                window.removeEventListener("mouseup", mouseUp);
            };
            window.addEventListener("mousemove", mouseMove);
            window.addEventListener("mouseup", mouseUp);
        });
    }

    private setupResizing(): void {
        let startX = 0;
        let startY = 0;
        let startWidth = 0;
        let startHeight = 0;

        const onStart = (clientX: number, clientY: number) => {
            this.isResizing = true;
            startWidth = this.card.offsetWidth;
            startHeight = this.card.offsetHeight;
            startX = clientX;
            startY = clientY;
        };

        const onMove = (clientX: number, clientY: number) => {
            if (!this.isResizing || this.minimized) return;
            const deltaX = clientX - startX;
            const deltaY = clientY - startY;

            const newW = Math.max(240, startWidth + deltaX);
            const newH = Math.max(140, startHeight + deltaY);

            this.card.style.width = `${newW}px`;
            this.card.style.height = `${newH}px`;
        };

        const onEnd = () => {
            this.isResizing = false;
        };

        this.resizeHandle.addEventListener("mousedown", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onStart(e.clientX, e.clientY);

            const mouseMove = (me: MouseEvent) => onMove(me.clientX, me.clientY);
            const mouseUp = () => {
                onEnd();
                window.removeEventListener("mousemove", mouseMove);
                window.removeEventListener("mouseup", mouseUp);
            };
            window.addEventListener("mousemove", mouseMove);
            window.addEventListener("mouseup", mouseUp);
        });
    }

    private setupResizeObserver(): void {
        if (typeof ResizeObserver === "undefined") return;
        this.resizeObserver = new ResizeObserver(() => {
            if (this.minimized) return;
            const w = this.body.clientWidth;
            const h = this.body.clientHeight;
            if (w > 0 && h > 0) {
                this.options.onResize?.(w, h);
            }
        });
        this.resizeObserver.observe(this.card);
    }

    public openPopoutWindow(): void {
        if (this.popoutWindow && !this.popoutWindow.closed) {
            this.popoutWindow.focus();
            return;
        }

        const win = window.open("", "_blank", "width=520,height=280");
        if (!win) return;
        this.popoutWindow = win;

        const doc = win.document;
        doc.open();
        doc.write(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${this.options.title || "MolSysViewer Data Card"}</title>
  <style>
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #121216; color: #f4f4f5; font-family: "IBM Plex Sans", system-ui, sans-serif; }
    #card-pop-host { width: 100%; height: 100%; display: flex; flex-direction: column; }
    #card-pop-header { padding: 8px 12px; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; background: rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.08); color: rgba(244,244,245,0.9); }
    #card-pop-body { flex: 1 1 auto; position: relative; width: 100%; height: 100%; overflow: hidden; }
  </style>
</head>
<body>
  <div id="card-pop-host">
    <div id="card-pop-header">${this.options.title}</div>
    <div id="card-pop-body"></div>
  </div>
</body>
</html>
        `);
        doc.close();

        const popBody = doc.getElementById("card-pop-body");
        if (popBody) {
            popBody.appendChild(this.body);
        }

        this.card.style.display = "none";

        const interval = window.setInterval(() => {
            if (!this.popoutWindow || this.popoutWindow.closed) {
                window.clearInterval(interval);
                this.popoutWindow = null;
                this.card.appendChild(this.body);
                this.card.style.display = "flex";
                const w = this.body.clientWidth;
                const h = this.body.clientHeight;
                if (w > 0 && h > 0) this.options.onResize?.(w, h);
            }
        }, 800);
    }

    public toggleMinimize(): void {
        this.minimized = !this.minimized;
        if (this.minimized) {
            this.storedHeight = this.card.style.height;
            this.card.style.height = "auto";
            this.body.style.display = "none";
            this.resizeHandle.style.display = "none";
            this.minimizeButton.title = "Restore";
            this.minimizeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="10" height="10" rx="1"/></svg>`;
        } else {
            this.card.style.height = this.storedHeight || `${this.options.height ?? 210}px`;
            this.body.style.display = "block";
            this.resizeHandle.style.display = "flex";
            this.minimizeButton.title = "Minimize";
            this.minimizeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="8" x2="13" y2="8"/></svg>`;
        }
    }

    public show(): void {
        this.card.style.display = "flex";
    }

    public hide(): void {
        this.card.style.display = "none";
    }

    public dispose(): void {
        if (this.popoutWindow && !this.popoutWindow.closed) {
            this.popoutWindow.close();
        }
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        this.card.remove();
    }
}
