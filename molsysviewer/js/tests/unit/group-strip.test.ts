import assert from "node:assert";
import test from "node:test";

import { GroupStrip } from "../../src/ui/group-strip";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
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

function findBadgeTexts(root: FakeElement): string[] {
    const out: string[] = [];
    const walk = (node: FakeElement) => {
        const text = node.textContent.trim();
        if (text === "L" || text.endsWith("L")) out.push(text);
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function findFirstBadge(root: FakeElement): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        const text = node.textContent.trim();
        if (text === "L" || text.endsWith("L")) {
            out = node;
            return;
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

test("GroupStrip displays and clears annotation overlay badges", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const strip = new GroupStrip(host, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                chain_name: "A",
            },
        ];
        (strip as any).structure = {};
        (strip as any).render();

        strip.addLabelOverlay({
            op: "add_label",
            tag: "notes",
            options: { text: "Catalytic", atom_indices: [0, 1], tag: "notes" },
        });

        let badges = findBadgeTexts((strip as any).root);
        assert.ok(badges.some((text) => text.includes("L")));

        strip.clearAnnotationOverlaysByTag("notes");
        badges = findBadgeTexts((strip as any).root);
        assert.strictEqual(badges.length, 0);

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip routes badge context menu to annotation target", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const annotationTargets: any[] = [];
        const strip = new GroupStrip(host, () => {}, () => {}, () => {}, () => {}, (target) => {
            annotationTargets.push(target);
        });
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                chain_name: "A",
            },
        ];
        (strip as any).structure = {};
        (strip as any).render();

        strip.addLabelOverlay({
            op: "add_label",
            tag: "notes",
            options: { text: "Catalytic", atom_indices: [0, 1], tag: "notes" },
        });

        const badge = findFirstBadge((strip as any).root);
        assert.ok(badge);

        let prevented = false;
        let stopped = false;
        badge.dispatch("contextmenu", {
            pageX: 12,
            pageY: 34,
            preventDefault() { prevented = true; },
            stopPropagation() { stopped = true; },
        });

        assert.deepStrictEqual(annotationTargets, [
            {
                event: "interaction_context_menu",
                kind: "annotation",
                atom_indices: [0, 1],
                tag: "notes",
                text: "Catalytic",
            },
        ]);
        assert.strictEqual(prevented, true);
        assert.strictEqual(stopped, true);

        strip.dispose();
    } finally {
        restore();
    }
});
