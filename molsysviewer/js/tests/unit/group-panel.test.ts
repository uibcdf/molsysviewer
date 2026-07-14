import assert from "node:assert";
import test from "node:test";

import { GroupPanel } from "../../src/ui/group-panel";
import type { AnnotationSummary } from "../../src/ui/panels/annotations-panel";

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
        createTextNode: (text: string) => {
            const node = new FakeElement();
            node.textContent = text;
            return node;
        },
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

        (panel as any).switchTab("selection");
        (panel as any).switchTab("regions");
        const root = host.children[0];
        const selectionSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "selection");
        const regionsSection = findFirstByAttribute(root, "data-molsysviewer-group-panel-section", "regions");
        const activeCard = findFirstByAttribute(root, "data-molsysviewer-selection-active-card", "true");
        const savedList = findFirstByAttribute(root, "data-molsysviewer-saved-selection-list", "true");
        const summaryItems = collectByAttribute(root, "data-molsysviewer-group-panel-summary-item", "true").map((node) => firstText(node));

        assert.ok(selectionSection);
        assert.ok(regionsSection);
        assert.ok(activeCard);
        assert.ok(savedList);
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

        (panel as any).switchTab("selection");
        const root = host.children[0];
        const input = findFirstByAttribute(root, "data-molsysviewer-query-input", "selection") as any;
        const union = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "add");
        assert.ok(input);
        assert.ok(union);
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "invert"),
            null,
        );

        input.value = "group_index==1";
        input.dispatch("input");
        const enabledUnion = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "add");
        assert.strictEqual((enabledUnion as any).disabled, false);
        enabledUnion?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        assert.deepStrictEqual(actions.at(-1), {
            action: "apply_selection_query",
            details: {
                expression: "group_index==1",
                syntax: "MolSysMT",
                op: "add",
            },
        });

        const check = findFirstByAttribute(root, "data-molsysviewer-query-check", "selection");
        assert.ok(check);
        check?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const previewRequest = actions.at(-1);
        assert.strictEqual(previewRequest.action, "selection_query_preview_request");
        assert.strictEqual(previewRequest.details.expression, "group_index==1");
        assert.strictEqual(previewRequest.details.syntax, "MolSysMT");
        panel.updateSelectionQueryPreview({ request_id: previewRequest.details.request_id - 1, ok: true, count: 99 });
        panel.updateSelectionQueryPreview({ request_id: previewRequest.details.request_id, ok: true, count: 2 });
        const status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(firstText(status), "✓ 2 atoms");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "ok");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel active card exposes All None Invert and Label controls", () => {
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

        (panel as any).switchTab("selection");
        const root = host.children[0];
        const all = findFirstByAttribute(root, "data-molsysviewer-selection-all", "true");
        const none = findFirstByAttribute(root, "data-molsysviewer-selection-none", "true");
        const invert = findFirstByAttribute(root, "data-molsysviewer-selection-invert", "true");
        const label = findFirstByAttribute(root, "data-molsysviewer-selection-to-label", "true");
        assert.ok(all);
        assert.ok(none);
        assert.ok(invert);
        assert.ok(label);

        all?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        none?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        invert?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions, [
            { action: "set_active_selection_operation", details: { operation: "all" } },
            { action: "set_active_selection_operation", details: { operation: "none" } },
            { action: "set_active_selection_operation", details: { operation: "invert" } },
        ]);

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

        (panel as any).switchTab("selection");
        const root = host.children[0];
        const input = findFirstByAttribute(root, "data-molsysviewer-query-input", "selection") as any;
        const select = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "replace") as any;
        assert.strictEqual(select.disabled, true);

        input.value = "bad query";
        input.dispatch("input");

        let status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(firstText(status), "Press Enter or Check to verify.");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "idle");

        const check = findFirstByAttribute(root, "data-molsysviewer-query-check", "selection");
        check?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(firstText(status), "Checking query...");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "pending");

        const requestId = (panel as any).selectionPanel.selectionQueryComposer.activeRequestId;
        panel.updateSelectionQueryPreview({ request_id: requestId, ok: false, error_message: "invalid syntax" });
        status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(firstText(status), "✗ invalid syntax");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "error");

        const enabledSelect = findFirstByAttribute(root, "data-molsysviewer-selection-query-apply", "replace") as any;
        assert.strictEqual(enabledSelect.disabled, false);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection query preview uses a dedicated query-only action", () => {
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
        const input = findFirstByAttribute(root, "data-molsysviewer-query-input", "selection") as any;
        assert.ok(input);
        input.value = "group_index==1";
        input.dispatch("input");
        assert.deepStrictEqual(actions, []);

        const check = findFirstByAttribute(root, "data-molsysviewer-query-check", "selection");
        assert.ok(check);
        check?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        assert.strictEqual(actions.at(-1).action, "selection_query_preview_request");
        assert.strictEqual(actions.at(-1).details.expression, "group_index==1");
        assert.strictEqual(actions.at(-1).details.syntax, "MolSysMT");
        assert.strictEqual(typeof actions.at(-1).details.request_id, "number");
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

        (panel as any).switchTab("selection");
        const root = host.children[0];
        const water = findFirstByAttribute(root, "data-molsysviewer-selection-query-preset", "water");
        assert.ok(water);

        water?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const input = findFirstByAttribute(root, "data-molsysviewer-query-input", "selection") as any;
        assert.strictEqual(input.value, 'molecule_type=="water"');
        const status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "idle");

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

        (panel as any).switchTab("selection");
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
        const input = findFirstByAttribute(root, "data-molsysviewer-query-input", "selection") as any;
        assert.strictEqual(input.value, 'chain_id=="A"');
        const status = findFirstByAttribute(root, "data-molsysviewer-query-status", "selection");
        assert.strictEqual(status?.getAttribute("data-molsysviewer-query-status-value"), "idle");

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel selection sidebar no longer renders expanders", () => {
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
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-selection-expander-panel"), null);
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-selection-expand-level", "group"), null);
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-selection-expand-spatial"), null);

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

        (panel as any).switchTab("selection");
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

        (panel as any).switchTab("selection");
        (panel as any).switchTab("regions");
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

test("GroupPanel region create composer covers active, checked query, split, and global actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        (panel as any).switchTab("regions");
        const root = host.children[0];

        const initiallyDisabled = findFirstByAttribute(
            root,
            "data-molsysviewer-region-create-active",
            "true",
        );
        assert.strictEqual(initiallyDisabled?.disabled, true);

        panel.updateSelection({
            count_atoms: 2,
            atom_indices: [0, 1],
        } as any);
        const activeCreate = findFirstByAttribute(root, "data-molsysviewer-region-create-active", "true");
        assert.strictEqual(activeCreate?.disabled, false);
        activeCreate?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "create_region_from_selection",
            details: {},
        });

        findFirstByAttribute(root, "data-molsysviewer-region-create-origin", "query")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const queryInput = findFirstByAttribute(root, "data-molsysviewer-query-input", "region") as any;
        queryInput.value = "group_index == 0";
        queryInput.dispatch("input");
        assert.strictEqual(actions.filter(item => item.action === "selection_query_preview_request").length, 0);

        findFirstByAttribute(root, "data-molsysviewer-query-check", "region")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const previewRequest = actions.at(-1);
        assert.strictEqual(previewRequest.action, "selection_query_preview_request");
        panel.updateSelectionQueryPreview({
            request_id: previewRequest.details.request_id,
            ok: true,
            count: 3,
        });
        const queryCreate = findFirstByAttribute(root, "data-molsysviewer-region-create-query", "true");
        assert.strictEqual(queryCreate?.disabled, false);
        queryCreate?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "create_region_from_query",
            details: {
                expression: "group_index == 0",
                syntax: "MolSysMT",
            },
        });

        findFirstByAttribute(root, "data-molsysviewer-region-create-origin", "split")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        findFirstByAttribute(root, "data-molsysviewer-region-split", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "make_regions_by",
            details: { element: "chain" },
        });
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-region-create-tag", "true"),
            null,
        );

        findFirstByAttribute(root, "data-molsysviewer-region-show-all", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        findFirstByAttribute(root, "data-molsysviewer-region-hide-all", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.slice(-2), [
            { action: "show_all_regions", details: undefined },
            { action: "hide_all_regions", details: undefined },
        ]);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region create uses real style options, saved selections, and inherit default when whole is hidden", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegionStyleOptions({
            representations: ["cartoon", "line", "spacefill"],
            presets: ["polymer-cartoon"],
            wholeHidden: true,
        });
        panel.setSavedSelections([{ tag: "saved_site", atom_count: 4 }]);
        panel.updateSelection({ count_atoms: 2, atom_indices: [0, 1] } as any);
        (panel as any).switchTab("regions");
        const root = host.children[0];
        const createRepresentation = findFirstByAttribute(
            root,
            "data-molsysviewer-region-create-representation",
            "true",
        ) as any;
        assert.strictEqual(createRepresentation.children.length, 6);
        assert.strictEqual(createRepresentation.value, "inherit");

        findFirstByAttribute(root, "data-molsysviewer-region-create-active", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "create_region_from_selection",
            details: { representation: "inherit" },
        });

        findFirstByAttribute(root, "data-molsysviewer-region-create-origin", "saved")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const savedSelect = findFirstByAttribute(
            root,
            "data-molsysviewer-region-create-saved-select",
            "true",
        ) as any;
        assert.strictEqual(savedSelect.value, "saved_site");
        createRepresentation.value = "preset:polymer-cartoon";
        createRepresentation.dispatch("change");
        findFirstByAttribute(root, "data-molsysviewer-region-create-saved", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "create_region_from_saved_selection",
            details: { selection_tag: "saved_site", preset: "polymer-cartoon" },
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region cards expose lifecycle actions and explicit collision choices", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegions([
            {
                tag: "binding",
                atom_count: 8,
                hidden: false,
                representation: "line",
                overlap_tags: ["catalytic"],
            },
            {
                tag: "catalytic",
                atom_count: 3,
                hidden: false,
                representation: "ball-and-stick",
                overlap_tags: ["binding"],
            },
        ]);
        (panel as any).switchTab("regions");
        const root = host.children[0];

        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-region-overlap", "binding")?.title,
            "Overlaps: catalytic",
        );
        for (const [attribute, action] of [
            ["data-molsysviewer-region-visibility", "toggle_region_visibility"],
            ["data-molsysviewer-region-isolate", "show_only_region"],
            ["data-molsysviewer-region-complement", "create_complementary_region"],
            ["data-molsysviewer-region-duplicate", "duplicate_region"],
            ["data-molsysviewer-region-reset", "reset_region_representation"],
            ["data-molsysviewer-region-delete", "delete_region"],
        ]) {
            findFirstByAttribute(root, attribute, "binding")
                ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
            assert.deepStrictEqual(actions.at(-1), { action, details: { tag: "binding" } });
        }

        findFirstByAttribute(root, "data-molsysviewer-region-rename", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const renameInput = findFirstByAttribute(
            root,
            "data-molsysviewer-region-rename-input",
            "binding",
        ) as any;
        renameInput.value = "catalytic";
        findFirstByAttribute(root, "data-molsysviewer-region-rename-confirm", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.ok(findFirstByAttribute(
            root,
            "data-molsysviewer-region-rename-collision",
            "catalytic",
        ));
        findFirstByAttribute(root, "data-molsysviewer-region-collision-overwrite", "rename")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.slice(-2), [
            { action: "delete_region", details: { tag: "catalytic" } },
            { action: "rename_region", details: { tag: "binding", new_tag: "catalytic" } },
        ]);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region style composer brackets live opacity changes for history", async () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegionStyleOptions({
            representations: [
                "backbone", "ball-and-stick", "carbohydrate", "cartoon",
                "ellipsoid", "gaussian-surface", "gaussian-volume", "line",
                "molecular-surface", "point", "putty", "spacefill",
            ],
            presets: ["atomic-detail", "auto", "coarse-surface", "empty", "polymer-and-ligand", "polymer-cartoon"],
        });
        panel.setRegions([{
            tag: "binding",
            atom_count: 8,
            hidden: false,
            representation: "line",
            representation_params: { alpha: 0.4, quality: "high", sizeFactor: 0.8 },
            available_attributes: ["b_factor"],
        }]);
        (panel as any).switchTab("regions");
        const root = host.children[0];
        findFirstByAttribute(root, "data-molsysviewer-region-style", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        const representation = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-representation",
            "binding",
        ) as any;
        const preset = findFirstByAttribute(root, "data-molsysviewer-region-style-preset", "binding") as any;
        const opacity = findFirstByAttribute(root, "data-molsysviewer-region-style-opacity", "binding") as any;
        const opacityValue = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-opacity-value",
            "binding",
        );
        const quality = findFirstByAttribute(root, "data-molsysviewer-region-style-quality", "binding") as any;
        const colorScheme = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-color-scheme",
            "binding",
        ) as any;
        const uniformColor = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-uniform-color",
            "binding",
        ) as any;
        const attribute = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-color-attribute",
            "binding",
        ) as any;

        assert.strictEqual(representation.children.length, 14);
        assert.strictEqual(preset.children.length, 7);
        assert.strictEqual(attribute.children.length, 2);
        representation.value = "cartoon";
        preset.value = "";
        quality.value = "high";
        colorScheme.value = "";
        opacity.value = "0.65";
        opacity.dispatch("pointerdown");
        opacity.dispatch("input");
        assert.strictEqual(opacityValue?.textContent, "0.65");
        panel.setRegions([{
            tag: "binding",
            atom_count: 8,
            hidden: false,
            representation: "line",
            representation_params: { alpha: 0.65, quality: "high", sizeFactor: 0.8 },
            available_attributes: ["b_factor"],
        }]);
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-region-style-opacity", "binding"),
            opacity,
        );
        opacity.dispatch("pointerup");
        assert.deepStrictEqual(actions.slice(-3), [{
            action: "begin_scene_history_coalescing",
            details: undefined,
        }, {
            action: "set_region_representation",
            details: {
                tag: "binding",
                representation: "line",
                params: { alpha: 0.65, quality: "high", sizeFactor: 0.8 },
            },
        }, {
            action: "end_scene_history_coalescing",
            details: undefined,
        }]);
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-region-style-opacity", "binding"),
            opacity,
        );
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.notStrictEqual(
            findFirstByAttribute(root, "data-molsysviewer-region-style-opacity", "binding"),
            opacity,
        );

        const refreshedRepresentation = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-representation",
            "binding",
        ) as any;
        const refreshedPreset = findFirstByAttribute(root, "data-molsysviewer-region-style-preset", "binding") as any;
        const refreshedQuality = findFirstByAttribute(root, "data-molsysviewer-region-style-quality", "binding") as any;
        const refreshedColorScheme = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-color-scheme",
            "binding",
        ) as any;
        const refreshedUniformColor = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-uniform-color",
            "binding",
        ) as any;
        refreshedPreset.value = "polymer-cartoon";
        refreshedPreset.dispatch("change");
        assert.strictEqual(refreshedRepresentation.value, "");
        refreshedColorScheme.value = "uniform";
        refreshedColorScheme.dispatch("change");
        refreshedUniformColor.value = "#112233";
        refreshedQuality.value = "highest";
        findFirstByAttribute(root, "data-molsysviewer-region-style-apply", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_region_representation",
            details: {
                tag: "binding",
                preset: "polymer-cartoon",
                params: {
                    alpha: 0.65,
                    quality: "highest",
                    sizeFactor: 0.8,
                    color: "#112233",
                },
            },
        });

        findFirstByAttribute(root, "data-molsysviewer-region-style", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const nextAttribute = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-color-attribute",
            "binding",
        ) as any;
        nextAttribute.value = "b_factor";
        nextAttribute.dispatch("change");
        assert.deepStrictEqual(actions.at(-1), {
            action: "color_region_by_attribute",
            details: {
                tag: "binding",
                attribute: "b_factor",
                element: "atom",
                palette: "viridis",
                replace: true,
            },
        });
        findFirstByAttribute(root, "data-molsysviewer-region-style-reset-colors", "binding")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "reset_region_colors",
            details: { tag: "binding" },
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region style composer disables base opacity and preserves current visual on empty apply", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegions([{ tag: "base", atom_count: 5, hidden: false }]);
        (panel as any).switchTab("regions");
        const root = host.children[0];
        findFirstByAttribute(root, "data-molsysviewer-region-style", "base")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const baseOpacity = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-opacity",
            "base",
        ) as any;
        assert.strictEqual(baseOpacity?.disabled, true);
        baseOpacity.value = "0.4";
        baseOpacity.dispatch("change");
        assert.strictEqual(actions.length, 0);

        findFirstByAttribute(root, "data-molsysviewer-region-style-apply", "base")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_region_representation",
            details: {
                tag: "base",
                representation: "inherit",
                params: { alpha: 0.4, quality: "auto" },
            },
        });

        panel.setRegions([{
            tag: "line",
            atom_count: 6,
            hidden: false,
            representation: "line",
            representation_params: { alpha: 0.8 },
        }]);
        findFirstByAttribute(root, "data-molsysviewer-region-style", "line")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const representation = findFirstByAttribute(
            root,
            "data-molsysviewer-region-style-representation",
            "line",
        ) as any;
        const preset = findFirstByAttribute(root, "data-molsysviewer-region-style-preset", "line") as any;
        const opacity = findFirstByAttribute(root, "data-molsysviewer-region-style-opacity", "line") as any;
        const quality = findFirstByAttribute(root, "data-molsysviewer-region-style-quality", "line") as any;
        representation.value = "";
        preset.value = "";
        opacity.value = "0.7";
        quality.value = "medium";
        findFirstByAttribute(root, "data-molsysviewer-region-style-apply", "line")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_region_representation",
            details: {
                tag: "line",
                representation: "line",
                params: { alpha: 0.7, quality: "medium" },
            },
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region boolean composer supports ordered operations and overlap prefill", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegions([
            { tag: "pocket", atom_count: 8, hidden: false, overlap_tags: ["backbone", "water"] },
            { tag: "backbone", atom_count: 4, hidden: false, overlap_tags: ["pocket"] },
            { tag: "water", atom_count: 12, hidden: false, overlap_tags: ["pocket"] },
        ]);
        (panel as any).switchTab("regions");
        const root = host.children[0];
        findFirstByAttribute(root, "data-molsysviewer-region-overlap", "pocket")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const composer = findFirstByAttribute(
            root,
            "data-molsysviewer-region-boolean-composer",
            "true",
        );
        assert.strictEqual(
            composer?.getAttribute("data-molsysviewer-region-boolean-current-a"),
            "pocket",
        );
        assert.strictEqual(
            composer?.getAttribute("data-molsysviewer-region-boolean-current-b"),
            "backbone,water",
        );
        assert.strictEqual(
            composer?.getAttribute("data-molsysviewer-region-boolean-current-operation"),
            "difference",
        );
        assert.strictEqual(
            composer?.getAttribute("data-molsysviewer-region-boolean-attention"),
            "true",
        );

        // The attention flag is one-shot: a subsequent repaint must clear it,
        // otherwise the ⚠ highlight sticks to the composer forever (the bug).
        panel.setRegions([
            { tag: "pocket", atom_count: 8, hidden: false, overlap_tags: ["backbone", "water"] },
            { tag: "backbone", atom_count: 4, hidden: false, overlap_tags: ["pocket"] },
            { tag: "water", atom_count: 12, hidden: false, overlap_tags: ["pocket"] },
        ]);
        const composerAfter = findFirstByAttribute(
            host.children[0],
            "data-molsysviewer-region-boolean-composer",
            "true",
        );
        assert.strictEqual(
            composerAfter?.getAttribute("data-molsysviewer-region-boolean-attention"),
            "false",
        );

        const output = findFirstByAttribute(
            root,
            "data-molsysviewer-region-boolean-output",
            "true",
        ) as any;
        output.value = "sidechains";
        output.dispatch("input");
        findFirstByAttribute(root, "data-molsysviewer-region-boolean-create", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "compose_regions",
            details: {
                tag_a: "pocket",
                operand_tags: ["backbone", "water"],
                op: "difference",
                new_tag: "sidechains",
            },
        });

        output.value = "backbone";
        output.dispatch("input");
        findFirstByAttribute(root, "data-molsysviewer-region-boolean-create", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.ok(findFirstByAttribute(
            root,
            "data-molsysviewer-region-boolean-collision",
            "backbone",
        ));
        findFirstByAttribute(root, "data-molsysviewer-region-boolean-overwrite", "true")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "compose_regions",
            details: {
                tag_a: "pocket",
                operand_tags: ["backbone", "water"],
                op: "difference",
                new_tag: "backbone",
                overwrite: true,
            },
        });

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel region inspect fetches lazily and rejects stale details", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details: any }> = [];
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
            (action, details) => actions.push({ action, details }),
        );
        panel.setRegions([{ tag: "site", atom_count: 3, hidden: false }]);
        (panel as any).switchTab("regions");
        const root = host.children[0];
        findFirstByAttribute(root, "data-molsysviewer-region-inspect", "site")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        const request = actions.at(-1);
        assert.strictEqual(request.action, "get_region_details");
        assert.strictEqual(request.details.tag, "site");
        assert.strictEqual(
            firstText(findFirstByAttribute(root, "data-molsysviewer-region-inspect-panel", "site")),
            "Loading...",
        );

        panel.updateRegionDetails({
            request_id: request.details.request_id + 1,
            tag: "site",
            atom_count: 99,
            group_count: 99,
            chain_count: 99,
            center_nm: [9, 9, 9],
            structure_index: 9,
        });
        assert.strictEqual(
            firstText(findFirstByAttribute(root, "data-molsysviewer-region-inspect-panel", "site")),
            "Loading...",
        );

        panel.updateRegionDetails({
            request_id: request.details.request_id,
            tag: "site",
            atom_count: 3,
            group_count: 2,
            chain_count: 1,
            center_nm: [0.1, 0.2, 0.3],
            structure_index: 4,
        });
        const details = findFirstByAttribute(root, "data-molsysviewer-region-inspect-panel", "site");
        assert.strictEqual(details?.getAttribute("data-molsysviewer-region-inspect-frame"), "4");
        assert.strictEqual(
            findFirstByAttribute(
                root,
                "data-molsysviewer-region-inspect-center",
                "true",
            )?.textContent,
            "center [nm]: 0.100, 0.200, 0.300",
        );
        findFirstByAttribute(root, "data-molsysviewer-region-inspect-refresh", "site")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(actions.at(-1).action, "get_region_details");
        assert.ok(actions.at(-1).details.request_id > request.details.request_id);

        panel.dispose();
    } finally {
        restore();
    }
});

test("GroupPanel layers panel joins typed members into user layers and emits lifecycle actions", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details?: any }> = [];
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
        const layersTab = findFirstByAttribute(root, "data-molsysviewer-group-panel-tab", "layers");
        assert.ok(layersTab);

        panel.setRegions([
            { tag: "pocket", atom_count: 4, hidden: false, layer: "analysis" },
            { tag: "free", atom_count: 2, hidden: false, layer: null },
        ]);
        panel.setLayerObjects([
            { kind: "annotation", tag: "note1", title: "Note", layerTag: "analysis" },
            { kind: "shape", tag: "marker", title: "Marker", layerTag: "marker" },
        ]);
        panel.setLayers([
            { tag: "analysis", provenance: "user", hidden: false },
            { tag: "empty", provenance: "user", hidden: false },
            { tag: "marker", provenance: "auto", hidden: false },
        ]);
        layersTab.dispatch("click", { preventDefault() {}, stopPropagation() {} });

        assert.ok(findFirstByAttribute(root, "data-molsysviewer-layer-card", "analysis"));
        assert.ok(findFirstByAttribute(root, "data-molsysviewer-layer-card", "empty"));
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-layer-card", "marker"), null);

        findFirstByAttribute(root, "data-molsysviewer-layer-visibility", "analysis")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_layer_visibility",
            details: { tag: "analysis", hidden: true },
        });

        findFirstByAttribute(root, "data-molsysviewer-layer-details", "analysis")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.ok(findFirstByAttribute(root, "data-molsysviewer-layer-member", "region:pocket"));
        assert.ok(findFirstByAttribute(root, "data-molsysviewer-layer-member", "annotation:note1"));

        findFirstByAttribute(root, "data-molsysviewer-layer-remove-member", "annotation:note1")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "remove_member_from_layer",
            details: { layer: "analysis", member_kind: "annotation", member_tag: "note1" },
        });

        const picker = findFirstByAttribute(root, "data-molsysviewer-layer-member-picker", "analysis") as any;
        picker.value = JSON.stringify(["region", "free"]);
        findFirstByAttribute(root, "data-molsysviewer-layer-add-member", "analysis")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "add_member_to_layer",
            details: { layer: "analysis", member_kind: "region", member_tag: "free" },
        });

        findFirstByAttribute(root, "data-molsysviewer-layer-ungroup", "analysis")
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), {
            action: "ungroup_layer",
            details: { tag: "analysis" },
        });

        const createInput = findFirstByAttribute(root, "data-molsysviewer-layer-create-input", "true") as any;
        createInput.value = "site";
        findFirstByAttribute(root, "data-molsysviewer-layer-create-form", "true")
            ?.children.at(-1)
            ?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.at(-1), { action: "create_layer", details: { tag: "site" } });

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

        (panel as any).switchTab("selection");
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

test("GroupPanel does not rebuild the System hierarchy when runtime visibility is unchanged", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const systemPanel = (panel as unknown as { systemPanel: { rebuild(): void } }).systemPanel;
        let rebuilds = 0;
        systemPanel.rebuild = () => { rebuilds += 1; };

        panel.setRuntimeVisible(null);
        panel.setRuntimeVisible(false);
        panel.setRuntimeVisible(false);
        panel.setRuntimeVisible(null);

        assert.strictEqual(rebuilds, 2);
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

test("GroupPanel does not expose a molecular color-scheme toggle in the System tab", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const root = host.children[0];
        const toggle = findFirstByAttribute(root, "data-molsysviewer-color-scheme-toggle", "true");
        assert.strictEqual(toggle, null, "whole-owned color scheme must not repaint the molecule from System");
    } finally {
        restore();
    }
});

test("GroupPanel Whole panel renders summary and confirms hiding base-only regions", () => {
    const restore = installFakeDom();
    const previousWindow = (globalThis as any).window;
    try {
        let confirmed = 0;
        (globalThis as any).window = { confirm: () => { confirmed += 1; return false; } };
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details?: any }> = [];
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, (action, details) => {
            actions.push({ action, details });
        });
        panel.setWholeSummary({
            representation: "cartoon",
            preset: null,
            params: { alpha: 0.65, quality: "medium" },
            visible: true,
            color_scheme: "physicochemical",
            scene_style_name: "publication",
            available_attributes: ["b_factor"],
            color_schemes: ["element_cpk", "physicochemical"],
            inheriting_region_count: 2,
            none_state_region_count: 1,
            covering_layer_count: 3,
        });
        const root = host.children[0];
        const dot = findFirstByAttribute(root, "data-molsysviewer-whole-visible-dot", "true");
        const hide = findFirstByAttribute(root, "data-molsysviewer-whole-visibility", "hide");
        const scheme = findFirstByAttribute(root, "data-molsysviewer-whole-color-scheme", "true") as any;
        assert.ok(dot);
        assert.ok(hide);
        assert.strictEqual(scheme?.value, "physicochemical");

        hide?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(confirmed, 1);
        assert.deepStrictEqual(actions, []);
    } finally {
        (globalThis as any).window = previousWindow;
        restore();
    }
});

test("GroupPanel Whole opacity brackets live changes for history", async () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details?: any }> = [];
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, (action, details) => {
            actions.push({ action, details });
        });
        panel.setWholeSummary({
            representation: "cartoon",
            preset: null,
            params: { alpha: 0.5 },
            visible: true,
            color_scheme: null,
            scene_style_name: null,
            available_attributes: [],
            color_schemes: ["element_cpk"],
            inheriting_region_count: 0,
            none_state_region_count: 0,
            covering_layer_count: 0,
        });
        const root = host.children[0];
        const opacity = findFirstByAttribute(root, "data-molsysviewer-whole-opacity", "true") as any;
        const readout = findFirstByAttribute(root, "data-molsysviewer-whole-opacity-value", "true");
        const wholePanel = (panel as any).wholePanel;
        const render = wholePanel.render.bind(wholePanel);
        let renders = 0;
        wholePanel.render = () => {
            renders += 1;
            render();
        };
        assert.ok(opacity);
        opacity.value = "0.25";
        opacity.dispatch("pointerdown", { preventDefault() {}, stopPropagation() {} });
        opacity.dispatch("input", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(readout?.textContent, "0.25");
        panel.setWholeSummary({
            representation: "cartoon",
            preset: null,
            params: { alpha: 0.25 },
            visible: true,
            color_scheme: null,
            scene_style_name: null,
            available_attributes: [],
            color_schemes: ["element_cpk"],
            inheriting_region_count: 0,
            none_state_region_count: 0,
            covering_layer_count: 0,
        });
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-whole-opacity", "true"),
            opacity,
        );
        opacity.dispatch("pointerup", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.map(item => item.action), [
            "begin_scene_history_coalescing",
            "set_whole_representation",
            "end_scene_history_coalescing",
        ]);
        assert.deepStrictEqual(actions[1].details.params.alpha, 0.25);
        assert.strictEqual(renders, 0);
        await new Promise(resolve => setTimeout(resolve, 0));
        assert.strictEqual(renders, 1);
    } finally {
        restore();
    }
});

test("GroupPanel Measures renders scientific values and routes every mutation through panel actions", async () => {
    const restore = installFakeDom();
    const previousWindow = (globalThis as any).window;
    try {
        (globalThis as any).window = { confirm: () => true };
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details?: any }> = [];
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, (action, details) => {
            actions.push({ action, details });
        });
        panel.setMeasurements([{
            kind: "distance",
            tag: "d1",
            layerTag: "analysis",
            picks: 2,
            hidden: false,
            atomIndices: [0, 1],
            value: 5.934,
            unit: "angstrom",
            endpointLabels: ["N (ALA 1)", "C (ALA 2)"],
            endpointPolicy: "centroid",
            broken: false,
        }, {
            kind: "angle",
            tag: "broken-angle",
            picks: 3,
            hidden: false,
            atomIndices: [2, 3],
            value: 112.4,
            unit: "degree",
            endpointLabels: [],
            endpointPolicy: "atom",
            broken: true,
            brokenReason: "Missing anchor atom indices: [4]",
        }], {
            endpointPolicyDefault: "representative_atom",
            representativeAtoms: { protein: "CA", nucleic: "P", lipid: "P", other: "" },
            structureIndex: 0,
            systemLoaded: true,
        });
        panel.updateSelection({
            source_kind: "element",
            atom_indices: [0, 1],
            group_indices: [0, 1],
            count_atoms: 2,
            count_groups: 2,
        } as any);
        (panel as any).switchTab("measures");
        const root = host.children[0];

        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-measurement-value", "d1")?.textContent, "5.93 Å");
        assert.strictEqual(findFirstByAttribute(root, "data-molsysviewer-measurement-value", "broken-angle")?.textContent, "—");
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-measurement-endpoints", "d1")?.textContent,
            "N (ALA 1) → C (ALA 2)",
        );

        findFirstByAttribute(root, "data-molsysviewer-measurement-create-kind", "distance")?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        findFirstByAttribute(root, "data-molsysviewer-measurement-visibility", "d1")?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        findFirstByAttribute(root, "data-molsysviewer-measurement-delete", "d1")?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.deepStrictEqual(actions.slice(-3), [
            { action: "create_measurement", details: { kind: "distance" } },
            { action: "toggle_measurement_visibility", details: { tag: "d1" } },
            { action: "delete_measurement", details: { tag: "d1" } },
        ]);

        findFirstByAttribute(root, "data-molsysviewer-measurement-series-toggle", "d1")?.dispatch("click", { preventDefault() {}, stopPropagation() {} });
        assert.strictEqual(actions.at(-1)?.action, "request_measurement_series");
        assert.strictEqual(actions.at(-1)?.details.tag, "d1");
        assert.strictEqual(typeof actions.at(-1)?.details.request_id, "number");
        const requestId = actions.at(-1)?.details.request_id;

        panel.updateMeasurementSeries({
            tag: "d1", requestId: requestId + 1, unit: "angstrom", nFrames: 2,
            sparkline: [5.934, 6.1], sparklineIndices: [0, 1], seriesIndex: 0,
        });
        assert.strictEqual(
            findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-series", "d1"),
            null,
            "a stale lazy-series response must not replace the pending request",
        );
        panel.updateMeasurementSeries({
            tag: "d1", requestId, unit: "angstrom", nFrames: 2,
            sparkline: [5.934, 6.1], sparklineIndices: [0, 1], seriesIndex: 0,
        });
        assert.ok(findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-series", "d1"));

        const clickEvent = { preventDefault() {}, stopPropagation() {} };
        findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-more", "d1")?.dispatch("click", clickEvent);
        await new Promise(resolve => setTimeout(resolve, 0));
        const rename = findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-rename-input", "d1") as any;
        rename.value = "distance";
        findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-rename", "d1")?.dispatch("click", clickEvent);
        const layer = findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-layer-input", "d1") as any;
        layer.value = "analysis-2";
        findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-layer", "d1")?.dispatch("click", clickEvent);
        assert.deepStrictEqual(actions.slice(-2), [
            { action: "rename_measurement", details: { tag: "d1", new_tag: "distance" } },
            { action: "set_measurement_layer", details: { tag: "d1", layer: "analysis-2" } },
        ]);

        for (const action of ["show_all_measurements", "hide_all_measurements", "clear_measurements"] as const) {
            findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-global", action)?.dispatch("click", clickEvent);
        }
        assert.deepStrictEqual(actions.slice(-3).map(item => item.action), [
            "show_all_measurements", "hide_all_measurements", "clear_measurements",
        ]);

        findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-policy", "centroid")?.dispatch("change");
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_measurement_endpoint_policy",
            details: { policy: "centroid" },
        });

        const representative = findFirstByAttribute(host.children[0], "data-molsysviewer-measurement-representative", "protein") as any;
        representative.value = "CB";
        representative.dispatch("change");
        assert.deepStrictEqual(actions.at(-1), {
            action: "set_measurement_representative_atom",
            details: { target: "protein", atom_name: "CB" },
        });

        panel.dispose();
    } finally {
        (globalThis as any).window = previousWindow;
        restore();
    }
});

test("GroupPanel Annotations edits labels and routes every mutation through panel actions", async () => {
    const restore = installFakeDom();
    const previousWindow = (globalThis as any).window;
    try {
        (globalThis as any).window = { confirm: () => true };
        const host = new FakeElement() as any;
        const actions: Array<{ action: string; details?: any }> = [];
        const focused: any[] = [];
        const panel = new GroupPanel(
            host,
            () => {},
            () => {},
            item => focused.push(item),
            () => {},
            () => {},
            () => {},
            () => {},
            () => {},
            (action, details) => actions.push({ action, details }),
        );
        const annotations: AnnotationSummary[] = [{
            kind: "label",
            tag: "note",
            layerTag: "analysis",
            text: "Catalytic site",
            hidden: false,
            nAtoms: 2,
            atomIndices: [0, 1],
            anchor: { type: "atoms", indices: [0, 1] },
            style: { color: "#123456", size_em: 1.2, background: true, background_opacity: 0.7 },
            broken: false,
        }, {
            kind: "label",
            tag: "broken",
            text: "Mutation site",
            hidden: false,
            nAtoms: 0,
            atomIndices: [],
            anchor: { type: "atoms", indices: [] },
            style: {},
            broken: true,
            brokenReason: "Missing anchor atom indices: [9]",
        }];
        const annotationSettings = { systemLoaded: true, activeSelectionCount: 3 };
        panel.setAnnotations(annotations, annotationSettings);
        panel.updateSelection({
            source_kind: "element",
            atom_indices: [4, 5, 6],
            group_indices: [1],
            count_atoms: 3,
            count_groups: 1,
        } as any);
        (panel as any).switchTab("annotations");
        const root = host.children[0];
        const clickEvent = { preventDefault() {}, stopPropagation() {} };

        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-annotation-identity", "note")?.textContent,
            "note · 2 atoms · layer: analysis",
        );
        assert.strictEqual(
            findFirstByAttribute(root, "data-molsysviewer-annotation-identity", "broken")?.textContent,
            "broken · anchor broken",
        );

        findFirstByAttribute(root, "data-molsysviewer-annotation-focus", "note")?.dispatch("click", clickEvent);
        assert.deepStrictEqual(focused[0].atom_indices, [0, 1]);
        findFirstByAttribute(root, "data-molsysviewer-annotation-visibility", "note")?.dispatch("click", clickEvent);
        findFirstByAttribute(root, "data-molsysviewer-annotation-delete", "note")?.dispatch("click", clickEvent);
        assert.deepStrictEqual(actions.slice(-2), [
            { action: "toggle_annotation_visibility", details: { tag: "note" } },
            { action: "delete_annotation", details: { tag: "note" } },
        ]);

        findFirstByAttribute(root, "data-molsysviewer-annotation-text", "note")?.dispatch("click", clickEvent);
        await new Promise(resolve => setTimeout(resolve, 0));
        const textInput = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-text-input", "note") as any;
        textInput.dispatch("focus");
        textInput.value = "Gate closed";
        textInput.dispatch("input");
        textInput.dispatch("keydown", { key: "Enter" });
        assert.deepStrictEqual(actions.slice(-3), [
            { action: "begin_scene_history_coalescing", details: undefined },
            { action: "set_annotation_text", details: { tag: "note", text: "Gate closed" } },
            { action: "end_scene_history_coalescing", details: undefined },
        ]);

        annotations[0] = { ...annotations[0], text: "Gate closed" };
        panel.setAnnotations(annotations, annotationSettings);
        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-text", "note")?.dispatch("click", clickEvent);
        await new Promise(resolve => setTimeout(resolve, 0));
        const cancelledInput = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-text-input", "note") as any;
        cancelledInput.dispatch("focus");
        cancelledInput.value = "Wrong text";
        cancelledInput.dispatch("input");
        cancelledInput.dispatch("keydown", { key: "Escape" });
        assert.deepStrictEqual(actions.slice(-4), [
            { action: "begin_scene_history_coalescing", details: undefined },
            { action: "set_annotation_text", details: { tag: "note", text: "Wrong text" } },
            { action: "set_annotation_text", details: { tag: "note", text: "Gate closed" } },
            { action: "end_scene_history_coalescing", details: undefined },
        ]);

        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-more", "note")?.dispatch("click", clickEvent);
        await new Promise(resolve => setTimeout(resolve, 0));
        const rename = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-rename-input", "note") as any;
        rename.value = "gate";
        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-rename", "note")?.dispatch("click", clickEvent);
        const layer = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-layer-input", "note") as any;
        layer.value = "sites";
        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-layer", "note")?.dispatch("click", clickEvent);
        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-reanchor", "note")?.dispatch("click", clickEvent);
        assert.deepStrictEqual(actions.slice(-3), [
            { action: "rename_annotation", details: { tag: "note", new_tag: "gate" } },
            { action: "set_annotation_layer", details: { tag: "note", layer: "sites" } },
            { action: "reanchor_annotation", details: { tag: "note" } },
        ]);

        const color = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-style-color", "note") as any;
        color.dispatch("focus");
        color.value = "#abcdef";
        color.dispatch("input");
        color.dispatch("blur");
        assert.deepStrictEqual(actions.slice(-3).map(item => item.action), [
            "begin_scene_history_coalescing", "set_annotation_style", "end_scene_history_coalescing",
        ]);
        assert.strictEqual(actions.at(-2)?.details.style.color, "#abcdef");

        const createText = findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-create-text", "true") as any;
        createText.value = "New label";
        createText.dispatch("input");
        findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-create-confirm", "true")?.dispatch("click", clickEvent);
        assert.strictEqual(actions.at(-1)?.action, "create_annotation");
        assert.strictEqual(actions.at(-1)?.details.text, "New label");

        for (const action of ["show_all_annotations", "hide_all_annotations", "clear_annotations"] as const) {
            findFirstByAttribute(host.children[0], "data-molsysviewer-annotation-global", action)?.dispatch("click", clickEvent);
        }
        assert.deepStrictEqual(actions.slice(-3).map(item => item.action), [
            "show_all_annotations", "hide_all_annotations", "clear_annotations",
        ]);
        panel.dispose();
    } finally {
        (globalThis as any).window = previousWindow;
        restore();
    }
});

test("GroupPanel tabs have correct tooltips and initial subtitle labels", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement() as any;
        const panel = new GroupPanel(host, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {}, () => {});
        const root = host.children[0];
        const tabs = collectByAttribute(root, "data-molsysviewer-group-panel-tab");
        const systemTab = tabs.find(t => t.getAttribute("data-molsysviewer-group-panel-tab") === "system");
        const wholeTab = tabs.find(t => t.getAttribute("data-molsysviewer-group-panel-tab") === "whole");

        assert.ok(systemTab);
        assert.ok(wholeTab);
        assert.strictEqual(systemTab.title, "Molecular hierarchy, chain sequence, and residue-level selections.");
        assert.strictEqual(wholeTab.title, "Global representation styling, visual presets, and overall system view.");
        panel.dispose();
    } finally {
        restore();
    }
});
