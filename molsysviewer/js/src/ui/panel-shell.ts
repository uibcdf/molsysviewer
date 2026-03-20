type PanelShellOptions = {
    title: string;
    width?: number;
    toggleWidth?: number;
    navButtonLabel?: string;
};

type WorkspaceOption = {
    id: string;
    title: string;
};

export class PanelShell {
    public readonly root: HTMLDivElement;
    public readonly panel: HTMLDivElement;
    public readonly titleElement: HTMLDivElement;
    public readonly headerElement: HTMLDivElement;
    public readonly navGroupElement?: HTMLDivElement;
    public readonly navButton?: HTMLButtonElement;
    public readonly workspaceGroupElement: HTMLDivElement;
    public readonly content: HTMLDivElement;
    public readonly toggleButton: HTMLButtonElement;
    private readonly width: number;
    private readonly workspaceCurrentElement: HTMLSpanElement;
    private visible = false;
    private onSelectWorkspace?: (workspaceId: string) => void;

    constructor(host: HTMLElement, options: PanelShellOptions) {
        const width = options.width ?? 240;
        const toggleWidth = options.toggleWidth ?? 26;
        this.width = width;

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
            boxShadow: "0 12px 32px rgba(0,0,0,0.28)",
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

        this.workspaceGroupElement = document.createElement("div");
        this.workspaceGroupElement.setAttribute("data-molsysviewer-panel-workspace-group", "true");
        Object.assign(this.workspaceGroupElement.style, {
            display: "none",
            alignItems: "center",
            gap: "4px",
            padding: "3px",
            borderRadius: "999px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginLeft: "auto",
        });
        this.workspaceCurrentElement = document.createElement("span");
        Object.assign(this.workspaceCurrentElement.style, {
            fontSize: "10px",
            fontWeight: "700",
            lineHeight: "1",
            padding: "5px 8px",
            borderRadius: "999px",
            background: "rgba(255,255,255,0.12)",
            color: "#f4f4f5",
        });
        this.workspaceGroupElement.appendChild(this.workspaceCurrentElement);
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
            border: "1px solid rgba(255,255,255,0.16)",
            borderLeft: "0",
            borderRadius: "0 10px 10px 0",
            background: "rgba(18, 18, 22, 0.94)",
            color: "#f4f4f5",
            boxShadow: "0 10px 24px rgba(0,0,0,0.24)",
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

    setWorkspaceOptions(items: WorkspaceOption[], currentId: string): void {
        this.workspaceGroupElement.replaceChildren();

        if (!Array.isArray(items) || items.length <= 1) {
            this.workspaceGroupElement.style.display = "none";
            return;
        }

        const current = items.find((item) => item.id === currentId) ?? items[0];
        this.workspaceCurrentElement.textContent = current.title;
        this.workspaceCurrentElement.setAttribute("data-molsysviewer-panel-workspace-current", current.id);
        this.workspaceGroupElement.appendChild(this.workspaceCurrentElement);

        for (const item of items) {
            if (item.id === current.id) continue;
            const button = document.createElement("button");
            button.type = "button";
            button.setAttribute("data-molsysviewer-panel-workspace", item.id);
            button.textContent = item.title;
            Object.assign(button.style, {
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
            button.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.onSelectWorkspace?.(item.id);
            });
            this.workspaceGroupElement.appendChild(button);
        }

        this.workspaceGroupElement.style.display = "inline-flex";
    }

    setExpanded(expanded: boolean): void {
        this.toggleButton.textContent = expanded ? "<" : ">";
        this.root.style.transform = expanded ? "translateX(0)" : `translateX(-${this.width}px)`;
    }

    dispose(): void {
        this.root.remove();
    }
}
