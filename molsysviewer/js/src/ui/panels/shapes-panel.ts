import { BasePanel } from "./base-panel";
import type { SavedSelectionSummary } from "./group-panel";
import type { ActiveSelectionPayload, PanelContext } from "./types";
import { makeButton, makeSectionHeader, makeStyledSelect } from "./ui-helpers";

export type ShapeLength = { magnitude: number; unit: string };

export type ShapeSummary = {
    op: string;
    kind: string;
    tag: string;
    owner?: string;
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

export type ShapeTypeCatalogItem = {
    op: string;
    label: string;
    mode: "ui" | "guide";
    description: string;
    codeSnippet?: string;
};

export const ALL_SHAPE_TYPES: ReadonlyArray<ShapeTypeCatalogItem> = [
    { op: "add_sphere", label: "Sphere (3D Primitive)", mode: "ui", description: "3D sphere centered on atom selection or spatial coordinates." },
    { op: "add_network_links", label: "Cylinder / Link (Pair)", mode: "ui", description: "Cylindrical link connecting two selections or coordinate points." },
    { op: "add_displacement_vectors", label: "Displacement Vector (Arrow)", mode: "ui", description: "3D arrow representing direction and displacement between two points." },
    { op: "add_pocket_surface", label: "Pocket Surface", mode: "ui", description: "Molecular surface representation for binding pockets and active sites." },
    { op: "add_hbonds", label: "Hydrogen Bonds (H-Bonds)", mode: "ui", description: "Calculates and displays hydrogen bonding networks." },
    { op: "add_rings", label: "Aromatic Rings", mode: "ui", description: "Rings centroids and aromatic planes." },
    {
        op: "add_scalar_isosurface",
        label: "Scalar Isosurface (3D Grid Field)",
        mode: "guide",
        description: "3D surface mesh from electronic density or potential field data.",
        codeSnippet: "view.shapes.blobs.add_scalar_isosurface(\n    field_data, isovalue=0.02, color='#10b981'\n)",
    },
    {
        op: "add_pharmacophore_features",
        label: "Pharmacophore Features",
        mode: "guide",
        description: "Interaction sites (acceptors, donors, hydrophobic cores).",
        codeSnippet: "view.shapes.interaction_sites.add_pharmacophore_features(\n    features, color='#3b82f6'\n)",
    },
    {
        op: "add_channel_tube",
        label: "Channel Tube (Pore / Tunnel)",
        mode: "guide",
        description: "Pathways and radii along membrane channels or protein tunnels.",
        codeSnippet: "view.shapes.tubes.add_channel_tube(\n    path_points, radii=radii_list\n)",
    },
    {
        op: "add_anisotropy_ellipsoids",
        label: "Anisotropy Ellipsoids",
        mode: "guide",
        description: "Thermal motion or fluctuation tensor ellipsoids.",
        codeSnippet: "view.shapes.ellipsoids.add_anisotropy_ellipsoids(\n    tensors, atom_indices=indices\n)",
    },
    {
        op: "add_pocket_blob",
        label: "Pocket Blob (Cavity Mesh)",
        mode: "guide",
        description: "Volumetric cavity mesh around binding pockets.",
        codeSnippet: "view.shapes.blobs.add_pocket_blob(\n    pocket_coords, radius_scale=1.0\n)",
    },
    {
        op: "add_tetrahedra",
        label: "Tetrahedra Mesh",
        mode: "guide",
        description: "Volumetric tetrahedral elements.",
        codeSnippet: "view.shapes.tetrahedra.add_tetrahedra(\n    vertices, indices\n)",
    },
    {
        op: "add_triangle_faces",
        label: "Triangle Mesh",
        mode: "guide",
        description: "Custom surface meshes made of triangular faces.",
        codeSnippet: "view.shapes.triangles.add_triangle_faces(\n    vertices, faces\n)",
    },
    {
        op: "add_alpha_sphere_set",
        label: "Alpha Sphere Set",
        mode: "guide",
        description: "Alpha sphere clusters for pocket detection.",
        codeSnippet: "view.shapes.spheres.add_set_alpha_spheres(\n    spheres_data\n)",
    },
];

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

function unitLabel(unit: string): string {
    return unit === "angstrom" || unit === "angstroms" ? "Å" : unit;
}

export class ShapesPanel extends BasePanel {
    readonly key = "shapes";
    private shapes: ShapeSummary[] = [];
    private renderStatuses = new Map<string, ShapeRenderStatus>();
    private detailsTag: string | null = null;
    private coalescing = false;

    // Interactive Creation State
    private selectedOp = "add_sphere";
    private customTag = "";
    private anchorType: "selection" | "coordinates" = "selection";
    private stagedAnchor1: number[] | null = null;
    private stagedAnchor2: number[] | null = null;
    private coord1: [number, number, number] = [0.0, 0.0, 0.0];
    private coord2: [number, number, number] = [0.0, 0.0, 0.0];
    private radiusVal = 0.15; // in nm
    private colorVal = "#3b82f6";
    private alphaVal = 0.8;

    private selection: ActiveSelectionPayload = { atom_indices: [] };
    private savedSelections: SavedSelectionSummary[] = [];

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

    setSavedSelections(items: SavedSelectionSummary[]): void {
        this.savedSelections = [...items];
        this.scheduleRender();
    }

    setCurrentSelection(selection: ActiveSelectionPayload): void {
        this.selection = selection;
        this.scheduleRender();
    }

    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren();

        // 1. Section Header and Global Actions Card
        this.host.appendChild(makeSectionHeader("Shapes"));
        this.host.appendChild(this.renderGlobalActions());

        // 2. New Shape Card
        this.host.appendChild(makeSectionHeader("New shape"));
        this.host.appendChild(this.renderNewShapeCard());

        // 3. Saved Shapes List
        this.host.appendChild(makeSectionHeader("Saved shapes"));
        const list = document.createElement("div");
        Object.assign(list.style, { display: "flex", flexDirection: "column", gap: "7px" });
        if (this.shapes.length === 0) {
            const empty = document.createElement("div");
            empty.textContent = "No shapes yet. Shapes are created above, from Python, or by an add-on.";
            Object.assign(empty.style, { color: "rgba(244,244,245,0.52)", fontSize: "11px" });
            list.appendChild(empty);
        } else {
            for (const item of this.shapes) list.appendChild(this.renderShape(item));
        }
        this.host.appendChild(list);
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

        const totalCount = this.shapes.length;
        const visibleCount = this.shapes.filter(m => !m.hidden).length;

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
        textSpan.textContent = `${visibleCount} of ${totalCount} shape${totalCount === 1 ? "" : "s"} visible`;
        info.appendChild(textSpan);
        row.appendChild(info);

        const actions = document.createElement("div");
        Object.assign(actions.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            flexShrink: "0",
        });

        for (const [label, action] of [
            ["Show all", "show_all_shapes"],
            ["Hide all", "hide_all_shapes"],
        ] as const) {
            const button = makeButton(label, () => {
                this.ctx.onAction(action);
            });
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            button.style.whiteSpace = "nowrap";
            button.setAttribute("data-molsysviewer-shape-global-action", action);
            actions.appendChild(button);
        }
        row.appendChild(actions);
        globalCard.appendChild(row);

        return globalCard;
    }

    private renderNewShapeCard(): HTMLDivElement {
        const formCard = card();
        formCard.setAttribute("data-molsysviewer-shape-new-card", "true");
        Object.assign(formCard.style, {
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            marginBottom: "10px",
        });

        // Type Selector Dropdown
        const typeRow = document.createElement("div");
        Object.assign(typeRow.style, { display: "flex", alignItems: "center", gap: "8px" });
        const typeLabel = document.createElement("span");
        typeLabel.textContent = "Type:";
        Object.assign(typeLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.7)", width: "50px" });
        typeRow.appendChild(typeLabel);

        const selectOptions = ALL_SHAPE_TYPES.map(item => ({ value: item.op, label: item.label }));
        const select = makeStyledSelect(selectOptions, this.selectedOp, (val) => {
            this.selectedOp = val;
            this.scheduleRender();
        });
        select.style.flex = "1 1 auto";
        select.setAttribute("data-molsysviewer-shape-type-select", "true");
        typeRow.appendChild(select);
        formCard.appendChild(typeRow);

        const currentCatalogItem = ALL_SHAPE_TYPES.find(i => i.op === this.selectedOp) || ALL_SHAPE_TYPES[0];

        if (currentCatalogItem.mode === "guide") {
            // Render Guide Card for Python/Add-on generated shapes
            const guideBox = document.createElement("div");
            Object.assign(guideBox.style, {
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                padding: "8px",
                background: "rgba(0,0,0,0.15)",
                borderRadius: "6px",
                border: "1px solid rgba(255,255,255,0.06)",
                marginTop: "4px",
            });

            const desc = document.createElement("div");
            desc.textContent = `ℹ ${currentCatalogItem.description}`;
            Object.assign(desc.style, { fontSize: "11px", color: "rgba(244,244,245,0.75)", lineHeight: "1.35" });
            guideBox.appendChild(desc);

            if (currentCatalogItem.codeSnippet) {
                const codeTitle = document.createElement("div");
                codeTitle.textContent = "Create from Python:";
                Object.assign(codeTitle.style, { fontSize: "10px", fontWeight: "600", color: "rgba(244,244,245,0.5)", marginTop: "2px" });
                guideBox.appendChild(codeTitle);

                const pre = document.createElement("pre");
                pre.textContent = currentCatalogItem.codeSnippet;
                Object.assign(pre.style, {
                    margin: "0",
                    padding: "6px 8px",
                    background: "rgba(0,0,0,0.3)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "4px",
                    color: "#34d399",
                    fontFamily: "monospace",
                    fontSize: "10px",
                    overflowX: "auto",
                    whiteSpace: "pre-wrap",
                });
                guideBox.appendChild(pre);
            }

            formCard.appendChild(guideBox);
        } else {
            // Render Interactive Creation Form (Mode UI)
            const isDoubleAnchor = this.selectedOp === "add_network_links" || this.selectedOp === "add_displacement_vectors";
            const isSingleAnchorOnly = this.selectedOp === "add_pocket_surface" || this.selectedOp === "add_hbonds" || this.selectedOp === "add_rings";

            // Optional Tag Name Row
            const tagRow = document.createElement("div");
            Object.assign(tagRow.style, { display: "flex", alignItems: "center", gap: "8px" });
            const tagLabel = document.createElement("span");
            tagLabel.textContent = "Tag:";
            Object.assign(tagLabel.style, { fontSize: "11px", color: "rgba(244,244,245,0.7)", width: "50px" });
            tagRow.appendChild(tagLabel);

            const tagInput = document.createElement("input");
            tagInput.value = this.customTag;
            tagInput.placeholder = "Optional name (e.g. site_sphere)";
            Object.assign(tagInput.style, { flex: "1 1 auto", ...INPUT_STYLE });
            tagInput.setAttribute("data-molsysviewer-shape-new-tag", "true");
            tagInput.addEventListener("input", () => { this.customTag = tagInput.value; });
            tagRow.appendChild(tagInput);
            formCard.appendChild(tagRow);

            if (!isSingleAnchorOnly && !isDoubleAnchor) {
                // Anchor Mode Radio (Selection vs Coordinates for Sphere)
                const modeRow = document.createElement("div");
                Object.assign(modeRow.style, { display: "flex", alignItems: "center", gap: "12px", fontSize: "11px", color: "rgba(244,244,245,0.8)" });
                
                const selLabel = document.createElement("label");
                Object.assign(selLabel.style, { display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" });
                const selRadio = document.createElement("input");
                selRadio.type = "radio";
                selRadio.name = "shapeAnchorMode";
                selRadio.checked = this.anchorType === "selection";
                selRadio.addEventListener("change", () => {
                    this.anchorType = "selection";
                    this.scheduleRender();
                });
                selLabel.appendChild(selRadio);
                const selSpan = document.createElement("span");
                selSpan.textContent = "Active selection";
                selLabel.appendChild(selSpan);

                const coordLabel = document.createElement("label");
                Object.assign(coordLabel.style, { display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" });
                const coordRadio = document.createElement("input");
                coordRadio.type = "radio";
                coordRadio.name = "shapeAnchorMode";
                coordRadio.checked = this.anchorType === "coordinates";
                coordRadio.addEventListener("change", () => {
                    this.anchorType = "coordinates";
                    this.scheduleRender();
                });
                coordLabel.appendChild(coordRadio);
                const coordSpan = document.createElement("span");
                coordSpan.textContent = "Coordinates";
                coordLabel.appendChild(coordSpan);

                modeRow.appendChild(selLabel);
                modeRow.appendChild(coordLabel);
                formCard.appendChild(modeRow);
            }

            // Anchor Buttons & Controls
            if (!isDoubleAnchor && (this.anchorType === "selection" || isSingleAnchorOnly)) {
                // Single Staged Anchor Box
                const anchorBox = document.createElement("div");
                Object.assign(anchorBox.style, {
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "6px 8px",
                    background: "rgba(0,0,0,0.18)",
                    borderRadius: "6px",
                    border: "1px solid rgba(255,255,255,0.08)",
                });

                const anchorBtn = makeButton("Anchor", () => {
                    this.stagedAnchor1 = [...this.selection.atom_indices];
                    this.scheduleRender();
                });
                anchorBtn.style.padding = "3px 8px";
                anchorBtn.style.fontSize = "11px";
                anchorBtn.setAttribute("data-molsysviewer-shape-anchor-btn", "true");

                const hint = document.createElement("div");
                Object.assign(hint.style, { fontSize: "11px", color: "rgba(244,244,245,0.75)" });
                if (this.stagedAnchor1 === null) {
                    hint.textContent = "Click Anchor to stage active selection";
                    hint.style.color = "rgba(244,244,245,0.45)";
                } else {
                    const cnt = this.stagedAnchor1.length;
                    hint.textContent = `Anchored to selection (${cnt} atom${cnt === 1 ? "" : "s"})`;
                }

                anchorBox.appendChild(anchorBtn);
                anchorBox.appendChild(hint);
                formCard.appendChild(anchorBox);
            } else if (!isDoubleAnchor && this.anchorType === "coordinates") {
                // Single Coordinate Inputs [X, Y, Z] (nm)
                const coordBox = document.createElement("div");
                Object.assign(coordBox.style, { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "6px" });
                
                (["X (nm)", "Y (nm)", "Z (nm)"] as const).forEach((lbl, idx) => {
                    const col = document.createElement("div");
                    Object.assign(col.style, { display: "flex", flexDirection: "column", gap: "2px" });
                    const span = document.createElement("span");
                    span.textContent = lbl;
                    Object.assign(span.style, { fontSize: "10px", color: "rgba(244,244,245,0.6)" });
                    
                    const numInput = document.createElement("input");
                    numInput.type = "number";
                    numInput.step = "0.1";
                    numInput.value = String(this.coord1[idx]);
                    Object.assign(numInput.style, INPUT_STYLE);
                    numInput.addEventListener("input", () => {
                        this.coord1[idx] = Number(numInput.value) || 0;
                    });
                    col.appendChild(span);
                    col.appendChild(numInput);
                    coordBox.appendChild(col);
                });
                formCard.appendChild(coordBox);
            } else if (isDoubleAnchor) {
                // Double Anchor Box (Start and End)
                const dBox = document.createElement("div");
                Object.assign(dBox.style, { display: "flex", flexDirection: "column", gap: "6px" });

                // Anchor 1
                const a1Box = document.createElement("div");
                Object.assign(a1Box.style, { display: "flex", alignItems: "center", gap: "8px" });
                const btn1 = makeButton("Anchor 1 (Start)", () => {
                    this.stagedAnchor1 = [...this.selection.atom_indices];
                    this.scheduleRender();
                });
                btn1.style.padding = "3px 8px";
                btn1.style.fontSize = "10px";
                const hint1 = document.createElement("span");
                Object.assign(hint1.style, { fontSize: "10px", color: "rgba(244,244,245,0.7)" });
                hint1.textContent = this.stagedAnchor1 ? `staged (${this.stagedAnchor1.length} atoms)` : "none staged";
                a1Box.appendChild(btn1);
                a1Box.appendChild(hint1);
                dBox.appendChild(a1Box);

                // Anchor 2
                const a2Box = document.createElement("div");
                Object.assign(a2Box.style, { display: "flex", alignItems: "center", gap: "8px" });
                const btn2 = makeButton("Anchor 2 (End)", () => {
                    this.stagedAnchor2 = [...this.selection.atom_indices];
                    this.scheduleRender();
                });
                btn2.style.padding = "3px 8px";
                btn2.style.fontSize = "10px";
                const hint2 = document.createElement("span");
                Object.assign(hint2.style, { fontSize: "10px", color: "rgba(244,244,245,0.7)" });
                hint2.textContent = this.stagedAnchor2 ? `staged (${this.stagedAnchor2.length} atoms)` : "none staged";
                a2Box.appendChild(btn2);
                a2Box.appendChild(hint2);
                dBox.appendChild(a2Box);

                formCard.appendChild(dBox);
            }

            // Style Parameters Row (Radius, Colour, Alpha)
            const styleRow = document.createElement("div");
            Object.assign(styleRow.style, { display: "flex", alignItems: "center", gap: "10px", marginTop: "4px" });

            // Radius (nm)
            const radCol = document.createElement("div");
            Object.assign(radCol.style, { display: "flex", alignItems: "center", gap: "4px" });
            const radLabel = document.createElement("span");
            radLabel.textContent = "Radius (nm):";
            Object.assign(radLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.6)" });
            const radInput = document.createElement("input");
            radInput.type = "number";
            radInput.min = "0.01";
            radInput.step = "0.05";
            radInput.value = String(this.radiusVal);
            radInput.style.width = "55px";
            Object.assign(radInput.style, INPUT_STYLE);
            radInput.setAttribute("data-molsysviewer-shape-new-radius", "true");
            radInput.addEventListener("input", () => { this.radiusVal = Number(radInput.value) || 0.15; });
            radCol.appendChild(radLabel);
            radCol.appendChild(radInput);
            styleRow.appendChild(radCol);

            // Color
            const colCol = document.createElement("div");
            Object.assign(colCol.style, { display: "flex", alignItems: "center", gap: "4px" });
            const colLabel = document.createElement("span");
            colLabel.textContent = "Colour:";
            Object.assign(colLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.6)" });
            const colInput = document.createElement("input");
            colInput.type = "color";
            colInput.value = this.colorVal;
            colInput.setAttribute("data-molsysviewer-shape-new-color", "true");
            colInput.addEventListener("input", () => { this.colorVal = colInput.value; });
            colCol.appendChild(colLabel);
            colCol.appendChild(colInput);
            styleRow.appendChild(colCol);

            // Alpha Slider
            const alphaCol = document.createElement("div");
            Object.assign(alphaCol.style, { display: "flex", alignItems: "center", gap: "4px", flex: "1 1 auto" });
            const alphaLabel = document.createElement("span");
            alphaLabel.textContent = "Alpha:";
            Object.assign(alphaLabel.style, { fontSize: "10px", color: "rgba(244,244,245,0.6)" });
            const alphaInput = document.createElement("input");
            alphaInput.type = "range";
            alphaInput.min = "0";
            alphaInput.max = "1";
            alphaInput.step = "0.05";
            alphaInput.value = String(this.alphaVal);
            alphaInput.style.flex = "1 1 auto";
            alphaInput.setAttribute("data-molsysviewer-shape-new-alpha", "true");
            alphaInput.addEventListener("input", () => { this.alphaVal = Number(alphaInput.value); });
            alphaCol.appendChild(alphaLabel);
            alphaCol.appendChild(alphaInput);
            styleRow.appendChild(alphaCol);

            formCard.appendChild(styleRow);

            // Create Button
            const createBtnRow = document.createElement("div");
            Object.assign(createBtnRow.style, { display: "flex", justifyContent: "flex-end", marginTop: "4px" });

            const createBtn = makeButton("Create Shape", () => {
                const payload: Record<string, unknown> = {
                    shape_type: this.selectedOp,
                    tag: this.customTag.trim() || undefined,
                    color: this.colorVal,
                    alpha: this.alphaVal,
                    radius: this.radiusVal,
                };

                if (isDoubleAnchor) {
                    if (this.stagedAnchor1) payload.atom_indices = this.stagedAnchor1;
                    if (this.stagedAnchor2) payload.atom_indices_2 = this.stagedAnchor2;
                } else if (this.anchorType === "selection" || isSingleAnchorOnly) {
                    if (this.stagedAnchor1) payload.atom_indices = this.stagedAnchor1;
                } else if (this.anchorType === "coordinates") {
                    payload.coordinates = this.coord1;
                }

                this.ctx.onAction("create_shape", payload);
                this.stagedAnchor1 = null;
                this.stagedAnchor2 = null;
                this.scheduleRender();
            });
            createBtn.style.padding = "4px 12px";
            createBtn.style.fontSize = "11px";
            createBtn.style.fontWeight = "600";
            createBtn.setAttribute("data-molsysviewer-shape-create-btn", "true");
            createBtnRow.appendChild(createBtn);
            formCard.appendChild(createBtnRow);
        }

        return formCard;
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
        identity.textContent = `${item.kind} · ${item.tag}${item.owner ? ` · from ${item.owner}` : ""}`;
        identity.setAttribute("data-molsysviewer-shape-identity", item.tag);
        Object.assign(identity.style, {
            flex: "1 1 0", minWidth: "0", overflow: "hidden", textOverflow: "ellipsis",
            whiteSpace: "nowrap", color: item.broken ? "#fbbf24" : "#f4f4f5", fontSize: "12px", fontWeight: "650",
        });
        head.appendChild(identity);
        row.appendChild(head);

        // Action Buttons Row (btnRow container)
        const btnRow = document.createElement("div");
        Object.assign(btnRow.style, {
            display: "flex",
            gap: "4px",
            alignItems: "center",
            marginTop: "4px",
        });

        const focus = makeButton("Focus", () => this.ctx.onAction("focus_shape", { tag: item.tag }));
        focus.title = "Focus shape";
        focus.setAttribute("data-molsysviewer-shape-focus", item.tag);

        const eye = makeButton(item.hidden ? "⦻" : "👁", () => this.ctx.onAction("toggle_shape_visibility", { tag: item.tag }));
        eye.title = item.hidden ? "Show shape" : "Hide shape";
        eye.setAttribute("data-molsysviewer-shape-visibility", item.tag);

        const more = makeButton("Edit", () => {
            this.detailsTag = this.detailsTag === item.tag ? null : item.tag;
            this.scheduleRender();
        });
        more.title = "Rename, layer, or edit style";
        more.setAttribute("data-molsysviewer-shape-more", item.tag);

        const remove = makeButton("🗑", () => this.ctx.onAction("delete_shape", { tag: item.tag }));
        remove.title = "Delete shape";
        remove.setAttribute("data-molsysviewer-shape-delete", item.tag);

        for (const button of [focus, eye, more, remove]) {
            button.style.flex = "0 0 auto";
            button.style.padding = "3px 6px";
            button.style.fontSize = "10px";
            btnRow.appendChild(button);
        }
        row.appendChild(btnRow);

        const layer = document.createElement("div");
        layer.textContent = item.layerTag && item.layerTag !== item.tag ? `layer: ${item.layerTag}` : item.subtitle || item.op;
        Object.assign(layer.style, { fontSize: "10px", color: "rgba(244,244,245,0.56)", marginTop: "2px" });
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
        Object.assign(editor.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            marginTop: "6px",
            padding: "8px",
            background: "rgba(0,0,0,0.12)",
            borderRadius: "6px",
        });

        // Rename Row
        const renameRow = document.createElement("div");
        Object.assign(renameRow.style, { display: "flex", gap: "6px" });
        const rename = document.createElement("input");
        rename.value = item.tag;
        Object.assign(rename.style, { flex: "1 1 auto", ...INPUT_STYLE });
        rename.setAttribute("data-molsysviewer-shape-rename", item.tag);
        const renameButton = makeButton("Rename", () => {
            const newTag = rename.value.trim();
            if (newTag && newTag !== item.tag) this.ctx.onAction("rename_shape", { tag: item.tag, new_tag: newTag });
        });
        renameButton.style.padding = "4px 8px";
        renameButton.style.fontSize = "11px";
        renameButton.style.flex = "0 0 auto";
        renameButton.setAttribute("data-molsysviewer-shape-rename-confirm", item.tag);
        renameRow.appendChild(rename);
        renameRow.appendChild(renameButton);
        editor.appendChild(renameRow);

        // Layer Row
        const layerRow = document.createElement("div");
        Object.assign(layerRow.style, { display: "flex", gap: "6px" });
        const layer = document.createElement("input");
        layer.value = item.layerTag && item.layerTag !== item.tag ? item.layerTag : "";
        layer.placeholder = "Layer (blank detaches)";
        Object.assign(layer.style, { flex: "1 1 auto", ...INPUT_STYLE });
        layer.setAttribute("data-molsysviewer-shape-layer", item.tag);
        const layerButton = makeButton("Set layer", () => this.ctx.onAction("set_shape_layer", {
            tag: item.tag, layer: layer.value.trim() || null,
        }));
        layerButton.style.padding = "4px 8px";
        layerButton.style.fontSize = "11px";
        layerButton.style.flex = "0 0 auto";
        layerButton.setAttribute("data-molsysviewer-shape-layer-confirm", item.tag);
        layerRow.appendChild(layer);
        layerRow.appendChild(layerButton);
        editor.appendChild(layerRow);

        // Style Section Header & Controls
        const sHeader = document.createElement("div");
        sHeader.textContent = "Style";
        Object.assign(sHeader.style, {
            fontSize: "11px",
            fontWeight: "700",
            color: "rgba(255,255,255,0.8)",
            marginTop: "4px",
            paddingTop: "4px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
        });
        editor.appendChild(sHeader);
        editor.appendChild(this.renderStyle(item));

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
}
