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

export class GroupPanel {
    private readonly root: HTMLDivElement;
    private readonly toggleButton: HTMLButtonElement;
    private readonly body: HTMLDivElement;
    private readonly shell: PanelShell;
    private readonly strips = new Map<string, GroupStrip>();
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

    constructor(
        private readonly host: HTMLElement,
        private readonly onSelect: OnSelect,
        private readonly onInteraction: OnInteraction,
        private readonly onFocus: OnFocus,
        private readonly onHover: OnHover,
        private readonly onContext: OnContext,
        private readonly onAnnotationContext: OnAnnotationContext,
    ) {
        this.shell = new PanelShell(this.host, { title: "Navigate", width: 240, toggleWidth: 26 });
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

        this.body.setAttribute("data-molsysviewer-group-panel-body", "true");
    }

    setStructure(structure: Structure | undefined): void {
        this.structure = structure;
        if (!structure) this.annotationMessages.length = 0;
        this.render();
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        this.currentSelection = selection;
        for (const strip of this.strips.values()) {
            strip.updateSelection(selection);
        }
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

        this.shell.setVisible(Boolean(this.structure) && grouped.size > 0);
        if (!this.structure || grouped.size === 0) return;

        for (const [chain, chainItems] of grouped.entries()) {
            let strip = this.strips.get(chain);
            if (!strip) {
                strip = new GroupStrip(this.body, chain, this.onSelect, this.onInteraction, this.onFocus, this.onHover, this.onContext, this.onAnnotationContext);
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
    }

    private captureCollapseState(): void {
        for (const [chain, strip] of this.strips.entries()) {
            this.collapseStateByChain.set(chain, strip.getCollapseState());
        }
    }
}
