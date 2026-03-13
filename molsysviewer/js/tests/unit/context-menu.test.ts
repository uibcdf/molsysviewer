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
    (globalThis as any).document = {
        createElement: (tag: string) => {
            const el = new FakeElement();
            el.tagName = String(tag).toUpperCase();
            return el;
        },
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
                details: { text: "Catalytic group" },
            },
        ]);
        assert.deepStrictEqual(notifications, [
            {
                event: "interaction_context_action",
                action: "add_label_from_selection",
                context: { event: "interaction_context_menu", kind: "structure", atom_indices: [0, 1, 2] },
                text: "Catalytic group",
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

        const regionButton = findNodeByText(root, "Create Region from Selection");
        assert.ok(regionButton);
        regionButton!.dispatch("click");

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
        assert.ok(!collectTexts(root).includes("Add Label from Selection"));

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

test("ViewerContextMenu exposes persist-last-measurement when recent measurement exists", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; target: any }> = [];
        const menu = new ViewerContextMenu(host, undefined, (action, target) => {
            actions.push({ action, target });
        });

        menu.open(
            { event: "interaction_context_menu", kind: "empty" },
            10,
            20,
            null,
            { action: "distance", picked_count: 2 },
        );

        const root = (menu as any).root as FakeElement;
        const texts = collectTexts(root);
        assert.ok(texts.includes("Last measurement: distance (2)"));
        assert.ok(texts.includes("Persist Last Measurement"));

        const persistButton = findNodeByText(root, "Persist Last Measurement");
        assert.ok(persistButton);
        persistButton!.dispatch("click");

        assert.deepStrictEqual(actions, [
            {
                action: "persist_last_measurement",
                target: { event: "interaction_context_menu", kind: "empty" },
            },
        ]);

        menu.dispose();
    } finally {
        restore();
    }
});
