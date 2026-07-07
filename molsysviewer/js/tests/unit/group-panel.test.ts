import assert from "node:assert";
import test from "node:test";

import { GroupPanel } from "../../src/ui/group-panel";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public title = "";
    public type = "";
    public disabled = false;
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
        const structure = { units: [{ kind: 0, elements: [0,1,2,3,4,5], model: {
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
        const navCurrent = findFirstByAttribute(root, "data-molsysviewer-panel-nav-current", "studio");
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "add-ons");
        const body = findFirstByAttribute(root, "data-molsysviewer-group-panel-body");
        const toggle = root.children[1];
        const stripRoots = collectByAttribute(root, 'data-molsysviewer-group-strip', 'true');
        assert.strictEqual(stripRoots.length, 2);
        assert.ok(shell);
        assert.ok(title);
        assert.ok(navGroup);
        assert.ok(navCurrent);
        assert.ok(navButton);
        assert.strictEqual(navButton?.textContent, "Add-ons");
        assert.strictEqual(title?.textContent, "Studio");
        assert.strictEqual(root.style.display, 'flex');
        assert.strictEqual(toggle.textContent, '>');
        assert.strictEqual(root.style.transform, 'translateX(-560px)');
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
        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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
        const selectionSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "selection");
        const regionsSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "regions");
        const summaryItems = collectByAttribute(root, "data-molsysviewer-group-panel-summary-item", "true").map((node) => firstText(node));

        assert.ok(selectionSection);
        assert.ok(regionsSection);
        assert.ok(summaryItems.some((txt) => txt.includes("2 atoms")));
        assert.ok(summaryItems.includes("site_a"));
        assert.ok(summaryItems.includes("binding"));

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection query composer emits apply actions and accepts current preview", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: any[] = [];
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => { actions.push({ action, details }); },
        );

        const root = host.children[0];
        const input = findFirstByAttribute(root, "data-molsysviewer-selection-query-input") as any;
        const union = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "add");
        const invert = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "invert");
        assert.ok(input);
        assert.ok(union);
        assert.ok(invert);

        input.value = "group_index==1";
        input.dispatch("input");
        union?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        assert.deepStrictEqual(actions.at(-1), {
            action: "apply_selection_query",
            details: {
                expression: "group_index==1",
                syntax: "MolSysMT",
                op: "add",
            },
        });

        invert?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(actions.at(-1).details.op, "invert");

        (panel as any).selectionQueryPreviewRequest = 3;
        panel.updateSelectionQueryPreview({ request_id: 2, ok: true, count: 99 });
        panel.updateSelectionQueryPreview({ request_id: 3, ok: true, count: 2 });
        const preview = findFirstByAttribute(root, "data-molsysviewer-selection-query-preview");
        assert.strictEqual(firstText(preview), "✓ 2 atoms");
        assert.strictEqual(preview?.getAttribute("data-molsysviewer-selection-query-preview-status"), "ok");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection query preview shows pending and error states", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
        );

        const root = host.children[0];
        const input = findFirstByAttribute(root, "data-molsysviewer-selection-query-input") as any;
        const select = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "replace") as any;
        assert.strictEqual(select.disabled, true);

        input.value = "bad query";
        input.dispatch("input");

        let preview = findFirstByAttribute(root, "data-molsysviewer-selection-query-preview");
        assert.strictEqual(firstText(preview), "Checking query...");
        assert.strictEqual(preview?.getAttribute("data-molsysviewer-selection-query-preview-status"), "pending");

        (panel as any).selectionQueryPreviewRequest = 1;
        panel.updateSelectionQueryPreview({ request_id: 1, ok: false, error_message: "invalid syntax" });
        preview = findFirstByAttribute(root, "data-molsysviewer-selection-query-preview");
        assert.strictEqual(firstText(preview), "✗ invalid syntax");
        assert.strictEqual(preview?.getAttribute("data-molsysviewer-selection-query-preview-status"), "error");

        const enabledSelect = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "replace") as any;
        assert.strictEqual(enabledSelect.disabled, false);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection query preview uses a dedicated query-only action", async () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: any[] = [];
        new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => { actions.push({ action, details }); },
        );

        const root = host.children[0];
        const input = findFirstByAttribute(root, "data-molsysviewer-selection-query-input") as any;
        assert.ok(input);
        input.value = "group_index==1";
        input.dispatch("input");

        await new Promise((resolve) => setTimeout(resolve, 270));

        assert.deepStrictEqual(actions.at(-1), {
            action: "selection_query_preview_request",
            details: {
                request_id: 1,
                expression: "group_index==1",
                syntax: "MolSysMT",
            },
        });
    } finally {
        restore();
    }
});

test("GroupPanel selection query presets inject exact MolSysMT syntax", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: any[] = [];
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => { actions.push({ action, details }); },
        );

        const root = host.children[0];
        const water = findFirstByAttribute(root, "data-molsysviewer-selection-query-preset", "water");
        assert.ok(water);

        water?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const input = findFirstByAttribute(root, "data-molsysviewer-selection-query-input") as any;
        assert.strictEqual(input.value, 'molecule_type=="water"');
        assert.strictEqual((panel as any).selectionQuerySyntax, "MolSysMT");

        (panel as any).selectionQueryPreviewRequest = 1;
        assert.deepStrictEqual((panel as any).selectionQueryPreview, {
            request_id: 1,
            status: "pending",
        });

        const select = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "replace") as any;
        assert.strictEqual(select.disabled, false);
        select.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "apply_selection_query",
            details: {
                expression: 'molecule_type=="water"',
                syntax: "MolSysMT",
                op: "replace",
            },
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection query cheat-sheet toggles and injects examples", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
        );

        const root = host.children[0];
        const toggle = findFirstByAttribute(root, "data-molsysviewer-selection-cheatsheet-toggle", "true");
        assert.ok(toggle);
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-selection-cheatsheet"), null);

        toggle?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const cheatSheet = findFirstByAttribute(root, "data-molsysviewer-selection-cheatsheet");
        assert.ok(cheatSheet);
        const chainExample = findFirstByAttribute(root, "data-molsysviewer-selection-cheatsheet-example", "Chain");
        assert.ok(chainExample);

        chainExample?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const input = findFirstByAttribute(root, "data-molsysviewer-selection-query-input") as any;
        assert.strictEqual(input.value, 'chain_id=="A"');
        assert.strictEqual((panel as any).selectionQuerySyntax, "MolSysMT");
        assert.deepStrictEqual((panel as any).selectionQueryPreview, {
            request_id: 1,
            status: "pending",
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection expanders emit hierarchical and spatial actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: any[] = [];
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => { actions.push({ action, details }); },
        );
        panel.updateSelection({
            event: "interaction_active_selection_changed",
            source_kind: "element",
            target_level: "none",
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

        const root = host.children[0];
        const group = findFirstByAttribute(root, "data-molsysviewer-selection-expand-level", "group");
        const distance = findFirstByAttribute(root, "data-molsysviewer-selection-spatial-distance") as any;
        const spatial = findFirstByAttribute(root, "data-molsysviewer-selection-expand-spatial");
        assert.ok(group);
        assert.ok(distance);
        assert.ok(spatial);

        group.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "expand_selection",
            details: { level: "group" },
        });

        distance.value = "6.5";
        distance.dispatch("input");
        spatial.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "expand_selection",
            details: { level: "spatial", distance_angstroms: 6.5 },
        });

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
        const structure = { units: [{ kind: 0, elements: [0,1,2,3], model: {
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

test("GroupPanel renders the selection modifier legend without changing callbacks", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let selectCalls = 0;
        const panel = new GroupPanel(
            host,
            () => { selectCalls += 1; },
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
        );

        const root = host.children[0];
        const legend = findFirstByAttribute(root, "data-molsysviewer-selection-modifier-legend", "true");
        const click = findFirstByAttribute(root, "data-molsysviewer-selection-modifier-legend-item", "Click");
        const shift = findFirstByAttribute(root, "data-molsysviewer-selection-modifier-legend-item", "Shift");
        const range = findFirstByAttribute(root, "data-molsysviewer-selection-modifier-legend-item", "Shift+Alt");

        assert.ok(legend);
        assert.strictEqual(click?.children[1]?.textContent, "Replace");
        assert.strictEqual(shift?.children[1]?.textContent, "Add/toggle");
        assert.strictEqual(range?.children[1]?.textContent, "Range");
        assert.strictEqual(selectCalls, 0);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel exposes active selection undo redo buttons and scoped shortcuts", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: any[] = [];
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => { actions.push({ action, details }); },
        );

        const root = host.children[0];
        let undo = findFirstByAttribute(root, "data-molsysviewer-selection-undo", "true") as any;
        let redo = findFirstByAttribute(root, "data-molsysviewer-selection-redo", "true") as any;
        assert.ok(undo);
        assert.ok(redo);
        assert.strictEqual(undo.disabled, true);
        assert.strictEqual(redo.disabled, true);

        panel.updateSelectionHistoryState({ canUndo: true, canRedo: false });
        undo = findFirstByAttribute(root, "data-molsysviewer-selection-undo", "true") as any;
        redo = findFirstByAttribute(root, "data-molsysviewer-selection-redo", "true") as any;
        assert.strictEqual(undo.disabled, false);
        assert.strictEqual(redo.disabled, true);

        undo.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), { action: "undo_active_selection", details: undefined });

        panel.updateSelectionHistoryState({ canUndo: true, canRedo: true });
        const selectionPanel = findFirstByAttribute(root, "data-molsysviewer-selection-panel", "true");
        const keyEvent = {
            key: "y",
            ctrlKey: true,
            metaKey: false,
            shiftKey: false,
            target: selectionPanel,
            prevented: false,
            stopped: false,
            preventDefault() { this.prevented = true; },
            stopPropagation() { this.stopped = true; },
        };
        selectionPanel?.dispatch("keydown", keyEvent);
        assert.deepStrictEqual(actions.at(-1), { action: "redo_active_selection", details: undefined });
        assert.strictEqual(keyEvent.prevented, true);
        assert.strictEqual(keyEvent.stopped, true);

        const inputTarget = { tagName: "INPUT" };
        selectionPanel?.dispatch("keydown", {
            key: "z",
            ctrlKey: true,
            metaKey: false,
            shiftKey: false,
            target: inputTarget,
            preventDefault() { throw new Error("should not capture editable shortcut"); },
            stopPropagation() {},
        });
        assert.deepStrictEqual(actions.at(-1), { action: "redo_active_selection", details: undefined });

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
        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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

test("GroupPanel saved selections card actions and inline forms", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let lastAction: string | null = null;
        let lastParams: any = null;
        let restoredTag: string | null = null;

        const panel = new GroupPanel(
            host,
            () => {}, // onSelect
            () => {}, // onInteraction
            () => {}, // onFocus
            () => {}, // onHover
            () => {}, // onContext
            () => {}, // onAnnotationContext
            (tag) => { restoredTag = tag; }, // onActivateSavedSelection
            () => {}, // onFocusRegion
            (action, params) => { lastAction = action; lastParams = params; } // onAction
        );

        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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
        panel.setSavedSelections([{ tag: "site_a", atom_count: 2, element_level: "group" }]);

        const root = host.children[0];

        // 1. Activate
        const activateBtn = findFirstByAttribute(root, "data-molsysviewer-saved-selection-activate", "site_a");
        assert.ok(activateBtn);
        activateBtn?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(restoredTag, "site_a");

        // 2. Compose Union
        const unionBtn = findFirstByAttribute(root, "data-molsysviewer-saved-selection-compose-add", "site_a");
        assert.ok(unionBtn);
        unionBtn?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(lastAction, "compose_saved_selection");
        assert.deepEqual(lastParams, { tag: "site_a", op: "add" });

        // 3. Rename inline form triggering
        const renameBtn = findFirstByAttribute(root, "data-molsysviewer-saved-selection-rename", "site_a");
        assert.ok(renameBtn);
        const card = findFirstByAttribute(root, "data-molsysviewer-saved-selection-card", "site_a");
        assert.ok(card);
        const btnRow = findFirstByAttribute(card, "data-molsysviewer-saved-selection-buttons-row", "site_a");
        const inlineForm = card?.children[1] as any;
        assert.ok(btnRow);
        assert.ok(inlineForm);

        // Initially inlineForm is hidden
        assert.strictEqual(inlineForm.style.display, "none");

        // Trigger rename
        renameBtn?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(btnRow.style.display, "none");
        assert.strictEqual(inlineForm.style.display, "flex");

        // Fill and confirm rename
        const input = inlineForm.children[0] as any;
        const confirm = inlineForm.children[1] as any;
        input.value = "site_new";
        confirm?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        assert.strictEqual(lastAction, "rename_selection");
        assert.deepEqual(lastParams, { tag: "site_a", new_tag: "site_new" });

        // Form hides after confirm
        assert.strictEqual(inlineForm.style.display, "none");
        assert.strictEqual(btnRow.style.display, "flex");

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
        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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
        assert.strictEqual(root.style.transform, "translateX(-560px)");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel exposes workspace launcher when multiple workspaces exist", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        let selectedWorkspace: string | null = null;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        panel.setWorkspaces(
            [
                { id: "core", title: "Core", subtitle: "Studio + Workbench" },
                { id: "topomt", title: "TopoMT", subtitle: "2 panels · 1 section" },
                { id: "pharmacophoremt", title: "PharmacophoreMT", subtitle: "3 panels · 2 sections" },
            ],
            "core",
            (workspaceId) => { selectedWorkspace = workspaceId; },
        );
        panel.setStructure({ units: [] } as any);

        const root = host.children[0];
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current", "core");
        const currentMarker = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-marker", "true");
        const currentTitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-title", "true");
        const currentSubtitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-current-subtitle", "true");
        const launcher = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-launcher", "true");
        assert.ok(current);
        assert.ok(currentMarker);
        assert.ok(currentTitle);
        assert.ok(currentSubtitle);
        assert.ok(launcher);
        assert.strictEqual(currentMarker?.textContent, "Core workspace");
        assert.strictEqual(currentTitle?.textContent, "Core");
        assert.strictEqual(currentSubtitle?.textContent, "Studio + Workbench");
        assert.strictEqual(launcher?.getAttribute("data-molsysviewer-panel-workspace-launcher-mode"), "mosaic");

        current?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const button = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option", "topomt");
        const title = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-title", "topomt");
        const subtitle = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-subtitle", "topomt");
        const marker = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option-marker", "core");
        const other = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-option", "pharmacophoremt");
        const coreSection = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-section", "core");
        const addonSection = findFirstByAttribute(root, "data-molsysviewer-panel-workspace-section", "addons");
        assert.ok(button);
        assert.ok(other);
        assert.ok(coreSection);
        assert.ok(addonSection);
        assert.strictEqual(title?.textContent, "TopoMT");
        assert.strictEqual(subtitle?.textContent, "2 panels · 1 section");
        assert.strictEqual(marker?.textContent, "Current");
        assert.strictEqual(coreSection?.textContent, "Core");
        assert.strictEqual(addonSection?.textContent, "Add-ons");

        button?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selectedWorkspace, "topomt");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel can be force-hidden for non-core workspaces", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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
        assert.strictEqual(panel.isVisible(), true);

        panel.setRuntimeVisible(false);
        assert.strictEqual(panel.isVisible(), false);

        panel.setRuntimeVisible(null);
        assert.strictEqual(panel.isVisible(), true);

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
                { id: "navigate", title: "Studio", active: true },
                { id: "addons", title: "Add-ons" },
            ],
            (panelId) => { selected = panelId; },
        );

        const root = host.children[0];
        const stack = findFirstByAttribute(root, "data-molsysviewer-panel-stack", "true");
        const current = findFirstByAttribute(root, "data-molsysviewer-panel-stack-current", "navigate");
        const option = findFirstByAttribute(root, "data-molsysviewer-panel-stack-option", "addons");

        assert.ok(stack);
        assert.ok(current);
        assert.ok(option);
        option?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(selected, "addons");

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
        const structure = { units: [{ kind: 0, elements: [0,1], model: {
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
        const navButton = findFirstByAttribute(root, "data-molsysviewer-panel-nav", "add-ons");
        assert.ok(navButton);

        navButton?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(navigated, 1);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel mounts the residue color-scheme (palette) toggle in the System tab", () => {
    // Regression: the 🎨 palette button was gated on a section titled "Structure",
    // which the navigate-panel redesign renamed to the "System" tab — silently
    // orphaning the button. It must mount in the System tab content on construction.
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const root = host.children[0];
        const toggle = findFirstByAttribute(root, "data-molsysviewer-color-scheme-toggle", "true");
        assert.ok(toggle, "the color-scheme (palette) toggle should be mounted in the System tab");
    } finally {
        restore();
    }
});
