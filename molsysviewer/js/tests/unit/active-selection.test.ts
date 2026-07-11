import assert from "node:assert";
import test from "node:test";

import { ActiveSelectionController } from "../../src/managers/active-selection";

const fullElements = [0, 1, 2, 3, 4];
const residueIndexByAtom = [0, 0, 0, 1, 1];
const residueOffsets = [0, 3, 5];
const chainIndexByAtom = [0, 0, 0, 0, 0];
const labelCompId = ["ALA", "GLY"];
const authSeqId = [1, 2];
const labelAsymId = ["A"];
const labelEntityId = ["1"];

function clickEvent(selectedAtoms: number[], shift = false): any {
    return {
        modifiers: { shift },
        current: {
            loci: selectedAtoms.length === 0 ? null : {
                kind: "element-loci",
                elements: [{
                    unit: {
                        elements: fullElements,
                        model: {
                            id: "model-1",
                            atomicHierarchy: {
                                residueAtomSegments: { index: residueIndexByAtom, offsets: residueOffsets },
                                chainAtomSegments: { index: chainIndexByAtom },
                                atoms: { label_comp_id: { value: (i: number) => labelCompId[residueIndexByAtom[i]] } },
                                residues: { auth_seq_id: { value: (i: number) => authSeqId[i] } },
                                chains: {
                                    label_asym_id: { value: (i: number) => labelAsymId[i] },
                                    label_entity_id: { value: (i: number) => labelEntityId[i] },
                                },
                                index: { getEntityFromChain: (_i: number) => 0 },
                            },
                        },
                    },
                    indices: selectedAtoms.map((atomIndex) => fullElements.indexOf(atomIndex)),
                }],
            },
        },
    };
}

test("ActiveSelectionController replaces, toggles group items with shift, and clears on empty click", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));

    controller.handlePrimaryClick(clickEvent([1]));
    controller.handlePrimaryClick(clickEvent([3], true));
    controller.handlePrimaryClick(clickEvent([4], true));
    controller.handlePrimaryClick(clickEvent([], true));
    controller.handlePrimaryClick(clickEvent([]));

    assert.deepStrictEqual(events, [
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "group",
            target_level: "none",
            items: [{
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1, 2],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                group_id: 1,
                chain_name: "A",
                entity_name: "1",
            }],
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
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "group",
            target_level: "none",
            items: [
                {
                    source_kind: "element",
                    element_level: "group",
                    atom_indices: [0, 1, 2],
                    group_indices: [0],
                    chain_indices: [0],
                    entity_indices: [0],
                    group_name: "ALA 1",
                    group_id: 1,
                    chain_name: "A",
                    entity_name: "1",
                },
                {
                    source_kind: "element",
                    element_level: "group",
                    atom_indices: [3, 4],
                    group_indices: [1],
                    chain_indices: [0],
                    entity_indices: [0],
                    group_name: "GLY 2",
                    group_id: 2,
                    chain_name: "A",
                    entity_name: "1",
                },
            ],
            atom_indices: [0, 1, 2, 3, 4],
            group_indices: [0, 1],
            component_indices: [],
            chain_indices: [0],
            molecule_indices: [],
            entity_indices: [0],
            count_atoms: 5,
            count_groups: 2,
            count_shapes: 0,
            count_annotations: 0,
        },
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "group",
            target_level: "none",
            items: [{
                source_kind: "element",
                element_level: "group",
                atom_indices: [0, 1, 2],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                group_name: "ALA 1",
                group_id: 1,
                chain_name: "A",
                entity_name: "1",
            }],
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
        {
            event: "interaction_active_selection_changed",
            source_kind: "empty",
            element_level: "none",
            target_level: "none",
            items: [],
            atom_indices: [],
            group_indices: [],
            component_indices: [],
            chain_indices: [],
            molecule_indices: [],
            entity_indices: [],
            count_atoms: 0,
            count_groups: 0,
            count_shapes: 0,
            count_annotations: 0,
        },
    ]);
});

test("ActiveSelectionController supports annotation selections and mixes them with element selections when added", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));

    controller.setItems([{
        source_kind: "annotation",
        annotation_kind: "label",
        atom_indices: [0, 1, 2],
        group_indices: [0],
        chain_indices: [0],
        entity_indices: [0],
        tag: "notes",
        text: "Catalytic",
    }]);
    controller.setItems([{
        source_kind: "annotation",
        annotation_kind: "label",
        atom_indices: [0, 1, 2],
        group_indices: [0],
        chain_indices: [0],
        entity_indices: [0],
        tag: "notes",
        text: "Catalytic",
    }], "add");
    controller.setItems([{
        source_kind: "element",
        element_level: "group",
        atom_indices: [3, 4],
        group_indices: [1],
        chain_indices: [0],
        entity_indices: [0],
        group_name: "GLY 2",
        group_id: 2,
        chain_name: "A",
        entity_name: "1",
    }], "add");

    assert.deepStrictEqual(events, [
        {
            event: "interaction_active_selection_changed",
            source_kind: "annotation",
            element_level: "none",
            target_level: "annotation",
            items: [{
                source_kind: "annotation",
                annotation_kind: "label",
                atom_indices: [0, 1, 2],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                tag: "notes",
                text: "Catalytic",
            }],
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
        {
            event: "interaction_active_selection_changed",
            source_kind: "annotation",
            element_level: "none",
            target_level: "annotation",
            items: [{
                source_kind: "annotation",
                annotation_kind: "label",
                atom_indices: [0, 1, 2],
                group_indices: [0],
                chain_indices: [0],
                entity_indices: [0],
                tag: "notes",
                text: "Catalytic",
            }],
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
        {
            event: "interaction_active_selection_changed",
            source_kind: "mixed",
            element_level: "group",
            target_level: "mixed",
            items: [
                {
                    source_kind: "annotation",
                    annotation_kind: "label",
                    atom_indices: [0, 1, 2],
                    group_indices: [0],
                    chain_indices: [0],
                    entity_indices: [0],
                    tag: "notes",
                    text: "Catalytic",
                },
                {
                    source_kind: "element",
                    element_level: "group",
                    atom_indices: [3, 4],
                    group_indices: [1],
                    chain_indices: [0],
                    entity_indices: [0],
                    group_name: "GLY 2",
                    group_id: 2,
                    chain_name: "A",
                    entity_name: "1",
                },
            ],
            atom_indices: [0, 1, 2, 3, 4],
            group_indices: [0, 1],
            component_indices: [],
            chain_indices: [0],
            molecule_indices: [],
            entity_indices: [0],
            count_atoms: 5,
            count_groups: 2,
            count_shapes: 0,
            count_annotations: 1,
        },
    ]);
});

test("ActiveSelectionController can rebuild a group-centric selection from atom indices", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));
    const structure: any = {
        units: [{
            kind: 0,
            elements: fullElements,
            model: {
                id: "model-1",
                atomicHierarchy: {
                    residueAtomSegments: { index: residueIndexByAtom, offsets: residueOffsets },
                    chainAtomSegments: { index: chainIndexByAtom },
                    atoms: { label_comp_id: { value: (i: number) => labelCompId[residueIndexByAtom[i]] } },
                    residues: { auth_seq_id: { value: (i: number) => authSeqId[i] } },
                    chains: {
                        label_asym_id: { value: (i: number) => labelAsymId[i] },
                        label_entity_id: { value: (i: number) => labelEntityId[i] },
                    },
                    index: { getEntityFromChain: (_i: number) => 0 },
                },
            },
        }],
    };

    controller.setFromAtomIndices([3, 4], structure);

    assert.deepStrictEqual(events, [{
        event: "interaction_active_selection_changed",
        source_kind: "element",
        element_level: "group",
        target_level: "none",
        items: [{
            source_kind: "element",
            element_level: "group",
            atom_indices: [3, 4],
            group_indices: [1],
            chain_indices: [0],
            entity_indices: [0],
            group_name: "GLY 2",
            group_id: 2,
            chain_name: "A",
            entity_name: "1",
        }],
        atom_indices: [3, 4],
        group_indices: [1],
        component_indices: [],
        chain_indices: [0],
        molecule_indices: [],
        entity_indices: [0],
        count_atoms: 2,
        count_groups: 1,
        count_shapes: 0,
        count_annotations: 0,
    }]);
});

test("ActiveSelectionController supports explicit subtract and intersect operations", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));
    const first = {
        source_kind: "element" as const,
        element_level: "group" as const,
        atom_indices: [0, 1, 2],
        group_indices: [0],
        chain_indices: [0],
        entity_indices: [0],
        group_name: "ALA 1",
        group_id: 1,
        chain_name: "A",
        entity_name: "1",
    };
    const second = {
        source_kind: "element" as const,
        element_level: "group" as const,
        atom_indices: [3, 4],
        group_indices: [1],
        chain_indices: [0],
        entity_indices: [0],
        group_name: "GLY 2",
        group_id: 2,
        chain_name: "A",
        entity_name: "1",
    };

    controller.setItems([first, second]);
    controller.setItems([first], "subtract");
    assert.deepStrictEqual(events.at(-1)?.group_indices, [1]);

    controller.setItems([first, second]);
    controller.setItems([first], "intersect");
    assert.deepStrictEqual(events.at(-1)?.group_indices, [0]);

    controller.setItems([], "intersect");
    assert.strictEqual(events.at(-1)?.source_kind, "empty");
});

test("ActiveSelectionController supports shape selections", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));

    controller.handlePrimaryClick({
        modifiers: { shift: false },
        current: {
            loci: {
                kind: "group-loci",
                groups: [{ ids: [0] }],
                shape: {
                    name: "Pocket Blob",
                    sourceData: {
                        tag: "pocket",
                        atom_indices: [8, 9],
                        __groupAtoms: [[8], [9]],
                        group_indices: [2],
                        chain_indices: [0],
                        entity_indices: [0],
                        __groupEntityRefs: [{ kind: "topomt.tetra", id: 3 }],
                    },
                },
            },
        },
    });

    assert.deepStrictEqual(events, [{
        event: "interaction_active_selection_changed",
        source_kind: "shape",
        element_level: "none",
        target_level: "shape",
        items: [{
            source_kind: "shape",
            shape_kind: "Pocket Blob",
            shape_name: "Pocket Blob",
            tag: "pocket",
            atom_indices: [8],
            group_indices: [2],
            chain_indices: [0],
            entity_indices: [0],
            entity_ref: { kind: "topomt.tetra", id: 3 },
        }],
        atom_indices: [8],
        group_indices: [2],
        component_indices: [],
        chain_indices: [0],
        molecule_indices: [],
        entity_indices: [0],
        count_atoms: 1,
        count_groups: 1,
        count_shapes: 1,
        count_annotations: 0,
    }]);
});

test("ActiveSelectionController clear emits the empty payload", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));

    controller.setItems([{
        source_kind: "element",
        element_level: "group",
        atom_indices: [0, 1, 2],
        group_indices: [0],
        chain_indices: [0],
        entity_indices: [0],
        group_name: "ALA 1",
        group_id: 1,
        chain_name: "A",
        entity_name: "1",
    }]);
    controller.clear();

    assert.deepStrictEqual(events.at(-1), {
        event: "interaction_active_selection_changed",
        source_kind: "empty",
        element_level: "none",
        target_level: "none",
        items: [],
        atom_indices: [],
        group_indices: [],
        component_indices: [],
        chain_indices: [],
        molecule_indices: [],
        entity_indices: [],
        count_atoms: 0,
        count_groups: 0,
        count_shapes: 0,
        count_annotations: 0,
    });
});
