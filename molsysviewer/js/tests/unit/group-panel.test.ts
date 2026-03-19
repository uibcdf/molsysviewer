import assert from "node:assert";
import test from "node:test";

import { GroupPanel } from "../../src/ui/group-panel";

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

function findFirstByAttribute(root: FakeElement, attributeName: string): FakeElement | null {
    let out: FakeElement | null = null;
    const walk = (node: FakeElement) => {
        if (out) return;
        if (node.getAttribute(attributeName) !== undefined) {
            out = node;
            return;
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function findFirstGroupButton(root: FakeElement): FakeElement | null {
    return findFirstByAttribute(root, "data-molsysviewer-group-item");
}

test("GroupPanel creates one GroupStrip per chain", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [0, 0, 1, 1, 1, 1],
                    molsys_molecule_name: ["Cap", "Cap", "Peptide", "Peptide", "Peptide", "Peptide"],
                    molsys_component_id: [0, 0, 1, 1, 2, 2],
                    molsys_component_name: ["Cap", "Cap", "Protein", "Protein", "Tail", "Tail"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2, 4, 6] },
                chainAtomSegments: { index: [0, 0, 1, 1, 1, 1] },
                atoms: { label_comp_id: { value: (i: number) => i < 2 ? 'ACE' : i < 4 ? 'ALA' : 'NME' } },
                residues: { auth_seq_id: { value: (i: number) => i + 1 } },
                chains: {
                    label_asym_id: { value: (i: number) => i === 0 ? 'A' : 'B' },
                    label_entity_id: { value: (i: number) => String(i) },
                },
                index: { getEntityFromChain: (i: number) => i },
            },
        }}] } as any;
        panel.setStructure(structure);
        const root = host.children[0];
        const shell = root.children[0];
        const title = findFirstByAttribute(root, "data-molsysviewer-group-panel-title");
        const body = findFirstByAttribute(root, "data-molsysviewer-group-panel-body");
        const toggle = root.children[1];
        const stripRoots = body?.children.filter((child) => child.getAttribute?.('data-molsysviewer-group-strip') === 'true') ?? [];
        assert.strictEqual(stripRoots.length, 2);
        assert.ok(shell);
        assert.ok(title);
        assert.strictEqual(title?.textContent, "Navigate");
        assert.strictEqual(root.style.display, 'flex');
        assert.strictEqual(toggle.textContent, '>');
        assert.strictEqual(root.style.transform, 'translateX(-240px)');
        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel preserves collapse state when strips are recreated", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [1, 1, 1, 1],
                    molsys_molecule_name: ["Peptide", "Peptide", "Peptide", "Peptide"],
                    molsys_component_id: [2, 2, 2, 2],
                    molsys_component_name: ["Protein", "Protein", "Protein", "Protein"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2, 4] },
                chainAtomSegments: { index: [0, 0, 0, 0] },
                atoms: { label_comp_id: { value: (_i: number) => "ALA" } },
                residues: { auth_seq_id: { value: (i: number) => i + 1 } },
                chains: {
                    label_asym_id: { value: (_i: number) => "A" },
                    label_entity_id: { value: (_i: number) => "0" },
                },
                index: { getEntityFromChain: (_i: number) => 0 },
            },
        }}] } as any;

        panel.setStructure(structure);
        const root = host.children[0];
        const moleculeCaption = findFirstByAttribute(root, "data-molsysviewer-group-strip-molecule-caption");
        assert.ok(moleculeCaption);
        moleculeCaption.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(findFirstGroupButton(root), null);

        panel.setStructure(undefined);
        panel.setStructure(structure);

        const remountedRoot = host.children[0];
        assert.strictEqual(findFirstGroupButton(remountedRoot), null);

        panel.dispose();
    } finally {
        restore();
    }
});
