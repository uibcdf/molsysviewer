import { PanelShell } from "./panel-shell";

type WorkbenchItem = {
    title: string;
    subtitle?: string;
    hidden?: boolean;
    onActivate?: () => void;
};

type SceneSummary = {
    styleTag?: string;
    preset?: string;
};

type WorkbenchSectionKey = "annotations" | "measurements" | "shapes" | "scene";

type SectionView = {
    root: HTMLDivElement;
    list: HTMLDivElement;
    empty: HTMLDivElement;
};

export class WorkbenchPanel {
    private readonly shell: PanelShell;
    private readonly root: HTMLDivElement;
    private readonly body: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly sections: Record<WorkbenchSectionKey, SectionView>;
    private expanded = false;

    constructor(private readonly host: HTMLElement) {
        this.shell = new PanelShell(host, { title: "Workbench", width: 240, toggleWidth: 26 });
        this.root = this.shell.root;
        this.body = this.shell.content;
        this.toggleButton = this.shell.toggleButton;

        this.root.setAttribute("data-molsysviewer-workbench-panel", "true");
        this.shell.titleElement.setAttribute("data-molsysviewer-workbench-panel-title", "true");
        this.body.setAttribute("data-molsysviewer-workbench-panel-body", "true");

        Object.assign(this.root.style, {
            left: "unset",
            right: "0",
            transform: "translateX(240px)",
        });
        Object.assign(this.shell.panel.style, {
            borderLeft: "1px solid rgba(255,255,255,0.14)",
            borderRight: "0",
            borderRadius: "14px 0 0 14px",
        });
        Object.assign(this.toggleButton.style, {
            order: "-1",
            borderLeft: "1px solid rgba(255,255,255,0.16)",
            borderRight: "0",
            borderRadius: "10px 0 0 10px",
            boxShadow: "0 10px 24px rgba(0,0,0,0.18)",
        });

        this.toggleButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.expanded = !this.expanded;
            this.applyExpandedState();
        });

        Object.assign(this.body.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "auto",
            gap: "8px",
        });

        this.sections = {
            annotations: this.createSection("Annotations", "No annotations yet."),
            measurements: this.createSection("Measurements", "No measurements yet."),
            shapes: this.createSection("Shapes", "No shapes yet."),
            scene: this.createSection("Scene", "No scene style selected."),
        };

        this.applyExpandedState();
        this.setVisible(false);
    }

    setVisible(visible: boolean): void {
        this.shell.setVisible(visible);
    }

    setAnnotations(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.annotations, items);
    }

    setMeasurements(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.measurements, items);
    }

    setShapes(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.shapes, items);
    }

    setScene(summary: SceneSummary | null): void {
        const items: WorkbenchItem[] = [];
        if (summary?.styleTag) items.push({ title: `Style: ${summary.styleTag}` });
        if (summary?.preset) items.push({ title: `Preset: ${summary.preset}` });
        this.renderItems(this.sections.scene, items);
    }

    dispose(): void {
        this.shell.dispose();
    }

    private applyExpandedState(): void {
        this.toggleButton.textContent = this.expanded ? ">" : "<";
        this.root.style.transform = this.expanded ? "translateX(0)" : "translateX(240px)";
    }

    private createSection(title: string, emptyText: string): SectionView {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-workbench-section", title.toLowerCase());
        Object.assign(section.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "8px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
        });

        const header = document.createElement("div");
        Object.assign(header.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.88)",
        });
        header.textContent = title;

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const empty = document.createElement("div");
        empty.setAttribute("data-molsysviewer-workbench-empty", title.toLowerCase());
        Object.assign(empty.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.56)",
        });
        empty.textContent = emptyText;

        section.appendChild(header);
        section.appendChild(list);
        section.appendChild(empty);
        this.body.appendChild(section);

        return { root: section, list, empty };
    }

    private renderItems(section: SectionView, items: WorkbenchItem[]): void {
        section.list.replaceChildren();
        if (items.length === 0) {
            section.empty.style.display = "block";
            return;
        }
        section.empty.style.display = "none";
        for (const item of items) {
            section.list.appendChild(this.makeRow(item));
        }
    }

    private makeRow(item: WorkbenchItem): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-workbench-item", "true");
        Object.assign(row.style, {
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            padding: "6px 8px",
            borderRadius: "8px",
            background: item.hidden ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.06)",
            color: item.hidden ? "rgba(244,244,245,0.58)" : "#f4f4f5",
            cursor: item.onActivate ? "pointer" : "default",
        });
        if (item.onActivate) {
            row.addEventListener("click", (event) => {
                event.preventDefault?.();
                event.stopPropagation?.();
                item.onActivate?.();
            });
        }

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "600",
        });
        title.textContent = item.title;
        row.appendChild(title);

        if (item.subtitle) {
            const subtitle = document.createElement("div");
            Object.assign(subtitle.style, {
                fontSize: "11px",
                color: item.hidden ? "rgba(244,244,245,0.45)" : "rgba(244,244,245,0.68)",
            });
            subtitle.textContent = item.subtitle;
            row.appendChild(subtitle);
        }

        return row;
    }
}
