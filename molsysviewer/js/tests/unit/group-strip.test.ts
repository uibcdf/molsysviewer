import assert from "node:assert";
import test from "node:test";

import { GroupStrip } from "../../src/ui/group-strip";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
    public readonly attributes: Record<string, string> = {};
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
    setAttribute(name: string, value: string) {
        this.attributes[name] = value;
    }

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

function collectTexts(root: FakeElement): string[] {
    const out: string[] = [];
    const walk = (node: FakeElement) => {
        const text = node.textContent.trim();
        if (text) out.push(text);
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function findFirstGroupButton(root: FakeElement): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        if (node.attributes["data-molsysviewer-group-item"] === "true") {
            out = node;
            return;
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function findFirstByAttribute(root: FakeElement, attributeName: string): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        if (node.attributes[attributeName] !== undefined) {
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
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
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
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, (target) => {
            annotationTargets.push(target);
        });
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
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

test("GroupStrip badge click selects annotation and shift-click is forwarded", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const selected: any[] = [];
        const strip = new GroupStrip(host, "A", (items, op) => {
            selected.push({ items, op });
        }, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
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
        badge.dispatch("click", { shiftKey: true, preventDefault() {}, stopPropagation() {} });

        assert.deepStrictEqual(selected, [{
            items: [{
                source_kind: "annotation",
                annotation_kind: "label",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                chain_indices: [0],
                molecule_indices: [],
                entity_indices: [0],
                tag: "notes",
                text: "Catalytic",
            }],
            op: "add",
        }]);

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip can reflect mixed element and annotation selection at once", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
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

        strip.updateSelection({
            event: "interaction_active_selection_changed",
            source_kind: "mixed",
            element_level: "group",
            target_level: "mixed",
            items: [
                {
                    source_kind: "element",
                    element_level: "group",
                    atom_indices: [0, 1],
                    group_indices: [0],
                    component_indices: [],
                    chain_indices: [0],
                    molecule_indices: [],
                    entity_indices: [0],
                    group_name: "ALA 1",
                    chain_name: "A",
                },
                {
                    source_kind: "annotation",
                    annotation_kind: "label",
                    atom_indices: [0, 1],
                    group_indices: [0],
                    component_indices: [],
                    chain_indices: [0],
                    molecule_indices: [],
                    entity_indices: [0],
                    tag: "notes",
                    text: "Catalytic",
                },
            ],
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
        } as any);

        const button = findFirstGroupButton((strip as any).root);
        assert.ok(button);
        const badge = findFirstBadge(button);
        assert.ok((button as FakeElement).style.background.includes("0.18"));
        assert.ok(badge);
        assert.strictEqual((badge as FakeElement).style.color, "#fde68a");

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip routes group context menu to element target", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const targets: any[] = [];
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, (item, pageX, pageY) => {
            targets.push({ item, pageX, pageY });
        }, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                chain_name: "A",
                entity_name: "1",
            },
        ];
        (strip as any).structure = {};
        (strip as any).render();

        const button = findFirstGroupButton((strip as any).root);
        assert.ok(button);
        let prevented = false;
        let stopped = false;
        (button as FakeElement).dispatch("contextmenu", {
            pageX: 20,
            pageY: 40,
            preventDefault() { prevented = true; },
            stopPropagation() { stopped = true; },
        });

        assert.deepStrictEqual(targets, [{
            item: {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                chain_name: "A",
                entity_name: "1",
            },
            pageX: 20,
            pageY: 40,
        }]);
        assert.strictEqual(prevented, true);
        assert.strictEqual(stopped, true);

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip renders compact visible molecule and component captions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [2],
                molecule_indices: [1],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                component_name: "Protein",
                molecule_name: "Peptide",
                chain_name: "A",
            },
        ];
        (strip as any).structure = {};
        (strip as any).render();

        const texts = collectTexts((strip as any).root);
        assert.ok(texts.some((text) => text.includes("M Peptide")));
        assert.ok(texts.some((text) => text.includes("C Protein")));

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip can collapse and expand molecule and component sections", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [2],
                molecule_indices: [1],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                component_name: "Protein",
                molecule_name: "Peptide",
                chain_name: "A",
            },
        ];
        (strip as any).structure = {};
        (strip as any).render();

        assert.ok(findFirstGroupButton((strip as any).root));

        const componentCaption = findFirstByAttribute((strip as any).root, "data-molsysviewer-group-strip-component-caption");
        assert.ok(componentCaption);
        (componentCaption as FakeElement).dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(findFirstGroupButton((strip as any).root), null);

        (componentCaption as FakeElement).dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.ok(findFirstGroupButton((strip as any).root));

        const moleculeCaption = findFirstByAttribute((strip as any).root, "data-molsysviewer-group-strip-molecule-caption");
        assert.ok(moleculeCaption);
        (moleculeCaption as FakeElement).dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(findFirstGroupButton((strip as any).root), null);

        strip.dispose();
    } finally {
        restore();
    }
});

test("GroupStrip marks structure and annotation context targets discreetly", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const strip = new GroupStrip(host, "A", () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        (strip as any).groupItems = [
            {
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1],
                group_indices: [0],
                component_indices: [],
                molecule_indices: [],
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

        strip.updateContextTarget({
            event: "interaction_context_menu",
            kind: "structure",
            atom_indices: [0, 1],
        });
        const button = findFirstGroupButton((strip as any).root);
        assert.ok(button);
        assert.ok((button as FakeElement).style.background.includes("251, 191, 36"));

        strip.updateContextTarget({
            event: "interaction_context_menu",
            kind: "annotation",
            atom_indices: [0, 1],
            tag: "notes",
            text: "Catalytic",
        });
        const badge = findFirstBadge((strip as any).root);
        assert.ok(badge);
        assert.strictEqual((badge as FakeElement).style.color, "#fcd34d");

        strip.dispose();
    } finally {
        restore();
    }
});
