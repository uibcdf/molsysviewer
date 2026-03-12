import assert from "node:assert";
import test from "node:test";

import { ViewerContextMenu } from "../../src/ui/context-menu";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
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
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    const previousWindow = (globalThis as any).window;
    (globalThis as any).document = {
        createElement: () => new FakeElement(),
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
        assert.ok(texts.includes("Active selection: mixed (0 items)"));
        assert.ok(texts.includes("Focus Selection"));
        assert.ok(texts.includes("Clear Selection"));

        const focusButton = findNodeByText(root, "Focus Selection");
        assert.ok(focusButton);
        focusButton!.dispatch("click");

        assert.deepStrictEqual(actions, [{
            action: "focus_selection",
            target: { event: "interaction_context_menu", kind: "annotation", atom_indices: [0, 1], tag: "notes", text: "Catalytic" },
        }]);

        menu.dispose();
    } finally {
        restore();
    }
});
