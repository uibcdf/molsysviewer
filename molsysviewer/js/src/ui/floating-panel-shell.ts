type FloatingPanelShellOptions = {
    title: string;
    navButtonLabel?: string;
    panelModeStyle?: string;
    onPanelPopClick?: () => void;
    isPanelOnly?: boolean;
};

type WorkspaceOption = {
    id: string;
    title: string;
    subtitle?: string;
};

type PanelOption = {
    id: string;
    title: string;
    active?: boolean;
};

export class FloatingPanelShell {
    public readonly root: HTMLDivElement;
    public readonly panel: HTMLDivElement;
    public readonly titleElement: HTMLDivElement;
    public readonly headerElement: HTMLDivElement;
    public readonly navGroupElement?: HTMLDivElement;
    public readonly navButton?: HTMLButtonElement;
    public readonly panelStackGroupElement: HTMLDivElement;
    public readonly workspaceGroupElement: HTMLDivElement;
    public readonly content: HTMLDivElement;
    public readonly toggleButton: HTMLButtonElement;
    public readonly panelModeStyle: string;
    public readonly isPanelOnly: boolean;
    public onResize?: (width: number) => void;

    get width(): number {
        if (this.isSplit) {
            return this.getWidth();
        }
        return 0;
    }

    get toggleWidth(): number {
        return 0;
    }

    private visible = false;
    private expanded = false;
    private displayUpdatePending = false;
    private minimized = false;
    private onSelectPanel?: (panelId: string) => void;
    private onSelectWorkspace?: (workspaceId: string) => void;
    private workspaceMenuOpen = false;
    private readonly workspaceCurrentElement: HTMLButtonElement;
    private readonly workspaceCurrentMarkerElement: HTMLSpanElement;
    private readonly workspaceCurrentTitleElement: HTMLSpanElement;
    private readonly workspaceCurrentSubtitleElement: HTMLSpanElement;
    private readonly workspaceMenuElement: HTMLDivElement;
    private panelResizeObserver?: ResizeObserver;
    public isSplit = false;
    public isAmbient = false;
    private lastSplitState = false;
    private dockButton?: HTMLButtonElement;
    private lockButton?: HTMLButtonElement;

    public onLayoutChange?: (state: { isSplit: boolean, isAmbient: boolean, visible: boolean, expanded: boolean }) => void;
    private isCanvasHidden = false;

    get isExpanded(): boolean {
        return this.expanded;
    }

    public setCanvasHidden(hidden: boolean): void {
        this.isCanvasHidden = hidden;
        this.updateLayout();
    }

    public setSplit(split: boolean): void {
        this.isSplit = split;
        this.updateLayout();
    }

    public setAmbient(ambient: boolean): void {
        this.isAmbient = ambient;
        this.updateLayout();
    }

    public clampPosition(): void {
        if (this.isPanelOnly || this.isSplit) return;
        const hostWidth = this.host.clientWidth;
        const hostHeight = this.host.clientHeight;
        if (!hostWidth || !hostHeight) return;

        let currentWidth = parseFloat(this.panel.style.width) || this.panel.offsetWidth;
        let currentHeight = parseFloat(this.panel.style.height) || this.panel.offsetHeight;

        // Clamp dimensions to host size
        currentWidth = Math.min(currentWidth, hostWidth - 20);
        currentHeight = Math.min(currentHeight, hostHeight - 20);

        let currentLeft = parseFloat(this.panel.style.left) || 0;
        let currentTop = parseFloat(this.panel.style.top) || 0;

        // Clamp position so it doesn't go off-screen
        currentLeft = Math.max(10, Math.min(currentLeft, hostWidth - currentWidth - 10));
        currentTop = Math.max(10, Math.min(currentTop, hostHeight - currentHeight - 10));

        this.panel.style.width = `${currentWidth}px`;
        this.panel.style.height = `${currentHeight}px`;
        this.panel.style.left = `${currentLeft}px`;
        this.panel.style.top = `${currentTop}px`;
    }

    public centerPanel(): void {
        if (this.isPanelOnly || this.isSplit) return;
        const hostWidth = this.host.clientWidth;
        const hostHeight = this.host.clientHeight;
        if (!hostWidth || !hostHeight) return;

        const isFullscreen = !!document.fullscreenElement;
        const maxWidth = isFullscreen ? 1100 : 950;
        const maxHeight = isFullscreen ? 850 : 780;

        const panelWidth = Math.min(hostWidth * 0.75, maxWidth);
        const panelHeight = Math.min(hostHeight * 0.80, maxHeight);
        const left = Math.max(10, (hostWidth - panelWidth) / 2);
        const top = Math.max(10, (hostHeight - panelHeight) / 2);

        this.panel.style.left = `${left}px`;
        this.panel.style.top = `${top}px`;
        this.panel.style.width = `${panelWidth}px`;
        this.panel.style.height = `${panelHeight}px`;
    }

    constructor(private readonly host: HTMLElement, options: FloatingPanelShellOptions) {
        this.isPanelOnly = !!options.isPanelOnly;
        const style = options.panelModeStyle || "floating";
        this.panelModeStyle = style;
        this.isAmbient = style === "ambient";
        this.isSplit = style === "split";
        this.lastSplitState = this.isSplit;

        // Backdrop overlay (fills the host, captures backdrop clicks)
        this.root = document.createElement("div");
        Object.assign(this.root.style, {
            position: "absolute",
            inset: "0",
            display: "none",
            alignItems: "center", // Center vertically
            zIndex: "18",
        });

        // Floating card
        this.panel = document.createElement("div");
        this.panel.style.opacity = "0.90";
        Object.assign(this.panel.style, {
            pointerEvents: "auto",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            boxSizing: "border-box",
            overflow: "hidden",
            padding: "10px",
            color: "#f4f4f5",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "12px",
        });

        // Header
        this.headerElement = document.createElement("div");
        Object.assign(this.headerElement.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            paddingBottom: "8px",
            marginBottom: "2px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            flexShrink: "0",
        });

        // Mouse/Touch dragging logic using absolute left/top coordinates (traditional behavior)
        if (!this.isPanelOnly) {
            let isDragging = false;
            let startX = 0;
            let startY = 0;
            let startLeft = 0;
            let startTop = 0;

            const dragStart = (clientX: number, clientY: number) => {
                if (this.isSplit) return false;
                isDragging = true;
                startLeft = this.panel.offsetLeft;
                startTop = this.panel.offsetTop;
                startX = clientX;
                startY = clientY;
                return true;
            };

            const dragMove = (clientX: number, clientY: number) => {
                if (!isDragging) return;
                const deltaX = clientX - startX;
                const deltaY = clientY - startY;

                const hostWidth = this.host.clientWidth;
                const hostHeight = this.host.clientHeight;
                const panelWidth = this.panel.offsetWidth;
                const panelHeight = this.panel.offsetHeight;

                // Clamp position so it doesn't go off-screen
                const left = Math.max(10, Math.min(startLeft + deltaX, hostWidth - panelWidth - 10));
                const top = Math.max(10, Math.min(startTop + deltaY, hostHeight - panelHeight - 10));

                this.panel.style.left = `${left}px`;
                this.panel.style.top = `${top}px`;
            };

            const dragEnd = () => {
                isDragging = false;
            };

            // Mouse events
            this.headerElement.addEventListener("mousedown", (e) => {
                if ((e.target as HTMLElement).closest("button, input, select")) return;
                if (dragStart(e.clientX, e.clientY)) {
                    e.preventDefault();
                    const onMouseMove = (moveEvent: MouseEvent) => {
                        dragMove(moveEvent.clientX, moveEvent.clientY);
                    };
                    const onMouseUp = () => {
                        dragEnd();
                        window.removeEventListener("mousemove", onMouseMove);
                        window.removeEventListener("mouseup", onMouseUp);
                    };
                    window.addEventListener("mousemove", onMouseMove);
                    window.addEventListener("mouseup", onMouseUp);
                }
            });

            // Touch events
            this.headerElement.addEventListener("touchstart", (e) => {
                if ((e.target as HTMLElement).closest("button, input, select")) return;
                const touch = e.touches[0];
                if (dragStart(touch.clientX, touch.clientY)) {
                    const onTouchMove = (moveEvent: TouchEvent) => {
                        const moveTouch = moveEvent.touches[0];
                        dragMove(moveTouch.clientX, moveTouch.clientY);
                    };
                    const onTouchEnd = () => {
                        dragEnd();
                        window.removeEventListener("touchmove", onTouchMove);
                        window.removeEventListener("touchend", onTouchEnd);
                    };
                    window.addEventListener("touchmove", onTouchMove, { passive: true });
                    window.addEventListener("touchend", onTouchEnd);
                }
            });
        }

        this.titleElement = document.createElement("div");
        this.titleElement.textContent = options.title;

        if (options.navButtonLabel) {
            this.navGroupElement = document.createElement("div");
            this.navGroupElement.setAttribute("data-molsysviewer-panel-nav-group", "true");
            Object.assign(this.navGroupElement.style, {
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "3px",
                borderRadius: "999px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
            });
            this.titleElement.setAttribute("data-molsysviewer-panel-nav-current", options.title.toLowerCase());
            Object.assign(this.titleElement.style, {
                fontSize: "10px",
                fontWeight: "700",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "#f4f4f5",
                padding: "5px 8px",
                borderRadius: "999px",
                background: "rgba(255,255,255,0.12)",
            });
            this.navButton = document.createElement("button");
            this.navButton.type = "button";
            this.navButton.setAttribute("data-molsysviewer-panel-nav", options.navButtonLabel.toLowerCase());
            this.navButton.textContent = options.navButtonLabel;
            Object.assign(this.navButton.style, {
                border: "0",
                borderRadius: "999px",
                background: "transparent",
                color: "rgba(244,244,245,0.8)",
                fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
                fontSize: "10px",
                lineHeight: "1",
                padding: "5px 8px",
                cursor: "pointer",
            });
        } else {
            Object.assign(this.titleElement.style, {
                fontSize: "11px",
                fontWeight: "700",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "rgba(244, 244, 245, 0.7)",
            });
        }

        if (this.navGroupElement) {
            this.navGroupElement.appendChild(this.titleElement);
            if (this.navButton) this.navGroupElement.appendChild(this.navButton);
            this.headerElement.appendChild(this.navGroupElement);
        } else {
            this.headerElement.appendChild(this.titleElement);
        }

        this.panelStackGroupElement = document.createElement("div");
        Object.assign(this.panelStackGroupElement.style, {
            display: "none",
            alignItems: "center",
            gap: "4px",
            flexWrap: "wrap",
            flex: "1 1 auto",
        });
        this.headerElement.appendChild(this.panelStackGroupElement);

        this.workspaceGroupElement = document.createElement("div");
        Object.assign(this.workspaceGroupElement.style, {
            display: "none",
            position: "relative",
            alignItems: "center",
        });
        this.workspaceCurrentElement = document.createElement("button");
        this.workspaceCurrentElement.type = "button";
        Object.assign(this.workspaceCurrentElement.style, {
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: "2px",
            minWidth: "110px",
            padding: "7px 10px",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.12)",
            color: "#f4f4f5",
            border: "1px solid rgba(255,255,255,0.14)",
            cursor: "pointer",
            textAlign: "left",
        });
        this.workspaceCurrentMarkerElement = document.createElement("span");
        Object.assign(this.workspaceCurrentMarkerElement.style, { fontSize: "9px", fontWeight: "700", lineHeight: "1.1", letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(244,244,245,0.52)" });
        this.workspaceCurrentTitleElement = document.createElement("span");
        Object.assign(this.workspaceCurrentTitleElement.style, { fontSize: "11px", fontWeight: "700", lineHeight: "1.1", color: "#f4f4f5" });
        this.workspaceCurrentSubtitleElement = document.createElement("span");
        Object.assign(this.workspaceCurrentSubtitleElement.style, { fontSize: "10px", lineHeight: "1.2", color: "rgba(244,244,245,0.68)" });
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentMarkerElement);
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentTitleElement);
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentSubtitleElement);
        this.workspaceCurrentElement.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.workspaceMenuOpen = !this.workspaceMenuOpen;
            this.applyWorkspaceMenuState();
        });

        this.workspaceMenuElement = document.createElement("div");
        Object.assign(this.workspaceMenuElement.style, {
            position: "absolute",
            top: "calc(100% + 6px)",
            right: "0",
            minWidth: "224px",
            display: "none",
            gap: "6px",
            padding: "6px",
            borderRadius: "12px",
            background: "rgba(18, 18, 22, 0.96)",
            border: "1px solid rgba(255,255,255,0.10)",
            boxShadow: "0 16px 32px rgba(0,0,0,0.24)",
            zIndex: "20",
        });
        this.headerElement.appendChild(this.workspaceGroupElement);

        this.dockButton = document.createElement("button");
        this.dockButton.type = "button";
        Object.assign(this.dockButton.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
            flexShrink: "0",
            marginLeft: "4px",
        });
        this.dockButton.addEventListener("mouseenter", () => { this.dockButton!.style.color = "rgba(255,255,255,0.9)"; });
        this.dockButton.addEventListener("mouseleave", () => { this.dockButton!.style.color = "rgba(255,255,255,0.45)"; });
        this.dockButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.isSplit = !this.isSplit;
            this.updateLayout();
        });
        this.lockButton = document.createElement("button");
        this.lockButton.type = "button";
        Object.assign(this.lockButton.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
            flexShrink: "0",
            marginLeft: "4px",
        });
        this.lockButton.addEventListener("mouseenter", () => { this.lockButton!.style.color = "rgba(255,255,255,0.9)"; });
        this.lockButton.addEventListener("mouseleave", () => { this.lockButton!.style.color = "rgba(255,255,255,0.45)"; });
        this.lockButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.isAmbient = !this.isAmbient;
            this.updateLayout();
        });

        const opacityButton = document.createElement("button");
        opacityButton.type = "button";
        opacityButton.title = "Toggle opacity";
        opacityButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="8" cy="8" r="6"/><path d="M8 2v12a6 6 0 0 0 0-12z" fill="currentColor"/></svg>`;
        Object.assign(opacityButton.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
            flexShrink: "0",
            marginLeft: "4px",
        });
        opacityButton.addEventListener("mouseenter", () => { opacityButton.style.color = "rgba(255,255,255,0.9)"; });
        opacityButton.addEventListener("mouseleave", () => { opacityButton.style.color = "rgba(255,255,255,0.45)"; });
        opacityButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const states = [0.90, 0.70, 0.45];
            const currentOpacity = parseFloat(this.panel.style.opacity) || states[0];
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
            this.panel.style.opacity = String(states[nextIdx]);
        });

        if (!this.isPanelOnly) {
            this.headerElement.appendChild(this.dockButton);
            this.headerElement.appendChild(this.lockButton);
            this.headerElement.appendChild(opacityButton);
        }

        if (options.onPanelPopClick) {
            const panelPopBtn = document.createElement("button");
            panelPopBtn.type = "button";
            panelPopBtn.title = "Popout panel to external window";
            panelPopBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="7" height="7" rx="1"/><path d="M12 3h1v1M13 3L8 8"/></svg>`;
            Object.assign(panelPopBtn.style, {
                background: "transparent",
                border: "none",
                color: "rgba(255,255,255,0.45)",
                cursor: "default",
                padding: "4px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "5px",
                flexShrink: "0",
                marginLeft: "4px",
            });
            panelPopBtn.addEventListener("mouseenter", () => { panelPopBtn.style.color = "rgba(255,255,255,0.9)"; });
            panelPopBtn.addEventListener("mouseleave", () => { panelPopBtn.style.color = "rgba(255,255,255,0.45)"; });
            panelPopBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                options.onPanelPopClick!();
            });
            this.headerElement.appendChild(panelPopBtn);
        }

        const minimizeButton = document.createElement("button");
        minimizeButton.type = "button";
        minimizeButton.title = "Minimize";
        minimizeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="8" x2="13" y2="8"/></svg>`;
        Object.assign(minimizeButton.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
            flexShrink: "0",
            marginLeft: "4px",
        });
        minimizeButton.addEventListener("mouseenter", () => { minimizeButton.style.color = "rgba(255,255,255,0.9)"; });
        minimizeButton.addEventListener("mouseleave", () => { minimizeButton.style.color = "rgba(255,255,255,0.45)"; });
        
        let originalHeight = "";
        let originalMinHeight = "";
        minimizeButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.minimized = !this.minimized;
            if (this.minimized) {
                originalHeight = this.panel.style.height;
                originalMinHeight = this.panel.style.minHeight;
                this.panel.style.height = "auto";
                this.panel.style.minHeight = "0";
                this.content.style.display = "none";
                this.root.style.background = "transparent";
                this.root.style.pointerEvents = "none";
                minimizeButton.title = "Restore";
                minimizeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="10" height="10" rx="1"/></svg>`;
            } else {
                this.panel.style.height = originalHeight || (isSplit ? "calc(100% - 20px)" : "min(68%, 700px)");
                this.panel.style.minHeight = originalMinHeight || (isSplit ? "0" : "420px");
                this.content.style.display = "flex";
                this.root.style.background = (isAmbient || isSplit) ? "transparent" : "rgba(0,0,0,0.32)";
                this.root.style.pointerEvents = (isAmbient || isSplit) ? "none" : "auto";
                minimizeButton.title = "Minimize";
                minimizeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="8" x2="13" y2="8"/></svg>`;
            }
        });
        if (!this.isPanelOnly) {
            this.headerElement.appendChild(minimizeButton);
        }

        // Close button (this is the toggleButton for interface compatibility)
        this.toggleButton = document.createElement("button");
        this.toggleButton.type = "button";
        this.toggleButton.title = "Close (Esc)";
        this.toggleButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>`;
        Object.assign(this.toggleButton.style, {
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.45)",
            cursor: "default",
            padding: "4px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "5px",
            flexShrink: "0",
            marginLeft: "4px",
        });
        this.toggleButton.addEventListener("mouseenter", () => { this.toggleButton.style.color = "rgba(255,255,255,0.9)"; });
        this.toggleButton.addEventListener("mouseleave", () => { this.toggleButton.style.color = "rgba(255,255,255,0.45)"; });
        this.headerElement.appendChild(this.toggleButton);

        // Content area
        this.content = document.createElement("div");
        Object.assign(this.content.style, {
            pointerEvents: "auto",
            display: "flex",
            alignItems: "stretch",
            gap: "10px",
            flexDirection: "row",
            flexWrap: "nowrap",
            width: "100%",
            minWidth: "100%",
            maxWidth: "100%",
            boxSizing: "border-box",
            flex: "1 1 auto",
            overflowX: "auto",
            overflowY: "hidden",
            minHeight: "0",
        });

        this.panel.appendChild(this.headerElement);
        this.panel.appendChild(this.content);
        this.root.appendChild(this.panel);

        // Backdrop click does not close the panel (per user request to prevent accidental dismissal)
        // Only the explicit close/toggle button can close it.

        // ResizeObserver to track width changes
        this.panelResizeObserver = new ResizeObserver(() => {
            if (this.isSplit) {
                this.onResize?.(this.panel.offsetWidth);
            }
        });

        const hostResizeObserver = new ResizeObserver(() => {
            if (this.visible && this.expanded) {
                this.centerPanel();
            }
        });
        hostResizeObserver.observe(host);

        this.updateLayout();

        host.appendChild(this.root);
    }

    private updateLayout(): void {
        const isSplit = this.isSplit;

        // Detect transitions between split and float states
        let transitionedToSplit = false;
        if (isSplit !== this.lastSplitState) {
            if (isSplit) {
                this.isAmbient = true; // Transitioning to split: always open the lock
                transitionedToSplit = true;
            } else {
                this.isAmbient = false; // Transitioning back to float: always close the lock
            }
            this.lastSplitState = isSplit;
        }

        const isAmbient = this.isAmbient;

        // 1. Update backdrop root styles
        Object.assign(this.root.style, {
            justifyContent: isSplit ? "flex-start" : "center",
            pointerEvents: isAmbient ? "none" : "auto",
            background: isAmbient ? "transparent" : "rgba(0,0,0,0.32)",
            paddingLeft: isSplit ? "10px" : "0",
        });

        // 2. Update panel card styles
        this.panel.style.position = "absolute";

        if (this.isPanelOnly) {
            this.panel.style.transform = "";
            this.panel.style.backdropFilter = "";
            this.panel.style.webkitBackdropFilter = "";
            
            this.panel.style.left = "0";
            this.panel.style.top = "0";
            this.panel.style.width = "100%";
            Object.assign(this.panel.style, {
                height: "100%",
                minHeight: "0",
                minWidth: "0",
                borderRadius: "0",
                border: "none",
                boxShadow: "none",
                background: "#121216",
                resize: "none",
            });
            this.headerElement.style.cursor = "default";
            if (this.panelResizeObserver) {
                this.panelResizeObserver.unobserve(this.panel);
            }
            
            Object.assign(this.root.style, {
                justifyContent: "flex-start",
                pointerEvents: "auto",
                background: "#121216",
                padding: "0",
            });
        } else if (isSplit) {
            this.headerElement.style.cursor = "default";
            this.panel.style.transform = "";
            this.panel.style.backdropFilter = "";
            this.panel.style.webkitBackdropFilter = "";
            
            this.panel.style.left = "10px";
            this.panel.style.top = "10px";
            
            // Keep the user-resized width if it was already set and is valid, otherwise default to 50%.
            // Always reset to 50% when transitioning from float to split.
            if (transitionedToSplit || !this.panel.style.width || this.panel.style.width === "100%" || this.panel.style.width.indexOf("px") === -1) {
                this.panel.style.width = "50%";
            }
            
            Object.assign(this.panel.style, {
                height: "calc(100% - 20px)",
                borderRadius: "14px",
                border: "1px solid rgba(255,255,255,0.12)",
                boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
                background: "rgba(18, 18, 22, 0.92)",
                resize: "horizontal",
            });
            this.panelResizeObserver?.observe(this.panel);
        } else {
            this.panelResizeObserver?.unobserve(this.panel);
            
            // When returning to float, always reset to the original center position and original default dimensions
            this.centerPanel();
            
            Object.assign(this.panel.style, {
                borderRadius: "16px",
                border: "1px solid rgba(255,255,255,0.12)",
                boxShadow: "0 24px 64px rgba(0,0,0,0.45)",
                background: "rgba(18, 18, 22, 0.92)",
                backdropFilter: "blur(20px)",
                webkitBackdropFilter: "blur(20px)",
                resize: "both",
            });
            this.headerElement.style.cursor = "move";
        }

        // 3. Update button icons/titles
        if (this.dockButton) {
            this.dockButton.title = isSplit ? "Float panel" : "Dock panel (Split)";
            this.dockButton.innerHTML = isSplit 
                ? `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="12" height="12" rx="1.5"/><rect x="5" y="5" width="6" height="6" rx="0.5"/></svg>` // Float layout (click to float)
                : `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="2" x2="4" y2="14"/><line x1="4" y1="8" x2="12" y2="8"/></svg>`; // Rotated T layout (click to split)
        }

        if (this.lockButton) {
            this.lockButton.title = isAmbient ? "Lock background" : "Unlock background (Ambient)";
            this.lockButton.innerHTML = isAmbient
                ? `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M4.5 7V4a3.5 3.5 0 0 1 6-2.5"/></svg>` // Open lock
                : `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M4.5 7V4a3.5 3.5 0 0 1 7 0v3"/></svg>`; // Closed lock
            this.lockButton.style.display = "inline-flex";
        }

        // Trigger callback to update canvas host left offset in real-time
        this.onLayoutChange?.({ 
            isSplit: this.isSplit, 
            isAmbient: this.isAmbient, 
            visible: this.visible, 
            expanded: this.expanded 
        });
        this.onResize?.(this.getWidth());
    }

    getWidth(): number {
        if (!this.expanded || !this.visible) return 0;
        let w = this.panel.offsetWidth;
        if (w === 0) {
            // Fallback when display is "none" before first render
            w = Math.max(300, Math.floor(this.host.clientWidth / 2));
        }
        return w;
    }

    private applyDisplay(): void {
        this.root.style.display = (this.visible && this.expanded) ? "flex" : "none";
    }

    private scheduleDisplayUpdate(): void {
        if (this.displayUpdatePending) return;
        this.displayUpdatePending = true;
        queueMicrotask(() => {
            this.displayUpdatePending = false;
            this.applyDisplay();
        });
    }

    setVisible(visible: boolean): void {
        this.visible = visible;
        if (!visible) {
            this.workspaceMenuOpen = false;
            this.applyWorkspaceMenuState();
        } else {
            this.centerPanel();
        }
        this.scheduleDisplayUpdate();
        this.onLayoutChange?.({ 
            isSplit: this.isSplit, 
            isAmbient: this.isAmbient, 
            visible: this.visible, 
            expanded: this.expanded 
        });
    }

    isVisible(): boolean {
        return this.visible;
    }

    setExpanded(expanded: boolean): void {
        this.expanded = expanded;
        if (expanded) {
            this.centerPanel();
        }
        this.scheduleDisplayUpdate();
        this.onLayoutChange?.({ 
            isSplit: this.isSplit, 
            isAmbient: this.isAmbient, 
            visible: this.visible, 
            expanded: this.expanded 
        });
    }

    setNavButtonLabel(label?: string): void {
        if (!this.navButton) return;
        this.navButton.textContent = label ?? "";
        this.navButton.style.display = label ? "inline-flex" : "none";
        this.navButton.setAttribute("data-molsysviewer-panel-nav", label ? label.toLowerCase() : "");
    }

    setOnSelectWorkspace(callback: ((workspaceId: string) => void) | undefined): void {
        this.onSelectWorkspace = callback;
    }

    setOnSelectPanel(callback: ((panelId: string) => void) | undefined): void {
        this.onSelectPanel = callback;
    }

    setPanelOptions(items: PanelOption[]): void {
        this.panelStackGroupElement.replaceChildren();

        if (!Array.isArray(items) || items.length <= 1) {
            this.panelStackGroupElement.style.display = "none";
            this.titleElement.style.display = "block";
            return;
        }

        this.panelStackGroupElement.style.display = "flex";
        this.titleElement.style.display = "none";
        for (const item of items) {
            const node = document.createElement(item.active ? "span" : "button");
            if (item.active) {
                node.setAttribute("data-molsysviewer-panel-stack-current", item.id);
            } else {
                const button = node as HTMLButtonElement;
                button.type = "button";
                button.setAttribute("data-molsysviewer-panel-stack-option", item.id);
                button.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    this.onSelectPanel?.(item.id);
                });
            }
            node.textContent = item.title;
            Object.assign(node.style, {
                border: item.active ? "1px solid rgba(255,255,255,0.14)" : "1px solid rgba(255,255,255,0.08)",
                borderRadius: "999px",
                background: item.active ? "rgba(255,255,255,0.14)" : "rgba(255,255,255,0.03)",
                color: item.active ? "#f4f4f5" : "rgba(244,244,245,0.78)",
                fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
                fontSize: "10px",
                lineHeight: "1",
                padding: "5px 8px",
                cursor: item.active ? "default" : "pointer",
            });
            this.panelStackGroupElement.appendChild(node);
        }
    }

    setWorkspaceOptions(items: WorkspaceOption[], currentId: string): void {
        if (!Array.isArray(items) || items.length <= 1) {
            this.workspaceMenuElement.replaceChildren();
            this.workspaceMenuOpen = false;
            this.applyWorkspaceMenuState();
            this.workspaceGroupElement.style.display = "none";
            return;
        }

        const current = items.find((item) => item.id === currentId) ?? items[0];
        const mosaic = items.length >= 3;
        const currentMarker = current.id === "core" ? "Core workspace" : "Add-on workspace";
        this.workspaceCurrentMarkerElement.textContent = currentMarker;
        this.workspaceCurrentTitleElement.textContent = current.title;
        this.workspaceCurrentSubtitleElement.textContent = current.subtitle ?? "";
        this.workspaceCurrentSubtitleElement.style.display = current.subtitle ? "block" : "none";
        this.workspaceCurrentElement.setAttribute("data-molsysviewer-panel-workspace-current", current.id);
        this.workspaceMenuElement.setAttribute("data-molsysviewer-panel-workspace-launcher-mode", mosaic ? "mosaic" : "list");
        Object.assign(this.workspaceMenuElement.style, {
            display: "none",
            gridTemplateColumns: mosaic ? "repeat(2, minmax(0, 1fr))" : "minmax(0, 1fr)",
        });
        this.workspaceMenuElement.replaceChildren();

        const appendSection = (key: string, label: string): void => {
            if (!mosaic) return;
            const section = document.createElement("div");
            section.setAttribute("data-molsysviewer-panel-workspace-section", key);
            section.textContent = label;
            Object.assign(section.style, {
                gridColumn: "1 / -1",
                fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
                fontSize: "10px",
                fontWeight: "700",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "rgba(244,244,245,0.58)",
                padding: "4px 2px 0 2px",
            });
            this.workspaceMenuElement.appendChild(section);
        };

        const appendOption = (item: WorkspaceOption, fullSpan = false): void => {
            const button = document.createElement("button");
            button.type = "button";
            button.setAttribute("data-molsysviewer-panel-workspace-option", item.id);
            Object.assign(button.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: "5px",
                width: "100%",
                border: item.id === current.id ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(255,255,255,0.08)",
                borderRadius: "12px",
                background: item.id === current.id ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.03)",
                color: item.id === current.id ? "#f4f4f5" : "rgba(244,244,245,0.82)",
                fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
                fontSize: "11px",
                lineHeight: "1.2",
                minHeight: mosaic ? "72px" : "0",
                padding: mosaic ? "10px 11px" : "8px 10px",
                cursor: "pointer",
                textAlign: "left",
            });
            if (fullSpan && mosaic) button.style.gridColumn = "1 / -1";
            const title = document.createElement("span");
            title.setAttribute("data-molsysviewer-panel-workspace-option-title", item.id);
            title.textContent = item.title;
            button.appendChild(title);
            if (item.subtitle) {
                const subtitle = document.createElement("span");
                subtitle.setAttribute("data-molsysviewer-panel-workspace-option-subtitle", item.id);
                subtitle.textContent = item.subtitle;
                Object.assign(subtitle.style, {
                    fontSize: "10px",
                    lineHeight: "1.25",
                    color: item.id === current.id ? "rgba(244,244,245,0.78)" : "rgba(244,244,245,0.62)",
                });
                button.appendChild(subtitle);
            }
            if (item.id === current.id) {
                const marker = document.createElement("span");
                marker.setAttribute("data-molsysviewer-panel-workspace-option-marker", item.id);
                marker.textContent = "Current";
                Object.assign(marker.style, {
                    fontSize: "10px",
                    lineHeight: "1.1",
                    color: "rgba(244,244,245,0.74)",
                });
                button.appendChild(marker);
            } else if (item.id === "core") {
                const marker = document.createElement("span");
                marker.setAttribute("data-molsysviewer-panel-workspace-option-marker", item.id);
                marker.textContent = "Core";
                Object.assign(marker.style, {
                    fontSize: "10px",
                    lineHeight: "1.1",
                    color: "rgba(244,244,245,0.54)",
                });
                button.appendChild(marker);
            }
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.workspaceMenuOpen = false;
                this.applyWorkspaceMenuState();
                this.onSelectWorkspace?.(item.id);
            });
            this.workspaceMenuElement.appendChild(button);
        };

        if (mosaic) {
            const coreItems = items.filter((item) => item.id === "core");
            const addonItems = items.filter((item) => item.id !== "core");
            if (coreItems.length > 0) {
                appendSection("core", "Core");
                for (const item of coreItems) appendOption(item, true);
            }
            if (addonItems.length > 0) {
                appendSection("addons", "Add-ons");
                for (const item of addonItems) appendOption(item, false);
            }
        } else {
            for (const item of items) appendOption(item, false);
        }

        this.workspaceMenuOpen = false;
        this.applyWorkspaceMenuState();
        this.workspaceGroupElement.style.display = "inline-flex";
    }

    private applyWorkspaceMenuState(): void {
        const mode = this.workspaceMenuElement.getAttribute("data-molsysviewer-panel-workspace-launcher-mode");
        this.workspaceMenuElement.style.display = this.workspaceMenuOpen ? (mode === "mosaic" ? "grid" : "flex") : "none";
        this.workspaceGroupElement.setAttribute("data-molsysviewer-panel-workspace-launcher-open", this.workspaceMenuOpen ? "true" : "false");
    }

    dispose(): void {
        this.panelResizeObserver?.disconnect();
        this.root.remove();
    }
}
