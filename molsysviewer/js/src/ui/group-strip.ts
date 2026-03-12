import { StructureElement, Structure } from "molstar/lib/mol-model/structure";

import { ActiveSelectionItem, ActiveSelectionPayload, buildGroupItemsFromStructure } from "../managers/active-selection";

type OnSelect = (items: ActiveSelectionItem[], additive: boolean) => void;
type OnFocus = (item: ActiveSelectionItem) => void;

function selectionKey(item: ActiveSelectionItem): string {
    return `${item.chain_indices.join(",")}:${item.group_indices.join(",")}`;
}

function makeLociForItem(structure: Structure, item: ActiveSelectionItem): StructureElement.Loci | null {
    const unit = structure.units.find((candidate) => candidate.kind === 0);
    if (!unit) return null;
    const indices: number[] = [];
    const unitElements = unit.elements;
    for (const atomIndex of item.atom_indices) {
        const unitIndex = unitElements.indexOf(atomIndex as any);
        if (unitIndex >= 0) indices.push(unitIndex);
    }
    if (indices.length === 0) return null;
    return StructureElement.Loci(structure, [{ unit, indices } as any]);
}

export class GroupStrip {
    private readonly root: HTMLDivElement;
    private groupItems: ActiveSelectionItem[] = [];
    private selectedKeys = new Set<string>();
    private structure?: Structure;

    constructor(
        private readonly host: HTMLElement,
        private readonly onSelect: OnSelect,
        private readonly onFocus: OnFocus,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-group-strip", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            left: "14px",
            right: "14px",
            bottom: "14px",
            display: "none",
            maxHeight: "140px",
            overflow: "auto",
            padding: "10px",
            borderRadius: "14px",
            border: "1px solid rgba(255,255,255,0.14)",
            background: "rgba(18, 18, 22, 0.92)",
            color: "#f4f4f5",
            boxShadow: "0 12px 32px rgba(0,0,0,0.28)",
            zIndex: "16",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
            fontSize: "12px",
        });
        this.host.appendChild(this.root);
    }

    setStructure(structure: Structure | undefined): void {
        this.structure = structure;
        this.groupItems = structure ? buildGroupItemsFromStructure(structure) : [];
        this.render();
    }

    updateSelection(selection: ActiveSelectionPayload): void {
        const next = new Set<string>();
        for (const item of selection.items ?? []) {
            if (item?.source_kind !== "element" || item?.element_level !== "group") continue;
            next.add(selectionKey(item));
        }
        this.selectedKeys = next;
        this.render();
    }

    dispose(): void {
        this.root.remove();
    }

    private render(): void {
        this.root.replaceChildren();
        if (!this.structure || this.groupItems.length === 0) {
            this.root.style.display = "none";
            return;
        }
        this.root.style.display = "block";

        const grouped = new Map<string, ActiveSelectionItem[]>();
        for (const item of this.groupItems) {
            const chain = item.chain_name ?? "?";
            if (!grouped.has(chain)) grouped.set(chain, []);
            grouped.get(chain)!.push(item);
        }

        for (const [chain, items] of grouped.entries()) {
            const section = document.createElement("div");
            section.style.marginBottom = "10px";

            const title = document.createElement("div");
            title.textContent = `Chain ${chain}`;
            Object.assign(title.style, {
                fontWeight: "700",
                marginBottom: "6px",
                opacity: "0.9",
            });
            section.appendChild(title);

            const row = document.createElement("div");
            Object.assign(row.style, {
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
            });

            for (const item of items) {
                const key = selectionKey(item);
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = item.group_name ?? `${item.group_indices[0] ?? "?"}`;
                const selected = this.selectedKeys.has(key);
                Object.assign(button.style, {
                    padding: "6px 8px",
                    borderRadius: "999px",
                    border: selected ? "1px solid rgba(255,255,255,0.38)" : "1px solid rgba(255,255,255,0.12)",
                    background: selected ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.06)",
                    color: "inherit",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    font: "inherit",
                });
                button.addEventListener("click", (event) => {
                    this.onSelect([item], !!(event as MouseEvent).shiftKey);
                });
                button.addEventListener("dblclick", () => {
                    this.onFocus(item);
                });
                row.appendChild(button);
            }

            section.appendChild(row);
            this.root.appendChild(section);
        }
    }

    focusItem(item: ActiveSelectionItem): StructureElement.Loci | null {
        if (!this.structure) return null;
        return makeLociForItem(this.structure, item);
    }
}
