import assert from "node:assert";
import test from "node:test";

import { ViewerContextMenu } from "../../src/ui/context-menu";

class FakeElement {
    public tagName = "DIV";
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
    public value = "";
    public placeholder = "";
    public offsetWidth = 180;
    public offsetHeight = 120;
    private listeners = new Map<string, Array<(event?: any) => void>>();

    appendChild(child: FakeElement) {
        this.children.push(child);
        return child;
    }

    replaceChildren(...children: FakeElement[]) {
        this.children.length = 0;
        this.children.push(...children);
    }

    remove() {}
    focus() {}
    setAttribute(_name: string, _value: string) {}
    contains(target: any) {
        if (target === this) return true;
        return this.children.includes(target);
    }
    getBoundingClientRect() {
        return { left: 0, top: 0, width: 600, height: 400 };
    }

    addEventListener(name: string, handler: (event?: any) => void) {
        const handlers = this.listeners.get(name) ?? [];
        handlers.push(handler);
        this.listeners.set(name, handlers);
    }

    dispatch(name: string, event?: any) {
        for (const handler of this.listeners.get(name) ?? []) handler(event);
    }

    dispatchEvent(event: any) {
        this.dispatch(event?.type ?? "", event);
        return true;
    }
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    const previousWindow = (globalThis as any).window;
    const fakeHead = new FakeElement();
    fakeHead.tagName = "HEAD";
    (globalThis as any).document = {
        createElement: (tag: string) => {
            const el = new FakeElement();
            el.tagName = String(tag).toUpperCase();
            return el;
        },
        getElementById: (_id: string) => {
            return null;
        },
        head: fakeHead,
    };
    (globalThis as any).window = {
        addEventListener() {},
        removeEventListener() {},
    };
    return () => {
        (globalThis as any).document = previousDocument;
        (globalThis as any).window = previousWindow;
    };
}

function collectTexts(node: FakeElement): string[] {
    const out: string[] = [];
    const walk = (current: FakeElement) => {
        if (current.textContent) out.push(current.textContent);
        for (const child of current.children) walk(child);
    };
    walk(node);
    return out;
}

function findNodeByText(node: FakeElement, text: string): FakeElement | null {
    if (node.textContent === text) return node;
    for (const child of node.children) {
        const found = findNodeByText(child, text);
        if (found) return found;
    }
    return null;
}

function findNodeByTag(node: FakeElement, tag: string): FakeElement | null {
    if (node.tagName === tag.toUpperCase()) return node;
    for (const child of node.children) {
        const found = findNodeByTag(child, tag);
        if (found) return found;
    }
    return null;
}

test("ViewerContextMenu hides actions unsupported by a projected surface", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const menu = new ViewerContextMenu(
            host,
            undefined,
            undefined,
            undefined,
            undefined,
            { allowedActions: new Set(["focus_target"]) },
        );
        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0] },
            10,
            20,
        );

        assert.strictEqual(findNodeByText(host, "Focus Target")?.style.display, "block");
        assert.strictEqual(findNodeByText(host, "Distance")?.style.display, "none");
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders active selection section and selection actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any }> = [];
        const menu = new ViewerContextMenu(host, undefined, (action, target) => {
            actions.push({ action, target });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "annotation", atom_indices: [0, 1], tag: "notes", text: "Catalytic" },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "mixed",
                element_level: "group",
                target_level: "mixed",
                items: [],
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 2,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 1,
            },
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Catalytic"));
        assert.ok(texts.includes("Focus Target"));
        assert.ok(texts.includes("Active selection: mixed (0 items)"));
        assert.ok(texts.includes("Focus Selection"));
        assert.ok(texts.includes("Save Selection"));
        assert.ok(texts.includes("Create Region from Selection"));
        assert.ok(texts.includes("Add Label from Selection"));
        assert.ok(!texts.includes("Remove Selected Atoms"));
        assert.ok(texts.includes("Clear Selection"));

        const targetButton = findNodeByText(root, "Focus Target");
        assert.ok(targetButton);
        targetButton!.dispatch("click");

        menu.open(
            { event: "interaction_context_menu", kind: "annotation", atom_indices: [0, 1], tag: "notes", text: "Catalytic" },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "mixed",
                element_level: "group",
                target_level: "mixed",
                items: [],
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 2,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 1,
            },
        );

        const refreshedRoot = (menu as any).root as FakeElement;
        const focusButton = findNodeByText(refreshedRoot, "Focus Selection");
        assert.ok(focusButton);
        focusButton!.dispatch("click");

        assert.deepStrictEqual(actions, [
            {
                action: "focus_target",
                target: { event: "interaction_context_menu", kind: "annotation", atom_indices: [0, 1], tag: "notes", text: "Catalytic" },
            },
            {
                action: "focus_selection",
                target: { event: "interaction_context_menu", kind: "annotation", atom_indices: [0, 1], tag: "notes", text: "Catalytic" },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu exposes selection expanders from the context menu", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });
        const selection = {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "atom",
            target_level: "none",
            items: [],
            atom_indices: [0, 1, 2, 3],
            group_indices: [0, 1],
            component_indices: [],
            chain_indices: [0],
            molecule_indices: [],
            entity_indices: [0],
            count_atoms: 4,
            count_groups: 2,
            count_shapes: 0,
            count_annotations: 0,
        };
        const target = { event: "interaction_context_menu", kind: "structure" as const, atom_indices: [0, 1], group_name: "ALA", chain_name: "A" };

        menu.open(target, 10, 20, selection);
        let root = (menu as any).root as FakeElement;
        let texts = collectTexts(root);
        assert.ok(texts.includes("Expand selection to..."));
        assert.ok(texts.includes("Group"));
        assert.ok(texts.includes("Component"));
        assert.ok(texts.includes("Molecule"));
        assert.ok(texts.includes("Chain"));
        assert.ok(texts.includes("Entity"));
        assert.ok(texts.includes("Spatial expansion..."));
        assert.ok(texts.includes("Within 3 Å"));
        assert.ok(texts.includes("Within 5 Å"));
        assert.ok(texts.includes("Within 8 Å"));

        findNodeByText(root, "Group")!.dispatch("click");
        assert.deepStrictEqual(actions.at(-1), {
            action: "expand_selection",
            target,
            details: { level: "group" },
        });
        assert.deepStrictEqual(notifications.at(-1), {
            event: "interaction_context_action",
            action: "expand_selection",
            context: target,
            level: "group",
        });

        menu.open(target, 10, 20, selection);
        root = (menu as any).root as FakeElement;
        findNodeByText(root, "Within 5 Å")!.dispatch("click");
        assert.deepStrictEqual(actions.at(-1), {
            action: "expand_selection",
            target,
            details: { level: "spatial", distance_angstroms: 5 },
        });
        assert.deepStrictEqual(notifications.at(-1), {
            event: "interaction_context_action",
            action: "expand_selection",
            context: target,
            level: "spatial",
            distance_angstroms: 5,
        });

        menu.open({ event: "interaction_context_menu", kind: "empty" }, 10, 20, selection);
        root = (menu as any).root as FakeElement;
        texts = collectTexts(root);
        assert.ok(texts.includes("Expand selection to..."));
        assert.ok(texts.includes("Clear Selection"));
        findNodeByText(root, "Clear Selection")!.dispatch("click");
        assert.strictEqual(actions.at(-1)?.action, "clear_selection");

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu hides legacy remove action when MolSysMT addon item is available", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        });

        const target = { event: "interaction_context_menu", kind: "structure" as const, atom_indices: [0, 1], group_name: "ALA", chain_name: "A" };
        menu.open(
            target,
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "element",
                element_level: "group",
                target_level: "none",
                items: [],
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 2,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 0,
            },
            null,
            null,
            null,
            null,
            [
                {
                    addon: "molsysmt",
                    id: "remove-selected-atoms",
                    title: "MolSysMT: remove selected atoms",
                    group: "molsysmt",
                    order: 5,
                    enabled: true,
                    target_kinds: ["structure"],
                    payload: { atom_indices: [0, 1] },
                },
            ],
        );

        const root = (menu as any).root as FakeElement;
        assert.equal(findNodeByText(root, "Remove Selected Atoms"), null);
        const addonButton = findNodeByText(root, "MolSysMT: remove selected atoms");
        assert.ok(addonButton);
        addonButton!.dispatch("click");

        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "addon_context_action",
                context: target,
                addon: "molsysmt",
                addon_action_id: "remove-selected-atoms",
                addon_action_title: "MolSysMT: remove selected atoms",
                addon_action_payload: { atom_indices: [0, 1] },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders delete action for annotation targets", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "annotation" as const, atom_indices: [0, 1], tag: "notes", text: "Catalytic" };
        menu.open(target, 10, 20, null, null, null, null);

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Focus Target"));
        assert.ok(texts.includes("Delete Annotation"));

        const button = findNodeByText(root, "Delete Annotation");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "delete_annotation", target, details: { tag: "notes" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "delete_annotation",
                context: target,
                tag: "notes",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders delete action for shape targets", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "shape" as const, atom_indices: [0, 1], tag: "pocket-shape", shape_name: "Pocket Surface" };
        menu.open(target, 10, 20, null, null, null, null);

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Focus Target"));
        assert.ok(texts.includes("Delete Shape"));

        const button = findNodeByText(root, "Delete Shape");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "delete_shape", target, details: { tag: "pocket-shape" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "delete_shape",
                context: target,
                tag: "pocket-shape",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders representative-atom measurement actions for structure targets", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "structure" as const, atom_indices: [0, 1], group_name: "ALA", chain_name: "A" };
        menu.open(target, 10, 20, null, null, null, null);

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Distance"));
        assert.ok(texts.includes("Distance (Representative Atom)"));
        assert.ok(texts.includes("Angle (Representative Atom)"));
        assert.ok(texts.includes("Dihedral (Representative Atom)"));

        const button = findNodeByText(root, "Distance (Representative Atom)");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "distance", target, details: { endpoint_policy: "representative_atom" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "distance",
                context: target,
                endpoint_policy: "representative_atom",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders delete action for measurement targets", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "measurement" as const, atom_indices: [0, 1], tag: "measurement_1", measurement_name: "Distance" };
        menu.open(target, 10, 20, null, null, null, null);

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Focus Target"));
        assert.ok(texts.includes("Hide Measurement"));
        assert.ok(texts.includes("Delete Measurement"));

        const hideButton = findNodeByText(root, "Hide Measurement");
        assert.ok(hideButton);
        hideButton!.dispatch("click");

        menu.open(target, 10, 20, null, null, null, null);
        const refreshedRoot = (menu as any).root as FakeElement;
        const button = findNodeByText(refreshedRoot, "Delete Measurement");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "hide_measurement", target, details: { tag: "measurement_1" } },
            { action: "delete_measurement", target, details: { tag: "measurement_1" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "hide_measurement",
                context: target,
                tag: "measurement_1",
            },
            {
                event: "interaction_context_action",
                action: "delete_measurement",
                context: target,
                tag: "measurement_1",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders saved selections and emits activate_selection", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "empty" as const };
        menu.open(target, 10, 20, null, null, [{ tag: "picked", atom_count: 10 }]);

        const root = (menu as any).root as FakeElement;
        const button = findNodeByText(root, "picked · 10 atoms");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "activate_selection", target, details: { tag: "picked" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "activate_selection",
                context: target,
                tag: "picked",
            },
        ]);
        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders relevant regions and emits focus_region", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "structure" as const, atom_indices: [3, 4, 5] };
        menu.open(
            target,
            10,
            20,
            null,
            null,
            null,
            [
                { tag: "siteA", atom_indices: [4, 5, 6], atom_count: 3, hidden: false },
                { tag: "siteB", atom_indices: [10, 11], atom_count: 2, hidden: true },
            ],
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Regions"));
        assert.ok(texts.includes("siteA · 3 atoms"));
        assert.ok(texts.includes("siteB · 2 atoms · hidden"));

        const button = findNodeByText(root, "siteA · 3 atoms");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "focus_region", target, details: { tag: "siteA" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "focus_region",
                context: target,
                tag: "siteA",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders add-on actions and emits addon_context_action", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        const target = { event: "interaction_context_menu", kind: "structure" as const, atom_indices: [3, 4, 5] };
        menu.open(
            target,
            10,
            20,
            null,
            null,
            null,
            null,
            [
                {
                    addon: "topomt-template",
                    id: "focus-pocket",
                    title: "Focus Pocket",
                    target_kinds: ["structure", "shape"],
                },
            ],
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Add-ons"));
        assert.ok(texts.includes("Focus Pocket · topomt-template"));

        const button = findNodeByText(root, "Focus Pocket · topomt-template");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(actions, [
            { action: "addon_context_action", target, details: { tag: "focus-pocket" } },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "addon_context_action",
                context: target,
                addon: "topomt-template",
                addon_action_id: "focus-pocket",
                addon_action_title: "Focus Pocket",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu renders dynamic add-on items and emits addon_context_action", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        });

        const target = { event: "interaction_context_menu", kind: "shape" as const, tag: "dfnd-face" };
        menu.open(
            target,
            10,
            20,
            null,
            null,
            null,
            null,
            null,
            [
                {
                    addon: "topomt",
                    id: "inspect-simplex",
                    title: "Inspect simplex",
                    group: "Selection",
                    order: 1,
                    target_kinds: ["shape"],
                    payload: { kind: "face", face_id: 7 },
                },
            ],
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("topomt"));
        assert.ok(texts.includes("Selection"));
        assert.ok(texts.includes("Inspect simplex"));

        const button = findNodeByText(root, "Inspect simplex");
        assert.ok(button);
        button!.dispatch("click");

        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "addon_context_action",
                context: target,
                addon: "topomt",
                addon_action_id: "inspect-simplex",
                addon_action_title: "Inspect simplex",
                addon_action_payload: { kind: "face", face_id: 7 },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu opens inline label composer before add-label action", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "element",
                element_level: "group",
                target_level: "none",
                items: [],
                atom_indices: [0, 1, 2],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 3,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 0,
            },
        );

        const root = (menu as any).root as FakeElement;
        const button = findNodeByText(root, "Add Label from Selection");
        assert.ok(button);
        button!.dispatch("click");

        const input = findNodeByTag(root, "input");
        assert.ok(input);
        input!.value = "Catalytic group";
        const confirm = findNodeByText(root, "Create Label");
        assert.ok(confirm);
        confirm!.dispatch("click");

        assert.deepStrictEqual(actions, [
            {
                action: "add_label_from_selection",
                target: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
                details: { text: "Catalytic group", label_style: { color: "#4080e0", size_em: 1 } },
            },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "add_label_from_selection",
                context: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
                text: "Catalytic group",
                label_style: { color: "#4080e0", size_em: 1 },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu opens inline selection composer before save-selection action", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any; details?: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target, details) => {
            actions.push({ action, target, details });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "element",
                element_level: "group",
                target_level: "none",
                items: [],
                atom_indices: [0, 1, 2],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 3,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 0,
            },
        );

        const root = (menu as any).root as FakeElement;
        const button = findNodeByText(root, "Save Selection");
        assert.ok(button);
        button!.dispatch("click");

        const input = findNodeByTag(root, "input");
        assert.ok(input);
        input!.value = "picked";
        input!.dispatch("keydown", { key: "Enter", preventDefault() {} });

        assert.deepStrictEqual(actions, [
            {
                action: "save_selection",
                target: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
                details: { tag: "picked" },
            },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "save_selection",
                context: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
                tag: "picked",
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu keeps add-label local until inline text is confirmed", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any }> = [];
        const notifications: any[] = [];
        const menu = new ViewerContextMenu(host, (msg) => {
            notifications.push(msg);
        }, (action, target) => {
            actions.push({ action, target });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "element",
                element_level: "group",
                target_level: "none",
                items: [],
                atom_indices: [0, 1, 2],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 3,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 0,
            },
        );

        const root = (menu as any).root as FakeElement;
        const button = findNodeByText(root, "Add Label from Selection");
        assert.ok(button);
        button!.dispatch("click");

        const confirm = findNodeByText(root, "Create Label");
        assert.ok(confirm);
        confirm!.dispatch("click");

        assert.deepStrictEqual(actions, []);
        assert.deepStrictEqual(notifications, []);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu exposes reproducible-selection actions with the right guard", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any }> = [];
        const menu = new ViewerContextMenu(host, undefined, (action, target) => {
            actions.push({ action, target });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "mixed",
                element_level: "group",
                target_level: "mixed",
                items: [],
                atom_indices: [0, 1, 2],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 3,
                count_groups: 1,
                count_shapes: 0,
                count_annotations: 1,
            },
        );

        let root = (menu as any).root as FakeElement;
        assert.ok(collectTexts(root).includes("Create Region from Selection"));
        assert.ok(collectTexts(root).includes("Add Label from Selection"));

        // Clicking "Create Region from Selection" opens the region composer inline
        const regionButton = findNodeByText(root, "Create Region from Selection");
        assert.ok(regionButton);
        regionButton!.dispatch("click");

        // Composer is now shown — submit with empty tag (tag is optional)
        root = (menu as any).root as FakeElement;
        assert.ok(collectTexts(root).includes("New Region from Selection"));
        const submitBtn = findNodeByText(root, "Create Region");
        assert.ok(submitBtn);
        submitBtn!.dispatch("click");

        menu.open(
            { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            10,
            20,
            {
                event: "interaction_active_selection_changed",
                source_kind: "element",
                element_level: "group",
                target_level: "none",
                items: [],
                atom_indices: [0, 1, 2, 3],
                group_indices: [0, 1],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                count_atoms: 4,
                count_groups: 2,
                count_shapes: 0,
                count_annotations: 0,
            },
        );

        root = (menu as any).root as FakeElement;
        assert.ok(collectTexts(root).includes("Create Region from Selection"));
        assert.ok(collectTexts(root).includes("Add Label from Selection"));

        assert.deepStrictEqual(actions, [
            {
                action: "create_region_from_selection",
                target: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});

test("ViewerContextMenu no longer exposes persist-last-measurement when recent measurement exists", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const menu = new ViewerContextMenu(host, undefined, () => {});

        menu.open(
            { event: "interaction_context_menu", kind: "empty" },
            10,
            20,
            null,
            { action: "distance", picked_count: 2 },
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(!texts.includes("Last measurement: distance (2)"));
        assert.ok(!texts.includes("Persist Last Measurement"));

        menu.dispose();
    } finally {
        restore();
    }
});
