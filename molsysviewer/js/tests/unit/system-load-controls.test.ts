import assert from "node:assert/strict";
import test from "node:test";
import { systemLoadArguments, systemStructureIndices, type SystemLoadRow } from "../../src/ui/panels/system-load-controls";

const row = (source: string, structures = "0", label = ""): SystemLoadRow => ({ source, structures, label, selection: "all" });

test("a single source retains single-system loading and whole label", () => {
    assert.deepEqual(systemLoadArguments([row(" a.pdb ", "0", " A ")], "independent", "add", false), {
        molecular_system: "a.pdb", multiple: false, mode: "add", label: "A", selection: "all", structure_indices: [0], structure_pairing: null,
    });
});
test("independent files and PDB IDs keep per-source selection and labels", () => {
    const a = row("a.pdb", "8,0", "same"); a.selection = "[2, 4]";
    assert.deepEqual(systemLoadArguments([a, row("1CRN", "1,3", "same")], "independent", "replace", true), {
        molecular_system: ["a.pdb", "1CRN"], multiple: true, mode: "replace", labels: ["same", "same"],
        selection: [[2, 4], "all"], structure_indices: [[8, 0], [1, 3]], structure_pairing: "by_index",
    });
});
test("complementary forms declare one system and use only visible shared selectors", () => {
    const a = row("a.prmtop", "all", "trajectory"); a.selection = "atom_name == 'CA'";
    assert.deepEqual(systemLoadArguments([a, row("a.dcd", "not a visible field")], "complementary", "append_structures", false), {
        molecular_system: ["a.prmtop", "a.dcd"], multiple: false, mode: "append_structures", label: "trajectory",
        selection: "atom_name == 'CA'", structure_indices: "all", structure_pairing: null,
    });
});
test("batch append and incomplete source drafts never dispatch", () => {
    assert.throws(() => systemLoadArguments([row("a"), row("b")], "independent", "append_structures", false));
    assert.throws(() => systemLoadArguments([row("")], "independent", "add", false));
    assert.throws(() => systemLoadArguments([], "independent", "add", false));
});
test("structure lists retain nonconsecutive order and reject lossy or duplicate values", () => {
    assert.deepEqual(systemStructureIndices("[8, 0, 3]"), [8, 0, 3]);
    assert.equal(systemStructureIndices(" all "), "all");
    for (const invalid of ["", "[]", "-1", "0.5", "true", "0,0", "0,", "[0", "0]", "9007199254740993"]) {
        assert.throws(() => systemStructureIndices(invalid), invalid);
    }
});
test("atom lists reject invalid scientific selectors without coercion", () => {
    for (const value of ["[]", "[true]", "[0.5]", "[-1]", "[2,null]"]) {
        const a = row("a.pdb"); a.selection = value;
        assert.throws(() => systemLoadArguments([a], "independent", "add", false));
    }
});
