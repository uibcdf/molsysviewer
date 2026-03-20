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

function findFirstGroupButton(root: FakeElement): FakeElement | null {
    return findFirstByAttribute(root, "data-molsysviewer-group-item");
}

function collectByAttribute(root: FakeElement, attributeName: string, value?: string): FakeElement[] {
    const out: FakeElement[] = [];
    const walk = (node: FakeElement) => {
        const attr = node.getAttribute(attributeName);
        if (attr !== undefined && (value === undefined || attr === value)) {
            out.push(node);
        }
        for (const child of node.children) walk(child);
    };
    walk(root);
    return out;
}

function firstText(node: FakeElement | null | undefined): string {
    if (!node) return "";
    if (node.textContent) return node.textContent;
    for (const child of node.children) {
        const text = firstText(child);
        if (text) return text;
    }
    return "";
}

test("GroupPanel creates one GroupStrip per chain", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
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
        const navGroup = findFirstByAttribute(root, "data-molsysviewer-panel-nav-group", "true");
        const navCurrent = findFirstByAttribute(root, "data-molsysviewer-panel-nav-current", "navigate");
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "workbench");
        const body = findFirstByAttribute(root, "data-molsysviewer-group-panel-body");
        const toggle = root.children[1];
        const stripRoots = collectByAttribute(root, 'data-molsysviewer-group-strip', 'true');
        assert.strictEqual(stripRoots.length, 2);
        assert.ok(shell);
        assert.ok(title);
        assert.ok(navGroup);
        assert.ok(navCurrent);
        assert.ok(navButton);
        assert.strictEqual(navButton?.textContent, "Workbench");
        assert.strictEqual(title?.textContent, "Navigate");
        assert.strictEqual(root.style.display, 'flex');
        assert.strictEqual(toggle.textContent, '>');
        assert.strictEqual(root.style.transform, 'translateX(-240px)');
        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel renders active, saved, and region summaries", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [0, 0],
                    molsys_molecule_name: ["Peptide", "Peptide"],
                    molsys_component_id: [0, 0],
                    molsys_component_name: ["Protein", "Protein"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2] },
                chainAtomSegments: { index: [0, 0] },
                atoms: { label_comp_id: { value: (_i: number) => 'ALA' } },
                residues: { auth_seq_id: { value: (i: number) => i + 1 } },
                chains: {
                    label_asym_id: { value: (_i: number) => 'A' },
                    label_entity_id: { value: (_i: number) => '0' },
                },
                index: { getEntityFromChain: (_i: number) => 0 },
            },
        }}] } as any;
        panel.setStructure(structure);
        panel.updateSelection({
            event: "interaction_active_selection_changed",
            source_kind: "selection",
            target_level: "group",
            element_level: "atom",
            items: [],
            atom_indices: [0, 1],
            group_indices: [0],
            component_indices: [0],
            chain_indices: [0],
            molecule_indices: [0],
            entity_indices: [0],
            count_atoms: 2,
            count_groups: 1,
            count_shapes: 0,
            count_annotations: 0,
        });
        panel.setSavedSelections([{ tag: "site_a", atom_count: 2 }]);
        panel.setRegions([{ tag: "binding", atom_count: 2, hidden: true }]);

        const root = host.children[0];
        const activeSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "active");
        const savedSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "saved");
        const regionsSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "regions");
        const summaryItems = collectByAttribute(root, "data-molsysviewer-group-panel-summary-item", "true").map((node) => firstText(node));

        assert.ok(activeSection);
        assert.ok(savedSection);
        assert.ok(regionsSection);
        assert.ok(summaryItems.includes("2 atoms"));
        assert.ok(summaryItems.includes("site_a"));
        assert.ok(summaryItems.includes("binding"));

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel preserves collapse state when strips are recreated", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
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

test("GroupPanel saved and region summaries trigger their primary actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let restoredTag: string | null = null;
        let focusedRegion: string | null = null;
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (tag) => { restoredTag = tag; },
            (tag) => { focusedRegion = tag; },
        );
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [0, 0],
                    molsys_molecule_name: ["Peptide", "Peptide"],
                    molsys_component_id: [0, 0],
                    molsys_component_name: ["Protein", "Protein"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2] },
                chainAtomSegments: { index: [0, 0] },
                atoms: { label_comp_id: { value: (_i: number) => 'ALA' } },
                residues: { auth_seq_id: { value: (i: number) => i + 1 } },
                chains: {
                    label_asym_id: { value: (_i: number) => 'A' },
                    label_entity_id: { value: (_i: number) => '0' },
                },
                index: { getEntityFromChain: (_i: number) => 0 },
            },
        }}] } as any;
        panel.setStructure(structure);
        panel.setSavedSelections([{ tag: "site_a", atom_count: 2 }]);
        panel.setRegions([{ tag: "binding", atom_count: 2, hidden: false }]);

        const root = host.children[0];
        const summaryItems = collectByAttribute(root, "data-molsysviewer-group-panel-summary-item", "true");
        const savedItem = summaryItems.find((node) => firstText(node) === "site_a");
        const regionItem = summaryItems.find((node) => firstText(node) === "binding");

        assert.ok(savedItem);
        assert.ok(regionItem);
        savedItem?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        regionItem?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(restoredTag, "site_a");
        assert.strictEqual(focusedRegion, "binding");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel exposes shared expanded state API", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let lastExpanded: boolean | null = null;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [0, 0],
                    molsys_molecule_name: ["Peptide", "Peptide"],
                    molsys_component_id: [0, 0],
                    molsys_component_name: ["Protein", "Protein"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2] },
                chainAtomSegments: { index: [0, 0] },
                atoms: { label_comp_id: { value: (_i: number) => "ALA" } },
                residues: { auth_seq_id: { value: (i: number) => i + 1 } },
                chains: {
                    label_asym_id: { value: (_i: number) => "A" },
                    label_entity_id: { value: (_i: number) => "0" },
                },
                index: { getEntityFromChain: (_i: number) => 0 },
            },
        }}] } as any;
        panel.setOnExpandedChange((expanded) => { lastExpanded = expanded; });
        panel.setStructure(structure);
        panel.setExpanded(true);

        const root = host.children[0];
        assert.strictEqual(panel.isExpanded(), true);
        assert.strictEqual(lastExpanded, true);
        assert.strictEqual(root.style.transform, "translateX(0)");

        panel.setExpanded(false);
        assert.strictEqual(panel.isExpanded(), false);
        assert.strictEqual(lastExpanded, false);
        assert.strictEqual(root.style.transform, "translateX(-240px)");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel exposes workspace selector when multiple workspaces exist", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let selectedWorkspace: string | null = null;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        panel.setWorkspaces(
            [
                { id: "core", title: "Core" },
                { id: "topomt", title: "TopoMT" },
            ],
            "core",
            (workspaceId) => { selectedWorkspace = workspaceId; },
        );
        panel.setStructure({ units: [] } as any);

        const root = host.children[0];
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current", "core");
        const button = findFirstByAttribute(root, "data-molsysviewer-panel-workspace", "topomt");
        assert.ok(current);
        assert.ok(button);

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel supports custom navigation labels", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});

        let navigated = 0;
        panel.setOnNavigateToWorkbench(() => {
            navigated += 1;
        }, "Core");

        const root = host.children[0];
        const button = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "core");
        assert.ok(button);
        assert.strictEqual(button?.textContent, "Core");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(navigated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel exposes panel stack in the shared header", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        let selected = "";

        panel.setPanelStack(
            [
                { id: "navigate", title: "Navigate", active: true },
                { id: "workbench", title: "Workbench" },
            ],
            (panelId) => { selected = panelId; },
        );

        const root = host.children[0];
        const stack = findFirstByAttribute(root, "data-molsysviewer-panel-stack", "true");
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-stack-current", "navigate");
        const option = findFirstByAttribute(root, "data-molsysviewer-panel-stack-option", "workbench");

        assert.ok(stack);
        assert.ok(current);
        assert.ok(option);
        option?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selected, "workbench");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel header nav button triggers navigate-to-workbench callback", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let navigated = 0;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        panel.setOnNavigateToWorkbench(() => { navigated += 1; });
        const structure = { units: [{ kind: 0, model: {
            sourceData: {
                kind: "mol-viewer:molsysmt",
                data: {
                    molsys_molecule_id: [0, 0],
                    molsys_molecule_name: ["Peptide", "Peptide"],
                    molsys_component_id: [0, 0],
                    molsys_component_name: ["Protein", "Protein"],
                },
            },
            atomicHierarchy: {
                residueAtomSegments: { offsets: [0, 2] },
                chainAtomSegments: { index: [0, 0] },
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
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "workbench");
        assert.ok(navButton);

        navButton?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(navigated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});
