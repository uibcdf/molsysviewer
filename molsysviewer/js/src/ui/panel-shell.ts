type PanelShellOptions = {
    title: string;
    width?: number;
    toggleWidth?: number;
    navButtonLabel?: string;
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

export class PanelShell {
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
    public readonly width: number;
    public readonly toggleWidth: number;
    private readonly workspaceCurrentElement: HTMLButtonElement;
    private readonly workspaceCurrentMarkerElement: HTMLSpanElement;
    private readonly workspaceCurrentTitleElement: HTMLSpanElement;
    private readonly workspaceCurrentSubtitleElement: HTMLSpanElement;
    private readonly workspaceMenuElement: HTMLDivElement;
    private onSelectPanel?: (panelId: string) => void;
    private visible = false;
    private onSelectWorkspace?: (workspaceId: string) => void;
    private workspaceMenuOpen = false;

    constructor(host: HTMLElement, options: PanelShellOptions) {
        const width = options.width ?? 240;
        const toggleWidth = options.toggleWidth ?? 26;
        this.width = width;
        this.toggleWidth = toggleWidth;

        this.root = document.createElement("div");
        Object.assign(this.root.style, {
            position: "absolute",
            left: "0",
            top: "14px",
            bottom: "14px",
            width: `${width + toggleWidth}px`,
            display: "none",
            alignItems: "stretch",
            pointerEvents: "auto",
            zIndex: "16",
            overflow: "hidden",
            transform: `translateX(-${width}px)`,
            transition: "transform 160ms ease",
        });

        this.panel = document.createElement("div");
        Object.assign(this.panel.style, {
            pointerEvents: "auto",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            gap: "8px",
            width: `${width}px`,
            minWidth: `${width}px`,
            maxWidth: `${width}px`,
            boxSizing: "border-box",
            height: "100%",
            overflow: "hidden",
            padding: "10px",
            borderRadius: "0 14px 14px 0",
            border: "1px solid rgba(255,255,255,0.14)",
            borderLeft: "0",
            background: "rgba(18, 18, 22, 0.92)",
            color: "#f4f4f5",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "12px",
        });

        this.headerElement = document.createElement("div");
        Object.assign(this.headerElement.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            paddingBottom: "2px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
        });

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
        this.panelStackGroupElement.setAttribute("data-molsysviewer-panel-stack", "true");
        Object.assign(this.panelStackGroupElement.style, {
            display: "none",
            alignItems: "center",
            gap: "4px",
            flexWrap: "wrap",
        });
        this.headerElement.appendChild(this.panelStackGroupElement);

        this.workspaceGroupElement = document.createElement("div");
        this.workspaceGroupElement.setAttribute("data-molsysviewer-panel-workspace-group", "true");
        Object.assign(this.workspaceGroupElement.style, {
            display: "none",
            position: "relative",
            alignItems: "center",
            marginLeft: "auto",
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
        this.workspaceCurrentMarkerElement.setAttribute("data-molsysviewer-panel-workspace-current-marker", "true");
        Object.assign(this.workspaceCurrentMarkerElement.style, {
            fontSize: "9px",
            fontWeight: "700",
            lineHeight: "1.1",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "rgba(244,244,245,0.52)",
        });
        this.workspaceCurrentTitleElement = document.createElement("span");
        this.workspaceCurrentTitleElement.setAttribute("data-molsysviewer-panel-workspace-current-title", "true");
        Object.assign(this.workspaceCurrentTitleElement.style, {
            fontSize: "11px",
            fontWeight: "700",
            lineHeight: "1.1",
            color: "#f4f4f5",
        });
        this.workspaceCurrentSubtitleElement = document.createElement("span");
        this.workspaceCurrentSubtitleElement.setAttribute("data-molsysviewer-panel-workspace-current-subtitle", "true");
        Object.assign(this.workspaceCurrentSubtitleElement.style, {
            fontSize: "10px",
            lineHeight: "1.2",
            color: "rgba(244,244,245,0.68)",
        });
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentMarkerElement);
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentTitleElement);
        this.workspaceCurrentElement.appendChild(this.workspaceCurrentSubtitleElement);
        this.workspaceCurrentElement.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (this.workspaceMenuElement.childElementCount <= 0) return;
            this.workspaceMenuOpen = !this.workspaceMenuOpen;
            this.applyWorkspaceMenuState();
        });

        this.workspaceMenuElement = document.createElement("div");
        this.workspaceMenuElement.setAttribute("data-molsysviewer-panel-workspace-launcher", "true");
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
        this.workspaceGroupElement.appendChild(this.workspaceCurrentElement);
        this.workspaceGroupElement.appendChild(this.workspaceMenuElement);
        this.headerElement.appendChild(this.workspaceGroupElement);

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
        });

        this.toggleButton = document.createElement("button");
        this.toggleButton.type = "button";
        Object.assign(this.toggleButton.style, {
            pointerEvents: "auto",
            alignSelf: "center",
            marginLeft: "0",
            width: `${toggleWidth}px`,
            minWidth: `${toggleWidth}px`,
            height: "54px",
            border: "1px solid rgba(255,255,255,0.14)",
            borderLeft: "0",
            borderRadius: "0 10px 10px 0",
            background: "rgba(18, 18, 22, 0.92)",
            color: "rgba(248, 250, 252, 0.94)",
            cursor: "pointer",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "16px",
            fontWeight: "700",
        });
        this.toggleButton.textContent = ">";

        this.panel.appendChild(this.headerElement);
        this.panel.appendChild(this.content);
        this.root.appendChild(this.panel);
        this.root.appendChild(this.toggleButton);
        host.appendChild(this.root);
    }

    setVisible(visible: boolean): void {
        this.visible = visible;
        this.root.style.display = visible ? "flex" : "none";
        if (!visible) {
            this.workspaceMenuOpen = false;
            this.applyWorkspaceMenuState();
        }
    }

    isVisible(): boolean {
        return this.visible;
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
            return;
        }

        this.panelStackGroupElement.style.display = "flex";
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

    setExpanded(expanded: boolean): void {
        this.toggleButton.textContent = expanded ? "<" : ">";
        this.root.style.transform = expanded ? "translateX(0)" : `translateX(-${this.width}px)`;
    }

    dispose(): void {
        this.root.remove();
    }
}
