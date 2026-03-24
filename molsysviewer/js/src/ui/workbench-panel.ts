import { PanelShell } from "./panel-shell";

type WorkbenchItem = {
    key?: string;
    title: string;
    subtitle?: string;
    hidden?: boolean;
    active?: boolean;
    context?: boolean;
    onActivate?: () => void;
    onToggleVisibility?: () => void;
};

type SceneSummary = {
    styleTag?: string;
    preset?: string;
    figurePreset?: string;
    figureScale?: number;
    figureVariants?: string[];
};

type AddonSummary = {
    name: string;
    workspaceTitles: string[];
    panelTitles: string[];
    workbenchTitles: string[];
    contextActionTitles: string[];
    exportHelperTitles: string[];
    active?: boolean;
};

type AddonWorkbenchSectionSummary = {
    key: string;
    workspaceId: string;
    title: string;
    itemTitle: string;
    itemSubtitle?: string;
};

type WorkspaceOption = {
    id: string;
    title: string;
    subtitle?: string;
    panelCount?: number;
    workbenchSectionCount?: number;
    contextActionCount?: number;
    exportHelperCount?: number;
};
type WorkspacePanelOption = {
    id: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
    active?: boolean;
};
type ActiveWorkspacePanelSummary = {
    workspaceTitle: string;
    title: string;
    description?: string;
    entry?: string;
    addon?: string;
    contextActionTitles?: string[];
    exportHelperTitles?: string[];
    sections?: Array<{
        key: string;
        title: string;
        itemTitle: string;
        itemSubtitle?: string;
    }>;
};

type BuiltInWorkbenchSectionKey = "annotations" | "measurements" | "shapes" | "scene" | "addons";
type WorkbenchSectionKey = BuiltInWorkbenchSectionKey | `addon:${string}`;

type SectionView = {
    root: HTMLDivElement;
    list: HTMLDivElement;
    empty: HTMLDivElement;
    marker: HTMLSpanElement;
};

export class WorkbenchPanel {
    private readonly shell: PanelShell;
    private readonly root: HTMLDivElement;
    private readonly body: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly workspaceRuntimeDeck: HTMLDivElement;
    private readonly workspaceOverviewHost: HTMLDivElement;
    private readonly workspaceOverviewTitle: HTMLDivElement;
    private readonly workspaceOverviewBody: HTMLDivElement;
    private readonly workspacePanelHost: HTMLDivElement;
    private readonly workspacePanelHostTitle: HTMLDivElement;
    private readonly workspacePanelHostBody: HTMLDivElement;
    private readonly sections = new Map<WorkbenchSectionKey, SectionView>();
    private readonly sectionExpanded = new Map<WorkbenchSectionKey, boolean>();
    private readonly builtInSectionKeys: BuiltInWorkbenchSectionKey[] = ["annotations", "measurements", "shapes", "scene", "addons"];
    private addonSectionKeys: WorkbenchSectionKey[] = [];
    private workspaceItems: WorkspaceOption[] = [];
    private workspacePanelItems: WorkspacePanelOption[] = [];
    private currentWorkspaceId = "core";
    private onSelectWorkspace?: (workspaceId: string) => void;
    private onSelectWorkspacePanel?: (panelId: string) => void;
    private activeWorkspacePanelSummary: ActiveWorkspacePanelSummary | null = null;
    private expanded = false;
    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToNavigate?: () => void;

    constructor(private readonly host: HTMLElement) {
        this.shell = new PanelShell(host, { title: "Workbench", width: 240, toggleWidth: 26, navButtonLabel: "Navigate" });
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
        this.shell.navButton?.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.onNavigateToNavigate?.();
        });

        Object.assign(this.body.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "auto",
            gap: "8px",
        });

        this.workspaceRuntimeDeck = document.createElement("div");
        this.workspaceRuntimeDeck.setAttribute("data-molsysviewer-workbench-workspace-runtime-deck", "true");
        Object.assign(this.workspaceRuntimeDeck.style, {
            display: "none",
            flexDirection: "column",
            gap: "8px",
        });
        this.body.appendChild(this.workspaceRuntimeDeck);

        this.workspaceOverviewHost = document.createElement("div");
        this.workspaceOverviewHost.setAttribute("data-molsysviewer-workbench-workspace-overview", "true");
        Object.assign(this.workspaceOverviewHost.style, {
            display: "none",
            flexDirection: "column",
            gap: "6px",
            padding: "10px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.045)",
            border: "1px solid rgba(255,255,255,0.08)",
        });

        this.workspaceOverviewTitle = document.createElement("div");
        this.workspaceOverviewTitle.setAttribute("data-molsysviewer-workbench-workspace-overview-title", "true");
        Object.assign(this.workspaceOverviewTitle.style, {
            fontSize: "11px",
            fontWeight: "700",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "rgba(244,244,245,0.74)",
        });
        this.workspaceOverviewTitle.textContent = "Workspaces";

        this.workspaceOverviewBody = document.createElement("div");
        this.workspaceOverviewBody.setAttribute("data-molsysviewer-workbench-workspace-overview-body", "true");
        Object.assign(this.workspaceOverviewBody.style, {
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "6px",
        });

        this.workspaceOverviewHost.appendChild(this.workspaceOverviewTitle);
        this.workspaceOverviewHost.appendChild(this.workspaceOverviewBody);
        this.workspaceRuntimeDeck.appendChild(this.workspaceOverviewHost);

        this.workspacePanelHost = document.createElement("div");
        this.workspacePanelHost.setAttribute("data-molsysviewer-workbench-workspace-panel-host", "true");
        Object.assign(this.workspacePanelHost.style, {
            display: "none",
            flexDirection: "column",
            gap: "6px",
            padding: "10px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.06)",
        });

        this.workspacePanelHostTitle = document.createElement("div");
        this.workspacePanelHostTitle.setAttribute("data-molsysviewer-workbench-workspace-panel-title", "true");
        Object.assign(this.workspacePanelHostTitle.style, {
            fontSize: "12px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.96)",
        });

        this.workspacePanelHostBody = document.createElement("div");
        this.workspacePanelHostBody.setAttribute("data-molsysviewer-workbench-workspace-panel-body", "true");
        Object.assign(this.workspacePanelHostBody.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            fontSize: "12px",
            color: "rgba(244,244,245,0.78)",
        });

        this.workspacePanelHost.appendChild(this.workspacePanelHostTitle);
        this.workspacePanelHost.appendChild(this.workspacePanelHostBody);
        this.workspaceRuntimeDeck.appendChild(this.workspacePanelHost);

        this.createSection("annotations", "Annotations", "No annotations yet.");
        this.createSection("measurements", "Measurements", "No measurements yet.");
        this.createSection("shapes", "Shapes", "No shapes yet.");
        this.createSection("scene", "Scene", "No scene style selected.");
        this.createSection("addons", "Add-ons", "No add-ons active.");

        this.applyExpandedState();
        this.setVisible(false);
    }

    setVisible(visible: boolean): void {
        this.shell.setVisible(visible);
        if (!visible && this.expanded) {
            this.expanded = false;
            this.applyExpandedState();
        }
    }

    isVisible(): boolean {
        return this.shell.isVisible();
    }

    setExpanded(expanded: boolean): void {
        this.expanded = expanded;
        this.applyExpandedState();
    }

    isExpanded(): boolean {
        return this.expanded;
    }

    setOnExpandedChange(callback: ((expanded: boolean) => void) | undefined): void {
        this.onExpandedChange = callback;
    }

    setOnNavigateToNavigate(callback: (() => void) | undefined, label = "Navigate"): void {
        this.onNavigateToNavigate = callback;
        this.shell.setNavButtonLabel(callback ? label : undefined);
    }

    setWorkspaces(items: WorkspaceOption[], currentId: string, onSelect: ((workspaceId: string) => void) | undefined): void {
        this.workspaceItems = Array.isArray(items) ? items : [];
        this.currentWorkspaceId = currentId;
        this.onSelectWorkspace = onSelect;
        this.shell.setOnSelectWorkspace(onSelect);
        this.shell.setWorkspaceOptions(items, currentId);
        this.renderWorkspaceOverview();
    }

    setWorkspacePanels(
        items: WorkspacePanelOption[],
        onSelect: ((panelId: string) => void) | undefined,
    ): void {
        this.workspacePanelItems = Array.isArray(items) ? items : [];
        this.onSelectWorkspacePanel = onSelect;
        this.shell.setOnSelectPanel(onSelect);
        this.shell.setPanelOptions(items.map((item) => ({
            id: item.id,
            title: item.title,
            active: item.active,
        })));
        this.renderWorkspaceOverview();
    }

    setActiveWorkspacePanel(summary: ActiveWorkspacePanelSummary | null): void {
        this.activeWorkspacePanelSummary = summary;
        this.renderWorkspaceOverview();
        this.workspacePanelHostBody.replaceChildren();
        if (!summary) {
            this.workspacePanelHost.style.display = "none";
            return;
        }

        this.workspacePanelHost.style.display = "flex";
        this.workspacePanelHostTitle.textContent = `${summary.workspaceTitle} · ${summary.title}`;

        if (summary.description) {
            const description = document.createElement("div");
            description.setAttribute("data-molsysviewer-workbench-workspace-panel-description", "true");
            description.textContent = summary.description;
            this.workspacePanelHostBody.appendChild(description);
        }
        if (summary.entry) {
            const entry = document.createElement("div");
            entry.setAttribute("data-molsysviewer-workbench-workspace-panel-entry", "true");
            entry.textContent = `Entry: ${summary.entry}`;
            this.workspacePanelHostBody.appendChild(entry);
        }
        if (summary.addon) {
            const addon = document.createElement("div");
            addon.setAttribute("data-molsysviewer-workbench-workspace-panel-addon", "true");
            addon.textContent = `Add-on: ${summary.addon}`;
            this.workspacePanelHostBody.appendChild(addon);
        }
        if ((summary.contextActionTitles?.length ?? 0) > 0 || (summary.exportHelperTitles?.length ?? 0) > 0) {
            const capabilities = document.createElement("div");
            capabilities.setAttribute("data-molsysviewer-workbench-workspace-panel-capabilities", "true");
            Object.assign(capabilities.style, {
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                marginTop: "4px",
            });

            if ((summary.contextActionTitles?.length ?? 0) > 0) {
                const context = document.createElement("div");
                context.setAttribute("data-molsysviewer-workbench-workspace-panel-context-actions", "true");
                context.textContent = `Context: ${summary.contextActionTitles!.join(", ")}`;
                capabilities.appendChild(context);
            }

            if ((summary.exportHelperTitles?.length ?? 0) > 0) {
                const exports = document.createElement("div");
                exports.setAttribute("data-molsysviewer-workbench-workspace-panel-export-helpers", "true");
                exports.textContent = `Export: ${summary.exportHelperTitles!.join(", ")}`;
                capabilities.appendChild(exports);
            }

            this.workspacePanelHostBody.appendChild(capabilities);
        }
        if (Array.isArray(summary.sections) && summary.sections.length > 0) {
            const sectionsBlock = document.createElement("div");
            sectionsBlock.setAttribute("data-molsysviewer-workbench-workspace-panel-sections", "true");
            Object.assign(sectionsBlock.style, {
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                marginTop: "4px",
            });

            for (const section of summary.sections) {
                const sectionCard = document.createElement("div");
                sectionCard.setAttribute("data-molsysviewer-workbench-workspace-panel-section", section.key);
                Object.assign(sectionCard.style, {
                    display: "flex",
                    flexDirection: "column",
                    gap: "3px",
                    padding: "8px",
                    borderRadius: "8px",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.06)",
                });

                const sectionTitle = document.createElement("div");
                sectionTitle.setAttribute("data-molsysviewer-workbench-workspace-panel-section-title", section.key);
                Object.assign(sectionTitle.style, {
                    fontSize: "11px",
                    fontWeight: "700",
                    color: "rgba(244,244,245,0.90)",
                });
                sectionTitle.textContent = section.title;

                const itemTitle = document.createElement("div");
                itemTitle.setAttribute("data-molsysviewer-workbench-workspace-panel-section-item", section.key);
                itemTitle.textContent = section.itemTitle;

                sectionCard.appendChild(sectionTitle);
                sectionCard.appendChild(itemTitle);

                if (section.itemSubtitle) {
                    const itemSubtitle = document.createElement("div");
                    itemSubtitle.setAttribute("data-molsysviewer-workbench-workspace-panel-section-subtitle", section.key);
                    Object.assign(itemSubtitle.style, {
                        fontSize: "11px",
                        color: "rgba(244,244,245,0.62)",
                    });
                    itemSubtitle.textContent = section.itemSubtitle;
                    sectionCard.appendChild(itemSubtitle);
                }

                sectionsBlock.appendChild(sectionCard);
            }

            this.workspacePanelHostBody.appendChild(sectionsBlock);
        }
    }

    private renderWorkspaceOverview(): void {
        const items = this.workspaceItems;
        const currentId = this.currentWorkspaceId;
        const onSelect = this.onSelectWorkspace;
        this.workspaceOverviewBody.replaceChildren();

        if (!Array.isArray(items) || items.length <= 1) {
            this.workspaceRuntimeDeck.style.display = this.activeWorkspacePanelSummary ? "flex" : "none";
            this.workspaceOverviewHost.style.display = "none";
            return;
        }

        const mosaic = items.length >= 3;
        this.workspaceRuntimeDeck.style.display = "flex";
        this.workspaceOverviewHost.style.display = "flex";
        this.workspaceOverviewBody.style.gridTemplateColumns = mosaic ? "repeat(2, minmax(0, 1fr))" : "minmax(0, 1fr)";

        const appendSection = (key: string, label: string): void => {
            if (!mosaic) return;
            const section = document.createElement("div");
            section.setAttribute("data-molsysviewer-workbench-workspace-overview-section", key);
            section.textContent = label;
            Object.assign(section.style, {
                gridColumn: "1 / -1",
                fontSize: "10px",
                fontWeight: "700",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "rgba(244,244,245,0.54)",
                padding: "2px 1px 0 1px",
            });
            this.workspaceOverviewBody.appendChild(section);
        };

        const appendCard = (item: WorkspaceOption, fullSpan = false): void => {
            const card = document.createElement("button");
            card.type = "button";
            card.setAttribute("data-molsysviewer-workbench-workspace-overview-card", item.id);
            const isCurrent = item.id === currentId;
            if (item.id === currentId) {
                card.setAttribute("data-molsysviewer-workbench-workspace-overview-current", item.id);
            }
            Object.assign(card.style, {
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: "5px",
                width: "100%",
                minHeight: mosaic ? "72px" : "0",
                padding: mosaic ? "10px 11px" : "8px 10px",
                borderRadius: "10px",
                border: isCurrent ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(255,255,255,0.07)",
                background: isCurrent ? "rgba(255,255,255,0.09)" : "rgba(255,255,255,0.03)",
                color: isCurrent ? "#f4f4f5" : "rgba(244,244,245,0.82)",
                cursor: "pointer",
                textAlign: "left",
            });
            if (fullSpan && mosaic) card.style.gridColumn = "1 / -1";

            const title = document.createElement("div");
            title.setAttribute("data-molsysviewer-workbench-workspace-overview-card-title", item.id);
            Object.assign(title.style, {
                fontSize: "12px",
                fontWeight: "700",
            });
            title.textContent = item.title;
            card.appendChild(title);

            const subtitleText = isCurrent && this.activeWorkspacePanelSummary
                ? `Panel: ${this.activeWorkspacePanelSummary.title}`
                : item.subtitle;
            if (subtitleText) {
                const subtitle = document.createElement("div");
                subtitle.setAttribute("data-molsysviewer-workbench-workspace-overview-card-subtitle", item.id);
                Object.assign(subtitle.style, {
                    fontSize: "11px",
                    lineHeight: "1.25",
                    color: isCurrent ? "rgba(244,244,245,0.72)" : "rgba(244,244,245,0.58)",
                });
                subtitle.textContent = subtitleText;
                card.appendChild(subtitle);
            }

            if (isCurrent && this.activeWorkspacePanelSummary?.entry) {
                const entry = document.createElement("div");
                entry.setAttribute("data-molsysviewer-workbench-workspace-overview-card-entry", item.id);
                Object.assign(entry.style, {
                    fontSize: "10px",
                    lineHeight: "1.2",
                    color: "rgba(244,244,245,0.58)",
                });
                entry.textContent = `Entry: ${this.activeWorkspacePanelSummary.entry}`;
                card.appendChild(entry);
            }

            const overviewCapabilityTexts: string[] = [];
            if ((item.panelCount ?? 0) > 0) overviewCapabilityTexts.push(`${item.panelCount} panel${item.panelCount === 1 ? "" : "s"}`);
            if ((item.workbenchSectionCount ?? 0) > 0) overviewCapabilityTexts.push(`${item.workbenchSectionCount} section${item.workbenchSectionCount === 1 ? "" : "s"}`);
            if ((item.contextActionCount ?? 0) > 0) overviewCapabilityTexts.push(`${item.contextActionCount} context`);
            if ((item.exportHelperCount ?? 0) > 0) overviewCapabilityTexts.push(`${item.exportHelperCount} export`);

            if (overviewCapabilityTexts.length > 0) {
                const capabilities = document.createElement("div");
                capabilities.setAttribute("data-molsysviewer-workbench-workspace-overview-card-capabilities", item.id);
                Object.assign(capabilities.style, {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px",
                    marginTop: "2px",
                });

                for (const text of overviewCapabilityTexts) {
                    const chip = document.createElement("div");
                    chip.setAttribute("data-molsysviewer-workbench-workspace-overview-card-capability", text.toLowerCase().replace(/\s+/g, "-"));
                    Object.assign(chip.style, {
                        padding: "3px 7px",
                        borderRadius: "999px",
                        border: "1px solid rgba(255,255,255,0.08)",
                        background: isCurrent ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.035)",
                        fontSize: "10px",
                        fontWeight: "700",
                        color: isCurrent ? "rgba(244,244,245,0.82)" : "rgba(244,244,245,0.72)",
                    });
                    chip.textContent = text;
                    capabilities.appendChild(chip);
                }

                card.appendChild(capabilities);
            }

            if (isCurrent && this.activeWorkspacePanelSummary) {
                const preview = document.createElement("div");
                preview.setAttribute("data-molsysviewer-workbench-workspace-overview-preview", item.id);
                Object.assign(preview.style, {
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    width: "100%",
                    marginTop: "2px",
                    padding: "8px",
                    borderRadius: "8px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.08)",
                });

                if (this.activeWorkspacePanelSummary.description) {
                    const description = document.createElement("div");
                    description.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-description", item.id);
                    Object.assign(description.style, {
                        fontSize: "11px",
                        lineHeight: "1.3",
                        color: "rgba(244,244,245,0.72)",
                    });
                    description.textContent = this.activeWorkspacePanelSummary.description;
                    preview.appendChild(description);
                }

                const capabilityTexts: string[] = [];
                if ((this.activeWorkspacePanelSummary.contextActionTitles?.length ?? 0) > 0) {
                    capabilityTexts.push(`Context ${this.activeWorkspacePanelSummary.contextActionTitles!.length}`);
                }
                if ((this.activeWorkspacePanelSummary.exportHelperTitles?.length ?? 0) > 0) {
                    capabilityTexts.push(`Export ${this.activeWorkspacePanelSummary.exportHelperTitles!.length}`);
                }
                if ((this.activeWorkspacePanelSummary.sections?.length ?? 0) > 0) {
                    capabilityTexts.push(`Sections ${this.activeWorkspacePanelSummary.sections!.length}`);
                }

                if (capabilityTexts.length > 0) {
                    const capabilities = document.createElement("div");
                    capabilities.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-capabilities", item.id);
                    Object.assign(capabilities.style, {
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "4px",
                    });

                    for (const text of capabilityTexts) {
                        const chip = document.createElement("div");
                        chip.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-capability", text.toLowerCase().replace(/\s+/g, "-"));
                        Object.assign(chip.style, {
                            padding: "3px 7px",
                            borderRadius: "999px",
                            border: "1px solid rgba(255,255,255,0.08)",
                            background: "rgba(255,255,255,0.04)",
                            fontSize: "10px",
                            fontWeight: "700",
                            color: "rgba(244,244,245,0.76)",
                        });
                        chip.textContent = text;
                        capabilities.appendChild(chip);
                    }

                    preview.appendChild(capabilities);
                }

                if ((this.activeWorkspacePanelSummary.sections?.length ?? 0) > 0) {
                    const sections = document.createElement("div");
                    sections.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-sections", item.id);
                    Object.assign(sections.style, {
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                    });

                    for (const section of this.activeWorkspacePanelSummary.sections!.slice(0, 2)) {
                        const sectionRow = document.createElement("div");
                        sectionRow.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-section", section.key);
                        Object.assign(sectionRow.style, {
                            display: "flex",
                            flexDirection: "column",
                            gap: "2px",
                        });

                        const sectionTitle = document.createElement("div");
                        sectionTitle.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-section-title", section.key);
                        Object.assign(sectionTitle.style, {
                            fontSize: "10px",
                            fontWeight: "700",
                            letterSpacing: "0.04em",
                            textTransform: "uppercase",
                            color: "rgba(244,244,245,0.54)",
                        });
                        sectionTitle.textContent = section.title;
                        sectionRow.appendChild(sectionTitle);

                        const sectionItem = document.createElement("div");
                        sectionItem.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-section-item", section.key);
                        Object.assign(sectionItem.style, {
                            fontSize: "11px",
                            color: "rgba(244,244,245,0.78)",
                        });
                        sectionItem.textContent = section.itemTitle;
                        sectionRow.appendChild(sectionItem);

                        if (section.itemSubtitle) {
                            const sectionSubtitle = document.createElement("div");
                            sectionSubtitle.setAttribute("data-molsysviewer-workbench-workspace-overview-preview-section-subtitle", section.key);
                            Object.assign(sectionSubtitle.style, {
                                fontSize: "10px",
                                color: "rgba(244,244,245,0.58)",
                            });
                            sectionSubtitle.textContent = section.itemSubtitle;
                            sectionRow.appendChild(sectionSubtitle);
                        }

                        sections.appendChild(sectionRow);
                    }

                    preview.appendChild(sections);
                }

                card.appendChild(preview);
            }

            if (isCurrent && this.workspacePanelItems.length > 0) {
                const panelStrip = document.createElement("div");
                panelStrip.setAttribute("data-molsysviewer-workbench-workspace-overview-panels", item.id);
                Object.assign(panelStrip.style, {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px",
                    marginTop: "2px",
                });

                for (const panel of this.workspacePanelItems) {
                    const panelButton = document.createElement("button");
                    panelButton.type = "button";
                    panelButton.setAttribute("data-molsysviewer-workbench-workspace-overview-panel", panel.id);
                    if (panel.active) {
                        panelButton.setAttribute("data-molsysviewer-workbench-workspace-overview-panel-current", panel.id);
                    }
                    Object.assign(panelButton.style, {
                        padding: "3px 7px",
                        borderRadius: "999px",
                        border: panel.active ? "1px solid rgba(255,255,255,0.18)" : "1px solid rgba(255,255,255,0.08)",
                        background: panel.active ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.04)",
                        color: panel.active ? "#f4f4f5" : "rgba(244,244,245,0.76)",
                        fontSize: "10px",
                        fontWeight: "700",
                        cursor: "pointer",
                    });
                    panelButton.textContent = panel.title;
                    panelButton.addEventListener("click", (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        this.onSelectWorkspacePanel?.(panel.id);
                    });
                    panelStrip.appendChild(panelButton);
                }

                card.appendChild(panelStrip);
            }

            const marker = document.createElement("div");
            marker.setAttribute("data-molsysviewer-workbench-workspace-overview-card-marker", item.id);
            Object.assign(marker.style, {
                fontSize: "10px",
                fontWeight: "700",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                color: isCurrent ? "rgba(244,244,245,0.72)" : "rgba(244,244,245,0.48)",
            });
            marker.textContent = isCurrent ? "Current workspace" : "Open workspace";
            card.appendChild(marker);

            card.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                onSelect?.(item.id);
            });
            this.workspaceOverviewBody.appendChild(card);
        };

        if (mosaic) {
            const currentItems = items.filter((item) => item.id === currentId);
            const remainingCoreItems = items.filter((item) => item.id === "core" && item.id !== currentId);
            const remainingAddonItems = items.filter((item) => item.id !== "core" && item.id !== currentId);
            if (currentItems.length > 0) {
                appendSection("current", "Current");
                for (const item of currentItems) appendCard(item, true);
            }
            if (remainingCoreItems.length > 0) {
                appendSection("core", "Core");
                for (const item of remainingCoreItems) appendCard(item, true);
            }
            if (remainingAddonItems.length > 0) {
                appendSection("addons", "Add-ons");
                for (const item of remainingAddonItems) appendCard(item, false);
            }
        } else {
            for (const item of items) appendCard(item, false);
        }
    }

    setAnnotations(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("annotations")!, items);
        this.applySectionExpandedState("annotations");
    }

    setMeasurements(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("measurements")!, items);
        this.applySectionExpandedState("measurements");
    }

    setShapes(items: WorkbenchItem[]): void {
        this.renderItems(this.sections.get("shapes")!, items);
        this.applySectionExpandedState("shapes");
    }

    setScene(summary: SceneSummary | null): void {
        const items: WorkbenchItem[] = [];
        if (summary?.styleTag) items.push({ title: `Style: ${summary.styleTag}` });
        if (summary?.preset) items.push({ title: `Preset: ${summary.preset}` });
        if (summary?.figurePreset || summary?.figureScale) {
            const scale = typeof summary?.figureScale === "number" ? `${summary.figureScale.toFixed(1)}x` : undefined;
            items.push({
                title: `Figure: ${summary?.figurePreset ?? "publication-light"}${scale ? ` @ ${scale}` : ""}`,
            });
        }
        if ((summary?.figureVariants?.length ?? 0) > 0) {
            items.push({ title: `Variants: ${summary!.figureVariants!.join(", ")}` });
        }
        this.renderItems(this.sections.get("scene")!, items);
        this.applySectionExpandedState("scene");
    }

    setAddons(items: AddonSummary[]): void {
        this.renderItems(
            this.sections.get("addons")!,
            items.map((item) => ({
                key: item.name,
                title: item.name,
                active: item.active,
                subtitle: [
                    item.workspaceTitles.length > 0 ? `Workspaces: ${item.workspaceTitles.join(", ")}` : null,
                    item.panelTitles.length > 0 ? `Panels: ${item.panelTitles.join(", ")}` : null,
                    item.workbenchTitles.length > 0 ? `Workbench: ${item.workbenchTitles.join(", ")}` : null,
                    item.contextActionTitles.length > 0 ? `Context: ${item.contextActionTitles.join(", ")}` : null,
                    item.exportHelperTitles.length > 0 ? `Export: ${item.exportHelperTitles.join(", ")}` : null,
                ].filter(Boolean).join(" · "),
            })),
        );
        this.applySectionExpandedState("addons");
    }

    setAddonWorkbenchSections(items: AddonWorkbenchSectionSummary[]): void {
        const nextKeys = new Set<WorkbenchSectionKey>();
        for (const item of items) {
            const key = (`addon:${item.key}`) as WorkbenchSectionKey;
            nextKeys.add(key);
            if (!this.sections.has(key)) {
                this.createSection(key, item.title, "Add-on section registered.");
            }
            const section = this.sections.get(key)!;
            this.renderItems(section, [{ key: item.key, title: item.itemTitle, subtitle: item.itemSubtitle }]);
            this.applySectionExpandedState(key);
        }

        for (const key of this.addonSectionKeys) {
            if (nextKeys.has(key)) continue;
            const section = this.sections.get(key);
            section?.root.remove();
            this.sections.delete(key);
            this.sectionExpanded.delete(key);
        }

        this.addonSectionKeys = Array.from(nextKeys);
        this.reorderSections();
    }

    dispose(): void {
        this.shell.dispose();
    }

    private applyExpandedState(): void {
        this.toggleButton.textContent = this.expanded ? ">" : "<";
        this.root.style.transform = this.expanded ? "translateX(0)" : "translateX(240px)";
        this.onExpandedChange?.(this.expanded);
    }

    private createSection(key: WorkbenchSectionKey, title: string, emptyText: string): SectionView {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-workbench-section", key);
        Object.assign(section.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "8px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
        });

        const header = document.createElement("button");
        header.type = "button";
        header.setAttribute("data-molsysviewer-workbench-section-toggle", key);
        Object.assign(header.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.88)",
            background: "transparent",
            border: "0",
            padding: "0",
            cursor: "pointer",
            textAlign: "left",
        });
        const headerTitle = document.createElement("span");
        headerTitle.textContent = title;
        const headerMarker = document.createElement("span");
        headerMarker.setAttribute("data-molsysviewer-workbench-section-marker", key);
        headerMarker.textContent = "−";
        Object.assign(headerMarker.style, {
            color: "rgba(244,244,245,0.52)",
            fontSize: "12px",
            lineHeight: "1",
        });
        header.appendChild(headerTitle);
        header.appendChild(headerMarker);
        header.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.sectionExpanded.set(key, !(this.sectionExpanded.get(key) ?? true));
            this.applySectionExpandedState(key);
        });

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

        const view = { root: section, list, empty, marker: headerMarker };
        this.sections.set(key, view);
        this.sectionExpanded.set(key, true);
        return view;
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

    private applySectionExpandedState(key: WorkbenchSectionKey): void {
        const section = this.sections.get(key);
        if (!section) return;
        const expanded = this.sectionExpanded.get(key) ?? true;
        section.marker.textContent = expanded ? "−" : "+";
        section.list.style.display = expanded ? "flex" : "none";
        const hasItems = section.list.children.length > 0;
        section.empty.style.display = expanded && !hasItems ? "block" : "none";
    }

    private reorderSections(): void {
        const orderedKeys: WorkbenchSectionKey[] = [
            ...this.builtInSectionKeys,
            ...this.addonSectionKeys.sort((left, right) => left.localeCompare(right)),
        ];
        for (const key of orderedKeys) {
            const section = this.sections.get(key);
            if (section) this.body.appendChild(section.root);
        }
    }

    private makeRow(item: WorkbenchItem): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-workbench-item", "true");
        if (item.key) row.setAttribute("data-molsysviewer-workbench-item-key", item.key);
        if (item.active) row.setAttribute("data-molsysviewer-workbench-item-active", "true");
        if (item.context) row.setAttribute("data-molsysviewer-workbench-item-context", "true");
        Object.assign(row.style, {
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            padding: "6px 8px",
            borderRadius: "8px",
            background: item.active
                ? "rgba(255,255,255,0.12)"
                : item.context
                    ? "rgba(255,255,255,0.08)"
                : item.hidden
                    ? "rgba(255,255,255,0.03)"
                    : "rgba(255,255,255,0.06)",
            color: item.hidden ? "rgba(244,244,245,0.58)" : "#f4f4f5",
            cursor: item.onActivate ? "pointer" : "default",
            outline: item.active
                ? "1px solid rgba(255,255,255,0.16)"
                : item.context
                    ? "1px solid rgba(255,255,255,0.10)"
                    : "none",
        });
        if (item.onActivate) {
            row.addEventListener("click", (event) => {
                event.preventDefault?.();
                event.stopPropagation?.();
                item.onActivate?.();
            });
        }

        const top = document.createElement("div");
        Object.assign(top.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
        });

        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "12px",
            fontWeight: "600",
            flex: "1 1 auto",
        });
        title.textContent = item.title;
        top.appendChild(title);

        if (item.onToggleVisibility) {
            const visibilityButton = document.createElement("button");
            visibilityButton.type = "button";
            visibilityButton.setAttribute("data-molsysviewer-workbench-item-visibility", item.hidden ? "hidden" : "visible");
            visibilityButton.textContent = item.hidden ? "Show" : "Hide";
            Object.assign(visibilityButton.style, {
                fontSize: "10px",
                color: "rgba(244,244,245,0.72)",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)",
                borderRadius: "999px",
                padding: "1px 6px",
                cursor: "pointer",
            });
            visibilityButton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                item.onToggleVisibility?.();
            });
            top.appendChild(visibilityButton);
        }

        row.appendChild(top);

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
