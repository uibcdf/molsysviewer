import type { RegionSummary } from "../group-panel";
import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";

export type LayerSummary = {
    tag: string;
    owner?: string;
    provenance: "auto" | "user";
    hidden: boolean;
};

export type LayerObjectSummary = {
    kind: "annotation" | "measurement" | "shape";
    tag: string;
    owner?: string;
    title: string;
    layerTag?: string;
    hidden?: boolean;
};

type MemberKind = "region" | LayerObjectSummary["kind"];
type LayerMember = {
    kind: MemberKind;
    tag: string;
    owner?: string;
    title: string;
    layerTag?: string | null;
    hidden: boolean;
    atomCount?: number;
};
type LayerRecord = LayerSummary & { members: LayerMember[] };

const INPUT_STYLE = {
    background: "rgba(0,0,0,0.2)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "6px",
    padding: "4px 8px",
    color: "#fff",
    fontSize: "11px",
};

function card(): HTMLDivElement {
    const element = document.createElement("div");
    Object.assign(element.style, {
        display: "flex", flexDirection: "column", gap: "7px", padding: "10px",
        borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.035)",
    });
    return element;
}

export class LayersPanel extends BasePanel {
    readonly key = "layers";

    private layers: LayerSummary[] = [];
    private regions: RegionSummary[] = [];
    private objects: LayerObjectSummary[] = [];
    private readonly expanded = new Set<string>();
    private selectedInitialMembers: Array<[MemberKind, string]> = [];

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

        // 1. Section Header and Global Actions Card
        this.host.appendChild(makeSectionHeader("Layers"));
        this.host.appendChild(this.renderGlobalActions());

        // 2. New Layer Section
        this.host.appendChild(makeSectionHeader("New layer"));
        this.host.appendChild(this.renderCreateCard());

        // 3. Saved Layers List Section
        this.host.appendChild(makeSectionHeader("Saved layers"));
        const layers = this.buildLayers();
        if (layers.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No user layers yet.";
            Object.assign(empty.style, { fontSize: "11px", color: "rgba(244,244,245,0.52)", padding: "4px" });
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
                owner: region.owner,
                title: region.tag,
                layerTag: region.layer,
                hidden: region.hidden,
                atomCount: region.atom_count,
            })),
            ...this.objects.map(object => ({
                kind: object.kind,
                tag: object.tag,
                owner: object.owner,
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

    private renderGlobalActions(): HTMLDivElement {
        const globalCard = document.createElement("div");
        Object.assign(globalCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "8px 10px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.035)",
            border: "1px solid rgba(255,255,255,0.08)",
            marginBottom: "10px",
        });

        const totalUserLayers = this.userLayers();
        const totalCount = totalUserLayers.length;
        const visibleCount = totalUserLayers.filter(l => !l.hidden).length;

        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            gap: "10px",
        });

        const info = document.createElement("div");
        Object.assign(info.style, {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "11px",
            color: "rgba(244,244,245,0.75)",
        });

        const dot = document.createElement("span");
        const anyVisible = totalCount > 0 && visibleCount > 0;
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "999px",
            background: anyVisible ? "#34d399" : "rgba(244,244,245,0.28)",
            boxShadow: anyVisible ? "0 0 6px rgba(52,211,153,0.4)" : "none",
            flexShrink: "0",
        });
        info.appendChild(dot);
        const textSpan = document.createElement("span");
        textSpan.textContent = `${visibleCount} of ${totalCount} user layer${totalCount === 1 ? "" : "s"} visible`;
        info.appendChild(textSpan);
        row.appendChild(info);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        const showAllBtn = makeButton("Show all", () => {
            for (const layer of totalUserLayers) {
                if (layer.hidden) {
                    this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: false });
                }
            }
        });
        showAllBtn.style.padding = "3px 6px";
        showAllBtn.style.fontSize = "10px";

        const hideAllBtn = makeButton("Hide all", () => {
            for (const layer of totalUserLayers) {
                if (!layer.hidden) {
                    this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: true });
                }
            }
        });
        hideAllBtn.style.padding = "3px 6px";
        hideAllBtn.style.fontSize = "10px";

        actions.appendChild(showAllBtn);
        actions.appendChild(hideAllBtn);
        row.appendChild(actions);
        globalCard.appendChild(row);

        return globalCard;
    }

    private renderCreateCard(): HTMLDivElement {
        const createCard = card();
        Object.assign(createCard.style, { marginBottom: "10px" });

        const form = document.createElement("form");
        form.setAttribute("data-molsysviewer-layer-create-form", "true");
        Object.assign(form.style, { display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "6px" });

        const input = this.makeInput("Layer name (e.g. active-site)");
        input.setAttribute("data-molsysviewer-layer-create-input", "true");

        const create = makeButton("Create", () => {
            const tag = input.value.trim();
            if (tag) {
                this.ctx.onAction("create_layer", { tag });
                for (const [kind, mTag] of this.selectedInitialMembers) {
                    this.ctx.onAction("add_member_to_layer", { layer: tag, member_kind: kind, member_tag: mTag });
                }
                this.selectedInitialMembers = [];
                input.value = "";
            }
        });
        create.type = "submit";
        create.style.padding = "4px 10px";
        create.style.fontSize = "11px";
        create.style.fontWeight = "600";

        form.addEventListener("submit", event => {
            event.preventDefault();
            create.click();
        });

        form.appendChild(input);
        form.appendChild(create);
        createCard.appendChild(form);

        // Optional Initial Member Staging/Picker
        const unassignedMembers = this.allMembers().filter(m => !m.layerTag || m.layerTag === m.tag);
        if (unassignedMembers.length > 0) {
            const optRow = document.createElement("div");
            Object.assign(optRow.style, { display: "flex", alignItems: "center", gap: "6px", marginTop: "6px" });
            const label = document.createElement("span");
            label.textContent = "Include items:";
            Object.assign(label.style, { fontSize: "10px", color: "rgba(244,244,245,0.6)" });
            optRow.appendChild(label);

            const select = document.createElement("select");
            this.styleControl(select);
            select.style.flex = "1 1 auto";

            const defaultOpt = document.createElement("option");
            defaultOpt.value = "";
            defaultOpt.textContent = "Select unassigned item to include...";
            select.appendChild(defaultOpt);

            for (const m of unassignedMembers) {
                const opt = document.createElement("option");
                opt.value = JSON.stringify([m.kind, m.tag]);
                opt.textContent = `${m.kind}: ${m.title}`;
                select.appendChild(opt);
            }

            select.addEventListener("change", () => {
                if (!select.value) return;
                const parsed = JSON.parse(select.value) as [MemberKind, string];
                if (!this.selectedInitialMembers.some(([k, t]) => k === parsed[0] && t === parsed[1])) {
                    this.selectedInitialMembers.push(parsed);
                    this.scheduleRender();
                }
            });

            optRow.appendChild(select);
            createCard.appendChild(optRow);

            if (this.selectedInitialMembers.length > 0) {
                const stagedTagsBox = document.createElement("div");
                Object.assign(stagedTagsBox.style, { display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "4px" });

                for (const [k, t] of this.selectedInitialMembers) {
                    const tagPill = document.createElement("span");
                    tagPill.textContent = `${k}:${t} ×`;
                    Object.assign(tagPill.style, {
                        fontSize: "10px",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "rgba(52,211,153,0.15)",
                        border: "1px solid rgba(52,211,153,0.3)",
                        color: "#34d399",
                        cursor: "pointer",
                    });
                    tagPill.addEventListener("click", () => {
                        this.selectedInitialMembers = this.selectedInitialMembers.filter(([k2, t2]) => !(k2 === k && t2 === t));
                        this.scheduleRender();
                    });
                    stagedTagsBox.appendChild(tagPill);
                }
                createCard.appendChild(stagedTagsBox);
            }
        }

        return createCard;
    }

    private renderLayerCard(layer: LayerRecord): HTMLDivElement {
        const row = card();
        row.setAttribute("data-molsysviewer-layer-card", layer.tag);
        row.style.opacity = layer.hidden ? "0.48" : "1";

        const head = document.createElement("div");
        Object.assign(head.style, { display: "flex", alignItems: "center", gap: "6px" });
        const identity = document.createElement("div");
        identity.textContent = `${layer.tag}${layer.owner ? ` · from ${layer.owner}` : ""}`;
        Object.assign(identity.style, {
            flex: "1 1 0", minWidth: "0", overflow: "hidden", textOverflow: "ellipsis",
            whiteSpace: "nowrap", color: "#f4f4f5", fontSize: "12px", fontWeight: "650",
        });
        head.appendChild(identity);
        row.appendChild(head);

        const summary = document.createElement("div");
        summary.textContent = `${layer.members.length} member${layer.members.length === 1 ? "" : "s"}`;
        Object.assign(summary.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)", marginTop: "2px" });
        row.appendChild(summary);

        const btnRow = document.createElement("div");
        Object.assign(btnRow.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            marginTop: "4px",
        });

        const eye = makeButton(layer.hidden ? "⦻" : "👁", () => {
            this.ctx.onAction("set_layer_visibility", { tag: layer.tag, hidden: !layer.hidden });
        });
        eye.title = layer.hidden ? "Show layer" : "Hide layer";
        eye.setAttribute("data-molsysviewer-layer-visibility", layer.tag);

        const editBtn = makeButton("Edit", () => {
            if (this.expanded.has(layer.tag)) this.expanded.delete(layer.tag);
            else this.expanded.add(layer.tag);
            this.scheduleRender();
        });
        editBtn.title = "Manage members, rename or delete";
        editBtn.setAttribute("data-molsysviewer-layer-details", layer.tag);

        const remove = makeButton("🗑", () => {
            const question = `Delete layer '${layer.tag}' and its ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}?`;
            if (typeof confirm !== "function" || confirm(question)) {
                this.ctx.onAction("delete_layer_and_contents", { tag: layer.tag });
            }
        });
        remove.title = `Delete layer and ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}`;
        remove.setAttribute("data-molsysviewer-layer-delete-contents", layer.tag);

        for (const button of [eye, editBtn, remove]) {
            button.style.flex = "0 1 auto";
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            btnRow.appendChild(button);
        }
        row.appendChild(btnRow);

        if (this.expanded.has(layer.tag)) this.renderDetails(row, layer);
        return row;
    }

    private renderDetails(container: HTMLDivElement, layer: LayerRecord): void {
        const editor = document.createElement("div");
        Object.assign(editor.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginTop: "6px",
            padding: "8px",
            background: "rgba(0,0,0,0.12)",
            borderRadius: "6px",
        });

        // Members Section
        const memHeader = document.createElement("div");
        memHeader.textContent = "Members";
        Object.assign(memHeader.style, { fontSize: "11px", fontWeight: "700", color: "rgba(255,255,255,0.8)" });
        editor.appendChild(memHeader);

        for (const member of layer.members) editor.appendChild(this.renderMemberRow(layer.tag, member));

        const available = this.allMembers().filter(member => member.layerTag !== layer.tag);
        if (available.length > 0) {
            const assign = document.createElement("div");
            Object.assign(assign.style, { display: "flex", gap: "6px", marginTop: "4px" });
            const picker = document.createElement("select");
            picker.setAttribute("data-molsysviewer-layer-member-picker", layer.tag);
            for (const member of available) {
                const option = document.createElement("option");
                option.value = JSON.stringify([member.kind, member.tag]);
                option.textContent = `${member.kind}: ${member.title}`;
                picker.appendChild(option);
            }
            this.styleControl(picker);
            picker.style.flex = "1 1 auto";

            const add = makeButton("Add", () => {
                const [memberKind, memberTag] = JSON.parse(picker.value) as [MemberKind, string];
                if (!memberKind || !memberTag) return;
                this.ctx.onAction("add_member_to_layer", {
                    layer: layer.tag,
                    member_kind: memberKind,
                    member_tag: memberTag,
                });
            });
            add.style.padding = "4px 8px";
            add.style.fontSize = "11px";
            add.setAttribute("data-molsysviewer-layer-add-member", layer.tag);
            assign.appendChild(picker);
            assign.appendChild(add);
            editor.appendChild(assign);
        }

        // Rename Section
        const renameHeader = document.createElement("div");
        renameHeader.textContent = "Rename Layer";
        Object.assign(renameHeader.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(255,255,255,0.8)",
            marginTop: "6px",
            paddingTop: "4px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
        });
        editor.appendChild(renameHeader);

        const rename = document.createElement("div");
        Object.assign(rename.style, { display: "flex", gap: "6px" });
        const renameInput = this.makeInput("New layer name");
        renameInput.style.flex = "1 1 auto";
        renameInput.setAttribute("data-molsysviewer-layer-rename-input", layer.tag);
        const renameButton = makeButton("Rename", () => {
            const newTag = renameInput.value.trim();
            if (newTag && newTag !== layer.tag) this.ctx.onAction("rename_layer", { tag: layer.tag, new_tag: newTag });
        });
        renameButton.style.padding = "4px 8px";
        renameButton.style.fontSize = "11px";
        renameButton.setAttribute("data-molsysviewer-layer-rename", layer.tag);
        renameInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                renameButton.click();
            }
        });
        rename.appendChild(renameInput);
        rename.appendChild(renameButton);
        editor.appendChild(rename);

        // Lifecycle Actions Section
        const lifecycleHeader = document.createElement("div");
        lifecycleHeader.textContent = "Lifecycle Actions";
        Object.assign(lifecycleHeader.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(255,255,255,0.8)",
            marginTop: "6px",
            paddingTop: "4px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
        });
        editor.appendChild(lifecycleHeader);

        const lifecycle = document.createElement("div");
        Object.assign(lifecycle.style, { display: "flex", gap: "6px" });
        const ungroup = makeButton("Ungroup Layer", () => this.ctx.onAction("ungroup_layer", { tag: layer.tag }));
        ungroup.style.padding = "4px 8px";
        ungroup.style.fontSize = "11px";
        ungroup.setAttribute("data-molsysviewer-layer-ungroup", layer.tag);

        const destroy = makeButton("Delete Contents", () => {
            const question = `Delete layer '${layer.tag}' and its ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}?`;
            if (typeof confirm !== "function" || confirm(question)) {
                this.ctx.onAction("delete_layer_and_contents", { tag: layer.tag });
            }
        });
        destroy.style.padding = "4px 8px";
        destroy.style.fontSize = "11px";
        destroy.setAttribute("data-molsysviewer-layer-delete-contents", layer.tag);
        destroy.title = `Delete layer and ${layer.members.length} member${layer.members.length === 1 ? "" : "s"}`;

        lifecycle.appendChild(ungroup);
        lifecycle.appendChild(destroy);
        editor.appendChild(lifecycle);

        container.appendChild(editor);
    }

    private renderMemberRow(layerTag: string, member: LayerMember): HTMLDivElement {
        const row = document.createElement("div");
        row.setAttribute("data-molsysviewer-layer-member", `${member.kind}:${member.tag}`);
        Object.assign(row.style, {
            display: "flex", justifyContent: "space-between", gap: "8px",
            alignItems: "center", padding: "4px 8px", borderRadius: "6px",
            background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.05)",
        });
        const label = document.createElement("div");
        label.textContent = `${member.title} · ${member.kind}${member.atomCount === undefined ? "" : ` · ${member.atomCount} atoms`}${member.owner ? ` · from ${member.owner}` : ""}`;
        Object.assign(label.style, { minWidth: "0", fontSize: "11px", color: member.hidden ? "rgba(244,244,245,0.42)" : "#f4f4f5" });
        const remove = makeButton("Remove", () => this.ctx.onAction("remove_member_from_layer", {
            layer: layerTag,
            member_kind: member.kind,
            member_tag: member.tag,
        }));
        remove.style.padding = "2px 6px";
        remove.style.fontSize = "10px";
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
