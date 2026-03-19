import assert from "node:assert";
import test from "node:test";

import { WorkbenchPanel } from "../../src/ui/workbench-panel";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
    private attributes = new Map<string, string>();
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
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }

    addEventListener(name: string, handler: (event?: any) => void) {
        const handlers = this.listeners.get(name) ?? [];
        handlers.push(handler);
        this.listeners.set(name, handlers);
    }

    dispatch(name: string, event?: any) {
        for (const handler of this.listeners.get(name) ?? []) {
            handler(event);
        }
    }
}

function installFakeDom() {
    const previousDocument = (globalThis as any).document;
    (globalThis as any).document = {
        createElement: () => new FakeElement(),
    };
    return () => {
        (globalThis as any).document = previousDocument;
    };
}

function findFirstByAttribute(root: FakeElement, attributeName: string, value?: string): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        const attr = node.getAttribute(attributeName);
        if (attr !== undefined && (value === undefined || attr === value)) {
            out = node;
            return;
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

test("WorkbenchPanel renders titled shell and empty sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);

        const root = host.children[0];
        const title = findFirstByAttribute(root, "data-molsysviewer-workbench-panel-title");
        const annotationsEmpty = findFirstByAttribute(root, "data-molsysviewer-workbench-empty", "annotations");
        const sceneEmpty = findFirstByAttribute(root, "data-molsysviewer-workbench-empty", "scene");

        assert.ok(root);
        assert.ok(title);
        assert.strictEqual(title?.textContent, "Workbench");
        assert.strictEqual(root.style.display, "flex");
        assert.strictEqual(root.style.transform, "translateX(240px)");
        assert.strictEqual(annotationsEmpty?.textContent, "No annotations yet.");
        assert.strictEqual(sceneEmpty?.textContent, "No scene style selected.");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel populates sections and scene summary", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);

        panel.setVisible(true);
        panel.setAnnotations([{ key: "notes", title: "Picked label", subtitle: "group 12", active: true, context: true }]);
        panel.setMeasurements([{ title: "Distance", subtitle: "3.2 A" }]);
        panel.setShapes([{ title: "Pocket", subtitle: "surface", hidden: true }]);
        panel.setScene({ styleTag: "polymer-and-ligand", preset: "atomic-detail" });

        const root = host.children[0];
        const items = [];
        const collect = (node: FakeElement) => {
            if (node.getAttribute("data-molsysviewer-workbench-item") === "true") items.push(node);
            for (const child of node.children) collect(child);
        };
        collect(root);

        assert.strictEqual(items.length, 5);
        assert.strictEqual(items[0].children[0]?.textContent, "Picked label");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-workbench-item-active"), "true");
        assert.strictEqual(items[0].getAttribute("data-molsysviewer-workbench-item-context"), "true");
        assert.strictEqual(items[1].children[0]?.textContent, "Distance");
        assert.strictEqual(items[2].children[0]?.textContent, "Pocket");
        assert.strictEqual(items[3].children[0]?.textContent, "Style: polymer-and-ligand");
        assert.strictEqual(items[4].children[0]?.textContent, "Preset: atomic-detail");

        panel.dispose();
    } finally {
        restore();
    }
});

test("WorkbenchPanel rows trigger activation when provided", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new WorkbenchPanel(host);
        let activated = 0;

        panel.setVisible(true);
        panel.setAnnotations([{ title: "Picked label", subtitle: "group 12", onActivate: () => { activated += 1; } }]);

        const root = host.children[0];
        const row = findFirstByAttribute(root, "data-molsysviewer-workbench-item");
        assert.ok(row);
        row?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(activated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});
