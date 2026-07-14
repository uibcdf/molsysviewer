import type { RegionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeSettingsCard } from "./ui-helpers";

export type LayerSummary = {
    tag: string;
    provenance: "auto" | "user";
    hidden: boolean;
};

export type LayerObjectSummary = {
    kind: "annotation" | "measurement" | "shape";
    tag: string;
    title: string;
    layerTag?: string;
    hidden?: boolean;
};

type MemberKind = "region" | LayerObjectSummary["kind"];
type LayerMember = {
    kind: MemberKind;
    tag: string;
    title: string;
    layerTag?: string | null;
    hidden: boolean;
    atomCount?: number;
};
type LayerRecord = LayerSummary & { members: LayerMember[] };

export class LayersPanel extends BasePanel {
    readonly key = "layers";

    private layers: LayerSummary[] = [];
    private regions: RegionSummary[] = [];
    private objects: LayerObjectSummary[] = [];
    private readonly expanded = new Set<string>();

    constructor(private readonly ctx: PanelContext) {
        super();
    }

    setLayers(items: LayerSummary[]): void {
        this.layers = [...items];
        this.updateBadge();
        this.scheduleRender();
    }

    setRegions(items: RegionSummary[]): void {
        this.regions = [...items];
        this.scheduleRender();
    }

    setObjects(items: LayerObjectSummary[]): void {
        this.objects = [...items];
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Logical Layers"));
        this.host.appendChild(this.renderCreateCard());

        const layers = this.buildLayers();
        if (layers.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No user layers yet.";
            Object.assign(empty.style, { fontSize: "11px", color: "rgba(244,244,245,0.48)", padding: "4px" });
            this.host.appendChild(empty);
            return;
        }

        const list = document.createElement("div");
        list.setAttribute("data-molsysviewer-layer-list", "true");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "8px" });
        for (const layer of layers) list.appendChild(this.renderLayerCard(layer));
        this.host.appendChild(list);
    }

    private userLayers(): LayerSummary[] {
        return this.layers.filter(layer => layer.provenance === "user");
    }

    private updateBadge(): void {
        this.ctx.setBadge(String(this.userLayers().length));
    }

    private allMembers(): LayerMember[] {
        return [
            ...this.regions.map(region => ({
                kind: "region" as const,
                tag: region.tag,
                title: region.tag,
                layerTag: region.layer,
                hidden: region.hidden,
                atomCount: region.atom_count,
            })),
            ...this.objects.map(object => ({
                kind: object.kind,
                tag: object.tag,
                title: object.title,
                layerTag: object.layerTag,
                hidden: !!object.hidden,
            })),
        ];
    }

    private buildLayers(): LayerRecord[] {
        const members = this.allMembers();
        return this.userLayers()
            .map(layer => ({
                ...layer,
                members: members
                    .filter(member => member.layerTag === layer.tag)
                    .sort((a, b) => a.kind.localeCompare(b.kind) || a.tag.localeCompare(b.tag)),
            }))
            .sort((a, b) => a.tag.localeCompare(b.tag));
    }

    private renderCreateCard(): HTMLDivElement {
        const card = makeSettingsCard("New Layer");
        const form = document.createElement("form");
        form.setAttribute("data-molsysviewer-layer-create-form", "true");
        Object.assign(form.style, { display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "6px" });
        const input = this.makeInput("Layer name");
        input.setAttribute("data-molsysviewer-layer-create-input", "true");
        const create = makeButton("Create", () => {
            const tag = input.value.trim();
            if (tag) this.ctx.onAction("create_layer", { tag });
        });
        create.type = "submit";
        form.addEventListener("submit", event => {
            event.preventDefault();
            create.click();
        });
        form.appendChild(input);
        form.appendChild(create);
        card.appendChild(form);
        return card;
    }

    private renderLayerCard(layer: LayerRecord): HTMLDivElement {
        const card = makeSettingsCard(layer.tag);
        card.setAttribute("data-molsysviewer-layer-card", layer.tag);

        const summary = document.createElement("div");
        summary.textContent = `${layer.members.length} member${layer.members.length === 1 ? "" : "s"}`;
        Object.assign(summary.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)" });
        card.appendChild(summary);

        const actions = document.createElement("div");
        Object.assign(actions.style, { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "6px" });
        const visibility = makeButton(layer.hidden ? "Show" : "Hide", () => {
            this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: !layer.hidden });
        });
        visibility.setAttribute("data-molsysviewer-layer-visibility", layer.tag);
        const details = makeButton(this.expanded.has(layer.tag) ? "Less" : "More", () => {
            if (this.expanded.has(layer.tag)) this.expanded.delete(layer.tag);
            else this.expanded.add(layer.tag);
            this.scheduleRender();
        });
        details.setAttribute("data-molsysviewer-layer-details", layer.tag);
        actions.appendChild(visibility);
        actions.appendChild(details);
        card.appendChild(actions);

        if (this.expanded.has(layer.tag)) this.renderDetails(card, layer);
        return card;
    }

    private renderDetails(card: HTMLDivElement, layer: LayerRecord): void {
        for (const member of layer.members) card.appendChild(this.renderMemberRow(layer.tag, member));

        const available = this.allMembers().filter(member => member.layerTag !== layer.tag);
        if (available.length > 0) {
            const assign = document.createElement("div");
            Object.assign(assign.style, { display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "6px" });
            const picker = document.createElement("select");
            picker.setAttribute("data-molsysviewer-layer-member-picker", layer.tag);
            for (const member of available) {
                const option = document.createElement("option");
                option.value = JSON.stringify([member.kind, member.tag]);
                option.textContent = `${member.kind}: ${member.title}`;
                picker.appendChild(option);
            }
            this.styleControl(picker);
            const add = makeButton("Add", () => {
                const [memberKind, memberTag] = JSON.parse(picker.value) as [MemberKind, string];
                if (!memberKind || !memberTag) return;
                this.ctx.onAction("add_member_to_layer", {
                    layer: layer.tag,
                    member_kind: memberKind,
                    member_tag: memberTag,
                });
            });
            add.setAttribute("data-molsysviewer-layer-add-member", layer.tag);
            assign.appendChild(picker);
            assign.appendChild(add);
            card.appendChild(assign);
        }

        const rename = document.createElement("div");
        Object.assign(rename.style, { display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "6px" });
        const renameInput = this.makeInput("New layer name");
        renameInput.setAttribute("data-molsysviewer-layer-rename-input", layer.tag);
        const renameButton = makeButton("Rename", () => {
            const newTag = renameInput.value.trim();
            if (newTag && newTag !== layer.tag) this.ctx.onAction("rename_layer", { tag: layer.tag, new_tag: newTag });
        });
        renameButton.setAttribute("data-molsysviewer-layer-rename", layer.tag);
        rename.appendChild(renameInput);
        rename.appendChild(renameButton);
        card.appendChild(rename);

        const lifecycle = document.createElement("div");
        Object.assign(lifecycle.style, { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "6px" });
        const ungroup = makeButton("Ungroup", () => this.ctx.onAction("ungroup_layer", { tag: layer.tag }));
        ungroup.setAttribute("data-molsysviewer-layer-ungroup", layer.tag);
        const destroy = makeButton("Delete contents", () => {
            const question = `Delete layer '${layer.tag}' and its ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}?`;
            if (typeof confirm !== "function" || confirm(question)) {
                this.ctx.onAction("delete_layer_and_contents", { tag: layer.tag });
            }
        });
        destroy.setAttribute("data-molsysviewer-layer-delete-contents", layer.tag);
        destroy.title = `Delete layer and ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}`;
        lifecycle.appendChild(ungroup);
        lifecycle.appendChild(destroy);
        card.appendChild(lifecycle);
    }

    private renderMemberRow(layerTag: string, member: LayerMember): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-layer-member", `${member.kind}:${member.tag}`);
        Object.assign(row.style, {
            display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "8px",
            alignItems: "center", padding: "6px 8px", borderRadius: "6px",
            background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.05)",
        });
        const label = document.createElement("div");
        label.textContent = `${member.title} · ${member.kind}${member.atomCount === undefined ? "" : ` · ${member.atomCount} atoms`}`;
        Object.assign(label.style, { minWidth: "0", fontSize: "11px", color: member.hidden ? "rgba(244,244,245,0.42)" : "#f4f4f5" });
        const remove = makeButton("Remove", () => this.ctx.onAction("remove_member_from_layer", {
            layer: layerTag,
            member_kind: member.kind,
            member_tag: member.tag,
        }));
        remove.setAttribute("data-molsysviewer-layer-remove-member", `${member.kind}:${member.tag}`);
        remove.title = `Remove ${member.tag} from ${layerTag} without deleting it`;
        row.appendChild(label);
        row.appendChild(remove);
        return row;
    }

    private styleControl(control: HTMLInputElement | HTMLSelectElement): void {
        Object.assign(control.style, {
            minWidth: "0", background: "rgba(0,0,0,0.28)", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px", padding: "5px 7px", color: "#f4f4f5", fontSize: "11px", outline: "none",
        });
    }

    private makeInput(placeholder: string): HTMLInputElement {
        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = placeholder;
        this.styleControl(input);
        return input;
    }
}
