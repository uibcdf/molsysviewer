import type { RegionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeSettingsCard } from "./ui-helpers";

export type LayerObjectSummary = {
    kind: "annotation" | "measurement" | "shape";
    tag: string;
    title: string;
    layerTag?: string;
    hidden?: boolean;
};

type LayerMember =
    | { kind: "region"; tag: string; title: string; atomCount: number; hidden: boolean }
    | { kind: "annotation" | "measurement" | "shape"; tag: string; title: string; hidden: boolean };

type LayerRecord = {
    tag: string;
    regions: LayerMember[];
    objects: LayerMember[];
};

export class LayersPanel extends BasePanel {
    readonly key = "layers";

    private regions: RegionSummary[] = [];
    private objects: LayerObjectSummary[] = [];

    constructor(private readonly ctx: PanelContext) {
        super();
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        this.updateBadge();
        this.scheduleRender();
    }

    setObjects(items: LayerObjectSummary[]): void {
        this.objects = [...items];
        this.updateBadge();
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Logical Layers"));
        this.host.appendChild(this.renderAssignCard());
        this.host.appendChild(makeSectionHeader("Layer Groups"));

        const layers = this.buildLayers();
        if (layers.length === 0) {
            const empty = document.createElement("div");
            Object.assign(empty.style, {
                fontSize: "11px",
                color: "rgba(244,244,245,0.48)",
                paddingLeft: "4px",
            });
            empty.textContent = "No layer groups yet.";
            this.host.appendChild(empty);
            return;
        }

        const list = document.createElement("div");
        list.setAttribute("data-molsysviewer-layer-list", "true");
        Object.assign(list.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
        });
        this.host.appendChild(list);

        for (const layer of layers) {
            list.appendChild(this.renderLayerCard(layer));
        }
    }

    private updateBadge(): void {
        this.ctx.setBadge(String(this.buildLayers().length));
    }

    private buildLayers(): LayerRecord[] {
        const records = new Map<string, LayerRecord>();
        const ensure = (tag: string): LayerRecord => {
            const existing = records.get(tag);
            if (existing) return existing;
            const record: LayerRecord = { tag, regions: [], objects: [] };
            records.set(tag, record);
            return record;
        };

        for (const region of this.regions) {
            const layerTag = typeof region.layer === "string" ? region.layer.trim() : "";
            if (!layerTag) continue;
            ensure(layerTag).regions.push({
                kind: "region",
                tag: region.tag,
                title: region.tag,
                atomCount: region.atom_count,
                hidden: region.hidden,
            });
        }
        for (const object of this.objects) {
            const layerTag = typeof object.layerTag === "string" ? object.layerTag.trim() : "";
            if (!layerTag) continue;
            ensure(layerTag).objects.push({
                kind: object.kind,
                tag: object.tag,
                title: object.title,
                hidden: !!object.hidden,
            });
        }

        return Array.from(records.values())
            .map(layer => ({
                ...layer,
                regions: [...layer.regions].sort((a, b) => a.tag.localeCompare(b.tag)),
                objects: [...layer.objects].sort((a, b) => a.tag.localeCompare(b.tag)),
            }))
            .sort((a, b) => a.tag.localeCompare(b.tag));
    }

    private renderAssignCard(): HTMLDivElement {
        const card = makeSettingsCard("Assign Region");
        const row = document.createElement("form");
        row.setAttribute("data-molsysviewer-layer-assign-form", "true");
        Object.assign(row.style, {
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr) auto",
            gap: "6px",
            alignItems: "center",
        });

        const regionInput = this.makeInput("Region tag");
        regionInput.setAttribute("data-molsysviewer-layer-assign-region", "true");
        const layerInput = this.makeInput("Layer tag");
        layerInput.setAttribute("data-molsysviewer-layer-assign-layer", "true");
        const button = makeButton("Assign", () => {
            const tag = regionInput.value.trim();
            const layer = layerInput.value.trim();
            if (!tag) return;
            this.ctx.onAction("set_region_layer", { tag, layer: layer || null });
        });
        button.type = "submit";
        row.appendChild(regionInput);
        row.appendChild(layerInput);
        row.appendChild(button);
        row.addEventListener("submit", (event) => {
            event.preventDefault();
            button.click();
        });
        card.appendChild(row);

        const hint = document.createElement("div");
        Object.assign(hint.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.48)",
            lineHeight: "1.4",
        });
        hint.textContent = "Leave the layer empty to detach the region.";
        card.appendChild(hint);
        return card;
    }

    private renderLayerCard(layer: LayerRecord): HTMLDivElement {
        const card = makeSettingsCard(layer.tag);
        card.setAttribute("data-molsysviewer-layer-card", layer.tag);

        const counts = document.createElement("div");
        Object.assign(counts.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
        });
        counts.textContent = `${layer.regions.length} regions · ${layer.objects.length} scene objects`;
        card.appendChild(counts);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "6px",
        });
        const show = makeButton("Show", () => {
            this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: false });
        });
        show.setAttribute("data-molsysviewer-layer-show", layer.tag);
        const hide = makeButton("Hide", () => {
            this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: true });
        });
        hide.setAttribute("data-molsysviewer-layer-hide", layer.tag);
        const del = makeButton("Delete", () => {
            this.ctx.onAction("delete_layer_group", { tag: layer.tag });
        });
        del.setAttribute("data-molsysviewer-layer-delete", layer.tag);
        actions.appendChild(show);
        actions.appendChild(hide);
        actions.appendChild(del);
        card.appendChild(actions);

        for (const member of [...layer.regions, ...layer.objects]) {
            card.appendChild(this.renderMemberRow(layer.tag, member));
        }
        return card;
    }

    private renderMemberRow(layerTag: string, member: LayerMember): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-layer-member", member.tag);
        Object.assign(row.style, {
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) auto",
            gap: "8px",
            alignItems: "center",
            padding: "6px 8px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.05)",
        });

        const label = document.createElement("div");
        Object.assign(label.style, {
            minWidth: "0",
            display: "flex",
            flexDirection: "column",
            gap: "2px",
        });
        const title = document.createElement("div");
        Object.assign(title.style, {
            fontSize: "11px",
            color: member.hidden ? "rgba(244,244,245,0.42)" : "#f4f4f5",
            fontWeight: "600",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
        });
        title.textContent = member.title;
        const subtitle = document.createElement("div");
        Object.assign(subtitle.style, {
            fontSize: "10px",
            color: "rgba(244,244,245,0.48)",
        });
        subtitle.textContent = member.kind === "region"
            ? `region · ${member.atomCount} atoms`
            : member.kind;
        label.appendChild(title);
        label.appendChild(subtitle);
        row.appendChild(label);

        const detach = makeButton("Remove", () => {
            if (member.kind !== "region") return;
            this.ctx.onAction("remove_region_from_layer", { tag: member.tag });
        });
        detach.setAttribute("data-molsysviewer-layer-remove-region", member.tag);
        detach.disabled = member.kind !== "region";
        detach.title = member.kind === "region"
            ? `Remove ${member.tag} from ${layerTag}`
            : "Scene objects are managed by their own addon layer tags.";
        detach.style.opacity = member.kind === "region" ? "1" : "0.35";
        row.appendChild(detach);
        return row;
    }

    private makeInput(placeholder: string): HTMLInputElement {
        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = placeholder;
        Object.assign(input.style, {
            minWidth: "0",
            background: "rgba(0,0,0,0.28)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "5px 7px",
            color: "#f4f4f5",
            fontSize: "11px",
            outline: "none",
        });
        return input;
    }
}
