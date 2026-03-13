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

test("GroupPanel creates one GroupStrip per chain", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, model: {
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2, 4, 6] },
                chainAtomSegments: { index: [0,0,1,1,1,1] },
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
        const stripRoots = host.children[0].children.filter((child) => child.getAttribute?.('data-molsysviewer-group-strip') === 'true');
        assert.strictEqual(stripRoots.length, 2);
        assert.strictEqual(host.children[0].style.display, 'block');
        panel.dispose();
    } finally {
        restore();
    }
});
