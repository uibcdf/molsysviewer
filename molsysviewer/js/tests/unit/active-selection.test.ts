import assert from "node:assert";
import test from "node:test";

import { ActiveSelectionController } from "../../src/managers/active-selection";

function clickEvent(atomIndices: number[], shift = false): any {
    return {
        modifiers: { shift },
        current: {
            loci: atomIndices.length === 0 ? null : {
                kind: "element-loci",
                elements: [{ unit: { elements: atomIndices }, indices: atomIndices.map((_, index) => index) }],
            },
        },
    };
}

test("ActiveSelectionController replaces, adds with shift, avoids duplicates, and clears on empty click", () => {
    const events: any[] = [];
    const controller = new ActiveSelectionController((msg) => events.push(msg));

    controller.handlePrimaryClick(clickEvent([1, 2]));
    controller.handlePrimaryClick(clickEvent([8], true));
    controller.handlePrimaryClick(clickEvent([8], true));
    controller.handlePrimaryClick(clickEvent([], true));
    controller.handlePrimaryClick(clickEvent([]));

    assert.deepStrictEqual(events, [
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "atom",
            target_level: "none",
            items: [{ source_kind: "element", element_level: "atom", atom_indices: [1, 2] }],
            atom_indices: [1, 2],
            group_indices: [],
            component_indices: [],
            chain_indices: [],
            molecule_indices: [],
            entity_indices: [],
            count_atoms: 2,
            count_groups: 0,
            count_shapes: 0,
        },
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "atom",
            target_level: "none",
            items: [
                { source_kind: "element", element_level: "atom", atom_indices: [1, 2] },
                { source_kind: "element", element_level: "atom", atom_indices: [8] },
            ],
            atom_indices: [1, 2, 8],
            group_indices: [],
            component_indices: [],
            chain_indices: [],
            molecule_indices: [],
            entity_indices: [],
            count_atoms: 3,
            count_groups: 0,
            count_shapes: 0,
        },
        {
            event: "interaction_active_selection_changed",
            source_kind: "element",
            element_level: "atom",
            target_level: "none",
            items: [
                { source_kind: "element", element_level: "atom", atom_indices: [1, 2] },
                { source_kind: "element", element_level: "atom", atom_indices: [8] },
            ],
            atom_indices: [1, 2, 8],
            group_indices: [],
            component_indices: [],
            chain_indices: [],
            molecule_indices: [],
            entity_indices: [],
            count_atoms: 3,
            count_groups: 0,
            count_shapes: 0,
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
        },
    ]);
});
