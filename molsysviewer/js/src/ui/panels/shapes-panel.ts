import { BasePanel } from "./base-panel";
import type { PanelContext } from "./types";
import { makeButton, makeSectionHeader } from "./ui-helpers";

export type ShapeLength = { magnitude: number; unit: string };

export type ShapeSummary = {
    op: string;
    kind: string;
    tag: string;
    layerTag?: string;
    title: string;
    subtitle?: string;
    hidden: boolean;
    atomIndices: number[];
    color?: string;
    nColors?: number;
    radius?: ShapeLength;
    nRadii?: number;
    alpha?: number;
    radiusScale?: number;
    lengthScale?: number;
    broken: boolean;
    brokenReason?: string;
};

export type ShapeRenderStatus = {
    tag: string;
    op: string;
    frame: number;
    status: "rendered" | "missing-frame-data" | "missing-structure" | "empty-selection" | "invalid-indices" | "render-error";
    requestedAtoms?: number;
    usedAtoms?: number;
    reason?: string;
};

export type ShapeStyleControl = "color" | "colors" | "alpha" | "radius" | "radii" | "radius_scale" | "length_scale";

export const SHAPE_STYLE_CONTROLS: Readonly<Record<string, readonly ShapeStyleControl[]>> = {
    add_sphere: ["color", "alpha", "radius"],
    add_network_links: ["colors", "alpha", "radii"],
    add_channel_tube: ["colors", "alpha", "radii"],
    add_tetrahedra: ["colors", "alpha"],
    add_triangle_faces: ["colors", "alpha"],
    add_anisotropy_ellipsoids: ["colors", "alpha"],
    add_pharmacophore_features: ["colors", "alpha", "radii"],
    add_displacement_vectors: ["radius_scale", "length_scale"],
    add_pocket_blob: ["alpha", "radii", "radius_scale"],
    add_pocket_surface: ["alpha"],
    add_alpha_sphere_set: [],
    add_hbonds: [],
    add_rings: [],
    add_scalar_isosurface: [],
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

function unitLabel(unit: string): string {
    return unit === "angstrom" || unit === "angstroms" ? "Å" : unit;
}

export class ShapesPanel extends BasePanel {
    readonly key = "shapes";
    private shapes: ShapeSummary[] = [];
    private renderStatuses = new Map<string, ShapeRenderStatus>();
    private detailsTag: string | null = null;
    private coalescing = false;

    constructor(private readonly ctx: PanelContext) { super(); }

    setShapes(items: ShapeSummary[], renderStatuses: ReadonlyMap<string, ShapeRenderStatus> = new Map()): void {
        this.shapes = [...items];
        this.renderStatuses = new Map(renderStatuses);
        if (this.detailsTag && !items.some(item => item.tag === this.detailsTag)) this.detailsTag = null;
        this.ctx.setBadge(String(items.length));
        this.scheduleRender();
    }

    updateRenderStatus(status: ShapeRenderStatus): void {
        this.renderStatuses.set(status.tag, status);
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader("Shapes"));

        const list = document.createElement("div");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "7px" });
        if (this.shapes.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No shapes yet. Shapes are created from Python (view.shapes.add_sphere(...)) or by an add-on.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "11px" });
            list.appendChild(empty);
        } else {
            for (const item of this.shapes) list.appendChild(this.renderShape(item));
        }
        this.host.appendChild(list);
        this.host.appendChild(this.renderGlobalActions());
    }

    private renderShape(item: ShapeSummary): HTMLDivElement {
        const row = card();
        row.setAttribute("data-molsysviewer-shape-tag", item.tag);
        row.setAttribute("data-molsysviewer-shape-op", item.op);
        row.setAttribute("data-molsysviewer-shape-broken", String(item.broken));
        row.style.opacity = item.hidden ? "0.48" : "1";

        const head = document.createElement("div");
        Object.assign(head.style, { display: "flex", alignItems: "center", gap: "6px" });
        const identity = document.createElement("div");
        identity.textContent = `${item.kind} · ${item.tag}`;
        identity.setAttribute("data-molsysviewer-shape-identity", item.tag);
        Object.assign(identity.style, {
            flex: "1 1 0", minWidth: "0", overflow: "hidden", textOverflow: "ellipsis",
            whiteSpace: "nowrap", color: item.broken ? "#fbbf24" : "#f4f4f5", fontSize: "12px", fontWeight: "650",
        });
        head.appendChild(identity);

        const focus = makeButton("⌖", () => this.ctx.onAction("focus_shape", { tag: item.tag }));
        focus.title = "Focus shape";
        focus.setAttribute("data-molsysviewer-shape-focus", item.tag);
        const eye = makeButton(item.hidden ? "⦻" : "👁", () => this.ctx.onAction("toggle_shape_visibility", { tag: item.tag }));
        eye.title = item.hidden ? "Show shape" : "Hide shape";
        eye.setAttribute("data-molsysviewer-shape-visibility", item.tag);
        const more = makeButton("⋯", () => {
            this.detailsTag = this.detailsTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        more.title = "Rename or move to layer";
        more.setAttribute("data-molsysviewer-shape-more", item.tag);
        const remove = makeButton("×", () => this.ctx.onAction("delete_shape", { tag: item.tag }));
        remove.title = "Delete shape";
        remove.setAttribute("data-molsysviewer-shape-delete", item.tag);
        for (const button of [focus, eye, more, remove]) {
            button.style.flex = "0 0 auto";
            head.appendChild(button);
        }
        row.appendChild(head);

        const layer = document.createElement("div");
        layer.textContent = item.layerTag && item.layerTag !== item.tag ? `layer: ${item.layerTag}` : item.subtitle || item.op;
        Object.assign(layer.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)" });
        row.appendChild(layer);

        const status = this.renderStatuses.get(item.tag);
        if (status && status.status !== "rendered") row.appendChild(this.renderWarning(status));
        if (item.broken) {
            const warning = document.createElement("div");
            warning.textContent = `⚠ ${item.brokenReason || "Shape anchor is broken."}`;
            warning.title = item.brokenReason || "Shape anchor is broken.";
            Object.assign(warning.style, { color: "#fbbf24", fontSize: "10px" });
            row.appendChild(warning);
        }

        if (this.detailsTag === item.tag) row.appendChild(this.renderDetails(item));
        row.appendChild(this.renderStyle(item));
        return row;
    }

    private renderWarning(status: ShapeRenderStatus): HTMLDivElement {
        const warning = document.createElement("div");
        const reason = status.reason || status.status.split("-").join(" ");
        warning.textContent = `⚠ Not rendered on frame ${status.frame}: ${reason}`;
        warning.title = reason;
        warning.setAttribute("data-molsysviewer-shape-render-warning", status.tag);
        Object.assign(warning.style, { color: "#fbbf24", fontSize: "10px" });
        return warning;
    }

    private renderDetails(item: ShapeSummary): HTMLDivElement {
        const editor = document.createElement("div");
        Object.assign(editor.style, { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px" });

        const rename = document.createElement("input");
        rename.value = item.tag;
        rename.setAttribute("data-molsysviewer-shape-rename", item.tag);
        const renameButton = makeButton("Rename", () => {
            const newTag = rename.value.trim();
            if (newTag && newTag !== item.tag) this.ctx.onAction("rename_shape", { tag: item.tag, new_tag: newTag });
        });
        renameButton.setAttribute("data-molsysviewer-shape-rename-confirm", item.tag);
        editor.appendChild(rename);
        editor.appendChild(renameButton);

        const layer = document.createElement("input");
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "Layer (blank detaches)";
        layer.setAttribute("data-molsysviewer-shape-layer", item.tag);
        const layerButton = makeButton("Set layer", () => this.ctx.onAction("set_shape_layer", {
            tag: item.tag, layer: layer.value.trim() || null,
        }));
        layerButton.setAttribute("data-molsysviewer-shape-layer-confirm", item.tag);
        editor.appendChild(layer);
        editor.appendChild(layerButton);
        return editor;
    }

    private renderStyle(item: ShapeSummary): HTMLDivElement {
        const section = document.createElement("div");
        section.setAttribute("data-molsysviewer-shape-style", item.tag);
        Object.assign(section.style, { display: "flex", flexDirection: "column", gap: "6px" });
        const controls = SHAPE_STYLE_CONTROLS[item.op] ?? [];
        if (controls.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "This shape type has no editable style.";
            empty.setAttribute("data-molsysviewer-shape-no-style", item.tag);
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "10px" });
            section.appendChild(empty);
            return section;
        }

        if (controls.includes("color") || controls.includes("colors")) {
            const color = document.createElement("input");
            color.type = "color";
            color.value = (item.color || "#ffffff").toLowerCase();
            color.setAttribute("data-molsysviewer-shape-color", item.tag);
            this.bindContinuous(color, () => this.ctx.onAction("set_shape_color", { tag: item.tag, color: color.value }));
            section.appendChild(this.controlRow(
                controls.includes("colors") ? `Colours (${item.nColors ?? 0})` : "Colour",
                color,
            ));
        }
        if (controls.includes("alpha")) {
            const alpha = document.createElement("input");
            alpha.type = "range";
            alpha.min = "0";
            alpha.max = "1";
            alpha.step = "0.05";
            alpha.value = String(item.alpha ?? 1);
            alpha.setAttribute("data-molsysviewer-shape-alpha", item.tag);
            this.bindContinuous(alpha, () => this.ctx.onAction("set_shape_alpha", { tag: item.tag, alpha: Number(alpha.value) }));
            section.appendChild(this.controlRow(`Alpha ${alpha.value}`, alpha));
        }
        if ((controls.includes("radius") || controls.includes("radii")) && item.radius) {
            const radius = document.createElement("input");
            radius.type = "number";
            radius.min = "0.01";
            radius.step = "0.1";
            radius.value = String(item.radius.magnitude);
            radius.setAttribute("data-molsysviewer-shape-radius", item.tag);
            this.bindContinuous(radius, () => this.ctx.onAction("set_shape_radius", {
                tag: item.tag,
                radius: { magnitude: Number(radius.value), unit: item.radius!.unit },
            }));
            const label = controls.includes("radii") ? `Radii (${item.nRadii ?? 0})` : "Radius";
            section.appendChild(this.controlRow(`${label} ${unitLabel(item.radius.unit)}`, radius));
        }
        if (controls.includes("radius_scale")) {
            section.appendChild(this.scaleControl(item, "radius_scale", item.radiusScale ?? 1, "Radius scale"));
        }
        if (controls.includes("length_scale")) {
            section.appendChild(this.scaleControl(item, "length_scale", item.lengthScale ?? 1, "Length scale"));
        }
        return section;
    }

    private scaleControl(item: ShapeSummary, kind: "radius_scale" | "length_scale", value: number, label: string): HTMLDivElement {
        const input = document.createElement("input");
        input.type = "number";
        input.min = "0.01";
        input.step = "0.05";
        input.value = String(value);
        input.setAttribute(`data-molsysviewer-shape-${kind.replace("_", "-")}`, item.tag);
        this.bindContinuous(input, () => this.ctx.onAction("set_shape_scale", { tag: item.tag, kind, value: Number(input.value) }));
        return this.controlRow(label, input);
    }

    private controlRow(labelText: string, control: HTMLElement): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "grid", gridTemplateColumns: "110px 1fr", alignItems: "center", gap: "7px" });
        const label = document.createElement("span");
        label.textContent = labelText;
        Object.assign(label.style, { fontSize: "10px", color: "rgba(244,244,245,0.66)" });
        row.appendChild(label);
        row.appendChild(control);
        return row;
    }

    private bindContinuous(input: HTMLInputElement, apply: () => void): void {
        input.addEventListener("focus", () => this.beginCoalescing());
        input.addEventListener("pointerdown", () => this.beginCoalescing());
        input.addEventListener("input", apply);
        input.addEventListener("change", () => this.endCoalescing());
        input.addEventListener("blur", () => this.endCoalescing());
    }

    private beginCoalescing(): void {
        if (this.coalescing) return;
        this.coalescing = true;
        this.ctx.onAction("begin_scene_history_coalescing");
    }

    private endCoalescing(): void {
        if (!this.coalescing) return;
        this.coalescing = false;
        this.ctx.onAction("end_scene_history_coalescing");
    }

    private renderGlobalActions(): HTMLDivElement {
        const row = document.createElement("div");
        Object.assign(row.style, { display: "flex", gap: "6px", marginTop: "8px" });
        for (const [label, action] of [
            ["Show all", "show_all_shapes"],
            ["Hide all", "hide_all_shapes"],
            ["Clear all", "clear_shapes"],
        ] as const) {
            const button = makeButton(label, () => this.ctx.onAction(action));
            button.setAttribute("data-molsysviewer-shape-global-action", action);
            row.appendChild(button);
        }
        return row;
    }
}
