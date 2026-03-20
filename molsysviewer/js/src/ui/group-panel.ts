import { Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, buildGroupItemsFromStructure } from "../managers/active-selection";
import { AddLabelMessage } from "../messages/viewer-messages";
import { ContextMenuTarget } from "./context-menu";
import { GroupStrip } from "./group-strip";
import { PanelShell } from "./panel-shell";

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnInteraction = (item: ActiveSelectionItem, modifiers: { shift: boolean; alt: boolean }) => void;
type OnFocus = (item: ActiveSelectionItem) => void;
type OnHover = (item: ActiveSelectionItem | null) => void;
type OnContext = (item: ActiveSelectionItem, pageX: number, pageY: number) => void;
type OnAnnotationContext = (target: ContextMenuTarget, pageX: number, pageY: number) => void;
type SavedSelectionSummary = { tag: string; atom_count: number };
type RegionSummary = { tag: string; atom_count: number; hidden: boolean };
type SummaryItem = { title: string; subtitle: string; onActivate?: () => void };
type SummarySectionKey = "active" | "saved" | "regions";
type SummarySectionView = {
    root: HTMLDivElement;
    list: HTMLDivElement;
    empty: HTMLDivElement;
};

export class GroupPanel {
    private readonly root: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly body: HTMLDivElement;
    private readonly structureSection: HTMLDivElement;
    private readonly shell: PanelShell;
    private readonly strips = new Map<string, GroupStrip>();
    private readonly summarySections: Record<SummarySectionKey, SummarySectionView>;
    private structure?: Structure;
    private expanded = false;
    private currentSelection: ActiveSelectionPayload = {
        event: "interaction_active_selection_changed",
        source_kind: "empty",
        target_level: "none",
        element_level: "none",
        items: [],
        atom_indices: [],
        group_indices: [],
        component_indices: [],
        chain_indices: [],
        molecule_indices: [],
        entity_indices: [],
        count_atoms: 0,
        count_groups: 0,
        count_shapes: 0,
        count_annotations: 0,
    };
    private readonly annotationMessages: AddLabelMessage[] = [];
    private currentContextTarget: ContextMenuTarget | null = null;
    private readonly collapseStateByChain = new Map<string, { molecules: number[]; components: string[] }>();
    private savedSelections: SavedSelectionSummary[] = [];
    private regions: RegionSummary[] = [];
    private onExpandedChange?: (expanded: boolean) => void;
    private onNavigateToWorkbench?: () => void;

    constructor(
        private readonly host: HTMLElement,
        private readonly onSelect: OnSelect,
        private readonly onInteraction: OnInteraction,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
        private readonly onActivateSavedSelection: (tag: string) => void,
        private readonly onFocusRegion: (tag: string) => void,
    ) {
        this.shell = new PanelShell(this.host, { title: "Navigate", width: 240, toggleWidth: 26, navButtonLabel: "Workbench" });
        this.root = this.shell.root;
        this.toggleButton = this.shell.toggleButton;
        this.body = this.shell.content;

        this.root.setAttribute("data-molsysviewer-group-panel", "true");
        this.toggleButton.setAttribute("data-molsysviewer-group-panel-toggle", "true");
        this.shell.titleElement.setAttribute("data-molsysviewer-group-panel-title", "true");
        this.toggleButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.expanded = !this.expanded;
            this.applyExpandedState();
        });
        this.shell.navButton?.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.onNavigateToWorkbench?.();
        });

        this.body.setAttribute("data-molsysviewer-group-panel-body", "true");
        Object.assign(this.body.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "auto",
            gap: "8px",
        });

        this.structureSection = document.createElement("div");
        this.structureSection.setAttribute("data-molsysviewer-group-panel-section", "structure");
        Object.assign(this.structureSection.style, {
            display: "flex",
            flexDirection: "row",
            gap: "10px",
            overflowX: "auto",
            overflowY: "hidden",
            minHeight: "96px",
        });
        this.body.appendChild(this.makeSectionHeader("Structure"));
        this.body.appendChild(this.structureSection);

        this.summarySections = {
            active: this.createSummarySection("Active", "No active selection."),
            saved: this.createSummarySection("Saved", "No saved selections yet."),
            regions: this.createSummarySection("Regions", "No regions yet."),
        };
    }

    setStructure(structure: Structure | undefined): void {
        this.structure = structure;
        if (!structure) this.annotationMessages.length = 0;
        this.render();
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

    setOnNavigateToWorkbench(callback: (() => void) | undefined): void {
        this.onNavigateToWorkbench = callback;
        this.shell.setNavButtonLabel(callback ? "Workbench" : undefined);
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        for (const strip of this.strips.values()) {
            strip.updateSelection(selection);
        }
        this.renderSummaries();
    }

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.renderSummaries();
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        this.renderSummaries();
    }

    updateContextTarget(target: ContextMenuTarget | null): void {
        this.currentContextTarget = target;
        for (const strip of this.strips.values()) {
            strip.updateContextTarget(target);
        }
    }

    addLabelOverlay(msg: AddLabelMessage): void {
        this.annotationMessages.push(msg);
        for (const strip of this.strips.values()) {
            strip.addLabelOverlay(msg);
        }
    }

    clearAnnotationOverlays(): void {
        this.annotationMessages.length = 0;
        for (const strip of this.strips.values()) {
            strip.clearAnnotationOverlays();
        }
    }

    clearAnnotationOverlaysByTag(tag?: string): void {
        if (!tag) {
            this.clearAnnotationOverlays();
            return;
        }
        for (let index = this.annotationMessages.length - 1; index >= 0; index--) {
            if (this.annotationMessages[index].tag === tag || this.annotationMessages[index].options?.tag === tag) {
                this.annotationMessages.splice(index, 1);
            }
        }
        for (const strip of this.strips.values()) {
            strip.clearAnnotationOverlaysByTag(tag);
        }
    }

    retagAnnotationOverlays(oldTag: string, newTag: string): void {
        for (const message of this.annotationMessages) {
            if (message.tag === oldTag) message.tag = newTag;
            if (message.options?.tag === oldTag) message.options.tag = newTag;
        }
        for (const strip of this.strips.values()) {
            strip.retagAnnotationOverlays(oldTag, newTag);
        }
    }

    focusItem(item: ActiveSelectionItem) {
        const chainName = item.chain_name ?? "?";
        return this.strips.get(chainName)?.focusItem(item) ?? null;
    }

    dispose(): void {
        this.captureCollapseState();
        for (const strip of this.strips.values()) strip.dispose();
        this.strips.clear();
        this.shell.dispose();
    }

    private applyExpandedState(): void {
        this.shell.setExpanded(this.expanded);
        this.onExpandedChange?.(this.expanded);
    }

    private render(): void {
        this.captureCollapseState();
        const grouped = new Map<string, ActiveSelectionItem[]>();
        const items = this.structure ? buildGroupItemsFromStructure(this.structure) : [];
        for (const item of items) {
            const chain = item.chain_name ?? "?";
            if (!grouped.has(chain)) grouped.set(chain, []);
            grouped.get(chain)!.push(item);
        }

        const nextChains = new Set(grouped.keys());
        for (const [chain, strip] of this.strips.entries()) {
            if (nextChains.has(chain)) continue;
            this.collapseStateByChain.set(chain, strip.getCollapseState());
            strip.dispose();
            this.strips.delete(chain);
        }

        const visible = Boolean(this.structure) && grouped.size > 0;
        this.shell.setVisible(visible);
        if (!visible && this.expanded) {
            this.expanded = false;
        }
        if (!this.structure || grouped.size === 0) return;

        for (const [chain, chainItems] of grouped.entries()) {
            let strip = this.strips.get(chain);
            if (!strip) {
                strip = new GroupStrip(this.structureSection, chain, this.onSelect, this.onInteraction, this.onFocus, this.onHover, this.onContext, this.onAnnotationContext);
                this.strips.set(chain, strip);
            }
            strip.setData(this.structure, chainItems);
            strip.setCollapseState(this.collapseStateByChain.get(chain));
            strip.updateSelection(this.currentSelection);
            strip.updateContextTarget(this.currentContextTarget);
            strip.clearAnnotationOverlays();
            for (const message of this.annotationMessages) {
                strip.addLabelOverlay(message);
            }
        }
        this.applyExpandedState();
        this.renderSummaries();
    }

    private captureCollapseState(): void {
        for (const [chain, strip] of this.strips.entries()) {
            this.collapseStateByChain.set(chain, strip.getCollapseState());
        }
    }

    private makeSectionHeader(title: string): HTMLDivElement {
        const header = document.createElement("div");
        header.setAttribute("data-molsysviewer-group-panel-section-title", title.toLowerCase());
        Object.assign(header.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(244,244,245,0.88)",
        });
        header.textContent = title;
        return header;
    }

    private createSummarySection(title: string, emptyText: string): SummarySectionView {
        const key = title.toLowerCase() as SummarySectionKey;
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-group-panel-section", key);
        Object.assign(section.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            padding: "8px",
            borderRadius: "10px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
        });
        section.appendChild(this.makeSectionHeader(title));

        const list = document.createElement("div");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const empty = document.createElement("div");
        empty.setAttribute("data-molsysviewer-group-panel-empty", key);
        Object.assign(empty.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.56)",
        });
        empty.textContent = emptyText;

        section.appendChild(list);
        section.appendChild(empty);
        this.body.appendChild(section);
        return { root: section, list, empty };
    }

    private renderSummaries(): void {
        this.renderSummaryItems(
            this.summarySections.active,
            this.currentSelection.source_kind === "empty"
                ? []
                : [{
                    title: `${this.currentSelection.count_atoms} atoms`,
                    subtitle: `${this.currentSelection.source_kind} · ${this.currentSelection.target_level}`,
                }]
        );
        this.renderSummaryItems(
            this.summarySections.saved,
            this.savedSelections
                .slice()
                .sort((a, b) => a.tag.localeCompare(b.tag))
                .map((item) => ({
                    title: item.tag,
                    subtitle: `${item.atom_count} atoms`,
                    onActivate: () => this.onActivateSavedSelection(item.tag),
                }))
        );
        this.renderSummaryItems(
            this.summarySections.regions,
            this.regions
                .slice()
                .sort((a, b) => a.tag.localeCompare(b.tag))
                .map((item) => ({
                    title: item.tag,
                    subtitle: item.hidden ? `${item.atom_count} atoms · hidden` : `${item.atom_count} atoms`,
                    onActivate: () => this.onFocusRegion(item.tag),
                }))
        );
    }

    private renderSummaryItems(section: SummarySectionView, items: SummaryItem[]): void {
        section.list.replaceChildren();
        if (items.length === 0) {
            section.empty.style.display = "block";
            return;
        }
        section.empty.style.display = "none";
        for (const item of items) {
            const row = document.createElement("div");
            row.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
            Object.assign(row.style, {
                display: "flex",
                flexDirection: "column",
                gap: "2px",
                padding: "6px 8px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.06)",
                color: "#f4f4f5",
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

            const subtitle = document.createElement("div");
            Object.assign(subtitle.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.68)",
            });
            subtitle.textContent = item.subtitle;

            row.appendChild(title);
            row.appendChild(subtitle);
            section.list.appendChild(row);
        }
    }
}
