import assert from "node:assert";
import test from "node:test";

import { ShapesPanel, SHAPE_STYLE_CONTROLS, type ShapeSummary } from "../../src/ui/panels/shapes-panel";

class FakeElement {
    readonly style: Record<string, string> = {};
    readonly children: FakeElement[] = [];
    textContent = "";
    title = "";
    type = "";
    value = "";
    min = "";
    max = "";
    step = "";
    placeholder = "";
    disabled = false;
    private readonly attributes = new Map<string, string>();
    private readonly listeners = new Map<string, Array<(event?: any) => void>>();

    appendChild(child: FakeElement) { this.children.push(child); return child; }
    replaceChildren(...children: FakeElement[]) { this.children.length = 0; this.children.push(...children); }
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }
    addEventListener(name: string, handler: (event?: any) => void) {
        const handlers = this.listeners.get(name) ?? [];
        handlers.push(handler);
        this.listeners.set(name, handlers);
    }
    dispatch(name: string, event: any = { preventDefault() {}, stopPropagation() {} }) {
        for (const handler of this.listeners.get(name) ?? []) handler(event);
    }
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    (globalThis as any).document = { createElement: () => new FakeElement() };
    return () => { (globalThis as any).document = previousDocument; };
}

function collect(root: FakeElement, attribute: string): FakeElement[] {
    const out: FakeElement[] = [];
    const walk = (node: FakeElement) => {
        if (node.getAttribute(attribute) !== undefined) out.push(node);
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function byAttribute(root: FakeElement, attribute: string, value: string): FakeElement {
    const found = collect(root, attribute).find(node => node.getAttribute(attribute) === value);
    assert.ok(found, `missing [${attribute}="${value}"]`);
    return found;
}

function summary(op: string): ShapeSummary {
    return {
        op,
        kind: op.slice(4).split("_").join("-"),
        tag: "shape1",
        title: "Shape",
        hidden: false,
        atomIndices: [],
        color: "#123456",
        nColors: 2,
        radius: { magnitude: 3, unit: "angstrom" },
        nRadii: 2,
        alpha: 0.6,
        radiusScale: 1.2,
        lengthScale: 1.4,
        broken: false,
    };
}

const controlAttribute: Record<string, string> = {
    color: "data-molsysviewer-shape-color",
    colors: "data-molsysviewer-shape-color",
    alpha: "data-molsysviewer-shape-alpha",
    radius: "data-molsysviewer-shape-radius",
    radii: "data-molsysviewer-shape-radius",
    radius_scale: "data-molsysviewer-shape-radius-scale",
    length_scale: "data-molsysviewer-shape-length-scale",
};

const EXPECTED_STYLE_CONTROLS: Readonly<Record<string, readonly string[]>> = {
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

test("ShapesPanel derives exactly the editable controls from every wire op", () => {
    const restore = installFakeDom();
    try {
        assert.deepStrictEqual(Object.keys(SHAPE_STYLE_CONTROLS).sort(), Object.keys(EXPECTED_STYLE_CONTROLS).sort());
        for (const [op, expected] of Object.entries(EXPECTED_STYLE_CONTROLS)) {
            const host = new FakeElement();
            const panel = new ShapesPanel({ onAction: () => {}, setBadge: () => {} });
            panel.mount(host as any);
            panel.setVisible(true);
            panel.setShapes([summary(op)]);

            const actual = new Set<string>();
            for (const [control, attribute] of Object.entries(controlAttribute)) {
                if (collect(host, attribute).length > 0) actual.add(control);
            }
            const normalizedExpected = new Set(expected.map(control =>
                control === "colors" ? "color" : control === "radii" ? "radius" : control
            ));
            const normalizedActual = new Set([...actual].map(control =>
                control === "colors" ? "color" : control === "radii" ? "radius" : control
            ));
            assert.deepStrictEqual(normalizedActual, normalizedExpected, op);
            assert.strictEqual(
                collect(host, "data-molsysviewer-shape-no-style").length > 0,
                expected.length === 0,
                `${op} no-style state`,
            );
        }
    } finally {
        restore();
    }
});

test("ShapesPanel routes lifecycle, style, units and diagnostics through panel actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement();
        const actions: Array<[string, Record<string, unknown> | undefined]> = [];
        const panel = new ShapesPanel({
            onAction: (action, details) => actions.push([action, details]),
            setBadge: () => {},
        });
        panel.mount(host as any);
        panel.setVisible(true);
        panel.setShapes([summary("add_sphere")], new Map([["shape1", {
            tag: "shape1", op: "add_sphere", frame: 42, status: "invalid-indices", reason: "invalid coordinates",
        }]]));

        assert.ok(byAttribute(host, "data-molsysviewer-shape-render-warning", "shape1").textContent.includes("frame 42"));
        byAttribute(host, "data-molsysviewer-shape-visibility", "shape1").dispatch("click");
        const radius = byAttribute(host, "data-molsysviewer-shape-radius", "shape1");
        radius.value = "4.5";
        radius.dispatch("focus");
        radius.dispatch("input");
        radius.dispatch("change");

        assert.deepStrictEqual(actions, [
            ["toggle_shape_visibility", { tag: "shape1" }],
            ["begin_scene_history_coalescing", undefined],
            ["set_shape_radius", { tag: "shape1", radius: { magnitude: 4.5, unit: "angstrom" } }],
            ["end_scene_history_coalescing", undefined],
        ]);
    } finally {
        restore();
    }
});

test("ShapesPanel routes every lifecycle and style affordance through the closed action seam", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement();
        const actions: Array<[string, Record<string, unknown> | undefined]> = [];
        const panel = new ShapesPanel({
            onAction: (action, details) => actions.push([action, details]),
            setBadge: () => {},
        });
        panel.mount(host as any);
        panel.setVisible(true);
        panel.setShapes([summary("add_sphere")]);

        byAttribute(host, "data-molsysviewer-shape-focus", "shape1").dispatch("click");
        byAttribute(host, "data-molsysviewer-shape-visibility", "shape1").dispatch("click");
        byAttribute(host, "data-molsysviewer-shape-more", "shape1").dispatch("click");
        const rename = byAttribute(host, "data-molsysviewer-shape-rename", "shape1");
        rename.value = "renamed";
        byAttribute(host, "data-molsysviewer-shape-rename-confirm", "shape1").dispatch("click");
        const layer = byAttribute(host, "data-molsysviewer-shape-layer", "shape1");
        layer.value = "analysis";
        byAttribute(host, "data-molsysviewer-shape-layer-confirm", "shape1").dispatch("click");
        byAttribute(host, "data-molsysviewer-shape-delete", "shape1").dispatch("click");

        const color = byAttribute(host, "data-molsysviewer-shape-color", "shape1");
        color.value = "#abcdef";
        color.dispatch("input");
        const alpha = byAttribute(host, "data-molsysviewer-shape-alpha", "shape1");
        alpha.value = "0.75";
        alpha.dispatch("input");
        const radius = byAttribute(host, "data-molsysviewer-shape-radius", "shape1");
        radius.value = "5";
        radius.dispatch("input");
        for (const action of ["show_all_shapes", "hide_all_shapes", "clear_shapes"]) {
            byAttribute(host, "data-molsysviewer-shape-global-action", action).dispatch("click");
        }

        panel.setShapes([summary("add_displacement_vectors")]);
        const radiusScale = byAttribute(host, "data-molsysviewer-shape-radius-scale", "shape1");
        radiusScale.value = "1.5";
        radiusScale.dispatch("input");
        const lengthScale = byAttribute(host, "data-molsysviewer-shape-length-scale", "shape1");
        lengthScale.value = "2";
        lengthScale.dispatch("input");

        assert.deepStrictEqual(actions, [
            ["focus_shape", { tag: "shape1" }],
            ["toggle_shape_visibility", { tag: "shape1" }],
            ["rename_shape", { tag: "shape1", new_tag: "renamed" }],
            ["set_shape_layer", { tag: "shape1", layer: "analysis" }],
            ["delete_shape", { tag: "shape1" }],
            ["set_shape_color", { tag: "shape1", color: "#abcdef" }],
            ["set_shape_alpha", { tag: "shape1", alpha: 0.75 }],
            ["set_shape_radius", { tag: "shape1", radius: { magnitude: 5, unit: "angstrom" } }],
            ["show_all_shapes", undefined],
            ["hide_all_shapes", undefined],
            ["clear_shapes", undefined],
            ["set_shape_scale", { tag: "shape1", kind: "radius_scale", value: 1.5 }],
            ["set_shape_scale", { tag: "shape1", kind: "length_scale", value: 2 }],
        ]);
    } finally {
        restore();
    }
});

test("ShapesPanel identifies the addon that created a shape", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement();
        const panel = new ShapesPanel({ onAction: () => {}, setBadge: () => {} });
        panel.mount(host as any);
        panel.setVisible(true);
        panel.setShapes([{ ...summary("add_sphere"), owner: "elastnetmt" }]);

        assert.strictEqual(
            byAttribute(host, "data-molsysviewer-shape-identity", "shape1").textContent,
            "sphere · shape1 · from elastnetmt",
        );
    } finally {
        restore();
    }
});
