import { Structure } from "molstar/lib/mol-model/structure";
import {
    ActiveSelectionItem,
    ActiveSelectionPayload,
    GroupSelectionItem,
    buildGroupItemsFromStructure,
} from "../../managers/active-selection";
import { AddLabelMessage } from "../../messages/viewer-messages";
import { ContextMenuTarget } from "../context-menu";
import { GroupStrip } from "../group-strip";
import type {
    OnAnnotationContext,
    OnContext,
    OnFocus,
    OnHover,
    OnInteraction,
    OnSelect,
} from "../group-panel";
import { PanelContext, StudioPanel } from "./types";

/** Interaction callbacks the System strips need, threaded from the controller. */
export interface SystemPanelCallbacks {
    onSelect: OnSelect;
    onInteraction: OnInteraction;
    onFocus: OnFocus;
    onHover: OnHover;
    onContext: OnContext;
    onAnnotationContext: OnAnnotationContext;
    /**
     * Called after every strip rebuild with whether the structure yields a
     * naturally-visible System tab. The host owns panel-level visibility.
     */
    onRebuilt: (naturalVisible: boolean) => void;
}

/**
 * Studio -> System subpanel.
 *
 * Owns the per-chain GroupStrip persistent widgets, the modifier legend,
 * and the annotation overlays that live on the
 * strips. It manages the strip lifecycle (build/prune/collapse-state) and
 * propagates selection / context-target / annotations to them. Panel-level
 * visibility stays with the host, reached through the onRebuilt callback.
 */
export class SystemPanel implements StudioPanel {
    readonly key = "system";
    private host: HTMLElement | null = null;
    private stripsRow: HTMLDivElement | null = null;

    private readonly strips = new Map<string, GroupStrip>();
    private structure?: Structure;
    private activeColorScheme: "neutral" | "physicochemical" = "neutral";
    private currentContextTarget: ContextMenuTarget | null = null;
    private readonly annotationMessages: AddLabelMessage[] = [];
    private readonly collapseStateByChain = new Map<string, { molecules: number[]; components: string[] }>();
    // A chrome refresh must not rebuild a residue hierarchy that has not changed.
    // The rows remain O(residues), but their DOM is reconciled on structure changes only.
    private renderedStructure?: Structure;
    private structureNeedsReconcile = true;
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

    constructor(
        private readonly ctx: PanelContext,
        private readonly callbacks: SystemPanelCallbacks,
    ) {}

    // System renders its strips on setStructure (not on visibility), so tab
    // visibility does not gate its rendering.
    setVisible(_visible: boolean): void {}

    setColorScheme(scheme: "neutral" | "physicochemical"): void {
        if (this.activeColorScheme === scheme) return;
        this.activeColorScheme = scheme;
        for (const strip of this.strips.values()) {
            strip.setColorScheme(scheme);
        }
        this.structureNeedsReconcile = true;
    }

    mount(host: HTMLElement): void {
        this.host = host;
        Object.assign(host.style, {
            flexDirection: "column",
            overflowX: "hidden",
            overflowY: "hidden",
            gap: "6px",
        });
        host.appendChild(this.makeSystemHeader());
        this.stripsRow = document.createElement("div");
        Object.assign(this.stripsRow.style, {
            display: "flex",
            flexDirection: "row",
            flex: "1 1 0",
            minHeight: "0",
            overflowX: "auto",
            overflowY: "hidden",
            paddingBottom: "8px",
        });
        host.appendChild(this.stripsRow);
    }

    // ── Domain state pushed from the host ──────────────────────

    setStructure(structure: Structure | undefined): void {
        if (this.structure === structure) return;
        this.structure = structure;
        this.structureNeedsReconcile = true;
        if (!structure) this.annotationMessages.length = 0;
        this.rebuild();
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
        const chainName = item.source_kind === "element" ? (item.chain_name ?? "?") : "?";
        return this.strips.get(chainName)?.focusItem(item) ?? null;
    }

    captureCollapseState(): void {
        for (const [chain, strip] of this.strips.entries()) {
            this.collapseStateByChain.set(chain, strip.getCollapseState());
        }
    }

    dispose(): void {
        this.captureCollapseState();
        for (const strip of this.strips.values()) strip.dispose();
        this.strips.clear();
    }

    // ── Strip lifecycle ────────────────────────────────────────

    /** Rebuild the strips for the current structure; reports natural visibility via onRebuilt. */
    rebuild(): void {
        if (!this.stripsRow) return;
        if (!this.structureNeedsReconcile && this.renderedStructure === this.structure) {
            this.callbacks.onRebuilt(Boolean(this.structure) && this.strips.size > 0);
            return;
        }
        this.captureCollapseState();

        const grouped = new Map<string, GroupSelectionItem[]>();
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

        const naturalVisible = Boolean(this.structure) && grouped.size > 0;

        this.ctx.setBadge(
            naturalVisible
                ? `Hierarchy: ${grouped.size} chain${grouped.size === 1 ? "" : "s"}, ${items.length} res`
                : "Molecular Hierarchy & Sequence",
        );

        if (this.structure && grouped.size > 0) {
            for (const [chain, chainItems] of grouped.entries()) {
                let strip = this.strips.get(chain);
                if (!strip) {
                    strip = new GroupStrip(
                        this.stripsRow,
                        chain,
                        this.callbacks.onSelect,
                        this.callbacks.onInteraction,
                        this.callbacks.onFocus,
                        this.callbacks.onHover,
                        this.callbacks.onContext,
                        this.callbacks.onAnnotationContext,
                    );
                    this.strips.set(chain, strip);
                }
                strip.setColorScheme(this.activeColorScheme);
                strip.setData(this.structure, chainItems);
                strip.setCollapseState(this.collapseStateByChain.get(chain));
                strip.updateSelection(this.currentSelection);
                strip.updateContextTarget(this.currentContextTarget);
                strip.clearAnnotationOverlays();
                for (const message of this.annotationMessages) {
                    strip.addLabelOverlay(message);
                }
            }
        }

        this.callbacks.onRebuilt(naturalVisible);
        this.renderedStructure = this.structure;
        this.structureNeedsReconcile = false;
    }

    // ── Header / color-scheme menu ─────────────────────────────

    private makeSystemHeader(): HTMLDivElement {
        const header = document.createElement("div");
        Object.assign(header.style, {
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            position: "relative",
            width: "100%",
            flex: "0 0 auto",
            gap: "8px",
        });
        header.appendChild(this.makeModifierLegend());
        return header;
    }

    private makeModifierLegend(): HTMLDivElement {
        const legend = document.createElement("div");
        legend.setAttribute("data-molsysviewer-selection-modifier-legend", "true");
        Object.assign(legend.style, {
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "6px",
            minWidth: "0",
            color: "rgba(244,244,245,0.56)",
            fontSize: "10px",
            lineHeight: "1.2",
        });

        const entries: Array<[string, string]> = [
            ["Click", "Replace"],
            ["Shift", "Add/toggle"],
            ["Shift+Alt", "Range"],
        ];
        for (const [key, label] of entries) {
            const item = document.createElement("span");
            item.setAttribute("data-molsysviewer-selection-modifier-legend-item", key);
            Object.assign(item.style, {
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                whiteSpace: "nowrap",
            });

            const keyEl = document.createElement("span");
            Object.assign(keyEl.style, {
                padding: "1px 4px",
                borderRadius: "4px",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "rgba(244,244,245,0.82)",
                fontWeight: "700",
            });
            keyEl.textContent = key;

            const labelEl = document.createElement("span");
            labelEl.textContent = label;

            item.appendChild(keyEl);
            item.appendChild(labelEl);
            legend.appendChild(item);
        }
        return legend;
    }

}
